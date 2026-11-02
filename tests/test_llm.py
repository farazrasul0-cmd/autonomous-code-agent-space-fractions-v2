# tests/test_llm.py - Unit tests for DeepSeek LLM client, dual budget guards, and cache
import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

# Ensure src/ is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.llm import (
    Budget,
    BudgetExceededError,
    Cache,
    CacheMissError,
    Client,
    FakeClient,
    LLMError,
    PRICE_IN_HIT,
    PRICE_IN_MISS,
    PRICE_OUT,
    DEFAULT_RUN_CAP,
    DEFAULT_TOTAL_CAP,
)


class TestLLM(unittest.TestCase):

    def test_budget_blocks_per_run(self):
        """A call exceeding run_cap raises BudgetExceededError."""
        budget = Budget(run_cap=0.0001, total_cap=0.85)
        # Usage that costs significantly more than $0.0001:
        # 1000 miss tokens * $0.00000066 + 500 completion tokens * $0.00000198 = $0.00165
        expensive_usage = {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 1000
        }
        with self.assertRaises(BudgetExceededError):
            budget.add(expensive_usage)

        # Also test check() pre-check blocking
        budget2 = Budget(run_cap=0.00005, total_cap=0.85, spent=0.00005)
        with self.assertRaises(BudgetExceededError):
            budget2.check(estimated_cost=0.00001)

    def test_budget_blocks_cumulative(self):
        """After several calls, a call exceeding total_cap raises BudgetExceededError."""
        # Total cap of $0.0001, high per-run cap
        budget = Budget(run_cap=0.15, total_cap=0.0001)
        # Each call costs ~ $0.00006
        call_usage = {
            "prompt_tokens": 50,
            "completion_tokens": 15,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 50
        }
        # First call succeeds: cost is ~ $0.0000627 <= $0.0001
        cost1 = budget.add(call_usage)
        self.assertGreater(cost1, 0)
        self.assertLess(budget.total_spent, 0.0001)

        # Second call adds another $0.0000627 -> total spent $0.0001254 > $0.0001
        with self.assertRaises(BudgetExceededError):
            budget.add(call_usage)

        # Even after per-run reset, cumulative guard must block
        budget.reset_run()
        self.assertEqual(budget.spent, 0.0)
        self.assertGreater(budget.total_spent, 0.0001)
        with self.assertRaises(BudgetExceededError):
            budget.check()

    def test_truncated_response_surfaced(self):
        """finish_reason='length' is returned intact, not retried automatically."""
        truncated_response = {
            "choices": [{
                "message": {"content": "def calculate_orbit(distance, mass):", "role": "assistant"},
                "finish_reason": "length"
            }],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 20
            }
        }
        client = FakeClient([truncated_response])
        res = client.chat([{"role": "user", "content": "Write orbit calculation function"}])

        self.assertEqual(res["finish_reason"], "length")
        self.assertEqual(res["content"], "def calculate_orbit(distance, mass):")

    def test_replay_returns_cached_body(self):
        """Record then replay returns the same response without a network call."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = Cache(cache_dir=tmp_dir, mode="record")

            req_messages = [{"role": "user", "content": "What is 2+2?"}]
            mock_api_response = {
                "choices": [{
                    "message": {"content": "4", "role": "assistant"},
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 2,
                    "prompt_cache_hit_tokens": 0,
                    "prompt_cache_miss_tokens": 10
                }
            }

            body = {
                "model": "deepseek-v4-pro",
                "messages": req_messages,
                "temperature": 0.1,
                "max_tokens": 4096,
                "thinking": {"type": "disabled"}
            }

            # Record in cache
            cache.put(body, mock_api_response)

            # Switch to replay mode
            cache.mode = "replay"

            # Create client with replay cache and dummy key
            client = Client(api_key="sk-test-dummy-key", budget=Budget(), cache=cache)
            res = client.chat(messages=req_messages)

            self.assertEqual(res["content"], "4")
            self.assertEqual(res["finish_reason"], "stop")
            self.assertEqual(res["cost"], 0.0)  # Replay must not bill budget

            # Replay with uncached prompt raises CacheMissError
            with self.assertRaises(CacheMissError):
                client.chat(messages=[{"role": "user", "content": "Uncached prompt"}])

    def test_cache_never_contains_headers(self):
        """Read cache file and assert 'Authorization' and API key value are not present."""
        dummy_secret_key = "sk-super-secret-key-probe-987654321"
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = Cache(cache_dir=tmp_dir, mode="record")

            body = {
                "model": "deepseek-v4-pro",
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.1,
                "max_tokens": 100,
                "thinking": {"type": "disabled"}
            }
            fake_response = {
                "choices": [{"message": {"content": "Hi there"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2}
            }

            cache.put(body, fake_response)
            key = cache.compute_key(body)
            cache_file = os.path.join(tmp_dir, f"{key}.json")
            self.assertTrue(os.path.exists(cache_file))

            with open(cache_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertNotIn("Authorization", content)
            self.assertNotIn(dummy_secret_key, content)
            self.assertNotIn("Bearer", content)

    def test_fake_client_sequence(self):
        """FakeClient returns scripted responses in order."""
        scripted = [
            "Response 1",
            {"content": "Response 2", "tool_calls": [{"id": "t1", "function": {"name": "run"}}]},
            "Response 3"
        ]
        client = FakeClient(scripted)

        r1 = client.chat([{"role": "user", "content": "a"}])
        self.assertEqual(r1["content"], "Response 1")

        r2 = client.chat([{"role": "user", "content": "b"}])
        self.assertEqual(r2["content"], "Response 2")
        self.assertIsNotNone(r2["tool_calls"])

        r3 = client.chat([{"role": "user", "content": "c"}])
        self.assertEqual(r3["content"], "Response 3")

        with self.assertRaises(IndexError):
            client.chat([{"role": "user", "content": "d"}])

    def test_cost_formula_matches_hand_calc(self):
        """Call budget.add with known usage dict from DECISIONS.md and assert cost matches hand arithmetic within $0.0000001."""
        # DECISIONS.md Section 4 probe usage:
        # prompt_cache_hit_tokens: 0
        # prompt_cache_miss_tokens: 39
        # completion_tokens: 6
        # Expected off-peak cost:
        # 39 * 0.00000066 + 6 * 0.00000198 = 0.00002574 + 0.00001188 = 0.00003762
        usage = {
            "prompt_tokens": 39,
            "completion_tokens": 6,
            "total_tokens": 45,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 39
        }
        budget = Budget()
        cost = budget.add(usage)
        expected = 0.00003762
        self.assertAlmostEqual(cost, expected, places=8, msg=f"Cost {cost} did not match hand arithmetic {expected}")

        # Fallback test: when hit/miss fields missing, treat all prompt tokens as cache misses
        usage_fallback = {
            "prompt_tokens": 39,
            "completion_tokens": 6
        }
        cost_fallback = budget.calculate_cost(usage_fallback)
        self.assertAlmostEqual(cost_fallback, expected, places=8)

        # Cache hit tokens test
        usage_with_hit = {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "prompt_cache_hit_tokens": 80,
            "prompt_cache_miss_tokens": 20
        }
        expected_hit_cost = (80 * PRICE_IN_HIT) + (20 * PRICE_IN_MISS) + (20 * PRICE_OUT)
        cost_with_hit = budget.calculate_cost(usage_with_hit)
        self.assertAlmostEqual(cost_with_hit, expected_hit_cost, places=8)


if __name__ == "__main__":
    unittest.main()
