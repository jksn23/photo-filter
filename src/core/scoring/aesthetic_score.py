"""Optional aesthetic scoring adapter."""

from pathlib import Path


class AestheticScorer:
    """Disabled-by-default aesthetic scorer interface."""

    def score(self, photo_path: Path) -> float:
        """Return a neutral aesthetic score."""
        return 0.5

