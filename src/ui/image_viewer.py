"""Image display helpers for the CullaGrace review UI."""

from __future__ import annotations

from pathlib import Path
import os
import platform
import subprocess
from typing import Any

from PIL import Image


def _path_or_none(value: Any) -> Path | None:
    if value is None:
        return None
    path = Path(str(value))
    return path if str(path) else None


def _get_attr(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def get_review_thumbnail_path(item: Any) -> Path | None:
    """Return the existing thumbnail path for a review item, if available."""
    path = _path_or_none(_get_attr(item, "thumbnail_path"))
    return path if path and path.exists() else None


def get_review_original_path(item: Any) -> Path:
    """Return the original image path for a review item."""
    return _path_or_none(_get_attr(item, "original_path")) or Path("")


def get_display_path(item: Any, prefer_thumbnail: bool = True) -> tuple[Path | None, str]:
    """Return a display path and mode label for grid/detail image rendering."""
    thumbnail = get_review_thumbnail_path(item)
    original = get_review_original_path(item)
    original_exists = original.exists()

    if prefer_thumbnail and thumbnail is not None:
        return thumbnail, "Thumbnail Preview"
    if original_exists:
        return original, "Original Image"
    if thumbnail is not None:
        return thumbnail, "Thumbnail Preview Fallback"
    return None, "Unavailable"


def get_image_resolution(path: Path) -> tuple[int, int] | None:
    """Return image width and height without crashing on missing/invalid files."""
    if not path.exists():
        return None
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def crop_original_image(
    image_path: Path,
    center_x_ratio: float = 0.5,
    center_y_ratio: float = 0.5,
    crop_size: int = 768,
) -> Image.Image | None:
    """Create a bounded crop from the original image."""
    if not image_path.exists():
        return None
    try:
        with Image.open(image_path) as image:
            source = image.convert("RGB")
            width, height = source.size
            size = max(1, min(int(crop_size), width, height))
            center_x = int(width * max(0.0, min(1.0, center_x_ratio)))
            center_y = int(height * max(0.0, min(1.0, center_y_ratio)))
            left = max(0, min(width - size, center_x - size // 2))
            top = max(0, min(height - size, center_y - size // 2))
            return source.crop((left, top, left + size, top + size))
    except Exception:
        return None


def crop_body_subject_image(image_path: Path, crop_size: int = 1024) -> Image.Image | None:
    """Create a center-weighted subject/body crop from the original image."""
    return crop_original_image(
        image_path,
        center_x_ratio=0.5,
        center_y_ratio=0.55,
        crop_size=crop_size,
    )


def open_local_file(path: Path) -> tuple[bool, str]:
    """Open a local file using the host OS file association."""
    if not path.exists() or not path.is_file():
        return False, f"File tidak ditemukan: {path}"
    return _open_path(path)


def open_local_folder(path: Path) -> tuple[bool, str]:
    """Open a local folder using the host OS file manager."""
    folder = path if path.is_dir() else path.parent
    if not folder.exists():
        return False, f"Folder tidak ditemukan: {folder}"
    return _open_path(folder)


def _open_path(path: Path) -> tuple[bool, str]:
    try:
        system_name = platform.system()
        if system_name == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        elif system_name == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return True, f"Dibuka: {path}"
    except Exception as exc:
        return False, f"Tidak dapat membuka path: {exc}. Path: {path}"
