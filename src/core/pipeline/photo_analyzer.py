"""Single-photo performance-aware analyzer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import imagehash
from PIL import Image

from src.core.cache.analysis_cache import AnalysisCache
from src.core.cache.cache_key import build_cache_key
from src.core.cache.cache_types import AnalysisCacheRecord
from src.core.performance.performance_config import PerformanceConfig
from src.core.photo.image_loader import load_image_for_analysis
from src.core.photo.photo_loader import make_photo_id
from src.core.photo.photo_types import BodyScore, FaceScore, PhotoItem, PhotoScore, TechnicalScore
from src.core.photo.thumbnail_cache import build_thumbnail
from src.core.quality.technical_score import compute_technical_score
from src.core.scoring.final_score import compute_final_score
from src.core.subject.face_analyzer import analyze_face, detect_face_regions
from src.core.subject.person_blur_analyzer import analyze_person_body_blur


def _flat_score(technical: TechnicalScore) -> float:
    return round(max(0.0, min(1.0, technical.sharpness * 0.5 + technical.exposure * 0.3 + technical.contrast * 0.2)), 4)


def _phash_from_path(path: Path, max_size: int) -> str:
    with Image.open(path) as image:
        image.thumbnail((max_size, max_size))
        return str(imagehash.phash(image))


def photo_item_from_cache_record(record: AnalysisCacheRecord) -> PhotoItem:
    """Rebuild a PhotoItem from a valid cache record."""
    technical = TechnicalScore(**record.technical)
    face = FaceScore(**record.face)
    body = BodyScore(**record.body)
    item = PhotoItem(
        id=record.photo_id,
        path=record.path,
        file_name=Path(record.path).name,
        filename=Path(record.path).name,
        thumbnail_path=record.thumbnail_path,
        cluster_id=record.cluster_id,
        status=record.ai_status or "unprocessed",  # type: ignore[arg-type]
        score=PhotoScore(
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
            final_score=record.final_score,
        ),
    )
    item.metadata_dict.update(
        {
            "cache_hit": True,
            "cache_key": record.cache_key,
            "analysis_size": record.analysis_size,
            "phash": record.phash,
            "performance_mode": record.analysis_mode,
        }
    )
    return item


def cache_record_from_photo_item(
    item: PhotoItem,
    path: Path,
    config: PerformanceConfig,
) -> AnalysisCacheRecord:
    """Build a JSON-safe cache record from an analyzed PhotoItem."""
    stat = path.stat()
    return AnalysisCacheRecord(
        photo_id=item.id,
        path=str(path.resolve()),
        file_size=stat.st_size,
        mtime=stat.st_mtime,
        thumbnail_path=item.thumbnail_path,
        phash=item.metadata_dict.get("phash"),
        technical=dict(item.score.technical.__dict__),
        face=dict(item.score.face.__dict__),
        body=dict(item.score.body.__dict__),
        final_score=item.score.final_score,
        cluster_id=item.cluster_id,
        ai_status=item.status if item.status != "unprocessed" else None,
        analysis_mode=config.mode,
        analysis_size=config.max_analysis_size,
        cache_version=config.cache_version,
        scoring_version=config.scoring_version,
        cache_key=build_cache_key(path),
    )


def _neutral_face(reason_list: list[str]) -> FaceScore:
    reason_list.append("Face analysis skipped by performance settings")
    return FaceScore(face_detected=False, face_count=0, face_score=0.45, face_sharpness=0.45)


def _neutral_body(reason_list: list[str]) -> BodyScore:
    reason_list.append("Body blur analysis skipped by performance settings")
    return BodyScore(person_detected=False, body_sharpness=0.45, body_blur_penalty=0.0, subject_score=0.45)


def analyze_photo(
    path: Path,
    config: PerformanceConfig,
    cache: AnalysisCache | None = None,
    output_dir: Path | None = None,
) -> PhotoItem:
    """Analyze one photo using cache and resized analysis images."""
    image_path = Path(path)
    if config.use_cache and cache is not None:
        record = cache.get_valid(image_path, config)
        if record is not None:
            return photo_item_from_cache_record(record)

    reasons: list[str] = []
    image = load_image_for_analysis(image_path, config.max_analysis_size)
    height, width = image.shape[:2]
    item = PhotoItem(
        id=make_photo_id(image_path),
        path=image_path,
        file_name=image_path.name,
        filename=image_path.name,
        width=width,
        height=height,
    )

    if config.generate_thumbnails:
        item.thumbnail_path = str(build_thumbnail(image_path, output_dir))

    technical = compute_technical_score(image)
    face_regions = detect_face_regions(image) if config.enable_face_analysis or config.enable_body_blur_analysis else []
    face = analyze_face(image) if config.enable_face_analysis else _neutral_face(reasons)
    body = (
        analyze_person_body_blur(image, face_regions, enable_person_detection=False)
        if config.enable_body_blur_analysis
        else _neutral_body(reasons)
    )
    final = compute_final_score(technical, face, body, mode=config.mode if config.mode in {"balanced", "accurate"} else "conservative")
    phash = _phash_from_path(image_path, config.max_analysis_size)

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
        reasons=reasons,
    )
    item.scores = item.score
    item.metadata_dict.update(
        {
            "cache_hit": False,
            "cache_key": build_cache_key(image_path),
            "analysis_size": config.max_analysis_size,
            "phash": phash,
            "performance_mode": config.mode,
            "face_analysis_enabled": config.enable_face_analysis,
            "body_blur_analysis_enabled": config.enable_body_blur_analysis,
            "similarity_grouping_enabled": config.enable_similarity_grouping,
            "copy_files_after_culling": config.copy_files_after_culling,
        }
    )

    if config.use_cache and cache is not None:
        cache.set(image_path, cache_record_from_photo_item(item, image_path, config))
    return item


def error_photo_item(path: Path, message: str) -> PhotoItem:
    """Create a placeholder PhotoItem for a failed analysis."""
    item = PhotoItem(id=str(path.resolve()), path=path, file_name=path.name, filename=path.name, status="rejected")
    item.score.reasons = [f"Analysis failed: {message}"]
    item.metadata_dict["analysis_error"] = message
    return item
