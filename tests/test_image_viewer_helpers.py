from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from src.ui.image_viewer import (
    crop_original_image,
    get_display_path,
    get_image_resolution,
    get_review_original_path,
    get_review_thumbnail_path,
)


@dataclass
class FakeReviewItem:
    original_path: Path
    thumbnail_path: Path | None = None


def _image(path: Path, size: tuple[int, int] = (1200, 800)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=(20, 40, 80)).save(path)
    return path


def test_get_image_resolution_returns_width_and_height(tmp_path: Path) -> None:
    path = _image(tmp_path / "original.jpg", size=(600, 400))

    assert get_image_resolution(path) == (600, 400)


def test_crop_original_image_returns_bounded_crop_size(tmp_path: Path) -> None:
    path = _image(tmp_path / "original.jpg", size=(600, 400))

    crop = crop_original_image(path, center_x_ratio=0.95, center_y_ratio=0.05, crop_size=512)

    assert crop is not None
    assert crop.size == (400, 400)


def test_crop_original_image_handles_small_images_and_missing_files(tmp_path: Path) -> None:
    small = _image(tmp_path / "small.jpg", size=(120, 90))

    crop = crop_original_image(small, crop_size=768)

    assert crop is not None
    assert crop.size == (90, 90)
    assert crop_original_image(tmp_path / "missing.jpg") is None
    assert get_image_resolution(tmp_path / "missing.jpg") is None


def test_thumbnail_and_original_path_selection(tmp_path: Path) -> None:
    original = _image(tmp_path / "original.jpg")
    thumbnail = _image(tmp_path / "thumb.jpg", size=(100, 100))
    item = FakeReviewItem(original_path=original, thumbnail_path=thumbnail)

    thumb_path, thumb_label = get_display_path(item, prefer_thumbnail=True)
    original_path, original_label = get_display_path(item, prefer_thumbnail=False)

    assert get_review_thumbnail_path(item) == thumbnail
    assert get_review_original_path(item) == original
    assert thumb_path == thumbnail
    assert thumb_label == "Thumbnail Preview"
    assert original_path == original
    assert original_label == "Original Image"


def test_display_path_falls_back_to_thumbnail_when_original_is_missing(tmp_path: Path) -> None:
    thumbnail = _image(tmp_path / "thumb.jpg", size=(100, 100))
    item = FakeReviewItem(original_path=tmp_path / "missing.jpg", thumbnail_path=thumbnail)

    path, label = get_display_path(item, prefer_thumbnail=False)

    assert path == thumbnail
    assert label == "Thumbnail Preview Fallback"
