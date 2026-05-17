"""Blur metric helpers."""

import cv2
import numpy as np


def variance_of_laplacian(image: np.ndarray) -> float:
    """Return raw variance of Laplacian for an image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def tenengrad_score(image: np.ndarray) -> float:
    """Return Tenengrad/Sobel gradient score."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return float(np.mean(gx * gx + gy * gy))


def normalize_blur_score(raw_score: float, reference: float = 300.0) -> float:
    """Normalize a raw blur/sharpness metric to 0-1."""
    return max(0.0, min(1.0, raw_score / reference))

