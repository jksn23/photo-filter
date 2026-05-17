"""Utilities for discovering and loading image files."""

from pathlib import Path

import cv2
import numpy as np

from src.config import SUPPORTED_EXTENSIONS


def list_image_files(input_folder: str) -> list[str]:
    """Return supported image files in the input folder, recursively sorted."""
    folder = Path(input_folder).expanduser()
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError("Folder input tidak ditemukan.")

    extensions = {extension.lower() for extension in SUPPORTED_EXTENSIONS}
    return sorted(
        str(path)
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions
    )


def load_image(image_path: str):
    """Load an image with OpenCV, including Windows paths with non-ASCII text."""
    path = Path(image_path)
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("File foto tidak dapat dibaca.")
    return image

