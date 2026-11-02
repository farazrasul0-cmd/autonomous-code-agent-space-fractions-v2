# game_sample.py - Detached sample Tk game window
import sys
import random
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("Space Fractions - Detached Sample Game")
root.geometry("380x220")
root.configure(bg="#1a1a2e")

title_lbl = tk.Label(
    root,
    text="Detached Game Running",
    font=("Arial", 14, "bold"),
    fg="#e94560",
    bg="#1a1a2e"
)
title_lbl.pack(pady=15)

info_lbl = tk.Label(
    root,
    text="Independent Process.\nSurvives parent window closure.",
    font=("Arial", 10),
    fg="#ffffff",
    bg="#1a1a2e"
)
info_lbl.pack(pady=5)

def on_click():
    n = random.randint(1, 10)
    messagebox.showinfo("Game Event", f"Fraction solved: {n}/10")

btn = tk.Button(
    root,
    text="Interactive Test Button",
    command=on_click,
    bg="#0f3460",
    fg="#ffffff",
    font=("Arial", 10, "bold"),
    padx=10,
    pady=5
)
btn.pack(pady=15)

# If launched with an auto-close delay for testing, schedule it
if "--auto-close" in sys.argv:
    idx = sys.argv.index("--auto-close")
    ms = int(sys.argv[idx + 1])
    root.after(ms, root.destroy)

root.mainloop()
