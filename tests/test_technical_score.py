import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.core.scoring.technical_score import calculate_technical_score


class TechnicalScoreTests(unittest.TestCase):
    def test_sharp_image_scores_higher_than_blur_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            sharp_path = Path(tmp) / "sharp.jpg"
            blur_path = Path(tmp) / "blur.jpg"
            image = np.zeros((120, 120, 3), dtype=np.uint8)
            for idx in range(0, 120, 6):
                cv2.line(image, (idx, 0), (idx, 119), (255, 255, 255), 1)
            cv2.imwrite(str(sharp_path), image)
            cv2.imwrite(str(blur_path), cv2.GaussianBlur(image, (31, 31), 0))

            sharp = calculate_technical_score(sharp_path)
            blur = calculate_technical_score(blur_path)

            self.assertGreater(sharp["sharpness_score"], blur["sharpness_score"])
            self.assertLess(sharp["blur_penalty"], blur["blur_penalty"])

    def test_underexposed_image_gets_exposure_penalty(self):
        with tempfile.TemporaryDirectory() as tmp:
            normal_path = Path(tmp) / "normal.jpg"
            dark_path = Path(tmp) / "dark.jpg"
            cv2.imwrite(str(normal_path), np.full((80, 80, 3), 128, dtype=np.uint8))
            cv2.imwrite(str(dark_path), np.full((80, 80, 3), 5, dtype=np.uint8))

            normal = calculate_technical_score(normal_path)
            dark = calculate_technical_score(dark_path)

            self.assertGreater(normal["exposure_score"], dark["exposure_score"])


if __name__ == "__main__":
    unittest.main()

