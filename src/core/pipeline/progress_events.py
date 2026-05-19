"""Progress event data model."""

from dataclasses import dataclass


@dataclass
class ProgressEvent:
    stage: str
    current: int = 0
    total: int = 0
    message: str = ""
    filename: str | None = None
