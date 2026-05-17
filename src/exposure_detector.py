"""Exposure analysis helpers."""

from pathlib import Path

import cv2
import numpy as np

from src.image_loader import load_image


UNDEREXPOSED = "UNDEREXPOSED"
NORMAL = "NORMAL"
OVEREXPOSED = "OVEREXPOSED"


def calculate_brightness(image_or_path) -> float:
    """Calculate average grayscale brightness in the 0-255 range."""
    image = load_image(str(Path(image_or_path))) if isinstance(image_or_path, (str, Path)) else image_or_path
    if image is None or not isinstance(image, np.ndarray):
        raise ValueError("File foto tidak dapat dibaca.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def classify_exposure(
    brightness: float,
    under_threshold: float = 50.0,
    over_threshold: float = 210.0,
) -> str:
    """Classify brightness into underexposed, normal, or overexposed."""
    if brightness < under_threshold:
        return UNDEREXPOSED
    if brightness > over_threshold:
        return OVEREXPOSED
    return NORMAL
