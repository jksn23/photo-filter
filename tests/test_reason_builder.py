from src.core.photo.photo_types import BodyScore, FaceScore, PhotoCluster, PhotoItem, PhotoScore, TechnicalScore
from src.core.scoring.reason_builder import build_reasons


def _photo(status="selected", winner=True):
    item = PhotoItem(id="a", path="a.jpg", file_name="a.jpg", status=status, is_cluster_winner=winner)
    item.score = PhotoScore(
        technical=TechnicalScore(sharpness=0.8, exposure=0.8, contrast=0.6, global_blur_penalty=0.1),
        face=FaceScore(face_detected=True, face_count=1, face_sharpness=0.8, face_score=0.8),
        body=BodyScore(person_detected=True, body_sharpness=0.2, body_blur_penalty=0.8, subject_score=0.0),
        final_score=0.7,
    )
    return item


def test_selected_cluster_winner_receives_selected_reason():
    item = _photo()
    cluster = PhotoCluster(id="CL001", photo_ids=["a", "b"], selected_photo_id="a")

    reasons = build_reasons(item, cluster)

    assert "Selected as best image in similar cluster" in reasons


def test_body_blur_reason_is_added():
    item = _photo()

    reasons = build_reasons(item, None)

    assert "Body/subject blur detected" in reasons

