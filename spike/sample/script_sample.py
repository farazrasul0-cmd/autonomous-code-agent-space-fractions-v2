# script_sample.py - Sample script importing random, tkinter.messagebox, and all 20 hidden imports
import sys

# Core required imports
import random
import tkinter.messagebox

# Test all 20 required hidden imports
hidden_modules = [
    "random", "dataclasses", "enum", "fractions", "uuid", "math",
    "typing", "itertools", "functools", "collections", "datetime",
    "pathlib", "copy", "tkinter", "tkinter.ttk", "tkinter.messagebox",
    "tkinter.simpledialog", "tkinter.font", "unittest", "unittest.mock"
]

imported = []
for mod in hidden_modules:
    __import__(mod)
    imported.append(mod)

num = random.randint(100, 999)
print(f"SUCCESS: random={num}")
print(f"SUCCESS: tkinter.messagebox={tkinter.messagebox.__name__}")
print(f"SUCCESS: all {len(imported)} hidden imports loaded successfully: {', '.join(imported)}")
sys.stdout.flush()
