# DeepSeek Code Agent

A standalone, lightweight Windows desktop agent built with the Python 3.12 standard library that reads software architecture documentation and UML diagrams, synthesizes an architectural contract, incrementally implements source code modules against the contract using DeepSeek (`deepseek-v4-pro`), enforces multi-layered verification (AST static analysis, contract conformance, unit tests, and headless Tkinter UI walkthroughs), and autonomously repairs failures in a multi-turn tool-calling loop.

## Video Walkthrough
- **Demonstration Video**: [YouTube Walkthrough (Demo & Autonomous Repair Walkthrough)](https://youtu.be/d-7qc7QIC8M)

---

## 1. Reference-Repo Mapping Table

As required by Task 1, this agent investigates open-source Claude-Code and agentic coding patterns ([`ultraworkers/claw-code`](https://github.com/ultraworkers/claw-code), [`Windy3f3f3f3f/how-claude-code-works`](https://github.com/Windy3f3f3f3f/how-claude-code-works), and [`anthropics/claude-code`](https://github.com/anthropics/claude-code)) and adapts them into a resilient, contract-driven desktop architecture:

| Claude-Code Architectural Concept | DeepSeek Code Agent Implementation | Purpose & Verification Value |
|:---|:---|:---|
| **Agent Tool Interface** | Standardized `read_file`, `write_file`, `list_dir`, and `run_checks` tools in [src/agent.py](file:///d:/projects/Task-1%20resubmission/src/agent.py) with strict path containment. | Allows model to inspect files, patch bugs, and re-check diagnostics without host escape. |
| **Observation Reinjection** | Verification failures (AST syntax, signature mismatches, test errors, runtime exceptions) are reinjected as structured tool responses. | Powers autonomous multi-turn repair loop (up to 5 rounds) to heal code errors without restarting synthesis. |
| **Context Management** | Dynamic **AST Signature Ledger** extracted on-the-fly from previously generated modules; passes only signatures instead of full files. | Reduces prompt token consumption by passing concise interface summaries rather than full file bodies, preventing context bloat. |
| **Multi-Stage Verification** | **V1–V8 Verification Suite**: V1 (Presence), V2 (AST compile), V3 (Contract conformance), V4 (Call-site AST), V5 (Tk collisions), V6 (Imports), V7 (Tests), V8 (Headless UI walkthrough). | Catches static, semantic, and runtime UI errors before human interaction. |
| **Permissions & Safety Guardrails** | Path confinement rejecting `..` traversal and absolute paths; windowed print guard redirecting `sys.stdout`/`sys.stderr` to prevent GUI crash. | Prevents disk escape and guarantees safe execution in windowed PyInstaller environments. |
| **Dual Budget Controls** | Hard stop enforcement at both per-run ($0.15) and cumulative evaluation ($0.85) boundaries in [src/llm.py](file:///d:/projects/Task-1%20resubmission/src/llm.py). | Eliminates runaway API spend while operating under a strict $1.00 budget ceiling. |

---

## 2. Quick Start

### Running the Standalone Executable (.exe)
1. Download the latest release (`CodeAgent_onedir.zip`, Release `v1.3.0`, commit `12e575b`, SHA-256 `562ceffcbe30d8708b414f5f6882bb8376156d7492a80412836efd995d2929dc`) from [GitHub Releases](https://github.com/farazrasul0-cmd/autonomous-code-agent-space-fractions-v2/releases) and extract the archive.
2. Double-click **`CodeAgent.exe`**.
   > **Note on Windows SmartScreen**: Because this binary is unsigned, Windows SmartScreen may display a blue warning dialog (*"Windows protected your PC"*). Click **"More info"**, then click **"Run anyway"**.
3. **Configure API Key**: Enter your DeepSeek API key in the masked field (or leave empty if `DEEPSEEK_API_KEY` is set in your environment). Click **"Test Key"** to verify connectivity.
4. **Select Inputs**: Browse and pick the Architecture Documentation and Architecture View files (pre-populated with `examples/inputs/` defaults).
5. **Run Agent**: Click **"Start Synthesis"**. Watch real-time visual progress across the 5 pipeline stages (`Parse` -> `Contract` -> `Implement` -> `Verify` -> `Repair`).
6. **Launch Synthesized App**: When complete, click **"Launch Game"** to start the synthesized desktop application in a detached, independent process.

### Running from Python Source
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.app
```

---

## 3. Evaluation Results Summary

Evaluation results across all runs (including failures) are recorded in [results.md](results.md):

- **Unified Run Table**: Every run from the project lifecycle is recorded in a single table with date, input, source/exe, build commit, first-attempt failures, repair rounds, final result, and cost. See [results.md](results.md) for the full table.
- **Dynamic Contract Synthesis**: Successfully parsed the second input specification (To-Do List: 1 UseCase diagram, 1 Class diagram, 1 State diagram) and dynamically generated an independent domain model (`Task`, `TaskManager`) with zero hardcoded game logic.
- **Autonomous Healing (Pre-v1.2.0 History)**: In `eval_todo_1` (pre-v1.2.0 history), initial generation produced a test mismatch (V7); the autonomous repair loop patched `models.py` at Round 2, achieving all 8 checks PASS and a final verdict of **PASSED**. In `eval_sf_1` (pre-v1.2.0 history), Round 3 repaired `app.py`, converting V8 to PASS; that run ultimately failed V7; the V7 helper fix in v1.2.0 addressed it.
- **Total Evaluation Spend**: Authoritative total spend verified on DeepSeek Dashboard at **¥4.22 CNY (~$0.58 USD)** across all development, testing, release binary evaluations, rehearsals, and video demonstration (the live video walkthrough run cost $0.011170 and healed via Round 1 autonomous repair), remaining comfortably under the strict $0.85 budget cap. A few cents per run (Dashboard is the authoritative source; typical synthesis runs cost between $0.010 and $0.018).

---

## 4. Honest Limitations & Architecture Decisions

1. **Source Line Count**: The agent is ~4,200 lines to support rigorous AST verification (V1-V8), while the generated output remains a lean ~500 lines across 6 files. All 84 automated verification and unit tests pass cleanly (`pytest -q` reports 84 passed, while `python -m unittest discover tests` reports 83 because pytest additionally executes the counter fixture test).
2. **Multi-Run Evaluation Methodology**: See [results.md](results.md) for the complete unified evaluation table. I did not get clarification on whether the $1 limit is per run or for the whole evaluation, so I assumed the stricter reading ($1.00 total for the entire evaluation).
3. **Architectural Conflicts Policy**: When architectural specifications contain contradictory requirements (e.g. web microservices or cloud Docker containers alongside a desktop GUI), the standalone desktop Tkinter architecture strictly supersedes distributed microservices.
4. **Naming Conventions**: Diagram names in camelCase are systematically translated to standard Python `snake_case` at the contract boundary, backed by `@property` decorators with private storage attributes.
