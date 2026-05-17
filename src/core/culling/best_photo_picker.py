"""Best photo selection per similarity cluster."""

from src.core.culling.culling_reasons import negative, positive
from src.core.photo.photo_types import CullingMode, PhotoCluster, PhotoItem
from src.core.scoring.reason_builder import build_reasons


def _score(item: PhotoItem) -> float:
    return item.scores.final_score if item.scores else 0.0


def pick_best_photos_for_cluster(
    cluster: PhotoCluster,
    items_by_id: dict[str, PhotoItem],
    mode: CullingMode = "balanced",
    conservative_keep_delta: float = 0.08,
) -> PhotoCluster:
    """Mark selected/rejected items for one cluster according to mode."""
    items = [items_by_id[photo_id] for photo_id in cluster.photo_ids if photo_id in items_by_id]
    ranked = sorted(items, key=_score, reverse=True)
    if not ranked:
        return cluster

    best = ranked[0]
    keep_ids = {best.id}
    if mode == "conservative":
        keep_ids.update(item.id for item in ranked[1:3] if _score(best) - _score(item) <= conservative_keep_delta)
    elif mode == "balanced" and len(ranked) >= 4:
        keep_ids.update(item.id for item in ranked[1:2] if _score(best) - _score(item) <= conservative_keep_delta)

    cluster.selected_photo_id = best.id
    cluster.rejected_photo_ids = []
    for item in ranked:
        if item.id in keep_ids:
            item.status = "selected"
            item.reasons.append(
                positive("BEST_IN_CLUSTER", "Foto ini memiliki skor tertinggi dalam grup foto mirip.", _score(item))
            )
        else:
            item.status = "rejected"
            cluster.rejected_photo_ids.append(item.id)
            item.reasons.append(
                negative(
                    "LOWER_SCORE_THAN_SELECTED",
                    f"Foto ini mirip dengan {best.file_name}, tetapi skor akhirnya lebih rendah.",
                    _score(item),
                )
            )
    return cluster


def _thresholds(mode: str) -> tuple[float, float, float]:
    if mode == "conservative":
        return 0.55, 0.35, 0.12
    if mode == "aggressive":
        return 0.75, 0.55, 0.03
    return 0.65, 0.45, 0.08


def pick_best_photos(
    clusters: list[PhotoCluster],
    mode: str = "balanced",
    keep_per_cluster: int = 1,
) -> list[PhotoCluster]:
    """Pick selected/review/rejected photos for all clusters."""
    selected_threshold, review_threshold, close_gap = _thresholds(mode)
    for cluster in clusters:
        photos = cluster.photos
        if not photos:
            continue
        ranked = sorted(photos, key=lambda photo: photo.score.final_score, reverse=True)
        best = ranked[0]
        cluster.selected_photo_id = best.id
        cluster.rejected_photo_ids = []
        is_duplicate_cluster = len(ranked) > 1

        for index, photo in enumerate(ranked):
            photo.is_cluster_winner = index == 0
            if index == 0:
                photo.status = "selected" if photo.score.final_score >= selected_threshold else (
                    "review" if photo.score.final_score >= review_threshold else "rejected"
                )
            elif is_duplicate_cluster:
                score_gap = best.score.final_score - photo.score.final_score
                if mode == "conservative" and index < keep_per_cluster and score_gap <= close_gap:
                    photo.status = "review"
                elif mode == "balanced" and score_gap <= close_gap:
                    photo.status = "review"
                elif mode == "aggressive":
                    photo.status = "rejected"
                else:
                    photo.status = "review" if photo.score.final_score >= review_threshold else "rejected"
            else:
                photo.status = "selected" if photo.score.final_score >= selected_threshold else (
                    "review" if photo.score.final_score >= review_threshold else "rejected"
                )

            if photo.status == "rejected":
                cluster.rejected_photo_ids.append(photo.id)
            photo.score.reasons = build_reasons(photo, cluster)
            photo.reasons.clear()
            for reason in photo.score.reasons:
                if photo.status == "selected":
                    photo.reasons.append(positive("SELECTED_REASON", reason, photo.score.final_score))
                elif photo.status == "rejected":
                    photo.reasons.append(negative("REJECTED_REASON", reason, photo.score.final_score))
    return clusters
