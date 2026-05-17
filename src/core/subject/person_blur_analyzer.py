"""Heuristic person/body blur analyzer."""

import cv2
import numpy as np

from src.core.photo.photo_types import BodyScore
from src.core.quality.blur_metrics import normalize_blur_score, variance_of_laplacian


def _central_subject_region(image: np.ndarray) -> tuple[int, int, int, int]:
    height, width = image.shape[:2]
    x = int(width * 0.2)
    y = int(height * 0.12)
    w = int(width * 0.6)
    h = int(height * 0.78)
    return x, y, w, h


def _mask_face_regions(region: np.ndarray, region_origin: tuple[int, int], face_regions: list[tuple[int, int, int, int]]) -> np.ndarray:
    masked = region.copy()
    ox, oy = region_origin
    for x, y, w, h in face_regions:
        rx1 = max(0, x - ox)
        ry1 = max(0, y - oy)
        rx2 = min(masked.shape[1], x + w - ox)
        ry2 = min(masked.shape[0], y + h - oy)
        if rx2 > rx1 and ry2 > ry1:
            cv2.rectangle(masked, (rx1, ry1), (rx2, ry2), (0, 0, 0), thickness=-1)
    return masked


def analyze_person_body_blur(
    image: np.ndarray,
    face_regions: list[tuple[int, int, int, int]] | None = None,
) -> BodyScore:
    """Estimate subject/body sharpness with a central-region heuristic."""
    if image.size == 0:
        return BodyScore()
    face_regions = face_regions or []
    x, y, w, h = _central_subject_region(image)
    region = image[y : y + h, x : x + w]
    if region.size == 0:
        return BodyScore()
    region = _mask_face_regions(region, (x, y), face_regions)
    body_sharpness = normalize_blur_score(variance_of_laplacian(region), reference=220.0)
    body_blur_penalty = max(0.0, min(1.0, 1.0 - body_sharpness))
    subject_score = max(0.0, min(1.0, body_sharpness - body_blur_penalty * 0.35))
    return BodyScore(
        person_detected=True,
        body_sharpness=round(body_sharpness, 4),
        body_blur_penalty=round(body_blur_penalty, 4),
        subject_score=round(subject_score, 4),
    )

