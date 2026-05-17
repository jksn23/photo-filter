"""JSON analysis cache keyed by file metadata."""

from pathlib import Path
import json

from src.core.cache.cache_key import ensure_cache_root, file_cache_key


def _analysis_path(image_path: Path, cache_root: Path | None = None) -> Path:
    root = ensure_cache_root(cache_root) / "analysis"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{file_cache_key(Path(image_path))}.json"


def load_analysis_cache(image_path: Path, cache_root: Path | None = None) -> dict | None:
    """Load cached analysis for an unchanged file."""
    path = _analysis_path(image_path, cache_root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_analysis_cache(image_path: Path, analysis: dict, cache_root: Path | None = None) -> Path:
    """Persist analysis data for reuse."""
    path = _analysis_path(image_path, cache_root)
    path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    return path

