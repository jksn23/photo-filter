"""Output folder creation and safe file copying."""

from pathlib import Path
import shutil


STATUS_FOLDERS = {
    "SELECTED": "01_SELECTED",
    "REVIEW": "02_REVIEW",
    "REJECTED": "03_REJECTED",
    "ERROR": "04_REPORT/errors",
}


def default_output_folder(input_folder: str) -> str:
    """Return the default culling output folder for an input folder."""
    input_path = Path(input_folder).expanduser()
    return str(input_path.with_name(f"{input_path.name}_CULLED"))


def create_output_folders(output_base: str) -> dict[str, str]:
    """Create the output folder structure and return status-to-folder paths."""
    base = Path(output_base).expanduser()
    folders = {}
    for status, folder_name in STATUS_FOLDERS.items():
        folder = base / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        folders[status] = str(folder)

    report_folder = base / "04_REPORT"
    report_folder.mkdir(parents=True, exist_ok=True)
    folders["REPORT"] = str(report_folder)
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


def copy_to_output(original_path: str, status: str, output_folders: dict[str, str]) -> str:
    """Copy a file into its status output folder without overwriting files."""
    folder_path = output_folders.get(status, output_folders["ERROR"])
    destination = _safe_destination(Path(folder_path), Path(original_path).name)
    shutil.copy2(original_path, destination)
    return str(destination)

