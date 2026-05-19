"""Resource limit helpers for safe Streamlit-friendly processing."""

from __future__ import annotations

import os


def _mode_cap(mode: str) -> int:
    return 2 if str(mode).lower() == "accurate" else 4


def resolve_worker_count(requested: int | str, mode: str) -> int:
    """Resolve user worker count without using all CPU cores by default."""
    cap = _mode_cap(mode)
    cpu_count = os.cpu_count() or 1

    if isinstance(requested, str):
        if requested.lower() == "auto":
            return max(1, min(cpu_count - 1 if cpu_count > 1 else 1, cap))
        try:
            requested_int = int(requested)
        except ValueError:
            requested_int = 1
    else:
        requested_int = int(requested)

    return max(1, min(requested_int, cap))
