"""Perceptual hash helpers."""

from pathlib import Path

from src.duplicate_detector import calculate_phash


def compute_phash(path: Path):
    """Compute perceptual hash for an image path."""
    return calculate_phash(Path(path))


def generate_perceptual_hash(image_path: Path) -> str:
    """Generate a pHash string for a photo."""
    return str(compute_phash(Path(image_path)))


def hash_distance(hash_a, hash_b) -> int:
    """Return ImageHash/string Hamming distance."""
    try:
        return int(hash_a - hash_b)
    except Exception:
        return hamming_distance(str(hash_a), str(hash_b))


def hamming_distance(left_hash: str, right_hash: str) -> int:
    """Calculate Hamming distance between two hexadecimal hash strings."""
    return bin(int(left_hash, 16) ^ int(right_hash, 16)).count("1")
