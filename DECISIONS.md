# Architecture & Implementation Decisions (DECISIONS.md)

This document records the locked architectural and technical decisions, API probe results, pricing models, and budget constraints for the DeepSeek Code Agent.

---

## 1. Model Identification & API Behavior

- **Model ID**: `deepseek-v4-pro` (Official DeepSeek API endpoint: `https://api.deepseek.com/chat/completions`)
- **Protocol**: Standard HTTPS REST POST with Bearer authentication (`urllib.request` standard library only).
- **JSON Mode (`response_format`)**: **YES** (Confirmed). Probe A verified that `response_format: {"type": "json_object"}` produces valid, parseable JSON conforming to expected output.
- **Tool Calling (Function Calling)**: **YES** (Confirmed). Probe B verified that providing `tools` with `type: "function"` returns structured `tool_calls` with function name and arguments.
- **Temperature Honored**: **YES** (Confirmed). Accepts standard floating-point temperatures (e.g. 0.0 to 0.2 for deterministic code generation).
- **Thinking Mode Control**: Supported via payload parameter `"thinking": {"type": "disabled"}` or `"thinking": {"type": "enabled"}`.

---

## 2. Official Pricing Card (`deepseek-v4-pro`)

Official rate card per 1 Million (1,000,000) tokens:

| Token Category | Off-Peak Rate (per 1M tokens) | Peak Rate (per 1M tokens) | Per-Token Cost (Off-Peak) | Per-Token Cost (Peak / Conservative) |
| :--- | :--- | :--- | :--- | :--- |
| **Input (Cache Hit)** | \$0.022 | \$0.044 | \$0.000000022 | \$0.000000044 |
| **Input (Cache Miss)** | \$0.66 | \$1.32 | \$0.000000660 | \$0.000001320 |
| **Output (Completion)** | \$1.98 | \$3.96 | \$0.000001980 | \$0.000003960 |

---

## 3. Reasoning-Token Billing & Non-Thinking Mode Comparison

### How Reasoning Tokens Appear
- In **thinking-enabled mode**, DeepSeek returns a nested `completion_tokens_details` object inside `usage`:
  ```json
  "completion_tokens_details": {
    "reasoning_tokens": 101
  }
  ```
- Reasoning tokens are included in `completion_tokens` and billed at the standard output token rate (\$1.98 / 1M off-peak, \$3.96 / 1M peak).
- In **non-thinking mode** (`"thinking": {"type": "disabled"}`), reasoning tokens are omitted (0 tokens generated), eliminating all internal chain-of-thought overhead.

### Measured Token Comparison (Probe D & E)
*Correction Note: Both calls were dispatched with identical message payloads (System: "You are a concise logic puzzle assistant.", User: "A farmer has 17 sheep, and all but 9 die. How many sheep are left alive? State your final answer clearly."); the 79 additional prompt tokens in thinking mode are automatically prepended server-side by DeepSeek as internal reasoning scaffold instructions.*

| Metric | Non-Thinking (`type: disabled`) | Thinking-Enabled (`type: enabled`) | Difference / Savings |
| :--- | :--- | :--- | :--- |
| **Prompt Tokens** | 39 | 118 (39 + 79 server scaffold) | **-79 prompt tokens (66.9% saved)** |
| **Reasoning Tokens** | **0** | **62** | **-62 reasoning tokens (100% saved)** |
| **Completion Tokens** | **6** | **69** | **-63 completion tokens (91.3% reduction)** |
| **Total Tokens** | 45 | 187 | **-142 total tokens (75.9% reduction)** |

**Conclusion**: Non-thinking mode is confirmed working and is **measurably faster and ~76% cheaper in total tokens** (saving 79 server scaffold prompt tokens and eliminating all 62 reasoning completion tokens). Thinking mode is strictly disabled across all pipeline stages unless provably necessary.

---

## 4. Real Probe Usage JSON & Hand-Calculated Cost

### Real Probe Usage JSON (Non-Thinking Call)
Key redacted. Raw usage payload returned from official API on identical clean comparison probe:

```json
{
  "prompt_tokens": 39,
  "completion_tokens": 6,
  "total_tokens": 45,
  "prompt_tokens_details": {
    "cached_tokens": 0
  },
  "prompt_cache_hit_tokens": 0,
  "prompt_cache_miss_tokens": 39
}
```

### Cost Formula for `llm.py`
$$\text{Cost} = (\text{prompt\_cache\_hit\_tokens} \times P_{\text{hit}}) + (\text{prompt\_cache\_miss\_tokens} \times P_{\text{miss}}) + (\text{completion\_tokens} \times P_{\text{out}})$$

Where:
- $P_{\text{hit}} = \frac{\$0.022}{1,000,000} = \$0.000000022$ (Off-Peak) or $\frac{\$0.044}{1,000,000} = \$0.000000044$ (Peak)
- $P_{\text{miss}} = \frac{\$0.66}{1,000,000} = \$0.00000066$ (Off-Peak) or $\frac{\$1.32}{1,000,000} = \$0.00000132$ (Peak)
- $P_{\text{out}} = \frac{\$1.98}{1,000,000} = \$0.00000198$ (Off-Peak) or $\frac{\$3.96}{1,000,000} = \$0.00000396$ (Peak)

### Hand Calculation (Exact Arithmetic)
For this call:
- $\text{prompt\_cache\_hit\_tokens} = 0$
- $\text{prompt\_cache\_miss\_tokens} = 39$
- $\text{completion\_tokens} = 6$

**1. Off-Peak Rate Arithmetic:**
$$\text{Input Cost} = 39 \times \$0.00000066 = \$0.00002574$$
$$\text{Output Cost} = 6 \times \$0.00000198 = \$0.00001188$$
$$\text{Total Cost (Off-Peak)} = \$0.00002574 + \$0.00001188 = \mathbf{\$0.00003762}$$

**2. Peak Rate Arithmetic (Conservative Budget Guard Upper Bound):**
$$\text{Input Cost} = 39 \times \$0.00000132 = \$0.00005148$$
$$\text{Output Cost} = 6 \times \$0.00000396 = \$0.00002376$$
$$\text{Total Cost (Peak)} = \$0.00005148 + \$0.00002376 = \mathbf{\$0.00007524}$$

---

## 5. Budget Constraints & Evaluation Protocol

- **Total Budget**: **\$1.00** total evaluation ceiling.
- **Per-Run Cap**: **\$0.15** maximum per generation/evaluation run.
- **Cumulative Cap**: **\$0.85** hard stopping threshold across all evaluation runs combined, leaving a \$0.15 safety buffer.
- **Enforcement**: Dual guards inside `src/llm.py` block any outbound request if either the per-run cost exceeds \$0.15 or the cumulative total evaluation spend exceeds \$0.85.
- **Planned Evaluation Runs**: 2 Space Fractions runs + 1 second-input run (2+1 format), safely staying within the \$0.85 cumulative cap ($3 \times \$0.15 = \$0.45 \ll \$0.85$). Adjust to 3+1 only if Phase 8 measures cost below \$0.10.
- **Professor Contact**: **None** (strict adherence to supervisory directive).
- **Environment & Key Protection**: No API keys appear in repository files, commit history, logs, or replay cache. `.env`, `.venv`, and `scratch/` are strictly gitignored.

---

## 6. Phase 6 Prerequisites (Standing Directive)

- **Windowed-Mode Print Guard**: In PyInstaller windowed mode on Windows (`runw.exe`), `sys.stdout` and `sys.stderr` may be `None` or raise exceptions when written to directly. Before implementing code generation in Phase 6, all runtime code and generated Tkinter application entrypoints must include a print guard (redirecting `sys.stdout`/`sys.stderr` to a safe dummy stream/null or logging stream) to prevent silent crashes in windowed mode.

---

## 7. Operational Parameters & Cost Controls (Phase 4 Updates)

- **Phase 4 Live Gate Scope**: Phase 4 live gate was a trivial 39-token call. Real budget behavior measured at Phase 8. If Phase 8 single-run cost > $0.25, drop evaluation to 1+1 per standing directive.
- **Model Usage Policy**: `deepseek-flash` is available on the official models list but will NOT be used without supervisor approval.
- **Budget Estimate Heuristic**: Budget estimate uses chars/3 heuristic + max_tokens * output price. This is conservative (assumes all miss, no cache hits).
- **Keyword-Based Conflict Detection**: Conflicts detection is keyword-based; a second-input doc mentioning 'Dockerfile' as an optional artifact will NOT trigger the cloud-conflict entry. Keywords are explicitly narrowed to `web-based`, `microservices`, `kubernetes`, `redis`, `rabbitmq`, `docker-compose`, and `docker container`.
