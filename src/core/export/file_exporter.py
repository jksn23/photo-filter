"""Export selected/review/rejected photos."""

from pathlib import Path
import shutil

from src.core.photo.photo_types import PhotoItem
from src.file_manager import _safe_destination


STATUS_DIRS = {
    "selected": "01_SELECTED",
    "review": "02_REVIEW",
    "rejected": "03_REJECTED",
}


def export_photos(photo_items: list[PhotoItem], output_dir: Path) -> None:
    """Copy photos into Selected/Review/Rejected folders without moving originals."""
    base = Path(output_dir)
    for dirname in STATUS_DIRS.values():
        (base / dirname).mkdir(parents=True, exist_ok=True)
    for item in photo_items:
        status_dir = STATUS_DIRS.get(item.status)
        if status_dir is None:
            continue
        source = Path(item.path)
        destination = _safe_destination(base / status_dir, source.name)
        shutil.copy2(source, destination)
        item.output_path = str(destination)
