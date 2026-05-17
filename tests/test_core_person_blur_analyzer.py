import cv2
import numpy as np

from src.core.subject.person_blur_analyzer import analyze_person_body_blur


def _subject_image(blur_body: bool = False):
    image = np.full((160, 120, 3), 120, dtype=np.uint8)
    cv2.rectangle(image, (35, 15), (85, 50), (230, 230, 230), -1)
    body = np.full((90, 60, 3), 90, dtype=np.uint8)
    for index in range(0, 90, 6):
        cv2.line(body, (0, index), (59, index), (255, 255, 255), 1)
    for index in range(0, 60, 6):
        cv2.line(body, (index, 0), (index, 89), (255, 255, 255), 1)
    if blur_body:
        body = cv2.GaussianBlur(body, (31, 31), 0)
    image[55:145, 30:90] = body
    return image


def test_blurred_body_has_lower_sharpness_and_higher_penalty():
    face_box = [(35, 15, 50, 35)]
    sharp = analyze_person_body_blur(_subject_image(False), face_box)
    blurred = analyze_person_body_blur(_subject_image(True), face_box)

    assert sharp.body_sharpness > blurred.body_sharpness
    assert sharp.body_blur_penalty < blurred.body_blur_penalty


def test_optional_detector_fallback_does_not_crash_without_detector():
    score = analyze_person_body_blur(_subject_image(False), enable_person_detection=True, detector=None)

    assert 0.0 <= score.body_sharpness <= 1.0
    assert 0.0 <= score.body_blur_penalty <= 1.0
