import sys, os
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import tkinter as tk
from ui import UiFrame

def create_app(root: tk.Tk) -> UiFrame:
    frame = UiFrame(root)
    frame.pack()
    return frame

if __name__ == "__main__":
    root = tk.Tk()
    app = create_app(root)
    root.mainloop()
