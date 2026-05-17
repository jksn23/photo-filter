import unittest

import cv2
import numpy as np

from src.person_blur_analyzer import calculate_blur_for_box, detect_localized_person_blur


class PersonBlurAnalyzerTests(unittest.TestCase):
    def test_calculate_blur_for_box_handles_valid_and_invalid_boxes(self):
        image = np.zeros((80, 80, 3), dtype=np.uint8)
        cv2.rectangle(image, (10, 10), (70, 70), (255, 255, 255), 2)
        blurred = cv2.GaussianBlur(image, (21, 21), 0)

        sharp_score = calculate_blur_for_box(image, (0, 0, 80, 80))
        blurred_score = calculate_blur_for_box(blurred, (0, 0, 80, 80))
        invalid_score = calculate_blur_for_box(image, (200, 200, 10, 10))

        self.assertGreater(sharp_score, blurred_score)
        self.assertEqual(invalid_score, 0.0)

    def test_detect_localized_person_blur(self):
        sharp = np.zeros((90, 90, 3), dtype=np.uint8)
        for index in range(0, 90, 6):
            cv2.line(sharp, (index, 0), (index, 89), (255, 255, 255), 1)
            cv2.line(sharp, (0, index), (89, index), (255, 255, 255), 1)

        blurred = cv2.GaussianBlur(sharp, (31, 31), 0)

        self.assertFalse(
            detect_localized_person_blur(
                sharp,
                (0, 0, 90, 90),
                patch_blur_threshold=1.0,
                min_blurry_patch_ratio=0.25,
            )
        )
        self.assertTrue(
            detect_localized_person_blur(
                blurred,
                (0, 0, 90, 90),
                patch_blur_threshold=75.0,
                min_blurry_patch_ratio=0.25,
            )
        )


if __name__ == "__main__":
    unittest.main()

