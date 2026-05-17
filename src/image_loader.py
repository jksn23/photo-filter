"""Utilities for discovering and loading image files."""

from pathlib import Path

import cv2
import numpy as np

from src.config import SUPPORTED_EXTENSIONS
from src.file_manager import normalize_user_path


EXCLUDED_OUTPUT_DIRS = {
    "01_SELECTED",
    "02_REVIEW",
    "03_REJECTED",
    "04_REPORT",
}


def _is_inside_generated_output(path: Path) -> bool:
    """Return True when a path is inside a generated culling output folder."""
    parts = set(path.parts)
    if parts.intersection(EXCLUDED_OUTPUT_DIRS):
        return True
    return any(part.upper().endswith("_CULLED") for part in path.parts)


def scan_images(input_dir: Path) -> list[Path]:
    """Return supported image files in a folder, sorted deterministically."""
    folder = normalize_user_path(input_dir)
    if folder is None:
        raise FileNotFoundError("Folder input tidak ditemukan.")
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError("Folder input tidak ditemukan.")

    extensions = {extension.lower() for extension in SUPPORTED_EXTENSIONS}
    return sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in extensions
        ),
        key=lambda path: path.name.lower(),
    )


def list_image_files(input_folder: str) -> list[str]:
    """Return supported image files in the input folder, recursively sorted."""
    folder = normalize_user_path(input_folder)
    if folder is None:
        raise FileNotFoundError("Folder input tidak ditemukan.")
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError("Folder input tidak ditemukan.")

    extensions = {extension.lower() for extension in SUPPORTED_EXTENSIONS}
    return sorted(
        str(path)
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions and not _is_inside_generated_output(path)
    )


def load_image(image_path: str):
    """Load an image with OpenCV, including Windows paths with non-ASCII text."""
    path = Path(image_path)
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("File foto tidak dapat dibaca.")
    return image
