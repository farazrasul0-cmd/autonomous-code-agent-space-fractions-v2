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
import re

dialog_texts = []

def collect_ui(root):
    texts, classes = [], set()
    def walk(w):
        try:
            cls = w.winfo_class()
        except Exception:
            return
        classes.add(cls)
        try:
            if cls in ("Label", "Button", "TLabel", "TButton", "Checkbutton", "Radiobutton", "Message", "Menubutton"):
                val = ""
                try:
                    name = str(w.cget("textvariable"))
                    if name:
                        val = w.tk.globalgetvar(name)
                except Exception:
                    val = ""
                texts.append(str(val) if val else str(w.cget("text")))
            elif cls == "Text":
                texts.append(w.get("1.0", "end"))
            elif cls == "Canvas":
                for item in w.find_all():
                    if w.type(item) == "text":
                        texts.append(str(w.itemcget(item, "text")))
        except Exception:
            pass
        try:
            for c in w.winfo_children():
                walk(c)
        except Exception:
            pass
    walk(root)
    return chr(10).join(texts + dialog_texts), classes

history = []

def check_expect(step, root):
    exp_text = step.get("expect_text")
    exp_cls = step.get("expect_widgets_any")
    exp_ever = step.get("expect_ever")
    if not exp_text and not exp_cls and not exp_ever:
        return None
    txt, classes = collect_ui(root)
    history.append(txt)
    if exp_ever and not any(re.search(p, chr(10).join(history), re.I) for p in exp_ever):
        return "expected feedback matching %s at least once across the answer steps, but never saw it. Last screen: %s" % (exp_ever, txt[:300].replace(chr(10), " | "))
    if exp_text and not any(re.search(p, txt, re.I) for p in exp_text):
        return "expected visible text matching %s but the screen showed: %s" % (exp_text, txt[:300].replace(chr(10), " | "))
    if exp_cls and not (set(exp_cls) & classes):
        return "expected an input widget (one of %s) but found only: %s" % (exp_cls, sorted(classes))
    return None

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

    # Neutralize modal dialogs so smoke steps can never block on user input.
    # Without this, a generated end_game() that calls messagebox.showinfo("Game Over")
    # blocks forever and the 35-second watchdog reports a false V8 failure.
    try:
        import tkinter.messagebox as mb
        import tkinter.simpledialog as sd
        import tkinter.filedialog as fd
        def _rec_ok(*a, **k):
            dialog_texts.append(" ".join(str(x) for x in a))
            return "ok"
        def _rec_yes(*a, **k):
            dialog_texts.append(" ".join(str(x) for x in a))
            return True
        def _rec_ask(*a, **k):
            dialog_texts.append(" ".join(str(x) for x in a))
            return "yes"
        mb.showinfo = mb.showwarning = mb.showerror = _rec_ok
        mb.askyesno = mb.askokcancel = mb.askretrycancel = _rec_yes
        mb.askquestion = _rec_ask
        sd.askstring = lambda *a, **k: "test"
        sd.askinteger = lambda *a, **k: 1
        sd.askfloat = lambda *a, **k: 1.0
        fd.askopenfilename = fd.asksaveasfilename = lambda *a, **k: ""
    except Exception:
        pass

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
            problem = check_expect(step, root)
            if problem:
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump({"status": "fail", "step": call_name, "error": "UI expectation failed after " + call_name + ": " + problem}, f)
                sys.exit(1)
        except Exception as e:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"status": "fail", "step": call_name, "error": str(e), "traceback": traceback.format_exc()}, f)
            sys.exit(1)

        if callback_errors:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"status": "fail", "step": call_name, "error": "Callback exception occurred", "traceback": callback_errors[0]}, f)
            sys.exit(1)

    if steps_executed == 0:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(
                {"status": "fail", "stage": "smoke", "error": "No smoke steps executed (steps_executed == 0)"},
                f
            )
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


import copy
import re

EXPECT_RULES = [
    (r"end_game|game_over|finish_game", {"expect_text": ["game over", "final score"]}),
    (r"^show_(update|edit|admin|manage)", {"expect_widgets_any": ["Entry", "TEntry", "Text", "Listbox", "Treeview"]}),
    (r"submit_answer|^answer", {"expect_text": ["correct|incorrect|wrong|right|try again"]}),
]


def augment_smoke_expectations(contract: dict) -> dict:
    """Add generic behavior expectations to smoke steps, based on step names only."""
    contract = copy.deepcopy(contract)
    steps = contract.get("smoke_steps", [])
    is_answer = lambda st: re.search(r"^submit_answer|^answer", st.get("call", ""), re.I) is not None
    # Make sure at least 4 different answers are tried, so a wrong answer is very likely hit.
    if sum(1 for st in steps if is_answer(st)) < 4:
        expanded, done = [], False
        for st in steps:
            args = st.get("args", [])
            if not done and is_answer(st) and len(args) == 1 and isinstance(args[0], int) and not isinstance(args[0], bool):
                expanded.extend({"call": st["call"], "args": [i]} for i in range(4))
                done = True
            else:
                expanded.append(st)
        steps = expanded
        contract["smoke_steps"] = steps
    for step in steps:
        name = step.get("call", "")
        for pattern, expectation in EXPECT_RULES:
            if re.search(pattern, name, re.I):
                for key, value in expectation.items():
                    step.setdefault(key, value)
                break
    answer_steps = [st for st in steps if is_answer(st)]
    if len(answer_steps) >= 3:
        answer_steps[-1].setdefault("expect_ever", ["incorrect|wrong|not quite|try again|oops"])
    return contract


def run_harness(run_dir: str | Path, contract: dict, timeout: int = 35) -> dict:
    """Run UI smoke walkthrough harness in an isolated subprocess with watchdog timer."""
    run_dir = Path(run_dir).resolve()

    with tempfile.TemporaryDirectory(prefix="harness_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        worker_script = tmp_path / "worker.py"
        contract_file = tmp_path / "contract.json"
        out_file = tmp_path / "result.json"

        worker_script.write_text(HARNESS_WORKER_SCRIPT, encoding="utf-8")
        contract_file.write_text(json.dumps(augment_smoke_expectations(contract)), encoding="utf-8")

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

        scrubbed_env = {k: v for k, v in os.environ.items() if "DEEPSEEK" not in k.upper() and "API_KEY" not in k.upper()}

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