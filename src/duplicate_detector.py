"""Perceptual hash based duplicate grouping."""

from pathlib import Path

from PIL import Image, ImageOps
import imagehash


def calculate_image_hash(image_path: str):
    """Calculate a perceptual hash for one image path."""
    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        return imagehash.phash(image)


def group_duplicates(image_paths: list[str], threshold: int) -> dict[str, str | None]:
    """Group visually similar images and return path-to-group-id mapping."""
    normalized_paths = [str(Path(path)) for path in image_paths]
    result: dict[str, str | None] = {path: None for path in normalized_paths}
    hashes = {}

    for path in normalized_paths:
        try:
            hashes[path] = calculate_image_hash(path)
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
            if left_hash - hashes[right] <= threshold:
                union(left, right)

    grouped: dict[str, list[str]] = {}
    for path in paths_with_hashes:
        grouped.setdefault(find(path), []).append(path)

    duplicate_groups = [sorted(paths) for paths in grouped.values() if len(paths) > 1]
    duplicate_groups.sort(key=lambda paths: paths[0])

    for group_index, paths in enumerate(duplicate_groups, start=1):
        group_id = f"G{group_index:03d}"
        for path in paths:
            result[path] = group_id

    return result

