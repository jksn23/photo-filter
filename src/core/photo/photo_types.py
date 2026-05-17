"""Shared data models for the CullaGrace culling pipeline."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


PhotoStatus = Literal["unprocessed", "selected", "review", "rejected", "manual-selected", "manual-rejected"]
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
class TechnicalScore:
    sharpness: float = 0.0
    exposure: float = 0.0
    contrast: float = 0.0
    global_blur_penalty: float = 0.0


@dataclass
class FaceScore:
    face_detected: bool = False
    face_count: int = 0
    face_sharpness: float = 0.0
    face_score: float = 0.0


@dataclass
class BodyScore:
    person_detected: bool = False
    body_sharpness: float = 0.0
    body_blur_penalty: float = 0.0
    subject_score: float = 0.0


@dataclass
class PhotoScore:
    technical: TechnicalScore = field(default_factory=TechnicalScore)
    face: FaceScore = field(default_factory=FaceScore)
    body: BodyScore = field(default_factory=BodyScore)
    duplicate_penalty: float = 0.0
    reasons: list[str] = field(default_factory=list)
    technical_score: float = 0.0
    sharpness_score: float = 0.0
    exposure_score: float = 0.0
    contrast_score: float = 0.0
    blur_penalty: float = 0.0
    face_score: float | None = None
    face_sharpness: float | None = None
    eye_open_score: float | None = None
    body_sharpness_score: float | None = None
    body_blur_penalty: float | None = None
    aesthetic_score: float | None = None
    final_score: float = 0.0

    def __post_init__(self) -> None:
        if self.technical_score == 0.0 and any(
            [self.technical.sharpness, self.technical.exposure, self.technical.contrast]
        ):
            self.sharpness_score = self.technical.sharpness
            self.exposure_score = self.technical.exposure
            self.contrast_score = self.technical.contrast
            self.blur_penalty = self.technical.global_blur_penalty
            self.technical_score = (
                self.technical.sharpness * 0.5 + self.technical.exposure * 0.3 + self.technical.contrast * 0.2
            )
        if self.face_score is None:
            self.face_score = self.face.face_score
        if self.face_sharpness is None:
            self.face_sharpness = self.face.face_sharpness
        if self.body_sharpness_score is None:
            self.body_sharpness_score = self.body.body_sharpness
        if self.body_blur_penalty is None:
            self.body_blur_penalty = self.body.body_blur_penalty


@dataclass
class PhotoItem:
    id: str
    path: Path | str
    file_name: str
    filename: str | None = None
    thumbnail_path: str | None = None
    width: int | None = None
    height: int | None = None
    created_at: str | None = None
    metadata: PhotoMetadata | None = None
    status: PhotoStatus = "unprocessed"
    cluster_id: str | None = None
    scores: PhotoScore | None = None
    score: PhotoScore = field(default_factory=PhotoScore)
    reasons: list[CullingReason] = field(default_factory=list)
    metadata_dict: dict[str, Any] = field(default_factory=dict)
    is_cluster_winner: bool = False

    def __post_init__(self) -> None:
        if self.filename is None:
            self.filename = self.file_name
        if self.scores is None:
            self.scores = self.score
        else:
            self.score = self.scores


@dataclass
class PhotoCluster:
    id: str
    photo_ids: list[str]
    photos: list[PhotoItem] = field(default_factory=list)
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
