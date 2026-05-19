"""Session builders and queries for the CullaGrace V2 review workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.review.decision_store import load_decisions, save_decisions, set_decision
from src.core.review.review_types import (
    AI_STATUSES,
    FINAL_DECISIONS,
    AIStatus,
    FinalDecision,
    ReviewDecision,
    ReviewItem,
    ReviewProgress,
    ReviewSession,
)


def _normalise_ai_status(value: Any) -> AIStatus:
    status = str(value or "review").lower()
    if status in {"selected", "select", "keep"}:
        return "selected"
    if status in {"rejected", "reject"}:
        return "rejected"
    return "review"


def _normalise_decision(value: Any) -> FinalDecision:
    decision = str(value or "undecided").lower()
    return decision if decision in FINAL_DECISIONS else "undecided"  # type: ignore[return-value]


def _get_attr(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def _score_from_item(source: Any) -> Any:
    return _get_attr(source, "score") or _get_attr(source, "scores")


def _first_number(*values: Any) -> float:
    for value in values:
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _split_reasons(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def _photo_id(source: Any, filename: str, original_path: Path) -> str:
    value = _get_attr(source, "id") or _get_attr(source, "photo_id")
    if value:
        return str(value)
    return str(original_path) if str(original_path) else filename


def _review_item_from_source(source: Any) -> ReviewItem:
    score = _score_from_item(source)
    original_path = Path(str(_get_attr(source, "original_path") or _get_attr(source, "path") or ""))
    filename = str(_get_attr(source, "filename") or _get_attr(source, "file_name") or original_path.name)
    if not filename:
        filename = "unknown"

    raw_status = _get_attr(source, "status") or _get_attr(source, "output_status")
    thumbnail = _get_attr(source, "thumbnail_path")
    cluster_id = _get_attr(source, "cluster_id") or _get_attr(source, "duplicate_group_id")
    is_winner = bool(_get_attr(source, "is_cluster_winner") or _get_attr(source, "is_best_duplicate") or False)

    technical = _get_attr(score, "technical")
    face = _get_attr(score, "face")
    body = _get_attr(score, "body")
    reasons = _split_reasons(_get_attr(score, "reasons"))
    if not reasons:
        reasons = _split_reasons(_get_attr(source, "final_reason") or _get_attr(source, "notes"))

    return ReviewItem(
        photo_id=_photo_id(source, filename, original_path),
        filename=filename,
        original_path=original_path,
        ai_status=_normalise_ai_status(raw_status),
        cluster_id=str(cluster_id) if cluster_id else None,
        is_cluster_winner=is_winner,
        final_score=_first_number(_get_attr(score, "final_score"), _get_attr(source, "score_percent"), _get_attr(source, "final_score")),
        face_score=_first_number(_get_attr(face, "face_score"), _get_attr(score, "face_score"), _get_attr(source, "face_score")),
        body_sharpness=_first_number(
            _get_attr(body, "body_sharpness"),
            _get_attr(score, "body_sharpness_score"),
            _get_attr(source, "body_sharpness_score"),
        ),
        body_blur_penalty=_first_number(
            _get_attr(body, "body_blur_penalty"),
            _get_attr(score, "body_blur_penalty"),
            _get_attr(source, "body_blur_penalty"),
        ),
        thumbnail_path=Path(str(thumbnail)) if thumbnail else None,
        reasons=reasons,
    )


def build_review_items_from_photo_items(photo_items: list[Any]) -> list[ReviewItem]:
    """Map V1 culling rows or core PhotoItem instances into V2 review items."""
    return [_review_item_from_source(item) for item in photo_items]


def merge_decisions(items: list[ReviewItem], decisions: dict[str, ReviewDecision]) -> None:
    for item in items:
        decision = decisions.get(item.photo_id)
        if decision is None:
            item.final_decision = "undecided"
            continue
        item.final_decision = _normalise_decision(decision.final_decision)
        item.decision_updated_at = decision.decision_updated_at
        item.decision_source = decision.decision_source
        item.notes = decision.notes


def build_review_session(photo_items: list[Any], decisions_path: Path) -> ReviewSession:
    """Build a review session and merge persisted human decisions."""
    items = build_review_items_from_photo_items(photo_items)
    decisions = load_decisions(decisions_path)
    merge_decisions(items, decisions)
    return ReviewSession(items=items, decisions=decisions)


def get_items_by_ai_status(session: ReviewSession, ai_status: AIStatus | str) -> list[ReviewItem]:
    status = _normalise_ai_status(ai_status)
    return [item for item in session.items if item.ai_status == status]


def get_items_by_final_decision(session: ReviewSession, decision: FinalDecision | str) -> list[ReviewItem]:
    final_decision = _normalise_decision(decision)
    return [item for item in session.items if item.final_decision == final_decision]


def get_cluster_items(session: ReviewSession, cluster_id: str) -> list[ReviewItem]:
    return [item for item in session.items if item.cluster_id == cluster_id]


def get_review_progress(session: ReviewSession) -> ReviewProgress:
    progress = ReviewProgress(total=len(session.items))
    for item in session.items:
        if item.final_decision == "post":
            progress.posts += 1
        elif item.final_decision == "save":
            progress.save += 1
        elif item.final_decision == "delete":
            progress.delete += 1
        else:
            progress.undecided += 1

        if item.ai_status == "selected":
            progress.selected_total += 1
        elif item.ai_status == "review":
            progress.review_total += 1
        elif item.ai_status == "rejected":
            progress.rejected_total += 1
    return progress


def apply_decision_to_item(
    session: ReviewSession,
    item: ReviewItem,
    decision: FinalDecision,
    decisions_path: Path,
) -> ReviewDecision:
    """Apply, persist, and reflect a final decision in the active session."""
    updated = set_decision(session.decisions, item, decision, notes=item.notes)
    item.final_decision = updated.final_decision
    item.decision_updated_at = updated.decision_updated_at
    item.decision_source = updated.decision_source
    item.notes = updated.notes
    save_decisions(session.decisions, decisions_path)
    return updated


def get_next_item(session: ReviewSession, current_photo_id: str, items: list[ReviewItem] | None = None) -> ReviewItem | None:
    visible = items or session.items
    if not visible:
        return None
    for index, item in enumerate(visible):
        if item.photo_id == current_photo_id:
            return visible[(index + 1) % len(visible)]
    return visible[0]


def get_previous_item(
    session: ReviewSession,
    current_photo_id: str,
    items: list[ReviewItem] | None = None,
) -> ReviewItem | None:
    visible = items or session.items
    if not visible:
        return None
    for index, item in enumerate(visible):
        if item.photo_id == current_photo_id:
            return visible[(index - 1) % len(visible)]
    return visible[0]
