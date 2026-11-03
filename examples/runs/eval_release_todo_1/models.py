"""Domain models for the Smart To-Do List application.

This module provides the core data classes used by the application:

* :class:`Task` - a single to-do item with an id, title, and state.
* :class:`TaskManager` - a collection of tasks with basic operations.

Only the Python 3.12 standard library is used.
"""

import uuid
from typing import List


class Task:
    """A single to-do item.

    Attributes:
        id: Unique identifier for the task.
        title: Human-readable description of the task.
        state: Current state of the task (``"Pending"`` or ``"Completed"``).
    """

    PENDING = "Pending"
    COMPLETED = "Completed"

    def __init__(self, title: str, task_id: str | None = None, state: str | None = None) -> None:
        """Create a new task.

        Args:
            title: The task description.
            task_id: Optional unique identifier. If omitted, a UUID is generated.
            state: Optional initial state. If omitted, defaults to ``"Pending"``.
        """
        self._id = task_id if task_id is not None else str(uuid.uuid4())
        self._title = title
        self._state = state if state is not None else self.PENDING

    @property
    def id(self) -> str:
        """Return the task's unique identifier."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """Set the task's unique identifier."""
        self._id = value

    @property
    def title(self) -> str:
        """Return the task's title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Set the task's title."""
        self._title = value

    @property
    def state(self) -> str:
        """Return the task's current state."""
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        """Set the task's current state."""
        self._state = value

    def mark_completed(self) -> None:
        """Transition the task from ``Pending`` to ``Completed``."""
        self._state = self.COMPLETED

    def get_title(self) -> str:
        """Return the task's title."""
        return self._title


class TaskManager:
    """Manages a collection of :class:`Task` objects."""

    def __init__(self, tasks: List[Task] | None = None) -> None:
        """Create a task manager.

        Args:
            tasks: Optional initial list of tasks. If omitted, an empty list is used.
        """
        self._tasks = tasks if tasks is not None else []

    @property
    def tasks(self) -> List[Task]:
        """Return the list of tasks managed by this instance."""
        return self._tasks

    @tasks.setter
    def tasks(self, value: List[Task]) -> None:
        """Replace the managed task list."""
        self._tasks = value

    def add_task(self, title: str) -> Task:
        """Create a new task with the given title and add it to the manager.

        Args:
            title: The description for the new task.

        Returns:
            The newly created :class:`Task`.
        """
        task = Task(title)
        self._tasks.append(task)
        return task

    def get_tasks(self) -> List[Task]:
        """Return all tasks currently managed.

        Returns:
            A list of :class:`Task` objects.
        """
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
                return
