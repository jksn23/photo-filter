"""Offline face detection using OpenCV Haar Cascade."""

from functools import lru_cache

import cv2


@lru_cache(maxsize=1)
def _load_face_cascade():
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    if cascade.empty():
        return None
    return cascade


def detect_faces(image) -> int:
    """Detect frontal faces and return the number found."""
    cascade = _load_face_cascade()
    if cascade is None:
        return 0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]
    max_width = 900
    scale = 1.0
    if width > max_width:
        scale = max_width / width
        gray = cv2.resize(gray, (max_width, int(height * scale)))

    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
    )
    return int(len(faces))

