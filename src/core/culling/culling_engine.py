"""End-to-end modular culling engine."""

from pathlib import Path

from src.core.cache.analysis_cache import load_analysis_cache, save_analysis_cache
from src.core.cache.thumbnail_cache import get_thumbnail_path
from src.core.culling.best_photo_picker import pick_best_photos_for_cluster
from src.core.photo.photo_loader import load_photo_items
from src.core.photo.photo_types import CullingMode, CullingResult, CullingSummary, PhotoItem, PhotoScore
from src.core.scoring.aesthetic_score import AestheticScorer
from src.core.scoring.body_score import calculate_body_score
from src.core.scoring.face_score import calculate_face_score
from src.core.scoring.final_score import MODE_CONFIG, calculate_final_score
from src.core.scoring.technical_score import calculate_technical_score
from src.core.similarity.cluster_service import assign_similarity_clusters


def analyze_photo_item(
    item: PhotoItem,
    cache_root: Path | None = None,
    enable_body_scoring: bool = True,
    person_detection_confidence: float = 0.35,
    person_patch_blur_threshold: float = 75.0,
    localized_blur_patch_ratio: float = 0.25,
) -> PhotoItem:
    """Analyze one photo with cache support."""
    path = Path(item.path)
    item.thumbnail_path = str(get_thumbnail_path(path, cache_root))
    cached = load_analysis_cache(path, cache_root)
    if cached:
        item.scores = PhotoScore(**cached["scores"])
        return item

    technical = calculate_technical_score(path)
    face = calculate_face_score(path)
    body = calculate_body_score(
        path,
        enabled=enable_body_scoring,
        confidence_threshold=person_detection_confidence,
        patch_blur_threshold=person_patch_blur_threshold,
        localized_blur_patch_ratio=localized_blur_patch_ratio,
    )
    aesthetic_score = AestheticScorer().score(path)
    final_score = calculate_final_score(
        technical_score=technical["technical_score"],
        face_score=face["face_score"],
        body_sharpness_score=body["body_sharpness_score"],
        body_blur_penalty=body["body_blur_penalty"],
        aesthetic_score=aesthetic_score,
        config=MODE_CONFIG["balanced"],
    )
    item.scores = PhotoScore(
        technical_score=technical["technical_score"],
        sharpness_score=technical["sharpness_score"],
        exposure_score=technical["exposure_score"],
        contrast_score=technical["contrast_score"],
        blur_penalty=technical["blur_penalty"],
        face_score=face["face_score"],
        face_sharpness=face["face_sharpness"],
        eye_open_score=face["eye_open_score"],
        body_sharpness_score=body["body_sharpness_score"],
        body_blur_penalty=body["body_blur_penalty"],
        aesthetic_score=aesthetic_score,
        final_score=final_score,
    )
    save_analysis_cache(path, {"scores": item.scores.__dict__}, cache_root)
    return item


def run_core_culling_engine(
    input_dir: Path,
    mode: CullingMode = "balanced",
    similarity_threshold: int = 8,
    cache_root: Path | None = None,
    enable_body_scoring: bool = True,
) -> CullingResult:
    """Run the modular culling engine from folder import to selected/rejected."""
    items = load_photo_items(Path(input_dir))
    for item in items:
        analyze_photo_item(item, cache_root=cache_root, enable_body_scoring=enable_body_scoring)

    clusters = assign_similarity_clusters(items, similarity_threshold)
    items_by_id = {item.id: item for item in items}
    config = MODE_CONFIG.get(mode, MODE_CONFIG["balanced"])
    for cluster in clusters:
        pick_best_photos_for_cluster(cluster, items_by_id, mode=mode, conservative_keep_delta=config.conservative_keep_score_delta)

    selected = [item for item in items if item.status == "selected"]
    rejected = [item for item in items if item.status == "rejected"]
    summary = CullingSummary(
        total_photos=len(items),
        selected_count=len(selected),
        rejected_count=len(rejected),
        cluster_count=len(clusters),
        mode=mode,
    )
    return CullingResult(selected=selected, rejected=rejected, clusters=clusters, summary=summary)

