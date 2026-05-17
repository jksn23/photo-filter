from src.core.photo.photo_types import BodyScore, FaceScore, TechnicalScore
from src.core.scoring.final_score import compute_final_score


def test_body_blur_lowers_final_score():
    technical = TechnicalScore(sharpness=0.8, exposure=0.8, contrast=0.7, global_blur_penalty=0.1)
    face = FaceScore(face_detected=True, face_count=1, face_sharpness=0.8, face_score=0.8)
    clean_body = BodyScore(person_detected=True, body_sharpness=0.8, body_blur_penalty=0.1, subject_score=0.75)
    blurry_body = BodyScore(person_detected=True, body_sharpness=0.3, body_blur_penalty=0.8, subject_score=0.05)

    assert compute_final_score(technical, face, blurry_body) < compute_final_score(technical, face, clean_body)


def test_sharper_face_increases_final_score():
    technical = TechnicalScore(sharpness=0.8, exposure=0.8, contrast=0.7, global_blur_penalty=0.1)
    body = BodyScore(person_detected=True, body_sharpness=0.7, body_blur_penalty=0.2, subject_score=0.63)
    weak_face = FaceScore(face_detected=True, face_count=1, face_sharpness=0.2, face_score=0.2)
    sharp_face = FaceScore(face_detected=True, face_count=1, face_sharpness=0.9, face_score=0.9)

    assert compute_final_score(technical, sharp_face, body) > compute_final_score(technical, weak_face, body)


def test_mode_changes_penalties_and_score_is_bounded():
    technical = TechnicalScore(sharpness=0.4, exposure=0.8, contrast=0.7, global_blur_penalty=0.7)
    face = FaceScore(face_detected=True, face_count=1, face_sharpness=0.8, face_score=0.8)
    body = BodyScore(person_detected=True, body_sharpness=0.4, body_blur_penalty=0.7, subject_score=0.15)

    conservative = compute_final_score(technical, face, body, mode="conservative")
    aggressive = compute_final_score(technical, face, body, mode="aggressive")

    assert conservative >= aggressive
    assert 0.0 <= aggressive <= 1.0

