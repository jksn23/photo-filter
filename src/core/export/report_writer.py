"""Detailed CSV and JSON audit report writer."""

from datetime import datetime
from pathlib import Path
import csv
import json

from src.core.photo.photo_types import PhotoCluster, PhotoItem


REPORT_COLUMNS = [
    "filename",
    "path",
    "status",
    "cluster_id",
    "is_cluster_winner",
    "selected_photo_id",
    "final_score",
    "score_percent",
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
    "duplicate_penalty",
    "mode",
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
        "selected_photo_id": item.metadata_dict.get("selected_photo_id"),
        "final_score": score.final_score,
        "score_percent": round(score.final_score * 100.0, 2),
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
        "duplicate_penalty": score.duplicate_penalty,
        "mode": item.metadata_dict.get("mode"),
        "reasons": "; ".join(score.reasons),
    }


def _score_breakdown(item: PhotoItem) -> dict:
    score = item.score
    return {
        "technical": {
            "sharpness": score.technical.sharpness,
            "exposure": score.technical.exposure,
            "contrast": score.technical.contrast,
            "globalBlurPenalty": score.technical.global_blur_penalty,
        },
        "face": {
            "faceDetected": score.face.face_detected,
            "faceCount": score.face.face_count,
            "faceSharpness": score.face.face_sharpness,
            "faceScore": score.face.face_score,
        },
        "body": {
            "personDetected": score.body.person_detected,
            "bodySharpness": score.body.body_sharpness,
            "bodyBlurPenalty": score.body.body_blur_penalty,
            "subjectScore": score.body.subject_score,
        },
        "duplicatePenalty": score.duplicate_penalty,
        "finalScore": score.final_score,
        "scorePercent": round(score.final_score * 100.0, 2),
    }


def _photo_record(item: PhotoItem) -> dict:
    return {
        **_row(item),
        "outputPath": item.output_path,
        "thumbnailPath": item.thumbnail_path,
        "clusterWinnerFilename": item.metadata_dict.get("cluster_winner_filename"),
        "scoreGapFromWinner": item.metadata_dict.get("score_gap_from_winner"),
        "scoreBreakdown": _score_breakdown(item),
        "reasonsList": list(item.score.reasons),
    }


def _cluster_records(photo_items: list[PhotoItem], clusters: list[PhotoCluster] | None) -> list[dict]:
    if clusters is None:
        cluster_ids = sorted({item.cluster_id for item in photo_items if item.cluster_id})
        clusters = [
            PhotoCluster(
                id=cluster_id,
                photo_ids=[item.id for item in photo_items if item.cluster_id == cluster_id],
                photos=[item for item in photo_items if item.cluster_id == cluster_id],
                selected_photo_id=next((item.id for item in photo_items if item.cluster_id == cluster_id and item.is_cluster_winner), None),
            )
            for cluster_id in cluster_ids
        ]

    records: list[dict] = []
    for cluster in clusters:
        photos = sorted(cluster.photos, key=lambda item: (not item.is_cluster_winner, -item.score.final_score))
        winner = next((item for item in photos if item.id == cluster.selected_photo_id), None)
        records.append(
            {
                "clusterId": cluster.id,
                "selectedPhotoId": cluster.selected_photo_id,
                "winner": _photo_record(winner) if winner else None,
                "photos": [_photo_record(item) for item in photos],
            }
        )
    return records


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


def write_json_report(
    photo_items: list[PhotoItem],
    output_dir: Path,
    clusters: list[PhotoCluster] | None = None,
    mode: str | None = None,
) -> Path:
    """Write detailed structured JSON report."""
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"culling_audit_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    cluster_records = _cluster_records(photo_items, clusters)
    payload = {
        "summary": {
            "totalPhotos": len(photo_items),
            "selectedCount": sum(item.status == "selected" for item in photo_items),
            "reviewCount": sum(item.status == "review" for item in photo_items),
            "rejectedCount": sum(item.status == "rejected" for item in photo_items),
            "clusterCount": len(cluster_records),
            "averageFinalScore": round(
                sum(item.score.final_score for item in photo_items) / len(photo_items), 4
            )
            if photo_items
            else 0.0,
            "mode": mode,
        },
        "photos": [_photo_record(item) for item in photo_items],
        "clusters": cluster_records,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path
