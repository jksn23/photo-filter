"""Core image loader facade."""

from pathlib import Path

import numpy as np

from src.image_loader import load_image, scan_images


def load_image_array(path: Path) -> np.ndarray:
    """Load an image as an OpenCV BGR ndarray."""
    return load_image(str(path))


def scan_image_paths(input_dir: Path, recursive: bool = True) -> list[Path]:
    """Scan image files. Recursive scanning delegates to the existing safe scanner."""
    if recursive:
        from src.image_loader import list_image_files

        return [Path(path) for path in list_image_files(str(input_dir))]
    return scan_images(Path(input_dir))

