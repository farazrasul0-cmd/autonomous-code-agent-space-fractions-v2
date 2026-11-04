# Smart To-Do List

Desktop application implementation synthesized by DeepSeek Code Agent.

## Architecture Overview
- **Target Platform**: Windows Standalone Desktop Application (Python 3.12 & Tkinter).
- **Dependencies**: Python Standard Library ONLY (zero external pip packages).
- **Modules**:
- `models.py`: Domain classes Task and TaskManager
- `app.py`: Tkinter GUI application class App
- `main.py`: Entry point with create_app function

## Running the Application
```bash
python main.py
```

## Running the Smoke Test Suite
```bash
python -m unittest discover -s tests -v
```

What this test suite checks: tests/test_game.py is a smoke test suite. Each test
constructs a domain class with synthetic arguments and asserts the object is created
successfully. It does not exercise gameplay or business logic.

What verifies behavior: The behavioral verification is the UI smoke walkthrough
harness (V8 in run_report.md), which drives the running Tkinter application through
the contract's declared smoke_steps sequence in an isolated subprocess. See
run_report.md → section 3 → V8 for the behavioral verification result.
