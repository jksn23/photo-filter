from pathlib import Path
import json

from PIL import Image

from src.core.culling.culling_engine import run_culling_engine
from src.core.performance.performance_config import PerformanceConfig


def _image(path: Path, color: tuple[int, int, int]) -> Path:
    Image.new("RGB", (128, 96), color=color).save(path)
    return path


def test_culling_engine_accepts_performance_config_and_writes_metadata(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    _image(input_dir / "a.jpg", (100, 120, 140))
    _image(input_dir / "b.jpg", (150, 120, 90))
    messages = []
    config = PerformanceConfig(
        worker_count=1,
        enable_face_analysis=False,
        enable_body_blur_analysis=False,
        copy_files_after_culling=False,
    )

    items = run_culling_engine(
        input_dir,
        output_dir=output_dir,
        performance_config=config,
        copy_files=False,
        progress_callback=lambda current, total, message: messages.append(message),
    )

    report = sorted((output_dir / "04_REPORT").glob("culling_audit_*.json"))[-1]
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert len(items) == 2
    assert not (output_dir / "01_SELECTED").exists()
    assert payload["performance"]["copy_files_after_culling"] is False
    assert payload["performance"]["max_analysis_size"] == 1600
    assert payload["photos"][0]["cache_hit"] in {True, False}
    assert any("Analyzed" in message for message in messages)


def test_culling_engine_cache_hit_on_second_run(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    _image(input_dir / "a.jpg", (100, 120, 140))
    config = PerformanceConfig(
        worker_count=1,
        enable_face_analysis=False,
        enable_body_blur_analysis=False,
        copy_files_after_culling=False,
    )

    first = run_culling_engine(input_dir, output_dir=output_dir, performance_config=config, copy_files=False)
    second = run_culling_engine(input_dir, output_dir=output_dir, performance_config=config, copy_files=False)

    assert first[0].metadata_dict["cache_hit"] is False
    assert second[0].metadata_dict["cache_hit"] is True
