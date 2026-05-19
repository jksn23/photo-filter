"""Cache data models for analysis results."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalysisCacheRecord:
    photo_id: str
    path: str
    file_size: int
    mtime: float
    thumbnail_path: str | None = None
    phash: str | None = None
    technical: dict[str, Any] = field(default_factory=dict)
    face: dict[str, Any] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)
    final_score: float = 0.0
    cluster_id: str | None = None
    ai_status: str | None = None
    analysis_mode: str = "balanced"
    analysis_size: int = 1600
    cache_version: str = "2.1"
    scoring_version: str = "2.1"
    cache_key: str | None = None
    cache_hit: bool = False
