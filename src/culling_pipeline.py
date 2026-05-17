"""Compatibility wrapper around the modular CullaGrace core engine."""

from pathlib import Path
from typing import Callable

from src.core.culling.culling_engine import run_culling_engine
from src.core.photo.photo_types import PhotoItem
from src.file_manager import default_output_folder, normalize_user_path
from src.models import PhotoAnalysisResult
from src.report_generator import generate_summary, results_to_dataframe


ProgressCallback = Callable[[int, int, str], None]
LogCallback = Callable[[str], None]


def _log(callback: LogCallback | None, message: str) -> None:
    if callback:
        callback(message)


def _progress(callback: ProgressCallback | None, current: int, total: int, message: str) -> None:
    if callback:
        callback(current, total, message)


def _latest_report(report_dir: Path, pattern: str) -> str | None:
    matches = sorted(report_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return str(matches[0]) if matches else None


def _core_item_to_result(item: PhotoItem) -> PhotoAnalysisResult:
    """Convert a core PhotoItem into the legacy UI dataframe shape."""
    score = item.score
    output_status = item.status.upper()
    reasons = "; ".join(score.reasons)
    selected_photo_id = str(item.metadata_dict.get("selected_photo_id") or "")
    winner_filename = str(item.metadata_dict.get("cluster_winner_filename") or "")
    score_gap = item.metadata_dict.get("score_gap_from_winner")
    cluster_size = int(item.metadata_dict.get("cluster_size") or 1)
    return PhotoAnalysisResult(
        filename=item.filename or item.file_name,
        original_path=str(item.path),
        output_status=output_status,
        output_path=getattr(item, "output_path", None),
        blur_score=round(score.technical.sharpness * 300.0, 2),
        is_blur=score.technical.global_blur_penalty > 0.55,
        brightness_score=None,
        exposure_status="NORMAL" if score.technical.exposure >= 0.5 else "UNDEREXPOSED_OR_OVEREXPOSED",
        face_count=score.face.face_count,
        has_face=score.face.face_detected,
        duplicate_group_id=item.cluster_id,
        is_duplicate_candidate=cluster_size > 1,
        best_in_duplicate_group=item.is_cluster_winner,
        final_score=round(score.final_score * 100.0, 2),
        notes=reasons,
        person_count=1 if score.body.person_detected else 0,
        main_person_blur_score=round(score.body.body_sharpness * 180.0, 2),
        avg_person_blur_score=None,
        min_person_blur_score=None,
        localized_person_blur=score.body.body_blur_penalty >= 0.45,
        human_quality_score=int(score.final_score * 150),
        duplicate_quality_rank=None,
        is_best_duplicate=item.is_cluster_winner,
        final_reason=reasons,
        thumbnail_path=item.thumbnail_path,
        technical_score=score.technical_score,
        sharpness_score=score.technical.sharpness,
        exposure_score=score.technical.exposure,
        contrast_score=score.technical.contrast,
        blur_penalty=score.technical.global_blur_penalty,
        face_score=score.face.face_score,
        face_sharpness_score=score.face.face_sharpness,
        body_sharpness_score=score.body.body_sharpness,
        body_blur_penalty=score.body.body_blur_penalty,
        subject_score=score.body.subject_score,
        aesthetic_score=score.aesthetic_score,
        culling_mode=str(item.metadata_dict.get("mode", "balanced")),
        selected_photo_id=selected_photo_id or None,
        score_percent=round(score.final_score * 100.0, 2),
        subject_detected=score.body.person_detected,
        cluster_winner_filename=winner_filename or None,
        score_gap_from_winner=round(float(score_gap), 4) if score_gap is not None else None,
    )


def run_culling_pipeline(
    input_folder: str,
    output_folder: str | None,
    config: dict,
    progress_callback: ProgressCallback | None = None,
    log_callback: LogCallback | None = None,
) -> tuple[list[PhotoAnalysisResult], dict]:
    """Run the core culling engine and return Streamlit-compatible rows."""
    _log(log_callback, "Scanning images...")
    input_path = normalize_user_path(input_folder)
    if input_path is None:
        raise FileNotFoundError("Folder input tidak ditemukan.")

    output_path = normalize_user_path(output_folder) if output_folder else Path(default_output_folder(str(input_path)))
    if output_path is None:
        output_path = Path(default_output_folder(str(input_path)))

    _progress(progress_callback, 0, 1, "Analyzing photos...")
    mode = config.get("culling_mode", "balanced")
    items = run_culling_engine(
        input_dir=input_path,
        output_dir=output_path,
        mode=mode,
        recursive=True,
        copy_files=bool(config.get("copy_files", True)),
        similarity_threshold=int(config.get("duplicate_hash_threshold", 8)),
        enable_body_scoring=bool(config.get("use_human_aware_detection", True)),
        enable_person_detection=bool(config.get("enable_person_detection", False)),
    )
    total = len(items)
    for index, item in enumerate(items, start=1):
        item.metadata_dict["mode"] = mode
        _progress(progress_callback, index, total, f"Processed {item.file_name} ({index}/{total})")

    results = [_core_item_to_result(item) for item in items]
    df = results_to_dataframe(results)
    report_dir = output_path / "04_REPORT"
    summary = generate_summary(df)
    summary["output_folder"] = str(output_path)
    summary["report_path"] = _latest_report(report_dir, "culling_report_*.csv")
    summary["json_report_path"] = _latest_report(report_dir, "culling_audit_*.json")
    summary["total_images"] = total
    summary["mode"] = mode
    summary["cluster_count"] = int(df["duplicate_group_id"].dropna().nunique()) if not df.empty else 0
    summary["average_final_score"] = round(float(df["final_score"].mean()), 2) if not df.empty else 0.0
    _log(log_callback, "Done.")
    _progress(progress_callback, total, total, "Culling selesai.")
    return results, summary
