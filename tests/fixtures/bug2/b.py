from a import Question

class App:
    def __init__(self):
        self.q = Question()

    def run(self):
        return self.q.prompt()  # prompt is attribute, not method
