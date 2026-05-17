"""Shared data models for the CullaGrace culling pipeline."""

from dataclasses import dataclass, field
from typing import Literal


PhotoStatus = Literal["unprocessed", "selected", "rejected", "manual-selected", "manual-rejected"]
CullingMode = Literal["conservative", "balanced", "aggressive"]
ReasonType = Literal["positive", "negative", "neutral"]


@dataclass
class PhotoMetadata:
    camera: str | None = None
    lens: str | None = None
    iso: int | None = None
    aperture: str | None = None
    shutter_speed: str | None = None
    focal_length: str | None = None
    date_taken: str | None = None


@dataclass
class CullingReason:
    type: ReasonType
    code: str
    message: str
    score: float | None = None


@dataclass
class PhotoScore:
    technical_score: float
    sharpness_score: float
    exposure_score: float
    contrast_score: float
    blur_penalty: float
    face_score: float | None = None
    face_sharpness: float | None = None
    eye_open_score: float | None = None
    body_sharpness_score: float | None = None
    body_blur_penalty: float | None = None
    aesthetic_score: float | None = None
    final_score: float = 0.0


@dataclass
class PhotoItem:
    id: str
    path: str
    file_name: str
    thumbnail_path: str | None = None
    width: int | None = None
    height: int | None = None
    created_at: str | None = None
    metadata: PhotoMetadata | None = None
    status: PhotoStatus = "unprocessed"
    cluster_id: str | None = None
    scores: PhotoScore | None = None
    reasons: list[CullingReason] = field(default_factory=list)


@dataclass
class PhotoCluster:
    id: str
    photo_ids: list[str]
    selected_photo_id: str | None = None
    rejected_photo_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class CullingSummary:
    total_photos: int
    selected_count: int
    rejected_count: int
    cluster_count: int
    mode: CullingMode


@dataclass
class CullingResult:
    selected: list[PhotoItem]
    rejected: list[PhotoItem]
    clusters: list[PhotoCluster]
    summary: CullingSummary

