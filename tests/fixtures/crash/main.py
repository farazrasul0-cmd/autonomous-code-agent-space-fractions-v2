class CrashingApp:
    def __init__(self, root):
        self.root = root

    def start_play_game(self):
        raise RuntimeError("Simulated UI crash in start_play_game")

def create_app(root):
    return CrashingApp(root)
