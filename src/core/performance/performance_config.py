"""Performance configuration model for CullaGrace culling."""

from dataclasses import dataclass, replace
from typing import Literal


PerformanceMode = Literal["fast", "balanced", "accurate"]


@dataclass(frozen=True)
class PerformanceConfig:
    mode: PerformanceMode = "balanced"
    max_analysis_size: int = 1600
    worker_count: int | str = 4
    use_cache: bool = True
    enable_face_analysis: bool = True
    enable_body_blur_analysis: bool = True
    enable_similarity_grouping: bool = True
    copy_files_after_culling: bool = True
    generate_thumbnails: bool = True
    force_reanalyze: bool = False
    cache_version: str = "2.1"
    scoring_version: str = "2.1"

    def with_overrides(self, **kwargs) -> "PerformanceConfig":
        """Return a copy with selected values changed."""
        return replace(self, **kwargs)
