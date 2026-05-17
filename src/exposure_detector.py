"""Exposure analysis helpers."""

import cv2


UNDEREXPOSED = "underexposed"
NORMAL = "normal"
OVEREXPOSED = "overexposed"


def calculate_brightness(image) -> float:
    """Calculate average grayscale brightness in the 0-255 range."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def classify_exposure(
    brightness: float,
    under_threshold: float,
    over_threshold: float,
) -> str:
    """Classify brightness into underexposed, normal, or overexposed."""
    if brightness < under_threshold:
        return UNDEREXPOSED
    if brightness > over_threshold:
        return OVEREXPOSED
    return NORMAL

