import tempfile
import unittest
from pathlib import Path

from src.verify import check_v4_call_resolution

BUG_FILES = {
    "engine.py": "class GameEngine:\n    def __init__(self):\n        self.current_question = None\n    def start(self): pass\n",
    "visual.py": "class FractionVisualizer:\n    def draw(self, q): pass\n",
    "hud.py": "import tkinter as tk\nclass HUD(tk.Frame):\n    def refresh(self, a): pass\n",
    "main.py": (
        "from engine import GameEngine\nfrom visual import FractionVisualizer\nfrom hud import HUD\n"
        "class App:\n    def __init__(self):\n        self.engine = GameEngine()\n"
        "        self.visualizer = FractionVisualizer()\n        self.hud = HUD()\n"
        "    def load(self):\n        self.engine.current_question()\n"
        "        self.visualizer.draw_question(1)\n        self.engine.progress()\n"
        "        self.hud.update(1)\n"
    ),
}

OK_FILES = {
    "hud.py": "import tkinter as tk\nclass HUD(tk.Frame):\n    def refresh(self, a): pass\nclass Base:\n    def shared(self): pass\nclass Child(Base): pass\n",
    "main.py": (
        "from hud import HUD, Child\nclass App:\n    def __init__(self, cb):\n"
        "        self.hud = HUD()\n        self.child = Child()\n        self.cb = cb\n"
        "    def go(self):\n        self.hud.pack()\n        self.hud.grid()\n        self.hud.configure()\n"
        "        self.hud.refresh(1)\n        self.child.shared()\n        self.cb()\n"
    ),
}


def _run(files):
    with tempfile.TemporaryDirectory() as d:
        for name, text in files.items():
            Path(d, name).write_text(text, encoding="utf-8")
        return check_v4_call_resolution(d)


class TestV4ProfessorBugs(unittest.TestCase):
    def setUp(self):
        self.msgs = [e["message"] for e in _run(BUG_FILES)]

    def test_attribute_called_as_method(self):
        self.assertTrue(any("current_question" in m for m in self.msgs))

    def test_missing_method_on_visualizer(self):
        self.assertTrue(any("draw_question" in m for m in self.msgs))

    def test_missing_method_on_engine(self):
        self.assertTrue(any("progress" in m for m in self.msgs))

    def test_tk_update_with_custom_args(self):
        self.assertTrue(any("'update'" in m and "Tk" in m for m in self.msgs))

    def test_inherited_and_callback_calls_not_flagged(self):
        self.assertEqual(_run(OK_FILES), [])


if __name__ == "__main__":
    unittest.main()
