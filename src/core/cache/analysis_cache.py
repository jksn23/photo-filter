"""JSON analysis cache keyed by file metadata and performance config."""

from dataclasses import asdict
from pathlib import Path
import json

from src.core.cache.cache_key import build_cache_key, ensure_cache_root, file_cache_key
from src.core.cache.cache_types import AnalysisCacheRecord
from src.core.performance.performance_config import PerformanceConfig


def _record_from_dict(payload: dict) -> AnalysisCacheRecord:
    allowed = set(AnalysisCacheRecord.__dataclass_fields__)
    return AnalysisCacheRecord(**{key: value for key, value in payload.items() if key in allowed})


def is_cache_record_valid(record: AnalysisCacheRecord, path: Path, config: PerformanceConfig) -> bool:
    """Return True only when file metadata and analysis config match."""
    if config.force_reanalyze or not path.exists():
        return False
    stat = path.stat()
    return (
        str(Path(record.path).resolve()) == str(Path(path).resolve())
        and record.file_size == stat.st_size
        and record.mtime == stat.st_mtime
        and record.analysis_mode == config.mode
        and record.analysis_size == config.max_analysis_size
        and record.cache_version == config.cache_version
        and record.scoring_version == config.scoring_version
    )


class AnalysisCache:
    """JSON-readable analysis cache for expensive per-photo results."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.path = self.cache_dir / "analysis_cache.json"
        self.records: dict[str, AnalysisCacheRecord] = {}

    def load(self) -> None:
        if not self.path.exists():
            self.records = {}
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.records = {}
            return
        self.records = {
            key: _record_from_dict(value)
            for key, value in raw.items()
            if isinstance(value, dict)
        }

    def save(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {key: asdict(record) for key, record in sorted(self.records.items())}
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, path: Path) -> AnalysisCacheRecord | None:
        return self.records.get(build_cache_key(path))

    def set(self, path: Path, record: AnalysisCacheRecord) -> None:
        key = build_cache_key(path)
        record.cache_key = key
        self.records[key] = record

    def get_valid(self, path: Path, config: PerformanceConfig) -> AnalysisCacheRecord | None:
        record = self.get(path)
        if record and is_cache_record_valid(record, path, config):
            record.cache_hit = True
            return record
        return None

    def invalidate(self, path: Path) -> None:
        self.records.pop(build_cache_key(path), None)

    def clear(self) -> None:
        self.records = {}
        if self.path.exists():
            self.path.unlink()


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
