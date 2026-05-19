"""End-to-end modular CullaGrace culling engine."""

from pathlib import Path
from typing import Callable

from src.core.cache.analysis_cache import load_analysis_cache, save_analysis_cache
from src.core.cache.analysis_cache import AnalysisCache
from src.core.culling.best_photo_picker import pick_best_photos
from src.core.export.file_exporter import export_photos
from src.core.export.report_writer import write_csv_report, write_json_report
from src.core.photo.image_loader import load_image_array, scan_image_paths
from src.core.photo.photo_loader import make_photo_id
from src.core.photo.photo_types import (
    BodyScore,
    CullingMode,
    CullingResult,
    CullingSummary,
    FaceScore,
    PhotoCluster,
    PhotoItem,
    PhotoScore,
    TechnicalScore,
)
from src.core.photo.thumbnail_cache import build_thumbnail
from src.core.performance.performance_config import PerformanceConfig
from src.core.performance.presets import get_performance_preset
from src.core.performance.resource_limits import resolve_worker_count
from src.core.pipeline.parallel_runner import analyze_photos_batch
from src.core.pipeline.photo_analyzer import cache_record_from_photo_item
from src.core.pipeline.progress_events import ProgressEvent
from src.core.quality.technical_score import compute_technical_score
from src.core.scoring.final_score import compute_final_score
from src.core.similarity.similarity_cluster import build_similarity_clusters
from src.core.subject.face_analyzer import analyze_face, detect_face_regions
from src.core.subject.person_blur_analyzer import analyze_person_body_blur
from src.file_manager import default_output_folder, normalize_user_path


ProgressCallback = Callable[[int, int, str], None]
LogCallback = Callable[[str], None]


def _log(callback: LogCallback | None, message: str) -> None:
    if callback:
        callback(message)


def _progress(callback: ProgressCallback | None, current: int, total: int, message: str) -> None:
    if callback:
        callback(current, total, message)


def _event_progress(callback: ProgressCallback | None, event: ProgressEvent) -> None:
    _progress(callback, event.current, event.total, event.message)


def _event_log(callback: LogCallback | None, event: ProgressEvent) -> None:
    filename = f" [{event.filename}]" if event.filename else ""
    _log(callback, f"{event.stage}: {event.message}{filename}")


def _photo_item_from_path(path: Path) -> PhotoItem:
    """Create a PhotoItem from a local image path."""
    width = 0
    height = 0
    try:
        image = load_image_array(path)
        height, width = image.shape[:2]
    except Exception:
        pass
    return PhotoItem(
        id=make_photo_id(path),
        path=path,
        file_name=path.name,
        filename=path.name,
        width=width,
        height=height,
    )


def _flat_score(technical: TechnicalScore) -> float:
    return round(max(0.0, min(1.0, technical.sharpness * 0.5 + technical.exposure * 0.3 + technical.contrast * 0.2)), 4)


def analyze_photo_item(
    item: PhotoItem,
    cache_root: Path | None = None,
    enable_body_scoring: bool = True,
    enable_person_detection: bool = False,
    mode: CullingMode = "balanced",
) -> PhotoItem:
    """Analyze one photo and attach normalized scores and thumbnail path."""
    image_path = Path(item.path)
    item.thumbnail_path = str(build_thumbnail(image_path, cache_root))
    cached = load_analysis_cache(image_path, cache_root)
    if (
        cached
        and "score" in cached
        and cached.get("enable_body_scoring") == enable_body_scoring
        and cached.get("enable_person_detection") == enable_person_detection
    ):
        score_payload = cached["score"]
        technical = TechnicalScore(**score_payload["technical"])
        face = FaceScore(**score_payload["face"])
        body = BodyScore(**score_payload["body"])
        item.score = PhotoScore(
            technical=technical,
            face=face,
            body=body,
            duplicate_penalty=score_payload.get("duplicate_penalty", 0.0),
            final_score=score_payload["final_score"],
            reasons=score_payload.get("reasons", []),
        )
        item.scores = item.score
        return item

    image = load_image_array(image_path)
    technical = compute_technical_score(image)
    face_regions = detect_face_regions(image)
    face = analyze_face(image)
    body = (
        analyze_person_body_blur(image, face_regions, enable_person_detection=enable_person_detection)
        if enable_body_scoring
        else BodyScore(subject_score=0.45)
    )
    final = compute_final_score(technical, face, body, mode=mode)
    item.score = PhotoScore(
        technical=technical,
        face=face,
        body=body,
        technical_score=_flat_score(technical),
        sharpness_score=technical.sharpness,
        exposure_score=technical.exposure,
        contrast_score=technical.contrast,
        blur_penalty=technical.global_blur_penalty,
        face_score=face.face_score,
        face_sharpness=face.face_sharpness,
        body_sharpness_score=body.body_sharpness,
        body_blur_penalty=body.body_blur_penalty,
        final_score=final,
    )
    item.scores = item.score
    save_analysis_cache(
        image_path,
        {
            "enable_body_scoring": enable_body_scoring,
            "enable_person_detection": enable_person_detection,
            "score": {
                "technical": technical.__dict__,
                "face": face.__dict__,
                "body": body.__dict__,
                "duplicate_penalty": item.score.duplicate_penalty,
                "final_score": item.score.final_score,
                "reasons": item.score.reasons,
            }
        },
        cache_root,
    )
    return item


def _summary(items: list[PhotoItem], clusters: list[PhotoCluster], mode: CullingMode) -> CullingSummary:
    return CullingSummary(
        total_photos=len(items),
        selected_count=sum(item.status == "selected" for item in items),
        rejected_count=sum(item.status == "rejected" for item in items),
        cluster_count=len(clusters),
        mode=mode,
    )


def run_culling_engine(
    input_dir: Path,
    output_dir: Path | None = None,
    mode: CullingMode = "balanced",
    recursive: bool = True,
    copy_files: bool | None = None,
    similarity_threshold: int = 8,
    cache_root: Path | None = None,
    enable_body_scoring: bool = True,
    enable_person_detection: bool = False,
    performance_config: PerformanceConfig | None = None,
    progress_callback: ProgressCallback | None = None,
    log_callback: LogCallback | None = None,
) -> list[PhotoItem]:
    """Run import, analysis, clustering, picking, export, and reports."""
    config = performance_config or get_performance_preset(mode)
    config = config.with_overrides(
        mode=config.mode if config.mode in {"fast", "balanced", "accurate"} else "balanced",
        enable_body_blur_analysis=enable_body_scoring and config.enable_body_blur_analysis,
        worker_count=resolve_worker_count(config.worker_count, config.mode),
    )
    if copy_files is not None:
        config = config.with_overrides(copy_files_after_culling=bool(copy_files))

    _log(log_callback, "Validating input folder...")
    _progress(progress_callback, 0, 1, "Validating input folder...")
    input_path = normalize_user_path(input_dir)
    if input_path is None:
        raise FileNotFoundError("Folder input tidak ditemukan.")
    output_path = normalize_user_path(output_dir) if output_dir else Path(default_output_folder(str(input_path)))
    if output_path is None:
        output_path = Path(default_output_folder(str(input_path)))

    _log(log_callback, "Scanning image files...")
    _progress(progress_callback, 0, 1, "Scanning image files...")
    paths = scan_image_paths(input_path, recursive=recursive)
    total_steps = max(len(paths), 1) + 5
    current_step = 0
    _log(log_callback, f"Found {len(paths)} image file(s).")
    _progress(progress_callback, current_step, total_steps, f"Found {len(paths)} image file(s).")

    cache_dir = (cache_root or output_path / ".cullagrace_cache")
    cache = AnalysisCache(cache_dir)
    if config.use_cache:
        _log(log_callback, "Loading analysis cache...")
        cache.load()
    else:
        _log(log_callback, "Analysis cache disabled.")

    def batch_progress(event: ProgressEvent) -> None:
        _event_log(log_callback, event)
        _event_progress(progress_callback, ProgressEvent(event.stage, event.current, total_steps, event.message, event.filename))

    items = analyze_photos_batch(paths, config, cache if config.use_cache else None, cache_dir, batch_progress)
    for item in items:
        item.metadata_dict["mode"] = mode
        item.metadata_dict["performance_mode"] = config.mode
        item.metadata_dict["max_analysis_size"] = config.max_analysis_size
        item.metadata_dict["worker_count"] = config.worker_count
        item.metadata_dict["used_cache"] = config.use_cache
        item.metadata_dict["face_analysis_enabled"] = config.enable_face_analysis
        item.metadata_dict["body_blur_analysis_enabled"] = config.enable_body_blur_analysis
        item.metadata_dict["similarity_grouping_enabled"] = config.enable_similarity_grouping
        item.metadata_dict["copy_files_after_culling"] = config.copy_files_after_culling

    current_step = len(items) + 1
    if config.enable_similarity_grouping:
        _log(log_callback, "Grouping similar photos...")
        _progress(progress_callback, current_step, total_steps, "Grouping similar photos...")
        clusters = build_similarity_clusters(items, threshold=similarity_threshold)
    else:
        _log(log_callback, "Similarity grouping disabled; creating one-photo clusters...")
        _progress(progress_callback, current_step, total_steps, "Similarity grouping disabled...")
        clusters = []
        for index, item in enumerate(items, start=1):
            cluster_id = f"CL{index:04d}"
            item.cluster_id = cluster_id
            clusters.append(PhotoCluster(id=cluster_id, photo_ids=[item.id], photos=[item], confidence=0.0))

    current_step = len(items) + 2
    _log(log_callback, "Selecting best photos in each cluster...")
    _progress(progress_callback, current_step, total_steps, "Selecting best photos in each cluster...")
    pick_best_photos(clusters, mode=mode, keep_per_cluster=3 if mode == "conservative" else 1)

    if config.use_cache:
        for item in items:
            if Path(item.path).exists():
                cache.set(Path(item.path), cache_record_from_photo_item(item, Path(item.path), config))
        cache.save()

    if config.copy_files_after_culling:
        current_step = len(items) + 3
        _log(log_callback, "Copying photos into AI recommendation folders...")
        _progress(progress_callback, current_step, total_steps, "Copying photos into AI recommendation folders...")
        export_photos(items, output_path)
    else:
        current_step = len(items) + 3
        _log(log_callback, "Skipping photo copy because copy_files is disabled.")
        _progress(progress_callback, current_step, total_steps, "Skipping photo copy because copy_files is disabled.")

    current_step = len(items) + 4
    _log(log_callback, "Writing CSV and JSON audit reports...")
    _progress(progress_callback, current_step, total_steps, "Writing CSV and JSON audit reports...")
    report_dir = output_path / "04_REPORT"
    write_csv_report(items, report_dir)
    write_json_report(
        items,
        report_dir,
        clusters=clusters,
        mode=mode,
        performance={
            "mode": config.mode,
            "max_analysis_size": config.max_analysis_size,
            "worker_count": config.worker_count,
            "use_cache": config.use_cache,
            "copy_files_after_culling": config.copy_files_after_culling,
            "enable_face_analysis": config.enable_face_analysis,
            "enable_body_blur_analysis": config.enable_body_blur_analysis,
            "enable_similarity_grouping": config.enable_similarity_grouping,
        },
    )
    _log(log_callback, "Core culling engine finished.")
    _progress(progress_callback, total_steps, total_steps, "Core culling engine finished.")
    return items


def run_core_culling_engine(
    input_dir: Path,
    mode: CullingMode = "balanced",
    similarity_threshold: int = 8,
    cache_root: Path | None = None,
    enable_body_scoring: bool = True,
    enable_person_detection: bool = False,
) -> CullingResult:
    """Compatibility result wrapper around run_culling_engine."""
    _ = enable_body_scoring
    items = run_culling_engine(
        input_dir=input_dir,
        output_dir=None,
        mode=mode,
        recursive=True,
        copy_files=False,
        similarity_threshold=similarity_threshold,
        cache_root=cache_root,
        enable_body_scoring=enable_body_scoring,
        enable_person_detection=enable_person_detection,
    )
    clusters = build_similarity_clusters(items, threshold=similarity_threshold)
    selected = [item for item in items if item.status == "selected"]
    rejected = [item for item in items if item.status == "rejected"]
    return CullingResult(selected=selected, rejected=rejected, clusters=clusters, summary=_summary(items, clusters, mode))
