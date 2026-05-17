"""Main orchestration pipeline for photo culling."""

from collections import defaultdict
from pathlib import Path
from typing import Callable

from src.blur_detector import calculate_blur_score, is_blurry
from src.core.cache.analysis_cache import load_analysis_cache, save_analysis_cache
from src.core.cache.thumbnail_cache import get_thumbnail_path
from src.core.photo.photo_types import CullingMode
from src.core.scoring.aesthetic_score import AestheticScorer
from src.core.scoring.final_score import MODE_CONFIG, calculate_final_score
from src.core.scoring.technical_score import calculate_technical_score
from src.duplicate_detector import group_duplicates
from src.exposure_detector import NORMAL, classify_exposure, calculate_brightness
from src.face_detector import count_faces
from src.file_manager import (
    copy_photo_to_status_folder,
    copy_to_output,
    create_output_folders,
    default_output_folder,
    normalize_user_path,
    prepare_output_dirs,
)
from src.image_loader import list_image_files, load_image, scan_images
from src.models import PhotoAnalysisResult
from src.person_blur_analyzer import calculate_person_blur_scores, detect_localized_person_blur
from src.person_detector import detect_person_boxes, select_main_person_box
from src.report_generator import (
    build_summary,
    generate_summary,
    results_to_dataframe,
    save_json_audit_report,
    save_csv_report,
    write_csv_report,
)
from src.scorer import (
    PhotoAnalysis,
    build_notes,
    calculate_human_quality_score,
    calculate_score,
    classify_status,
)


ProgressCallback = Callable[[int, int, str], None]
LogCallback = Callable[[str], None]


def _log(log_callback: LogCallback | None, message: str) -> None:
    if log_callback:
        log_callback(message)


def _progress(progress_callback: ProgressCallback | None, current: int, total: int, message: str) -> None:
    if progress_callback:
        progress_callback(current, total, message)


def _default_output_dir(input_dir: Path) -> Path:
    return input_dir / f"{input_dir.name}_CULLED"


def _duplicate_lookup(groups: dict[str, list[Path]]) -> dict[Path, str | None]:
    lookup: dict[Path, str | None] = {}
    for group_id, paths in groups.items():
        is_duplicate_group = len(paths) > 1
        for path in paths:
            lookup[path] = group_id if is_duplicate_group else None
    return lookup


def rank_duplicate_group(analyses: list[PhotoAnalysis]) -> list[PhotoAnalysis]:
    """Rank duplicate candidates from best to worst using human-aware quality."""
    return sorted(
        analyses,
        key=lambda analysis: (
            analysis.human_quality_score,
            not analysis.localized_person_blur,
            analysis.main_person_blur_score if analysis.main_person_blur_score is not None else -1.0,
            analysis.face_count,
            analysis.blur_score,
            analysis.exposure_status == NORMAL,
        ),
        reverse=True,
    )


def _legacy_best_paths(rows: list[dict]) -> set[Path]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        group_id = row.get("duplicate_group")
        if group_id:
            grouped[group_id].append(row)

    best_paths: set[Path] = set()
    for group_rows in grouped.values():
        if len(group_rows) <= 1:
            continue
        best = max(
            group_rows,
            key=lambda row: (
                not row["is_blurry"],
                row["exposure_status"] == NORMAL,
                row["blur_score"],
                row["face_count"],
            ),
        )
        best_paths.add(best["path"])
    return best_paths


def _human_blur_data(
    image_path: Path,
    enabled: bool,
    confidence_threshold: float,
    patch_blur_threshold: float,
    localized_blur_patch_ratio: float,
) -> tuple[dict, str]:
    if not enabled:
        return (
            {
                "person_count": 0,
                "main_person_blur_score": None,
                "avg_person_blur_score": None,
                "min_person_blur_score": None,
                "localized_person_blur": False,
            },
            "Human-aware blur detection disabled.",
        )

    try:
        person_boxes = detect_person_boxes(image_path, confidence_threshold=confidence_threshold)
        scores = calculate_person_blur_scores(image_path, person_boxes) if person_boxes else {
            "person_count": 0,
            "main_person_blur_score": None,
            "avg_person_blur_score": None,
            "min_person_blur_score": None,
        }
        image = load_image(str(image_path))
        height, width = image.shape[:2]
        main_box = select_main_person_box(person_boxes, width, height)
        localized_blur = (
            detect_localized_person_blur(
                image,
                main_box,
                patch_blur_threshold=patch_blur_threshold,
                min_blurry_patch_ratio=localized_blur_patch_ratio,
            )
            if main_box is not None
            else False
        )
        scores["localized_person_blur"] = localized_blur
        reason = "Person detection completed." if person_boxes else "No person detected or person detector unavailable."
        return scores, reason
    except Exception as exc:
        return (
            {
                "person_count": 0,
                "main_person_blur_score": None,
                "avg_person_blur_score": None,
                "min_person_blur_score": None,
                "localized_person_blur": False,
            },
            f"Person detection failed or unavailable: {exc}",
        )


def _technical_data(image_path: Path) -> dict:
    """Load cached technical analysis or compute it once for this file version."""
    cached = load_analysis_cache(image_path)
    if cached and "technical" in cached:
        return cached["technical"]

    thumbnail_path = get_thumbnail_path(image_path)
    technical = calculate_technical_score(image_path)
    technical["thumbnail_path"] = str(thumbnail_path)
    save_analysis_cache(image_path, {"technical": technical})
    return technical


def _build_base_analysis(
    row: dict,
    selected_min: int,
    review_min: int,
    is_duplicate_non_best: bool,
    is_best_in_duplicate_group: bool,
    duplicate_quality_rank: int | None,
    best_human_quality_score: int | None,
    culling_mode: CullingMode,
) -> PhotoAnalysis:
    final_score = calculate_score(
        is_blurry=row["is_blurry"],
        exposure_status=row["exposure_status"],
        face_count=row["face_count"],
        is_duplicate_non_best=is_duplicate_non_best,
        is_best_in_duplicate_group=is_best_in_duplicate_group,
    )
    status = classify_status(final_score, selected_min, review_min)
    reasons = [row.get("person_detection_reason", "")]

    if row["localized_person_blur"] and status == "SELECTED":
        status = "REVIEW"
        reasons.append("Moved to REVIEW because localized person blur was detected.")

    if row["main_person_blur_score"] is not None and row["main_person_blur_score"] < 60 and status == "SELECTED":
        status = "REVIEW"
        reasons.append("Moved to REVIEW because main person blur score is low.")

    if duplicate_quality_rank is not None and duplicate_quality_rank > 1 and status == "SELECTED":
        status = "REVIEW"
        reasons.append("Moved to REVIEW because this is not the best duplicate candidate.")

    if (
        duplicate_quality_rank is not None
        and duplicate_quality_rank > 1
        and best_human_quality_score is not None
        and row["human_quality_score"] < best_human_quality_score - 25
    ):
        status = "REJECTED"
        reasons.append("Rejected because a similar photo has much better human quality score.")

    if duplicate_quality_rank == 1:
        reasons.append(
            "Selected as best duplicate because human subject is cleaner and no localized body blur detected."
        )
    elif row["localized_person_blur"]:
        reasons.append("Localized body blur detected; photo should be reviewed manually.")

    return PhotoAnalysis(
        path=row["path"],
        filename=row["filename"],
        blur_score=round(float(row["blur_score"]), 2),
        is_blurry=row["is_blurry"],
        brightness=round(float(row["brightness"]), 2),
        exposure_status=row["exposure_status"],
        face_count=row["face_count"],
        duplicate_group=row["duplicate_group"],
        is_best_in_duplicate_group=is_best_in_duplicate_group,
        final_score=final_score,
        status=status,
        person_count=row["person_count"],
        main_person_blur_score=row["main_person_blur_score"],
        avg_person_blur_score=row["avg_person_blur_score"],
        min_person_blur_score=row["min_person_blur_score"],
        localized_person_blur=row["localized_person_blur"],
        human_quality_score=row["human_quality_score"],
        duplicate_quality_rank=duplicate_quality_rank,
        is_best_duplicate=is_best_in_duplicate_group,
        final_reason=" ".join(reason for reason in reasons if reason).strip(),
        thumbnail_path=row.get("thumbnail_path"),
        technical_score=row.get("technical_score", 0.0),
        sharpness_score=row.get("sharpness_score", 0.0),
        exposure_score=row.get("exposure_score", 0.0),
        contrast_score=row.get("contrast_score", 0.0),
        blur_penalty=row.get("blur_penalty", 0.0),
        face_score=row.get("face_score"),
        body_sharpness_score=row.get("body_sharpness_score"),
        body_blur_penalty=row.get("body_blur_penalty"),
        aesthetic_score=row.get("aesthetic_score"),
        culling_mode=culling_mode,
    )


def _analyze_rows(
    image_paths: list[Path],
    duplicates: dict[Path, str | None],
    blur_threshold: float,
    under_threshold: float,
    over_threshold: float,
    use_face_detection: bool,
    use_human_aware_detection: bool,
    person_detection_confidence: float,
    person_patch_blur_threshold: float,
    localized_blur_patch_ratio: float,
    progress_callback: ProgressCallback | None,
) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    errors: list[dict] = []
    total = len(image_paths)
    for index, image_path in enumerate(image_paths, start=1):
        _progress(progress_callback, index, total, f"Memproses foto {index} dari {total}: {image_path.name}")
        try:
            technical = _technical_data(image_path)
            blur_score = technical["raw_blur_score"]
            brightness = calculate_brightness(image_path)
            exposure_status = classify_exposure(brightness, under_threshold, over_threshold)
            face_count = count_faces(image_path) if use_face_detection else 0
            face_score = min(1.0, 0.35 + face_count * 0.25) if face_count > 0 else 0.45
            person_data, person_reason = _human_blur_data(
                image_path,
                use_human_aware_detection,
                person_detection_confidence,
                person_patch_blur_threshold,
                localized_blur_patch_ratio,
            )
            human_quality_score = calculate_human_quality_score(
                face_count=face_count,
                global_blur_score=blur_score,
                main_person_blur_score=person_data["main_person_blur_score"],
                avg_person_blur_score=person_data["avg_person_blur_score"],
                localized_person_blur=person_data["localized_person_blur"],
                exposure_status=exposure_status,
            )
            body_sharpness_score = (
                max(0.0, min(1.0, person_data["main_person_blur_score"] / 180.0))
                if person_data["main_person_blur_score"] is not None
                else 0.45
            )
            body_blur_penalty = 0.35 if person_data["localized_person_blur"] else max(0.0, 0.45 - body_sharpness_score)
            aesthetic_score = AestheticScorer().score(image_path)
            normalized_final_score = calculate_final_score(
                technical_score=technical["technical_score"],
                face_score=face_score,
                body_sharpness_score=body_sharpness_score,
                body_blur_penalty=body_blur_penalty,
                aesthetic_score=aesthetic_score,
            )
            rows.append(
                {
                    "path": image_path,
                    "filename": image_path.name,
                    "blur_score": blur_score,
                    "is_blurry": is_blurry(blur_score, blur_threshold),
                    "brightness": brightness,
                    "exposure_status": exposure_status,
                    "face_count": face_count,
                    "duplicate_group": duplicates.get(image_path),
                    "human_quality_score": human_quality_score,
                    "person_detection_reason": person_reason,
                    "thumbnail_path": technical.get("thumbnail_path"),
                    "technical_score": technical["technical_score"],
                    "sharpness_score": technical["sharpness_score"],
                    "exposure_score": technical["exposure_score"],
                    "contrast_score": technical["contrast_score"],
                    "blur_penalty": technical["blur_penalty"],
                    "face_score": face_score,
                    "body_sharpness_score": round(body_sharpness_score, 4),
                    "body_blur_penalty": round(body_blur_penalty, 4),
                    "aesthetic_score": aesthetic_score,
                    "normalized_final_score": normalized_final_score,
                    **person_data,
                }
            )
        except Exception as exc:
            errors.append({"path": str(image_path), "error": str(exc)})
    return rows, errors


def _finalize_analyses(
    rows: list[dict],
    selected_min: int,
    review_min: int,
    use_human_aware_detection: bool,
    culling_mode: CullingMode = "balanced",
) -> list[PhotoAnalysis]:
    analyses: list[PhotoAnalysis] = []
    if use_human_aware_detection:
        grouped: dict[str, list[PhotoAnalysis]] = defaultdict(list)
        single_rows: list[dict] = []
        for row in rows:
            if row["duplicate_group"] is None:
                single_rows.append(row)
                continue
            preview = _build_base_analysis(row, selected_min, review_min, False, False, None, None, culling_mode)
            grouped[row["duplicate_group"]].append(preview)

        for row in single_rows:
            analyses.append(_build_base_analysis(row, selected_min, review_min, False, False, None, None, culling_mode))

        row_by_path = {row["path"]: row for row in rows}
        for group_analyses in grouped.values():
            if len(group_analyses) <= 1:
                analysis = group_analyses[0]
                row = row_by_path[analysis.path]
                analyses.append(_build_base_analysis(row, selected_min, review_min, False, False, None, None, culling_mode))
                continue
            ranked = rank_duplicate_group(group_analyses)
            best_human_quality_score = ranked[0].human_quality_score
            keep_extra = 0
            if culling_mode == "conservative":
                keep_extra = 2
            elif culling_mode == "balanced" and len(ranked) >= 4:
                keep_extra = 1
            for rank, preview in enumerate(ranked, start=1):
                row = row_by_path[preview.path]
                is_kept_candidate = rank == 1
                if rank > 1 and rank <= keep_extra + 1:
                    allowed_delta = int(MODE_CONFIG[culling_mode].conservative_keep_score_delta * 150)
                    is_kept_candidate = best_human_quality_score - row["human_quality_score"] <= allowed_delta
                analyses.append(
                    _build_base_analysis(
                        row,
                        selected_min,
                        review_min,
                        is_duplicate_non_best=not is_kept_candidate,
                        is_best_in_duplicate_group=is_kept_candidate,
                        duplicate_quality_rank=rank,
                        best_human_quality_score=best_human_quality_score,
                        culling_mode=culling_mode,
                    )
                )
        return analyses

    legacy_best_paths = _legacy_best_paths(rows)
    for row in rows:
        is_best = row["path"] in legacy_best_paths
        analyses.append(
            _build_base_analysis(
                row,
                selected_min,
                review_min,
                is_duplicate_non_best=row["duplicate_group"] is not None and not is_best,
                is_best_in_duplicate_group=is_best,
                duplicate_quality_rank=None,
                best_human_quality_score=None,
                culling_mode=culling_mode,
            )
        )
    return analyses


def run_culling(
    input_dir: Path,
    output_dir: Path | None = None,
    blur_threshold: float = 100.0,
    under_threshold: float = 50.0,
    over_threshold: float = 210.0,
    duplicate_hash_threshold: int = 8,
    selected_min: int = 80,
    review_min: int = 50,
    progress_callback: ProgressCallback | None = None,
    use_human_aware_detection: bool = True,
    person_detection_confidence: float = 0.35,
    person_patch_blur_threshold: float = 75.0,
    localized_blur_patch_ratio: float = 0.25,
    culling_mode: CullingMode = "balanced",
) -> tuple[list[PhotoAnalysis], Path, dict]:
    """Run the MVP culling pipeline and return analyses, report path, and summary."""
    input_path = normalize_user_path(input_dir)
    if input_path is None:
        raise FileNotFoundError("Folder input tidak ditemukan.")
    image_paths = scan_images(input_path)
    if not image_paths:
        raise ValueError("Tidak ada file foto JPG, JPEG, atau PNG di folder ini.")

    output_path = normalize_user_path(output_dir) if output_dir else _default_output_dir(input_path)
    if output_path is None:
        output_path = _default_output_dir(input_path)
    output_dirs = prepare_output_dirs(output_path)
    duplicate_groups = group_duplicates(image_paths, hash_threshold=duplicate_hash_threshold)
    duplicates = _duplicate_lookup(duplicate_groups)

    rows, errors = _analyze_rows(
        image_paths=image_paths,
        duplicates=duplicates,
        blur_threshold=blur_threshold,
        under_threshold=under_threshold,
        over_threshold=over_threshold,
        use_face_detection=True,
        use_human_aware_detection=use_human_aware_detection,
        person_detection_confidence=person_detection_confidence,
        person_patch_blur_threshold=person_patch_blur_threshold,
        localized_blur_patch_ratio=localized_blur_patch_ratio,
        progress_callback=progress_callback,
    )
    analyses = _finalize_analyses(rows, selected_min, review_min, use_human_aware_detection, culling_mode)
    for analysis in analyses:
        copy_photo_to_status_folder(analysis.path, analysis.status, output_dirs)

    report_path = write_csv_report(analyses, output_dirs["REPORT"])
    summary = build_summary(analyses)
    summary["output_dir"] = str(output_path)
    summary["report_path"] = str(report_path)
    summary["mode"] = culling_mode
    summary["errors"] = errors
    summary["error_count"] = len(errors)
    return analyses, report_path, summary


def _to_legacy_result(analysis: PhotoAnalysis, output_path: str | None = None) -> PhotoAnalysisResult:
    """Convert an MVP PhotoAnalysis row into the richer UI result model."""
    return PhotoAnalysisResult(
        filename=analysis.filename,
        original_path=str(analysis.path),
        output_status=analysis.status,
        output_path=output_path,
        blur_score=analysis.blur_score,
        is_blur=analysis.is_blurry,
        brightness_score=analysis.brightness,
        exposure_status=analysis.exposure_status,
        face_count=analysis.face_count,
        has_face=analysis.face_count > 0,
        duplicate_group_id=analysis.duplicate_group,
        is_duplicate_candidate=analysis.duplicate_group is not None,
        best_in_duplicate_group=analysis.is_best_in_duplicate_group,
        final_score=analysis.final_score,
        notes=build_notes(
            analysis.is_blurry,
            analysis.exposure_status,
            analysis.face_count,
            analysis.duplicate_group is not None,
            analysis.is_best_in_duplicate_group,
        ),
        person_count=analysis.person_count,
        main_person_blur_score=analysis.main_person_blur_score,
        avg_person_blur_score=analysis.avg_person_blur_score,
        min_person_blur_score=analysis.min_person_blur_score,
        localized_person_blur=analysis.localized_person_blur,
        human_quality_score=analysis.human_quality_score,
        duplicate_quality_rank=analysis.duplicate_quality_rank,
        is_best_duplicate=analysis.is_best_duplicate,
        final_reason=analysis.final_reason,
        thumbnail_path=analysis.thumbnail_path,
        technical_score=analysis.technical_score,
        sharpness_score=analysis.sharpness_score,
        exposure_score=analysis.exposure_score,
        contrast_score=analysis.contrast_score,
        blur_penalty=analysis.blur_penalty,
        face_score=analysis.face_score,
        body_sharpness_score=analysis.body_sharpness_score,
        body_blur_penalty=analysis.body_blur_penalty,
        aesthetic_score=analysis.aesthetic_score,
        culling_mode=analysis.culling_mode,
    )


def _error_result(image_path: Path, error: str) -> PhotoAnalysisResult:
    return PhotoAnalysisResult(
        filename=image_path.name,
        original_path=str(image_path),
        output_status="ERROR",
        output_path=None,
        blur_score=None,
        is_blur=False,
        brightness_score=None,
        exposure_status="ERROR",
        face_count=0,
        has_face=False,
        duplicate_group_id=None,
        is_duplicate_candidate=False,
        best_in_duplicate_group=False,
        final_score=0,
        notes=build_notes(False, "ERROR", 0, False, False, error),
        error=error,
        final_reason=error,
    )


def run_culling_pipeline(
    input_folder: str,
    output_folder: str | None,
    config: dict,
    progress_callback: ProgressCallback | None = None,
    log_callback: LogCallback | None = None,
) -> tuple[list[PhotoAnalysisResult], dict]:
    """Run the Streamlit-oriented culling workflow and return UI-compatible data."""
    _log(log_callback, "Memvalidasi folder input...")
    image_path_strings = list_image_files(input_folder)
    total = len(image_path_strings)
    if total == 0:
        raise ValueError("Tidak ada file foto JPG, JPEG, atau PNG di folder ini.")

    normalized_output = normalize_user_path(output_folder) if output_folder else None
    resolved_output = str(normalized_output) if normalized_output else default_output_folder(input_folder)
    output_folders = create_output_folders(resolved_output)
    _log(log_callback, f"Folder output dibuat: {output_folders['BASE']}")
    _log(log_callback, f"Loaded {total} images")

    image_paths = [Path(path) for path in image_path_strings]
    if config.get("use_duplicate_detection", True):
        _log(log_callback, "Sedang mencari foto yang mirip...")
        duplicate_groups = group_duplicates(
            image_paths,
            hash_threshold=int(config.get("duplicate_hash_threshold", 8)),
        )
        duplicates = _duplicate_lookup(duplicate_groups)
    else:
        _log(log_callback, "Deteksi duplikat dilewati sesuai pengaturan.")
        duplicates = {path: None for path in image_paths}

    _log(log_callback, "Menganalisis blur, exposure, wajah, dan kualitas subjek manusia...")
    rows, errors = _analyze_rows(
        image_paths=image_paths,
        duplicates=duplicates,
        blur_threshold=float(config.get("blur_threshold", 100)),
        under_threshold=float(config.get("underexposed_threshold", 50)),
        over_threshold=float(config.get("overexposed_threshold", 210)),
        use_face_detection=bool(config.get("use_face_detection", True)),
        use_human_aware_detection=bool(config.get("use_human_aware_detection", True)),
        person_detection_confidence=float(config.get("person_detection_confidence", 0.35)),
        person_patch_blur_threshold=float(config.get("person_patch_blur_threshold", 75.0)),
        localized_blur_patch_ratio=float(config.get("localized_blur_patch_ratio", 0.25)),
        progress_callback=progress_callback,
    )
    results = [_error_result(Path(error["path"]), error["error"]) for error in errors]

    _log(log_callback, "Meranking foto mirip berdasarkan kualitas subjek manusia...")
    analyses = _finalize_analyses(
        rows,
        int(config.get("selected_score_min", 80)),
        int(config.get("review_score_min", 50)),
        bool(config.get("use_human_aware_detection", True)),
        config.get("culling_mode", "balanced"),
    )

    _log(log_callback, "Menyalin file dan membuat hasil akhir...")
    for analysis in analyses:
        output_path = None
        copy_error = None
        if config.get("copy_files", True):
            try:
                output_path = copy_to_output(str(analysis.path), analysis.status, output_folders)
            except Exception as exc:
                copy_error = f"Gagal menyalin file: {exc}"
        result = _to_legacy_result(analysis, output_path)
        if copy_error:
            result.error = copy_error
            result.notes = build_notes(
                result.is_blur,
                result.exposure_status,
                result.face_count,
                result.is_duplicate_candidate,
                result.best_in_duplicate_group,
                result.error,
            )
            result.final_reason = copy_error
        results.append(result)

    df = results_to_dataframe(results)
    report_path = None
    json_report_path = None
    if config.get("create_csv", True):
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_path = str(
            Path(output_folders["REPORT"]) / f"culling_report_{timestamp}.csv"
        )
        _log(log_callback, "Membuat laporan CSV...")
        save_csv_report(df, report_path)

    summary = generate_summary(df)
    summary["output_folder"] = output_folders["BASE"]
    summary["report_path"] = report_path
    summary["total_images"] = total
    summary["mode"] = config.get("culling_mode", "balanced")
    if config.get("create_csv", True):
        from datetime import datetime

        json_report_path = str(
            Path(output_folders["REPORT"]) / f"culling_audit_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
        )
        save_json_audit_report(results, summary, json_report_path)
    summary["json_report_path"] = json_report_path
    _log(log_callback, "Done.")
    _progress(progress_callback, total, total, "Culling selesai.")
    return results, summary


def _latest_report(report_dir: Path, pattern: str) -> str | None:
    matches = sorted(report_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return str(matches[0]) if matches else None


def _core_item_to_result(item) -> PhotoAnalysisResult:
    score = item.score
    output_status = item.status.upper()
    reasons = "; ".join(score.reasons)
    output_path = getattr(item, "output_path", None)
    return PhotoAnalysisResult(
        filename=item.filename or item.file_name,
        original_path=str(item.path),
        output_status=output_status,
        output_path=output_path,
        blur_score=round(score.sharpness_score * 300.0, 2),
        is_blur=score.technical.global_blur_penalty > 0.55,
        brightness_score=None,
        exposure_status="NORMAL" if score.technical.exposure >= 0.5 else "UNDEREXPOSED_OR_OVEREXPOSED",
        face_count=score.face.face_count,
        has_face=score.face.face_detected,
        duplicate_group_id=item.cluster_id,
        is_duplicate_candidate=item.cluster_id is not None,
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
        body_sharpness_score=score.body.body_sharpness,
        body_blur_penalty=score.body.body_blur_penalty,
        aesthetic_score=score.aesthetic_score,
        culling_mode=str(item.metadata_dict.get("mode", "balanced")),
    )


# Public Streamlit wrapper: keep the old API, but route production work through the new core engine.
def run_culling_pipeline(
    input_folder: str,
    output_folder: str | None,
    config: dict,
    progress_callback: ProgressCallback | None = None,
    log_callback: LogCallback | None = None,
) -> tuple[list[PhotoAnalysisResult], dict]:
    """Run CullaGrace culling via the modular core engine and return UI-compatible data."""
    from src.core.culling.culling_engine import run_culling_engine

    _log(log_callback, "Scanning images...")
    input_path = normalize_user_path(input_folder)
    if input_path is None:
        raise FileNotFoundError("Folder input tidak ditemukan.")
    image_paths = list_image_files(str(input_path))
    total = len(image_paths)
    if total == 0:
        raise ValueError("Tidak ada file foto JPG, JPEG, atau PNG di folder ini.")
    _progress(progress_callback, 0, total, "Scanning images...")

    output_path = normalize_user_path(output_folder) if output_folder else Path(default_output_folder(str(input_path)))
    if output_path is None:
        output_path = Path(default_output_folder(str(input_path)))

    _log(log_callback, "Generating thumbnails and analyzing scores...")
    items = run_culling_engine(
        input_dir=input_path,
        output_dir=output_path,
        mode=config.get("culling_mode", "balanced"),
        recursive=True,
        copy_files=bool(config.get("copy_files", True)),
        similarity_threshold=int(config.get("duplicate_hash_threshold", 8)),
        enable_body_scoring=bool(config.get("use_human_aware_detection", True)),
    )
    for index, item in enumerate(items, start=1):
        item.metadata_dict["mode"] = config.get("culling_mode", "balanced")
        _progress(progress_callback, index, total, f"Processed {item.file_name} ({index}/{total})")

    results = [_core_item_to_result(item) for item in items]
    report_dir = output_path / "04_REPORT"
    csv_report = _latest_report(report_dir, "culling_report_*.csv")
    json_report = _latest_report(report_dir, "culling_audit_*.json")
    df = results_to_dataframe(results)
    summary = generate_summary(df)
    summary["output_folder"] = str(output_path)
    summary["report_path"] = csv_report
    summary["json_report_path"] = json_report
    summary["total_images"] = total
    summary["mode"] = config.get("culling_mode", "balanced")
    summary["cluster_count"] = len({item.cluster_id for item in items if item.cluster_id})
    _log(log_callback, "Done.")
    _progress(progress_callback, total, total, "Culling selesai.")
    return results, summary
