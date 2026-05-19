from pathlib import Path

from src.core.review.review_types import ReviewDecision, ReviewItem, ReviewProgress, ReviewSession


def test_review_types_defaults_keep_final_decision_separate_from_ai_status() -> None:
    item = ReviewItem(
        photo_id="photo-1",
        filename="IMG_0001.jpg",
        original_path=Path("IMG_0001.jpg"),
        ai_status="selected",
    )
    session = ReviewSession(items=[item])
    decision = ReviewDecision(
        photo_id=item.photo_id,
        filename=item.filename,
        original_path=str(item.original_path),
        ai_status=item.ai_status,
    )
    progress = ReviewProgress(total=1, selected_total=1, undecided=1)

    assert item.ai_status == "selected"
    assert item.final_decision == "undecided"
    assert decision.final_decision == "undecided"
    assert session.items == [item]
    assert progress.selected_total == 1
