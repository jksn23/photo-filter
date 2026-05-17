"""Lightweight subject/body blur analyzer with safe fallbacks."""

from collections.abc import Callable
from typing import Any

import cv2
import numpy as np

from src.core.photo.photo_types import BodyScore
from src.core.quality.blur_metrics import normalize_blur_score, variance_of_laplacian


Box = tuple[int, int, int, int]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _central_subject_regions(image: np.ndarray) -> list[Box]:
    height, width = image.shape[:2]
    return [
        (int(width * 0.20), int(height * 0.34), int(width * 0.60), int(height * 0.58)),
        (int(width * 0.28), int(height * 0.40), int(width * 0.44), int(height * 0.48)),
        (int(width * 0.12), int(height * 0.46), int(width * 0.76), int(height * 0.38)),
    ]


def _clip_box(box: Box, image_shape: tuple[int, ...]) -> Box | None:
    height, width = image_shape[:2]
    x, y, w, h = box
    x1 = max(0, int(x))
    y1 = max(0, int(y))
    x2 = min(width, int(x + w))
    y2 = min(height, int(y + h))
    if x2 <= x1 or y2 <= y1:
        return None
    clipped = (x1, y1, x2 - x1, y2 - y1)
    if clipped[2] * clipped[3] < max(64, width * height * 0.01):
        return None
    return clipped


def _detector_boxes(detector: Any, image: np.ndarray) -> list[Box]:
    if detector is None:
        return []
    try:
        if callable(detector):
            raw_boxes = detector(image)
        elif hasattr(detector, "detect"):
            raw_boxes = detector.detect(image)
        else:
            return []
    except Exception:
        return []

    boxes: list[Box] = []
    for raw_box in raw_boxes or []:
        if len(raw_box) < 4:
            continue
        x, y, w, h = raw_box[:4]
        boxes.append((int(x), int(y), int(w), int(h)))
    return boxes


def _mask_face_regions(region: np.ndarray, region_origin: tuple[int, int], face_regions: list[Box]) -> np.ndarray:
    masked = region.copy()
    ox, oy = region_origin
    for x, y, w, h in face_regions:
        rx1 = max(0, int(x - ox))
        ry1 = max(0, int(y - oy))
        rx2 = min(masked.shape[1], int(x + w - ox))
        ry2 = min(masked.shape[0], int(y + h - oy))
        if rx2 > rx1 and ry2 > ry1:
            cv2.rectangle(masked, (rx1, ry1), (rx2, ry2), (0, 0, 0), thickness=-1)
    return masked


def _tenengrad_score(region: np.ndarray) -> float:
    if region.size == 0:
        return 0.0
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if region.ndim == 3 else region
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = sobel_x * sobel_x + sobel_y * sobel_y
    return float(np.mean(magnitude))


def _region_sharpness(region: np.ndarray) -> float:
    if region.size == 0:
        return 0.0
    laplacian = normalize_blur_score(variance_of_laplacian(region), reference=220.0)
    tenengrad = normalize_blur_score(_tenengrad_score(region), reference=9000.0)
    return round(_clamp(laplacian * 0.65 + tenengrad * 0.35), 4)


def _analyze_regions(image: np.ndarray, boxes: list[Box], face_regions: list[Box]) -> list[float]:
    scores: list[float] = []
    for box in boxes:
        clipped = _clip_box(box, image.shape)
        if clipped is None:
            continue
        x, y, w, h = clipped
        region = image[y : y + h, x : x + w]
        masked = _mask_face_regions(region, (x, y), face_regions)
        scores.append(_region_sharpness(masked))
    return scores


def _robust_score(scores: list[float]) -> float:
    if not scores:
        return 0.0
    ordered = sorted(scores, reverse=True)
    if len(ordered) == 1:
        return ordered[0]
    return round(_clamp(ordered[0] * 0.70 + float(np.median(ordered)) * 0.30), 4)


def analyze_person_body_blur(
    image: np.ndarray,
    face_regions: list[Box] | None = None,
    enable_person_detection: bool = False,
    detector: Callable[[np.ndarray], list[Box]] | object | None = None,
) -> BodyScore:
    """Estimate body/subject sharpness without requiring a heavy detector.

    A supplied detector can provide person boxes. If no detector is supplied, or
    it fails, the analyzer falls back to weighted central subject regions.
    """
    if image.size == 0:
        return BodyScore()

    face_regions = face_regions or []
    person_boxes = _detector_boxes(detector, image) if enable_person_detection else []
    scores = _analyze_regions(image, person_boxes, face_regions)
    person_detected = bool(scores)

    if not scores:
        scores = _analyze_regions(image, _central_subject_regions(image), face_regions)

    body_sharpness = _robust_score(scores)
    body_blur_penalty = round(_clamp(1.0 - body_sharpness), 4)
    subject_score = round(_clamp(body_sharpness * 0.85 + (1.0 - body_blur_penalty) * 0.15), 4)
    return BodyScore(
        person_detected=person_detected or bool(scores),
        body_sharpness=body_sharpness,
        body_blur_penalty=body_blur_penalty,
        subject_score=subject_score,
    )
