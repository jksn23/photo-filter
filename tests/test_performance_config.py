from src.core.performance.presets import get_performance_preset
from src.core.performance.resource_limits import resolve_worker_count


def test_performance_presets_have_expected_core_values() -> None:
    fast = get_performance_preset("fast")
    balanced = get_performance_preset("balanced")
    accurate = get_performance_preset("accurate")

    assert fast.mode == "fast"
    assert fast.max_analysis_size == 1024
    assert fast.copy_files_after_culling is False
    assert fast.enable_body_blur_analysis is False
    assert balanced.mode == "balanced"
    assert balanced.max_analysis_size == 1600
    assert balanced.copy_files_after_culling is True
    assert accurate.mode == "accurate"
    assert accurate.max_analysis_size == 2400
    assert accurate.worker_count <= 2


def test_worker_count_caps_are_safe() -> None:
    assert resolve_worker_count("auto", "fast") <= 4
    assert resolve_worker_count("auto", "balanced") <= 4
    assert resolve_worker_count("auto", "accurate") <= 2
    assert resolve_worker_count(99, "accurate") == 2
    assert resolve_worker_count(0, "balanced") == 1
