"""Shared cache key helpers."""

from pathlib import Path
import hashlib


def build_cache_key(path: Path) -> str:
    """Return a stable safe cache key for an absolute path."""
    raw = str(Path(path).resolve()).lower()
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def file_cache_key(path: Path) -> str:
    """Return a stable cache key for path + size + modified time."""
    stat = Path(path).stat()
    raw = f"{Path(path).resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def ensure_cache_root(root: Path | None = None) -> Path:
    """Return the cache root, creating it when needed."""
    cache_root = root or Path(".cullagrace-cache")
    cache_root.mkdir(parents=True, exist_ok=True)
    return cache_root
