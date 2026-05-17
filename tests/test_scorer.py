import unittest

from src.scorer import calculate_score, classify_status


class ScorerTests(unittest.TestCase):
    def test_score_with_face_is_higher_than_no_face(self):
        with_face = calculate_score(
            is_blurry=False,
            exposure_status="NORMAL",
            face_count=1,
            is_duplicate_non_best=False,
            is_best_in_duplicate_group=False,
        )
        without_face = calculate_score(
            is_blurry=False,
            exposure_status="NORMAL",
            face_count=0,
            is_duplicate_non_best=False,
            is_best_in_duplicate_group=False,
        )
        self.assertGreater(with_face, without_face)

    def test_blur_lowers_score(self):
        sharp = calculate_score(
            is_blurry=False,
            exposure_status="NORMAL",
            face_count=1,
            is_duplicate_non_best=False,
            is_best_in_duplicate_group=False,
        )
        blurry = calculate_score(
            is_blurry=True,
            exposure_status="NORMAL",
            face_count=1,
            is_duplicate_non_best=False,
            is_best_in_duplicate_group=False,
        )
        self.assertLess(blurry, sharp)

    def test_classify_status(self):
        self.assertEqual(classify_status(90), "SELECTED")
        self.assertEqual(classify_status(60), "REVIEW")
        self.assertEqual(classify_status(30), "REJECTED")


if __name__ == "__main__":
    unittest.main()
