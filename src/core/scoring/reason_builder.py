"""Human-readable decision reason builder."""

from src.core.photo.photo_types import PhotoCluster, PhotoItem


def _winner_for_cluster(photo: PhotoItem, cluster: PhotoCluster | None) -> PhotoItem | None:
    if cluster is None:
        return None
    selected_id = cluster.selected_photo_id
    for candidate in cluster.photos:
        if candidate.id == selected_id:
            return candidate
    return photo if photo.is_cluster_winner else None


def _score_gap(photo: PhotoItem, winner: PhotoItem | None) -> float:
    if winner is None or winner.id == photo.id:
        return 0.0
    return max(0.0, winner.score.final_score - photo.score.final_score)


def build_reasons(photo: PhotoItem, cluster: PhotoCluster | None = None, mode: str = "balanced") -> list[str]:
    """Build explainable selected/rejected/review reasons for a photo."""
    reasons: list[str] = []
    score = photo.score
    winner = _winner_for_cluster(photo, cluster)
    cluster_size = 0 if cluster is None else max(len(cluster.photos), len(cluster.photo_ids))
    is_unique = cluster is None or cluster_size <= 1

    if is_unique:
        reasons.append("Unique image; decision is based on its own technical, face, and body scores.")
    elif photo.is_cluster_winner or (winner and winner.id == photo.id):
        reasons.append("Selected as best image in similar cluster.")
    elif winner:
        gap = _score_gap(photo, winner)
        reasons.append(
            f"Similar to {winner.file_name}; final score lower by {gap:.2f}."
        )
        body_gap = score.body.body_blur_penalty - winner.score.body.body_blur_penalty
        if body_gap >= 0.08:
            reasons.append(f"Body blur penalty higher than winner by {body_gap:.2f}.")
        face_gap = winner.score.face.face_score - score.face.face_score
        if face_gap >= 0.08:
            reasons.append(f"Face score lower than winner by {face_gap:.2f}.")
        if gap <= 0.08 and photo.status == "review":
            reasons.append("Close candidate kept for manual review.")
        elif gap > 0.15:
            reasons.append("Large score gap from selected winner.")
    else:
        reasons.append("Similar cluster candidate; selected winner could not be resolved.")

    if mode == "aggressive" and photo.status == "rejected" and not photo.is_cluster_winner:
        reasons.append("Aggressive mode rejects duplicate alternatives unless they clearly win.")
    if mode == "conservative" and photo.status == "review" and not photo.is_cluster_winner:
        reasons.append("Conservative mode keeps close duplicate candidates for review.")

    if score.face.face_detected:
        if score.face.face_sharpness >= 0.55:
            reasons.append("Good face sharpness.")
        elif score.face.face_sharpness > 0:
            reasons.append("Face detected but face sharpness is weak.")
        else:
            reasons.append("Face detected.")
    else:
        reasons.append("No face detected.")

    if score.body.body_blur_penalty >= 0.45:
        reasons.append("Body/subject blur detected.")
    elif score.body.subject_score >= 0.65:
        reasons.append("Body/subject region is sharp.")

    if score.technical.global_blur_penalty >= 0.55:
        reasons.append("Low global sharpness.")
    elif score.technical.sharpness >= 0.65:
        reasons.append("Good global sharpness.")

    if score.technical.exposure >= 0.65:
        reasons.append("Good exposure.")
    elif score.technical.exposure < 0.30:
        reasons.append("Poor exposure.")

    return reasons
