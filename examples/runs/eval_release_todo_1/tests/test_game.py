import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from models import Task, TaskManager
except ImportError:
    pass

class TestDomainModels(unittest.TestCase):

    def test_task_initialization(self):
        obj = Task("test", "test", "test")
        self.assertIsNotNone(obj)
    def test_taskmanager_initialization(self):
        obj = TaskManager([])
        self.assertIsNotNone(obj)
