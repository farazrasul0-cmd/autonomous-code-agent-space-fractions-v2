import sys
import unittest
import tkinter as tk
from pathlib import Path

repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.insert(0, str(repo_dir))

from models import Game, Question, User, Admin
from app import Application
from main import create_app


class TestGame(unittest.TestCase):
    """Tests for the Game model class."""

    def test_init_and_properties(self):
        game = Game("g1", 0)
        self.assertEqual(game.id, "g1")
        self.assertEqual(game.score, 0)
        self.assertEqual(game.state, "Playing")

    def test_id_setter(self):
        game = Game("g1", 0)
        game.id = "g2"
        self.assertEqual(game.id, "g2")

    def test_score_setter(self):
        game = Game("g1", 0)
        game.score = 42
        self.assertEqual(game.score, 42)

    def test_state_setter(self):
        game = Game("g1", 0)
        game.state = "Paused"
        self.assertEqual(game.state, "Paused")

    def test_play(self):
        game = Game("g1", 0)
        game.state = "Paused"
        game.play()
        self.assertEqual(game.state, "Playing")

    def test_view_score(self):
        game = Game("g1", 10)
        self.assertEqual(game.view_score(), 10)

    def test_pause(self):
        game = Game("g1", 0)
        game.pause()
        self.assertEqual(game.state, "Paused")

    def test_resume(self):
        game = Game("g1", 0)
        game.pause()
        game.resume()
        self.assertEqual(game.state, "Playing")

    def test_game_over(self):
        game = Game("g1", 0)
        game.game_over()
        self.assertEqual(game.state, "GameOver")

    def test_state_transitions_pause_resume(self):
        game = Game("g1", 0)
        self.assertEqual(game.state, "Playing")
        game.pause()
        self.assertEqual(game.state, "Paused")
        game.resume()
        self.assertEqual(game.state, "Playing")

    def test_state_transition_end_game(self):
        game = Game("g1", 0)
        game.game_over()
        self.assertEqual(game.state, "GameOver")


class TestQuestion(unittest.TestCase):
    """Tests for the Question model class."""

    def test_init_and_properties(self):
        q = Question("q1", "What is 2+2?", ["1", "2", "4"], 2)
        self.assertEqual(q.id, "q1")
        self.assertEqual(q.prompt, "What is 2+2?")
        self.assertEqual(q.options, ["1", "2", "4"])
        self.assertEqual(q.answer_index, 2)

    def test_id_setter(self):
        q = Question("q1", "p", ["a"], 0)
        q.id = "q2"
        self.assertEqual(q.id, "q2")

    def test_prompt_setter(self):
        q = Question("q1", "p", ["a"], 0)
        q.prompt = "new prompt"
        self.assertEqual(q.prompt, "new prompt")

    def test_options_setter(self):
        q = Question("q1", "p", ["a"], 0)
        q.options = ["x", "y"]
        self.assertEqual(q.options, ["x", "y"])

    def test_answer_index_setter(self):
        q = Question("q1", "p", ["a"], 0)
        q.answer_index = 1
        self.assertEqual(q.answer_index, 1)

    def test_get_prompt(self):
        q = Question("q1", "hello", ["a"], 0)
        self.assertEqual(q.get_prompt(), "hello")

    def test_get_options(self):
        q = Question("q1", "p", ["a", "b"], 0)
        self.assertEqual(q.get_options(), ["a", "b"])

    def test_get_answer_index(self):
        q = Question("q1", "p", ["a", "b"], 1)
        self.assertEqual(q.get_answer_index(), 1)


class TestUser(unittest.TestCase):
    """Tests for the User model class."""

    def test_init_and_properties(self):
        user = User("u1", "alice")
        self.assertEqual(user.id, "u1")
        self.assertEqual(user.username, "alice")

    def test_id_setter(self):
        user = User("u1", "alice")
        user.id = "u2"
        self.assertEqual(user.id, "u2")

    def test_username_setter(self):
        user = User("u1", "alice")
        user.username = "bob"
        self.assertEqual(user.username, "bob")

    def test_play_game(self):
        user = User("u1", "alice")
        game = Game("g1", 0)
        user.play_game(game)
        self.assertEqual(game.state, "Playing")

    def test_view_score(self):
        user = User("u1", "alice")
        game = Game("g1", 25)
        self.assertEqual(user.view_score(game), 25)


class TestAdmin(unittest.TestCase):
    """Tests for the Admin model class."""

    def test_init_and_properties(self):
        admin = Admin("a1", "root")
        self.assertEqual(admin.id, "a1")
        self.assertEqual(admin.username, "root")

    def test_id_setter(self):
        admin = Admin("a1", "root")
        admin.id = "a2"
        self.assertEqual(admin.id, "a2")

    def test_username_setter(self):
        admin = Admin("a1", "root")
        admin.username = "admin2"
        self.assertEqual(admin.username, "admin2")

    def test_update_questions(self):
        admin = Admin("a1", "root")
        q1 = Question("q1", "p1", ["a", "b"], 0)
        q2 = Question("q2", "p2", ["c", "d"], 1)
        admin.update_questions([q1, q2])
        self.assertEqual(admin.questions, [q1, q2])

    def test_questions_setter(self):
        admin = Admin("a1", "root")
        q = Question("q1", "p", ["a"], 0)
        admin.questions = [q]
        self.assertEqual(admin.questions, [q])


class TestApplication(unittest.TestCase):
    """Tests for the Application class."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = Application(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_init_and_properties(self):
        self.assertIsInstance(self.app.root, tk.Tk)
        self.assertIsNone(self.app.current_user)
        self.assertIsNone(self.app.current_game)
        self.assertIsInstance(self.app.questions, list)

    def test_root_setter(self):
        new_root = tk.Tk()
        new_root.withdraw()
        try:
            self.app.root = new_root
            self.assertEqual(self.app.root, new_root)
        finally:
            new_root.destroy()

    def test_current_user_setter(self):
        user = User("u1", "alice")
        self.app.current_user = user
        self.assertEqual(self.app.current_user, user)

    def test_current_game_setter(self):
        game = Game("g1", 0)
        self.app.current_game = game
        self.assertEqual(self.app.current_game, game)

    def test_questions_setter(self):
        q = Question("q1", "p", ["a"], 0)
        self.app.questions = [q]
        self.assertEqual(self.app.questions, [q])

    def test_seed_questions(self):
        questions = Application._seed_questions()
        self.assertIsInstance(questions, list)
        self.assertTrue(len(questions) > 0)
        for q in questions:
            self.assertIsInstance(q, Question)

    def test_show_menu(self):
        self.app.show_menu()

    def test_show_play_game(self):
        self.app.show_play_game()

    def test_show_view_score(self):
        self.app.show_view_score()

    def test_show_update_questions(self):
        self.app.show_update_questions()

    def test_show_help(self):
        self.app.show_help()

    def test_start_play_game(self):
        self.app.start_play_game()
        self.assertIsNotNone(self.app.current_game)
        self.assertEqual(self.app.current_game.state, "Playing")

    def test_submit_answer_correct(self):
        self.app.start_play_game()
        question = self.app.questions[0]
        correct_index = question.answer_index
        initial_score = self.app.current_game.score
        self.app.submit_answer(correct_index)
        self.assertGreater(self.app.current_game.score, initial_score)

    def test_submit_answer_wrong(self):
        self.app.start_play_game()
        question = self.app.questions[0]
        wrong_index = (question.answer_index + 1) % len(question.options)
        initial_score = self.app.current_game.score
        self.app.submit_answer(wrong_index)
        self.assertEqual(self.app.current_game.score, initial_score)

    def test_toggle_pause(self):
        self.app.start_play_game()
        self.assertEqual(self.app.current_game.state, "Playing")
        self.app.toggle_pause()
        self.assertEqual(self.app.current_game.state, "Paused")
        self.app.toggle_pause()
        self.assertEqual(self.app.current_game.state, "Playing")

    def test_end_game(self):
        self.app.start_play_game()
        self.app.end_game()
        self.assertEqual(self.app.current_game.state, "GameOver")

    def test_update_questions(self):
        q1 = Question("q1", "p1", ["a", "b"], 0)
        q2 = Question("q2", "p2", ["c", "d"], 1)
        self.app.update_questions([q1, q2])
        self.assertEqual(self.app.questions, [q1, q2])

    def test_run(self):
        # run() should not raise; it may block, so we don't call it directly
        # in a way that hangs. Instead verify it is callable.
        self.assertTrue(callable(self.app.run))


class TestCreateApp(unittest.TestCase):
    """Tests for the create_app factory functions."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_create_app_from_main(self):
        app = create_app(self.root)
        self.assertIsInstance(app, Application)

    def test_create_app_from_app_module(self):
        from app import create_app as app_create_app
        app = app_create_app()
        self.assertIsInstance(app, Application)
        # Clean up the root created inside create_app
        if app.root is not None:
            try:
                app.root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    unittest.main()
