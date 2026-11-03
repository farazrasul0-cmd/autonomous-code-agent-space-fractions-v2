"""Space Fractions - Standalone Windows desktop application.

Implements the Application class with UI and game logic using only the
Python 3.12 standard library (tkinter, json, math, random, datetime, sys,
os, pathlib).
"""

import json
import math
import random
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import tkinter as tk
from tkinter import ttk

from models import Game, Question, User, Admin


class Application:
    """Main application window and controller for Space Fractions."""

    SYSTEM_NAME = "Space Fractions"

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        """Initialize the application window, state, and seed content."""
        self._root = root if root is not None else tk.Tk()
        self._root.title(self.SYSTEM_NAME)
        self._root.geometry("720x560")
        self._root.minsize(560, 420)

        # Contract-declared attributes (Rule 1: private storage + accessors).
        self._current_user: Optional[User] = None
        self._current_game: Optional[Game] = None
        self._questions: List[Question] = self._seed_questions()

        # Internal UI state (not part of the public contract surface).
        self._current_frame: Optional[tk.Frame] = None
        self._question_index: int = 0
        self._status_var: Optional[tk.StringVar] = None
        self._question_label: Optional[tk.Label] = None
        self._option_buttons: List[tk.Button] = []
        self._score_label: Optional[tk.Label] = None
        self._pause_button: Optional[tk.Button] = None
        self._questions_text: Optional[tk.Text] = None

        # Seed a default user so the app is immediately usable.
        self._current_user = User("u1", "Player")

        self.show_menu()

    # ------------------------------------------------------------------
    # Contract attribute accessors (Rule 1)
    # ------------------------------------------------------------------
    @property
    def root(self) -> tk.Tk:
        return self._root

    @root.setter
    def root(self, value: tk.Tk) -> None:
        self._root = value

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    @current_user.setter
    def current_user(self, value: Optional[User]) -> None:
        self._current_user = value

    @property
    def current_game(self) -> Optional[Game]:
        return self._current_game

    @current_game.setter
    def current_game(self, value: Optional[Game]) -> None:
        self._current_game = value

    @property
    def questions(self) -> List[Question]:
        return self._questions

    @questions.setter
    def questions(self, value: List[Question]) -> None:
        self._questions = list(value)

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
                ["1/4", "3/4", "2/6", "1/8"],
                1,
            ),
            Question(
                "q2",
                "What is 2/3 - 1/6?",
                ["1/2", "1/3", "1/6", "2/6"],
                0,
            ),
            Question(
                "q3",
                "What is 3/4 * 2/3?",
                ["5/7", "6/12", "1/2", "2/4"],
                2,
            ),
            Question(
                "q4",
                "What is 5/8 divided by 1/4?",
                ["5/2", "5/32", "4/5", "2/5"],
                0,
            ),
            Question(
                "q5",
                "Which fraction is equivalent to 0.75?",
                ["2/3", "3/4", "4/5", "5/6"],
                1,
            ),
        ]

    # ------------------------------------------------------------------
    # Screen management
    # ------------------------------------------------------------------
    def _clear_screen(self) -> None:
        """Destroy all root children and reset the current frame."""
        for widget in self._root.winfo_children():
            widget.destroy()
        self._current_frame = None
        self._status_var = None
        self._question_label = None
        self._option_buttons = []
        self._score_label = None
        self._pause_button = None
        self._questions_text = None

    def _new_frame(self) -> tk.Frame:
        """Create and return a fresh frame attached to the root."""
        frame = tk.Frame(self._root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        self._current_frame = frame
        return frame

    def _set_status(self, message: str) -> None:
        """Update the status label if one exists on the current screen."""
        if self._status_var is not None:
            self._status_var.set(message)

    # ------------------------------------------------------------------
    # Navigation methods (contract)
    # ------------------------------------------------------------------
    def show_menu(self) -> None:
        """Navigate to the main menu screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text=self.SYSTEM_NAME,
            font=("Segoe UI", 28, "bold"),
        ).pack(pady=(10, 5))

        tk.Label(
            frame,
            text="Learn fractions among the stars!",
            font=("Segoe UI", 12),
        ).pack(pady=(0, 20))

        buttons = [
            ("Play Game", self.start_play_game),
            ("View Score", self.show_view_score),
            ("Update Questions", self.show_update_questions),
            ("Help", self.show_help),
            ("Exit", self._root.destroy),
        ]

        for text, command in buttons:
            tk.Button(
                frame,
                text=text,
                command=command,
                width=24,
                font=("Segoe UI", 12),
            ).pack(pady=6)

    def show_play_game(self) -> None:
        """Navigate to the game screen (renders current game state)."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Play Game",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(0, 10))

        if self._current_game is None:
            tk.Label(
                frame,
                text="No active game. Start a new game to begin.",
                font=("Segoe UI", 12),
            ).pack(pady=20)
            tk.Button(
                frame,
                text="Start Game",
                command=self.start_play_game,
                width=20,
            ).pack(pady=10)
            tk.Button(
                frame,
                text="Back to Menu",
                command=self.show_menu,
                width=20,
            ).pack(pady=10)
            return

        self._render_game_screen(frame)

    def show_view_score(self) -> None:
        """Navigate to the score screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="View Score",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(0, 10))

        if self._current_game is None:
            score_text = "No game has been played yet."
        else:
            score = self._current_game.view_score()
            state = self._current_game.state
            score_text = f"Current score: {score}  (State: {state})"

        tk.Label(
            frame,
            text=score_text,
            font=("Segoe UI", 14),
        ).pack(pady=20)

        tk.Button(
            frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
        ).pack(pady=10)

    def show_update_questions(self) -> None:
        """Navigate to the admin questions screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Update Questions",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(0, 10))

        tk.Label(
            frame,
            text=(
                "Enter one question per line in the format:\n"
                "prompt | option1 | option2 | option3 | option4 | answer_index"
            ),
            font=("Segoe UI", 10),
            justify="left",
        ).pack(pady=(0, 10))

        self._questions_text = tk.Text(frame, height=12, width=70)
        self._questions_text.pack(pady=5)

        # Pre-populate with current questions.
        for question in self._questions:
            line = " | ".join(
                [question.prompt]
                + list(question.options)
                + [str(question.answer_index)]
            )
            self._questions_text.insert("end", line + "\n")

        button_row = tk.Frame(frame)
        button_row.pack(pady=10)

        tk.Button(
            button_row,
            text="Save Questions",
            command=self._save_questions_from_text,
            width=18,
        ).pack(side="left", padx=5)

        tk.Button(
            button_row,
            text="Back to Menu",
            command=self.show_menu,
            width=18,
        ).pack(side="left", padx=5)

        self._status_var = tk.StringVar(value="")
        tk.Label(
            frame,
            textvariable=self._status_var,
            font=("Segoe UI", 10),
            fg="green",
        ).pack(pady=5)

    def show_help(self) -> None:
        """Navigate to the help screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text=self.SYSTEM_NAME + " - Help",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(0, 10))

        help_text = (
            "Welcome to Space Fractions!\n\n"
            "How to play:\n"
            "1. Choose 'Play Game' from the main menu.\n"
            "2. Read each fraction question and select an answer.\n"
            "3. Correct answers increase your score.\n"
            "4. Use Pause/Resume to take a break.\n"
            "5. End the game to view your final score.\n\n"
            "Admins can update the question bank from the\n"
            "'Update Questions' screen."
        )

        tk.Label(
            frame,
            text=help_text,
            font=("Segoe UI", 12),
            justify="left",
        ).pack(pady=10)

        tk.Button(
            frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
        ).pack(pady=10)

    # ------------------------------------------------------------------
    # Game flow methods (contract)
    # ------------------------------------------------------------------
    def start_play_game(self) -> None:
        """Navigate to play screen and initialize game state."""
        if not self._questions:
            self._clear_screen()
            frame = self._new_frame()
            tk.Label(
                frame,
                text="No questions available. Please add questions first.",
                font=("Segoe UI", 12),
            ).pack(pady=20)
            tk.Button(
                frame,
                text="Back to Menu",
                command=self.show_menu,
                width=20,
            ).pack(pady=10)
            return

        game_id = "g" + datetime.now().strftime("%Y%m%d%H%M%S%f")
        self._current_game = Game(game_id, 0)
        self._current_game.play()
        self._question_index = 0

        self._clear_screen()
        frame = self._new_frame()
        self._render_game_screen(frame)

    def submit_answer(self, answer_index: int) -> None:
        """Submit an answer for the current question."""
        if self._current_game is None:
            self._set_status("No active game.")
            return

        if self._current_game.state != "Playing":
            self._set_status("Game is not currently playing.")
            return

        if self._question_index >= len(self._questions):
            self._set_status("No more questions.")
            return

        question = self._questions[self._question_index]
        if answer_index == question.answer_index:
            self._current_game.score += 1
            feedback = "Correct!"
        else:
            feedback = (
                f"Incorrect. The answer was: "
                f"{question.options[question.answer_index]}"
            )

        self._question_index += 1

        if self._question_index >= len(self._questions):
            self._current_game.game_over()
            self._set_status(feedback + " Game over!")
            self._refresh_game_screen()
            return

        self._set_status(feedback)
        self._refresh_game_screen()

    def toggle_pause(self) -> None:
        """Toggle pause/resume state of the current game."""
        if self._current_game is None:
            self._set_status("No active game.")
            return

        if self._current_game.state == "Playing":
            self._current_game.pause()
            self._set_status("Game paused.")
        elif self._current_game.state == "Paused":
            self._current_game.resume()
            self._set_status("Game resumed.")
        else:
            self._set_status("Cannot pause a finished game.")

        self._refresh_game_screen()

    def end_game(self) -> None:
        """Transition the current game state to GameOver."""
        if self._current_game is None:
            self._set_status("No active game.")
            return

        if self._current_game.state == "GameOver":
            self._set_status("Game is already over.")
            return

        self._current_game.game_over()
        self._set_status("Game over!")
        self._refresh_game_screen()

    def update_questions(self, questions: list) -> None:
        """Update the questions list (Admin flow)."""
        self._questions = list(questions)
        self._set_status(f"Questions updated ({len(self._questions)} total).")

    # ------------------------------------------------------------------
    # Game screen rendering helpers
    # ------------------------------------------------------------------
    def _render_game_screen(self, frame: tk.Frame) -> None:
        """Render the full game screen into the given frame."""
        game = self._current_game
        if game is None:
            return

        tk.Label(
            frame,
            text="Play Game",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(0, 10))

        self._score_label = tk.Label(
            frame,
            text=f"Score: {game.score}",
            font=("Segoe UI", 14),
        )
        self._score_label.pack(pady=(0, 5))

        state_label = tk.Label(
            frame,
            text=f"State: {game.state}",
            font=("Segoe UI", 11),
        )
        state_label.pack(pady=(0, 10))

        self._question_label = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 14),
            wraplength=600,
            justify="center",
        )
        self._question_label.pack(pady=10)

        options_frame = tk.Frame(frame)
        options_frame.pack(pady=10)
        self._option_buttons = []

        self._status_var = tk.StringVar(value="")
        tk.Label(
            frame,
            textvariable=self._status_var,
            font=("Segoe UI", 10),
            fg="blue",
        ).pack(pady=5)

        controls = tk.Frame(frame)
        controls.pack(pady=10)

        self._pause_button = tk.Button(
            controls,
            text="Pause",
            command=self.toggle_pause,
            width=14,
        )
        self._pause_button.pack(side="left", padx=5)

        tk.Button(
            controls,
            text="End Game",
            command=self.end_game,
            width=14,
        ).pack(side="left", padx=5)

        tk.Button(
            controls,
            text="Back to Menu",
            command=self.show_menu,
            width=14,
        ).pack(side="left", padx=5)

        self._refresh_game_screen()

    def _refresh_game_screen(self) -> None:
        """Refresh dynamic widgets on the game screen."""
        game = self._current_game
        if game is None:
            return

        if self._score_label is not None:
            self._score_label.config(text=f"Score: {game.score}")

        if self._pause_button is not None:
            if game.state == "Playing":
                self._pause_button.config(text="Pause")
            elif game.state == "Paused":
                self._pause_button.config(text="Resume")
            else:
                self._pause_button.config(text="Pause", state="disabled")

        # Clear existing option buttons.
        for button in self._option_buttons:
            button.destroy()
        self._option_buttons = []

        if self._question_label is None:
            return

        if game.state == "GameOver":
            self._question_label.config(text="Game Over!")
            return

        if self._question_index >= len(self._questions):
            self._question_label.config(text="No more questions.")
            return

        question = self._questions[self._question_index]
        self._question_label.config(text=question.prompt)

        for index, option in enumerate(question.options):
            button = tk.Button(
                self._question_label.master,
                text=option,
                command=lambda idx=index: self.submit_answer(idx),
                width=30,
            )
            button.pack(pady=3)
            self._option_buttons.append(button)

    # ------------------------------------------------------------------
    # Admin screen helper
    # ------------------------------------------------------------------
    def _save_questions_from_text(self) -> None:
        """Parse the questions text widget and update the question bank."""
        if self._questions_text is None:
            return

        raw = self._questions_text.get("1.0", "end")
        parsed: List[Question] = []
        errors: List[str] = []

        for line_number, line in enumerate(raw.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue

            parts = [part.strip() for part in line.split("|")]
            if len(parts) != 6:
                errors.append(f"Line {line_number}: expected 6 fields.")
                continue

            prompt = parts[0]
            options = parts[1:5]
            try:
                answer_index = int(parts[5])
            except ValueError:
                errors.append(f"Line {line_number}: answer index must be an integer.")
                continue

            if not (0 <= answer_index < len(options)):
                errors.append(
                    f"Line {line_number}: answer index out of range."
                )
                continue

            question_id = f"q{line_number}"
            parsed.append(Question(question_id, prompt, options, answer_index))

        if errors:
            self._set_status("Errors:\n" + "\n".join(errors))
            return

        if not parsed:
            self._set_status("No valid questions entered.")
            return

        self.update_questions(parsed)
        self._set_status(f"Saved {len(parsed)} questions.")


def create_app() -> Application:
    """Create and return an Application instance (smoke-test entry point)."""
    root = tk.Tk()
    app = Application(root)
    return app


if __name__ == "__main__":
    app = create_app()
    app.root.mainloop()
