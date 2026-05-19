"""Persistence helpers for CullaGrace V2 final user decisions."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from src.core.review.review_types import FINAL_DECISIONS, FinalDecision, ReviewDecision, ReviewItem


def _normalise_decision(value: str | None) -> FinalDecision:
    candidate = str(value or "undecided").lower()
    return candidate if candidate in FINAL_DECISIONS else "undecided"  # type: ignore[return-value]


def _decision_from_mapping(payload: dict[str, Any]) -> ReviewDecision:
    return ReviewDecision(
        photo_id=str(payload.get("photo_id") or ""),
        filename=str(payload.get("filename") or ""),
        original_path=str(payload.get("original_path") or ""),
        ai_status=str(payload.get("ai_status") or "review").lower(),  # type: ignore[arg-type]
        final_decision=_normalise_decision(payload.get("final_decision")),
        decision_source=str(payload.get("decision_source") or "manual"),
        decision_updated_at=payload.get("decision_updated_at"),
        notes=str(payload.get("notes") or ""),
    )


def load_decisions(path: Path) -> dict[str, ReviewDecision]:
    """Load persisted final decisions, returning an empty mapping when absent."""
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}

    decisions: dict[str, ReviewDecision] = {}
    for key, payload in raw.items():
        if isinstance(payload, dict):
            decision = _decision_from_mapping(payload)
            if not decision.photo_id:
                decision.photo_id = str(key)
            decisions[decision.photo_id] = decision
    return decisions


def save_decisions(decisions: dict[str, ReviewDecision], path: Path) -> None:
    """Persist final decisions as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {photo_id: asdict(decision) for photo_id, decision in sorted(decisions.items())}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def set_decision(
    decisions: dict[str, ReviewDecision],
    item: ReviewItem,
    decision: FinalDecision,
    notes: str = "",
) -> ReviewDecision:
    """Set or update the final human decision for one review item."""
    if decision not in FINAL_DECISIONS:
        raise ValueError(f"Unsupported final decision: {decision}")

    existing = decisions.get(item.photo_id)
    updated = ReviewDecision(
        photo_id=item.photo_id,
        filename=item.filename,
        original_path=str(item.original_path),
        ai_status=item.ai_status,
        final_decision=decision,
        decision_source="manual",
        decision_updated_at=datetime.now().isoformat(timespec="seconds"),
        notes=notes if notes != "" else existing.notes if existing else "",
    )
    decisions[item.photo_id] = updated
    return updated


def clear_decision(decisions: dict[str, ReviewDecision], photo_id: str) -> None:
    """Remove a persisted decision for a photo."""
    decisions.pop(photo_id, None)
