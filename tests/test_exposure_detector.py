import unittest

from src.exposure_detector import classify_exposure


class ExposureDetectorTests(unittest.TestCase):
    def test_classifies_underexposed(self):
        self.assertEqual(classify_exposure(49, 50, 210), "underexposed")

    def test_classifies_overexposed(self):
        self.assertEqual(classify_exposure(211, 50, 210), "overexposed")

    def test_classifies_normal_at_boundaries(self):
        self.assertEqual(classify_exposure(50, 50, 210), "normal")
        self.assertEqual(classify_exposure(210, 50, 210), "normal")


if __name__ == "__main__":
    unittest.main()

