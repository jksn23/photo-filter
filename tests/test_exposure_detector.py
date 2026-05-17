import unittest

from src.exposure_detector import classify_exposure


class ExposureDetectorTests(unittest.TestCase):
    def test_classifies_underexposed(self):
        self.assertEqual(classify_exposure(30, 50, 210), "UNDEREXPOSED")

    def test_classifies_overexposed(self):
        self.assertEqual(classify_exposure(230, 50, 210), "OVEREXPOSED")

    def test_classifies_normal(self):
        self.assertEqual(classify_exposure(120, 50, 210), "NORMAL")


if __name__ == "__main__":
    unittest.main()
