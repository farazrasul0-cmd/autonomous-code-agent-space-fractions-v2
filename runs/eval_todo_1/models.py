"""Domain models for the Smart To-Do List application.

This module provides the core data classes used by the application:

* :class:`Task` - a single to-do item with an id, title, and state.
* :class:`TaskManager` - a collection of tasks with operations to add,
  list, and complete tasks.

The module uses only the Python 3.12 standard library.
"""

from __future__ import annotations

import uuid
from typing import List


class Task:
    """Represents a single to-do item.

    A task has a unique identifier, a human-readable title, and a state
    that is either ``"pending"`` or ``"completed"``.
    """

    def __init__(self, title: str) -> None:
        """Create a new task with the given title.

        The task is assigned a unique id and starts in the ``"pending"``
        state.
        """
        self._id: str = str(uuid.uuid4())
        self._title: str = title
        self._state: str = "pending"

    @property
    def id(self) -> str:
        """Return the unique identifier of the task."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """Set the unique identifier of the task."""
        self._id = value

    @property
    def title(self) -> str:
        """Return the title of the task."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Set the title of the task."""
        self._title = value

    @property
    def state(self) -> str:
        """Return the current state of the task."""
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        """Set the current state of the task."""
        self._state = value

    def mark_completed(self) -> None:
        """Transition the task from ``"pending"`` to ``"completed"``."""
        self._state = "completed"

    def get_title(self) -> str:
        """Return the title of the task."""
        return self._title


class TaskManager:
    """Manages a collection of :class:`Task` objects."""

    def __init__(self) -> None:
        """Create an empty task manager."""
        self._tasks: List[Task] = []

    @property
    def tasks(self) -> List[Task]:
        """Return the list of tasks managed by this object."""
        return self._tasks

    @tasks.setter
    def tasks(self, value: List[Task]) -> None:
        """Replace the list of tasks managed by this object."""
        self._tasks = value

    def add_task(self, title: str) -> Task:
        """Create a new task with the given title and add it to the manager.

        Args:
            title: The title for the new task.

        Returns:
            The newly created :class:`Task` instance.
        """
        task = Task(title)
        self._tasks.append(task)
        return task

    def get_tasks(self) -> List[Task]:
        """Return the list of tasks managed by this object."""
        return self._tasks

    def complete_task(self, task_id: str) -> None:
        """Mark the task with the given id as completed.

        If no task matches ``task_id``, this method does nothing.

        Args:
            task_id: The unique identifier of the task to complete.
        """
        for task in self._tasks:
            if task.id == task_id:
                task.mark_completed()
                break
