"""Final score combination and culling configuration."""

from dataclasses import dataclass

from src.core.photo.photo_types import BodyScore, CullingMode, FaceScore, TechnicalScore


@dataclass
class CullingConfig:
    mode: CullingMode = "balanced"
    similarity_threshold: int = 8
    sharpness_blur_threshold: float = 0.45
    body_blur_threshold: float = 0.45
    face_score_weight: float = 0.3
    body_score_weight: float = 0.25
    technical_score_weight: float = 0.3
    aesthetic_score_weight: float = 0.1
    conservative_keep_score_delta: float = 0.08


DEFAULT_CULLING_CONFIG = CullingConfig()


MODE_CONFIG = {
    "conservative": CullingConfig(mode="conservative", conservative_keep_score_delta=0.12),
    "balanced": DEFAULT_CULLING_CONFIG,
    "aggressive": CullingConfig(mode="aggressive", conservative_keep_score_delta=0.03),
}


def calculate_final_score(
    technical_score: float,
    face_score: float | None,
    body_sharpness_score: float | None,
    body_blur_penalty: float | None,
    aesthetic_score: float | None = None,
    config: CullingConfig = DEFAULT_CULLING_CONFIG,
) -> float:
    """Combine normalized score components into a final 0.0-1.0 score."""
    face_value = 0.45 if face_score is None else face_score
    body_value = 0.45 if body_sharpness_score is None else body_sharpness_score
    aesthetic_value = 0.5 if aesthetic_score is None else aesthetic_score
    body_penalty = 0.0 if body_blur_penalty is None else body_blur_penalty
    aesthetic_weight = config.aesthetic_score_weight
    if body_penalty > 0.35:
        aesthetic_weight = min(aesthetic_weight, 0.03)
    score = (
        technical_score * config.technical_score_weight
        + face_value * config.face_score_weight
        + body_value * config.body_score_weight
        + aesthetic_value * aesthetic_weight
        - body_penalty * 0.2
    )
    return round(max(0.0, min(1.0, score)), 4)


def compute_final_score(
    technical: TechnicalScore,
    face: FaceScore,
    body: BodyScore,
    mode: str = "balanced",
) -> float:
    """Compute mode-aware final score from nested score models."""
    config = MODE_CONFIG.get(mode, MODE_CONFIG["balanced"])
    face_weight = config.face_score_weight
    body_weight = 0.30 if mode in {"balanced", "aggressive"} else config.body_score_weight
    technical_weight = config.technical_score_weight
    body_value = body.subject_score
    if body_value == 0.0 and (body.body_sharpness or body.body_blur_penalty):
        body_value = max(0.0, min(1.0, body.body_sharpness - body.body_blur_penalty * 0.35))
    body_penalty_weight = 0.2
    blur_penalty_weight = 0.15
    if mode == "conservative":
        body_penalty_weight = 0.14
        blur_penalty_weight = 0.10
    elif mode == "aggressive":
        body_penalty_weight = 0.28
        blur_penalty_weight = 0.22

    score = (
        0.30 * technical.sharpness
        + 0.20 * technical.exposure
        + 0.10 * technical.contrast
        + face_weight * face.face_score
        + body_weight * body_value
        - blur_penalty_weight * technical.global_blur_penalty
        - body_penalty_weight * body.body_blur_penalty
    )
    # Keep configured weights visible to callers while following the requested formula.
    _ = technical_weight
    return round(max(0.0, min(1.0, score)), 4)
