"""Domain model classes for the standalone Windows desktop application.

This module defines the core entities used by the application:

* :class:`Game` - represents a single game session with a score and state.
* :class:`Question` - represents a trivia question and its answer options.
* :class:`User` - represents a player who can play games.
* :class:`Admin` - represents an administrator who can manage questions.

Only the Python 3.12 standard library is used.
"""

from __future__ import annotations

from typing import List


class Game:
    """A single game session.

    A game starts in the ``Playing`` state, can be paused/resumed, and
    eventually transitions to ``GameOver``.
    """

    # Valid states for a game session.
    STATE_PLAYING = "Playing"
    STATE_PAUSED = "Paused"
    STATE_GAME_OVER = "GameOver"

    def __init__(self, id: str, score: int) -> None:
        """Initialize a new game session.

        Args:
            id: Unique identifier for the game.
            score: Initial score for the game.
        """
        self.__id = id
        self.__score = score
        self.__state = self.STATE_PLAYING

    def play(self) -> None:
        """Start or continue playing the game.

        If the game is currently paused, it is resumed. If the game is
        already over, this method has no effect.
        """
        if self.__state == self.STATE_PAUSED:
            self.__state = self.STATE_PLAYING
        elif self.__state == self.STATE_GAME_OVER:
            # A finished game cannot be played again.
            return
        # If already playing, nothing needs to change.

    def view_score(self) -> int:
        """Return the current score of the game."""
        return self.__score

    def pause(self) -> None:
        """Pause the game if it is currently being played."""
        if self.__state == self.STATE_PLAYING:
            self.__state = self.STATE_PAUSED

    def resume(self) -> None:
        """Resume the game if it is currently paused."""
        if self.__state == self.STATE_PAUSED:
            self.__state = self.STATE_PLAYING

    def game_over(self) -> None:
        """End the game session.

        The game transitions to the ``GameOver`` state. This is only
        meaningful while the game is being played.
        """
        if self.__state == self.STATE_PLAYING:
            self.__state = self.STATE_GAME_OVER


class Question:
    """A trivia question with a prompt, answer options, and correct answer."""

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
            options: The list of possible answers.
            answer_index: Index into ``options`` of the correct answer.
        """
        self.__id = id
        self.__prompt = prompt
        self.__options = list(options)
        self.__answer_index = answer_index

    def get_prompt(self) -> str:
        """Return the question prompt text."""
        return self.__prompt

    def get_options(self) -> List[str]:
        """Return a copy of the answer options."""
        return list(self.__options)

    def get_answer_index(self) -> int:
        """Return the index of the correct answer."""
        return self.__answer_index


class User:
    """A player who can play games and view scores."""

    def __init__(self, id: str, username: str) -> None:
        """Initialize a user.

        Args:
            id: Unique identifier for the user.
            username: The user's display name.
        """
        self.__id = id
        self.__username = username

    def play_game(self, game: Game) -> None:
        """Start playing the provided game.

        Args:
            game: The game session to play.
        """
        game.play()

    def view_score(self, game: Game) -> int:
        """Return the score of the provided game.

        Args:
            game: The game session whose score should be returned.
        """
        return game.view_score()


class Admin:
    """An administrator who can manage the question bank."""

    def __init__(self, id: str, username: str) -> None:
        """Initialize an administrator.

        Args:
            id: Unique identifier for the administrator.
            username: The administrator's display name.
        """
        self.__id = id
        self.__username = username

    def update_questions(self, questions: List[Question]) -> None:
        """Update the set of questions managed by the administrator.

        Args:
            questions: The new collection of questions.
        """
        # Store a defensive copy so external mutation does not affect the
        # administrator's managed question set.
        self.__questions = list(questions)
