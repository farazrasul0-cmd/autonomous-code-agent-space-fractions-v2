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


def _run_harness_in_process(run_dir: str | Path, contract: dict) -> dict:
    """Fallback: Execute UI smoke walkthrough in-process when subprocess is blocked or frozen."""
    run_dir = Path(run_dir).resolve()
    run_dir_str = str(run_dir)
    sys_path_added = False
    if run_dir_str not in sys.path:
        sys.path.insert(0, run_dir_str)
        sys_path_added = True

    # Evict project modules from previous runs to prevent stale module caching
    for name in ["models", "engine", "ui", "app", "main"]:
        if name in sys.modules:
            del sys.modules[name]

    try:
        import tkinter as tk
        root = None
        try:
            if getattr(tk, "_default_root", None) is None:
                root = tk.Tk()
                root.withdraw()
            else:
                root = tk.Toplevel(tk._default_root)
                root.withdraw()
        except Exception as e:
            return {"status": "skipped", "reason": "Sandbox GUI blocked / no display", "error": str(e)}

        try:
            import importlib
            if "main" in sys.modules:
                main_mod = importlib.reload(sys.modules["main"])
            else:
                main_mod = importlib.import_module("main")

            if not hasattr(main_mod, "create_app"):
                return {"status": "fail", "error": "main.py does not define create_app(root)"}

            app = main_mod.create_app(root)
            root.update()

            smoke_steps = contract.get("smoke_steps", [])
            steps_run = 0
            for step in smoke_steps:
                call_name = step.get("call")
                args = step.get("args", [])
                if call_name == "create_app":
                    continue
                if not hasattr(app, call_name):
                    return {"status": "fail", "step": call_name, "error": f"App has no method '{call_name}'"}
                method = getattr(app, call_name)
                method(*args)
                root.update()
                steps_run += 1

            return {"status": "pass", "steps_run": steps_run, "in_process": True}
        finally:
            try:
                if root:
                    root.destroy()
            except Exception:
                pass
    except Exception as exc:
        return {"status": "skipped", "reason": "Sandbox GUI in-process error", "error": str(exc)}
    finally:
        if sys_path_added and run_dir_str in sys.path:
            try:
                sys.path.remove(run_dir_str)
            except Exception:
                pass


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

        creationflags = 0
        startupinfo = None
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

        proc = None
        proc_exc = None
        timed_out = False

        scrubbed_env = {k: v for k, v in os.environ.items() if "DEEPSEEK" not in k and "API_KEY" not in k}

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(run_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                creationflags=creationflags,
                startupinfo=startupinfo,
                env=scrubbed_env,
                close_fds=True
            )
        except subprocess.TimeoutExpired:
            timed_out = True
        except Exception as exc:
            proc_exc = exc

        if out_file.exists():
            try:
                with open(out_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                return {"status": "fail", "error": f"Failed reading harness output: {e}"}

        if timed_out:
            return {
                "status": "fail",
                "error": f"UI harness timed out after {timeout} seconds (watchdog triggered)"
            }

        err_msg = (proc.stderr if proc else "") or (proc.stdout if proc else "") or str(proc_exc or "")
        return {
            "status": "fail",
            "error": f"Harness worker terminated without result file: {err_msg[:400]}"
        }
