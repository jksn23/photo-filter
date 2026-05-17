from pathlib import Path


def test_readme_documents_normalized_scoring_not_old_base_100_rules():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "technical.sharpness" in text
    assert "body.body_blur_penalty" in text
    assert "Skor dasar adalah 100" not in text
    assert "Blur: -40" not in text
    assert "python -m pytest -q" in text
