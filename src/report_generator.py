"""CSV reporting and summary generation."""

from pathlib import Path
from datetime import datetime
from dataclasses import asdict
import json

import pandas as pd

from src.models import PhotoAnalysisResult
from src.exposure_detector import OVEREXPOSED, UNDEREXPOSED
from src.scorer import PhotoAnalysis


CSV_COLUMNS = [
    "filename",
    "original_path",
    "output_status",
    "output_path",
    "blur_score",
    "is_blur",
    "brightness_score",
    "exposure_status",
    "face_count",
    "has_face",
    "duplicate_group_id",
    "is_duplicate_candidate",
    "best_in_duplicate_group",
    "final_score",
    "notes",
    "error",
    "person_count",
    "main_person_blur_score",
    "avg_person_blur_score",
    "min_person_blur_score",
    "localized_person_blur",
    "human_quality_score",
    "duplicate_quality_rank",
    "is_best_duplicate",
    "final_reason",
    "thumbnail_path",
    "technical_score",
    "sharpness_score",
    "exposure_score",
    "contrast_score",
    "blur_penalty",
    "face_score",
    "body_sharpness_score",
    "body_blur_penalty",
    "aesthetic_score",
    "culling_mode",
]

ANALYSIS_CSV_COLUMNS = [
    "filename",
    "path",
    "blur_score",
    "is_blurry",
    "brightness",
    "exposure_status",
    "face_count",
    "duplicate_group",
    "is_best_in_duplicate_group",
    "final_score",
    "status",
    "person_count",
    "main_person_blur_score",
    "avg_person_blur_score",
    "min_person_blur_score",
    "localized_person_blur",
    "human_quality_score",
    "duplicate_quality_rank",
    "is_best_duplicate",
    "final_reason",
    "thumbnail_path",
    "technical_score",
    "sharpness_score",
    "exposure_score",
    "contrast_score",
    "blur_penalty",
    "face_score",
    "body_sharpness_score",
    "body_blur_penalty",
    "aesthetic_score",
    "culling_mode",
]


def write_csv_report(analyses: list[PhotoAnalysis], report_dir: Path) -> Path:
    """Write a timestamped CSV report for MVP PhotoAnalysis rows."""
    report_folder = Path(report_dir)
    report_folder.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = report_folder / f"culling_report_{timestamp}.csv"
    rows = []
    for analysis in analyses:
        row = asdict(analysis)
        row["path"] = str(row["path"])
        rows.append(row)
    pd.DataFrame(rows, columns=ANALYSIS_CSV_COLUMNS).to_csv(
        report_path,
        index=False,
        encoding="utf-8-sig",
    )
    return report_path


def build_summary(analyses: list[PhotoAnalysis]) -> dict:
    """Build a summary dictionary for MVP PhotoAnalysis rows."""
    duplicate_groups = {
        analysis.duplicate_group
        for analysis in analyses
        if analysis.duplicate_group is not None
    }
    return {
        "total_photos": len(analyses),
        "selected_count": sum(analysis.status == "SELECTED" for analysis in analyses),
        "review_count": sum(analysis.status == "REVIEW" for analysis in analyses),
        "rejected_count": sum(analysis.status == "REJECTED" for analysis in analyses),
        "blurry_count": sum(analysis.is_blurry for analysis in analyses),
        "underexposed_count": sum(analysis.exposure_status == UNDEREXPOSED for analysis in analyses),
        "overexposed_count": sum(analysis.exposure_status == OVEREXPOSED for analysis in analyses),
        "duplicate_groups_count": len(duplicate_groups),
    }


def results_to_dataframe(results: list[PhotoAnalysisResult]):
    """Convert result dataclasses to a pandas DataFrame with stable columns."""
    rows = [result.to_dict() for result in results]
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def save_csv_report(df, report_path: str) -> None:
    """Write the CSV report to disk."""
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(report_path, index=False, encoding="utf-8-sig")


def save_json_audit_report(results: list[PhotoAnalysisResult], summary: dict, report_path: str) -> None:
    """Write a JSON audit report with summary, scores, and reasons."""
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary,
        "photos": [result.to_dict() for result in results],
    }
    Path(report_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def generate_summary(df) -> dict:
    """Generate aggregate statistics for UI display."""
    if df.empty:
        return {
            "total_processed": 0,
            "selected": 0,
            "review": 0,
            "rejected": 0,
            "errors": 0,
            "blur_photos": 0,
            "underexposed_photos": 0,
            "overexposed_photos": 0,
            "duplicate_groups": 0,
        }

    duplicate_groups = df["duplicate_group_id"].dropna()
    duplicate_groups = duplicate_groups[duplicate_groups != ""]

    return {
        "total_processed": int(len(df)),
        "selected": int((df["output_status"] == "SELECTED").sum()),
        "review": int((df["output_status"] == "REVIEW").sum()),
        "rejected": int((df["output_status"] == "REJECTED").sum()),
        "errors": int((df["output_status"] == "ERROR").sum()),
        "blur_photos": int(df["is_blur"].fillna(False).sum()),
        "underexposed_photos": int((df["exposure_status"].str.upper() == UNDEREXPOSED).sum()),
        "overexposed_photos": int((df["exposure_status"].str.upper() == OVEREXPOSED).sum()),
        "duplicate_groups": int(duplicate_groups.nunique()),
        "localized_person_blur_photos": int(df.get("localized_person_blur", pd.Series(dtype=bool)).fillna(False).sum()),
    }
