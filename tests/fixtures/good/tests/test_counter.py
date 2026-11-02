import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from models import Counter

class TestCounter(unittest.TestCase):
    def test_increment(self):
        c = Counter()
        self.assertEqual(c.get_count(), 0)
        c.increment()
        self.assertEqual(c.get_count(), 1)

if __name__ == "__main__":
    unittest.main()
