"""Selected photo and JSON report export."""

from dataclasses import asdict
from pathlib import Path
import json
import shutil

from src.core.photo.photo_types import CullingResult, PhotoItem
from src.file_manager import _safe_destination


def export_selected_photos(selected: list[PhotoItem], output_dir: Path) -> list[Path]:
    """Copy selected photos to a folder without moving originals."""
    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for item in selected:
        source = Path(item.path)
        destination = _safe_destination(destination_dir, source.name)
        shutil.copy2(source, destination)
        copied.append(destination)
    return copied


def export_culling_json_report(result: CullingResult, report_path: Path) -> Path:
    """Write an auditable JSON report with summary, clusters, scores, and reasons."""
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(asdict(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path

