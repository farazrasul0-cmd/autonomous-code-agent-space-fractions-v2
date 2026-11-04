"""Space Fractions - Standalone Windows Desktop Application.

Implements the Application class with a Tkinter GUI and game logic.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional

from models import Game, Question, User, Admin


class Application:
    """Main application class managing the UI and game logic."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application with a Tkinter root window."""
        self._root = root
        self._current_user: Optional[User] = None
        self._current_game: Optional[Game] = None
        self._questions: List[Question] = []
        self._current_frame: Optional[tk.Frame] = None
        self._current_question_index: int = 0
        self._status_label: Optional[tk.Label] = None
        self._answer_buttons: List[tk.Button] = []
        self._question_label: Optional[tk.Label] = None
        self._pause_button: Optional[tk.Button] = None
        self._score_label: Optional[tk.Label] = None

        # Seed content so the application is immediately usable.
        self._questions = self._seed_questions()

        # Configure root window.
        self._root.title("Space Fractions")
        self._root.geometry("700x500")
        self._root.minsize(500, 400)

        # Show the main menu on launch.
        self.show_menu()

    # ------------------------------------------------------------------
    # Properties (Rule 1: getter + setter for every declared attribute)
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
                "What is 2/3 - 1/3?",
                ["1/3", "1/2", "1", "2/6"],
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
                ["2/3", "3/6", "2/5", "3/4"],
                1,
            ),
            Question(
                "q5",
                "What is 3/4 + 1/4?",
                ["1", "3/8", "4/8", "1/2"],
                0,
            ),
        ]

    # ------------------------------------------------------------------
    # Screen management
    # ------------------------------------------------------------------
    def _clear_screen(self) -> None:
        """Destroy all children of the root window and reset current frame."""
        for widget in self._root.winfo_children():
            widget.destroy()
        self._current_frame = None
        self._status_label = None
        self._answer_buttons = []
        self._question_label = None
        self._pause_button = None
        self._score_label = None

    def _create_frame(self) -> tk.Frame:
        """Create and return a fresh frame filling the root window."""
        frame = tk.Frame(self._root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        self._current_frame = frame
        return frame

    def _set_status(self, message: str) -> None:
        """Update the status label if it exists."""
        if self._status_label is not None:
            self._status_label.config(text=message)

    # ------------------------------------------------------------------
    # Navigation methods
    # ------------------------------------------------------------------
    def show_menu(self) -> None:
        """Navigate to main menu screen."""
        self._clear_screen()
        frame = self._create_frame()

        title = tk.Label(
            frame,
            text="Space Fractions",
            font=("Arial", 28, "bold"),
        )
        title.pack(pady=(20, 10))

        subtitle = tk.Label(
            frame,
            text="Learn fractions while exploring space!",
            font=("Arial", 14),
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
                frame,
                text=text,
                command=command,
                width=24,
                font=("Arial", 12),
            )
            btn.pack(pady=8)

        self._status_label = tk.Label(
            frame,
            text="Welcome! Choose an option to begin.",
            font=("Arial", 10),
            fg="gray",
        )
        self._status_label.pack(pady=(30, 0))

    def show_play_game(self) -> None:
        """Navigate to game screen."""
        self._clear_screen()
        frame = self._create_frame()

        title = tk.Label(
            frame,
            text="Play Game",
            font=("Arial", 22, "bold"),
        )
        title.pack(pady=(10, 20))

        self._question_label = tk.Label(
            frame,
            text="",
            font=("Arial", 16),
            wraplength=600,
            justify="center",
        )
        self._question_label.pack(pady=20)

        answers_frame = tk.Frame(frame)
        answers_frame.pack(pady=10)

        self._answer_buttons = []
        for i in range(4):
            btn = tk.Button(
                answers_frame,
                text="",
                width=30,
                font=("Arial", 12),
                command=lambda idx=i: self.submit_answer(idx),
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10)
            self._answer_buttons.append(btn)

        controls = tk.Frame(frame)
        controls.pack(pady=20)

        self._pause_button = tk.Button(
            controls,
            text="Pause",
            command=self.toggle_pause,
            width=12,
            font=("Arial", 11),
        )
        self._pause_button.grid(row=0, column=0, padx=10)

        end_btn = tk.Button(
            controls,
            text="End Game",
            command=self.end_game,
            width=12,
            font=("Arial", 11),
        )
        end_btn.grid(row=0, column=1, padx=10)

        menu_btn = tk.Button(
            controls,
            text="Main Menu",
            command=self.show_menu,
            width=12,
            font=("Arial", 11),
        )
        menu_btn.grid(row=0, column=2, padx=10)

        self._score_label = tk.Label(
            frame,
            text="Score: 0",
            font=("Arial", 12, "bold"),
        )
        self._score_label.pack(pady=(10, 0))

        self._status_label = tk.Label(
            frame,
            text="",
            font=("Arial", 10),
            fg="blue",
        )
        self._status_label.pack(pady=(10, 0))

        # Render the current question if a game is active.
        self._render_question()

    def show_view_score(self) -> None:
        """Navigate to score screen."""
        self._clear_screen()
        frame = self._create_frame()

        title = tk.Label(
            frame,
            text="View Score",
            font=("Arial", 22, "bold"),
        )
        title.pack(pady=(10, 20))

        if self._current_game is not None:
            score = self._current_game.view_score()
            state = self._current_game.state
            score_text = f"Current Score: {score}"
            state_text = f"Game State: {state}"
        else:
            score_text = "No game has been played yet."
            state_text = ""

        score_label = tk.Label(
            frame,
            text=score_text,
            font=("Arial", 16),
        )
        score_label.pack(pady=10)

        if state_text:
            state_label = tk.Label(
                frame,
                text=state_text,
                font=("Arial", 12),
            )
            state_label.pack(pady=5)

        back_btn = tk.Button(
            frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
            font=("Arial", 12),
        )
        back_btn.pack(pady=30)

        self._status_label = tk.Label(
            frame,
            text="",
            font=("Arial", 10),
            fg="gray",
        )
        self._status_label.pack(pady=(10, 0))

    def show_update_questions(self) -> None:
        """Navigate to admin questions screen."""
        self._clear_screen()
        frame = self._create_frame()

        title = tk.Label(
            frame,
            text="Update Questions",
            font=("Arial", 22, "bold"),
        )
        title.pack(pady=(10, 10))

        info = tk.Label(
            frame,
            text="Admin: manage the question bank below.",
            font=("Arial", 12),
        )
        info.pack(pady=(0, 20))

        # Listbox showing current questions.
        list_frame = tk.Frame(frame)
        list_frame.pack(fill="both", expand=True, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 11),
        )
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        for question in self._questions:
            listbox.insert("end", question.get_prompt())

        # Entry fields for adding a new question.
        entry_frame = tk.Frame(frame)
        entry_frame.pack(pady=10)

        prompt_label = tk.Label(entry_frame, text="Prompt:")
        prompt_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        prompt_entry = tk.Entry(entry_frame, width=40)
        prompt_entry.grid(row=0, column=1, padx=5, pady=2)

        options_label = tk.Label(
            entry_frame,
            text="Options (comma-separated):",
        )
        options_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        options_entry = tk.Entry(entry_frame, width=40)
        options_entry.grid(row=1, column=1, padx=5, pady=2)

        answer_label = tk.Label(entry_frame, text="Answer index (0-3):")
        answer_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        answer_entry = tk.Entry(entry_frame, width=10)
        answer_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)

        self._status_label = tk.Label(
            frame,
            text="",
            font=("Arial", 10),
            fg="green",
        )
        self._status_label.pack(pady=(5, 0))

        def add_question() -> None:
            """Add a new question from the entry fields."""
            prompt = prompt_entry.get().strip()
            options_text = options_entry.get().strip()
            answer_text = answer_entry.get().strip()

            if not prompt or not options_text or not answer_text:
                self._set_status("Please fill in all fields.")
                return

            options = [opt.strip() for opt in options_text.split(",")]
            if len(options) != 4:
                self._set_status("Please provide exactly 4 options.")
                return

            try:
                answer_index = int(answer_text)
            except ValueError:
                self._set_status("Answer index must be an integer.")
                return

            if answer_index < 0 or answer_index > 3:
                self._set_status("Answer index must be between 0 and 3.")
                return

            new_question = Question(
                f"q{len(self._questions) + 1}",
                prompt,
                options,
                answer_index,
            )
            self._questions.append(new_question)
            listbox.insert("end", prompt)
            prompt_entry.delete(0, "end")
            options_entry.delete(0, "end")
            answer_entry.delete(0, "end")
            self._set_status("Question added successfully.")

        add_btn = tk.Button(
            frame,
            text="Add Question",
            command=add_question,
            width=20,
            font=("Arial", 11),
        )
        add_btn.pack(pady=5)

        back_btn = tk.Button(
            frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
            font=("Arial", 11),
        )
        back_btn.pack(pady=5)

    def show_help(self) -> None:
        """Navigate to help screen."""
        self._clear_screen()
        frame = self._create_frame()

        title = tk.Label(
            frame,
            text="Space Fractions - Help",
            font=("Arial", 22, "bold"),
        )
        title.pack(pady=(10, 20))

        help_text = (
            "Welcome to Space Fractions!\n\n"
            "How to Play:\n"
            "1. Click 'Play Game' from the main menu.\n"
            "2. Read each fraction question carefully.\n"
            "3. Click the correct answer from the four options.\n"
            "4. Earn points for each correct answer.\n"
            "5. Use 'Pause' to take a break and 'Resume' to continue.\n"
            "6. Click 'End Game' when you are finished.\n\n"
            "View your score anytime from the main menu.\n"
            "Admins can update questions via 'Update Questions'."
        )

        help_label = tk.Label(
            frame,
            text=help_text,
            font=("Arial", 12),
            justify="left",
            wraplength=600,
        )
        help_label.pack(pady=10)

        back_btn = tk.Button(
            frame,
            text="Back to Menu",
            command=self.show_menu,
            width=20,
            font=("Arial", 12),
        )
        back_btn.pack(pady=30)

        self._status_label = tk.Label(
            frame,
            text="",
            font=("Arial", 10),
            fg="gray",
        )
        self._status_label.pack(pady=(10, 0))

    # ------------------------------------------------------------------
    # Game logic methods
    # ------------------------------------------------------------------
    def start_play_game(self) -> None:
        """Navigate to play screen and initialize game state."""
        # Create a new game session.
        self._current_game = Game("game1", 0)
        self._current_game.play()
        self._current_question_index = 0

        # Create a default user if none exists.
        if self._current_user is None:
            self._current_user = User("user1", "Player")

        self.show_play_game()

    def submit_answer(self, answer_index: int) -> None:
        """Submit answer for current question."""
        if self._current_game is None:
            self._set_status("No active game. Start a new game first.")
            return

        if self._current_game.state != "Playing":
            self._set_status("Game is not currently playing.")
            return

        if not self._questions:
            self._set_status("No questions available.")
            return

        if self._current_question_index >= len(self._questions):
            self._set_status("No more questions. End the game to finish.")
            return

        question = self._questions[self._current_question_index]

        if answer_index == question.get_answer_index():
            self._current_game.score += 1
            self._set_status("Correct! +1 point")
        else:
            self._set_status("Incorrect. Try the next one!")

        # Advance to the next question.
        self._current_question_index += 1

        # Update score label.
        if self._score_label is not None:
            self._score_label.config(
                text=f"Score: {self._current_game.score}"
            )

        # Render next question or indicate completion.
        if self._current_question_index >= len(self._questions):
            self._render_question()
            self._set_status(
                "All questions answered! End the game to finish."
            )
        else:
            self._render_question()

    def toggle_pause(self) -> None:
        """Toggle pause/resume state of current game."""
        if self._current_game is None:
            self._set_status("No active game to pause.")
            return

        if self._current_game.state == "Playing":
            self._current_game.pause()
            if self._pause_button is not None:
                self._pause_button.config(text="Resume")
            self._set_status("Game paused.")
        elif self._current_game.state == "Paused":
            self._current_game.resume()
            if self._pause_button is not None:
                self._pause_button.config(text="Pause")
            self._set_status("Game resumed.")
        else:
            self._set_status("Game is over. Start a new game.")

    def end_game(self) -> None:
        """Transition Game.state to GameOver."""
        if self._current_game is None:
            self._set_status("No active game to end.")
            return

        if self._current_game.state == "GameOver":
            self._set_status("Game is already over.")
            return

        self._current_game.game_over()
        self._set_status(
            f"Game over! Final score: {self._current_game.score}"
        )

        # Disable answer buttons after game over.
        for btn in self._answer_buttons:
            btn.config(state="disabled")

        if self._pause_button is not None:
            self._pause_button.config(state="disabled")

    def update_questions(self, questions: list) -> None:
        """Update questions list (Admin flow)."""
        self._questions = list(questions)
        self._set_status(f"Questions updated. Total: {len(self._questions)}")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _render_question(self) -> None:
        """Render the current question and its options on the play screen."""
        if self._question_label is None:
            return

        if not self._questions:
            self._question_label.config(text="No questions available.")
            for btn in self._answer_buttons:
                btn.config(text="", state="disabled")
            return

        if self._current_question_index >= len(self._questions):
            self._question_label.config(
                text="All questions answered! End the game to finish."
            )
            for btn in self._answer_buttons:
                btn.config(text="", state="disabled")
            return

        question = self._questions[self._current_question_index]
        self._question_label.config(text=question.get_prompt())

        options = question.get_options()
        for i, btn in enumerate(self._answer_buttons):
            if i < len(options):
                btn.config(text=options[i], state="normal")
            else:
                btn.config(text="", state="disabled")


def create_app() -> Application:
    """Create and return an Application instance with a hidden root window.

    This entry point is used by smoke tests to instantiate the app
    without requiring a visible display loop.
    """
    root = tk.Tk()
    root.withdraw()
    app = Application(root)
    return app


def main() -> None:
    """Run the application main loop."""
    root = tk.Tk()
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
