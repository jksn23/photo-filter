"""Data models used by the culling pipeline."""

from dataclasses import asdict, dataclass


@dataclass
class PhotoAnalysisResult:
    """Analysis result for one photo file."""

    filename: str
    original_path: str
    output_status: str
    output_path: str | None
    blur_score: float | None
    is_blur: bool
    brightness_score: float | None
    exposure_status: str
    face_count: int
    has_face: bool
    duplicate_group_id: str | None
    is_duplicate_candidate: bool
    best_in_duplicate_group: bool
    final_score: float
    notes: str
    error: str | None = None
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

    def to_dict(self) -> dict:
        """Convert the result to a serializable dictionary."""
        return asdict(self)
