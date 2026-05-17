"""Default configuration for Church Photo Culling v1 / CullaGrace."""

DEFAULT_BLUR_THRESHOLD = 100
DEFAULT_UNDEREXPOSED_THRESHOLD = 50
DEFAULT_OVEREXPOSED_THRESHOLD = 210
DEFAULT_DUPLICATE_HASH_THRESHOLD = 8
DEFAULT_SELECTED_SCORE_MIN = 80
DEFAULT_REVIEW_SCORE_MIN = 50

SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png"]


def default_runtime_config() -> dict:
    """Return the default runtime configuration used by the culling pipeline."""
    return {
        "blur_threshold": DEFAULT_BLUR_THRESHOLD,
        "underexposed_threshold": DEFAULT_UNDEREXPOSED_THRESHOLD,
        "overexposed_threshold": DEFAULT_OVEREXPOSED_THRESHOLD,
        "duplicate_hash_threshold": DEFAULT_DUPLICATE_HASH_THRESHOLD,
        "selected_score_min": DEFAULT_SELECTED_SCORE_MIN,
        "review_score_min": DEFAULT_REVIEW_SCORE_MIN,
        "copy_files": True,
        "create_csv": True,
        "use_face_detection": True,
        "use_duplicate_detection": True,
    }

