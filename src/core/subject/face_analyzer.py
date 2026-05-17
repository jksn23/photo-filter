"""Face analyzer using OpenCV Haar Cascade."""

import cv2
import numpy as np

from src.core.photo.photo_types import FaceScore
from src.face_detector import _load_face_cascade
from src.core.quality.blur_metrics import normalize_blur_score, variance_of_laplacian


def detect_face_regions(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Detect face regions as x, y, w, h."""
    cascade = _load_face_cascade()
    if cascade is None or image.size == 0:
        return []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24))
    return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]


def analyze_face(image: np.ndarray) -> FaceScore:
    """Analyze face count and face sharpness, bounded to 0-1."""
    try:
        faces = detect_face_regions(image)
        if not faces:
            return FaceScore(face_detected=False, face_count=0, face_sharpness=0.0, face_score=0.45)
        sharpness_scores = []
        height, width = image.shape[:2]
        for x, y, w, h in faces:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(width, x + w), min(height, y + h)
            crop = image[y1:y2, x1:x2]
            if crop.size:
                sharpness_scores.append(normalize_blur_score(variance_of_laplacian(crop), reference=220.0))
        face_sharpness = max(sharpness_scores) if sharpness_scores else 0.0
        face_score = max(0.0, min(1.0, face_sharpness * 0.75 + min(len(faces), 4) * 0.06))
        return FaceScore(
            face_detected=True,
            face_count=len(faces),
            face_sharpness=round(face_sharpness, 4),
            face_score=round(face_score, 4),
        )
    except Exception:
        return FaceScore(face_detected=False, face_count=0, face_sharpness=0.0, face_score=0.45)

