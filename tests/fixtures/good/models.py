class Counter:
    def __init__(self):
        self._count = 0

    def increment(self) -> None:
        self._count += 1

    def get_count(self) -> int:
        return self._count
