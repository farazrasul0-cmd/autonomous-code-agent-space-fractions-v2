"""Domain model classes for the Space Fractions desktop application.

This module defines the core domain entities used by the application:

* :class:`Game`      - represents a single game session and its lifecycle.
* :class:`Question`  - represents a single multiple-choice question.
* :class:`User`      - represents a player account.
* :class:`Admin`     - represents an administrator account.

All classes use single-underscore private attributes (``_name``) together with
public properties so that cross-module access such as ``obj.state`` or
``obj.score += 1`` works reliably without Python name mangling.
"""

from typing import List


class Game:
    """A single game session.

    A game progresses through the states ``Playing``, ``Paused``, and
    ``GameOver``.  The score is tracked as an integer and can be inspected at
    any time.
    """

    def __init__(self, id: str, score: int) -> None:
        """Create a new game session.

        Args:
            id: Unique identifier for the game session.
            score: Initial score for the game session.
        """
        self._id = id
        self._score = score
        self._state = "Playing"

    @property
    def id(self) -> str:
        """Return the game session identifier."""
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
        """Start or continue playing the game.

        The game is placed into the ``Playing`` state.
        """
        self._state = "Playing"

    def view_score(self) -> int:
        """Return the current score.

        Returns:
            The current integer score.
        """
        return self._score

    def pause(self) -> None:
        """Pause the game.

        The game is placed into the ``Paused`` state.
        """
        self._state = "Paused"

    def resume(self) -> None:
        """Resume a paused game.

        The game is placed back into the ``Playing`` state.
        """
        self._state = "Playing"

    def game_over(self) -> None:
        """End the game.

        The game is placed into the ``GameOver`` state.
        """
        self._state = "GameOver"


class Question:
    """A single multiple-choice question."""

    def __init__(
        self,
        id: str,
        prompt: str,
        options: List[str],
        answer_index: int,
    ) -> None:
        """Create a question.

        Args:
            id: Unique identifier for the question.
            prompt: The question text shown to the player.
            options: The list of possible answers.
            answer_index: Index (into ``options``) of the correct answer.
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
        """Return the question prompt text."""
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
        """Return the question prompt text.

        Returns:
            The prompt string.
        """
        return self._prompt

    def get_options(self) -> List[str]:
        """Return the list of answer options.

        Returns:
            A list of option strings.
        """
        return self._options

    def get_answer_index(self) -> int:
        """Return the index of the correct answer.

        Returns:
            The integer index of the correct answer.
        """
        return self._answer_index


class User:
    """A player account."""

    def __init__(self, id: str, username: str) -> None:
        """Create a user account.

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
        """Start playing the supplied game.

        Args:
            game: The :class:`Game` instance to play.
        """
        game.play()

    def view_score(self, game: Game) -> int:
        """Return the score of the supplied game.

        Args:
            game: The :class:`Game` instance whose score is requested.

        Returns:
            The current integer score of the game.
        """
        return game.view_score()


class Admin:
    """An administrator account."""

    def __init__(self, id: str, username: str) -> None:
        """Create an administrator account.

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

        The supplied list replaces the administrator's current question set.
        The list is stored by reference so that callers can continue to mutate
        it if desired.

        Args:
            questions: The new list of :class:`Question` instances.
        """
        self._questions = questions

    @property
    def questions(self) -> List[Question]:
        """Return the administrator's current question set.

        Returns:
            The list of :class:`Question` instances, or ``None`` if
            :meth:`update_questions` has not been called yet.
        """
        return getattr(self, "_questions", None)

    @questions.setter
    def questions(self, value: List[Question]) -> None:
        self._questions = value
