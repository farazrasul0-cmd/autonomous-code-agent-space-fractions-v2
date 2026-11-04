"""Space Fractions - Standalone Windows desktop application.

Implements the Application class with UI and game logic using only the
Python 3.12 standard library (tkinter, json, math, random, datetime, sys,
os, pathlib).
"""

import json
import math
import random
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models import Admin, Game, Question, User


class Application:
    """Main application window and controller for Space Fractions."""

    SYSTEM_NAME = "Space Fractions"

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        """Initialize the application window, state, and seed content."""
        self._root = root if root is not None else tk.Tk()
        self._root.title(self.SYSTEM_NAME)
        self._root.geometry("720x560")
        self._root.minsize(560, 420)

        # Application state
        self._current_user: Optional[User] = User("u1", "Player One")
        self._current_game: Optional[Game] = None
        self._questions: List[Question] = self._seed_questions()
        self._current_frame: Optional[tk.Frame] = None
        self._current_question_index: int = 0
        self._status_var: tk.StringVar = tk.StringVar(value="Ready")

        # Seed an admin user for the update questions flow.
        self._admin: Admin = Admin("a1", "Admin")

        # Show the main menu on launch.
        self.show_menu()

    # ------------------------------------------------------------------
    # Seed content
    # ------------------------------------------------------------------
    @staticmethod
    def _seed_questions() -> List[Question]:
        """Return a default list of fraction questions."""
        return [
            Question(
                "q1",
                "What is 1/2 + 1/4?",
                ["1/4", "3/4", "2/6", "1/8"],
                1,
            ),
            Question(
                "q2",
                "What is 2/3 - 1/3?",
                ["1/3", "1/2", "2/6", "1"],
                0,
            ),
            Question(
                "q3",
                "What is 1/2 of 1/2?",
                ["1/2", "1/4", "1/8", "1"],
                1,
            ),
            Question(
                "q4",
                "Which fraction is equivalent to 1/2?",
                ["2/3", "3/6", "2/4", "4/6"],
                2,
            ),
            Question(
                "q5",
                "What is 3/4 + 1/4?",
                ["1", "3/8", "4/8", "2/4"],
                0,
            ),
        ]

    # ------------------------------------------------------------------
    # Public properties (Rule 1: getter + setter for every attribute)
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
        self._questions = value

    @property
    def current_frame(self) -> Optional[tk.Frame]:
        return self._current_frame

    @current_frame.setter
    def current_frame(self, value: Optional[tk.Frame]) -> None:
        self._current_frame = value

    @property
    def current_question_index(self) -> int:
        return self._current_question_index

    @current_question_index.setter
    def current_question_index(self, value: int) -> None:
        self._current_question_index = value

    @property
    def status_var(self) -> tk.StringVar:
        return self._status_var

    @status_var.setter
    def status_var(self, value: tk.StringVar) -> None:
        self._status_var = value

    @property
    def admin(self) -> Admin:
        return self._admin

    @admin.setter
    def admin(self, value: Admin) -> None:
        self._admin = value

    # ------------------------------------------------------------------
    # Screen management
    # ------------------------------------------------------------------
    def _clear_screen(self) -> None:
        """Destroy all children of the root window to avoid overlap."""
        for widget in self._root.winfo_children():
            widget.destroy()
        self._current_frame = None

    def _new_frame(self) -> tk.Frame:
        """Create and return a fresh frame packed into the root."""
        frame = tk.Frame(self._root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        self._current_frame = frame
        return frame

    def _status_label(self, parent: tk.Frame) -> tk.Label:
        """Create a shared status label bound to the status variable."""
        label = tk.Label(
            parent,
            textvariable=self._status_var,
            anchor="w",
            fg="#333333",
            font=("Segoe UI", 10),
        )
        label.pack(fill="x", pady=(0, 10))
        return label

    def _back_button(self, parent: tk.Frame) -> tk.Button:
        """Create a standard back-to-menu button."""
        return tk.Button(
            parent,
            text="Back to Main Menu",
            command=self.show_menu,
            width=20,
        )

    # ------------------------------------------------------------------
    # Navigation methods
    # ------------------------------------------------------------------
    def show_menu(self) -> None:
        """Navigate to the main menu screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text=self.SYSTEM_NAME,
            font=("Segoe UI", 28, "bold"),
            fg="#1a3c6e",
        ).pack(pady=(10, 5))

        tk.Label(
            frame,
            text="Learn fractions the fun way!",
            font=("Segoe UI", 12),
            fg="#555555",
        ).pack(pady=(0, 20))

        buttons = [
            ("Play Game", self.start_play_game),
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
                font=("Segoe UI", 11),
            ).pack(pady=6)

        self._status_label(frame)
        self._status_var.set("Welcome to Space Fractions!")

    def show_play_game(self) -> None:
        """Navigate to the game screen (renders current game state)."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Play Game",
            font=("Segoe UI", 20, "bold"),
            fg="#1a3c6e",
        ).pack(pady=(0, 10))

        if self._current_game is None:
            tk.Label(
                frame,
                text="No active game. Start a new game to begin.",
                font=("Segoe UI", 11),
            ).pack(pady=10)
            tk.Button(
                frame,
                text="Start New Game",
                command=self.start_play_game,
                width=20,
            ).pack(pady=6)
        else:
            self._render_game_screen(frame)

        self._back_button(frame).pack(pady=(20, 0))
        self._status_label(frame)

    def show_view_score(self) -> None:
        """Navigate to the score screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="View Score",
            font=("Segoe UI", 20, "bold"),
            fg="#1a3c6e",
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

        self._back_button(frame).pack(pady=(20, 0))
        self._status_label(frame)
        self._status_var.set("Score displayed.")

    def show_update_questions(self) -> None:
        """Navigate to the admin questions screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Update Questions",
            font=("Segoe UI", 20, "bold"),
            fg="#1a3c6e",
        ).pack(pady=(0, 10))

        tk.Label(
            frame,
            text=f"Current question count: {len(self._questions)}",
            font=("Segoe UI", 11),
        ).pack(pady=(0, 10))

        # Listbox showing current questions.
        listbox = tk.Listbox(frame, height=10, width=70)
        listbox.pack(pady=5)
        for question in self._questions:
            listbox.insert("end", f"{question.id}: {question.prompt}")

        # Non-blocking admin actions (no modal dialogs).
        def add_sample_question() -> None:
            new_id = f"q{len(self._questions) + 1}"
            new_question = Question(
                new_id,
                "What is 1/3 + 1/3?",
                ["1/3", "2/3", "2/6", "1/6"],
                1,
            )
            self.update_questions(self._questions + [new_question])
            listbox.insert("end", f"{new_question.id}: {new_question.prompt}")
            self._status_var.set(f"Added question {new_id}.")

        def remove_last_question() -> None:
            if self._questions:
                removed = self._questions[-1]
                self.update_questions(self._questions[:-1])
                listbox.delete("end")
                self._status_var.set(f"Removed question {removed.id}.")
            else:
                self._status_var.set("No questions to remove.")

        tk.Button(
            frame,
            text="Add Sample Question",
            command=add_sample_question,
            width=20,
        ).pack(pady=4)
        tk.Button(
            frame,
            text="Remove Last Question",
            command=remove_last_question,
            width=20,
        ).pack(pady=4)

        self._back_button(frame).pack(pady=(20, 0))
        self._status_label(frame)
        self._status_var.set("Admin question management.")

    def show_help(self) -> None:
        """Navigate to the help screen."""
        self._clear_screen()
        frame = self._new_frame()

        tk.Label(
            frame,
            text=f"{self.SYSTEM_NAME} - Help",
            font=("Segoe UI", 20, "bold"),
            fg="#1a3c6e",
        ).pack(pady=(0, 10))

        help_text = (
            "Welcome to Space Fractions!\n\n"
            "How to play:\n"
            "1. Click 'Play Game' to start a new session.\n"
            "2. Read each fraction question and choose an answer.\n"
            "3. Correct answers earn points.\n"
            "4. Use 'Pause' to pause and 'Resume' to continue.\n"
            "5. Click 'End Game' when you are finished.\n\n"
            "View your score anytime from the main menu."
        )

        tk.Label(
            frame,
            text=help_text,
            justify="left",
            font=("Segoe UI", 11),
        ).pack(pady=10)

        self._back_button(frame).pack(pady=(20, 0))
        self._status_label(frame)
        self._status_var.set("Help displayed.")

    # ------------------------------------------------------------------
    # Game logic
    # ------------------------------------------------------------------
    def start_play_game(self) -> None:
        """Navigate to play screen and initialize game state."""
        self._clear_screen()
        frame = self._new_frame()

        # Create a fresh game and start it.
        game = Game("g1", 0)
        game.play()
        self._current_game = game
        self._current_question_index = 0

        self._render_game_screen(frame)
        self._status_var.set("New game started. Good luck!")

    def _render_game_screen(self, frame: tk.Frame) -> None:
        """Render the current game state into the given frame."""
        game = self._current_game
        if game is None:
            return

        tk.Label(
            frame,
            text="Play Game",
            font=("Segoe UI", 20, "bold"),
            fg="#1a3c6e",
        ).pack(pady=(0, 10))

        # Score and state display.
        info_text = f"Score: {game.view_score()}   |   State: {game.state}"
        tk.Label(
            frame,
            text=info_text,
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(0, 10))

        # Question display.
        if self._questions:
            index = self._current_question_index % len(self._questions)
            question = self._questions[index]
            tk.Label(
                frame,
                text=f"Question {index + 1} of {len(self._questions)}",
                font=("Segoe UI", 10),
                fg="#555555",
            ).pack(pady=(0, 5))
            tk.Label(
                frame,
                text=question.get_prompt(),
                font=("Segoe UI", 14),
                wraplength=600,
            ).pack(pady=(0, 10))

            # Answer buttons.
            for option_index, option in enumerate(question.get_options()):
                tk.Button(
                    frame,
                    text=option,
                    command=lambda idx=option_index: self.submit_answer(idx),
                    width=40,
                ).pack(pady=3)
        else:
            tk.Label(
                frame,
                text="No questions available. Add questions via Update Questions.",
                font=("Segoe UI", 11),
            ).pack(pady=10)

        # Control buttons.
        controls = tk.Frame(frame)
        controls.pack(pady=15)

        if game.state == "Paused":
            pause_text = "Resume"
        else:
            pause_text = "Pause"

        tk.Button(
            controls,
            text=pause_text,
            command=self.toggle_pause,
            width=12,
        ).pack(side="left", padx=5)

        tk.Button(
            controls,
            text="End Game",
            command=self.end_game,
            width=12,
        ).pack(side="left", padx=5)

        self._back_button(frame).pack(pady=(10, 0))
        self._status_label(frame)

    def submit_answer(self, answer_index: int) -> None:
        """Submit an answer for the current question."""
        game = self._current_game
        if game is None:
            self._status_var.set("No active game. Start a new game first.")
            return

        if game.state != "Playing":
            self._status_var.set("Game is not currently playing.")
            return

        if not self._questions:
            self._status_var.set("No questions available.")
            return

        index = self._current_question_index % len(self._questions)
        question = self._questions[index]

        if answer_index == question.get_answer_index():
            game.score += 1
            self._status_var.set("Correct! +1 point.")
        else:
            self._status_var.set(
                f"Incorrect. The answer was: "
                f"{question.get_options()[question.get_answer_index()]}"
            )

        # Advance to the next question.
        self._current_question_index += 1

        # Re-render the game screen to show the next question and score.
        self._clear_screen()
        frame = self._new_frame()
        self._render_game_screen(frame)

    def toggle_pause(self) -> None:
        """Toggle pause/resume state of the current game."""
        game = self._current_game
        if game is None:
            self._status_var.set("No active game to pause.")
            return

        if game.state == "Playing":
            game.pause()
            self._status_var.set("Game paused.")
        elif game.state == "Paused":
            game.resume()
            self._status_var.set("Game resumed.")
        else:
            self._status_var.set("Cannot pause a finished game.")
            return

        # Re-render to update the pause/resume button label.
        self._clear_screen()
        frame = self._new_frame()
        self._render_game_screen(frame)

    def end_game(self) -> None:
        """Transition the current game state to GameOver."""
        game = self._current_game
        if game is None:
            self._status_var.set("No active game to end.")
            return

        if game.state == "GameOver":
            self._status_var.set("Game is already over.")
            return

        game.game_over()
        self._status_var.set(
            f"Game over! Final score: {game.view_score()}"
        )

        # Re-render to reflect the GameOver state.
        self._clear_screen()
        frame = self._new_frame()
        self._render_game_screen(frame)

    def update_questions(self, questions: list) -> None:
        """Update the questions list (Admin flow)."""
        # Accept any iterable of Question instances.
        self._questions = list(questions)
        self._admin.update_questions(self._questions)
        self._status_var.set(f"Questions updated. Total: {len(self._questions)}")


def create_app() -> Application:
    """Create and return an Application instance (smoke-test entry point)."""
    root = tk.Tk()
    app = Application(root)
    return app


if __name__ == "__main__":
    app = create_app()
    app.root.mainloop()
