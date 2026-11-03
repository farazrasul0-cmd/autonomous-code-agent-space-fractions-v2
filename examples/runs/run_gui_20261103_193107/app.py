"""Space Fractions - Standalone Windows Desktop Application.

Application class implementing UI and orchestration for the Space Fractions
quiz game. Built exclusively with the Python 3.12 standard library.
"""

import tkinter as tk
from tkinter import ttk

from models import Game, Question, User, Admin


class App:
    """Main application window and orchestration logic."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application with a Tkinter root window."""
        self._root = root
        self._current_user = None
        self._current_game = None
        self._questions = self._seed_questions()

        self._root.title("Space Fractions")
        self._root.geometry("720x520")
        self._root.minsize(560, 420)

        # Container frame that holds the currently displayed screen.
        self._screen_frame = tk.Frame(self._root)
        self._screen_frame.pack(fill=tk.BOTH, expand=True)

        self.show_menu()

    # ------------------------------------------------------------------
    # Seed content
    # ------------------------------------------------------------------
    @staticmethod
    def _seed_questions() -> list:
        """Return a default list of Question instances for immediate play."""
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
                "What is 3/5 * 2/3?",
                ["6/15", "5/8", "2/5", "1/5"],
                2,
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
                ["1/3", "3/4", "2/5", "5/6"],
                1,
            ),
        ]

    # ------------------------------------------------------------------
    # Public attributes (Rule 1: property + setter for each)
    # ------------------------------------------------------------------
    @property
    def root(self) -> tk.Tk:
        """Return the Tkinter root window."""
        return self._root

    @root.setter
    def root(self, value: tk.Tk) -> None:
        self._root = value

    @property
    def current_user(self):
        """Return the current user, if any."""
        return self._current_user

    @current_user.setter
    def current_user(self, value) -> None:
        self._current_user = value

    @property
    def current_game(self):
        """Return the current game, if any."""
        return self._current_game

    @current_game.setter
    def current_game(self, value) -> None:
        self._current_game = value

    @property
    def questions(self) -> list:
        """Return the list of questions."""
        return self._questions

    @questions.setter
    def questions(self, value: list) -> None:
        self._questions = value

    # ------------------------------------------------------------------
    # Screen navigation helpers
    # ------------------------------------------------------------------
    def _clear_screen(self) -> None:
        """Destroy all widgets in the current screen frame."""
        for child in self._screen_frame.winfo_children():
            child.destroy()

    def _set_status(self, text: str) -> None:
        """Update the status label if one exists on the current screen."""
        status = getattr(self, "_status_label", None)
        if status is not None and status.winfo_exists():
            status.config(text=text)

    # ------------------------------------------------------------------
    # Screen navigation
    # ------------------------------------------------------------------
    def show_menu(self) -> None:
        """Navigate to main menu screen."""
        self._clear_screen()
        self._status_label = None

        title = tk.Label(
            self._screen_frame,
            text="Space Fractions",
            font=("Segoe UI", 28, "bold"),
        )
        title.pack(pady=(60, 10))

        subtitle = tk.Label(
            self._screen_frame,
            text="Test your fraction skills across the galaxy!",
            font=("Segoe UI", 12),
        )
        subtitle.pack(pady=(0, 30))

        buttons = [
            ("Play Game", self.start_play_game),
            ("View Score", self.show_view_score),
            ("Update Questions", self.show_update_questions),
            ("Help", self.show_help),
        ]

        for text, command in buttons:
            btn = tk.Button(
                self._screen_frame,
                text=text,
                command=command,
                width=24,
                font=("Segoe UI", 12),
            )
            btn.pack(pady=6)

    def show_play_game(self) -> None:
        """Navigate to game screen."""
        self._clear_screen()
        self._status_label = None

        title = tk.Label(
            self._screen_frame,
            text="Play Game",
            font=("Segoe UI", 22, "bold"),
        )
        title.pack(pady=(30, 10))

        if self._current_game is None:
            info = tk.Label(
                self._screen_frame,
                text="No game in progress. Start a new game to begin.",
                font=("Segoe UI", 12),
            )
            info.pack(pady=20)

            start_btn = tk.Button(
                self._screen_frame,
                text="Start New Game",
                command=self.start_play_game,
                width=20,
                font=("Segoe UI", 12),
            )
            start_btn.pack(pady=10)
        else:
            self._render_game_screen()

        back_btn = tk.Button(
            self._screen_frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
        )
        back_btn.pack(pady=20)

    def show_view_score(self) -> None:
        """Navigate to score screen."""
        self._clear_screen()
        self._status_label = None

        title = tk.Label(
            self._screen_frame,
            text="View Score",
            font=("Segoe UI", 22, "bold"),
        )
        title.pack(pady=(30, 10))

        if self._current_game is None:
            score_text = "No game has been played yet."
        else:
            score_text = f"Current score: {self._current_game.score}"

        score_label = tk.Label(
            self._screen_frame,
            text=score_text,
            font=("Segoe UI", 14),
        )
        score_label.pack(pady=20)

        back_btn = tk.Button(
            self._screen_frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
        )
        back_btn.pack(pady=20)

    def show_update_questions(self) -> None:
        """Navigate to admin questions screen."""
        self._clear_screen()
        self._status_label = None

        title = tk.Label(
            self._screen_frame,
            text="Update Questions",
            font=("Segoe UI", 22, "bold"),
        )
        title.pack(pady=(30, 10))

        info = tk.Label(
            self._screen_frame,
            text=(
                "Admin flow: replace the question list with a new set.\n"
                "Enter questions as JSON in the format:\n"
                '[{"id": "q1", "prompt": "...", "options": ["a", "b"], '
                '"answer_index": 0}]'
            ),
            font=("Segoe UI", 10),
            justify=tk.LEFT,
        )
        info.pack(pady=10)

        text_frame = tk.Frame(self._screen_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self._questions_text = tk.Text(text_frame, height=10, wrap=tk.WORD)
        self._questions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self._questions_text.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._questions_text.config(yscrollcommand=scrollbar.set)

        # Pre-populate with current questions as JSON for convenience.
        import json

        current = [
            {
                "id": q.id,
                "prompt": q.prompt,
                "options": q.options,
                "answer_index": q.answer_index,
            }
            for q in self._questions
        ]
        self._questions_text.insert(tk.END, json.dumps(current, indent=2))

        self._status_label = tk.Label(
            self._screen_frame, text="", font=("Segoe UI", 10), fg="green"
        )
        self._status_label.pack(pady=(0, 5))

        button_frame = tk.Frame(self._screen_frame)
        button_frame.pack(pady=10)

        apply_btn = tk.Button(
            button_frame,
            text="Apply Questions",
            command=self._apply_questions_from_text,
            width=18,
        )
        apply_btn.pack(side=tk.LEFT, padx=5)

        back_btn = tk.Button(
            button_frame,
            text="Back to Menu",
            command=self.show_menu,
            width=18,
        )
        back_btn.pack(side=tk.LEFT, padx=5)

    def show_help(self) -> None:
        """Navigate to help screen."""
        self._clear_screen()
        self._status_label = None

        title = tk.Label(
            self._screen_frame,
            text="Space Fractions - Help",
            font=("Segoe UI", 22, "bold"),
        )
        title.pack(pady=(30, 10))

        help_text = (
            "Welcome to Space Fractions!\n\n"
            "How to play:\n"
            "1. Click 'Play Game' from the main menu.\n"
            "2. Read each fraction question carefully.\n"
            "3. Select an answer and click 'Submit Answer'.\n"
            "4. Earn points for correct answers.\n"
            "5. Use 'Pause' to take a break and 'Resume' to continue.\n"
            "6. Click 'End Game' when you are finished.\n\n"
            "Admins can update the question set via 'Update Questions'."
        )

        help_label = tk.Label(
            self._screen_frame,
            text=help_text,
            font=("Segoe UI", 11),
            justify=tk.LEFT,
        )
        help_label.pack(pady=10, padx=30)

        back_btn = tk.Button(
            self._screen_frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
        )
        back_btn.pack(pady=20)

    # ------------------------------------------------------------------
    # Game play and state management
    # ------------------------------------------------------------------
    def start_play_game(self) -> None:
        """Navigate to play screen and initialize game state."""
        self._current_game = Game(id="game-1", score=0)
        self._current_game.play()  # state -> 'Playing'
        self._current_question_index = 0
        self._selected_answer = None

        self.show_play_game()

    def _render_game_screen(self) -> None:
        """Render the in-progress game widgets on the play screen."""
        game = self._current_game
        if game is None:
            return

        state_label = tk.Label(
            self._screen_frame,
            text=f"State: {game.state}",
            font=("Segoe UI", 12, "italic"),
        )
        state_label.pack(pady=(0, 5))

        score_label = tk.Label(
            self._screen_frame,
            text=f"Score: {game.score}",
            font=("Segoe UI", 14, "bold"),
        )
        score_label.pack(pady=(0, 15))

        if game.state == "GameOver":
            over_label = tk.Label(
                self._screen_frame,
                text="Game Over!",
                font=("Segoe UI", 18, "bold"),
                fg="red",
            )
            over_label.pack(pady=10)
            return

        if game.state == "Paused":
            paused_label = tk.Label(
                self._screen_frame,
                text="Game Paused",
                font=("Segoe UI", 16, "bold"),
                fg="orange",
            )
            paused_label.pack(pady=10)
            return

        # Playing state: show current question.
        index = getattr(self, "_current_question_index", 0)
        if index >= len(self._questions):
            self.end_game()
            self.show_play_game()
            return

        question = self._questions[index]

        prompt_label = tk.Label(
            self._screen_frame,
            text=question.prompt,
            font=("Segoe UI", 16, "bold"),
            wraplength=600,
        )
        prompt_label.pack(pady=10)

        self._answer_var = tk.IntVar(value=-1)
        for i, option in enumerate(question.options):
            radio = tk.Radiobutton(
                self._screen_frame,
                text=option,
                variable=self._answer_var,
                value=i,
                font=("Segoe UI", 12),
            )
            radio.pack(anchor=tk.W, padx=80, pady=2)

        self._status_label = tk.Label(
            self._screen_frame, text="", font=("Segoe UI", 10), fg="green"
        )
        self._status_label.pack(pady=(10, 5))

        button_frame = tk.Frame(self._screen_frame)
        button_frame.pack(pady=10)

        submit_btn = tk.Button(
            button_frame,
            text="Submit Answer",
            command=self._submit_selected_answer,
            width=16,
        )
        submit_btn.pack(side=tk.LEFT, padx=5)

        pause_btn = tk.Button(
            button_frame,
            text="Pause",
            command=self.toggle_pause,
            width=16,
        )
        pause_btn.pack(side=tk.LEFT, padx=5)

        end_btn = tk.Button(
            button_frame,
            text="End Game",
            command=self.end_game,
            width=16,
        )
        end_btn.pack(side=tk.LEFT, padx=5)

    def _submit_selected_answer(self) -> None:
        """Read the selected radio answer and submit it."""
        answer_var = getattr(self, "_answer_var", None)
        if answer_var is None:
            return
        selected = answer_var.get()
        if selected >= 0:
            self.submit_answer(selected)

    def submit_answer(self, answer_index: int) -> None:
        """Submit answer for current question."""
        game = self._current_game
        if game is None or game.state != "Playing":
            return

        index = getattr(self, "_current_question_index", 0)
        if index >= len(self._questions):
            return

        question = self._questions[index]
        if answer_index == question.answer_index:
            game.score += 1
            feedback = "Correct!"
        else:
            feedback = "Incorrect."

        self._set_status(feedback)

        # Advance to the next question.
        self._current_question_index = index + 1
        if self._current_question_index >= len(self._questions):
            self.end_game()
        else:
            # Re-render the play screen with the next question.
            self.show_play_game()

    def toggle_pause(self) -> None:
        """Toggle pause/resume state of current game."""
        game = self._current_game
        if game is None:
            return

        if game.state == "Playing":
            game.pause()
        elif game.state == "Paused":
            game.resume()

        self.show_play_game()

    def end_game(self) -> None:
        """Transition Game.state to GameOver."""
        game = self._current_game
        if game is None:
            return

        game.game_over()
        self.show_play_game()

    # ------------------------------------------------------------------
    # Admin flow
    # ------------------------------------------------------------------
    def update_questions(self, questions: list) -> None:
        """Update questions list (Admin flow)."""
        self._questions = list(questions)
        self._set_status(f"Questions updated: {len(self._questions)} total.")

    def _apply_questions_from_text(self) -> None:
        """Parse the JSON text area and update questions."""
        import json

        text_widget = getattr(self, "_questions_text", None)
        if text_widget is None:
            return

        raw = text_widget.get("1.0", tk.END).strip()
        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("Expected a JSON list.")
            questions = [
                Question(
                    id=str(item["id"]),
                    prompt=str(item["prompt"]),
                    options=list(item["options"]),
                    answer_index=int(item["answer_index"]),
                )
                for item in data
            ]
            self.update_questions(questions)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            self._set_status(f"Error: {exc}")


def create_app() -> App:
    """Create and return an App instance with a fresh Tkinter root."""
    root = tk.Tk()
    app = App(root)
    return app


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
