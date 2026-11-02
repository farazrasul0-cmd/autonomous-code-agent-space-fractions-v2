"""Standalone Windows desktop application for a trivia quiz game.

This module implements the App class, which provides the graphical user
interface and game logic for a quiz application built with Tkinter.
"""

import tkinter as tk
from tkinter import messagebox
from typing import List

from models import Admin, Game, Question, User


class App:
    """Main application class managing UI screens and game state."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application with a Tk root window.

        Args:
            root: The Tkinter root window.
        """
        self.root = root
        self.root.title("Trivia Quiz Game")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)

        # Private state attributes
        self._current_user: User = User(1, "Player")
        self._current_game: Game = Game(1, 0)
        self._questions: List[Question] = self._seed_questions()

        # Internal UI state
        self._current_frame: tk.Frame | None = None
        self._question_index: int = 0
        self._answer_buttons: List[tk.Button] = []
        self._question_label: tk.Label | None = None
        self._status_label: tk.Label | None = None
        self._pause_button: tk.Button | None = None
        self._score_label: tk.Label | None = None

        # Show the main menu on startup
        self.show_menu()

    # ------------------------------------------------------------------
    # Seed content
    # ------------------------------------------------------------------
    @staticmethod
    def _seed_questions() -> List[Question]:
        """Return a default list of Question instances for immediate play."""
        return [
            Question(
                1,
                "What is the capital of France?",
                ["London", "Berlin", "Paris", "Madrid"],
                2,
            ),
            Question(
                2,
                "Which planet is known as the Red Planet?",
                ["Venus", "Mars", "Jupiter", "Saturn"],
                1,
            ),
            Question(
                3,
                "What is 2 + 2?",
                ["3", "4", "5", "22"],
                1,
            ),
            Question(
                4,
                "Who wrote 'Romeo and Juliet'?",
                ["Charles Dickens", "William Shakespeare", "Mark Twain", "Jane Austen"],
                1,
            ),
            Question(
                5,
                "What is the largest ocean on Earth?",
                ["Atlantic", "Indian", "Arctic", "Pacific"],
                3,
            ),
        ]

    # ------------------------------------------------------------------
    # Screen management helpers
    # ------------------------------------------------------------------
    def _clear_screen(self) -> None:
        """Destroy the current screen frame, if any."""
        if self._current_frame is not None:
            self._current_frame.destroy()
            self._current_frame = None

    def _new_frame(self) -> tk.Frame:
        """Create and return a fresh frame, clearing any existing screen."""
        self._clear_screen()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        self._current_frame = frame
        return frame

    def _back_button(self, frame: tk.Frame) -> None:
        """Add a standard 'Back to Menu' button to a screen."""
        tk.Button(
            frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
        ).pack(pady=10)

    # ------------------------------------------------------------------
    # Navigation methods
    # ------------------------------------------------------------------
    def show_menu(self) -> None:
        """Navigate to main menu screen."""
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Trivia Quiz Game",
            font=("Arial", 24, "bold"),
        ).pack(pady=20)

        tk.Label(
            frame,
            text=f"Welcome, {self._current_user.username}!",
            font=("Arial", 12),
        ).pack(pady=5)

        tk.Button(
            frame,
            text="Play Game",
            command=self.show_play_game,
            width=25,
            height=2,
        ).pack(pady=8)

        tk.Button(
            frame,
            text="View Score",
            command=self.show_view_score,
            width=25,
            height=2,
        ).pack(pady=8)

        tk.Button(
            frame,
            text="Update Questions (Admin)",
            command=self.show_update_questions,
            width=25,
            height=2,
        ).pack(pady=8)

        tk.Button(
            frame,
            text="Help",
            command=self.show_help,
            width=25,
            height=2,
        ).pack(pady=8)

        tk.Button(
            frame,
            text="Exit",
            command=self.root.destroy,
            width=25,
            height=2,
        ).pack(pady=8)

    def show_play_game(self) -> None:
        """Navigate to game screen."""
        self.start_play_game()

    def show_view_score(self) -> None:
        """Navigate to score screen."""
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Score",
            font=("Arial", 20, "bold"),
        ).pack(pady=20)

        score = self._current_game.view_score()
        tk.Label(
            frame,
            text=f"Current Score: {score}",
            font=("Arial", 16),
        ).pack(pady=20)

        self._back_button(frame)

    def show_update_questions(self) -> None:
        """Navigate to admin questions screen."""
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Update Questions (Admin)",
            font=("Arial", 20, "bold"),
        ).pack(pady=20)

        tk.Label(
            frame,
            text="Enter questions in the format below, one per line:\n"
                 "prompt | option1 | option2 | option3 | option4 | answer_index",
            justify=tk.LEFT,
        ).pack(pady=10)

        text_area = tk.Text(frame, height=12, width=70)
        text_area.pack(pady=10)

        # Pre-populate with current questions for convenience
        for question in self._questions:
            line = " | ".join(
                [question.get_prompt()]
                + question.get_options()
                + [str(question.get_answer_index())]
            )
            text_area.insert(tk.END, line + "\n")

        def _save_questions() -> None:
            """Parse the text area and update the question list."""
            raw = text_area.get("1.0", tk.END).strip()
            if not raw:
                messagebox.showwarning(
                    "No Questions", "Please enter at least one question."
                )
                return

            parsed: List[Question] = []
            for idx, line in enumerate(raw.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                parts = [part.strip() for part in line.split("|")]
                if len(parts) != 6:
                    messagebox.showerror(
                        "Invalid Format",
                        f"Line {idx} must have 6 parts separated by '|'.",
                    )
                    return
                prompt, opt1, opt2, opt3, opt4, answer_str = parts
                try:
                    answer_index = int(answer_str)
                except ValueError:
                    messagebox.showerror(
                        "Invalid Answer Index",
                        f"Line {idx} answer index must be an integer.",
                    )
                    return
                if not (0 <= answer_index <= 3):
                    messagebox.showerror(
                        "Invalid Answer Index",
                        f"Line {idx} answer index must be between 0 and 3.",
                    )
                    return
                parsed.append(
                    Question(idx, prompt, [opt1, opt2, opt3, opt4], answer_index)
                )

            self.update_questions(parsed)
            messagebox.showinfo(
                "Success", f"Updated {len(parsed)} question(s)."
            )
            self.show_menu()

        tk.Button(
            frame,
            text="Save Questions",
            command=_save_questions,
            width=20,
        ).pack(pady=5)

        self._back_button(frame)

    def show_help(self) -> None:
        """Navigate to help screen."""
        frame = self._new_frame()

        tk.Label(
            frame,
            text="Help",
            font=("Arial", 20, "bold"),
        ).pack(pady=20)

        help_text = (
            "How to Play:\n\n"
            "1. Click 'Play Game' from the main menu.\n"
            "2. Read each question and select an answer.\n"
            "3. Correct answers increase your score.\n"
            "4. Use 'Pause' to pause the game and 'Resume' to continue.\n"
            "5. Click 'End Game' to finish and view your score.\n\n"
            "Admin:\n"
            "Use 'Update Questions' to modify the question list.\n"
            "Each line must follow the format:\n"
            "prompt | option1 | option2 | option3 | option4 | answer_index"
        )
        tk.Label(
            frame,
            text=help_text,
            justify=tk.LEFT,
            font=("Arial", 11),
        ).pack(pady=10)

        self._back_button(frame)

    # ------------------------------------------------------------------
    # Game logic methods
    # ------------------------------------------------------------------
    def start_play_game(self) -> None:
        """Navigate to play screen and initialize game state."""
        if not self._questions:
            messagebox.showwarning(
                "No Questions",
                "There are no questions available. Please add questions first.",
            )
            self.show_menu()
            return

        # Reset game state
        self._current_game = Game(1, 0)
        self._current_game.play()
        self._question_index = 0

        frame = self._new_frame()

        tk.Label(
            frame,
            text="Play Game",
            font=("Arial", 20, "bold"),
        ).pack(pady=10)

        self._score_label = tk.Label(
            frame,
            text=f"Score: {self._current_game.view_score()}",
            font=("Arial", 12),
        )
        self._score_label.pack(pady=5)

        self._status_label = tk.Label(
            frame,
            text=f"State: {self._current_game.state}",
            font=("Arial", 10),
        )
        self._status_label.pack(pady=5)

        self._question_label = tk.Label(
            frame,
            text="",
            font=("Arial", 14),
            wraplength=600,
            justify=tk.CENTER,
        )
        self._question_label.pack(pady=20)

        answers_frame = tk.Frame(frame)
        answers_frame.pack(pady=10)

        self._answer_buttons = []
        for i in range(4):
            button = tk.Button(
                answers_frame,
                text="",
                width=40,
                command=lambda idx=i: self.submit_answer(idx),
            )
            button.pack(pady=4)
            self._answer_buttons.append(button)

        controls_frame = tk.Frame(frame)
        controls_frame.pack(pady=15)

        self._pause_button = tk.Button(
            controls_frame,
            text="Pause",
            command=self.toggle_pause,
            width=15,
        )
        self._pause_button.pack(side=tk.LEFT, padx=5)

        tk.Button(
            controls_frame,
            text="End Game",
            command=self.end_game,
            width=15,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            controls_frame,
            text="Back to Menu",
            command=self.show_menu,
            width=15,
        ).pack(side=tk.LEFT, padx=5)

        self._render_question()

    def _render_question(self) -> None:
        """Render the current question and its options on the play screen."""
        if self._question_index >= len(self._questions):
            self.end_game()
            return

        question = self._questions[self._question_index]
        if self._question_label is not None:
            self._question_label.config(
                text=f"Question {self._question_index + 1} of {len(self._questions)}:\n"
                     f"{question.get_prompt()}"
            )

        options = question.get_options()
        for i, button in enumerate(self._answer_buttons):
            if i < len(options):
                button.config(text=options[i], state=tk.NORMAL)
            else:
                button.config(text="", state=tk.DISABLED)

    def submit_answer(self, answer_index: int) -> None:
        """Submit answer for current question.

        Args:
            answer_index: The index of the selected answer option.
        """
        if self._current_game.state != "Playing":
            return

        if self._question_index >= len(self._questions):
            return

        question = self._questions[self._question_index]
        if answer_index == question.get_answer_index():
            self._current_game.score += 1
            if self._score_label is not None:
                self._score_label.config(
                    text=f"Score: {self._current_game.view_score()}"
                )

        self._question_index += 1
        self._render_question()

    def toggle_pause(self) -> None:
        """Toggle pause/resume state of current game."""
        if self._current_game.state == "Playing":
            self._current_game.pause()
            if self._pause_button is not None:
                self._pause_button.config(text="Resume")
            self._set_answers_enabled(False)
        elif self._current_game.state == "Paused":
            self._current_game.resume()
            if self._pause_button is not None:
                self._pause_button.config(text="Pause")
            self._set_answers_enabled(True)

        if self._status_label is not None:
            self._status_label.config(text=f"State: {self._current_game.state}")

    def _set_answers_enabled(self, enabled: bool) -> None:
        """Enable or disable all answer buttons."""
        state = tk.NORMAL if enabled else tk.DISABLED
        for button in self._answer_buttons:
            if button.cget("text"):
                button.config(state=state)

    def end_game(self) -> None:
        """Transition Game.state to GameOver."""
        if self._current_game.state == "GameOver":
            return

        self._current_game.game_over()
        if self._status_label is not None:
            self._status_label.config(text=f"State: {self._current_game.state}")

        self._set_answers_enabled(False)
        if self._pause_button is not None:
            self._pause_button.config(state=tk.DISABLED)

        messagebox.showinfo(
            "Game Over",
            f"Game over! Your final score is {self._current_game.view_score()}.",
        )
        self.show_view_score()

    def update_questions(self, questions: List[Question]) -> None:
        """Update questions list (Admin flow).

        Args:
            questions: The new list of Question instances.
        """
        self._questions = list(questions)
        admin = Admin(1, "Admin")
        admin.update_questions(self._questions)
