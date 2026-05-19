from pathlib import Path

from src.core.photo.photo_types import BodyScore, FaceScore, PhotoItem, PhotoScore, TechnicalScore
from src.core.review.decision_store import save_decisions, set_decision
from src.core.review.review_session import (
    apply_decision_to_item,
    build_review_session,
    get_cluster_items,
    get_items_by_ai_status,
    get_items_by_final_decision,
    get_review_progress,
)
from src.core.review.review_types import ReviewItem


def _photo(path: Path, status: str, cluster_id: str | None = None, winner: bool = False) -> PhotoItem:
    return PhotoItem(
        id=str(path),
        path=path,
        file_name=path.name,
        status=status,  # type: ignore[arg-type]
        cluster_id=cluster_id,
        is_cluster_winner=winner,
        score=PhotoScore(
            technical=TechnicalScore(sharpness=0.8, exposure=0.7, contrast=0.6),
            face=FaceScore(face_detected=True, face_count=1, face_score=0.75),
            body=BodyScore(person_detected=True, body_sharpness=0.7, body_blur_penalty=0.2),
            reasons=["Good sharpness"],
            final_score=0.82,
        ),
    )


def test_build_review_session_merges_persisted_decision_and_queries(tmp_path: Path) -> None:
    photo_1 = _photo(tmp_path / "IMG_0001.jpg", "selected", "cluster-1", True)
    photo_2 = _photo(tmp_path / "IMG_0002.jpg", "review", "cluster-1")
    photo_3 = _photo(tmp_path / "IMG_0003.jpg", "rejected")
    decisions_path = tmp_path / "reports" / "final_decisions.json"

    decisions = {}
    set_decision(
        decisions,
        ReviewItem(
            photo_id=photo_1.id,
            filename=photo_1.file_name,
            original_path=Path(photo_1.path),
            ai_status="selected",
        ),
        "save",
    )
    save_decisions(decisions, decisions_path)

    session = build_review_session([photo_1, photo_2, photo_3], decisions_path)
    progress = get_review_progress(session)

    assert session.items[0].final_decision == "save"
    assert get_items_by_ai_status(session, "selected")[0].filename == "IMG_0001.jpg"
    assert get_items_by_final_decision(session, "save")[0].photo_id == photo_1.id
    assert len(get_cluster_items(session, "cluster-1")) == 2
    assert progress.total == 3
    assert progress.save == 1
    assert progress.undecided == 2
    assert progress.selected_total == 1
    assert progress.review_total == 1
    assert progress.rejected_total == 1


def test_apply_decision_to_item_persists_change(tmp_path: Path) -> None:
    photo = _photo(tmp_path / "IMG_0001.jpg", "review")
    decisions_path = tmp_path / "reports" / "final_decisions.json"
    session = build_review_session([photo], decisions_path)

    updated = apply_decision_to_item(session, session.items[0], "delete", decisions_path)
    reloaded = build_review_session([photo], decisions_path)

    assert updated.final_decision == "delete"
    assert reloaded.items[0].final_decision == "delete"
