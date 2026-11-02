"""Smart To-Do List - Tkinter GUI application.

This module provides the :class:`App` class, a standalone Windows desktop
application built with the Python 3.12 standard library only.
"""

import tkinter as tk
from tkinter import ttk

from models import TaskManager


class App:
    """Main Tkinter application window for the Smart To-Do List."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialise the application window and its widgets.

        Args:
            root: The root Tkinter window that hosts this application.
        """
        self._root = root
        self._task_manager = TaskManager()
        self._task_listbox = None
        self._title_entry = None

        self._root.title("Smart To-Do List")
        self._root.geometry("500x400")
        self._root.minsize(400, 300)

        self._build_ui()
        self.refresh_task_list()

    # ------------------------------------------------------------------
    # Attribute storage and accessors
    # ------------------------------------------------------------------
    @property
    def root(self) -> tk.Tk:
        """Return the root Tkinter window."""
        return self._root

    @root.setter
    def root(self, value: tk.Tk) -> None:
        self._root = value

    @property
    def task_manager(self) -> TaskManager:
        """Return the underlying task manager."""
        return self._task_manager

    @task_manager.setter
    def task_manager(self, value: TaskManager) -> None:
        self._task_manager = value

    @property
    def task_listbox(self) -> tk.Listbox:
        """Return the task listbox widget."""
        return self._task_listbox

    @task_listbox.setter
    def task_listbox(self, value: tk.Listbox) -> None:
        self._task_listbox = value

    @property
    def title_entry(self) -> tk.Entry:
        """Return the title entry widget."""
        return self._title_entry

    @title_entry.setter
    def title_entry(self, value: tk.Entry) -> None:
        self._title_entry = value

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Create and lay out the application widgets."""
        main_frame = ttk.Frame(self._root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Entry row for adding new tasks.
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        self._title_entry = ttk.Entry(entry_frame)
        self._title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self._title_entry.bind("<Return>", lambda _event: self.add_task())

        add_button = ttk.Button(entry_frame, text="Add Task", command=self.add_task)
        add_button.pack(side=tk.RIGHT)

        # Listbox showing current tasks.
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self._task_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            activestyle="dotbox",
        )
        scrollbar.config(command=self._task_listbox.yview)

        self._task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action row.
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        complete_button = ttk.Button(
            action_frame, text="Complete Selected", command=self.complete_task
        )
        complete_button.pack(side=tk.LEFT)

        refresh_button = ttk.Button(
            action_frame, text="Refresh", command=self.refresh_task_list
        )
        refresh_button.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Application methods
    # ------------------------------------------------------------------
    def add_task(self) -> None:
        """Add a new task from the entry field.

        Reads the current text from the title entry, adds it to the task
        manager, clears the entry, and refreshes the displayed list. Empty
        or whitespace-only input is ignored.
        """
        title = self._title_entry.get().strip()
        if not title:
            return

        self._task_manager.add_task(title)
        self._title_entry.delete(0, tk.END)
        self.refresh_task_list()

    def complete_task(self) -> None:
        """Mark the selected task as completed.

        If no task is selected, this method does nothing. Otherwise the
        selected task is completed and the list is refreshed.
        """
        selection = self._task_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        tasks = self._task_manager.get_tasks()
        if index < 0 or index >= len(tasks):
            return

        task = tasks[index]
        self._task_manager.complete_task(task.id)
        self.refresh_task_list()

    def refresh_task_list(self) -> None:
        """Update the listbox with the current tasks.

        Each task is displayed with its state and title. Completed tasks are
        shown with a visual marker.
        """
        self._task_listbox.delete(0, tk.END)

        for task in self._task_manager.get_tasks():
            if task.state == "Completed":
                display_text = f"[Completed] {task.get_title()}"
            else:
                display_text = f"[Pending] {task.get_title()}"
            self._task_listbox.insert(tk.END, display_text)
