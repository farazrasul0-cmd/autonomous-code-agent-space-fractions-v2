import sys
import unittest
import tkinter as tk
from pathlib import Path

repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.insert(0, str(repo_dir))

from models import Task, TaskManager
from app import App
from main import create_app


class TestTask(unittest.TestCase):
    """Tests for the Task class."""

    def test_init_sets_title(self):
        task = Task("Buy groceries")
        self.assertEqual(task.title, "Buy groceries")

    def test_id_is_generated(self):
        task = Task("Some task")
        self.assertIsInstance(task.id, str)
        self.assertTrue(task.id)

    def test_id_is_settable(self):
        task = Task("Some task")
        task.id = "custom-id"
        self.assertEqual(task.id, "custom-id")

    def test_title_is_settable(self):
        task = Task("Original")
        task.title = "Updated"
        self.assertEqual(task.title, "Updated")

    def test_default_state_is_pending(self):
        task = Task("Some task")
        self.assertEqual(task.state, "pending")

    def test_state_is_settable(self):
        task = Task("Some task")
        task.state = "completed"
        self.assertEqual(task.state, "completed")

    def test_mark_completed_transitions_state(self):
        task = Task("Some task")
        self.assertEqual(task.state, "pending")
        task.mark_completed()
        self.assertEqual(task.state, "completed")

    def test_get_title_returns_title(self):
        task = Task("Read a book")
        self.assertEqual(task.get_title(), "Read a book")


class TestTaskManager(unittest.TestCase):
    """Tests for the TaskManager class."""

    def setUp(self):
        self.manager = TaskManager()

    def test_init_has_empty_tasks(self):
        self.assertEqual(self.manager.tasks, [])

    def test_tasks_is_settable(self):
        task = Task("Sample")
        self.manager.tasks = [task]
        self.assertEqual(self.manager.tasks, [task])

    def test_add_task_returns_task(self):
        task = self.manager.add_task("Write tests")
        self.assertIsInstance(task, Task)
        self.assertEqual(task.title, "Write tests")

    def test_add_task_appends_to_tasks(self):
        self.manager.add_task("First")
        self.manager.add_task("Second")
        self.assertEqual(len(self.manager.tasks), 2)
        self.assertEqual(self.manager.tasks[0].title, "First")
        self.assertEqual(self.manager.tasks[1].title, "Second")

    def test_get_tasks_returns_list(self):
        self.manager.add_task("Task A")
        tasks = self.manager.get_tasks()
        self.assertIsInstance(tasks, list)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Task A")

    def test_complete_task_marks_completed(self):
        task = self.manager.add_task("Finish work")
        self.assertEqual(task.state, "pending")
        self.manager.complete_task(task.id)
        self.assertEqual(task.state, "completed")

    def test_complete_task_unknown_id_does_not_raise(self):
        self.manager.add_task("Existing")
        # Completing a non-existent task id should not raise.
        self.manager.complete_task("does-not-exist")


class TestApp(unittest.TestCase):
    """Tests for the App class."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = App(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_root_property(self):
        self.assertIs(self.app.root, self.root)

    def test_root_is_settable(self):
        new_root = tk.Tk()
        new_root.withdraw()
        try:
            self.app.root = new_root
            self.assertIs(self.app.root, new_root)
        finally:
            new_root.destroy()

    def test_task_manager_property(self):
        self.assertIsInstance(self.app.task_manager, TaskManager)

    def test_task_manager_is_settable(self):
        manager = TaskManager()
        self.app.task_manager = manager
        self.assertIs(self.app.task_manager, manager)

    def test_task_listbox_property(self):
        self.assertIsInstance(self.app.task_listbox, tk.Listbox)

    def test_task_listbox_is_settable(self):
        listbox = tk.Listbox(self.root)
        self.app.task_listbox = listbox
        self.assertIs(self.app.task_listbox, listbox)

    def test_title_entry_property(self):
        self.assertIsInstance(self.app.title_entry, tk.Entry)

    def test_title_entry_is_settable(self):
        entry = tk.Entry(self.root)
        self.app.title_entry = entry
        self.assertIs(self.app.title_entry, entry)

    def test_add_task_adds_to_manager(self):
        self.app.title_entry.insert(0, "New task")
        self.app.add_task()
        self.assertEqual(len(self.app.task_manager.tasks), 1)
        self.assertEqual(self.app.task_manager.tasks[0].title, "New task")

    def test_add_task_refreshes_listbox(self):
        self.app.title_entry.insert(0, "Listed task")
        self.app.add_task()
        self.assertEqual(self.app.task_listbox.size(), 1)

    def test_complete_task_completes_selected(self):
        task = self.app.task_manager.add_task("To complete")
        self.app.refresh_task_list()
        # Select the first (and only) item in the listbox.
        self.app.task_listbox.selection_set(0)
        self.app.complete_task()
        self.assertEqual(task.state, "completed")

    def test_refresh_task_list_populates_listbox(self):
        self.app.task_manager.add_task("One")
        self.app.task_manager.add_task("Two")
        self.app.refresh_task_list()
        self.assertEqual(self.app.task_listbox.size(), 2)


class TestMain(unittest.TestCase):
    """Tests for the main module's create_app function."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_create_app_returns_app(self):
        app = create_app(self.root)
        self.assertIsInstance(app, App)
        self.assertIs(app.root, self.root)


if __name__ == "__main__":
    unittest.main()
