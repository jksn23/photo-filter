"""Core technical scoring using image arrays."""

import numpy as np

from src.core.photo.photo_types import TechnicalScore
from src.core.quality.blur_metrics import normalize_blur_score, variance_of_laplacian
from src.core.quality.exposure_metrics import contrast_score, exposure_score


def compute_technical_score(image: np.ndarray) -> TechnicalScore:
    """Compute normalized technical score components for an image."""
    sharpness = normalize_blur_score(variance_of_laplacian(image))
    exposure = exposure_score(image)
    contrast = contrast_score(image)
    global_blur_penalty = max(0.0, min(1.0, 1.0 - sharpness))
    return TechnicalScore(
        sharpness=round(sharpness, 4),
        exposure=round(exposure, 4),
        contrast=round(contrast, 4),
        global_blur_penalty=round(global_blur_penalty, 4),
    )

