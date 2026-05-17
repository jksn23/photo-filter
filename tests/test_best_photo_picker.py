import unittest

from src.core.culling.best_photo_picker import pick_best_photos_for_cluster
from src.core.culling.best_photo_picker import pick_best_photos
from src.core.photo.photo_types import BodyScore, FaceScore, PhotoCluster, PhotoItem, PhotoScore, TechnicalScore
from src.core.scoring.final_score import compute_final_score


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


def test_body_blur_can_change_cluster_winner_when_face_scores_are_close():
    technical = TechnicalScore(sharpness=0.8, exposure=0.8, contrast=0.7, global_blur_penalty=0.1)
    blurry_body = BodyScore(person_detected=True, body_sharpness=0.30, body_blur_penalty=0.70)
    clean_body = BodyScore(person_detected=True, body_sharpness=0.80, body_blur_penalty=0.20)
    photo_a = PhotoItem(id="a", path="a.jpg", file_name="a.jpg")
    photo_b = PhotoItem(id="b", path="b.jpg", file_name="b.jpg")
    photo_a.score = PhotoScore(
        technical=technical,
        face=FaceScore(face_detected=True, face_count=1, face_sharpness=0.90, face_score=0.90),
        body=blurry_body,
        final_score=compute_final_score(technical, FaceScore(True, 1, 0.90, 0.90), blurry_body, mode="balanced"),
    )
    photo_b.score = PhotoScore(
        technical=technical,
        face=FaceScore(face_detected=True, face_count=1, face_sharpness=0.86, face_score=0.86),
        body=clean_body,
        final_score=compute_final_score(technical, FaceScore(True, 1, 0.86, 0.86), clean_body, mode="balanced"),
    )
    photo_a.scores = photo_a.score
    photo_b.scores = photo_b.score
    cluster = PhotoCluster(id="CL001", photo_ids=["a", "b"], photos=[photo_a, photo_b])

    pick_best_photos([cluster], mode="balanced")

    assert cluster.selected_photo_id == "b"
    assert photo_b.status == "selected"
    assert photo_a.status in {"review", "rejected"}
