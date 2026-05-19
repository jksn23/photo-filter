"""Core image loader facade."""

from pathlib import Path

import numpy as np
import cv2

from src.image_loader import load_image, scan_images


def load_image_array(path: Path) -> np.ndarray:
    """Load an image as an OpenCV BGR ndarray."""
    return load_image(str(path))


def resize_for_analysis(image: np.ndarray, max_size: int) -> np.ndarray:
    """Resize image so longest side is at most max_size while preserving aspect ratio."""
    if max_size <= 0:
        return image
    height, width = image.shape[:2]
    longest = max(width, height)
    if longest <= max_size:
        return image
    scale = max_size / float(longest)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


def load_image_for_analysis(path: Path, max_size: int) -> np.ndarray:
    """Load an image and resize it for routine analysis."""
    return resize_for_analysis(load_image_array(path), max_size)


def scan_image_paths(input_dir: Path, recursive: bool = True) -> list[Path]:
    """Scan image files. Recursive scanning delegates to the existing safe scanner."""
    if recursive:
        from src.image_loader import list_image_files

        return [Path(path) for path in list_image_files(str(input_dir))]
    return scan_images(Path(input_dir))
