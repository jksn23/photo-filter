import unittest

from src.scorer import calculate_human_quality_score


class HumanQualityScoreTests(unittest.TestCase):
    def test_sharp_person_scores_higher_than_blurry_person(self):
        sharp_score = calculate_human_quality_score(
            face_count=1,
            global_blur_score=180,
            main_person_blur_score=160,
            avg_person_blur_score=140,
            localized_person_blur=False,
            exposure_status="NORMAL",
        )
        blurry_score = calculate_human_quality_score(
            face_count=1,
            global_blur_score=80,
            main_person_blur_score=50,
            avg_person_blur_score=70,
            localized_person_blur=True,
            exposure_status="NORMAL",
        )

        self.assertGreater(sharp_score, blurry_score)

    def test_localized_person_blur_lowers_score(self):
        clean_score = calculate_human_quality_score(
            face_count=1,
            global_blur_score=140,
            main_person_blur_score=120,
            avg_person_blur_score=120,
            localized_person_blur=False,
            exposure_status="NORMAL",
        )
        localized_blur_score = calculate_human_quality_score(
            face_count=1,
            global_blur_score=140,
            main_person_blur_score=120,
            avg_person_blur_score=120,
            localized_person_blur=True,
            exposure_status="NORMAL",
        )

        self.assertLess(localized_blur_score, clean_score)


if __name__ == "__main__":
    unittest.main()

