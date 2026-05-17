"""Photo loading helpers that produce shared PhotoItem objects."""

from pathlib import Path
import hashlib

from PIL import Image

from src.core.photo.photo_metadata import read_photo_metadata
from src.core.photo.photo_types import PhotoItem
from src.image_loader import scan_images


def make_photo_id(path: Path) -> str:
    """Build a stable id from absolute path, size, and modified time."""
    stat = path.stat()
    key = f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def load_photo_items(input_dir: Path) -> list[PhotoItem]:
    """Scan a folder and return PhotoItem rows."""
    items: list[PhotoItem] = []
    for path in scan_images(input_dir):
        width = None
        height = None
        try:
            with Image.open(path) as image:
                width, height = image.size
        except Exception:
            pass
        stat = path.stat()
        items.append(
            PhotoItem(
                id=make_photo_id(path),
                path=str(path),
                file_name=path.name,
                width=width,
                height=height,
                created_at=str(stat.st_mtime),
                metadata=read_photo_metadata(path),
            )
        )
    return items

