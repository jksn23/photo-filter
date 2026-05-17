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

    def to_dict(self) -> dict:
        """Convert the result to a serializable dictionary."""
        return asdict(self)

