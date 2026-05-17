import unittest

from src.duplicate_detector import map_duplicate_groups


class DuplicateDetectorTests(unittest.TestCase):
    def test_map_duplicate_groups_returns_none_for_empty_input(self):
        self.assertEqual(map_duplicate_groups([]), {})


if __name__ == "__main__":
    unittest.main()
