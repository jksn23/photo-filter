import numpy as np

from src.core.subject.face_analyzer import analyze_face


def test_face_analyzer_no_face_is_bounded():
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    result = analyze_face(image)

    assert result.face_detected is False
    assert result.face_count == 0
    assert 0.0 <= result.face_score <= 1.0


def test_face_analyzer_handles_small_image():
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    result = analyze_face(image)

    assert 0.0 <= result.face_score <= 1.0

