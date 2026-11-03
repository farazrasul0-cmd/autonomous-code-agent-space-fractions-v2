"""Space Fractions - Standalone Windows desktop application controller.

This module implements the :class:`App` controller class, which owns the
Tkinter root window and coordinates navigation between the application's
screens (Main Menu, Play Game, View Score, Update Questions, Help).
"""

import tkinter as tk
from typing import List

from models import Admin, Game, Question, User


class App:
    """Application controller for the Space Fractions desktop app.

    The controller manages the Tkinter root window, the currently active
    game, and the list of questions used by the game.  It provides screen
    navigation methods and game-play state transitions.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application controller.

        Parameters
        ----------
        root : tk.Tk
            The Tkinter root window that hosts the application UI.
        """
        self._root = root
        self._current_game = None
        self._questions = self._seed_questions()

        # Internal UI state (not part of the public contract surface).
        self._current_frame = None
        self._question_index = 0
        self._status_label = None
        self._question_label = None
        self._score_label = None
        self._pause_button = None
        self._option_buttons = []

        self._root.title("Space Fractions")
        self._root.geometry("720x520")
        self._root.minsize(560, 420)

        self.show_menu()

    # ------------------------------------------------------------------
    # Public attributes (contract surface)
    # ------------------------------------------------------------------
    @property
    def root(self) -> tk.Tk:
        """Return the Tkinter root window."""
        return self._root

    @root.setter
    def root(self, value: tk.Tk) -> None:
        self._root = value

    @property
    def current_game(self):
        """Return the currently active game, if any."""
        return self._current_game

    @current_game.setter
    def current_game(self, value) -> None:
        self._current_game = value

    @property
    def questions(self):
        """Return the list of questions used by the game."""
        return self._questions

    @questions.setter
    def questions(self, value) -> None:
        self._questions = value

    # ------------------------------------------------------------------
    # Seed content
    # ------------------------------------------------------------------
    @staticmethod
    def _seed_questions():
        """Return a default list of questions so the game is playable on launch."""
        return [
            Question(
                id="q1",
                prompt="What is 1/2 + 1/4?",
                options=["1/4", "3/4", "2/6", "1/8"],
                answer_index=1,
            ),
            Question(
                id="q2",
                prompt="What is 2/3 - 1/6?",
                options=["1/2", "1/3", "1/6", "2/6"],
                answer_index=0,
            ),
            Question(
                id="q3",
                prompt="What is 3/5 * 2/3?",
                options=["6/15", "5/8", "2/5", "1/5"],
                answer_index=2,
            ),
            Question(
                id="q4",
                prompt="What is 3/4 divided by 1/2?",
                options=["3/8", "1 1/2", "2/3", "3/2"],
                answer_index=1,
            ),
            Question(
                id="q5",
                prompt="Which fraction is equivalent to 1/2?",
                options=["2/3", "3/6", "4/6", "5/8"],
                answer_index=1,
            ),
        ]

    # ------------------------------------------------------------------
    # Screen navigation
    # ------------------------------------------------------------------
    def _clear_screen(self) -> None:
        """Destroy the current screen frame and reset transient UI state."""
        if self._current_frame is not None:
            self._current_frame.destroy()
            self._current_frame = None
        self._status_label = None
        self._question_label = None
        self._score_label = None
        self._pause_button = None
        self._option_buttons = []

    def _new_frame(self) -> tk.Frame:
        """Create and return a fresh frame that fills the root window."""
        frame = tk.Frame(self._root, padx=24, pady=24)
        frame.pack(fill=tk.BOTH, expand=True)
        self._current_frame = frame
        return frame

    def _back_button(self, frame: tk.Frame) -> None:
        """Add a standard 'Back to Menu' button to a screen frame."""
        tk.Button(
            frame,
            text="Back to Menu",
            command=self.show_menu,
            width=18,
        ).pack(pady=(20, 0))

    def show_menu(self) -> None:
        """Navigate to the main menu screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Space Fractions",
            font=("Segoe UI", 28, "bold"),
        ).pack(pady=(10, 30))

        tk.Button(
            frame,
            text="Play Game",
            command=self.start_play_game,
            width=24,
            height=2,
        ).pack(pady=6)

        tk.Button(
            frame,
            text="View Score",
            command=self.show_view_score,
            width=24,
            height=2,
        ).pack(pady=6)

        tk.Button(
            frame,
            text="Update Questions",
            command=self.show_update_questions,
            width=24,
            height=2,
        ).pack(pady=6)

        tk.Button(
            frame,
            text="Help",
            command=self.show_help,
            width=24,
            height=2,
        ).pack(pady=6)

    def show_play_game(self) -> None:
        """Navigate to the game screen.

        This method renders the play screen.  If no game is active, it
        initializes one via :meth:`start_play_game`; otherwise it renders
        the current game state.
        """
        if self._current_game is None:
            self.start_play_game()
            return

        self._render_play_screen()

    def show_view_score(self) -> None:
        """Navigate to the score screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="View Score",
            font=("Segoe UI", 22, "bold"),
        ).pack(pady=(10, 20))

        if self._current_game is not None:
            score_text = f"Current Score: {self._current_game.score}"
        else:
            score_text = "No game has been played yet."

        tk.Label(frame, text=score_text, font=("Segoe UI", 14)).pack(pady=10)

        self._back_button(frame)

    def show_update_questions(self) -> None:
        """Navigate to the admin questions screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Update Questions",
            font=("Segoe UI", 22, "bold"),
        ).pack(pady=(10, 20))

        tk.Label(
            frame,
            text="Admin question management",
            font=("Segoe UI", 12),
        ).pack(pady=5)

        count_label = tk.Label(
            frame,
            text=f"Current question count: {len(self._questions)}",
            font=("Segoe UI", 12),
        )
        count_label.pack(pady=5)

        # Non-blocking feedback label for admin actions.
        status = tk.Label(frame, text="", fg="#0066cc", font=("Segoe UI", 11))
        status.pack(pady=10)
        self._status_label = status

        tk.Button(
            frame,
            text="Reset to Default Questions",
            command=self._reset_default_questions,
            width=24,
        ).pack(pady=6)

        self._back_button(frame)

    def show_help(self) -> None:
        """Navigate to the help screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Space Fractions",
            font=("Segoe UI", 22, "bold"),
        ).pack(pady=(10, 10))

        tk.Label(
            frame,
            text="Help",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(0, 15))

        help_text = (
            "Space Fractions is a quiz game that helps you practice\n"
            "fraction arithmetic.\n\n"
            "• Play Game: answer each question by selecting an option.\n"
            "• Pause/Resume: pause or resume the current session.\n"
            "• View Score: see your current score.\n"
            "• Update Questions: manage the question bank.\n\n"
            "Correct answers increase your score by one point."
        )
        tk.Label(
            frame,
            text=help_text,
            justify=tk.LEFT,
            font=("Segoe UI", 12),
        ).pack(pady=10)

        self._back_button(frame)

    # ------------------------------------------------------------------
    # Game play and state
    # ------------------------------------------------------------------
    def start_play_game(self) -> None:
        """Navigate to the play screen and initialize game state.

        Creates a new :class:`Game` in the ``Playing`` state and resets the
        question index to the beginning of the question list.
        """
        self._current_game = Game(id="game-1", score=0)
        self._current_game.play()
        self._question_index = 0
        self._render_play_screen()

    def _render_play_screen(self) -> None:
        """Render the play screen for the current game state."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Play Game",
            font=("Segoe UI", 22, "bold"),
        ).pack(pady=(10, 10))

        score_label = tk.Label(
            frame,
            text=f"Score: {self._current_game.score}",
            font=("Segoe UI", 14),
        )
        score_label.pack(pady=(0, 10))
        self._score_label = score_label

        state_label = tk.Label(
            frame,
            text=f"State: {self._current_game.state}",
            font=("Segoe UI", 11),
            fg="#555555",
        )
        state_label.pack(pady=(0, 10))

        question_label = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 16),
            wraplength=600,
            justify=tk.CENTER,
        )
        question_label.pack(pady=(10, 20))
        self._question_label = question_label

        options_frame = tk.Frame(frame)
        options_frame.pack(pady=5)
        self._option_buttons = []

        for index in range(4):
            button = tk.Button(
                options_frame,
                text="",
                width=40,
                command=lambda i=index: self.submit_answer(i),
            )
            button.pack(pady=4)
            self._option_buttons.append(button)

        status = tk.Label(
            frame,
            text="",
            fg="#0066cc",
            font=("Segoe UI", 11),
        )
        status.pack(pady=(15, 5))
        self._status_label = status

        controls = tk.Frame(frame)
        controls.pack(pady=(10, 0))

        pause_text = "Pause" if self._current_game.state == "Playing" else "Resume"
        pause_button = tk.Button(
            controls,
            text=pause_text,
            command=self.toggle_pause,
            width=14,
        )
        pause_button.pack(side=tk.LEFT, padx=6)
        self._pause_button = pause_button

        tk.Button(
            controls,
            text="End Game",
            command=self.end_game,
            width=14,
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            controls,
            text="Menu",
            command=self.show_menu,
            width=14,
        ).pack(side=tk.LEFT, padx=6)

        self._refresh_question_display()

    def _refresh_question_display(self) -> None:
        """Update the question prompt and option buttons for the current index."""
        if self._question_label is None:
            return

        if not self._questions:
            self._question_label.config(text="No questions available.")
            for button in self._option_buttons:
                button.config(text="", state=tk.DISABLED)
            return

        if self._question_index >= len(self._questions):
            self._question_label.config(text="You have completed all questions!")
            for button in self._option_buttons:
                button.config(text="", state=tk.DISABLED)
            return

        question = self._questions[self._question_index]
        self._question_label.config(text=question.prompt)

        for index, button in enumerate(self._option_buttons):
            if index < len(question.options):
                button.config(text=question.options[index], state=tk.NORMAL)
            else:
                button.config(text="", state=tk.DISABLED)

    def submit_answer(self, answer_index: int) -> None:
        """Submit an answer for the current question.

        Parameters
        ----------
        answer_index : int
            The index of the selected option.
        """
        if self._current_game is None:
            return

        if self._current_game.state != "Playing":
            self._set_status("Game is not currently playing.")
            return

        if not self._questions:
            self._set_status("No questions available.")
            return

        if self._question_index >= len(self._questions):
            self._set_status("All questions have been answered.")
            return

        question = self._questions[self._question_index]
        if answer_index < 0 or answer_index >= len(question.options):
            self._set_status("Invalid answer selection.")
            return

        if answer_index == question.answer_index:
            self._current_game.score += 1
            self._set_status("Correct!")
        else:
            self._set_status("Incorrect.")

        self._question_index += 1

        if self._score_label is not None:
            self._score_label.config(text=f"Score: {self._current_game.score}")

        self._refresh_question_display()

    def toggle_pause(self) -> None:
        """Toggle pause/resume state of the current game."""
        if self._current_game is None:
            return

        if self._current_game.state == "Playing":
            self._current_game.pause()
            self._set_status("Game paused.")
        elif self._current_game.state == "Paused":
            self._current_game.resume()
            self._set_status("Game resumed.")
        else:
            self._set_status("Game is over and cannot be paused or resumed.")
            return

        if self._pause_button is not None:
            self._pause_button.config(
                text="Pause" if self._current_game.state == "Playing" else "Resume"
            )

    def end_game(self) -> None:
        """Transition the current game's state to ``GameOver``."""
        if self._current_game is None:
            return

        if self._current_game.state == "GameOver":
            self._set_status("Game is already over.")
            return

        self._current_game.game_over()
        self._set_status("Game over.")

        if self._pause_button is not None:
            self._pause_button.config(state=tk.DISABLED)

        for button in self._option_buttons:
            button.config(state=tk.DISABLED)

    def update_questions(self, questions: List[Question]) -> None:
        """Update the questions list (Admin flow).

        Parameters
        ----------
        questions : list
            The new list of :class:`Question` instances.
        """
        self._questions = list(questions)
        self._set_status(f"Questions updated. Total: {len(self._questions)}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _set_status(self, message: str) -> None:
        """Update the status label if one is currently displayed."""
        if self._status_label is not None:
            self._status_label.config(text=message)

    def _reset_default_questions(self) -> None:
        """Reset the question bank to the default seed content."""
        self.update_questions(self._seed_questions())
