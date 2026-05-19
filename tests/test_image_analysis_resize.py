from pathlib import Path

from PIL import Image

from src.core.photo.image_loader import load_image_for_analysis


def test_large_image_resized_to_max_dimension_preserving_ratio(tmp_path: Path) -> None:
    path = tmp_path / "large.jpg"
    Image.new("RGB", (600, 400), color=(10, 20, 30)).save(path)

    image = load_image_for_analysis(path, 300)

    assert max(image.shape[:2]) == 300
    assert image.shape[1] == 300
    assert image.shape[0] == 200


def test_small_image_is_not_enlarged(tmp_path: Path) -> None:
    path = tmp_path / "small.jpg"
    Image.new("RGB", (120, 80), color=(10, 20, 30)).save(path)

    image = load_image_for_analysis(path, 300)

    assert image.shape[1] == 120
    assert image.shape[0] == 80
