"""Direction and velocity calculations for each person."""

from __future__ import annotations

import numpy as np


def direction_vector(position: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Compute the normalized direction from a person to an exit."""
    difference = np.asarray(target, dtype=float) - np.asarray(position, dtype=float)
    distance = np.linalg.norm(difference)
    if distance < 1e-12:
        return np.array([0.0, 0.0], dtype=float)
    return difference / distance


def velocity_components(speed: float, direction: np.ndarray) -> np.ndarray:
    """Return the x and y velocity components from speed and direction."""
    direction = np.asarray(direction, dtype=float)
    return np.array([speed * direction[0], speed * direction[1]], dtype=float)
