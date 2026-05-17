"""Perceptual hash based duplicate grouping."""

from pathlib import Path

from PIL import Image, ImageOps
import imagehash


def calculate_phash(image_path: Path) -> imagehash.ImageHash:
    """Calculate a perceptual hash for one image path."""
    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        return imagehash.phash(image)


def calculate_image_hash(image_path: str):
    """Backward-compatible alias for perceptual hash calculation."""
    return calculate_phash(Path(image_path))


def group_duplicates(
    image_paths: list[Path],
    hash_threshold: int = 8,
    threshold: int | None = None,
) -> dict[str, list[Path]]:
    """Group visually similar images and return group-id to image paths."""
    if threshold is not None:
        hash_threshold = threshold

    normalized_paths = [Path(path) for path in image_paths]
    hashes = {}

    for path in normalized_paths:
        try:
            hashes[path] = calculate_phash(path)
        except Exception:
            continue

    paths_with_hashes = list(hashes.keys())
    parent = {path: path for path in paths_with_hashes}

    def find(path: str) -> str:
        while parent[path] != path:
            parent[path] = parent[parent[path]]
            path = parent[path]
        return path

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for index, left in enumerate(paths_with_hashes):
        left_hash = hashes[left]
        for right in paths_with_hashes[index + 1 :]:
            if left_hash - hashes[right] <= hash_threshold:
                union(left, right)

    grouped: dict[Path, list[Path]] = {}
    for path in paths_with_hashes:
        grouped.setdefault(find(path), []).append(path)

    missing_hash_paths = [path for path in normalized_paths if path not in hashes]
    all_groups = [sorted(paths, key=lambda item: item.name.lower()) for paths in grouped.values()]
    all_groups.extend([[path] for path in missing_hash_paths])
    all_groups.sort(key=lambda paths: paths[0].name.lower())

    return {f"G{index:03d}": paths for index, paths in enumerate(all_groups, start=1)}


def map_duplicate_groups(image_paths: list[Path], hash_threshold: int = 8) -> dict[str, str | None]:
    """Return path-to-group-id mapping, only marking groups with duplicates."""
    grouped = group_duplicates(image_paths, hash_threshold)
    result: dict[str, str | None] = {str(Path(path)): None for path in image_paths}
    for group_id, paths in grouped.items():
        if len(paths) <= 1:
            continue
        for path in paths:
            result[str(path)] = group_id
    return result
