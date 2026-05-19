from pathlib import Path

from PIL import Image

from src.core.cache.analysis_cache import AnalysisCache
from src.core.performance.performance_config import PerformanceConfig
from src.core.pipeline.photo_analyzer import analyze_photo


def _image(path: Path) -> Path:
    Image.new("RGB", (160, 120), color=(100, 120, 140)).save(path)
    return path


def test_photo_analyzer_writes_and_uses_cache(tmp_path: Path, monkeypatch) -> None:
    path = _image(tmp_path / "a.jpg")
    config = PerformanceConfig(worker_count=1, enable_face_analysis=False, enable_body_blur_analysis=False)
    cache = AnalysisCache(tmp_path / ".cache")
    cache.load()

    first = analyze_photo(path, config, cache=cache, output_dir=tmp_path / ".cache")
    cache.save()
    assert first.metadata_dict["cache_hit"] is False

    reloaded = AnalysisCache(tmp_path / ".cache")
    reloaded.load()

    def fail_load(*args, **kwargs):
        raise AssertionError("cache hit should not load image")

    monkeypatch.setattr("src.core.pipeline.photo_analyzer.load_image_for_analysis", fail_load)
    second = analyze_photo(path, config, cache=reloaded, output_dir=tmp_path / ".cache")

    assert second.metadata_dict["cache_hit"] is True
    assert second.score.final_score == first.score.final_score


def test_photo_analyzer_feature_toggles_are_neutral_and_no_arrays_stored(tmp_path: Path) -> None:
    path = _image(tmp_path / "a.jpg")
    config = PerformanceConfig(enable_face_analysis=False, enable_body_blur_analysis=False, generate_thumbnails=False)

    item = analyze_photo(path, config, cache=None, output_dir=tmp_path / ".cache")

    assert item.score.face.face_score == 0.45
    assert item.score.body.subject_score == 0.45
    assert item.thumbnail_path is None
    assert not hasattr(item, "image")
    assert any("Face analysis skipped" in reason for reason in item.score.reasons)
    assert any("Body blur analysis skipped" in reason for reason in item.score.reasons)
