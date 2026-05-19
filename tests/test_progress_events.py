from src.core.pipeline.progress_events import ProgressEvent


def test_progress_event_fields() -> None:
    event = ProgressEvent(stage="analyzing", current=1, total=2, message="Analyzing", filename="a.jpg")

    assert event.stage == "analyzing"
    assert event.current == 1
    assert event.total == 2
    assert event.filename == "a.jpg"
