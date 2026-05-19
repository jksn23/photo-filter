"""Batch photo analysis with controlled workers."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from src.core.cache.analysis_cache import AnalysisCache
from src.core.performance.performance_config import PerformanceConfig
from src.core.performance.resource_limits import resolve_worker_count
from src.core.photo.photo_types import PhotoItem
from src.core.pipeline.photo_analyzer import analyze_photo, error_photo_item
from src.core.pipeline.progress_events import ProgressEvent


ProgressCallback = Callable[[ProgressEvent], None]


def _emit(callback: ProgressCallback | None, event: ProgressEvent) -> None:
    if callback:
        callback(event)


def _analyze_one(path: Path, config: PerformanceConfig, cache: AnalysisCache | None, output_dir: Path | None) -> PhotoItem:
    try:
        return analyze_photo(path, config, cache=cache, output_dir=output_dir)
    except Exception as exc:
        return error_photo_item(path, str(exc))


def analyze_photos_batch(
    paths: list[Path],
    config: PerformanceConfig,
    cache: AnalysisCache | None,
    output_dir: Path | None,
    progress_callback: ProgressCallback | None = None,
) -> list[PhotoItem]:
    """Analyze photos sequentially or with a bounded ThreadPoolExecutor."""
    total = len(paths)
    workers = resolve_worker_count(config.worker_count, config.mode)
    if workers == 1 or total <= 1:
        items: list[PhotoItem] = []
        for index, path in enumerate(paths, start=1):
            item = _analyze_one(path, config, cache, output_dir)
            items.append(item)
            _emit(
                progress_callback,
                ProgressEvent("analyzing", index, total, f"Analyzed {path.name} ({index}/{total})", path.name),
            )
        return items

    indexed_results: dict[int, PhotoItem] = {}
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_by_index = {
            executor.submit(_analyze_one, path, config, cache, output_dir): index
            for index, path in enumerate(paths)
        }
        for future in as_completed(future_by_index):
            index = future_by_index[future]
            item = future.result()
            indexed_results[index] = item
            completed += 1
            _emit(
                progress_callback,
                ProgressEvent(
                    "analyzing",
                    completed,
                    total,
                    f"Analyzed {item.file_name} ({completed}/{total})",
                    item.file_name,
                ),
            )
    return [indexed_results[index] for index in sorted(indexed_results)]
