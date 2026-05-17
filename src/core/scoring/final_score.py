"""Final score combination and culling configuration."""

from dataclasses import dataclass

from src.core.photo.photo_types import CullingMode


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

