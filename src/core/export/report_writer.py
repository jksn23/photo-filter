"""Detailed CSV and JSON report writer."""

from dataclasses import asdict
from pathlib import Path
from datetime import datetime
import csv
import json

from src.core.photo.photo_types import PhotoItem


REPORT_COLUMNS = [
    "filename",
    "path",
    "status",
    "cluster_id",
    "is_cluster_winner",
    "final_score",
    "technical_sharpness",
    "technical_exposure",
    "technical_contrast",
    "global_blur_penalty",
    "face_detected",
    "face_count",
    "face_sharpness",
    "face_score",
    "person_detected",
    "body_sharpness",
    "body_blur_penalty",
    "subject_score",
    "reasons",
]


def _row(item: PhotoItem) -> dict:
    score = item.score
    return {
        "filename": item.filename or item.file_name,
        "path": str(item.path),
        "status": item.status,
        "cluster_id": item.cluster_id,
        "is_cluster_winner": item.is_cluster_winner,
        "final_score": score.final_score,
        "technical_sharpness": score.technical.sharpness,
        "technical_exposure": score.technical.exposure,
        "technical_contrast": score.technical.contrast,
        "global_blur_penalty": score.technical.global_blur_penalty,
        "face_detected": score.face.face_detected,
        "face_count": score.face.face_count,
        "face_sharpness": score.face.face_sharpness,
        "face_score": score.face.face_score,
        "person_detected": score.body.person_detected,
        "body_sharpness": score.body.body_sharpness,
        "body_blur_penalty": score.body.body_blur_penalty,
        "subject_score": score.body.subject_score,
        "reasons": "; ".join(score.reasons),
    }


def write_csv_report(photo_items: list[PhotoItem], output_dir: Path) -> Path:
    """Write detailed CSV report."""
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"culling_report_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for item in photo_items:
            writer.writerow(_row(item))
    return path


def write_json_report(photo_items: list[PhotoItem], output_dir: Path) -> Path:
    """Write detailed structured JSON report."""
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"culling_audit_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    payload = {
        "summary": {
            "totalPhotos": len(photo_items),
            "selectedCount": sum(item.status == "selected" for item in photo_items),
            "reviewCount": sum(item.status == "review" for item in photo_items),
            "rejectedCount": sum(item.status == "rejected" for item in photo_items),
            "clusterCount": len({item.cluster_id for item in photo_items if item.cluster_id}),
        },
        "photos": [_row(item) for item in photo_items],
        "structuredPhotos": [asdict(item) for item in photo_items],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path

