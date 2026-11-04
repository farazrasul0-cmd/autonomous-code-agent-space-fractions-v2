import unittest
import sys
import inspect
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from models import Task, TaskManager
except ImportError:
    pass

def make(cls):
    args = []
    for n, p in list(inspect.signature(cls.__init__).parameters.items())[1:]:
        if p.default is not p.empty or p.kind in (
            p.VAR_POSITIONAL,
            p.VAR_KEYWORD,
        ):
            continue
        a = str(p.annotation).lower()
        if "int" in a:
            args.append(0)
        elif "float" in a:
            args.append(0.0)
        elif "list" in a:
            args.append([])
        elif "bool" in a:
            args.append(False)
        elif "str" in a or n in ("id", "name", "username", "prompt", "title"):
            args.append("test")
        else:
            args.append(None)
    return cls(*args)

class TestDomainModels(unittest.TestCase):

    def test_task_initialization(self):
        obj = make(Task)
        self.assertIsNotNone(obj)
    def test_taskmanager_initialization(self):
        obj = make(TaskManager)
        self.assertIsNotNone(obj)
