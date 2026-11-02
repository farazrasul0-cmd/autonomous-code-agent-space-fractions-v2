# tests/test_parser.py - Unit tests for architecture parser and spec.json generation
import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

# Ensure src/ is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.parser import (
    parse_architecture,
    extract_blocks,
    split_headings,
    extract_requirements,
    extract_warnings,
)


class TestParser(unittest.TestCase):
    def setUp(self):
        self.doc_path = os.path.join(repo_root, "examples", "inputs", "Architecture_Documentation.md")
        self.view_path = os.path.join(repo_root, "examples", "inputs", "Architecture_View.md")

    def test_diagram_count(self):
        """Test 1: count actual diagram blocks in Architecture_View.md (13) vs parsed count."""
        self.assertTrue(os.path.exists(self.view_path), f"File not found: {self.view_path}")
        with open(self.view_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Count occurrences of @startuml in markdown
        raw_startuml_count = content.count("@startuml")
        self.assertEqual(raw_startuml_count, 13, f"Expected 13 @startuml markers, got {raw_startuml_count}")

        blocks = extract_blocks(content)
        self.assertEqual(len(blocks), 13, f"Expected extract_blocks to find 13 blocks, found {len(blocks)}")

        spec, _ = parse_architecture(self.doc_path, self.view_path)
        self.assertEqual(spec["diagram_count"], 13, f"Expected spec['diagram_count'] == 13, got {spec['diagram_count']}")
        self.assertEqual(len(spec["diagrams"]), 13, f"Expected 13 parsed diagrams, got {len(spec['diagrams'])}")

    def test_empty_and_no_diagrams(self):
        """Test 2: handles empty files and files with no plantuml blocks without crashing."""
        # Empty string calls
        self.assertEqual(extract_blocks(""), [])
        self.assertEqual(extract_blocks("No plantuml code here at all."), [])

        sections = split_headings("")
        self.assertIsInstance(sections, dict)

        reqs = extract_requirements("")
        self.assertEqual(reqs, [])

        warns = extract_warnings("", "", [])
        self.assertEqual(warns, [])

        # Parse with non-existent / empty files
        spec_empty, json_empty = parse_architecture("", "")
        self.assertEqual(spec_empty["diagram_count"], 0)
        self.assertEqual(spec_empty["diagrams"], {})
        self.assertTrue(isinstance(json.loads(json_empty), dict))

        # Parse with actual empty temporary files
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as f_doc, \
             tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as f_view:
            f_doc_path = f_doc.name
            f_view_path = f_view.name
            f_doc.write("# Simple Markdown\nNo diagrams here.\n")
            f_view.write("# Views\nJust plain text.\n")

        try:
            spec_temp, json_temp = parse_architecture(f_doc_path, f_view_path)
            self.assertEqual(spec_temp["diagram_count"], 0)
            self.assertEqual(spec_temp["diagrams"], {})
            self.assertIn("conflicts", spec_temp)
            self.assertTrue(len(json_temp) > 0)
        finally:
            if os.path.exists(f_doc_path):
                os.remove(f_doc_path)
            if os.path.exists(f_view_path):
                os.remove(f_view_path)

    def test_core_extraction(self):
        """Test 3: extracts 4 classes, 4 use cases, 3 states."""
        spec, _ = parse_architecture(self.doc_path, self.view_path)

        # 4 classes: Game, Question, User, Admin
        self.assertIn("ClassDiagram", spec["diagrams"])
        extracted_classes = [c["name"] for c in spec["diagrams"]["ClassDiagram"]["classes"]]
        expected_classes = ["Game", "Question", "User", "Admin"]
        for c in expected_classes:
            self.assertIn(c, extracted_classes, f"Class {c} missing from extracted classes: {extracted_classes}")
        self.assertEqual(len(extracted_classes), 4)

        # 4 use cases: Play Game, View Score, View Help, Update Questions
        self.assertIn("UseCaseDiagram", spec["diagrams"])
        extracted_usecases = spec["diagrams"]["UseCaseDiagram"]["usecases"]
        expected_usecases = ["Play Game", "View Score", "View Help", "Update Questions"]
        for uc in expected_usecases:
            self.assertIn(uc, extracted_usecases, f"Use case '{uc}' missing from extracted usecases: {extracted_usecases}")
        self.assertEqual(len(extracted_usecases), 4)

        # 3 states: Playing, Paused, GameOver
        self.assertIn("StateDiagram", spec["diagrams"])
        extracted_states = spec["diagrams"]["StateDiagram"]["states"]
        expected_states = ["Playing", "Paused", "GameOver"]
        for st in expected_states:
            self.assertIn(st, extracted_states, f"State '{st}' missing from extracted states: {extracted_states}")
        self.assertEqual(len(extracted_states), 3)

        # PackageDiagram must be classified as package, not class
        self.assertIn("PackageDiagram", spec["diagrams"])
        self.assertEqual(spec["diagrams"]["PackageDiagram"]["kind"], "package")
        self.assertIn("Game", spec["diagrams"]["PackageDiagram"]["elements"])

    def test_conflicts_entry(self):
        """Test 4: conflicts entry specifies 'desktop' resolution."""
        spec, _ = parse_architecture(self.doc_path, self.view_path)
        self.assertIn("conflicts", spec)
        conflicts = spec["conflicts"]
        self.assertIn("prescribed_stack", conflicts)
        self.assertIn("assignment_requirement", conflicts)
        self.assertIn("resolution", conflicts)
        self.assertIn("desktop", conflicts["resolution"].lower(), "Resolution must specify desktop target")

    def test_spec_size_under_6000(self):
        """Test 5: spec.json size strictly < 6000 bytes on real input."""
        spec, json_str = parse_architecture(self.doc_path, self.view_path)
        byte_size = len(json_str.encode("utf-8"))
        self.assertLess(byte_size, 6000, f"spec.json size {byte_size} bytes exceeds 6000-byte cap")

        # Also verify the committed spec.json file on disk
        disk_spec_path = os.path.join(repo_root, "spec.json")
        if os.path.exists(disk_spec_path):
            disk_size = os.path.getsize(disk_spec_path)
            self.assertLess(disk_size, 6000, f"spec.json on disk ({disk_size} bytes) exceeds 6000-byte cap")

    def test_sequence_message_counts(self):
        """Test 6: assert len(SequenceDiagram1 messages) == 8 and len(SequenceDiagram2 messages) == 2."""
        spec, _ = parse_architecture(self.doc_path, self.view_path)
        self.assertIn("SequenceDiagram1", spec["diagrams"])
        self.assertIn("SequenceDiagram2", spec["diagrams"])
        seq1_msgs = spec["diagrams"]["SequenceDiagram1"]["messages"]
        seq2_msgs = spec["diagrams"]["SequenceDiagram2"]["messages"]
        self.assertEqual(len(seq1_msgs), 8, f"Expected 8 messages in SequenceDiagram1, got {len(seq1_msgs)}")
        self.assertEqual(len(seq2_msgs), 2, f"Expected 2 messages in SequenceDiagram2, got {len(seq2_msgs)}")

    def test_genericity(self):
        """Test 7: parse minimal synthetic document pair without cloud mentions.
        Assert (a) system_name is not 'Space Fractions',
               (b) conflicts is empty or explicitly 'no cloud/desktop conflict detected',
               (c) the diagram count matches the synthetic input.
        """
        synth_doc = """# QuizMaster Architecture Documentation
The QuizMaster system is an offline quiz tool for classroom practice.

# Requirements
| FR-1 | User can answer multiple choice questions |
"""
        synth_view = """# Diagrams

```plantuml
@startuml UseCaseDiagram
actor Student
usecase "Take Quiz" as (TakeQuiz)
Student -- (TakeQuiz)
@enduml
```

```plantuml
@startuml ClassDiagram
class Quiz {
  - title: string
  + start(): void
}
@enduml
```

```plantuml
@startuml SequenceDiagram
participant Student
participant Quiz
Student ->> Quiz: start()
@enduml
```
"""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md", encoding="utf-8") as f_doc, \
             tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md", encoding="utf-8") as f_view:
            f_doc_path = f_doc.name
            f_view_path = f_view.name
            f_doc.write(synth_doc)
            f_view.write(synth_view)

        try:
            synth_spec, _ = parse_architecture(f_doc_path, f_view_path)
            # (a) system_name is not "Space Fractions"
            self.assertNotEqual(synth_spec["system_name"], "Space Fractions")
            self.assertEqual(synth_spec["system_name"], "QuizMaster")

            # (b) conflicts is empty or explicitly "no cloud/desktop conflict detected"
            conflicts = synth_spec["conflicts"]
            if conflicts:
                self.assertEqual(conflicts.get("resolution"), "no cloud/desktop conflict detected")

            # (c) diagram count matches synthetic input (3)
            self.assertEqual(synth_spec["diagram_count"], 3)
            self.assertEqual(len(synth_spec["diagrams"]), 3)
        finally:
            if os.path.exists(f_doc_path):
                os.remove(f_doc_path)
            if os.path.exists(f_view_path):
                os.remove(f_view_path)


if __name__ == "__main__":
    unittest.main()
