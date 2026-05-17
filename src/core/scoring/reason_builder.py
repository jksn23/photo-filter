"""Human-readable reason builder."""

from src.core.photo.photo_types import PhotoCluster, PhotoItem


def build_reasons(photo: PhotoItem, cluster: PhotoCluster | None = None) -> list[str]:
    """Build explainable selected/rejected/review reasons for a photo."""
    reasons: list[str] = []
    score = photo.score
    if cluster is None or len(cluster.photo_ids) <= 1:
        reasons.append("Unique image")
    elif photo.is_cluster_winner or cluster.selected_photo_id == photo.id:
        reasons.append("Selected as best image in similar cluster")
    else:
        reasons.append("Rejected because similar photo has higher final score")

    if score.face.face_detected or (score.face_score or 0) > 0.5:
        reasons.append("Sharp face detected" if (score.face.face_sharpness or score.face_sharpness or 0) >= 0.45 else "Face detected")
    else:
        reasons.append("No face detected")

    if score.body.body_blur_penalty >= 0.45 or (score.body_blur_penalty or 0) >= 0.45:
        reasons.append("Body/subject blur detected")
    if score.technical.global_blur_penalty >= 0.55 or score.blur_penalty >= 0.55:
        reasons.append("Low global sharpness")
    if score.technical.exposure >= 0.65 or score.exposure_score >= 0.65:
        reasons.append("Good exposure")
    elif score.technical.exposure < 0.3 or score.exposure_score < 0.3:
        reasons.append("Underexposed or overexposed")

    return reasons

