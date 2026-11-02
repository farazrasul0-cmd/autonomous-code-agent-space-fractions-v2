# tests/test_contract.py - Unit tests for architectural contract generator and validator
import os
import sys
import json
import unittest
from pathlib import Path

# Ensure src/ is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.agent import (
    validate_contract,
    build_contract_prompt,
    compute_forbidden_names,
    ContractError
)


def get_sample_spec():
    """Load real spec.json or fallback mock spec."""
    spec_path = os.path.join(repo_root, "spec.json")
    if os.path.exists(spec_path):
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "system_name": "Space Fractions",
        "diagrams": {
            "ClassDiagram": {
                "classes": [
                    {"name": "Game", "methods": ["+ play(): void"]},
                    {"name": "Question", "methods": ["+ getPrompt(): str"]},
                    {"name": "User", "methods": ["+ playGame(): void"]},
                    {"name": "Admin", "methods": ["+ updateQuestions(): void"]}
                ]
            },
            "UseCaseDiagram": {
                "actors": ["User", "Admin"],
                "usecases": ["Play Game", "View Score", "Update Questions", "View Help"]
            },
            "StateDiagram": {
                "states": ["Playing", "Paused", "GameOver"],
                "transitions": [
                    "[*] -> Playing",
                    "Playing -> Paused : pause()",
                    "Paused -> Playing : resume()",
                    "Playing -> GameOver : gameOver()"
                ]
            }
        },
        "requirements": []
    }


def make_valid_contract():
    """Construct valid contract conforming to spec and new application structure."""
    return {
        "files": [
            {"path": "models.py", "purpose": "Domain models", "order": 1, "imports": []},
            {"path": "services.py", "purpose": "Game logic and administration", "order": 2, "imports": ["models.py"]},
            {"path": "ui.py", "purpose": "Tkinter GUI interface", "order": 3, "imports": ["services.py", "models.py"]},
            {"path": "main.py", "purpose": "Application entry point", "order": 4, "imports": ["ui.py"]}
        ],
        "classes": [
            {
                "name": "Game",
                "file": "models.py",
                "base": None,
                "attributes": [
                    {"name": "id", "type": "str", "visibility": "private"},
                    {"name": "score", "type": "int", "visibility": "private"},
                    {"name": "state", "type": "str", "visibility": "private"}
                ],
                "properties": [],
                "methods": [{"name": "play", "params": ["self"], "returns": "None", "kind": "method"}]
            },
            {
                "name": "Question",
                "file": "models.py",
                "base": None,
                "attributes": [
                    {"name": "id", "type": "str", "visibility": "private"},
                    {"name": "prompt", "type": "str", "visibility": "private"},
                    {"name": "options", "type": "list", "visibility": "private"},
                    {"name": "answer_index", "type": "int", "visibility": "private"}
                ],
                "properties": [],
                "methods": [{"name": "getPrompt", "params": ["self"], "returns": "str", "kind": "method"}]
            },
            {
                "name": "User",
                "file": "models.py",
                "base": None,
                "attributes": [
                    {"name": "id", "type": "str", "visibility": "private"},
                    {"name": "username", "type": "str", "visibility": "private"}
                ],
                "properties": [],
                "methods": [{"name": "playGame", "params": ["self", "game"], "returns": "None", "kind": "method"}]
            },
            {
                "name": "Admin",
                "file": "models.py",
                "base": None,
                "attributes": [
                    {"name": "id", "type": "str", "visibility": "private"},
                    {"name": "username", "type": "str", "visibility": "private"}
                ],
                "properties": [],
                "methods": [{"name": "updateQuestions", "params": ["self", "questions"], "returns": "None", "kind": "method"}]
            }
        ],
        "entrypoints": [
            {"name": "create_app", "signature": "create_app(root: tk.Tk) -> App", "purpose": "Create and return the App instance"}
        ],
        "app_methods": [
            {"name": "start_game", "signature": "start_game() -> None", "purpose": "Use case: Play Game"},
            {"name": "view_score", "signature": "view_score() -> int", "purpose": "Use case: View Score"},
            {"name": "update_questions", "signature": "update_questions(questions: list) -> None", "purpose": "Use case: Update Questions"},
            {"name": "show_help", "signature": "show_help() -> None", "purpose": "Use case: View Help"},
            {"name": "end_game", "signature": "end_game() -> None", "purpose": "Transition Game.state to GameOver (trigger for gameOver state transition)"}
        ],
        "states": [
            {"name": "Playing", "owner": "Game", "attribute": "state"},
            {"name": "Paused", "owner": "Game", "attribute": "state"},
            {"name": "GameOver", "owner": "Game", "attribute": "state"}
        ],
        "transitions": [
            {"trigger": "pause", "from": "Playing", "to": "Paused"},
            {"trigger": "resume", "from": "Paused", "to": "Playing"},
            {"trigger": "gameOver", "method": "end_game", "from": "Playing", "to": "GameOver"}
        ],
        "smoke_steps": [
            {"call": "create_app", "args": [], "purpose": "Smoke test application launch"},
            {"call": "start_game", "args": [], "purpose": "Smoke test Play Game flow"},
            {"call": "view_score", "args": [], "purpose": "Smoke test View Score flow"},
            {"call": "end_game", "args": [], "purpose": "Smoke test game over state"},
            {"call": "update_questions", "args": [[]], "purpose": "Smoke test admin update questions flow"},
            {"call": "show_help", "args": [], "purpose": "Smoke test View Help flow"}
        ],
        "traceability": [
            {"diagram_element": "ClassDiagram.Game", "code_symbol": "Game"},
            {"diagram_element": "ClassDiagram.Question", "code_symbol": "Question"},
            {"diagram_element": "ClassDiagram.User", "code_symbol": "User"},
            {"diagram_element": "ClassDiagram.Admin", "code_symbol": "Admin"},
            {"diagram_element": "UseCaseDiagram.Play Game", "code_symbol": "App.start_game"},
            {"diagram_element": "UseCaseDiagram.View Score", "code_symbol": "App.view_score"},
            {"diagram_element": "UseCaseDiagram.Update Questions", "code_symbol": "App.update_questions"},
            {"diagram_element": "UseCaseDiagram.View Help", "code_symbol": "App.show_help"}
        ]
    }


class TestContract(unittest.TestCase):

    def setUp(self):
        self.spec = get_sample_spec()
        self.valid_contract = make_valid_contract()

    def test_valid_contract_passes(self):
        """Verify the real contract.json on disk passes all validation rules with 0 problems."""
        contract_path = os.path.join(repo_root, "contract.json")
        self.assertTrue(os.path.exists(contract_path), f"contract.json not found on disk at {contract_path}")
        with open(contract_path, "r", encoding="utf-8") as f:
            real_contract = json.load(f)
        problems = validate_contract(real_contract, self.spec)
        self.assertEqual(problems, [], f"Real contract.json failed validation: {problems}")

    def test_contract_schema_rejects_missing_class(self):
        """Test 1: take a valid contract, remove one class, assert validate_contract returns a problem naming that class."""
        contract = make_valid_contract()
        # Remove 'Admin' class
        contract["classes"] = [c for c in contract["classes"] if c["name"] != "Admin"]
        problems = validate_contract(contract, self.spec)

        self.assertTrue(len(problems) > 0, "Validation should have failed for missing class")
        named_problem = any("Admin" in p for p in problems)
        self.assertTrue(named_problem, f"Expected problem naming missing class 'Admin', got: {problems}")

    def test_contract_rejects_missing_admin_smoke_step(self):
        """Test 2: take a valid contract, remove any admin/update smoke_step, assert validation fails with a message about the admin flow."""
        contract = make_valid_contract()
        # Filter out any smoke steps referencing admin or update
        contract["smoke_steps"] = [
            s for s in contract["smoke_steps"]
            if "admin" not in s["purpose"].lower()
            and "admin" not in s["call"].lower()
            and "update" not in s["purpose"].lower()
            and "update" not in s["call"].lower()
        ]

        problems = validate_contract(contract, self.spec)
        self.assertTrue(len(problems) > 0, "Validation should fail when Admin smoke step is omitted")
        admin_problem = any("Admin" in p or "admin" in p.lower() or "update" in p.lower() for p in problems)
        self.assertTrue(admin_problem, f"Expected problem regarding missing Admin smoke step, got: {problems}")

    def test_contract_rejects_undeclared_smoke_call(self):
        """Test 3: add a smoke_step calling 'nonexistent_method', assert validation fails."""
        contract = make_valid_contract()
        contract["smoke_steps"].append({
            "call": "nonexistent_method",
            "args": [],
            "purpose": "Call invalid method"
        })

        problems = validate_contract(contract, self.spec)
        self.assertTrue(len(problems) > 0, "Validation should fail for undeclared smoke step call")
        call_problem = any("nonexistent_method" in p for p in problems)
        self.assertTrue(call_problem, f"Expected problem naming 'nonexistent_method', got: {problems}")

    def test_contract_rejects_bad_file_order(self):
        """Test 4: construct a files list where a later file is imported before it appears, assert validation fails."""
        contract = make_valid_contract()
        # Invert order: make models.py order 3 and gui.py order 1, but gui.py imports models.py
        contract["files"] = [
            {"path": "gui.py", "purpose": "GUI interface", "order": 1, "imports": ["models.py"]},
            {"path": "models.py", "purpose": "Domain models", "order": 3, "imports": []}
        ]

        problems = validate_contract(contract, self.spec)
        self.assertTrue(len(problems) > 0, "Validation should fail for dependency order violation")
        order_problem = any("File order violation" in p for p in problems)
        self.assertTrue(order_problem, f"Expected file order violation problem, got: {problems}")

    def test_forbidden_names_computed_from_tk(self):
        """Test 5: assert 'update' and 'pack' and 'grid' are in the forbidden_names set (from dir(tkinter.Misc) / Widget)."""
        names = compute_forbidden_names()
        self.assertIsInstance(names, list)
        self.assertIn("update", names, "'update' must be in forbidden names")
        self.assertIn("pack", names, "'pack' must be in forbidden names")
        self.assertIn("grid", names, "'grid' must be in forbidden names")

    def test_build_contract_prompt_is_generic(self):
        """Verify build_contract_prompt does not leak 'Space Fractions' into prompt text."""
        prompt = build_contract_prompt(self.spec)
        self.assertNotIn("Space Fractions", prompt, "Prompt must not contain brand name 'Space Fractions'")
        self.assertIn("Tkinter", prompt)
        self.assertIn("Calculator", prompt)

    def test_rejects_missing_create_app(self):
        """Fix 3.1: Contract missing create_app entrypoint taking root parameter is rejected."""
        contract = make_valid_contract()
        contract["entrypoints"] = [
            {"name": "launch", "signature": "launch() -> None", "purpose": "Start application"}
        ]
        problems = validate_contract(contract, self.spec)
        self.assertTrue(any("create_app" in p for p in problems), f"Expected create_app error, got: {problems}")

    def test_rejects_identifier_args_in_smoke_steps(self):
        """Fix 3.4: Reject smoke step args that are bare identifier strings like 'user', 'game', 'admin', 'questions'."""
        for bad_arg in ["user", "game", "admin", "questions"]:
            contract = make_valid_contract()
            contract["smoke_steps"][1]["args"] = [bad_arg]
            problems = validate_contract(contract, self.spec)
            self.assertTrue(
                any("bare identifier" in p for p in problems),
                f"Expected bare identifier rejection for '{bad_arg}', got: {problems}"
            )

    def test_rejects_missing_states_section(self):
        """Fix 3.5: Contract missing states or with fewer states than spec StateDiagram is rejected."""
        contract = make_valid_contract()
        # Missing states key
        del contract["states"]
        problems = validate_contract(contract, self.spec)
        self.assertTrue(any("states" in p for p in problems), f"Expected missing states error, got: {problems}")

        # Fewer states than spec (spec has 3 states: Playing, Paused, GameOver)
        contract2 = make_valid_contract()
        contract2["states"] = [{"name": "Playing", "owner": "Game", "attribute": "state"}]
        problems2 = validate_contract(contract2, self.spec)
        self.assertTrue(any("states" in p for p in problems2), f"Expected state count error, got: {problems2}")

    def test_rejects_missing_transitions(self):
        """Fix 3.6: Contract missing transitions or omitting triggers from spec StateDiagram is rejected."""
        contract = make_valid_contract()
        # Missing transitions key
        del contract["transitions"]
        problems = validate_contract(contract, self.spec)
        self.assertTrue(any("transitions" in p for p in problems), f"Expected missing transitions error, got: {problems}")

        # Transitions omitting 'pause' trigger
        contract2 = make_valid_contract()
        contract2["transitions"] = [
            {"trigger": "resume", "from": "Paused", "to": "Playing"},
            {"trigger": "gameOver", "from": "Playing", "to": "GameOver"}
        ]
        problems2 = validate_contract(contract2, self.spec)
        self.assertTrue(any("pause" in p for p in problems2), f"Expected missing trigger 'pause' error, got: {problems2}")


if __name__ == "__main__":
    unittest.main()
