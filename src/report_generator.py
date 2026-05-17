"""CSV reporting and summary generation."""

from pathlib import Path

import pandas as pd

from src.models import PhotoAnalysisResult


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
]


def results_to_dataframe(results: list[PhotoAnalysisResult]):
    """Convert result dataclasses to a pandas DataFrame with stable columns."""
    rows = [result.to_dict() for result in results]
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def save_csv_report(df, report_path: str) -> None:
    """Write the CSV report to disk."""
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(report_path, index=False, encoding="utf-8-sig")


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
        "underexposed_photos": int((df["exposure_status"] == "underexposed").sum()),
        "overexposed_photos": int((df["exposure_status"] == "overexposed").sum()),
        "duplicate_groups": int(duplicate_groups.nunique()),
    }

