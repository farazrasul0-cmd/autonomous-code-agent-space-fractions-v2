# tests/test_verify.py - Unit tests for Phase 7 Verification Checks (V1 through V8)
import os
import sys
import json
import unittest
import subprocess
from pathlib import Path

# Ensure repo root is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.verify import (
    check_v1_file_presence,
    check_v2_compilation,
    check_v3_contract_conformance,
    check_v4_call_resolution,
    check_v5_tk_collisions,
    check_v6_import_boundaries,
    check_v7_test_execution,
    check_v8_harness,
    run_all_checks
)


class TestVerify(unittest.TestCase):

    def setUp(self):
        self.fixtures_dir = repo_root / "tests" / "fixtures"

    def test_v4_flags_bug1(self):
        """V4 flags method on wrong object (self.other.start where 'other' is object)."""
        bug1_dir = self.fixtures_dir / "bug1"
        errors = check_v4_call_resolution(bug1_dir)
        self.assertTrue(len(errors) > 0, "V4 must flag bug1")
        self.assertTrue(
            any("start" in e["message"] and "object" in e["message"] for e in errors),
            f"Expected error for method 'start' on object, got: {errors}"
        )

    def test_v4_flags_bug2(self):
        """V4 flags attribute called as method (self.q.prompt())."""
        bug2_dir = self.fixtures_dir / "bug2"
        errors = check_v4_call_resolution(bug2_dir)
        self.assertTrue(len(errors) > 0, "V4 must flag bug2")
        self.assertTrue(
            any("prompt" in e["message"] and ("attribute" in e["message"] or "property" in e["message"]) for e in errors),
            f"Expected error for attribute 'prompt' called as method, got: {errors}"
        )

    def test_v4_flags_bug3(self):
        """V4 flags self.x.method where x was never assigned in class."""
        bug3_dir = self.fixtures_dir / "bug3"
        errors = check_v4_call_resolution(bug3_dir)
        self.assertTrue(len(errors) > 0, "V4 must flag bug3")
        self.assertTrue(
            any("engine" in e["message"] and "never assigned" in e["message"] for e in errors),
            f"Expected error for unassigned attribute 'engine', got: {errors}"
        )

    def test_v5_flags_bug4(self):
        """V5 flags Tkinter method collision in subclass (update on Frame)."""
        bug4_dir = self.fixtures_dir / "bug4"
        errors = check_v5_tk_collisions(bug4_dir)
        self.assertTrue(len(errors) > 0, "V5 must flag bug4")
        self.assertTrue(
            any("update" in e["message"] and "collides" in e["message"] for e in errors),
            f"Expected error for 'update' colliding with Tkinter, got: {errors}"
        )

    def test_good_fixture_clean_v1_to_v6_and_v8(self):
        """Good fixture produces ZERO errors from V1-V6 and V8."""
        good_dir = self.fixtures_dir / "good"
        contract_path = good_dir / "contract.json"
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        v1 = check_v1_file_presence(good_dir, contract)
        self.assertEqual(v1, [], f"V1 failed on good fixture: {v1}")

        v2 = check_v2_compilation(good_dir)
        self.assertEqual(v2, [], f"V2 failed on good fixture: {v2}")

        v3 = check_v3_contract_conformance(good_dir, contract)
        self.assertEqual(v3, [], f"V3 failed on good fixture: {v3}")

        v4 = check_v4_call_resolution(good_dir)
        self.assertEqual(v4, [], f"V4 failed on good fixture: {v4}")

        v5 = check_v5_tk_collisions(good_dir)
        self.assertEqual(v5, [], f"V5 failed on good fixture: {v5}")

        v6 = check_v6_import_boundaries(good_dir)
        self.assertEqual(v6, [], f"V6 failed on good fixture: {v6}")

        v7 = check_v7_test_execution(good_dir)
        self.assertEqual(v7, [], f"V7 failed on good fixture: {v7}")

        v8 = check_v8_harness(good_dir, contract)
        self.assertEqual(v8, [], f"V8 failed on good fixture: {v8}")

    def test_v3_flags_missing_method(self):
        """V3 flags when a declared method is missing in source code."""
        good_dir = self.fixtures_dir / "good"
        contract_path = good_dir / "contract.json"
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        # Mutate contract to require nonexistent method
        bad_contract = json.loads(json.dumps(contract))
        bad_contract["classes"][0]["methods"].append({"name": "nonexistent_func", "params": ["self"]})

        errors = check_v3_contract_conformance(good_dir, bad_contract)
        self.assertTrue(len(errors) > 0, "V3 should flag missing method")
        self.assertTrue(any("nonexistent_func" in e["message"] for e in errors))

    def test_v3_flags_property_called_as_method(self):
        """V3 flags when a method marked as 'property' in contract is not decorated with @property."""
        good_dir = self.fixtures_dir / "good"
        contract_path = good_dir / "contract.json"
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        bad_contract = json.loads(json.dumps(contract))
        # Mark increment as property
        bad_contract["classes"][0]["methods"][1]["kind"] = "property"

        errors = check_v3_contract_conformance(good_dir, bad_contract)
        self.assertTrue(len(errors) > 0, "V3 should flag method that is not @property")
        self.assertTrue(any("@property" in e["message"] for e in errors))

    def test_v3_does_not_reject_extra_private_attributes(self):
        """V3 must tolerate extra private attributes not in contract and name-mangled attributes."""
        good_dir = self.fixtures_dir / "good"
        contract_path = good_dir / "contract.json"
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        # Contract only specifies _count, but source code may have extra attributes
        errors = check_v3_contract_conformance(good_dir, contract)
        self.assertEqual(errors, [])

    def test_v3_accepts_property_backed_attribute(self):
        """Attribute declared in contract is satisfied if @property <name> exists."""
        import tempfile
        contract = {
            "classes": [{
                "name": "Widget", "file": "w.py", "base": None,
                "attributes": [{"name": "state", "type": "str", "visibility": "private"}],
                "properties": [], "methods": []
            }]
        }
        src = (
            "class Widget:\n"
            "    def __init__(self):\n"
            "        self._state = 'x'\n"
            "    @property\n"
            "    def state(self):\n"
            "        return self._state\n"
            "    @state.setter\n"
            "    def state(self, value):\n"
            "        self._state = value\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_run_dir = Path(temp_dir)
            (temp_run_dir / "w.py").write_text(src, encoding="utf-8")
            problems = check_v3_contract_conformance(temp_run_dir, contract)
            self.assertEqual(problems, [], f"V3 flagged property-backed attribute: {problems}")

    def test_harness_passes_good_fixture(self):
        """V8 harness passes clean good fixture."""
        good_dir = self.fixtures_dir / "good"
        contract_path = good_dir / "contract.json"
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        errors = check_v8_harness(good_dir, contract)
        self.assertEqual(errors, [])

    def test_harness_fails_on_crash(self):
        """V8 harness detects and flags UI exception in smoke step."""
        crash_dir = self.fixtures_dir / "crash"
        contract_path = crash_dir / "contract.json"
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        errors = check_v8_harness(crash_dir, contract)
        self.assertTrue(len(errors) > 0, "V8 harness must flag crash fixture")
        self.assertTrue(any("Simulated UI crash" in e["message"] for e in errors))

    def test_v4_handles_annotated_assignments(self):
        """V4 does not flag attributes assigned using type annotations (AnnAssign)."""
        import tempfile
        src = (
            "import tkinter as tk\n"
            "class Helper:\n"
            "    def work(self):\n"
            "        pass\n"
            "class App:\n"
            "    def __init__(self):\n"
            "        self._status_var: tk.StringVar = tk.StringVar(value='Ready')\n"
            "        self.helper: Helper = Helper()\n"
            "        self._status_var.set('Running')\n"
            "        self.helper.work()\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_run_dir = Path(temp_dir)
            (temp_run_dir / "app.py").write_text(src, encoding="utf-8")
            errors = check_v4_call_resolution(temp_run_dir)
            self.assertEqual(errors, [], f"V4 unexpectedly flagged annotated assignments: {errors}")

    def test_v7_in_process_fallback(self):
        """V7 in-process fallback runs unit tests in-process and reports success."""
        from src.verify import _run_v7_in_process
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_run_dir = Path(temp_dir)
            tests_dir = temp_run_dir / "tests"
            tests_dir.mkdir()
            (tests_dir / "__init__.py").write_text("", encoding="utf-8")
            (tests_dir / "test_sample.py").write_text(
                "import unittest\n"
                "class SampleTest(unittest.TestCase):\n"
                "    def test_pass(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8"
            )
            errors = _run_v7_in_process(temp_run_dir, tests_dir)
            self.assertEqual(errors, [])

    def test_v7_in_process_with_spaces_in_path(self):
        """V7 in-process handles directory paths containing spaces without choking."""
        from src.verify import _run_v7_in_process
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            spaced_dir = Path(temp_dir) / "run dir with spaces"
            spaced_dir.mkdir()
            tests_dir = spaced_dir / "tests"
            tests_dir.mkdir()
            (tests_dir / "__init__.py").write_text("", encoding="utf-8")
            (tests_dir / "test_sample.py").write_text(
                "import unittest\n"
                "class SampleTest(unittest.TestCase):\n"
                "    def test_pass(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8"
            )
            errors = _run_v7_in_process(spaced_dir, tests_dir)
            self.assertEqual(errors, [])

    def test_v7_in_process_failure_contains_traceback(self):
        """V7 in-process captures full failure traceback for failing tests."""
        from src.verify import _run_v7_in_process
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_run_dir = Path(temp_dir)
            tests_dir = temp_run_dir / "tests"
            tests_dir.mkdir()
            (tests_dir / "__init__.py").write_text("", encoding="utf-8")
            (tests_dir / "test_sample.py").write_text(
                "import unittest\n"
                "class FailingTest(unittest.TestCase):\n"
                "    def test_fail(self):\n"
                "        self.assertEqual(1, 2, 'intentional assertion failure')\n",
                encoding="utf-8"
            )
            errors = _run_v7_in_process(temp_run_dir, tests_dir)
            self.assertEqual(len(errors), 1)
            self.assertIn("intentional assertion failure", errors[0]["message"])

    def test_v8_harness_skipped_returns_no_errors(self):
        """V8 check returns 0 errors when harness returns skipped status."""
        with unittest.mock.patch("src.verify.run_harness", return_value={"status": "skipped", "reason": "Sandbox Timeout"}):
            errors = check_v8_harness(Path("dummy"), {})
            self.assertEqual(errors, [])

    def test_v7_missing_or_empty_tests_dir(self):
        """V7 strictly fails when tests/ directory is missing or has no test_*.py files."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            # Missing tests/ directory
            res = check_v7_test_execution(td)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["check"], "V7")
            self.assertEqual(res[0]["message"], "Missing or empty tests/ directory")

            # Empty tests/ directory (no test_*.py)
            (Path(td) / "tests").mkdir()
            (Path(td) / "tests" / "__init__.py").write_text("", encoding="utf-8")
            res2 = check_v7_test_execution(td)
            self.assertEqual(len(res2), 1)
            self.assertEqual(res2[0]["check"], "V7")
            self.assertEqual(res2[0]["message"], "Missing or empty tests/ directory")

    def test_v7_scrubbed_environment(self):
        """V7 passes a scrubbed environment without DEEPSEEK_API_KEY to subprocess."""
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            tests_dir = Path(td) / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_dummy.py").write_text("import unittest\n", encoding="utf-8")

            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "secret-audit-key", "SAFE_VAR": "safe"}):
                with patch("subprocess.run") as mock_run:
                    mock_proc = unittest.mock.MagicMock()
                    mock_proc.returncode = 0
                    mock_run.return_value = mock_proc
                    check_v7_test_execution(td)
                    self.assertTrue(mock_run.called)
                    call_env = mock_run.call_args.kwargs.get("env")
                    self.assertIsNotNone(call_env)
                    self.assertNotIn("DEEPSEEK_API_KEY", call_env)
                    self.assertIn("SAFE_VAR", call_env)

    def test_harness_strict_failure_on_timeout_or_crash(self):
        """Harness returns status: fail when subprocess times out or crashes (no in-process fallback)."""
        from src.harness import run_harness
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "main.py").write_text("def create_app(root): return None\n", encoding="utf-8")
            # Timeout scenario
            with unittest.mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=1)):
                res = run_harness(td, {}, timeout=1)
                self.assertEqual(res["status"], "fail")
                self.assertIn("timed out", res["error"])

            # Crash scenario
            mock_proc = unittest.mock.MagicMock()
            mock_proc.returncode = 1
            mock_proc.stderr = "Fatal crash"
            mock_proc.stdout = ""
            with unittest.mock.patch("subprocess.run", return_value=mock_proc):
                res = run_harness(td, {})
                self.assertEqual(res["status"], "fail")
                self.assertIn("terminated without result file", res["error"])


if __name__ == "__main__":
    unittest.main()
