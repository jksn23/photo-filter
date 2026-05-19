from pathlib import Path
import os

from src.core.cache.analysis_cache import AnalysisCache, is_cache_record_valid
from src.core.cache.cache_types import AnalysisCacheRecord
from src.core.performance.performance_config import PerformanceConfig


def _record(path: Path, config: PerformanceConfig) -> AnalysisCacheRecord:
    stat = path.stat()
    return AnalysisCacheRecord(
        photo_id="photo-1",
        path=str(path.resolve()),
        file_size=stat.st_size,
        mtime=stat.st_mtime,
        analysis_mode=config.mode,
        analysis_size=config.max_analysis_size,
        cache_version=config.cache_version,
        scoring_version=config.scoring_version,
    )


def test_missing_cache_loads_empty_and_save_reload_works(tmp_path: Path) -> None:
    image = tmp_path / "a.jpg"
    image.write_text("one", encoding="utf-8")
    config = PerformanceConfig()
    cache = AnalysisCache(tmp_path / ".cache")

    cache.load()
    assert cache.records == {}
    cache.set(image, _record(image, config))
    cache.save()

    reloaded = AnalysisCache(tmp_path / ".cache")
    reloaded.load()
    assert reloaded.get_valid(image, config) is not None


def test_cache_invalidates_when_file_or_config_changes(tmp_path: Path) -> None:
    image = tmp_path / "a.jpg"
    image.write_text("one", encoding="utf-8")
    config = PerformanceConfig()
    record = _record(image, config)

    assert is_cache_record_valid(record, image, config)
    image.write_text("changed-size", encoding="utf-8")
    assert not is_cache_record_valid(record, image, config)

    image.write_text("one", encoding="utf-8")
    os.utime(image, (image.stat().st_atime, image.stat().st_mtime + 10))
    assert not is_cache_record_valid(record, image, config)

    fresh_record = _record(image, config)
    assert not is_cache_record_valid(fresh_record, image, config.with_overrides(mode="fast"))
    assert not is_cache_record_valid(fresh_record, image, config.with_overrides(max_analysis_size=1024))
    assert not is_cache_record_valid(fresh_record, image, config.with_overrides(force_reanalyze=True))
