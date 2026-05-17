"""Technical photo quality scoring."""

from pathlib import Path

import cv2
import numpy as np

from src.core.scoring.blur_score import calculate_blur_penalty, calculate_sharpness_score
from src.image_loader import load_image


def calculate_exposure_score(image_path: Path) -> float:
    """Score exposure using brightness histogram clipping and average luminance."""
    image = load_image(str(image_path))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    highlight_clip = float((gray >= 245).mean())
    shadow_clip = float((gray <= 10).mean())
    center_score = 1.0 - min(abs(brightness - 128.0) / 128.0, 1.0)
    clipping_penalty = min(highlight_clip + shadow_clip, 1.0)
    return max(0.0, min(1.0, center_score - clipping_penalty * 0.5))


def calculate_contrast_score(image_path: Path) -> float:
    """Score contrast from grayscale standard deviation."""
    image = load_image(str(image_path))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return max(0.0, min(1.0, float(np.std(gray)) / 80.0))


def calculate_technical_score(image_path: Path, sharpness_blur_threshold: float = 0.45) -> dict:
    """Calculate normalized technical score components."""
    sharpness_score, raw_blur_score = calculate_sharpness_score(image_path)
    exposure_score = calculate_exposure_score(image_path)
    contrast_score = calculate_contrast_score(image_path)
    blur_penalty = calculate_blur_penalty(sharpness_score, sharpness_blur_threshold)
    technical_score = sharpness_score * 0.5 + exposure_score * 0.3 + contrast_score * 0.2 - blur_penalty
    return {
        "technical_score": round(max(0.0, min(1.0, technical_score)), 4),
        "sharpness_score": round(sharpness_score, 4),
        "raw_blur_score": round(raw_blur_score, 2),
        "exposure_score": round(exposure_score, 4),
        "contrast_score": round(contrast_score, 4),
        "blur_penalty": round(blur_penalty, 4),
    }

