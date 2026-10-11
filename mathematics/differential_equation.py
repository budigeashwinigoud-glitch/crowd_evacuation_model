"""Differential equations used in the motion model."""

from __future__ import annotations

import numpy as np


def dxdt(x_position: float, x_velocity: float) -> float:
    """Return the rate of change of x with respect to time."""
    return float(x_velocity)


def dydt(y_position: float, y_velocity: float) -> float:
    """Return the rate of change of y with respect to time."""
    return float(y_velocity)


def position_derivative(position: np.ndarray, velocity: np.ndarray) -> np.ndarray:
    """A compact representation of the system d(position)/dt = velocity."""
    return np.asarray(velocity, dtype=float)
