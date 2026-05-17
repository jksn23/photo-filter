"""Perceptual hash helpers."""

from pathlib import Path

from src.duplicate_detector import calculate_phash


def generate_perceptual_hash(image_path: Path) -> str:
    """Generate a pHash string for a photo."""
    return str(calculate_phash(Path(image_path)))


def hamming_distance(left_hash: str, right_hash: str) -> int:
    """Calculate Hamming distance between two hexadecimal hash strings."""
    return bin(int(left_hash, 16) ^ int(right_hash, 16)).count("1")

