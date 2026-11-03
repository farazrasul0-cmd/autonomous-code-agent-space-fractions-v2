# tests/test_agent.py - Unit tests for Phase 6 Code Generation & Agent capabilities
import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Ensure src/ is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.llm import FakeClient
from src.agent import (
    PathEscapeError,
    safe_write,
    ledger,
    build_file_prompt,
    extract_code_from_response,
    ensure_windowed_guard,
    compile_file,
    generate_non_code_files,
    repair_project
)


class TestAgent(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="agent_test_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_safe_write_normal(self):
        """Verify normal relative write creates the file within run_dir."""
        content = "print('hello world')\n"
        path = safe_write(self.temp_dir, "models.py", content)
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_safe_write_nested(self):
        """Verify safe_write creates parent directories for nested paths."""
        content = "# test\n"
        path = safe_write(self.temp_dir, "sub/dir/nested.py", content)
        self.assertTrue(os.path.exists(path))

    def test_safe_write_rejects_absolute_path(self):
        """Verify safe_write raises PathEscapeError on absolute paths."""
        bad_paths = ["/etc/passwd", "C:\\Windows\\system.ini", "C:/test.py"]
        for bp in bad_paths:
            with self.assertRaises(PathEscapeError):
                safe_write(self.temp_dir, bp, "bad")

    def test_safe_write_rejects_parent_traversal(self):
        """Verify safe_write raises PathEscapeError on paths containing '..'."""
        bad_paths = ["../escape.py", "sub/../../escape.py", "a/b/../../../etc/passwd"]
        for bp in bad_paths:
            with self.assertRaises(PathEscapeError):
                safe_write(self.temp_dir, bp, "bad")

    def test_ledger_extracts_class_and_methods(self):
        """Verify ledger extracts classes, instantiations, methods, return types, and properties."""
        test_py = Path(self.temp_dir) / "test_module.py"
        test_py.write_text(
            "class Engine:\n"
            "    def __init__(self, name: str) -> None:\n"
            "        self.name = name\n"
            "        self.sub = SubEngine(name)\n"
            "\n"
            "    def start(self) -> bool:\n"
            "        return True\n"
            "\n"
            "    @property\n"
            "    def is_active(self) -> bool:\n"
            "        return True\n"
            "\n"
            "def helper(x: int) -> int:\n"
            "    return x + 1\n",
            encoding="utf-8"
        )

        ledger_text = ledger(test_py)
        self.assertIn("class Engine:", ledger_text)
        self.assertIn("self.sub = SubEngine(name)", ledger_text)
        self.assertIn("def __init__(self, name)", ledger_text)
        self.assertIn("def start(self) -> bool", ledger_text)
        self.assertIn("@property def is_active(self) -> bool", ledger_text)
        self.assertIn("def helper(x) -> int", ledger_text)

    def test_build_file_prompt_is_generic(self):
        """Verify build_file_prompt does not leak brand name 'Space Fractions' and contains ledger."""
        contract = {
            "files": [{"path": "models.py", "purpose": "Domain models", "order": 1, "imports": []}],
            "classes": [
                {
                    "name": "Game",
                    "file": "models.py",
                    "attributes": [{"name": "score", "type": "int"}],
                    "methods": [{"name": "play", "params": ["self"], "returns": "None", "kind": "method"}]
                }
            ],
            "forbidden_names": ["update", "pack", "grid"]
        }
        file_entry = {"path": "models.py", "purpose": "Domain models", "order": 1}
        ledger_sample = "File: prev.py\n  class Helper:\n    def run(self)\n"

        prompt = build_file_prompt(contract, file_entry, ledger_sample)
        self.assertNotIn("Space Fractions", prompt)
        self.assertIn("models.py", prompt)
        self.assertIn("Domain models", prompt)
        self.assertIn("File: prev.py", prompt)
        self.assertIn("Helper", prompt)
        self.assertIn("single-underscore (_name)", prompt)

        # Fix A: verify dynamic injection when spec is provided
        prompt_with_spec = build_file_prompt(contract, file_entry, ledger_sample, spec={"system_name": "Dynamic System"})
        self.assertIn("SYSTEM NAME: Dynamic System", prompt_with_spec)
        self.assertIn("Use this system name as the window title", prompt_with_spec)

    def test_extract_code_from_tool_call(self):
        """Verify extraction from write_file tool_calls response."""
        resp = {
            "tool_calls": [
                {
                    "function": {
                        "name": "write_file",
                        "arguments": json.dumps({"path": "models.py", "content": "class Game:\n    pass\n"})
                    }
                }
            ],
            "content": ""
        }
        path, code = extract_code_from_response(resp, default_path="fallback.py")
        self.assertEqual(path, "models.py")
        self.assertEqual(code, "class Game:\n    pass\n")

    def test_extract_code_from_fenced_block(self):
        """Verify extraction fallback from markdown fenced code block."""
        resp = {
            "tool_calls": [],
            "content": "Here is the code:\n```python\nclass Question:\n    pass\n```\nDone."
        }
        path, code = extract_code_from_response(resp, default_path="models.py")
        self.assertEqual(path, "models.py")
        self.assertEqual(code, "class Question:\n    pass")

    def test_windowed_guard_injection(self):
        """Verify windowed-mode print guard is injected if missing and untouched if present."""
        code_without = "import tkinter as tk\nroot = tk.Tk()\n"
        guarded = ensure_windowed_guard(code_without)
        self.assertIn("sys.stdout is None", guarded)
        self.assertIn("os.devnull", guarded)

        # Calling again should not duplicate
        double_guarded = ensure_windowed_guard(guarded)
        self.assertEqual(guarded, double_guarded)

    def test_compile_file(self):
        """Verify compile_file returns None on valid code and error message on syntax error."""
        valid_py = Path(self.temp_dir) / "valid.py"
        valid_py.write_text("x = 1 + 2\n", encoding="utf-8")
        self.assertIsNone(compile_file(valid_py))

        invalid_py = Path(self.temp_dir) / "invalid.py"
        invalid_py.write_text("def broken(:\n", encoding="utf-8")
        err = compile_file(invalid_py)
        self.assertIsNotNone(err)
        self.assertIn("SyntaxError", err)

    def test_generate_non_code_files(self):
        """Verify Python-based generation of requirements.txt, README.md, DECISIONS.md without model calls."""
        spec = {
            "system_name": "Test System",
            "conflicts": {"resolution": "Desktop application selected"}
        }
        contract = {
            "files": [
                {"path": "models.py", "purpose": "Data models", "order": 1},
                {"path": "app.py", "purpose": "GUI", "order": 2},
                {"path": "main.py", "purpose": "Entry point", "order": 3}
            ]
        }
        written = generate_non_code_files(self.temp_dir, spec, contract)
        self.assertIn("requirements.txt", written)
        self.assertIn("README.md", written)
        self.assertIn("DECISIONS.md", written)

        # Verify files exist on disk
        for name in written:
            self.assertTrue((Path(self.temp_dir) / name).exists())

        readme = (Path(self.temp_dir) / "README.md").read_text(encoding="utf-8")
        self.assertIn("Test System", readme)
        self.assertIn("models.py", readme)

    def test_repair_loop_terminates_on_success(self):
        """Repair loop executes tool call to repair a failing file and terminates on success."""
        fixtures_dir = repo_root / "tests" / "fixtures" / "good"
        for item in ["contract.json", "engine.py", "main.py", "models.py", "ui.py"]:
            shutil.copy(fixtures_dir / item, Path(self.temp_dir) / item)
        shutil.copytree(fixtures_dir / "tests", Path(self.temp_dir) / "tests")

        with open(fixtures_dir / "contract.json", "r", encoding="utf-8") as f:
            contract = json.load(f)

        # Introduce a flaw into models.py that triggers V4: self.other.start() where other is object()
        flawed_models = (
            "class Counter:\n"
            "    def __init__(self):\n"
            "        self._count = 0\n"
            "        self.other = object()\n"
            "    @property\n"
            "    def count(self):\n"
            "        return self._count\n"
            "    def increment(self):\n"
            "        self.other.start()\n"
            "        self._count += 1\n"
            "    def reset(self):\n"
            "        self._count = 0\n"
        )
        safe_write(self.temp_dir, "models.py", flawed_models)

        good_models = (Path(fixtures_dir) / "models.py").read_text(encoding="utf-8")

        fake_response = {
            "content": "Fixing the unresolvable call in models.py",
            "tool_calls": [
                {
                    "id": "call_fix_models",
                    "function": {
                        "name": "write_file",
                        "arguments": json.dumps({
                            "path": "models.py",
                            "content": good_models
                        })
                    }
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            "cost": 0.0001
        }
        fake_client = FakeClient([fake_response])

        spec = {"system_name": "Counter App"}
        result = repair_project(
            client=fake_client,
            contract=contract,
            spec=spec,
            run_dir=self.temp_dir,
            max_rounds=3
        )

        self.assertTrue(result["all_passed"], "Repair loop should pass all checks after fix")
        self.assertEqual(len(result["rounds"]), 1, "Should succeed in exactly 1 round")
        self.assertIn("models.py", result["rounds"][0]["files_changed"])

    def test_generate_run_report_verdict_verification_incomplete(self):
        """Verify generate_run_report sets verdict to VERIFICATION INCOMPLETE on dynamic timeouts."""
        from src.agent import generate_run_report
        contract = {
            "files": [{"order": 1, "path": "models.py", "purpose": "Domain models"}],
            "classes": [{"name": "Counter"}]
        }
        spec = {"system_name": "Counter App"}
        initial_verif = {
            "all_passed": False,
            "checks": {
                "V1": [], "V2": [], "V3": [], "V4": [], "V5": [], "V6": [],
                "V7": [{"check": "V7", "file": "tests", "message": "Unit test suite timed out after 60 seconds"}],
                "V8": []
            },
            "errors": [{"check": "V7", "file": "tests", "message": "Unit test suite timed out after 60 seconds"}]
        }
        final_verif = dict(initial_verif)

        report = generate_run_report(
            run_dir=self.temp_dir,
            contract=contract,
            spec=spec,
            initial_verif=initial_verif,
            final_verif=final_verif,
            repair_rounds=[],
            total_cost=0.01,
            cumulative_spend=0.02,
            start_time="2026-11-03 20:00:00",
            end_time="2026-11-03 20:01:00",
            elapsed_seconds=60.0
        )

        self.assertIn("- **Final Verdict**: **VERIFICATION INCOMPLETE**", report)
        self.assertIn("### Verdict: VERIFICATION INCOMPLETE", report)
        self.assertNotIn("Verdict: FAILED", report)
        self.assertNotIn("Verdict: PASSED", report)

    def test_build_traceability_table_maps_app_methods(self):
        """Verify build_traceability_table maps App methods from app.py correctly."""
        from src.agent import build_traceability_table
        contract = {
            "traceability": [
                {"diagram_element": "UseCaseDiagram.Play Game", "code_symbol": "App.start_play_game"},
                {"diagram_element": "UseCaseDiagram.View Score", "code_symbol": "App.show_view_score"},
                {"diagram_element": "UseCaseDiagram.Update Questions", "code_symbol": "App.update_questions"},
                {"diagram_element": "UseCaseDiagram.View Help", "code_symbol": "App.show_help"}
            ]
        }
        app_code = (
            "class Application:\n"
            "    def start_play_game(self): pass\n"
            "    def show_view_score(self): pass\n"
            "    def update_questions(self, qs): pass\n"
            "    def show_help(self): pass\n"
        )
        safe_write(self.temp_dir, "app.py", app_code)
        rows = build_traceability_table(self.temp_dir, contract)
        self.assertEqual(len(rows), 4)
        for r in rows:
            self.assertEqual(r["status"], "Verified", f"Expected Verified for {r['code_symbol']}, got {r}")
            self.assertEqual(r["file"], "app.py")
            self.assertNotEqual(r["line"], 0)


if __name__ == "__main__":
    unittest.main()
