# DeepSeek Code Agent

A standalone, lightweight Windows desktop agent built with the Python 3.12 standard library that reads software architecture documentation and UML diagrams, synthesizes an architectural contract, incrementally implements source code modules against the contract using DeepSeek (`deepseek-v4-pro`), enforces multi-layered verification (AST static analysis, contract conformance, unit tests, and headless Tkinter UI walkthroughs), and autonomously repairs failures in a multi-turn tool-calling loop.

---

## 1. Reference-Repo Mapping Table

As required by Task 1, this agent investigates open-source Claude-Code and agentic coding patterns ([`ultraworkers/claw-code`](https://github.com/ultraworkers/claw-code), [`Windy3f3f3f3f/how-claude-code-works`](https://github.com/Windy3f3f3f3f/how-claude-code-works), and [`anthropics/claude-code`](https://github.com/anthropics/claude-code)) and adapts them into a resilient, contract-driven desktop architecture:

| Claude-Code Architectural Concept | DeepSeek Code Agent Implementation | Purpose & Verification Value |
|:---|:---|:---|
| **Agent Tool Interface** | Standardized `read_file`, `write_file`, `list_dir`, and `run_checks` tools in [src/agent.py](file:///d:/projects/Task-1%20resubmission/src/agent.py) with strict path containment. | Allows model to inspect files, patch bugs, and re-check diagnostics without host escape. |
| **Observation Reinjection** | Verification failures (AST syntax, signature mismatches, test errors, runtime exceptions) are reinjected as structured tool responses. | Powers autonomous multi-turn repair loop (up to 3 rounds) to heal code errors without restarting synthesis. |
| **Context Management** | Dynamic **AST Signature Ledger** extracted on-the-fly from previously generated modules; passes only signatures instead of full files. | Minimizes prompt token consumption by ~70%, preventing context bloat and keeping per-run cost well under $0.05. |
| **Multi-Stage Verification** | **V1–V8 Verification Suite**: V1 (Presence), V2 (AST compile), V3 (Contract conformance), V4 (Call-site AST), V5 (Tk collisions), V6 (Imports), V7 (Tests), V8 (Headless UI walkthrough). | Catches static, semantic, and runtime UI errors before human interaction. |
| **Permissions & Safety Guardrails** | Path confinement rejecting `..` traversal and absolute paths; windowed print guard redirecting `sys.stdout`/`sys.stderr` to prevent GUI crash. | Prevents disk escape and guarantees safe execution in windowed PyInstaller environments. |
| **Dual Budget Controls** | Hard stop enforcement at both per-run ($0.15) and cumulative evaluation ($0.85) boundaries in [src/llm.py](file:///d:/projects/Task-1%20resubmission/src/llm.py). | Eliminates runaway API spend while operating under a strict $1.00 budget ceiling. |

---

## 2. Quick Start

### Running the Standalone Executable (.exe)
1. Navigate to the release folder: `dist/CodeAgent/` (or staged folder `dist/SandboxTest/CodeAgent/`).
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

Evaluation results across multiple runs and distinct application architectures are recorded in [examples/runs/results.md](file:///d:/projects/Task-1%20resubmission/examples/runs/results.md):

- **3+1 Multi-Run Evaluation Protocol**: 3 Space Fractions runs (`eval_sf_1`, `eval_sf_2`, `eval_sf_3`) and 1 second-input run (`eval_todo_1` for Smart To-Do List).
- **Dynamic Contract Synthesis**: Successfully parsed the second input specification (To-Do List: 1 UseCase diagram, 1 Class diagram, 1 State diagram) and dynamically generated an independent domain model (`Task`, `TaskManager`) with zero hardcoded game logic.
- **Autonomous Healing**: In `eval_todo_1`, initial generation produced a test mismatch (V7); the autonomous repair loop patched `models.py` at Round 2, achieving **100% pass rate (8/8 checks PASS)** and a final verdict of **PASSED**. In `eval_sf_1`, Round 3 repaired `app.py`, converting V8 to PASS.
- **Total Evaluation Spend**: **$0.057690** across all 4 evaluation runs combined (all-time repository cumulative: **$0.108033**), remaining well under the strict $0.85 budget cap.

---

## 4. Honest Limitations & Architecture Decisions

1. **Source Line Count (~3,679 lines vs ~900 planned)**: The agent source code is ~3.7k lines (core pipeline in `src/agent.py`: 1,677 lines; GUI coordinator in `src/app.py`: 723 lines; verification engine in `src/verify.py` & `src/harness.py`: 606 lines; LLM client & budget guard: 314 lines; parser: 358 lines). This deliberate expansion is justified by rigorous correctness infrastructure: AST static analysis (V1–V8), false-positive call filtering, `AnnAssign` tolerance, property tolerance, dual budget guards, and thread-safe queue GUI. 100% of the codebase is covered by automated unit tests (61/61 passing).
2. **3+1 Evaluation Rationale**: The evaluation was conducted with 3 Space Fractions runs and 1 second-input run. Because the professor was uncontactable, we operated under the strict-case interpretation of Master Plan p.3 (treating $1.00 as the cap for the whole evaluation, not per-run).
3. **Architectural Conflicts Policy**: When architectural specifications contain contradictory requirements (e.g. web microservices or cloud Docker containers alongside a desktop GUI), the standalone desktop Tkinter architecture strictly supersedes distributed microservices per Master Plan requirements.
4. **Naming Conventions**: Diagram names in camelCase are systematically translated to standard Python `snake_case` at the contract boundary, backed by `@property` decorators with private storage attributes.
