"""Local thumbnail cache for responsive previews."""

from pathlib import Path

from PIL import Image, ImageOps

from src.core.cache.cache_key import ensure_cache_root, file_cache_key


def get_thumbnail_path(image_path: Path, cache_root: Path | None = None, size: tuple[int, int] = (360, 270)) -> Path:
    """Create or reuse a thumbnail for an image."""
    root = ensure_cache_root(cache_root) / "thumbnails"
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{file_cache_key(Path(image_path))}.jpg"
    if destination.exists():
        return destination

    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail(size)
        if image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")
        image.save(destination, "JPEG", quality=82)
    return destination

