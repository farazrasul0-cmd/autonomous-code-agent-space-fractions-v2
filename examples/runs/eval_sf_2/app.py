"""Space Fractions - Standalone Windows Desktop Application.

This module implements the Application class, which provides the Tkinter
user interface and game logic for the Space Fractions quiz game.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional

from models import Game, Question, User, Admin


class Application:
    """Main application window and controller for Space Fractions."""

    SYSTEM_NAME = "Space Fractions"

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        """Initialize the application window and seed content.

        Args:
            root: An optional existing Tk root window. If None, a new one
                is created.
        """
        self._root = root if root is not None else tk.Tk()
        self._root.title(self.SYSTEM_NAME)
        self._root.geometry("720x560")
        self._root.minsize(560, 420)

        # Seed content so the game is immediately playable.
        self._questions: List[Question] = self._seed_questions()

        # Application state.
        self._current_user: Optional[User] = User("u1", "Player")
        self._current_game: Optional[Game] = None

        # Internal UI state (not part of the public contract).
        self._screen_frame: Optional[tk.Frame] = None
        self._status_var: tk.StringVar = tk.StringVar(value="Ready")
        self._question_index: int = 0
        self._answer_buttons: List[tk.Button] = []
        self._question_label: Optional[tk.Label] = None
        self._score_label: Optional[tk.Label] = None
        self._pause_button: Optional[tk.Button] = None
        self._end_button: Optional[tk.Button] = None
        self._status_label: Optional[tk.Label] = None

        self.show_menu()

    # ------------------------------------------------------------------
    # Public attributes (contract)
    # ------------------------------------------------------------------
    @property
    def root(self) -> tk.Tk:
        """Return the Tk root window."""
        return self._root

    @root.setter
    def root(self, value: tk.Tk) -> None:
        self._root = value

    @property
    def current_user(self) -> Optional[User]:
        """Return the current user."""
        return self._current_user

    @current_user.setter
    def current_user(self, value: Optional[User]) -> None:
        self._current_user = value

    @property
    def current_game(self) -> Optional[Game]:
        """Return the current game."""
        return self._current_game

    @current_game.setter
    def current_game(self, value: Optional[Game]) -> None:
        self._current_game = value

    @property
    def questions(self) -> List[Question]:
        """Return the list of questions."""
        return self._questions

    @questions.setter
    def questions(self, value: List[Question]) -> None:
        self._questions = value

    # ------------------------------------------------------------------
    # Seed content
    # ------------------------------------------------------------------
    @staticmethod
    def _seed_questions() -> List[Question]:
        """Return a default list of Question instances."""
        return [
            Question(
                "q1",
                "What is 1/2 + 1/4?",
                ["1/4", "3/4", "1/2", "1"],
                1,
            ),
            Question(
                "q2",
                "What is 2/3 - 1/6?",
                ["1/2", "1/3", "1/6", "2/3"],
                0,
            ),
            Question(
                "q3",
                "What is 3/5 * 5/3?",
                ["1", "9/25", "3/5", "5/3"],
                0,
            ),
            Question(
                "q4",
                "What is 1/2 divided by 1/4?",
                ["1/8", "1/2", "2", "4"],
                2,
            ),
            Question(
                "q5",
                "Which fraction is equivalent to 0.75?",
                ["1/3", "2/3", "3/4", "4/5"],
                2,
            ),
        ]

    # ------------------------------------------------------------------
    # Screen management helpers
    # ------------------------------------------------------------------
    def _clear_screen(self) -> None:
        """Destroy the current screen frame, if any."""
        if self._screen_frame is not None:
            self._screen_frame.destroy()
            self._screen_frame = None

    def _new_screen(self) -> tk.Frame:
        """Create and return a fresh screen frame."""
        self._clear_screen()
        frame = tk.Frame(self._root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        self._screen_frame = frame
        return frame

    def _set_status(self, message: str) -> None:
        """Update the non-blocking status label."""
        self._status_var.set(message)
        if self._status_label is not None:
            self._status_label.config(text=message)

    def _make_nav_bar(self, frame: tk.Frame, active: str) -> None:
        """Create a navigation bar with buttons for each screen."""
        nav = tk.Frame(frame)
        nav.pack(fill="x", pady=(0, 12))

        buttons = [
            ("Main Menu", self.show_menu, "menu"),
            ("Play Game", self.show_play_game, "play"),
            ("View Score", self.show_view_score, "score"),
            ("Update Questions", self.show_update_questions, "update"),
            ("Help", self.show_help, "help"),
        ]

        for text, command, key in buttons:
            style = "Accent.TButton" if key == active else "TButton"
            tk.Button(nav, text=text, command=command, style=style).pack(
                side="left", padx=4
            )

    def _make_status_bar(self, frame: tk.Frame) -> None:
        """Create a status label at the bottom of the screen."""
        self._status_label = tk.Label(
            frame,
            textvariable=self._status_var,
            anchor="w",
            relief="sunken",
            padx=8,
            pady=4,
        )
        self._status_label.pack(side="bottom", fill="x", pady=(12, 0))

    # ------------------------------------------------------------------
    # Screen navigation methods
    # ------------------------------------------------------------------
    def show_menu(self) -> None:
        """Navigate to the main menu screen."""
        frame = self._new_screen()
        self._make_nav_bar(frame, "menu")

        tk.Label(
            frame,
            text=self.SYSTEM_NAME,
            font=("Segoe UI", 28, "bold"),
        ).pack(pady=(20, 8))

        tk.Label(
            frame,
            text="A fraction quiz adventure through space!",
            font=("Segoe UI", 12),
        ).pack(pady=(0, 24))

        tk.Button(
            frame,
            text="Start Game",
            command=self.start_play_game,
            width=24,
            style="Accent.TButton",
        ).pack(pady=6)

        tk.Button(
            frame,
            text="View Score",
            command=self.show_view_score,
            width=24,
        ).pack(pady=6)

        tk.Button(
            frame,
            text="Update Questions",
            command=self.show_update_questions,
            width=24,
        ).pack(pady=6)

        tk.Button(
            frame,
            text="Help",
            command=self.show_help,
            width=24,
        ).pack(pady=6)

        self._make_status_bar(frame)
        self._set_status("Main menu")

    def show_play_game(self) -> None:
        """Navigate to the game screen."""
        frame = self._new_screen()
        self._make_nav_bar(frame, "play")

        tk.Label(
            frame,
            text="Play Game",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(8, 12))

        if self._current_game is None:
            tk.Label(
                frame,
                text="No game in progress. Start a new game to begin.",
                font=("Segoe UI", 11),
            ).pack(pady=20)
            tk.Button(
                frame,
                text="Start New Game",
                command=self.start_play_game,
                style="Accent.TButton",
            ).pack(pady=8)
        else:
            self._render_game_widgets(frame)

        self._make_status_bar(frame)
        self._set_status("Game screen")

    def show_view_score(self) -> None:
        """Navigate to the score screen."""
        frame = self._new_screen()
        self._make_nav_bar(frame, "score")

        tk.Label(
            frame,
            text="View Score",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(8, 12))

        if self._current_game is None:
            score_text = "No game has been played yet."
        else:
            score_text = f"Current score: {self._current_game.score}"

        tk.Label(
            frame,
            text=score_text,
            font=("Segoe UI", 14),
        ).pack(pady=20)

        self._make_status_bar(frame)
        self._set_status("Score screen")

    def show_update_questions(self) -> None:
        """Navigate to the admin questions screen."""
        frame = self._new_screen()
        self._make_nav_bar(frame, "update")

        tk.Label(
            frame,
            text="Update Questions",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(8, 12))

        tk.Label(
            frame,
            text=f"Current question count: {len(self._questions)}",
            font=("Segoe UI", 11),
        ).pack(pady=(0, 12))

        # Non-blocking admin controls (no modal dialogs).
        tk.Button(
            frame,
            text="Clear All Questions",
            command=lambda: self.update_questions([]),
            width=24,
        ).pack(pady=6)

        tk.Button(
            frame,
            text="Restore Default Questions",
            command=lambda: self.update_questions(self._seed_questions()),
            width=24,
        ).pack(pady=6)

        self._make_status_bar(frame)
        self._set_status("Admin questions screen")

    def show_help(self) -> None:
        """Navigate to the help screen."""
        frame = self._new_screen()
        self._make_nav_bar(frame, "help")

        tk.Label(
            frame,
            text=self.SYSTEM_NAME,
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(8, 12))

        help_text = (
            "Welcome to Space Fractions!\n\n"
            "How to play:\n"
            "1. Click 'Start Game' from the main menu.\n"
            "2. Read each fraction question and choose an answer.\n"
            "3. Correct answers increase your score.\n"
            "4. Use Pause/Resume to take a break.\n"
            "5. End the game to see your final score.\n\n"
            "Admins can update questions from the 'Update Questions' screen."
        )

        tk.Label(
            frame,
            text=help_text,
            font=("Segoe UI", 11),
            justify="left",
        ).pack(pady=12)

        self._make_status_bar(frame)
        self._set_status("Help screen")

    # ------------------------------------------------------------------
    # Game logic methods
    # ------------------------------------------------------------------
    def start_play_game(self) -> None:
        """Navigate to the play screen and initialize game state."""
        self._current_game = Game("g1", 0)
        self._current_game.play()
        self._question_index = 0

        if self._current_user is not None:
            self._current_user.play_game(self._current_game)

        self.show_play_game()
        self._set_status("Game started - Playing")

    def _render_game_widgets(self, frame: tk.Frame) -> None:
        """Render the in-game widgets for the current question."""
        game = self._current_game
        if game is None:
            return

        self._score_label = tk.Label(
            frame,
            text=f"Score: {game.score}",
            font=("Segoe UI", 14, "bold"),
        )
        self._score_label.pack(pady=(0, 8))

        state_label = tk.Label(
            frame,
            text=f"State: {game.state}",
            font=("Segoe UI", 11),
        )
        state_label.pack(pady=(0, 12))

        if not self._questions:
            self._question_label = tk.Label(
                frame,
                text="No questions available.",
                font=("Segoe UI", 14),
            )
            self._question_label.pack(pady=20)
            return

        if self._question_index >= len(self._questions):
            self._question_index = 0

        question = self._questions[self._question_index]

        self._question_label = tk.Label(
            frame,
            text=question.prompt,
            font=("Segoe UI", 16, "bold"),
            wraplength=600,
        )
        self._question_label.pack(pady=16)

        self._answer_buttons = []
        for idx, option in enumerate(question.options):
            button = tk.Button(
                frame,
                text=option,
                width=32,
                command=lambda i=idx: self.submit_answer(i),
            )
            button.pack(pady=4)
            self._answer_buttons.append(button)

        controls = tk.Frame(frame)
        controls.pack(pady=16)

        self._pause_button = tk.Button(
            controls,
            text="Pause",
            command=self.toggle_pause,
            width=12,
        )
        self._pause_button.pack(side="left", padx=6)

        self._end_button = tk.Button(
            controls,
            text="End Game",
            command=self.end_game,
            width=12,
        )
        self._end_button.pack(side="left", padx=6)

    def submit_answer(self, answer_index: int) -> None:
        """Submit an answer for the current question.

        Args:
            answer_index: The index of the selected answer option.
        """
        game = self._current_game
        if game is None:
            self._set_status("No active game")
            return

        if game.state != "Playing":
            self._set_status("Game is not currently playing")
            return

        if not self._questions:
            self._set_status("No questions available")
            return

        if self._question_index >= len(self._questions):
            self._question_index = 0

        question = self._questions[self._question_index]

        if answer_index == question.answer_index:
            game.score += 1
            self._set_status("Correct!")
        else:
            self._set_status("Incorrect.")

        # Advance to the next question.
        self._question_index += 1
        if self._question_index >= len(self._questions):
            self._question_index = 0

        self._refresh_game_screen()

    def toggle_pause(self) -> None:
        """Toggle pause/resume state of the current game."""
        game = self._current_game
        if game is None:
            self._set_status("No active game")
            return

        if game.state == "Playing":
            game.pause()
            self._set_status("Game paused")
        elif game.state == "Paused":
            game.resume()
            self._set_status("Game resumed")
        else:
            self._set_status("Cannot pause a finished game")

        self._refresh_game_screen()

    def end_game(self) -> None:
        """Transition the current Game.state to GameOver."""
        game = self._current_game
        if game is None:
            self._set_status("No active game")
            return

        game.game_over()
        self._set_status("Game over")
        self._refresh_game_screen()

    def update_questions(self, questions: list) -> None:
        """Update the questions list (Admin flow).

        Args:
            questions: A list of Question instances.
        """
        self._questions = list(questions)
        self._set_status(f"Questions updated ({len(self._questions)} total)")

        # Refresh the current screen if it is the admin screen.
        if self._screen_frame is not None:
            self.show_update_questions()

    def _refresh_game_screen(self) -> None:
        """Re-render the game screen to reflect current state."""
        if self._screen_frame is None:
            return

        # Only refresh if we are on the play screen.
        self.show_play_game()

    # ------------------------------------------------------------------
    # Application entry point
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Start the Tkinter main event loop."""
        self._root.mainloop()


def create_app() -> Application:
    """Create and return an Application instance for smoke testing."""
    return Application()


if __name__ == "__main__":
    app = Application()
    app.run()
