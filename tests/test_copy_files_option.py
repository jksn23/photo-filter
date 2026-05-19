from pathlib import Path

from PIL import Image

from src.core.culling.culling_engine import run_culling_engine
from src.core.performance.performance_config import PerformanceConfig
from src.core.review.review_session import build_review_session


def test_copy_files_off_still_supports_review_session(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source = input_dir / "a.jpg"
    Image.new("RGB", (96, 96), color=(80, 90, 100)).save(source)

    items = run_culling_engine(
        input_dir,
        output_dir=output_dir,
        performance_config=PerformanceConfig(
            worker_count=1,
            enable_face_analysis=False,
            enable_body_blur_analysis=False,
            copy_files_after_culling=False,
        ),
        copy_files=False,
    )
    session = build_review_session(items, output_dir / "reports" / "final_decisions.json")

    assert not (output_dir / "01_SELECTED").exists()
    assert session.items[0].original_path == source
    assert source.exists()
