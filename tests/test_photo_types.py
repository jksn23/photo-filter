from pathlib import Path

from src.core.photo.photo_types import BodyScore, FaceScore, PhotoItem, PhotoScore, TechnicalScore


def test_photo_types_support_required_models():
    item = PhotoItem(id="1", path=Path("a.jpg"), file_name="a.jpg")
    item.score = PhotoScore(
        technical=TechnicalScore(sharpness=0.8, exposure=0.7, contrast=0.6, global_blur_penalty=0.1),
        face=FaceScore(face_detected=True, face_count=1, face_sharpness=0.8, face_score=0.75),
        body=BodyScore(person_detected=True, body_sharpness=0.7, body_blur_penalty=0.2, subject_score=0.63),
        final_score=0.72,
    )

    assert item.filename == "a.jpg"
    assert item.status == "unprocessed"
    assert item.score.technical.sharpness == 0.8

