"""Lightweight person detection helpers using Ultralytics YOLO."""

from functools import lru_cache
from pathlib import Path

import cv2


PersonBox = tuple[int, int, int, int]


@lru_cache(maxsize=2)
def _load_yolo_model(model_name: str):
    """Load and cache a YOLO model, returning None if unavailable."""
    try:
        from ultralytics import YOLO

        return YOLO(model_name)
    except Exception:
        return None


def detect_person_boxes(
    image_path: Path,
    confidence_threshold: float = 0.35,
    model_name: str = "yolov8n.pt",
) -> list[PersonBox]:
    """Detect person boxes with a cached YOLO model."""
    model = _load_yolo_model(model_name)
    if model is None:
        return []

    try:
        results = model.predict(
            source=str(Path(image_path)),
            conf=confidence_threshold,
            classes=[0],
            device="cpu",
            imgsz=640,
            verbose=False,
        )
    except Exception:
        return []

    boxes: list[PersonBox] = []
    for result in results:
        if result.boxes is None:
            continue
        for detected_box in result.boxes:
            try:
                confidence = float(detected_box.conf[0])
                class_id = int(detected_box.cls[0])
                if class_id != 0 or confidence < confidence_threshold:
                    continue
                x1, y1, x2, y2 = detected_box.xyxy[0].tolist()
                x = max(0, int(round(x1)))
                y = max(0, int(round(y1)))
                w = max(0, int(round(x2 - x1)))
                h = max(0, int(round(y2 - y1)))
                if w > 0 and h > 0:
                    boxes.append((x, y, w, h))
            except Exception:
                continue
    return boxes


def select_main_person_box(
    boxes: list[PersonBox],
    image_width: int,
    image_height: int,
) -> PersonBox | None:
    """Select the most important person box by size and center proximity."""
    if not boxes or image_width <= 0 or image_height <= 0:
        return None

    image_area = float(image_width * image_height)
    image_center_x = image_width / 2.0
    image_center_y = image_height / 2.0
    max_distance = ((image_center_x**2) + (image_center_y**2)) ** 0.5

    def score(box: PersonBox) -> float:
        x, y, w, h = box
        box_area = max(w * h, 0)
        box_center_x = x + (w / 2.0)
        box_center_y = y + (h / 2.0)
        distance = ((box_center_x - image_center_x) ** 2 + (box_center_y - image_center_y) ** 2) ** 0.5
        normalized_distance = 0.0 if max_distance == 0 else min(distance / max_distance, 1.0)
        area_score = box_area / image_area
        center_score = 1.0 - normalized_distance
        return area_score * 0.75 + center_score * 0.25

    return max(boxes, key=score)


def get_image_size(image_path: Path) -> tuple[int, int]:
    """Return image width and height, or (0, 0) when unreadable."""
    image = cv2.imread(str(Path(image_path)))
    if image is None:
        return 0, 0
    height, width = image.shape[:2]
    return width, height

