import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from models import Game, Question, User, Admin
except ImportError:
    pass

class TestDomainModels(unittest.TestCase):

    def test_game_initialization(self):
        obj = Game("test", 0)
        self.assertIsNotNone(obj)
    def test_question_initialization(self):
        obj = Question("test", "test", "test", 0)
        self.assertIsNotNone(obj)
    def test_user_initialization(self):
        obj = User("test", "test")
        self.assertIsNotNone(obj)
    def test_admin_initialization(self):
        obj = Admin("test", "test")
        self.assertIsNotNone(obj)
