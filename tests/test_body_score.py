import unittest

from src.core.scoring.final_score import calculate_final_score


class BodyScoreTests(unittest.TestCase):
    def test_body_blur_penalty_lowers_final_score(self):
        clean = calculate_final_score(
            technical_score=0.8,
            face_score=0.8,
            body_sharpness_score=0.8,
            body_blur_penalty=0.0,
            aesthetic_score=0.5,
        )
        blurry = calculate_final_score(
            technical_score=0.8,
            face_score=0.8,
            body_sharpness_score=0.3,
            body_blur_penalty=0.5,
            aesthetic_score=0.5,
        )

        self.assertLess(blurry, clean)


if __name__ == "__main__":
    unittest.main()

