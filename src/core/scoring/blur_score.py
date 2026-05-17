"""Normalized sharpness and blur scoring."""

from pathlib import Path

from src.blur_detector import calculate_blur_score


def normalize_laplacian_score(raw_score: float, reference_score: float = 300.0) -> float:
    """Normalize a Laplacian variance score to 0.0-1.0."""
    return max(0.0, min(1.0, raw_score / reference_score))


def calculate_sharpness_score(image_path: Path) -> tuple[float, float]:
    """Return normalized sharpness and raw Laplacian score."""
    raw_score = calculate_blur_score(image_path)
    return normalize_laplacian_score(raw_score), raw_score


def calculate_blur_penalty(sharpness_score: float, threshold: float = 0.45) -> float:
    """Return penalty when normalized sharpness is below threshold."""
    if sharpness_score >= threshold:
        return 0.0
    return max(0.0, min(1.0, (threshold - sharpness_score) / threshold))

