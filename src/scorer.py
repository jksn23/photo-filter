"""Scoring and classification rules for culling results."""

from dataclasses import dataclass
from pathlib import Path

from src.exposure_detector import OVEREXPOSED, UNDEREXPOSED


@dataclass
class PhotoAnalysis:
    """Final analysis result for one photo in the simplified MVP contract."""

    path: Path
    filename: str
    blur_score: float
    is_blurry: bool
    brightness: float
    exposure_status: str
    face_count: int
    duplicate_group: str | None
    is_best_in_duplicate_group: bool
    final_score: int
    status: str
    person_count: int = 0
    main_person_blur_score: float | None = None
    avg_person_blur_score: float | None = None
    min_person_blur_score: float | None = None
    localized_person_blur: bool = False
    human_quality_score: int = 0
    duplicate_quality_rank: int | None = None
    is_best_duplicate: bool = False
    final_reason: str = ""
    thumbnail_path: str | None = None
    technical_score: float = 0.0
    sharpness_score: float = 0.0
    exposure_score: float = 0.0
    contrast_score: float = 0.0
    blur_penalty: float = 0.0
    face_score: float | None = None
    body_sharpness_score: float | None = None
    body_blur_penalty: float | None = None
    aesthetic_score: float | None = None
    culling_mode: str = "balanced"


def calculate_score(
    is_blurry: bool | None = None,
    exposure_status: str = "NORMAL",
    face_count: int = 0,
    is_duplicate_non_best: bool = False,
    is_best_in_duplicate_group: bool = False,
    **legacy_kwargs,
) -> int:
    """Calculate the final culling score using the default scoring rules."""
    if is_blurry is None:
        is_blurry = bool(legacy_kwargs.get("is_blur", False))
    if "is_duplicate_candidate" in legacy_kwargs and "best_in_duplicate_group" in legacy_kwargs:
        is_duplicate_non_best = bool(legacy_kwargs["is_duplicate_candidate"]) and not bool(
            legacy_kwargs["best_in_duplicate_group"]
        )
        is_best_in_duplicate_group = bool(legacy_kwargs["is_duplicate_candidate"]) and bool(
            legacy_kwargs["best_in_duplicate_group"]
        )

    normalized_exposure = exposure_status.upper()
    score = 100

    if is_blurry:
        score -= 40
    if normalized_exposure in {UNDEREXPOSED, OVEREXPOSED}:
        score -= 25
    if face_count > 0:
        score += 15
    else:
        score -= 10
    if is_duplicate_non_best:
        score -= 30
    if is_best_in_duplicate_group:
        score += 10

    return score


def classify_status(final_score: int | float, selected_min: int | float = 80, review_min: int | float = 50) -> str:
    """Classify a score into SELECTED, REVIEW, or REJECTED."""
    if final_score >= selected_min:
        return "SELECTED"
    if final_score >= review_min:
        return "REVIEW"
    return "REJECTED"


def calculate_human_quality_score(
    face_count: int,
    global_blur_score: float,
    main_person_blur_score: float | None,
    avg_person_blur_score: float | None,
    localized_person_blur: bool,
    exposure_status: str,
) -> int:
    """Calculate a human-subject quality score clamped to 0-150."""
    score = 100
    normalized_exposure = exposure_status.upper()

    score += 20 if face_count > 0 else -15

    if global_blur_score >= 180:
        score += 10
    elif global_blur_score >= 100:
        score += 0
    elif global_blur_score >= 50:
        score -= 25
    else:
        score -= 60

    if main_person_blur_score is None:
        score -= 10
    elif main_person_blur_score >= 150:
        score += 25
    elif main_person_blur_score >= 100:
        score += 10
    elif main_person_blur_score >= 60:
        score -= 25
    else:
        score -= 50

    if avg_person_blur_score is None:
        score += 0
    elif avg_person_blur_score >= 130:
        score += 10
    elif avg_person_blur_score >= 80:
        score += 0
    else:
        score -= 20

    if localized_person_blur:
        score -= 35

    if normalized_exposure in {UNDEREXPOSED, OVEREXPOSED}:
        score -= 15

    return max(0, min(150, int(score)))


def build_notes(
    is_blur: bool,
    exposure_status: str,
    face_count: int,
    is_duplicate_candidate: bool,
    best_in_duplicate_group: bool,
    error: str | None = None,
) -> str:
    """Build a compact notes string for CSV reporting."""
    if error:
        return f"error: {error}"

    notes = ["blur" if is_blur else "sharp"]
    normalized_exposure = exposure_status.upper()
    if normalized_exposure == UNDEREXPOSED:
        notes.append("underexposed")
    elif normalized_exposure == OVEREXPOSED:
        notes.append("overexposed")
    else:
        notes.append("normal_exposure")
    notes.append("has_face" if face_count > 0 else "no_face")

    if is_duplicate_candidate:
        notes.append("best_duplicate" if best_in_duplicate_group else "duplicate_candidate")

    return "; ".join(notes)
