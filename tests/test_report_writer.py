from pathlib import Path
import json

from src.core.export.report_writer import write_csv_report, write_json_report
from src.core.photo.photo_types import BodyScore, FaceScore, PhotoCluster, PhotoItem, PhotoScore, TechnicalScore


def test_report_writer_outputs_csv_and_json(tmp_path):
    item = PhotoItem(id="a", path=Path("a.jpg"), file_name="a.jpg", cluster_id="CL001", status="selected")
    item.is_cluster_winner = True
    item.metadata_dict.update({"selected_photo_id": "a", "mode": "balanced"})
    item.score = PhotoScore(
        technical=TechnicalScore(sharpness=0.8, exposure=0.8, contrast=0.6, global_blur_penalty=0.1),
        face=FaceScore(face_detected=True, face_count=1, face_sharpness=0.8, face_score=0.8),
        body=BodyScore(person_detected=True, body_sharpness=0.7, body_blur_penalty=0.2, subject_score=0.63),
        final_score=0.7,
        reasons=["Selected as best image in similar cluster"],
    )
    cluster = PhotoCluster(id="CL001", photo_ids=["a"], photos=[item], selected_photo_id="a")

    csv_path = write_csv_report([item], tmp_path)
    json_path = write_json_report([item], tmp_path, clusters=[cluster], mode="balanced")

    assert csv_path.exists()
    assert json_path.exists()
    csv_text = csv_path.read_text(encoding="utf-8-sig")
    assert "body_blur_penalty" in csv_text
    assert "selected_photo_id" in csv_text
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["clusters"][0]["selectedPhotoId"] == "a"
    assert payload["photos"][0]["scoreBreakdown"]["body"]["bodyBlurPenalty"] == 0.2
