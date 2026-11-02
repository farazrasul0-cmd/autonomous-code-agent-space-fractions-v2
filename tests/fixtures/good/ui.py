import tkinter as tk
from engine import Engine
from models import Counter

class UiFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.counter = Counter()
        self.engine = Engine(self.counter)

    def execute_run(self) -> None:
        self.engine.run()
