"""Blur detection using variance of Laplacian."""

import cv2


def calculate_blur_score(image) -> float:
    """Calculate sharpness score using grayscale Laplacian variance."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(blur_score: float, threshold: float) -> bool:
    """Return True when the blur score is below the configured threshold."""
    return blur_score < threshold

