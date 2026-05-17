import unittest

from src.scorer import calculate_score, classify_status


class ScorerTests(unittest.TestCase):
    def test_score_rewards_faces_and_best_duplicate(self):
        score = calculate_score(
            is_blur=False,
            exposure_status="normal",
            face_count=2,
            is_duplicate_candidate=True,
            best_in_duplicate_group=True,
        )
        self.assertEqual(score, 125.0)

    def test_score_penalizes_blur_exposure_no_face_and_duplicate(self):
        score = calculate_score(
            is_blur=True,
            exposure_status="underexposed",
            face_count=0,
            is_duplicate_candidate=True,
            best_in_duplicate_group=False,
        )
        self.assertEqual(score, -5.0)

    def test_classify_status(self):
        self.assertEqual(classify_status(80, 80, 50), "SELECTED")
        self.assertEqual(classify_status(50, 80, 50), "REVIEW")
        self.assertEqual(classify_status(49, 80, 50), "REJECTED")


if __name__ == "__main__":
    unittest.main()

