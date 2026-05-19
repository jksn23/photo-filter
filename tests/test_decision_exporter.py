from pathlib import Path

from src.core.review.decision_exporter import export_final_decisions
from src.core.review.review_types import ReviewItem, ReviewSession


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_export_final_decisions_copies_without_moving_and_handles_collisions(tmp_path: Path) -> None:
    first = _write(tmp_path / "a" / "IMG_0001.jpg", "first")
    second = _write(tmp_path / "b" / "IMG_0001.jpg", "second")
    source_delete = _write(tmp_path / "IMG_0003.jpg", "delete")
    missing = tmp_path / "missing.jpg"
    output_dir = tmp_path / "output"
    session = ReviewSession(
        items=[
            ReviewItem("1", first.name, first, "selected", final_decision="post"),
            ReviewItem("2", second.name, second, "review", final_decision="post"),
            ReviewItem("3", source_delete.name, source_delete, "rejected", final_decision="delete"),
            ReviewItem("4", "missing.jpg", missing, "review", final_decision="save"),
            ReviewItem("5", "IMG_0005.jpg", tmp_path / "IMG_0005.jpg", "review"),
        ]
    )

    counts = export_final_decisions(session, output_dir)

    assert counts == {"post": 2, "save": 1, "delete": 1, "undecided": 1, "missing": 1}
    assert first.exists()
    assert second.exists()
    assert source_delete.exists()
    assert (output_dir / "02_FINAL_DECISION" / "Posts" / "IMG_0001.jpg").exists()
    assert (output_dir / "02_FINAL_DECISION" / "Posts" / "IMG_0001_1.jpg").exists()
    assert (output_dir / "02_FINAL_DECISION" / "Delete" / "IMG_0003.jpg").exists()
    assert not (output_dir / "02_FINAL_DECISION" / "Undecided").exists()
