from pathlib import Path
import json

from src.core.photo.photo_types import PhotoItem, PhotoScore
from src.core.review.decision_exporter import export_final_decisions
from src.core.review.review_report_writer import write_final_decision_csv, write_final_decision_json
from src.core.review.review_session import apply_decision_to_item, build_review_session


def _photo(path: Path, status: str) -> PhotoItem:
    path.write_text(path.name, encoding="utf-8")
    return PhotoItem(
        id=str(path),
        path=path,
        file_name=path.name,
        status=status,  # type: ignore[arg-type]
        score=PhotoScore(final_score=0.75, reasons=[f"{status} recommendation"]),
    )


def test_v2_review_workflow_end_to_end(tmp_path: Path) -> None:
    photos = [
        _photo(tmp_path / "IMG_0001.jpg", "selected"),
        _photo(tmp_path / "IMG_0002.jpg", "review"),
        _photo(tmp_path / "IMG_0003.jpg", "rejected"),
        _photo(tmp_path / "IMG_0004.jpg", "review"),
    ]
    output_dir = tmp_path / "output"
    decisions_path = output_dir / "reports" / "final_decisions.json"
    session = build_review_session(photos, decisions_path)

    apply_decision_to_item(session, session.items[0], "post", decisions_path)
    apply_decision_to_item(session, session.items[1], "save", decisions_path)
    apply_decision_to_item(session, session.items[2], "delete", decisions_path)

    counts = export_final_decisions(session, output_dir)
    csv_path = write_final_decision_csv(session, output_dir)
    json_path = write_final_decision_json(session, output_dir)
    audit = json.loads(json_path.read_text(encoding="utf-8"))

    assert counts == {"post": 1, "save": 1, "delete": 1, "undecided": 1, "missing": 0}
    assert (output_dir / "02_FINAL_DECISION" / "Posts" / "IMG_0001.jpg").exists()
    assert (output_dir / "02_FINAL_DECISION" / "Save" / "IMG_0002.jpg").exists()
    assert (output_dir / "02_FINAL_DECISION" / "Delete" / "IMG_0003.jpg").exists()
    assert not (output_dir / "02_FINAL_DECISION" / "Undecided").exists()
    assert decisions_path.exists()
    assert csv_path.exists()
    assert audit["summary"]["posts"] == 1
    assert audit["summary"]["save"] == 1
    assert audit["summary"]["delete"] == 1
    assert audit["summary"]["undecided"] == 1
    assert photos[0].path.exists()
