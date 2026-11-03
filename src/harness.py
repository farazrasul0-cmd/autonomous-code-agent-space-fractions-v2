# src/harness.py - UI Walkthrough Harness executing smoke steps in isolated subprocess
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Subprocess worker script executed inside the target run_dir environment
HARNESS_WORKER_SCRIPT = """
import sys
import os
import json
import traceback

def run():
    run_dir = sys.argv[1]
    contract_file = sys.argv[2]
    out_file = sys.argv[3]

    if run_dir not in sys.path:
        sys.path.insert(0, run_dir)

    with open(contract_file, "r", encoding="utf-8") as f:
        contract = json.load(f)

    # 1. Initialize Tkinter with headless display check
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        # Headless CI or display unavailable
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"status": "skipped", "reason": "no display", "error": str(e)}, f)
        sys.exit(0)

    callback_errors = []
    def callback_error_handler(exc_type, exc_val, exc_tb):
        callback_errors.append("".join(traceback.format_exception(exc_type, exc_val, exc_tb)))

    root.report_callback_exception = callback_error_handler

    # 2. Import main and create_app(root)
    try:
        import main
        if not hasattr(main, "create_app"):
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"status": "fail", "error": "main.py does not define create_app(root)"}, f)
            sys.exit(1)

        app = main.create_app(root)
        root.update()
    except Exception as e:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"status": "fail", "stage": "create_app", "error": str(e), "traceback": traceback.format_exc()}, f)
        sys.exit(1)

    # 3. Execute smoke steps in order
    smoke_steps = contract.get("smoke_steps", [])
    steps_executed = 0

    for idx, step in enumerate(smoke_steps):
        call_name = step.get("call")
        args = step.get("args", [])
        if call_name == "create_app":
            continue

        if not hasattr(app, call_name):
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"status": "fail", "step": call_name, "error": f"App has no method '{call_name}'"}, f)
            sys.exit(1)

        try:
            method = getattr(app, call_name)
            method(*args)
            root.update()
            steps_executed += 1
        except Exception as e:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"status": "fail", "step": call_name, "error": str(e), "traceback": traceback.format_exc()}, f)
            sys.exit(1)

        if callback_errors:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"status": "fail", "step": call_name, "error": "Callback exception occurred", "traceback": callback_errors[0]}, f)
            sys.exit(1)

    try:
        root.destroy()
    except Exception:
        pass

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"status": "pass", "steps_run": steps_executed}, f)
    sys.exit(0)

if __name__ == "__main__":
    run()
"""


def run_harness(run_dir: str | Path, contract: dict, timeout: int = 35) -> dict:
    """Run UI smoke walkthrough harness in an isolated subprocess with watchdog timer."""
    run_dir = Path(run_dir).resolve()

    with tempfile.TemporaryDirectory(prefix="harness_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        worker_script = tmp_path / "worker.py"
        contract_file = tmp_path / "contract.json"
        out_file = tmp_path / "result.json"

        worker_script.write_text(HARNESS_WORKER_SCRIPT, encoding="utf-8")
        contract_file.write_text(json.dumps(contract), encoding="utf-8")

        is_frozen = getattr(sys, "frozen", False)
        if is_frozen:
            cmd = [sys.executable, "--run-script", str(worker_script), str(run_dir), str(contract_file), str(out_file)]
        else:
            cmd = [sys.executable, str(worker_script), str(run_dir), str(contract_file), str(out_file)]

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(run_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creationflags
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "fail",
                "error": f"UI harness timed out after {timeout} seconds (watchdog triggered)"
            }

        if out_file.exists():
            try:
                with open(out_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                return {"status": "fail", "error": f"Failed reading harness output: {e}"}

        # If result file not produced, report process failure
        err_msg = proc.stderr or proc.stdout or f"Worker exited with code {proc.returncode}"
        return {
            "status": "fail",
            "error": f"Harness worker terminated without result file: {err_msg[:400]}"
        }
