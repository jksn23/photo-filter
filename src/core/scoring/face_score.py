"""Face-aware scoring based on OpenCV face detection."""

from pathlib import Path

from src.face_detector import count_faces


def calculate_face_score(image_path: Path) -> dict:
    """Return a lightweight face score that does not reject non-portrait photos."""
    face_count = count_faces(Path(image_path))
    face_score = min(1.0, 0.35 + face_count * 0.25) if face_count > 0 else 0.45
    return {
        "face_count": face_count,
        "face_score": round(face_score, 4),
        "face_sharpness": None,
        "eye_open_score": None,
    }

