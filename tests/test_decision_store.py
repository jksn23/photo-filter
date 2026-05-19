from pathlib import Path

from src.core.review.decision_store import clear_decision, load_decisions, save_decisions, set_decision
from src.core.review.review_types import ReviewItem


def _item(path: Path) -> ReviewItem:
    return ReviewItem(
        photo_id="photo-1",
        filename=path.name,
        original_path=path,
        ai_status="review",
    )


def test_load_missing_decision_file_returns_empty_dict(tmp_path: Path) -> None:
    assert load_decisions(tmp_path / "reports" / "final_decisions.json") == {}


def test_save_reload_set_and_clear_decisions(tmp_path: Path) -> None:
    decisions_path = tmp_path / "reports" / "final_decisions.json"
    item = _item(tmp_path / "IMG_0001.jpg")
    decisions = {}

    decision = set_decision(decisions, item, "post")
    assert decision.final_decision == "post"
    assert decision.decision_updated_at

    save_decisions(decisions, decisions_path)
    reloaded = load_decisions(decisions_path)
    assert reloaded[item.photo_id].filename == "IMG_0001.jpg"
    assert reloaded[item.photo_id].final_decision == "post"

    clear_decision(reloaded, item.photo_id)
    assert item.photo_id not in reloaded
