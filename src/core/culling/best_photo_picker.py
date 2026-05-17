"""Best photo selection per similarity cluster."""

from src.core.culling.culling_reasons import negative, positive
from src.core.photo.photo_types import CullingMode, PhotoCluster, PhotoItem


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

