"""Copy-only exporter for CullaGrace V2 final decisions."""

from __future__ import annotations

from pathlib import Path
import shutil

from src.core.review.review_types import FinalDecision, ReviewItem, ReviewSession


FOLDER_NAMES: dict[FinalDecision, str] = {
    "post": "Posts",
    "save": "Save",
    "delete": "Delete",
    "undecided": "Undecided",
}


def _destination_for(source: Path, folder: Path) -> Path:
    candidate = folder / source.name
    if not candidate.exists():
        return candidate
    stem = source.stem
    suffix = source.suffix
    index = 1
    while True:
        candidate = folder / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _should_export(item: ReviewItem, include_undecided: bool) -> bool:
    if item.final_decision == "undecided":
        return include_undecided
    return item.final_decision in {"post", "save", "delete"}


def export_final_decisions(
    session: ReviewSession,
    output_dir: Path,
    copy_files: bool = True,
    include_undecided: bool = False,
) -> dict[str, int]:
    """Export final decisions by copying source files into final folders."""
    counts = {"post": 0, "save": 0, "delete": 0, "undecided": 0, "missing": 0}
    final_root = output_dir / "02_FINAL_DECISION"
    for decision in ("post", "save", "delete"):
        (final_root / FOLDER_NAMES[decision]).mkdir(parents=True, exist_ok=True)
    if include_undecided:
        (final_root / FOLDER_NAMES["undecided"]).mkdir(parents=True, exist_ok=True)

    for item in session.items:
        counts[item.final_decision] += 1
        if not _should_export(item, include_undecided):
            continue

        source = Path(item.original_path)
        if not source.exists():
            counts["missing"] += 1
            continue

        destination_folder = final_root / FOLDER_NAMES[item.final_decision]
        destination_folder.mkdir(parents=True, exist_ok=True)
        if copy_files:
            shutil.copy2(source, _destination_for(source, destination_folder))

    return counts
