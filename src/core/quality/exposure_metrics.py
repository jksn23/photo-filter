"""Exposure and contrast metrics."""

import cv2
import numpy as np


def grayscale(image: np.ndarray) -> np.ndarray:
    """Return grayscale image."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def exposure_score(image: np.ndarray) -> float:
    """Score exposure by average brightness and clipping."""
    gray = grayscale(image)
    brightness = float(gray.mean())
    highlight_clip = float((gray >= 245).mean())
    shadow_clip = float((gray <= 10).mean())
    center_score = 1.0 - min(abs(brightness - 128.0) / 128.0, 1.0)
    return max(0.0, min(1.0, center_score - (highlight_clip + shadow_clip) * 0.5))


def contrast_score(image: np.ndarray) -> float:
    """Score contrast from luminance standard deviation."""
    return max(0.0, min(1.0, float(np.std(grayscale(image))) / 80.0))

