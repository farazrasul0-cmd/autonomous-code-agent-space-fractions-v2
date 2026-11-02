from models import Counter

class Engine:
    def __init__(self, counter: Counter):
        self.counter = counter

    def run(self) -> None:
        self.counter.increment()
