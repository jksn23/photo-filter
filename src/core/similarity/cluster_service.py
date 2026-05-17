"""High-level cluster service."""

from pathlib import Path

from src.core.photo.photo_types import PhotoItem, PhotoCluster
from src.core.similarity.similarity_cluster import build_similarity_clusters


def assign_similarity_clusters(items: list[PhotoItem], threshold: int = 8) -> list[PhotoCluster]:
    """Assign cluster ids to PhotoItem rows and return clusters."""
    return build_similarity_clusters(items, threshold)
