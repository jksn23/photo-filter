"""Metadata extraction helpers for local image files."""

from pathlib import Path

from PIL import Image, ExifTags

from src.core.photo.photo_types import PhotoMetadata


EXIF_NAME_BY_ID = {value: key for key, value in ExifTags.TAGS.items()}


def _stringify_ratio(value) -> str | None:
    if value is None:
        return None
    try:
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            return f"{value.numerator}/{value.denominator}"
    except Exception:
        pass
    return str(value)


def read_photo_metadata(path: Path) -> PhotoMetadata:
    """Read a small, safe subset of EXIF metadata."""
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            if not exif:
                return PhotoMetadata()
            make = exif.get(EXIF_NAME_BY_ID.get("Make"))
            model = exif.get(EXIF_NAME_BY_ID.get("Model"))
            return PhotoMetadata(
                camera=" ".join(str(part).strip() for part in [make, model] if part).strip() or None,
                iso=exif.get(EXIF_NAME_BY_ID.get("ISOSpeedRatings")),
                aperture=_stringify_ratio(exif.get(EXIF_NAME_BY_ID.get("FNumber"))),
                shutter_speed=_stringify_ratio(exif.get(EXIF_NAME_BY_ID.get("ExposureTime"))),
                focal_length=_stringify_ratio(exif.get(EXIF_NAME_BY_ID.get("FocalLength"))),
                date_taken=str(exif.get(EXIF_NAME_BY_ID.get("DateTimeOriginal")) or "") or None,
            )
    except Exception:
        return PhotoMetadata()

