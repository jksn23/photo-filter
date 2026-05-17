import unittest

from src.blur_detector import is_blurry


class BlurDetectorTests(unittest.TestCase):
    def test_is_blurry_when_score_below_threshold(self):
        self.assertTrue(is_blurry(99.0, 100.0))

    def test_is_not_blurry_when_score_equals_threshold(self):
        self.assertFalse(is_blurry(100.0, 100.0))


if __name__ == "__main__":
    unittest.main()

