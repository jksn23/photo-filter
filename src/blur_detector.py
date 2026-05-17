"""Blur detection using variance of Laplacian."""

from pathlib import Path

import cv2
import numpy as np

from src.image_loader import load_image


def calculate_blur_score(image_or_path) -> float:
    """Calculate sharpness score using grayscale Laplacian variance."""
    image = load_image(str(Path(image_or_path))) if isinstance(image_or_path, (str, Path)) else image_or_path
    if image is None or not isinstance(image, np.ndarray):
        raise ValueError("File foto tidak dapat dibaca.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(blur_score: float, threshold: float = 100.0) -> bool:
    """Return True when the blur score is below the configured threshold."""
    return blur_score < threshold
