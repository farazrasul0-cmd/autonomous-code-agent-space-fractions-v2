"""Domain model classes for the Space Fractions desktop application.

This module provides the core domain entities used by the application:
Game, Question, User, and Admin. It relies exclusively on the Python 3.12
standard library and exposes public properties for every declared attribute
so that other modules (for example, the Tkinter UI layer) can read and
mutate state directly.
"""

from typing import List


class Game:
    """Represents a single game session.

    A game tracks its identifier, current score, and lifecycle state. The
    state is one of ``"Playing"``, ``"Paused"``, or ``"GameOver"``.
    """

    def __init__(self, id: str, score: int) -> None:
        """Initialize a new game session.

        Args:
            id: Unique identifier for the game session.
            score: Initial score for the game.
        """
        self._id = id
        self._score = score
        self._state = "Playing"

    @property
    def id(self) -> str:
        """Return the game identifier."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id = value

    @property
    def score(self) -> int:
        """Return the current score."""
        return self._score

    @score.setter
    def score(self, value: int) -> None:
        self._score = value

    @property
    def state(self) -> str:
        """Return the current game state."""
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        self._state = value

    def play(self) -> None:
        """Start or continue the game session."""
        self._state = "Playing"

    def view_score(self) -> int:
        """Return the current score."""
        return self._score

    def pause(self) -> None:
        """Pause the game session."""
        self._state = "Paused"

    def resume(self) -> None:
        """Resume a paused game session."""
        self._state = "Playing"

    def game_over(self) -> None:
        """End the game session."""
        self._state = "GameOver"


class Question:
    """Represents a single multiple-choice question."""

    def __init__(
        self,
        id: str,
        prompt: str,
        options: List[str],
        answer_index: int,
    ) -> None:
        """Initialize a question.

        Args:
            id: Unique identifier for the question.
            prompt: The question text shown to the player.
            options: The list of answer choices.
            answer_index: Index of the correct answer within ``options``.
        """
        self._id = id
        self._prompt = prompt
        self._options = options
        self._answer_index = answer_index

    @property
    def id(self) -> str:
        """Return the question identifier."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id = value

    @property
    def prompt(self) -> str:
        """Return the question prompt."""
        return self._prompt

    @prompt.setter
    def prompt(self, value: str) -> None:
        self._prompt = value

    @property
    def options(self) -> List[str]:
        """Return the list of answer options."""
        return self._options

    @options.setter
    def options(self, value: List[str]) -> None:
        self._options = value

    @property
    def answer_index(self) -> int:
        """Return the index of the correct answer."""
        return self._answer_index

    @answer_index.setter
    def answer_index(self, value: int) -> None:
        self._answer_index = value

    def get_prompt(self) -> str:
        """Return the question prompt."""
        return self._prompt

    def get_options(self) -> List[str]:
        """Return the list of answer options."""
        return self._options

    def get_answer_index(self) -> int:
        """Return the index of the correct answer."""
        return self._answer_index


class User:
    """Represents a player account."""

    def __init__(self, id: str, username: str) -> None:
        """Initialize a user.

        Args:
            id: Unique identifier for the user.
            username: The user's display name.
        """
        self._id = id
        self._username = username

    @property
    def id(self) -> str:
        """Return the user identifier."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id = value

    @property
    def username(self) -> str:
        """Return the username."""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        self._username = value

    def play_game(self, game: Game) -> None:
        """Start playing the given game session."""
        game.play()

    def view_score(self, game: Game) -> int:
        """Return the score of the given game session."""
        return game.view_score()


class Admin:
    """Represents an administrator account."""

    def __init__(self, id: str, username: str) -> None:
        """Initialize an administrator.

        Args:
            id: Unique identifier for the administrator.
            username: The administrator's display name.
        """
        self._id = id
        self._username = username

    @property
    def id(self) -> str:
        """Return the administrator identifier."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id = value

    @property
    def username(self) -> str:
        """Return the administrator username."""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        self._username = value

    def update_questions(self, questions: List[Question]) -> None:
        """Update the set of questions managed by the administrator.

        Args:
            questions: The new list of questions to manage.
        """
        self._questions = questions

    @property
    def questions(self) -> List[Question]:
        """Return the questions currently managed by the administrator."""
        return self._questions

    @questions.setter
    def questions(self, value: List[Question]) -> None:
        self._questions = value
