"""Similarity clustering primitives."""

from pathlib import Path

from src.core.photo.photo_types import PhotoCluster
from src.core.similarity.perceptual_hash import generate_perceptual_hash, hamming_distance


def cluster_paths_by_hash(image_paths: list[Path], threshold: int = 8) -> dict[str, list[Path]]:
    """Cluster image paths by perceptual hash distance."""
    hashes: dict[Path, str] = {}
    for path in image_paths:
        try:
            hashes[path] = generate_perceptual_hash(path)
        except Exception:
            continue

    parent = {path: path for path in hashes}

    def find(path: Path) -> Path:
        while parent[path] != path:
            parent[path] = parent[parent[path]]
            path = parent[path]
        return path

    def union(left: Path, right: Path) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    paths = list(hashes)
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            if hamming_distance(hashes[left], hashes[right]) <= threshold:
                union(left, right)

    grouped: dict[Path, list[Path]] = {}
    for path in paths:
        grouped.setdefault(find(path), []).append(path)

    missing = [[path] for path in image_paths if path not in hashes]
    groups = [sorted(group, key=lambda item: item.name.lower()) for group in grouped.values()]
    groups.extend(missing)
    groups.sort(key=lambda group: group[0].name.lower())
    return {f"CL{index:04d}": group for index, group in enumerate(groups, start=1)}


def build_photo_clusters(photo_id_by_path: dict[Path, str], path_groups: dict[str, list[Path]]) -> list[PhotoCluster]:
    """Build PhotoCluster models from path groups."""
    clusters: list[PhotoCluster] = []
    for cluster_id, paths in path_groups.items():
        photo_ids = [photo_id_by_path[path] for path in paths if path in photo_id_by_path]
        if not photo_ids:
            continue
        clusters.append(
            PhotoCluster(
                id=cluster_id,
                photo_ids=photo_ids,
                rejected_photo_ids=[],
                confidence=1.0 if len(photo_ids) > 1 else 0.0,
            )
        )
    return clusters


def build_similarity_clusters(photo_items: list, threshold: int = 8) -> list[PhotoCluster]:
    """Build similarity clusters and assign cluster_id on PhotoItem objects."""
    paths = [Path(item.path) for item in photo_items]
    cached_hashes = {
        Path(item.path): str(item.metadata_dict.get("phash"))
        for item in photo_items
        if item.metadata_dict.get("phash")
    }
    if cached_hashes and len(cached_hashes) == len(paths):
        parent = {path: path for path in paths}

        def find(path: Path) -> Path:
            while parent[path] != path:
                parent[path] = parent[parent[path]]
                path = parent[path]
            return path

        def union(left: Path, right: Path) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        for index, left in enumerate(paths):
            for right in paths[index + 1 :]:
                if hamming_distance(cached_hashes[left], cached_hashes[right]) <= threshold:
                    union(left, right)
        grouped: dict[Path, list[Path]] = {}
        for path in paths:
            grouped.setdefault(find(path), []).append(path)
        groups_list = [sorted(group, key=lambda item: item.name.lower()) for group in grouped.values()]
        groups_list.sort(key=lambda group: group[0].name.lower())
        groups = {f"CL{index:04d}": group for index, group in enumerate(groups_list, start=1)}
    else:
        groups = cluster_paths_by_hash(paths, threshold)
    path_to_item = {Path(item.path): item for item in photo_items}
    clusters: list[PhotoCluster] = []
    for cluster_id, group_paths in groups.items():
        photos = [path_to_item[path] for path in group_paths if path in path_to_item]
        if not photos:
            continue
        for photo in photos:
            photo.cluster_id = cluster_id
        clusters.append(
            PhotoCluster(
                id=cluster_id,
                photo_ids=[photo.id for photo in photos],
                photos=photos,
                confidence=1.0 if len(photos) > 1 else 0.0,
            )
        )
    return clusters
