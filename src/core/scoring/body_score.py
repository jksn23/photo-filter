"""Body and subject blur scoring."""

from pathlib import Path

from src.image_loader import load_image
from src.person_blur_analyzer import calculate_person_blur_scores, detect_localized_person_blur
from src.person_detector import detect_person_boxes, select_main_person_box


def _normalize_body_blur(score: float | None, reference_score: float = 180.0) -> float:
    if score is None:
        return 0.45
    return max(0.0, min(1.0, score / reference_score))


def calculate_body_score(
    image_path: Path,
    enabled: bool = True,
    confidence_threshold: float = 0.35,
    patch_blur_threshold: float = 75.0,
    localized_blur_patch_ratio: float = 0.25,
) -> dict:
    """Calculate body sharpness and body blur penalty."""
    if not enabled:
        return {
            "person_count": 0,
            "main_person_blur_score": None,
            "avg_person_blur_score": None,
            "min_person_blur_score": None,
            "localized_person_blur": False,
            "body_sharpness_score": 0.45,
            "body_blur_penalty": 0.0,
            "body_reason": "Body scoring disabled.",
        }

    try:
        boxes = detect_person_boxes(image_path, confidence_threshold=confidence_threshold)
        scores = calculate_person_blur_scores(image_path, boxes) if boxes else {
            "person_count": 0,
            "main_person_blur_score": None,
            "avg_person_blur_score": None,
            "min_person_blur_score": None,
        }
        image = load_image(str(image_path))
        height, width = image.shape[:2]
        main_box = select_main_person_box(boxes, width, height)
        localized_blur = (
            detect_localized_person_blur(
                image,
                main_box,
                patch_blur_threshold=patch_blur_threshold,
                min_blurry_patch_ratio=localized_blur_patch_ratio,
            )
            if main_box is not None
            else False
        )
        body_sharpness = _normalize_body_blur(scores["main_person_blur_score"])
        body_penalty = 0.35 if localized_blur else max(0.0, 0.45 - body_sharpness)
        return {
            **scores,
            "localized_person_blur": localized_blur,
            "body_sharpness_score": round(body_sharpness, 4),
            "body_blur_penalty": round(min(body_penalty, 1.0), 4),
            "body_reason": "Body scoring completed." if boxes else "No person detected; body score used fallback.",
        }
    except Exception as exc:
        return {
            "person_count": 0,
            "main_person_blur_score": None,
            "avg_person_blur_score": None,
            "min_person_blur_score": None,
            "localized_person_blur": False,
            "body_sharpness_score": 0.45,
            "body_blur_penalty": 0.0,
            "body_reason": f"Body scoring unavailable: {exc}",
        }

