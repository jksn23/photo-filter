"""Explainable culling reasons."""

from src.core.photo.photo_types import CullingReason, PhotoItem


def positive(code: str, message: str, score: float | None = None) -> CullingReason:
    return CullingReason(type="positive", code=code, message=message, score=score)


def negative(code: str, message: str, score: float | None = None) -> CullingReason:
    return CullingReason(type="negative", code=code, message=message, score=score)


def neutral(code: str, message: str, score: float | None = None) -> CullingReason:
    return CullingReason(type="neutral", code=code, message=message, score=score)


def reason_text(item: PhotoItem) -> str:
    """Flatten reasons for CSV/UI display."""
    return " ".join(reason.message for reason in item.reasons)

