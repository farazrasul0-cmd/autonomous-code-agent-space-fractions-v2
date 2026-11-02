"""Space Fractions - standalone Windows desktop application.

This module implements the Tkinter application class that ties together the
domain models (Game, Question, User, Admin) with a multi-screen GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List, Optional

from models import Admin, Game, Question, User


class App:
    """Main application window and controller for Space Fractions."""

    SYSTEM_NAME = "Space Fractions"

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application with a Tk root window.

        Args:
            root: The Tk root window instance.
        """
        self._root = root
        self._current_user: Optional[User] = None
        self._current_game: Optional[Game] = None
        self._questions: List[Question] = self._seed_questions()

        self._screen_frame: Optional[tk.Frame] = None
        self._status_var: tk.StringVar = tk.StringVar(value="Ready")
        self._question_index: int = 0

        self._configure_root()
        self.show_menu()

    # ------------------------------------------------------------------
    # Attribute storage / accessors
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
        """Return the currently active user."""
        return self._current_user

    @current_user.setter
    def current_user(self, value: Optional[User]) -> None:
        self._current_user = value

    @property
    def current_game(self) -> Optional[Game]:
        """Return the currently active game."""
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
    # Internal helpers
    # ------------------------------------------------------------------
    def _configure_root(self) -> None:
        """Configure the root window title and geometry."""
        self._root.title(self.SYSTEM_NAME)
        self._root.geometry("720x520")
        self._root.minsize(560, 420)

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
        """Update the non-blocking status label text."""
        self._status_var.set(message)

    def _seed_questions(self) -> List[Question]:
        """Return a default set of questions so the game is playable on launch."""
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
                prompt="Which fraction is equivalent to 0.75?",
                options=["2/3", "3/4", "4/5", "5/6"],
                answer_index=1,
            ),
        ]

    def _render_header(self, frame: tk.Frame, title: str) -> None:
        """Render a standard screen header."""
        tk.Label(frame, text=title, font=("Segoe UI", 20, "bold")).pack(
            pady=(0, 10)
        )

    def _render_status(self, frame: tk.Frame) -> None:
        """Render the shared status label at the bottom of a screen."""
        tk.Label(
            frame,
            textvariable=self._status_var,
            anchor="w",
            relief="sunken",
            padx=8,
            pady=4,
        ).pack(side="bottom", fill="x", pady=(10, 0))

    def _render_back_button(self, frame: tk.Frame) -> None:
        """Render a back-to-menu button."""
        tk.Button(
            frame,
            text="Back to Main Menu",
            command=self.show_menu,
            width=20,
        ).pack(pady=10)

    # ------------------------------------------------------------------
    # Screen navigation
    # ------------------------------------------------------------------
    def show_menu(self) -> None:
        """Navigate to the main menu screen."""
        frame = self._new_screen()
        self._render_header(frame, self.SYSTEM_NAME)
        self._set_status("Main Menu")

        tk.Label(
            frame,
            text="Welcome to Space Fractions!",
            font=("Segoe UI", 14),
        ).pack(pady=(0, 20))

        buttons = [
            ("Play Game", self.show_play_game),
            ("View Score", self.show_view_score),
            ("Update Questions", self.show_update_questions),
            ("Help", self.show_help),
        ]
        for text, command in buttons:
            tk.Button(
                frame,
                text=text,
                command=command,
                width=24,
                height=2,
            ).pack(pady=6)

        self._render_status(frame)

    def show_play_game(self) -> None:
        """Navigate to the game screen."""
        frame = self._new_screen()
        self._render_header(frame, "Play Game")
        self._set_status("Game screen ready. Press Start to begin.")

        tk.Label(
            frame,
            text="Answer the fraction questions to earn points.",
            font=("Segoe UI", 12),
        ).pack(pady=(0, 20))

        tk.Button(
            frame,
            text="Start Game",
            command=self.start_play_game,
            width=20,
            height=2,
        ).pack(pady=10)

        self._render_back_button(frame)
        self._render_status(frame)

    def show_view_score(self) -> None:
        """Navigate to the score screen."""
        frame = self._new_screen()
        self._render_header(frame, "View Score")
        self._set_status("View Score")

        if self._current_game is not None:
            score_text = f"Current score: {self._current_game.score}"
            state_text = f"Game state: {self._current_game.state}"
        else:
            score_text = "No game has been played yet."
            state_text = ""

        tk.Label(frame, text=score_text, font=("Segoe UI", 14)).pack(pady=10)
        if state_text:
            tk.Label(frame, text=state_text, font=("Segoe UI", 12)).pack(pady=5)

        self._render_back_button(frame)
        self._render_status(frame)

    def show_update_questions(self) -> None:
        """Navigate to the admin questions screen."""
        frame = self._new_screen()
        self._render_header(frame, "Update Questions")
        self._set_status("Update Questions")

        tk.Label(
            frame,
            text="Admin: manage the question bank.",
            font=("Segoe UI", 12),
        ).pack(pady=(0, 10))

        tk.Label(
            frame,
            text=f"Current question count: {len(self._questions)}",
        ).pack(pady=5)

        # Non-blocking admin action: clear the question list.
        tk.Button(
            frame,
            text="Clear All Questions",
            command=lambda: self.update_questions([]),
            width=20,
        ).pack(pady=10)

        self._render_back_button(frame)
        self._render_status(frame)

    def show_help(self) -> None:
        """Navigate to the help screen."""
        frame = self._new_screen()
        self._render_header(frame, f"{self.SYSTEM_NAME} - Help")
        self._set_status("Help")

        help_lines = [
            "How to play:",
            "1. From the main menu, choose Play Game.",
            "2. Press Start Game to begin a session.",
            "3. Select an answer for each fraction question.",
            "4. Use Pause/Resume to control the session.",
            "5. End the game to see your final score.",
        ]
        for line in help_lines:
            tk.Label(frame, text=line, anchor="w", justify="left").pack(
                fill="x", pady=2
            )

        self._render_back_button(frame)
        self._render_status(frame)

    # ------------------------------------------------------------------
    # Game play and state management
    # ------------------------------------------------------------------
    def start_play_game(self) -> None:
        """Navigate to the play screen and initialize game state."""
        if not self._questions:
            self._set_status("No questions available. Add questions first.")
            self.show_update_questions()
            return

        self._current_game = Game(id="game-1", score=0)
        self._current_game.play()
        self._question_index = 0

        frame = self._new_screen()
        self._render_header(frame, "Playing Game")
        self._set_status("Playing")

        self._render_question(frame)

        controls = tk.Frame(frame)
        controls.pack(pady=10)

        tk.Button(
            controls,
            text="Pause",
            command=self.toggle_pause,
            width=12,
        ).pack(side="left", padx=5)

        tk.Button(
            controls,
            text="End Game",
            command=self.end_game,
            width=12,
        ).pack(side="left", padx=5)

        self._render_back_button(frame)
        self._render_status(frame)

    def _render_question(self, frame: tk.Frame) -> None:
        """Render the current question and its answer options."""
        if self._question_index >= len(self._questions):
            self.end_game()
            return

        question = self._questions[self._question_index]

        tk.Label(
            frame,
            text=f"Question {self._question_index + 1} of {len(self._questions)}",
            font=("Segoe UI", 11),
        ).pack(pady=(0, 5))

        tk.Label(
            frame,
            text=question.prompt,
            font=("Segoe UI", 14, "bold"),
            wraplength=600,
        ).pack(pady=(0, 15))

        for index, option in enumerate(question.options):
            tk.Button(
                frame,
                text=option,
                command=lambda idx=index: self.submit_answer(idx),
                width=30,
            ).pack(pady=3)

    def submit_answer(self, answer_index: int) -> None:
        """Submit an answer for the current question.

        Args:
            answer_index: The index of the selected answer option.
        """
        if self._current_game is None:
            self._set_status("No active game. Start a game first.")
            return

        if self._current_game.state != "Playing":
            self._set_status("Game is not currently playing.")
            return

        if self._question_index >= len(self._questions):
            self.end_game()
            return

        question = self._questions[self._question_index]
        if answer_index == question.answer_index:
            self._current_game.score += 1
            self._set_status("Correct!")
        else:
            self._set_status("Incorrect.")

        self._question_index += 1

        if self._question_index >= len(self._questions):
            self.end_game()
        else:
            self._render_question(self._screen_frame)

    def toggle_pause(self) -> None:
        """Toggle pause/resume state of the current game."""
        if self._current_game is None:
            self._set_status("No active game to pause.")
            return

        if self._current_game.state == "Playing":
            self._current_game.pause()
            self._set_status("Paused")
        elif self._current_game.state == "Paused":
            self._current_game.resume()
            self._set_status("Playing")
        else:
            self._set_status(f"Cannot pause from state: {self._current_game.state}")

    def end_game(self) -> None:
        """Transition the current game state to GameOver."""
        if self._current_game is None:
            self._set_status("No active game to end.")
            return

        if self._current_game.state == "GameOver":
            self._set_status("Game is already over.")
            return

        self._current_game.game_over()
        self._set_status(
            f"Game Over! Final score: {self._current_game.score}"
        )

        # Re-render the current screen with a game-over summary.
        frame = self._new_screen()
        self._render_header(frame, "Game Over")
        tk.Label(
            frame,
            text=f"Final score: {self._current_game.score}",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=20)

        tk.Button(
            frame,
            text="Play Again",
            command=self.start_play_game,
            width=20,
        ).pack(pady=10)

        self._render_back_button(frame)
        self._render_status(frame)

    def update_questions(self, questions: List[Question]) -> None:
        """Update the questions list (Admin flow).

        Args:
            questions: The new list of Question instances.
        """
        self._questions = list(questions)
        self._set_status(f"Questions updated. Count: {len(self._questions)}")

        # Refresh the admin screen if it is currently displayed.
        if self._screen_frame is not None:
            self.show_update_questions()
