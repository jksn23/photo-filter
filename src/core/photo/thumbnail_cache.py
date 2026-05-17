"""Compatibility wrapper for thumbnail cache under core.photo."""

from pathlib import Path

from src.core.cache.thumbnail_cache import get_thumbnail_path


def build_thumbnail(image_path: Path, cache_root: Path | None = None) -> Path:
    """Create or reuse a thumbnail."""
    return get_thumbnail_path(image_path, cache_root)

