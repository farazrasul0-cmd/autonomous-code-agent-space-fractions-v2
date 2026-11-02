# DeepSeek Code Agent

A lightweight Windows desktop Code Agent built with Python 3.12 standard library, designed to transform software architecture documentation and UML diagrams into fully functioning, self-verified desktop applications powered by DeepSeek (`deepseek-v4-pro`).

---

## 1. Research & Mapping to Reference Implementations

As required by Task 1, this project investigates open-source Claude-Code and agentic coding patterns ([`ultraworkers/claw-code`](https://github.com/ultraworkers/claw-code), [`Windy3f3f3f3f/how-claude-code-works`](https://github.com/Windy3f3f3f3f/how-claude-code-works), and [`anthropics/claude-code`](https://github.com/anthropics/claude-code)) and adapts them into a resilient, contract-driven desktop architecture:

| Claude Code Architecture Idea | CodeAgent Implementation |
| :--- | :--- |
| **Agent Loop with Tool Calling** | Focused repair loop where the LLM calls tools (`read_file`, `write_file`, `list_dir`, `run_checks`) until verification passes. |
| **Tool Interface** | Standardized `write_file`, `read_file`, `list_dir`, and `run_checks` tools with strict path validation. |
| **Observation Reinjection** | Verification failures (AST syntax, contract conformance, call-site mismatches, runtime exceptions) are formatted as structured diagnostic observations for the LLM. |
| **Context Management** | Dynamic signature ledger extracted via Python `ast` from previously generated files, providing exact method signatures rather than concatenating whole files. |
| **Permissions & Safety** | Path containment: file writes are strictly confined to the targeted project output directory. |
| **Verification & Self-Testing** | Eight automated checks (V1 to V8) including static AST analysis, contract validation, and a headless Tkinter UI walkthrough harness. |
| **Cost Awareness & Budgets** | Live per-run token/dollar counter and cumulative evaluation budget guards enforcing hard stops (\$0.15/run, \$0.85 cumulative). |

---

## 2. Pipeline Architecture

```text
Architecture_Documentation.md + Architecture_View.md
        |
   [1 PARSE]      -> spec.json (requirements, use cases, classes, states, sequences)
        |
   [2 CONTRACT]   -> contract.json (files, classes, signatures, smoke steps)
        |
   [3 IMPLEMENT]  -> one file per call, with a signature ledger of files already written
        |
   [4 VERIFY]     -> V1 to V8: compile, contract, call-site, Tk collisions, stdlib, unittest, UI walkthrough
        |
   pass? -- no --> [5 REPAIR] (model uses read_file, write_file, list_dir, run_checks; max 3 rounds)
        |                       |
       yes <---------------------
        |
   [6 REPORT]     -> run_report.md (plan, checks, repairs, traceability, cost)
```

### The 8 Verification Checks (V1 to V8)
- **V1 (Existence)**: All files declared in `contract.json` exist and are non-empty.
- **V2 (Syntax)**: `py_compile` passes cleanly on every generated Python file.
- **V3 (Contract Conformance)**: Every class, method, and attribute declared in the contract exists with matching signatures.
- **V4 (Call-Site Verification)**: Static cross-file AST check ensuring calls (e.g. `self.engine.method()`) resolve to valid methods and attributes are not called as functions.
- **V5 (Tkinter Collision Check)**: Custom methods on Tkinter widget subclasses do not shadow internal Tkinter names (`update`, `config`, `grid`, `pack`, `focus`, `after`).
- **V6 (Dependency Confinement)**: Standard library and local module imports only; warns against unbundled dependencies.
- **V7 (Automated Unit Tests)**: `unittest discover` runs in the project folder with strict timeout.
- **V8 (UI Walkthrough Harness)**: Headless Tkinter runner executes all `smoke_steps` across every screen, trapping callback exceptions.

---

## 3. Project Structure

```text
deepseek-code-agent/
  README.md               # Project architecture and reference mapping
  DECISIONS.md            # Locked decisions, probe results, and pricing
  requirements.txt        # pyinstaller only (build requirement)
  build.ps1               # PyInstaller automated build script
  src/
    app.py                # Tkinter GUI entrypoint and task coordinator
    parser.py             # Markdown and PlantUML parser -> spec.json
    llm.py                # DeepSeek API client with dual budget guards & caching
    agent.py              # Generation pipeline and tool-driven repair loop
    verify.py             # V1-V8 static and runtime verification checks
    harness.py            # Headless Tkinter UI walkthrough harness
  tests/                  # Verification test suite & bug fixtures
  examples/
    inputs/               # Space Fractions specification & views
    inputs_second/        # Second evaluation input
  runs/                   # Untouched raw agent output directories
  docs/                   # Architecture diagrams and documentation
```

---

## 4. Setup & Building

### Prerequisites
- Windows 10/11
- 64-bit Python 3.12+ (standard python.org distribution)

### Virtual Environment Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Building Standalone Executable
```powershell
.\build.ps1
```
The compiled application is generated in `dist/CodeAgent/CodeAgent.exe`.
