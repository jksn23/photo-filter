"""High-level cluster service."""

from pathlib import Path

from src.core.photo.photo_types import PhotoItem, PhotoCluster
from src.core.similarity.similarity_cluster import build_photo_clusters, cluster_paths_by_hash


def assign_similarity_clusters(items: list[PhotoItem], threshold: int = 8) -> list[PhotoCluster]:
    """Assign cluster ids to PhotoItem rows and return clusters."""
    paths = [Path(item.path) for item in items]
    groups = cluster_paths_by_hash(paths, threshold)
    id_by_path = {Path(item.path): item.id for item in items}
    clusters = build_photo_clusters(id_by_path, groups)
    for cluster in clusters:
        for item in items:
            if item.id in cluster.photo_ids:
                item.cluster_id = cluster.id
    return clusters

