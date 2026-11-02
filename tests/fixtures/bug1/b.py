from a import Engine

class App:
    def __init__(self):
        self.engine = Engine()

    def run(self):
        self.other = object()
        return self.other.start()  # 'other' has no start
