"""Main orchestration pipeline for photo culling."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from src.blur_detector import calculate_blur_score, is_blurry
from src.duplicate_detector import group_duplicates
from src.exposure_detector import classify_exposure, calculate_brightness
from src.face_detector import detect_faces
from src.file_manager import copy_to_output, create_output_folders, default_output_folder
from src.image_loader import list_image_files, load_image
from src.models import PhotoAnalysisResult
from src.report_generator import generate_summary, results_to_dataframe, save_csv_report
from src.scorer import build_notes, calculate_score, classify_status


def _log(log_callback, message: str) -> None:
    if log_callback:
        log_callback(message)


def _progress(progress_callback, current: int, total: int, message: str) -> None:
    if progress_callback:
        progress_callback(current, total, message)


def _choose_best_duplicates(partial_results: list[dict]) -> set[str]:
    grouped = defaultdict(list)
    for result in partial_results:
        group_id = result.get("duplicate_group_id")
        if group_id:
            grouped[group_id].append(result)

    best_paths = set()
    for group_results in grouped.values():
        best = max(
            group_results,
            key=lambda item: (
                item.get("pre_duplicate_score", 0),
                item.get("blur_score") or 0,
                item.get("brightness_score") or 0,
            ),
        )
        best_paths.add(best["original_path"])
    return best_paths


def run_culling_pipeline(
    input_folder: str,
    output_folder: str | None,
    config: dict,
    progress_callback=None,
    log_callback=None,
) -> tuple[list[PhotoAnalysisResult], dict]:
    """Run the full culling workflow and return per-photo results plus summary."""
    _log(log_callback, "Memvalidasi folder input...")
    image_paths = list_image_files(input_folder)
    total = len(image_paths)
    if total == 0:
        raise ValueError("Tidak ada file foto JPG, JPEG, atau PNG di folder ini.")

    resolved_output = output_folder.strip() if output_folder else ""
    if not resolved_output:
        resolved_output = default_output_folder(input_folder)

    _log(log_callback, f"Loaded {total} images")
    output_folders = create_output_folders(resolved_output)

    duplicate_groups: dict[str, str | None] = {path: None for path in image_paths}
    if config.get("use_duplicate_detection", True):
        _log(log_callback, "Sedang mencari foto yang mirip...")
        duplicate_groups = group_duplicates(
            image_paths,
            int(config.get("duplicate_hash_threshold", 8)),
        )
    else:
        _log(log_callback, "Deteksi duplikat dilewati sesuai pengaturan.")

    partial_results: list[dict] = []
    _log(log_callback, "Menganalisis blur, exposure, dan wajah...")
    for index, image_path in enumerate(image_paths, start=1):
        filename = Path(image_path).name
        _progress(progress_callback, index, total, f"Memproses {filename} ({index}/{total})")

        try:
            image = load_image(image_path)
            blur_score = calculate_blur_score(image)
            blur = is_blurry(blur_score, float(config.get("blur_threshold", 100)))
            brightness = calculate_brightness(image)
            exposure_status = classify_exposure(
                brightness,
                float(config.get("underexposed_threshold", 50)),
                float(config.get("overexposed_threshold", 210)),
            )
            face_count = detect_faces(image) if config.get("use_face_detection", True) else 0
            group_id = duplicate_groups.get(image_path)
            pre_duplicate_score = calculate_score(
                blur,
                exposure_status,
                face_count,
                bool(group_id),
                bool(group_id),
            )
            partial_results.append(
                {
                    "filename": filename,
                    "original_path": image_path,
                    "blur_score": blur_score,
                    "is_blur": blur,
                    "brightness_score": brightness,
                    "exposure_status": exposure_status,
                    "face_count": face_count,
                    "has_face": face_count > 0,
                    "duplicate_group_id": group_id,
                    "is_duplicate_candidate": bool(group_id),
                    "pre_duplicate_score": pre_duplicate_score,
                    "error": None,
                }
            )
        except Exception as exc:
            partial_results.append(
                {
                    "filename": filename,
                    "original_path": image_path,
                    "blur_score": None,
                    "is_blur": False,
                    "brightness_score": None,
                    "exposure_status": "error",
                    "face_count": 0,
                    "has_face": False,
                    "duplicate_group_id": None,
                    "is_duplicate_candidate": False,
                    "pre_duplicate_score": 0.0,
                    "error": str(exc),
                }
            )

    _log(log_callback, "Menentukan foto terbaik dalam grup duplikat...")
    best_duplicate_paths = _choose_best_duplicates(partial_results)

    _log(log_callback, "Menghitung skor dan menyalin file...")
    results: list[PhotoAnalysisResult] = []
    for item in partial_results:
        if item["error"]:
            result = PhotoAnalysisResult(
                filename=item["filename"],
                original_path=item["original_path"],
                output_status="ERROR",
                output_path=None,
                blur_score=None,
                is_blur=False,
                brightness_score=None,
                exposure_status="error",
                face_count=0,
                has_face=False,
                duplicate_group_id=None,
                is_duplicate_candidate=False,
                best_in_duplicate_group=False,
                final_score=0.0,
                notes=build_notes(False, "error", 0, False, False, item["error"]),
                error=item["error"],
            )
        else:
            best_in_duplicate_group = item["original_path"] in best_duplicate_paths
            final_score = calculate_score(
                item["is_blur"],
                item["exposure_status"],
                item["face_count"],
                item["is_duplicate_candidate"],
                best_in_duplicate_group,
            )
            output_status = classify_status(
                final_score,
                float(config.get("selected_score_min", 80)),
                float(config.get("review_score_min", 50)),
            )
            result = PhotoAnalysisResult(
                filename=item["filename"],
                original_path=item["original_path"],
                output_status=output_status,
                output_path=None,
                blur_score=round(float(item["blur_score"]), 2),
                is_blur=bool(item["is_blur"]),
                brightness_score=round(float(item["brightness_score"]), 2),
                exposure_status=item["exposure_status"],
                face_count=int(item["face_count"]),
                has_face=bool(item["has_face"]),
                duplicate_group_id=item["duplicate_group_id"],
                is_duplicate_candidate=bool(item["is_duplicate_candidate"]),
                best_in_duplicate_group=bool(best_in_duplicate_group),
                final_score=round(float(final_score), 2),
                notes=build_notes(
                    item["is_blur"],
                    item["exposure_status"],
                    item["face_count"],
                    item["is_duplicate_candidate"],
                    best_in_duplicate_group,
                ),
                error=None,
            )

        if config.get("copy_files", True):
            try:
                result.output_path = copy_to_output(
                    result.original_path,
                    result.output_status,
                    output_folders,
                )
            except Exception as exc:
                result.error = f"Gagal menyalin file: {exc}"
                result.notes = build_notes(
                    result.is_blur,
                    result.exposure_status,
                    result.face_count,
                    result.is_duplicate_candidate,
                    result.best_in_duplicate_group,
                    result.error,
                )

        results.append(result)

    df = results_to_dataframe(results)
    report_path = None
    if config.get("create_csv", True):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_path = str(Path(output_folders["REPORT"]) / f"culling_report_{timestamp}.csv")
        _log(log_callback, "Membuat laporan CSV...")
        save_csv_report(df, report_path)

    summary = generate_summary(df)
    summary["output_folder"] = output_folders["BASE"]
    summary["report_path"] = report_path
    summary["total_images"] = total
    _log(log_callback, "Done.")
    _progress(progress_callback, total, total, "Culling selesai.")

    return results, summary

