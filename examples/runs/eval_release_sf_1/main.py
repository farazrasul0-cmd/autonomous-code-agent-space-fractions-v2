import sys, os
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import tkinter as tk

from app import Application


def create_app(root: tk.Tk) -> Application:
    """Create and return the application instance."""
    return Application(root)


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Space Fractions")
    create_app(root)
    root.mainloop()
