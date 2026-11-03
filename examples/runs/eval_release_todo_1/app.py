"""Smart To-Do List - Tkinter GUI application.

This module implements the App class, a standalone Windows desktop
application built with the Python 3.12 standard library only.
"""

import tkinter as tk
from tkinter import ttk

from models import TaskManager


class App:
    """Main Tkinter application window for the Smart To-Do List."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application window and its widgets.

        Args:
            root: The root Tkinter window.
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
        """Return the task manager instance."""
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
        """Build the application's user interface."""
        main_frame = ttk.Frame(self._root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Label(
            main_frame,
            text="Smart To-Do List",
            font=("Segoe UI", 16, "bold"),
        )
        header.pack(pady=(0, 10))

        # Entry row
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        self._title_entry = ttk.Entry(entry_frame)
        self._title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self._title_entry.bind("<Return>", lambda _event: self.add_task())

        add_button = ttk.Button(entry_frame, text="Add Task", command=self.add_task)
        add_button.pack(side=tk.RIGHT)

        # Listbox with scrollbar
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

        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        complete_button = ttk.Button(
            button_frame, text="Complete Selected", command=self.complete_task
        )
        complete_button.pack(side=tk.LEFT, padx=(0, 5))

        refresh_button = ttk.Button(
            button_frame, text="Refresh", command=self.refresh_task_list
        )
        refresh_button.pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Application methods
    # ------------------------------------------------------------------
    def add_task(self) -> None:
        """Add a new task from the entry field."""
        title = self._title_entry.get().strip()
        if not title:
            return

        self._task_manager.add_task(title)
        self._title_entry.delete(0, tk.END)
        self.refresh_task_list()

    def complete_task(self) -> None:
        """Mark the selected task as completed."""
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
        """Update the listbox with current tasks."""
        self._task_listbox.delete(0, tk.END)

        for task in self._task_manager.get_tasks():
            prefix = "[x]" if task.state == "Completed" else "[ ]"
            self._task_listbox.insert(tk.END, f"{prefix} {task.get_title()}")
