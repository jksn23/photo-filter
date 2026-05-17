"""Human-aware blur analysis for detected person regions."""

from pathlib import Path

import cv2
import numpy as np

from src.image_loader import load_image
from src.person_detector import PersonBox, select_main_person_box


def _clip_box(image: np.ndarray, box: PersonBox) -> PersonBox | None:
    height, width = image.shape[:2]
    x, y, w, h = box
    x1 = max(0, min(int(x), width))
    y1 = max(0, min(int(y), height))
    x2 = max(0, min(int(x + w), width))
    y2 = max(0, min(int(y + h), height))
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2 - x1, y2 - y1


def calculate_blur_for_box(image: np.ndarray, box: PersonBox) -> float:
    """Calculate variance of Laplacian for one image crop."""
    clipped = _clip_box(image, box)
    if clipped is None:
        return 0.0

    x, y, w, h = clipped
    crop = image[y : y + h, x : x + w]
    if crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def calculate_person_blur_scores(
    image_path: Path,
    person_boxes: list[PersonBox],
) -> dict:
    """Calculate blur statistics for all detected person boxes."""
    image = load_image(str(Path(image_path)))
    height, width = image.shape[:2]
    main_box = select_main_person_box(person_boxes, width, height)
    scores = [calculate_blur_for_box(image, box) for box in person_boxes]
    scores = [score for score in scores if score > 0.0]

    main_score = calculate_blur_for_box(image, main_box) if main_box is not None else None
    return {
        "person_count": len(person_boxes),
        "main_person_blur_score": round(float(main_score), 2) if main_score is not None else None,
        "avg_person_blur_score": round(float(np.mean(scores)), 2) if scores else None,
        "min_person_blur_score": round(float(np.min(scores)), 2) if scores else None,
    }


def detect_localized_person_blur(
    image: np.ndarray,
    main_person_box: PersonBox,
    grid_rows: int = 3,
    grid_cols: int = 3,
    patch_blur_threshold: float = 75.0,
    min_blurry_patch_ratio: float = 0.25,
) -> bool:
    """Detect localized body blur by splitting the main person crop into a grid."""
    clipped = _clip_box(image, main_person_box)
    if clipped is None or grid_rows <= 0 or grid_cols <= 0:
        return False

    x, y, w, h = clipped
    crop = image[y : y + h, x : x + w]
    if crop.size == 0:
        return False

    blurry_patches = 0
    total_patches = 0
    for row in range(grid_rows):
        y1 = int(row * h / grid_rows)
        y2 = int((row + 1) * h / grid_rows)
        for col in range(grid_cols):
            x1 = int(col * w / grid_cols)
            x2 = int((col + 1) * w / grid_cols)
            patch = crop[y1:y2, x1:x2]
            if patch.size == 0:
                continue
            total_patches += 1
            score = calculate_blur_for_box(patch, (0, 0, patch.shape[1], patch.shape[0]))
            if score < patch_blur_threshold:
                blurry_patches += 1

    if total_patches == 0:
        return False
    return (blurry_patches / total_patches) >= min_blurry_patch_ratio

