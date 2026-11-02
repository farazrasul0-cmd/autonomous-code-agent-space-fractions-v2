# src/llm.py - DeepSeek LLM client with dual budget guards and record/replay caching
import os
import json
import time
import hashlib
import threading
import urllib.request
import urllib.error

# Official endpoints and constants locked in DECISIONS.md
BASE_URL = "https://api.deepseek.com/chat/completions"
MODELS_URL = "https://api.deepseek.com/models"
MODEL = "deepseek-v4-pro"

# Pricing per token (off-peak official rate card)
PRICE_IN_HIT = 0.022 / 1_000_000     # $0.000000022 per token
PRICE_IN_MISS = 0.66 / 1_000_000     # $0.000000660 per token
PRICE_OUT = 1.98 / 1_000_000         # $0.000001980 per token

# Default budget ceilings
DEFAULT_RUN_CAP = 0.15               # $0.15 hard cap per run
DEFAULT_TOTAL_CAP = 0.85             # $0.85 cumulative cap across all runs

# MAX_TOKENS: 4096 tokens accommodates full contract JSON schemas, module
# implementations with unit tests, while bounding runaway output generation to protect per-run budget.
MAX_TOKENS = 4096


class BudgetExceededError(Exception):
    """Raised when an operation would exceed or has exceeded the per-run or total budget ceiling."""
    pass


class LLMError(Exception):
    """Raised on LLM API or network errors, sanitizing headers and secrets."""
    pass


class CacheMissError(Exception):
    """Raised in replay mode when a requested payload hash is not found in cache."""
    pass


def get_api_key(explicit_key=None):
    """Load API key from argument, environment variable, or repo-root .env file without external dependencies."""
    if explicit_key:
        return explicit_key.strip()
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key.strip()

    env_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    ]
    for p in env_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DEEPSEEK_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
    return None


class Budget:
    """Thread-safe dual budget guard tracking per-run spent and cumulative total spent."""
    def __init__(self, run_cap=DEFAULT_RUN_CAP, total_cap=DEFAULT_TOTAL_CAP, spent=0.0, total_spent=0.0):
        self.run_cap = float(run_cap)
        self.total_cap = float(total_cap)
        self.spent = float(spent)
        self.total_spent = float(total_spent)
        self._lock = threading.Lock()

    def check(self, estimated_cost=0.0):
        """Check if adding estimated_cost would exceed either cap. Raise BudgetExceededError if so."""
        with self._lock:
            projected_run = self.spent + estimated_cost
            if projected_run > self.run_cap:
                raise BudgetExceededError(
                    f"Per-run budget cap would be exceeded: ${projected_run:.6f} > cap ${self.run_cap:.6f}"
                )
            projected_total = self.total_spent + estimated_cost
            if projected_total > self.total_cap:
                raise BudgetExceededError(
                    f"Cumulative total budget cap would be exceeded: ${projected_total:.6f} > cap ${self.total_cap:.6f}"
                )

    def calculate_cost(self, usage_dict):
        """Compute exact cost from usage dictionary using DECISIONS.md rate card formula."""
        if not usage_dict:
            return 0.0

        hit_tokens = usage_dict.get("prompt_cache_hit_tokens", 0) or 0
        miss_tokens = usage_dict.get("prompt_cache_miss_tokens")
        prompt_tokens = usage_dict.get("prompt_tokens", 0) or 0

        # Handle missing hit/miss fields gracefully: if only prompt_tokens present, treat all as miss
        if miss_tokens is None:
            if hit_tokens == 0:
                miss_tokens = prompt_tokens
            else:
                miss_tokens = max(0, prompt_tokens - hit_tokens)

        completion_tokens = usage_dict.get("completion_tokens", 0) or 0

        cost = (hit_tokens * PRICE_IN_HIT) + (miss_tokens * PRICE_IN_MISS) + (completion_tokens * PRICE_OUT)
        return cost

    def add(self, usage_dict):
        """Compute cost from usage, increment spent and total_spent, and verify against caps."""
        cost = self.calculate_cost(usage_dict)
        with self._lock:
            self.spent += cost
            self.total_spent += cost
            if self.spent > self.run_cap:
                raise BudgetExceededError(
                    f"Per-run budget cap exceeded: spent ${self.spent:.6f} > cap ${self.run_cap:.6f}"
                )
            if self.total_spent > self.total_cap:
                raise BudgetExceededError(
                    f"Cumulative total budget cap exceeded: total spent ${self.total_spent:.6f} > cap ${self.total_cap:.6f}"
                )
        return cost

    def reset_run(self):
        """Reset per-run spent for a new evaluation run while preserving total_spent."""
        with self._lock:
            self.spent = 0.0


class Cache:
    """Record and replay cache keyed by SHA-256 of request payload. Never stores headers or API keys."""
    def __init__(self, cache_dir=".cache", mode="live"):
        self.cache_dir = cache_dir
        self.mode = mode  # "live", "record", or "replay"
        self._lock = threading.Lock()

    @staticmethod
    def compute_key(body: dict) -> str:
        """Compute deterministic SHA-256 hash of JSON request body."""
        serialized = json.dumps(body, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def get_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, body: dict):
        """Retrieve cached response if available. Raises CacheMissError in replay mode if missing."""
        if self.mode == "live":
            return None

        key = self.compute_key(body)
        path = self.get_path(key)

        with self._lock:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    return entry.get("response")

        if self.mode == "replay":
            raise CacheMissError(f"Replay cache miss for request hash {key}")

        return None

    def put(self, body: dict, response_dict: dict):
        """Store request body and response in cache. Explicitly excludes headers and authorization secrets."""
        if self.mode not in ("record", "live"):
            return

        key = self.compute_key(body)
        with self._lock:
            os.makedirs(self.cache_dir, exist_ok=True)
            path = self.get_path(key)
            entry = {
                "request": body,
                "response": response_dict
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)


class Client:
    """Official DeepSeek API client with non-thinking default, budget tracking, and caching."""
    def __init__(self, api_key=None, base_url=BASE_URL, model=MODEL, budget=None, cache=None, max_tokens=MAX_TOKENS):
        self.api_key = get_api_key(api_key)
        self.base_url = base_url
        self.model = model
        self.budget = budget or Budget()
        self.cache = cache
        self.max_tokens = max_tokens

    def _format_response(self, resp_dict, is_cached=False):
        """Format raw API response dictionary into client result dict."""
        choices = resp_dict.get("choices", [])
        first_choice = choices[0] if choices else {}
        message = first_choice.get("message", {})
        content = message.get("content")
        tool_calls = message.get("tool_calls")
        finish_reason = first_choice.get("finish_reason")
        usage = resp_dict.get("usage", {})

        # Do not charge budget for cache replay (cost = 0.0)
        cost = 0.0 if is_cached else self.budget.add(usage)

        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
            "usage": usage,
            "cost": cost
        }

    def chat(self, messages, tools=None, json_mode=False, max_tokens=None, temperature=0.1, thinking=False):
        """Send chat request with non-thinking by default and budget/cache controls."""
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "thinking": {"type": "enabled" if thinking else "disabled"}
        }

        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if tools:
            body["tools"] = tools

        # 1. Check cache first
        if self.cache and self.cache.mode in ("record", "replay"):
            cached_resp = self.cache.get(body)
            if cached_resp is not None:
                return self._format_response(cached_resp, is_cached=True)

        # 2. Check budget before network call
        self.budget.check(estimated_cost=0.0)

        # 3. Validate credentials
        if not self.api_key:
            raise LLMError("DeepSeek API key not provided or found in environment/.env.")

        # 4. Execute HTTP request with retry logic
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.base_url, data=data, headers=headers, method="POST")

        max_retries = 3
        backoff_delays = [1.0, 2.0, 4.0]
        network_retried = False

        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_bytes = resp.read()
                    resp_dict = json.loads(resp_bytes.decode("utf-8"))

                    # Cache raw response if in record mode
                    if self.cache and self.cache.mode == "record":
                        self.cache.put(body, resp_dict)

                    return self._format_response(resp_dict, is_cached=False)

            except urllib.error.HTTPError as e:
                # 429 and 5xx: exponential backoff retry
                if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                    time.sleep(backoff_delays[attempt])
                    continue
                # Sanitize error message: never include headers or API keys
                raise LLMError(f"HTTP error {e.code}: {e.reason}")

            except urllib.error.URLError as e:
                # Network error: retry once after 2 seconds
                if not network_retried and attempt < max_retries - 1:
                    network_retried = True
                    time.sleep(2.0)
                    continue
                raise LLMError(f"Network error: {e.reason}")

            except json.JSONDecodeError as e:
                raise LLMError(f"Failed to parse API response as JSON: {str(e)}")

        raise LLMError("Request failed after maximum retry attempts.")


class FakeClient:
    """Mock client returning scripted responses from a list in sequence without network calls."""
    def __init__(self, responses, budget=None):
        self.responses = list(responses)
        self.index = 0
        self.budget = budget or Budget()

    def chat(self, messages, tools=None, json_mode=False, max_tokens=None, temperature=0.1, thinking=False):
        if self.index >= len(self.responses):
            raise IndexError("FakeClient has exhausted all scripted responses")

        resp = self.responses[self.index]
        self.index += 1

        if isinstance(resp, str):
            usage = {
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 10
            }
            cost = self.budget.add(usage)
            return {
                "content": resp,
                "tool_calls": None,
                "finish_reason": "stop",
                "usage": usage,
                "cost": cost
            }
        elif isinstance(resp, dict):
            if "choices" in resp:
                choices = resp.get("choices", [])
                first = choices[0] if choices else {}
                msg = first.get("message", {})
                usage = resp.get("usage", {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "prompt_cache_hit_tokens": 0,
                    "prompt_cache_miss_tokens": 10
                })
                cost = self.budget.add(usage)
                return {
                    "content": msg.get("content"),
                    "tool_calls": msg.get("tool_calls"),
                    "finish_reason": first.get("finish_reason", "stop"),
                    "usage": usage,
                    "cost": cost
                }
            else:
                usage = resp.get("usage", {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "prompt_cache_hit_tokens": 0,
                    "prompt_cache_miss_tokens": 10
                })
                cost = self.budget.add(usage)
                return {
                    "content": resp.get("content"),
                    "tool_calls": resp.get("tool_calls"),
                    "finish_reason": resp.get("finish_reason", "stop"),
                    "usage": usage,
                    "cost": cost
                }
        else:
            raise TypeError(f"Unsupported scripted response type: {type(resp)}")


def models(api_key=None, base_url=None):
    """Query DeepSeek models endpoint and return list of model IDs for GUI testing."""
    key = get_api_key(api_key)
    if not key:
        raise LLMError("API key not found for models() call")

    url = base_url or MODELS_URL
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("id") for m in data.get("data", [])]
    except Exception as e:
        raise LLMError(f"Failed to fetch models: {str(e)}")
