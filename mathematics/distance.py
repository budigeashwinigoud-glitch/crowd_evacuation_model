"""Distance and nearest-exit calculations."""

from __future__ import annotations

from typing import Iterable, Optional

import numpy as np


def euclidean_distance(point_a: np.ndarray, point_b: np.ndarray) -> float:
    """Return the Euclidean distance between two points."""
    return float(np.linalg.norm(np.asarray(point_a, dtype=float) - np.asarray(point_b, dtype=float)))


def nearest_available_exit(position: np.ndarray, exits: Iterable) -> Optional[object]:
    """Pick the nearest exit among all exits currently available."""
    available_exits = [exit for exit in exits if getattr(exit, "available", True)]
    if not available_exits:
        return None

    distances = [euclidean_distance(position, exit.position) for exit in available_exits]
    index = int(np.argmin(distances))
    return available_exits[index]
