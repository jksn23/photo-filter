"""Performance mode presets."""

from src.core.performance.performance_config import PerformanceConfig
from src.core.performance.resource_limits import resolve_worker_count


def get_performance_preset(mode: str) -> PerformanceConfig:
    """Return a safe performance preset for Fast, Balanced, or Accurate mode."""
    normalized = str(mode or "balanced").lower()
    if normalized == "fast":
        return PerformanceConfig(
            mode="fast",
            max_analysis_size=1024,
            worker_count=resolve_worker_count("auto", "fast"),
            use_cache=True,
            enable_face_analysis=True,
            enable_body_blur_analysis=False,
            enable_similarity_grouping=True,
            copy_files_after_culling=False,
            generate_thumbnails=True,
        )
    if normalized == "accurate":
        return PerformanceConfig(
            mode="accurate",
            max_analysis_size=2400,
            worker_count=resolve_worker_count("auto", "accurate"),
            use_cache=True,
            enable_face_analysis=True,
            enable_body_blur_analysis=True,
            enable_similarity_grouping=True,
            copy_files_after_culling=True,
            generate_thumbnails=True,
        )
    return PerformanceConfig(
        mode="balanced",
        max_analysis_size=1600,
        worker_count=resolve_worker_count("auto", "balanced"),
        use_cache=True,
        enable_face_analysis=True,
        enable_body_blur_analysis=True,
        enable_similarity_grouping=True,
        copy_files_after_culling=True,
        generate_thumbnails=True,
    )
