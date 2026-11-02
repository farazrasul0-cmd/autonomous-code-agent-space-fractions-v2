# tests/test_app.py - Unit tests for GUI Front-End, Detached Launch, and Queue Architecture
import os
import sys
import time
import tempfile
import unittest
from pathlib import Path

# Ensure repo root is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.app import (
    App,
    create_app,
    launch_game,
    sanitize_log,
    get_current_cumulative_spend
)


class TestApp(unittest.TestCase):

    def test_sanitize_log_masks_api_keys(self):
        """Sanitization redacts both standard DeepSeek keys and user-entered custom keys."""
        text = "Connecting to https://api.deepseek.com with key sk-abcdef1234567890uvwxyz"
        clean = sanitize_log(text)
        self.assertNotIn("sk-abcdef1234567890uvwxyz", clean)
        self.assertIn("[REDACTED_API_KEY]", clean)

        custom_text = "Sending request with custom_secret_token_12345"
        clean_custom = sanitize_log(custom_text, current_key="custom_secret_token_12345")
        self.assertNotIn("custom_secret_token_12345", clean_custom)
        self.assertIn("[REDACTED_API_KEY]", clean_custom)

    def test_get_current_cumulative_spend(self):
        """Verify cumulative spend calculation reads existing run_log.jsonl files."""
        spend = get_current_cumulative_spend(repo_root / "examples" / "runs")
        self.assertIsInstance(spend, float)
        self.assertGreaterEqual(spend, 0.070000, f"Expected cumulative spend >= $0.07, got {spend}")

    def test_launch_game_detached_process(self):
        """Verify launch_game spawns a detached independent process with valid PID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_py = Path(temp_dir) / "dummy_main.py"
            temp_py.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")

            proc = launch_game(temp_py)
            self.assertIsNotNone(proc.pid)
            self.assertGreater(proc.pid, 0)

            # Cleanup detached process
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                pass

    def test_launch_game_raises_on_missing_file(self):
        """launch_game raises FileNotFoundError if entrypoint does not exist."""
        with self.assertRaises(FileNotFoundError):
            launch_game("nonexistent_file_xyz_123.py")

    def test_app_gui_initialization_and_headless(self):
        """Verify Tkinter App initializes in headless mode with correct default widget states."""
        app = create_app(headless=True)
        try:
            self.assertIn("DeepSeek Code Agent", app.title())
            self.assertEqual(app.start_btn.cget("state"), "normal")
            self.assertEqual(app.cancel_btn.cget("state"), "disabled")
            self.assertEqual(app.launch_game_btn.cget("state"), "disabled")
            self.assertEqual(app.open_folder_btn.cget("state"), "disabled")

            # Check all 5 stages default to Pending
            for sname in ["parse", "contract", "implement", "verify", "repair"]:
                self.assertIn(sname, app.stage_widgets)
                self.assertEqual(app.stage_widgets[sname]["status"].cget("text"), "Pending")
        finally:
            app.destroy()

    def test_app_queue_polling_and_stage_updates(self):
        """Verify GUI handles worker thread events through queue and updates widgets safely."""
        app = create_app(headless=True)
        try:
            # Stage update event
            app._handle_event({"type": "stage", "stage": "parse", "status": "running"})
            self.assertEqual(app.stage_widgets["parse"]["status"].cget("text"), "In Progress...")

            # Cost update event
            app._handle_event({"type": "cost", "run_spent": 0.012345, "total_spent": 0.075432})
            self.assertIn("$0.012345", app.cost_lbl.cget("text"))
            self.assertIn("$0.075432", app.cost_lbl.cget("text"))

            # Log event
            app._handle_event({"type": "log", "text": "Test pipeline log event"})
            log_content = app.log_text.get("1.0", "end")
            self.assertIn("Test pipeline log event", log_content)

            # Done event (success)
            app._handle_event({
                "type": "done",
                "success": True,
                "run_dir": str(repo_root / "examples" / "runs"),
                "main_py": str(repo_root / "contract.json")  # file exists for test
            })
            self.assertEqual(app.launch_game_btn.cget("state"), "normal")
            self.assertEqual(app.open_folder_btn.cget("state"), "normal")
            self.assertEqual(app.start_btn.cget("state"), "normal")
        finally:
            app.destroy()

    def test_app_cancel_event_sets_flag(self):
        """Verify cancel button sets the cancellation event."""
        app = create_app(headless=True)
        try:
            self.assertFalse(app.cancel_event.is_set())
            app._cancel_run()
            self.assertTrue(app.cancel_event.is_set())
        finally:
            app.destroy()

    def test_run_script_cli_flag(self):
        """Verify python src/app.py --run-script <path> executes target script without launching GUI."""
        import subprocess
        with tempfile.TemporaryDirectory() as temp_dir:
            marker = Path(temp_dir) / "marker.txt"
            script = Path(temp_dir) / "test_target.py"
            script.write_text(f"from pathlib import Path\nPath(r'{marker}').write_text('ran', encoding='utf-8')\n", encoding="utf-8")

            res = subprocess.run(
                [sys.executable, str(repo_root / "src" / "app.py"), "--run-script", str(script)],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(res.returncode, 0, f"Subprocess failed: {res.stderr}")
            self.assertTrue(marker.exists())
            self.assertEqual(marker.read_text(encoding="utf-8"), "ran")


if __name__ == "__main__":
    unittest.main()
