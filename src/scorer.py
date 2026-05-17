"""Scoring and classification rules for culling results."""

from src.exposure_detector import OVEREXPOSED, UNDEREXPOSED


def calculate_score(
    is_blur: bool,
    exposure_status: str,
    face_count: int,
    is_duplicate_candidate: bool,
    best_in_duplicate_group: bool,
) -> float:
    """Calculate the final culling score using the default scoring rules."""
    score = 100.0

    if is_blur:
        score -= 40
    if exposure_status in {UNDEREXPOSED, OVEREXPOSED}:
        score -= 25
    if face_count > 0:
        score += 15
    else:
        score -= 10
    if is_duplicate_candidate and not best_in_duplicate_group:
        score -= 30
    if is_duplicate_candidate and best_in_duplicate_group:
        score += 10

    return score


def classify_status(final_score: float, selected_min: float, review_min: float) -> str:
    """Classify a score into SELECTED, REVIEW, or REJECTED."""
    if final_score >= selected_min:
        return "SELECTED"
    if final_score >= review_min:
        return "REVIEW"
    return "REJECTED"


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
    if exposure_status == UNDEREXPOSED:
        notes.append("underexposed")
    elif exposure_status == OVEREXPOSED:
        notes.append("overexposed")
    else:
        notes.append("normal_exposure")
    notes.append("has_face" if face_count > 0 else "no_face")

    if is_duplicate_candidate:
        notes.append("best_duplicate" if best_in_duplicate_group else "duplicate_candidate")

    return "; ".join(notes)

