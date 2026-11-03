# tests/test_verify.py - Unit tests for Phase 7 Verification Checks (V1 through V8)
import os
import sys
import json
import unittest
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

    def test_v8_harness_skipped_returns_no_errors(self):
        """V8 check returns 0 errors when harness returns skipped status."""
        with unittest.mock.patch("src.verify.run_harness", return_value={"status": "skipped", "reason": "Sandbox Timeout"}):
            errors = check_v8_harness(Path("dummy"), {})
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
