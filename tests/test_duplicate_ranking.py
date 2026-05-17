import unittest
from pathlib import Path

from src.culling_pipeline import _finalize_analyses, rank_duplicate_group
from src.scorer import PhotoAnalysis


class DuplicateRankingTests(unittest.TestCase):
    def test_cleaner_human_subject_ranks_first(self):
        blurry_human = PhotoAnalysis(
            path=Path("a.jpg"),
            filename="a.jpg",
            blur_score=160,
            is_blurry=False,
            brightness=120,
            exposure_status="NORMAL",
            face_count=2,
            duplicate_group="G001",
            is_best_in_duplicate_group=False,
            final_score=100,
            status="SELECTED",
            person_count=1,
            main_person_blur_score=70,
            avg_person_blur_score=80,
            min_person_blur_score=60,
            localized_person_blur=True,
            human_quality_score=80,
        )
        clean_human = PhotoAnalysis(
            path=Path("b.jpg"),
            filename="b.jpg",
            blur_score=150,
            is_blurry=False,
            brightness=120,
            exposure_status="NORMAL",
            face_count=2,
            duplicate_group="G001",
            is_best_in_duplicate_group=False,
            final_score=100,
            status="SELECTED",
            person_count=1,
            main_person_blur_score=150,
            avg_person_blur_score=140,
            min_person_blur_score=130,
            localized_person_blur=False,
            human_quality_score=130,
        )

        ranked = rank_duplicate_group([blurry_human, clean_human])

        self.assertEqual(ranked[0].filename, "b.jpg")
        self.assertEqual(ranked[1].filename, "a.jpg")

    def test_rank_two_cannot_remain_selected(self):
        rows = [
            {
                "path": Path("a.jpg"),
                "filename": "a.jpg",
                "blur_score": 160,
                "is_blurry": False,
                "brightness": 120,
                "exposure_status": "NORMAL",
                "face_count": 2,
                "duplicate_group": "G001",
                "person_count": 1,
                "main_person_blur_score": 70,
                "avg_person_blur_score": 80,
                "min_person_blur_score": 60,
                "localized_person_blur": True,
                "human_quality_score": 80,
                "person_detection_reason": "test",
            },
            {
                "path": Path("b.jpg"),
                "filename": "b.jpg",
                "blur_score": 150,
                "is_blurry": False,
                "brightness": 120,
                "exposure_status": "NORMAL",
                "face_count": 2,
                "duplicate_group": "G001",
                "person_count": 1,
                "main_person_blur_score": 150,
                "avg_person_blur_score": 140,
                "min_person_blur_score": 130,
                "localized_person_blur": False,
                "human_quality_score": 130,
                "person_detection_reason": "test",
            },
        ]

        finalized = _finalize_analyses(rows, selected_min=80, review_min=50, use_human_aware_detection=True)
        by_name = {analysis.filename: analysis for analysis in finalized}

        self.assertEqual(by_name["b.jpg"].duplicate_quality_rank, 1)
        self.assertEqual(by_name["a.jpg"].duplicate_quality_rank, 2)
        self.assertNotEqual(by_name["a.jpg"].status, "SELECTED")


if __name__ == "__main__":
    unittest.main()

