from pathlib import Path

from src.core.photo.photo_types import BodyScore, FaceScore, PhotoItem, PhotoScore, TechnicalScore
from src.culling_pipeline import _core_item_to_result


def test_streamlit_result_adapter_exposes_score_breakdown_and_reasons():
    item = PhotoItem(id="a", path=Path("a.jpg"), file_name="a.jpg", cluster_id="CL001", status="review")
    item.score = PhotoScore(
        technical=TechnicalScore(sharpness=0.7, exposure=0.6, contrast=0.5, global_blur_penalty=0.2),
        face=FaceScore(face_detected=True, face_count=2, face_sharpness=0.75, face_score=0.8),
        body=BodyScore(person_detected=True, body_sharpness=0.35, body_blur_penalty=0.65, subject_score=0.2),
        final_score=0.62,
        reasons=["Close candidate kept for manual review.", "Body/subject blur detected."],
    )
    item.metadata_dict.update(
        {
            "mode": "balanced",
            "selected_photo_id": "b",
            "cluster_winner_filename": "b.jpg",
            "score_gap_from_winner": 0.07,
        }
    )

    result = _core_item_to_result(item)

    assert result.output_status == "REVIEW"
    assert result.face_sharpness_score == 0.75
    assert result.subject_score == 0.2
    assert result.cluster_winner_filename == "b.jpg"
    assert "Body/subject blur detected" in result.final_reason
