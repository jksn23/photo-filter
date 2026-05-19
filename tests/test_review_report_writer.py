from pathlib import Path
import csv
import json

from src.core.review.review_report_writer import write_final_decision_csv, write_final_decision_json
from src.core.review.review_types import ReviewItem, ReviewSession


def test_review_report_writer_outputs_required_csv_and_json(tmp_path: Path) -> None:
    session = ReviewSession(
        items=[
            ReviewItem(
                photo_id="1",
                filename="IMG_0001.jpg",
                original_path=tmp_path / "IMG_0001.jpg",
                ai_status="selected",
                final_decision="post",
                cluster_id="cluster-1",
                is_cluster_winner=True,
                final_score=0.9,
                face_score=0.8,
                body_sharpness=0.7,
                body_blur_penalty=0.1,
                reasons=["Selected as cluster winner"],
            ),
            ReviewItem(
                photo_id="2",
                filename="IMG_0002.jpg",
                original_path=tmp_path / "IMG_0002.jpg",
                ai_status="review",
                final_decision="undecided",
                cluster_id="cluster-1",
                final_score=0.78,
            ),
        ]
    )

    csv_path = write_final_decision_csv(session, tmp_path)
    json_path = write_final_decision_json(session, tmp_path)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert rows[0]["photo_id"] == "1"
    assert rows[0]["final_decision"] == "post"
    assert "body_blur_penalty" in rows[0]
    assert payload["summary"]["posts"] == 1
    assert payload["summary"]["undecided"] == 1
    assert payload["items"][0]["final_decision"] == "post"
    assert payload["clusters"][0]["winner"] == "1"
