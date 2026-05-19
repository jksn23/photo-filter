"""Data models for the CullaGrace V2 human review workflow."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


AIStatus = Literal["selected", "review", "rejected"]
FinalDecision = Literal["post", "save", "delete", "undecided"]

AI_STATUSES: tuple[AIStatus, ...] = ("selected", "review", "rejected")
FINAL_DECISIONS: tuple[FinalDecision, ...] = ("post", "save", "delete", "undecided")


@dataclass
class ReviewDecision:
    photo_id: str
    filename: str
    original_path: str
    ai_status: AIStatus
    final_decision: FinalDecision = "undecided"
    decision_source: str = "manual"
    decision_updated_at: str | None = None
    notes: str = ""


@dataclass
class ReviewItem:
    photo_id: str
    filename: str
    original_path: Path
    ai_status: AIStatus
    final_decision: FinalDecision = "undecided"
    cluster_id: str | None = None
    is_cluster_winner: bool = False
    final_score: float = 0.0
    face_score: float = 0.0
    body_sharpness: float = 0.0
    body_blur_penalty: float = 0.0
    thumbnail_path: Path | None = None
    reasons: list[str] = field(default_factory=list)
    decision_updated_at: str | None = None
    decision_source: str = "manual"
    notes: str = ""


@dataclass
class ReviewProgress:
    total: int = 0
    posts: int = 0
    save: int = 0
    delete: int = 0
    undecided: int = 0
    selected_total: int = 0
    review_total: int = 0
    rejected_total: int = 0


@dataclass
class ReviewSession:
    items: list[ReviewItem]
    decisions: dict[str, ReviewDecision] = field(default_factory=dict)
