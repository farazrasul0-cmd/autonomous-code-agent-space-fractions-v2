"""Smart To-Do List - Tkinter GUI application.

This module implements the App class, a standalone Windows desktop
application built with the Python 3.12 standard library only.
"""

import tkinter as tk
from tkinter import messagebox

from models import TaskManager


class App:
    """Main Tkinter application window for the Smart To-Do List."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application with the given Tk root window."""
        self._root = root
        self._task_manager = TaskManager()
        self._task_listbox = None
        self._title_entry = None
        self._current_frame = None

        self._root.title("Smart To-Do List")
        self._root.geometry("500x400")
        self._root.minsize(400, 300)

        self._build_ui()
        self.refresh_task_list()

    # ------------------------------------------------------------------
    # Attribute storage (Rule 1)
    # ------------------------------------------------------------------
    @property
    def root(self) -> tk.Tk:
        """Return the Tk root window."""
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
        """Build the main application layout."""
        self._clear_screen()

        main_frame = tk.Frame(self._root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self._current_frame = main_frame

        # Header
        header = tk.Label(
            main_frame,
            text="Smart To-Do List",
            font=("Segoe UI", 16, "bold"),
        )
        header.pack(pady=(0, 10))

        # Entry row
        entry_frame = tk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        self._title_entry = tk.Entry(entry_frame)
        self._title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self._title_entry.bind("<Return>", lambda event: self.add_task())

        add_button = tk.Button(
            entry_frame,
            text="Add Task",
            command=self.add_task,
        )
        add_button.pack(side=tk.RIGHT)

        # Task list
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self._task_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
        )
        scrollbar.config(command=self._task_listbox.yview)

        self._task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        complete_button = tk.Button(
            button_frame,
            text="Complete Selected",
            command=self.complete_task,
        )
        complete_button.pack(side=tk.LEFT, padx=(0, 5))

        refresh_button = tk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh_task_list,
        )
        refresh_button.pack(side=tk.LEFT)

        # Status label for non-blocking feedback
        self._status_label = tk.Label(
            main_frame,
            text="",
            anchor=tk.W,
            fg="#555555",
        )
        self._status_label.pack(fill=tk.X, pady=(10, 0))

    def _clear_screen(self) -> None:
        """Destroy all children of the root window and reset current frame."""
        for widget in self._root.winfo_children():
            widget.destroy()
        self._current_frame = None

    def _set_status(self, message: str) -> None:
        """Update the status label with a non-blocking message."""
        if hasattr(self, "_status_label") and self._status_label is not None:
            self._status_label.config(text=message)

    # ------------------------------------------------------------------
    # Application methods
    # ------------------------------------------------------------------
    def add_task(self) -> None:
        """Add a new task from the title entry."""
        if self._title_entry is None:
            return

        title = self._title_entry.get().strip()
        if not title:
            self._set_status("Please enter a task title.")
            return

        self._task_manager.add_task(title)
        self._title_entry.delete(0, tk.END)
        self.refresh_task_list()
        self._set_status(f"Added task: {title}")

    def complete_task(self) -> None:
        """Mark the selected task as completed."""
        if self._task_listbox is None:
            return

        selection = self._task_listbox.curselection()
        if not selection:
            self._set_status("Please select a task to complete.")
            return

        index = selection[0]
        tasks = self._task_manager.get_tasks()
        if index < 0 or index >= len(tasks):
            self._set_status("Invalid selection.")
            return

        task = tasks[index]
        if task.state == "Completed":
            self._set_status("Task is already completed.")
            return

        self._task_manager.complete_task(task.id)
        self.refresh_task_list()
        self._set_status(f"Completed task: {task.title}")

    def refresh_task_list(self) -> None:
        """Update the task listbox with current tasks."""
        if self._task_listbox is None:
            return

        self._task_listbox.delete(0, tk.END)

        for task in self._task_manager.get_tasks():
            prefix = "[x]" if task.state == "Completed" else "[ ]"
            display_text = f"{prefix} {task.title}"
            self._task_listbox.insert(tk.END, display_text)

            if task.state == "Completed":
                self._task_listbox.itemconfig(tk.END, fg="#888888")


def create_app() -> App:
    """Create and return an App instance for smoke testing.

    This helper is used by the smoke test surface to instantiate the
    application without requiring an external Tk root.
    """
    root = tk.Tk()
    root.withdraw()  # Keep the window hidden during automated testing.
    return App(root)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
