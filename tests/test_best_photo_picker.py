import unittest

from src.core.culling.best_photo_picker import pick_best_photos_for_cluster
from src.core.photo.photo_types import PhotoCluster, PhotoItem, PhotoScore


def _item(photo_id: str, score: float) -> PhotoItem:
    return PhotoItem(
        id=photo_id,
        path=f"{photo_id}.jpg",
        file_name=f"{photo_id}.jpg",
        scores=PhotoScore(
            technical_score=score,
            sharpness_score=score,
            exposure_score=score,
            contrast_score=score,
            blur_penalty=0.0,
            final_score=score,
        ),
    )


class BestPhotoPickerTests(unittest.TestCase):
    def test_highest_score_is_selected(self):
        items = {_id: _item(_id, score) for _id, score in [("a", 0.6), ("b", 0.9), ("c", 0.3)]}
        cluster = PhotoCluster(id="CL001", photo_ids=["a", "b", "c"])

        result = pick_best_photos_for_cluster(cluster, items, mode="aggressive")

        self.assertEqual(result.selected_photo_id, "b")
        self.assertEqual(items["b"].status, "selected")
        self.assertEqual(items["a"].status, "rejected")

    def test_conservative_keeps_close_candidates(self):
        items = {_id: _item(_id, score) for _id, score in [("a", 0.90), ("b", 0.86), ("c", 0.65)]}
        cluster = PhotoCluster(id="CL001", photo_ids=["a", "b", "c"])

        pick_best_photos_for_cluster(cluster, items, mode="conservative", conservative_keep_delta=0.08)

        self.assertEqual(items["a"].status, "selected")
        self.assertEqual(items["b"].status, "selected")
        self.assertEqual(items["c"].status, "rejected")


if __name__ == "__main__":
    unittest.main()

