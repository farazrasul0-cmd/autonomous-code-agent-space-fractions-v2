# test_sample.py - Tiny unittest sample for Spike
import unittest

class TestMathAndLogic(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(21 + 21, 42)

    def test_fractions(self):
        import fractions
        f = fractions.Fraction(1, 2) + fractions.Fraction(1, 4)
        self.assertEqual(f, fractions.Fraction(3, 4))

    def test_dataclass(self):
        import dataclasses
        @dataclasses.dataclass
        class Item:
            name: str
            val: int
        item = Item("test", 10)
        self.assertEqual(item.name, "test")

if __name__ == "__main__":
    unittest.main()
