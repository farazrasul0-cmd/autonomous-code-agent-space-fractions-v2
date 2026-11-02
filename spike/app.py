# spike/app.py - Frozen executable spike with dispatcher and process runner
import os
import sys
import runpy
import subprocess

# ---------------------------------------------------------------------------
# 1. DISPATCHER: MUST execute before ANY GUI imports
# ---------------------------------------------------------------------------
if len(sys.argv) > 1:
    flag = sys.argv[1]
    if flag == "--run-script":
        if len(sys.argv) < 3:
            sys.stderr.write("Error: --run-script requires script path\n")
            sys.exit(1)
        script_path = os.path.abspath(sys.argv[2])
        script_dir = os.path.dirname(script_path)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        sys.argv = [script_path] + sys.argv[3:]
        try:
            runpy.run_path(script_path, run_name="__main__")
            sys.exit(0)
        except SystemExit as se:
            sys.exit(se.code)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            sys.exit(1)

    elif flag == "--run-module":
        if len(sys.argv) < 3:
            sys.stderr.write("Error: --run-module requires module name\n")
            sys.exit(1)
        mod_name = sys.argv[2]
        sys.argv = [mod_name] + sys.argv[3:]
        if mod_name == "unittest":
            import unittest
            try:
                unittest.main(module=None)
                sys.exit(0)
            except SystemExit as se:
                sys.exit(se.code)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            try:
                runpy.run_module(mod_name, run_name="__main__", alter_sys=True)
                sys.exit(0)
            except SystemExit as se:
                sys.exit(se.code)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                sys.exit(1)

# ---------------------------------------------------------------------------
# 2. RUNNERS & HELPERS
# ---------------------------------------------------------------------------
CREATE_NO_WINDOW = 0x08000000

def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def ensure_sample_files(base_dir):
    sample_dir = os.path.join(base_dir, "sample")
    os.makedirs(sample_dir, exist_ok=True)

    test_file = os.path.join(sample_dir, "test_sample.py")
    if not os.path.exists(test_file):
        with open(test_file, "w", encoding="utf-8") as f:
            f.write('''import unittest

class TestMathAndLogic(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(21 + 21, 42)

    def test_fractions(self):
        import fractions
        f = fractions.Fraction(1, 2) + fractions.Fraction(1, 4)
        self.assertEqual(f, fractions.Fraction(3, 4))

    def test_dataclass(self):
        import dataclasses
        @dataclasses.dataclass
        class Item:
            name: str
            val: int
        item = Item("test", 10)
        self.assertEqual(item.name, "test")

if __name__ == "__main__":
    unittest.main()
''')

    script_file = os.path.join(sample_dir, "script_sample.py")
    if not os.path.exists(script_file):
        with open(script_file, "w", encoding="utf-8") as f:
            f.write('''import sys
import random
import tkinter.messagebox

hidden_modules = [
    "random", "dataclasses", "enum", "fractions", "uuid", "math",
    "typing", "itertools", "functools", "collections", "datetime",
    "pathlib", "copy", "tkinter", "tkinter.ttk", "tkinter.messagebox",
    "tkinter.simpledialog", "tkinter.font", "unittest", "unittest.mock"
]

imported = []
for mod in hidden_modules:
    __import__(mod)
    imported.append(mod)

num = random.randint(100, 999)
print(f"SUCCESS: random={num}")
print(f"SUCCESS: tkinter.messagebox={tkinter.messagebox.__name__}")
print(f"SUCCESS: all {len(imported)} hidden imports loaded successfully: {', '.join(imported)}")
sys.stdout.flush()
''')

    game_file = os.path.join(sample_dir, "game_sample.py")
    if not os.path.exists(game_file):
        with open(game_file, "w", encoding="utf-8") as f:
            f.write('''import sys
import random
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("Space Fractions - Detached Sample Game")
root.geometry("380x220")
root.configure(bg="#1a1a2e")

title_lbl = tk.Label(
    root,
    text="Detached Game Running",
    font=("Arial", 14, "bold"),
    fg="#e94560",
    bg="#1a1a2e"
)
title_lbl.pack(pady=15)

info_lbl = tk.Label(
    root,
    text="Independent Process.\\nSurvives parent window closure.",
    font=("Arial", 10),
    fg="#ffffff",
    bg="#1a1a2e"
)
info_lbl.pack(pady=5)

def on_click():
    n = random.randint(1, 10)
    messagebox.showinfo("Game Event", f"Fraction solved: {n}/10")

btn = tk.Button(
    root,
    text="Interactive Test Button",
    command=on_click,
    bg="#0f3460",
    fg="#ffffff",
    font=("Arial", 10, "bold"),
    padx=10,
    pady=5
)
btn.pack(pady=15)

if "--auto-close" in sys.argv:
    idx = sys.argv.index("--auto-close")
    ms = int(sys.argv[idx + 1])
    root.after(ms, root.destroy)

root.mainloop()
''')

    return sample_dir

def run_py_module(args, cwd=None, timeout=30):
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        cmd = [sys.executable, "--run-module"] + args
    else:
        cmd = [sys.executable, "-m"] + args

    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW
    )

def run_py_script(script_path, args=None, cwd=None, timeout=30):
    if args is None:
        args = []
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        cmd = [sys.executable, "--run-script", script_path] + args
    else:
        cmd = [sys.executable, script_path] + args

    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW
    )

def launch_py_detached(script_path, args=None, cwd=None):
    if args is None:
        args = []
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        cmd = [sys.executable, "--run-script", script_path] + args
    else:
        cmd = [sys.executable, script_path] + args

    # Clean environment to prevent PyInstaller parent-child lockup
    env = dict(os.environ)
    # Detached launch: strictly NO PIPES (DEVNULL) to avoid handle inheritance hang
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )

# ---------------------------------------------------------------------------
# 3. CLI SELF-TEST MODE (--test-spike)
# ---------------------------------------------------------------------------
if len(sys.argv) > 1 and sys.argv[1] == "--test-spike":
    base_dir = get_base_dir()
    sample_dir = ensure_sample_files(base_dir)
    print("=== EXECUTING SPIKE SELF-TEST ===")
    print(f"Base Directory: {base_dir}")
    print(f"Frozen mode: {getattr(sys, 'frozen', False)}")

    # 1. Unittest
    print("\n[1/3] Testing unittest discover...")
    res_test = run_py_module(["unittest", "discover", "-s", sample_dir], cwd=sample_dir)
    print(f"Exit code: {res_test.returncode}")
    print(f"Stdout:\n{res_test.stdout}")
    print(f"Stderr:\n{res_test.stderr}")
    assert res_test.returncode == 0, "Unittest discover failed"

    # 2. Script
    print("\n[2/3] Testing script with 20 hidden imports...")
    script_path = os.path.join(sample_dir, "script_sample.py")
    res_script = run_py_script(script_path, cwd=sample_dir)
    print(f"Exit code: {res_script.returncode}")
    print(f"Output:\n{res_script.stdout}")
    if res_script.stderr:
        print(f"Stderr:\n{res_script.stderr}")
    assert res_script.returncode == 0, "Script execution failed"
    assert "SUCCESS: all 20 hidden imports loaded successfully" in res_script.stdout

    # 3. Detached Tk game launch
    print("\n[3/3] Testing detached Tk game launch...")
    game_path = os.path.join(sample_dir, "game_sample.py")
    # Launch with --auto-close 2000 ms so it runs detached and shuts itself down cleanly
    proc = launch_py_detached(game_path, args=["--auto-close", "2000"], cwd=sample_dir)
    print(f"Launched detached game process PID: {proc.pid}")
    assert proc.pid > 0, "Failed to launch detached process"

    print("\n=== ALL SPIKE CHECKS PASSED SUCCESSFULLY ===")
    sys.exit(0)

# ---------------------------------------------------------------------------
# 4. GUI IMPLEMENTATION
# ---------------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class SpikeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Frozen Executable Spike - CodeAgent")
        self.root.geometry("640x480")
        self.root.minsize(500, 350)

        self.base_dir = get_base_dir()
        self.sample_dir = ensure_sample_files(self.base_dir)

        self._build_ui()

    def _build_ui(self):
        header_frame = tk.Frame(self.root, bg="#2c3e50", padx=10, pady=10)
        header_frame.pack(fill="x")

        status_text = "FROZEN BUILD" if getattr(sys, "frozen", False) else "SOURCE SCRIPT"
        title_lbl = tk.Label(
            header_frame,
            text=f"Phase 2 Spike: Dispatcher & Process Verification ({status_text})",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_lbl.pack(anchor="w")

        info_lbl = tk.Label(
            header_frame,
            text=f"Base: {self.base_dir}",
            font=("Consolas", 8),
            fg="#bdc3c7",
            bg="#2c3e50"
        )
        info_lbl.pack(anchor="w")

        btn_frame = tk.Frame(self.root, padx=10, pady=10)
        btn_frame.pack(fill="x")

        self.btn_unittest = ttk.Button(btn_frame, text="1. Run Unittest", command=self.on_unittest)
        self.btn_unittest.pack(side="left", padx=5)

        self.btn_script = ttk.Button(btn_frame, text="2. Run Script (20 Imports)", command=self.on_script)
        self.btn_script.pack(side="left", padx=5)

        self.btn_game = ttk.Button(btn_frame, text="3. Launch Tk Game (Detached)", command=self.on_game)
        self.btn_game.pack(side="left", padx=5)

        self.btn_clear = ttk.Button(btn_frame, text="Clear Log", command=self.on_clear)
        self.btn_clear.pack(side="right", padx=5)

        log_frame = tk.LabelFrame(self.root, text="Process Execution Log", padx=5, pady=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.txt_log = scrolledtext.ScrolledText(log_frame, font=("Consolas", 9), wrap="word")
        self.txt_log.pack(fill="both", expand=True)

        self.log(f"Spike ready. Mode: {status_text}")
        self.log(f"Executable: {sys.executable}")
        self.log("Click any button to test process dispatching.\n")

    def log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    def on_clear(self):
        self.txt_log.delete("1.0", tk.END)

    def on_unittest(self):
        self.log(">>> Running 'unittest discover'...")
        try:
            res = run_py_module(["unittest", "discover", "-s", self.sample_dir], cwd=self.sample_dir)
            if res.returncode == 0:
                self.log(f"[SUCCESS] Unittest completed (exit {res.returncode}):\n{res.stderr.strip() or res.stdout.strip()}")
            else:
                self.log(f"[FAILED] Unittest returned exit code {res.returncode}:\n{res.stderr or res.stdout}")
        except Exception as e:
            self.log(f"[ERROR] Exception running unittest: {e}")

    def on_script(self):
        self.log(">>> Running sample script (importing random, tkinter.messagebox, and 20 hidden imports)...")
        script_path = os.path.join(self.sample_dir, "script_sample.py")
        try:
            res = run_py_script(script_path, cwd=self.sample_dir)
            if res.returncode == 0:
                self.log(f"[SUCCESS] Script executed cleanly:\n{res.stdout.strip()}")
            else:
                self.log(f"[FAILED] Script failed (exit {res.returncode}):\n{res.stderr or res.stdout}")
        except Exception as e:
            self.log(f"[ERROR] Exception running script: {e}")

    def on_game(self):
        self.log(">>> Launching detached Tk game window...")
        game_path = os.path.join(self.sample_dir, "game_sample.py")
        try:
            proc = launch_py_detached(game_path, cwd=self.sample_dir)
            self.log(f"[SUCCESS] Detached process started with PID: {proc.pid}")
            self.log("Notice: You can close this Spike window now and the game window will remain active!")
        except Exception as e:
            self.log(f"[ERROR] Failed to launch detached game: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SpikeApp(root)
    root.mainloop()
