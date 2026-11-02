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
Test prompt: Sheep puzzle reasoning query.

| Metric | Non-Thinking (`type: disabled`) | Thinking-Enabled (`type: enabled`) | Difference / Savings |
| :--- | :--- | :--- | :--- |
| **Prompt Tokens** | 35 | 114 | -79 tokens (prompt overhead) |
| **Reasoning Tokens** | 0 | 101 | **-101 reasoning tokens (100% saved)** |
| **Completion Tokens** | 89 | 191 | **-102 completion tokens (53.4% reduction)** |
| **Total Tokens** | 124 | 305 | **-181 total tokens (59.3% reduction)** |

**Conclusion**: Non-thinking mode is confirmed working and is **measurably faster and >50% cheaper** per call. Thinking mode is strictly disabled across all pipeline stages unless provably necessary.

---

## 4. Real Probe Usage JSON & Hand-Calculated Cost

### Real Probe Usage JSON (Non-Thinking Call)
Key redacted. Raw usage payload returned from official API:

```json
{
  "prompt_tokens": 35,
  "completion_tokens": 89,
  "total_tokens": 124,
  "prompt_tokens_details": {
    "cached_tokens": 0
  },
  "prompt_cache_hit_tokens": 0,
  "prompt_cache_miss_tokens": 35
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
- $\text{prompt\_cache\_miss\_tokens} = 35$
- $\text{completion\_tokens} = 89$

**1. Off-Peak Rate Arithmetic:**
$$\text{Input Cost} = 35 \times \$0.00000066 = \$0.00002310$$
$$\text{Output Cost} = 89 \times \$0.00000198 = \$0.00017622$$
$$\text{Total Cost (Off-Peak)} = \$0.00002310 + \$0.00017622 = \mathbf{\$0.00019932} \quad (\approx \$0.00020)$$

**2. Peak Rate Arithmetic (Conservative Budget Guard Upper Bound):**
$$\text{Input Cost} = 35 \times \$0.00000132 = \$0.00004620$$
$$\text{Output Cost} = 89 \times \$0.00000396 = \$0.00035244$$
$$\text{Total Cost (Peak)} = \$0.00004620 + \$0.00035244 = \mathbf{\$0.00039864} \quad (\approx \$0.00040)$$

---

## 5. Budget Constraints & Evaluation Protocol

- **Total Budget**: **\$1.00** total evaluation ceiling.
- **Per-Run Cap**: **\$0.15** maximum per generation/evaluation run.
- **Cumulative Cap**: **\$0.85** hard stopping threshold across all evaluation runs combined, leaving a \$0.15 safety buffer.
- **Enforcement**: Dual guards inside `src/llm.py` block any outbound request if either the per-run cost exceeds \$0.15 or the cumulative total evaluation spend exceeds \$0.85.
- **Planned Evaluation Runs**: 2 Space Fractions runs + 1 second-input run (2+1 format), safely staying within the \$0.85 cumulative cap ($3 \times \$0.15 = \$0.45 \ll \$0.85$). Adjust to 3+1 only if Phase 8 measures cost below \$0.10.
- **Professor Contact**: **None** (strict adherence to supervisory directive).
- **Environment & Key Protection**: No API keys appear in repository files, commit history, logs, or replay cache. `.env`, `.venv`, and `scratch/` are strictly gitignored.
