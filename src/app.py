# src/app.py - Tkinter Desktop Front-End for Autonomous Software Synthesis
import os
import sys
import re
import json
import time
import queue
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# Ensure repo root is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.parser import parse_architecture
from src.agent import (
    validate_contract,
    implement_project,
    repair_project,
    generate_run_report,
    ContractError
)
from src.verify import run_all_checks
from src.llm import (
    Client,
    Budget,
    Cache,
    get_api_key,
    models,
    LLMError,
    BudgetExceededError
)

_KEY_RE = re.compile(r"sk-[A-Za-z0-9\-]{8,}")


def sanitize_log(text: str, current_key: str = None) -> str:
    """Ensure API keys never appear in GUI logs or text displays."""
    if text is None:
        return ""
    s = _KEY_RE.sub("[REDACTED_API_KEY]", str(text))
    if current_key and len(current_key.strip()) >= 6:
        s = s.replace(current_key.strip(), "[REDACTED_API_KEY]")
    return s


def get_current_cumulative_spend(base_runs_dir: str | Path = "runs") -> float:
    """Compute cumulative spend across all previous runs using run_log.jsonl as source of truth."""
    baseline = 0.020315  # Phase 1-5 fixed spend recorded in DECISIONS.md
    runs_path = Path(base_runs_dir)
    logged_spend = 0.0
    if runs_path.exists():
        for log_file in runs_path.glob("*/run_log.jsonl"):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            logged_spend += float(data.get("cost", 0.0))
            except Exception:
                pass
    return baseline + logged_spend


def launch_game(main_path: str | Path) -> subprocess.Popen:
    """Launch generated desktop application in a detached, independent process.
    
    Adheres strictly to Master Plan detached execution rules:
      - Frozen (PyInstaller/exe): [sys.executable, '--run-script', str(main_path)]
      - Source execution: [sys.executable, str(main_path)]
      - Creation flags: CREATE_NEW_PROCESS_GROUP on Windows
      - Independent streams: DEVNULL for stdin, stdout, stderr with close_fds=True
    """
    target = Path(main_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"Entrypoint file not found: {target}")

    run_dir = target.parent

    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "--run-script", str(target)]
    else:
        cmd = [sys.executable, str(target)]

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        cmd,
        cwd=str(run_dir),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creationflags
    )
    return proc


class App(tk.Tk):
    """Main Tkinter GUI Front-End for DeepSeek Code Agent."""

    def __init__(self, headless: bool = False):
        super().__init__()
        self.title("DeepSeek Code Agent - Space Fractions")
        self.geometry("920x820")
        self.minsize(820, 680)

        # Threading and communication
        self.queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker_thread = None

        # State tracking
        self.current_run_dir = None
        self.current_main_py = None
        self.cumulative_spend = get_current_cumulative_spend()
        self.run_spend = 0.0

        # Colors & Styling
        self._setup_styles()

        # Build UI layout
        self._build_ui()

        # Start queue poller
        self.after(100, self._poll_queue)

        if headless:
            self.withdraw()

    def _setup_styles(self):
        """Define styling constants for progress stages and elements."""
        self.STAGE_COLORS = {
            "pending": {"bg": "#E9ECEF", "fg": "#495057", "text": "Pending"},
            "running": {"bg": "#FFF3CD", "fg": "#856404", "text": "In Progress..."},
            "complete": {"bg": "#D4EDDA", "fg": "#155724", "text": "PASSED"},
            "failed": {"bg": "#F8D7DA", "fg": "#721C24", "text": "FAILED"},
            "skipped": {"bg": "#E2E3E5", "fg": "#6C757D", "text": "Skipped"}
        }

    def _build_ui(self):
        """Construct the full Tkinter layout."""
        # Main container with padding
        container = ttk.Frame(self, padding="12")
        container.pack(fill=tk.BOTH, expand=True)

        # 1. Header
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_lbl = tk.Label(
            header_frame,
            text="DeepSeek Code Agent",
            font=("Segoe UI", 16, "bold"),
            fg="#1A365D"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Autonomous Software Synthesis & Multi-Turn Verification Engine",
            font=("Segoe UI", 9, "italic"),
            fg="#4A5568"
        )
        subtitle_lbl.pack(anchor=tk.W)

        # 2. Configuration Frame
        cfg_frame = ttk.LabelFrame(container, text="Configuration & Inputs", padding="10")
        cfg_frame.pack(fill=tk.X, pady=(0, 10))

        # API Key Row
        key_lbl = ttk.Label(cfg_frame, text="DeepSeek API Key:", font=("Segoe UI", 9, "bold"))
        key_lbl.grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)

        self.key_var = tk.StringVar()
        env_key = get_api_key()
        if env_key:
            self.key_var.set(env_key)

        self.key_entry = ttk.Entry(cfg_frame, textvariable=self.key_var, show="*", width=42)
        self.key_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=4)

        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_cb = ttk.Checkbutton(
            cfg_frame,
            text="Show",
            variable=self.show_key_var,
            command=self._toggle_key_visibility
        )
        self.show_key_cb.grid(row=0, column=2, padx=5, pady=4)

        self.test_key_btn = ttk.Button(cfg_frame, text="Test Key", command=self._test_api_key)
        self.test_key_btn.grid(row=0, column=3, padx=5, pady=4)

        self.key_status_lbl = ttk.Label(cfg_frame, text="Loaded from environment" if env_key else "Key required", font=("Segoe UI", 8, "italic"))
        self.key_status_lbl.grid(row=0, column=4, sticky=tk.W, padx=5, pady=4)

        # Architecture Documentation Picker Row
        doc_lbl = ttk.Label(cfg_frame, text="Architecture Doc:")
        doc_lbl.grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)

        default_doc = "Architecture_Documentation.md" if Path("Architecture_Documentation.md").exists() else ""
        self.doc_var = tk.StringVar(value=default_doc)
        self.doc_entry = ttk.Entry(cfg_frame, textvariable=self.doc_var, width=54)
        self.doc_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=4)

        self.doc_btn = ttk.Button(cfg_frame, text="Browse...", command=self._browse_doc)
        self.doc_btn.grid(row=1, column=3, padx=5, pady=4)

        # Architecture View Picker Row
        view_lbl = ttk.Label(cfg_frame, text="Architecture View:")
        view_lbl.grid(row=2, column=0, sticky=tk.W, padx=5, pady=4)

        default_view = "Architecture_View.md" if Path("Architecture_View.md").exists() else ""
        self.view_var = tk.StringVar(value=default_view)
        self.view_entry = ttk.Entry(cfg_frame, textvariable=self.view_var, width=54)
        self.view_entry.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=4)

        self.view_btn = ttk.Button(cfg_frame, text="Browse...", command=self._browse_view)
        self.view_btn.grid(row=2, column=3, padx=5, pady=4)

        # Output Folder Row
        out_lbl = ttk.Label(cfg_frame, text="Output Directory:")
        out_lbl.grid(row=3, column=0, sticky=tk.W, padx=5, pady=4)

        self.out_var = tk.StringVar(value="runs")
        self.out_entry = ttk.Entry(cfg_frame, textvariable=self.out_var, width=54)
        self.out_entry.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=5, pady=4)

        self.out_btn = ttk.Button(cfg_frame, text="Browse...", command=self._browse_out)
        self.out_btn.grid(row=3, column=3, padx=5, pady=4)

        # 3. Task Description Frame
        task_frame = ttk.LabelFrame(container, text="Task Description", padding="10")
        task_frame.pack(fill=tk.X, pady=(0, 10))

        self.task_text = tk.Text(task_frame, height=3, wrap=tk.WORD, font=("Segoe UI", 9))
        self.task_text.pack(fill=tk.X, expand=True)
        default_task = (
            "Synthesize a clean, self-contained desktop application adhering strictly to the architecture specifications, "
            "PlantUML class/state diagrams, and verification contracts. Ensure zero external dependencies and 100% Tkinter compatibility."
        )
        self.task_text.insert("1.0", default_task)

        # 4. Progress Indicators & Controls Frame
        prog_frame = ttk.LabelFrame(container, text="Synthesis Progress & Controls", padding="10")
        prog_frame.pack(fill=tk.X, pady=(0, 10))

        # 5 Stage Cards
        cards_frame = ttk.Frame(prog_frame)
        cards_frame.pack(fill=tk.X, pady=(0, 10))
        cards_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.stage_names = ["Parse", "Contract", "Implement", "Verify", "Repair"]
        self.stage_widgets = {}

        for idx, sname in enumerate(self.stage_names):
            card = tk.Frame(cards_frame, relief="ridge", borderwidth=2, bg="#E9ECEF", padx=6, pady=6)
            card.grid(row=0, column=idx, padx=4, sticky="nsew")

            title = tk.Label(card, text=f"{idx+1}. {sname}", font=("Segoe UI", 9, "bold"), bg="#E9ECEF", fg="#212529")
            title.pack(anchor=tk.CENTER)

            status = tk.Label(card, text="Pending", font=("Segoe UI", 8), bg="#E9ECEF", fg="#495057")
            status.pack(anchor=tk.CENTER)

            self.stage_widgets[sname.lower()] = {
                "frame": card,
                "title": title,
                "status": status
            }

        # Budget & Controls Row
        ctrl_frame = ttk.Frame(prog_frame)
        ctrl_frame.pack(fill=tk.X)

        self.start_btn = tk.Button(
            ctrl_frame,
            text="Start Run",
            command=self._start_run,
            bg="#28A745",
            fg="white",
            activebackground="#218838",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=4,
            relief="raised"
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.cancel_btn = tk.Button(
            ctrl_frame,
            text="Cancel",
            command=self._cancel_run,
            state=tk.DISABLED,
            bg="#DC3545",
            fg="white",
            activebackground="#C82333",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=4,
            relief="raised"
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Cost Display
        self.cost_lbl = tk.Label(
            ctrl_frame,
            text=self._format_cost_text(0.0, self.cumulative_spend),
            font=("Consolas", 10, "bold"),
            fg="#0D6EFD"
        )
        self.cost_lbl.pack(side=tk.RIGHT, padx=5)

        # 5. Live Scrolled Log Frame
        log_frame = ttk.LabelFrame(container, text="Live Execution Log (API Keys Redacted)", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            height=10,
            font=("Consolas", 9),
            bg="#1E1E1E",
            fg="#D4D4D4",
            insertbackground="#FFFFFF",
            selectbackground="#264F78"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)

        # 6. Action / Completion Buttons Frame
        act_frame = ttk.Frame(container)
        act_frame.pack(fill=tk.X, pady=(0, 5))

        self.open_folder_btn = tk.Button(
            act_frame,
            text="Open Run Folder",
            command=self._open_run_folder,
            state=tk.DISABLED,
            bg="#6C757D",
            fg="white",
            activebackground="#5A6268",
            activeforeground="white",
            font=("Segoe UI", 9),
            padx=10,
            pady=3
        )
        self.open_folder_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.launch_game_btn = tk.Button(
            act_frame,
            text="Launch Generated Game",
            command=self._launch_game,
            state=tk.DISABLED,
            bg="#0D6EFD",
            fg="white",
            activebackground="#0B5ED7",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3
        )
        self.launch_game_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.status_var = tk.StringVar(value="Ready to synthesize.")
        self.status_lbl = ttk.Label(act_frame, textvariable=self.status_var, font=("Segoe UI", 9, "italic"))
        self.status_lbl.pack(side=tk.RIGHT, padx=5)

    def _format_cost_text(self, run_spent: float, total_spent: float) -> str:
        """Format cost text with run cap ($0.15) and total cap ($0.85)."""
        return f"Run: ${run_spent:.6f} / $0.150000   |   Cumulative: ${total_spent:.6f} / $0.850000"

    def _toggle_key_visibility(self):
        """Toggle masked visibility of API key entry."""
        if self.show_key_var.get():
            self.key_entry.configure(show="")
        else:
            self.key_entry.configure(show="*")

    def _browse_doc(self):
        """File picker for Architecture Documentation markdown."""
        path = filedialog.askopenfilename(
            title="Select Architecture Documentation",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if path:
            self.doc_var.set(path)

    def _browse_view(self):
        """File picker for Architecture View markdown."""
        path = filedialog.askopenfilename(
            title="Select Architecture View",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if path:
            self.view_var.set(path)

    def _browse_out(self):
        """Directory picker for output folder."""
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.out_var.set(path)

    def _test_api_key(self):
        """Asynchronously test the DeepSeek API key."""
        key = self.key_var.get().strip() or get_api_key()
        if not key:
            messagebox.showwarning("API Key Required", "Please enter a DeepSeek API key or set DEEPSEEK_API_KEY.")
            return

        self.test_key_btn.configure(state=tk.DISABLED, text="Testing...")
        self.key_status_lbl.configure(text="Connecting to DeepSeek API...", fg="#856404")

        def _worker():
            try:
                available_models = models(api_key=key)
                self.queue.put({
                    "type": "key_test_result",
                    "success": True,
                    "message": f"Connection verified! Models found: {len(available_models)}"
                })
            except Exception as e:
                self.queue.put({
                    "type": "key_test_result",
                    "success": False,
                    "message": f"Test failed: {sanitize_log(str(e), key)}"
                })

        threading.Thread(target=_worker, daemon=True).start()

    def update_stage(self, stage_name: str, status_key: str):
        """Update a stage indicator widget's background, foreground, and status text."""
        stage_key = stage_name.lower()
        if stage_key not in self.stage_widgets:
            return

        meta = self.STAGE_COLORS.get(status_key, self.STAGE_COLORS["pending"])
        card = self.stage_widgets[stage_key]["frame"]
        title = self.stage_widgets[stage_key]["title"]
        status = self.stage_widgets[stage_key]["status"]

        card.configure(bg=meta["bg"])
        title.configure(bg=meta["bg"], fg=meta["fg"])
        status.configure(bg=meta["bg"], fg=meta["fg"], text=meta["text"])

    def reset_stages(self):
        """Reset all stage indicators to Pending state."""
        for sname in self.stage_names:
            self.update_stage(sname, "pending")

    def append_log(self, text: str):
        """Append sanitized text to the scrolled log widget."""
        curr_key = self.key_var.get().strip()
        sanitized = sanitize_log(text, curr_key)
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, sanitized + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _start_run(self):
        """Validate inputs and launch background worker thread."""
        doc_path = self.doc_var.get().strip()
        view_path = self.view_var.get().strip()
        out_root = self.out_var.get().strip() or "runs"
        api_key = self.key_var.get().strip() or get_api_key()

        if not doc_path or not Path(doc_path).exists():
            messagebox.showerror("File Error", f"Architecture documentation not found:\n{doc_path}")
            return
        if not view_path or not Path(view_path).exists():
            messagebox.showerror("File Error", f"Architecture view not found:\n{view_path}")
            return
        if not api_key:
            messagebox.showerror("API Key Error", "DeepSeek API key is required. Please enter a key or set DEEPSEEK_API_KEY.")
            return

        # Prepare GUI controls for active run
        self.start_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        self.open_folder_btn.configure(state=tk.DISABLED)
        self.launch_game_btn.configure(state=tk.DISABLED)

        self.reset_stages()
        self.cancel_event.clear()
        self.run_spend = 0.0
        self.status_var.set("Synthesis in progress...")

        self.append_log("=" * 60)
        self.append_log(f"Starting synthesis run at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.append_log(f"Doc: {doc_path} | View: {view_path}")
        self.append_log("=" * 60)

        # Launch worker
        self.worker_thread = threading.Thread(
            target=self._run_worker_pipeline,
            args=(doc_path, view_path, out_root, api_key),
            daemon=True
        )
        self.worker_thread.start()

    def _cancel_run(self):
        """Signal background thread to cancel gracefully."""
        self.cancel_event.set()
        self.cancel_btn.configure(state=tk.DISABLED)
        self.status_var.set("Cancellation requested...")
        self.append_log("\n[!] Cancellation requested by user. Aborting cleanly...")

    def _run_worker_pipeline(self, doc_path: str, view_path: str, out_root: str, api_key: str):
        """Worker thread executing the 5-stage synthesis pipeline."""
        curr_cum = get_current_cumulative_spend(out_root)
        self.queue.put({"type": "cost", "run_spent": 0.0, "total_spent": curr_cum})

        try:
            # -------------------------------------------------------------
            # Stage 1: Parse
            # -------------------------------------------------------------
            if self.cancel_event.is_set():
                self.queue.put({"type": "cancelled"})
                return

            self.queue.put({"type": "stage", "stage": "parse", "status": "running"})
            self.queue.put({"type": "log", "text": "Stage 1: Parsing architecture documentation..."})

            spec, _ = parse_architecture(doc_path, view_path)

            self.queue.put({"type": "stage", "stage": "parse", "status": "complete"})
            self.queue.put({
                "type": "log",
                "text": f"Stage 1 Complete: Parsed {len(spec.get('classes', []))} classes, "
                        f"{len(spec.get('use_cases', []))} use cases. System: {spec.get('system_name')}"
            })

            # -------------------------------------------------------------
            # Stage 2: Contract
            # -------------------------------------------------------------
            if self.cancel_event.is_set():
                self.queue.put({"type": "cancelled"})
                return

            self.queue.put({"type": "stage", "stage": "contract", "status": "running"})
            self.queue.put({"type": "log", "text": "Stage 2: Loading & validating frozen contract.json..."})

            contract_file = repo_root / "contract.json"
            if not contract_file.exists():
                raise FileNotFoundError("contract.json not found in repository root")

            with open(contract_file, "r", encoding="utf-8") as f:
                contract = json.load(f)

            problems = validate_contract(contract, spec)
            if problems:
                self.queue.put({"type": "stage", "stage": "contract", "status": "failed"})
                self.queue.put({"type": "error", "message": f"Contract validation failed: {problems}"})
                return

            self.queue.put({"type": "stage", "stage": "contract", "status": "complete"})
            self.queue.put({"type": "log", "text": "Stage 2 Complete: Contract schema and rules verified (0 problems)."})

            # -------------------------------------------------------------
            # Stage 3: Implement
            # -------------------------------------------------------------
            if self.cancel_event.is_set():
                self.queue.put({"type": "cancelled"})
                return

            self.queue.put({"type": "stage", "stage": "implement", "status": "running"})
            self.queue.put({"type": "log", "text": "Stage 3: Generating code modules with DeepSeek LLM..."})

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            run_dir = Path(out_root) / f"run_gui_{timestamp}"
            run_dir.mkdir(parents=True, exist_ok=True)
            self.queue.put({"type": "run_dir", "path": str(run_dir)})

            budget = Budget(run_cap=0.15, total_cap=0.85, spent=0.0, total_spent=curr_cum)
            cache = Cache(cache_dir=".cache", mode="record")
            client = Client(api_key=api_key, budget=budget, cache=cache)

            t_start = time.time()
            start_time_str = time.strftime("%Y-%m-%d %H:%M:%S")

            impl_result = implement_project(client=client, contract=contract, spec=spec, run_dir=run_dir)

            elapsed = time.time() - t_start
            run_spent = budget.spent
            self.queue.put({"type": "cost", "run_spent": run_spent, "total_spent": budget.total_spent})
            self.queue.put({"type": "stage", "stage": "implement", "status": "complete"})
            self.queue.put({
                "type": "log",
                "text": f"Stage 3 Complete: Synthesized {len(impl_result['files'])} files. "
                        f"Implement spend: ${run_spent:.6f}"
            })

            # -------------------------------------------------------------
            # Stage 4: Verify
            # -------------------------------------------------------------
            if self.cancel_event.is_set():
                self.queue.put({"type": "cancelled"})
                return

            self.queue.put({"type": "stage", "stage": "verify", "status": "running"})
            self.queue.put({"type": "log", "text": "Stage 4: Executing verification checks V1 through V8..."})

            initial_verif = run_all_checks(run_dir, contract, skip_harness=False)
            passes = len(initial_verif.get("passes", []))
            errors = len(initial_verif.get("errors", []))

            final_verif = initial_verif
            repair_rounds = []

            if initial_verif.get("all_passed"):
                self.queue.put({"type": "stage", "stage": "verify", "status": "complete"})
                self.queue.put({"type": "stage", "stage": "repair", "status": "skipped"})
                self.queue.put({
                    "type": "log",
                    "text": f"Stage 4 Complete: All V1-V8 checks PASSED ({passes}/8)! Repair not needed."
                })
            else:
                self.queue.put({"type": "stage", "stage": "verify", "status": "failed"})
                self.queue.put({
                    "type": "log",
                    "text": f"Stage 4 Failed: {errors} check error(s) detected. Moving to Repair stage..."
                })

                # -------------------------------------------------------------
                # Stage 5: Repair
                # -------------------------------------------------------------
                if self.cancel_event.is_set():
                    self.queue.put({"type": "cancelled"})
                    return

                self.queue.put({"type": "stage", "stage": "repair", "status": "running"})
                self.queue.put({"type": "log", "text": "Stage 5: Starting multi-turn autonomous repair loop..."})

                log_file = run_dir / "run_log.jsonl"
                repair_res = repair_project(
                    client=client,
                    contract=contract,
                    spec=spec,
                    run_dir=run_dir,
                    max_rounds=3,
                    log_file=log_file,
                    initial_verif=initial_verif
                )
                final_verif = repair_res["final_verification"]
                repair_rounds = repair_res["rounds"]
                run_spent += repair_res["total_cost"]

                self.queue.put({"type": "cost", "run_spent": budget.spent, "total_spent": budget.total_spent})

                if final_verif.get("all_passed"):
                    self.queue.put({"type": "stage", "stage": "repair", "status": "complete"})
                    self.queue.put({
                        "type": "log",
                        "text": f"Stage 5 Complete: Autonomous repair succeeded at round {len(repair_rounds)}!"
                    })
                else:
                    self.queue.put({"type": "stage", "stage": "repair", "status": "failed"})
                    self.queue.put({
                        "type": "log",
                        "text": f"Stage 5 Failed: Verification checks remained failing after {len(repair_rounds)} rounds."
                    })

            # -------------------------------------------------------------
            # Finalize: Report generation
            # -------------------------------------------------------------
            end_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            report_text = generate_run_report(
                run_dir=run_dir,
                contract=contract,
                spec=spec,
                initial_verif=initial_verif,
                final_verif=final_verif,
                repair_rounds=repair_rounds,
                total_cost=run_spent,
                cumulative_spend=budget.total_spent,
                start_time=start_time_str,
                end_time=end_time_str,
                elapsed_seconds=elapsed,
                model_id=client.model
            )
            report_path = run_dir / "run_report.md"
            report_path.write_text(report_text, encoding="utf-8")

            # Determine main entry point
            main_py = run_dir / "main.py"
            if not main_py.exists():
                main_py = run_dir / "app.py"

            success = bool(final_verif.get("all_passed", False))
            self.queue.put({
                "type": "done",
                "success": success,
                "run_dir": str(run_dir),
                "main_py": str(main_py) if main_py.exists() else None,
                "message": "Synthesis and verification completed successfully!" if success else "Synthesis completed with unresolved errors."
            })

        except BudgetExceededError as be:
            self.queue.put({"type": "error", "message": f"Budget ceiling exceeded: {be}"})
        except Exception as e:
            self.queue.put({"type": "error", "message": f"Unexpected error: {str(e)}"})

    def _poll_queue(self):
        """Poll the message queue on the main GUI thread every 100ms."""
        while True:
            try:
                event = self.queue.get_nowait()
            except queue.Empty:
                break
            self._handle_event(event)

        self.after(100, self._poll_queue)

    def _handle_event(self, event: dict):
        """Process messages dispatched from worker thread."""
        etype = event.get("type")

        if etype == "stage":
            sname = event.get("stage")
            status = event.get("status")
            self.update_stage(sname, status)

        elif etype == "log":
            self.append_log(event.get("text", ""))

        elif etype == "cost":
            self.run_spend = event.get("run_spent", 0.0)
            self.cumulative_spend = event.get("total_spent", self.cumulative_spend)
            self.cost_lbl.configure(text=self._format_cost_text(self.run_spend, self.cumulative_spend))

        elif etype == "run_dir":
            self.current_run_dir = event.get("path")
            self.open_folder_btn.configure(state=tk.NORMAL)

        elif etype == "key_test_result":
            self.test_key_btn.configure(state=tk.NORMAL, text="Test Key")
            msg = event.get("message", "")
            if event.get("success"):
                self.key_status_lbl.configure(text="Connected to DeepSeek API", fg="#155724")
                messagebox.showinfo("API Key Test", msg)
            else:
                self.key_status_lbl.configure(text="Connection failed", fg="#721C24")
                messagebox.showerror("API Key Test", msg)

        elif etype == "cancelled":
            self.start_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.DISABLED)
            self.status_var.set("Run cancelled.")
            self.append_log("\n[ABORTED] Synthesis run cancelled by user.")

        elif etype == "error":
            self.start_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.DISABLED)
            err = event.get("message", "Unknown error")
            self.status_var.set(f"Run Error: {err}")
            self.append_log(f"\n[ERROR] {err}")
            messagebox.showerror("Pipeline Error", err)

        elif etype == "done":
            self.start_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.DISABLED)
            self.open_folder_btn.configure(state=tk.NORMAL)

            self.current_run_dir = event.get("run_dir")
            self.current_main_py = event.get("main_py")
            success = event.get("success", False)

            if success and self.current_main_py:
                self.launch_game_btn.configure(state=tk.NORMAL)
                self.status_var.set("Synthesis complete! All checks PASSED.")
                self.append_log("\n" + "=" * 60)
                self.append_log("[SUCCESS] Synthesis completed with 100% verification passing.")
                self.append_log(f"Run folder: {self.current_run_dir}")
                self.append_log("Game launcher is ready.")
                self.append_log("=" * 60)
            else:
                self.launch_game_btn.configure(state=tk.DISABLED)
                self.status_var.set("Completed with verification failures.")
                self.append_log("\n" + "=" * 60)
                self.append_log("[FAIL] Synthesis finished with verification check failures.")
                self.append_log(f"Inspect run report at: {self.current_run_dir}/run_report.md")
                self.append_log("=" * 60)

    def _open_run_folder(self):
        """Open the current run output folder in system file explorer."""
        if not self.current_run_dir or not Path(self.current_run_dir).exists():
            messagebox.showwarning("Open Folder", "No active run directory found.")
            return

        target_dir = str(Path(self.current_run_dir).resolve())
        try:
            if sys.platform == "win32":
                os.startfile(target_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target_dir])
            else:
                subprocess.Popen(["xdg-open", target_dir])
            self.append_log(f"Opened folder: {target_dir}")
        except Exception as e:
            messagebox.showerror("Open Folder", f"Failed to open folder: {e}")

    def _launch_game(self):
        """Launch the synthesized desktop game in a detached independent process."""
        if not self.current_main_py or not Path(self.current_main_py).exists():
            messagebox.showerror("Launch Error", "Generated entrypoint file (main.py) was not found.")
            return

        try:
            proc = launch_game(self.current_main_py)
            msg = f"Launched application process (PID: {proc.pid}) in detached mode."
            self.append_log(msg)
            self.status_var.set(f"Application running (PID: {proc.pid})")
        except Exception as e:
            err = f"Failed to launch application: {e}"
            self.append_log(f"[ERROR] {err}")
            messagebox.showerror("Launch Error", err)


def create_app(headless: bool = False) -> App:
    """Create and return the GUI application instance."""
    return App(headless=headless)


if __name__ == "__main__":
    app = create_app()
    app.mainloop()
