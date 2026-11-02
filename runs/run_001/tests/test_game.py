import sys
import unittest
import tkinter as tk
from pathlib import Path

repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.insert(0, str(repo_dir))

from models import Game, Question, User, Admin
from app import App
from main import create_app


class TestGame(unittest.TestCase):
    """Tests for the Game model."""

    def test_init_and_view_score(self):
        game = Game(id=1, score=10)
        self.assertEqual(game.id, 1)
        self.assertEqual(game.view_score(), 10)

    def test_play(self):
        game = Game(id=1, score=0)
        game.play()
        # play() should not raise and should leave score unchanged
        self.assertEqual(game.view_score(), 0)

    def test_pause_resume_state_transitions(self):
        game = Game(id=1, score=5)
        # Initial state should be Playing
        self.assertEqual(game.state, "Playing")

        game.pause()
        self.assertEqual(game.state, "Paused")

        game.resume()
        self.assertEqual(game.state, "Playing")

        # Pause again to verify repeated transitions
        game.pause()
        self.assertEqual(game.state, "Paused")
        game.resume()
        self.assertEqual(game.state, "Playing")

    def test_game_over_state_transition(self):
        game = Game(id=1, score=5)
        game.game_over()
        self.assertEqual(game.state, "GameOver")


class TestQuestion(unittest.TestCase):
    """Tests for the Question model."""

    def test_init_and_getters(self):
        options = ["A", "B", "C", "D"]
        q = Question(id=1, prompt="What is 2+2?", options=options, answer_index=2)
        self.assertEqual(q.id, 1)
        self.assertEqual(q.get_prompt(), "What is 2+2?")
        self.assertEqual(q.get_options(), options)
        self.assertEqual(q.get_answer_index(), 2)

    def test_options_are_copied(self):
        options = ["A", "B"]
        q = Question(id=1, prompt="P", options=options, answer_index=0)
        # Mutating the original list should not affect the question's options
        options.append("C")
        self.assertEqual(q.get_options(), ["A", "B"])


class TestUser(unittest.TestCase):
    """Tests for the User model."""

    def test_init(self):
        user = User(id=1, username="alice")
        self.assertEqual(user.id, 1)
        self.assertEqual(user.username, "alice")

    def test_play_game_and_view_score(self):
        user = User(id=1, username="alice")
        game = Game(id=10, score=42)
        user.play_game(game)
        self.assertEqual(user.view_score(game), 42)


class TestAdmin(unittest.TestCase):
    """Tests for the Admin model."""

    def test_init(self):
        admin = Admin(id=1, username="root")
        self.assertEqual(admin.id, 1)
        self.assertEqual(admin.username, "root")

    def test_update_questions(self):
        admin = Admin(id=1, username="root")
        questions = [
            Question(id=1, prompt="Q1", options=["a", "b"], answer_index=0),
            Question(id=2, prompt="Q2", options=["c", "d"], answer_index=1),
        ]
        admin.update_questions(questions)
        self.assertEqual(admin.questions, questions)


class TestApp(unittest.TestCase):
    """Tests for the App GUI class."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = App(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_init(self):
        self.assertIsNotNone(self.app)
        self.assertIs(self.app.root, self.root)

    def test_seed_questions(self):
        questions = App._seed_questions()
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)
        for q in questions:
            self.assertIsInstance(q, Question)
            self.assertIsInstance(q.get_prompt(), str)
            self.assertIsInstance(q.get_options(), list)
            self.assertIsInstance(q.get_answer_index(), int)

    def test_show_menu(self):
        self.app.show_menu()
        # Should not raise; menu frame should be created
        self.assertIsNotNone(self.app.current_frame)

    def test_show_play_game(self):
        self.app.show_play_game()
        self.assertIsNotNone(self.app.current_frame)

    def test_show_view_score(self):
        self.app.show_view_score()
        self.assertIsNotNone(self.app.current_frame)

    def test_show_update_questions(self):
        self.app.show_update_questions()
        self.assertIsNotNone(self.app.current_frame)

    def test_show_help(self):
        self.app.show_help()
        self.assertIsNotNone(self.app.current_frame)

    def test_start_play_game(self):
        self.app.start_play_game()
        self.assertIsNotNone(self.app.current_frame)

    def test_submit_answer_correct(self):
        self.app.start_play_game()
        # Ensure a question is rendered
        self.app._render_question()
        answer_index = self.app.current_question.get_answer_index()
        self.app.submit_answer(answer_index)
        # Correct answer should increment score
        self.assertGreaterEqual(self.app.game.view_score(), 1)

    def test_submit_answer_wrong(self):
        self.app.start_play_game()
        self.app._render_question()
        correct = self.app.current_question.get_answer_index()
        wrong = (correct + 1) % len(self.app.current_question.get_options())
        self.app.submit_answer(wrong)
        # Wrong answer should not increment score
        self.assertEqual(self.app.game.view_score(), 0)

    def test_toggle_pause(self):
        self.app.start_play_game()
        self.app.toggle_pause()
        self.assertEqual(self.app.game.state, "Paused")
        self.app.toggle_pause()
        self.assertEqual(self.app.game.state, "Playing")

    def test_end_game(self):
        self.app.start_play_game()
        self.app.end_game()
        self.assertEqual(self.app.game.state, "GameOver")

    def test_update_questions(self):
        questions = [
            Question(id=1, prompt="New Q1", options=["x", "y"], answer_index=0),
        ]
        self.app.update_questions(questions)
        self.assertEqual(self.app.questions, questions)


class TestCreateApp(unittest.TestCase):
    """Tests for the create_app factory in main.py."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_create_app_returns_app(self):
        app = create_app(self.root)
        self.assertIsInstance(app, App)
        self.assertIs(app.root, self.root)


if __name__ == "__main__":
    unittest.main()
