"""Final decision report writers for CullaGrace V2."""

from __future__ import annotations

from dataclasses import asdict
import csv
import json
from pathlib import Path
from typing import Any

from src.core.review.review_session import get_review_progress
from src.core.review.review_types import ReviewItem, ReviewSession


CSV_COLUMNS = [
    "photo_id",
    "filename",
    "original_path",
    "ai_status",
    "final_decision",
    "cluster_id",
    "is_cluster_winner",
    "final_score",
    "face_score",
    "body_sharpness",
    "body_blur_penalty",
    "decision_updated_at",
    "decision_source",
    "reasons",
    "notes",
]


def _reports_dir(output_dir: Path) -> Path:
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def _item_row(item: ReviewItem) -> dict[str, Any]:
    return {
        "photo_id": item.photo_id,
        "filename": item.filename,
        "original_path": str(item.original_path),
        "ai_status": item.ai_status,
        "final_decision": item.final_decision,
        "cluster_id": item.cluster_id or "",
        "is_cluster_winner": item.is_cluster_winner,
        "final_score": item.final_score,
        "face_score": item.face_score,
        "body_sharpness": item.body_sharpness,
        "body_blur_penalty": item.body_blur_penalty,
        "decision_updated_at": item.decision_updated_at or "",
        "decision_source": item.decision_source,
        "reasons": "; ".join(item.reasons),
        "notes": item.notes,
    }


def _json_item(item: ReviewItem) -> dict[str, Any]:
    payload = _item_row(item)
    payload["thumbnail_path"] = str(item.thumbnail_path) if item.thumbnail_path else None
    payload["reasons"] = item.reasons
    return payload


def _clusters(session: ReviewSession) -> list[dict[str, Any]]:
    grouped: dict[str, list[ReviewItem]] = {}
    for item in session.items:
        if item.cluster_id:
            grouped.setdefault(item.cluster_id, []).append(item)

    clusters = []
    for cluster_id, items in sorted(grouped.items()):
        winner = next((item for item in items if item.is_cluster_winner), None)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "winner": winner.photo_id if winner else None,
                "items": [
                    {
                        "photo_id": item.photo_id,
                        "filename": item.filename,
                        "ai_status": item.ai_status,
                        "final_decision": item.final_decision,
                        "final_score": item.final_score,
                        "is_cluster_winner": item.is_cluster_winner,
                    }
                    for item in items
                ],
            }
        )
    return clusters


def write_final_decision_csv(session: ReviewSession, output_dir: Path) -> Path:
    """Write final decision CSV report and return the path."""
    path = _reports_dir(output_dir) / "final_decision_report.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for item in session.items:
            writer.writerow(_item_row(item))
    return path


def write_final_decision_json(session: ReviewSession, output_dir: Path) -> Path:
    """Write final decision JSON audit report and return the path."""
    progress = get_review_progress(session)
    path = _reports_dir(output_dir) / "final_decision_audit.json"
    payload = {
        "summary": asdict(progress),
        "items": [_json_item(item) for item in session.items],
        "clusters": _clusters(session),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
