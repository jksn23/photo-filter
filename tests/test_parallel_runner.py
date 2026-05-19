from pathlib import Path

from PIL import Image

from src.core.performance.performance_config import PerformanceConfig
from src.core.pipeline.parallel_runner import analyze_photos_batch


def _image(path: Path) -> Path:
    Image.new("RGB", (96, 96), color=(50, 60, 70)).save(path)
    return path


def test_parallel_runner_sequential_and_parallel_progress(tmp_path: Path) -> None:
    paths = [_image(tmp_path / f"{index}.jpg") for index in range(3)]
    events = []

    sequential = analyze_photos_batch(
        paths,
        PerformanceConfig(worker_count=1, enable_face_analysis=False, enable_body_blur_analysis=False),
        cache=None,
        output_dir=tmp_path / ".cache",
        progress_callback=events.append,
    )
    parallel = analyze_photos_batch(
        paths,
        PerformanceConfig(worker_count=2, enable_face_analysis=False, enable_body_blur_analysis=False),
        cache=None,
        output_dir=tmp_path / ".cache",
    )

    assert len(sequential) == 3
    assert len(parallel) == 3
    assert len(events) == 3


def test_parallel_runner_error_does_not_stop_batch(tmp_path: Path) -> None:
    valid = _image(tmp_path / "valid.jpg")
    missing = tmp_path / "missing.jpg"

    items = analyze_photos_batch(
        [valid, missing],
        PerformanceConfig(worker_count=2, enable_face_analysis=False, enable_body_blur_analysis=False),
        cache=None,
        output_dir=tmp_path / ".cache",
    )

    assert len(items) == 2
    assert any(item.metadata_dict.get("analysis_error") for item in items)
