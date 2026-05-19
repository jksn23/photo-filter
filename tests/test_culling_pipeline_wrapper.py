from pathlib import Path

from src.core.photo.photo_types import BodyScore, FaceScore, PhotoItem, PhotoScore, TechnicalScore
from src.culling_pipeline import run_culling_pipeline


def test_culling_pipeline_wrapper_calls_core_engine(monkeypatch, tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    called = {}
    progress_messages = []
    log_messages = []

    def fake_engine(**kwargs):
        called.update(kwargs)
        kwargs["log_callback"]("Fake engine started.")
        kwargs["progress_callback"](1, 3, "Fake analyzing a.jpg...")
        item = PhotoItem(id="a", path=input_dir / "a.jpg", file_name="a.jpg", cluster_id="CL001", status="selected")
        item.score = PhotoScore(
            technical=TechnicalScore(sharpness=0.8, exposure=0.7, contrast=0.6, global_blur_penalty=0.1),
            face=FaceScore(face_detected=True, face_count=1, face_sharpness=0.8, face_score=0.8),
            body=BodyScore(person_detected=True, body_sharpness=0.8, body_blur_penalty=0.1, subject_score=0.8),
            final_score=0.82,
            reasons=["Selected as best image in similar cluster."],
        )
        item.is_cluster_winner = True
        item.metadata_dict.update({"mode": "balanced", "selected_photo_id": "a", "cluster_winner_filename": "a.jpg"})
        return [item]

    monkeypatch.setattr("src.culling_pipeline.run_culling_engine", fake_engine)

    results, summary = run_culling_pipeline(
        str(input_dir),
        str(output_dir),
        {"copy_files": False, "duplicate_hash_threshold": 8, "culling_mode": "balanced"},
        progress_callback=lambda current, total, message: progress_messages.append((current, total, message)),
        log_callback=log_messages.append,
    )

    assert called["input_dir"] == input_dir
    assert called["output_dir"] == output_dir
    assert called["mode"] == "balanced"
    assert results[0].output_status == "SELECTED"
    assert results[0].body_blur_penalty == 0.1
    assert summary["selected"] == 1
    assert called["progress_callback"] is not None
    assert called["log_callback"] is not None
    assert "Fake engine started." in log_messages
    assert any(message == "Fake analyzing a.jpg..." for _, _, message in progress_messages)
