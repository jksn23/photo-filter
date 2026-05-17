"""Output folder creation and safe file copying."""

from pathlib import Path
import shutil


STATUS_FOLDERS = {
    "SELECTED": "01_SELECTED",
    "REVIEW": "02_REVIEW",
    "REJECTED": "03_REJECTED",
    "ERROR": "04_REPORT/errors",
}


def normalize_user_path(path_value: str | Path | None) -> Path | None:
    """Normalize a user-entered filesystem path from a text input."""
    if path_value is None:
        return None
    path_text = str(path_value).strip()
    if not path_text:
        return None
    if (path_text.startswith('"') and path_text.endswith('"')) or (
        path_text.startswith("'") and path_text.endswith("'")
    ):
        path_text = path_text[1:-1].strip()
    return Path(path_text).expanduser()


def prepare_output_dirs(output_dir: Path) -> dict[str, Path]:
    """Create and return the required output directories."""
    base = Path(output_dir).expanduser()
    output_dirs = {
        "SELECTED": base / "01_SELECTED",
        "REVIEW": base / "02_REVIEW",
        "REJECTED": base / "03_REJECTED",
        "REPORT": base / "04_REPORT",
    }
    for folder in output_dirs.values():
        folder.mkdir(parents=True, exist_ok=True)
    return output_dirs


def default_output_folder(input_folder: str) -> str:
    """Return the default culling output folder for an input folder."""
    input_path = normalize_user_path(input_folder)
    if input_path is None:
        raise ValueError("Folder input belum diisi.")
    return str(input_path / f"{input_path.name}_CULLED")


def create_output_folders(output_base: str) -> dict[str, str]:
    """Create the output folder structure and return status-to-folder paths."""
    base = normalize_user_path(output_base)
    if base is None:
        raise ValueError("Folder output belum diisi.")
    prepared = prepare_output_dirs(base)
    error_folder = prepared["REPORT"] / "errors"
    error_folder.mkdir(parents=True, exist_ok=True)
    folders = {status: str(path) for status, path in prepared.items()}
    folders["ERROR"] = str(error_folder)
    folders["BASE"] = str(base)
    return folders


def _safe_destination(folder: Path, filename: str) -> Path:
    destination = folder / filename
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    counter = 1
    while True:
        candidate = folder / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def copy_photo_to_status_folder(
    photo_path: Path,
    status: str,
    output_dirs: dict[str, Path],
) -> Path:
    """Copy a photo to its status folder without deleting or moving the original."""
    if status not in {"SELECTED", "REVIEW", "REJECTED"}:
        raise ValueError(f"Status output tidak dikenal: {status}")
    destination = _safe_destination(output_dirs[status], Path(photo_path).name)
    shutil.copy2(photo_path, destination)
    return destination


def copy_to_output(original_path: str, status: str, output_folders: dict[str, str]) -> str:
    """Backward-compatible copy helper that accepts string folder mappings."""
    folder_path = Path(output_folders.get(status, output_folders["ERROR"]))
    destination = _safe_destination(folder_path, Path(original_path).name)
    shutil.copy2(original_path, destination)
    return str(destination)
