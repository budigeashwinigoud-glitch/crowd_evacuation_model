"""Numerical integration methods for the crowd movement model."""

from __future__ import annotations

import numpy as np


def euler_step(position: np.ndarray, velocity: np.ndarray, dt: float) -> np.ndarray:
    """Euler method update: x_{n+1} = x_n + dt * v."""
    return np.asarray(position, dtype=float) + dt * np.asarray(velocity, dtype=float)


def rk4_step(position: np.ndarray, velocity: np.ndarray, dt: float) -> np.ndarray:
    """Fourth-order Runge-Kutta step for dx/dt = v and dy/dt = v."""
    pos = np.asarray(position, dtype=float)
    vel = np.asarray(velocity, dtype=float)

    def derivative(state: np.ndarray) -> np.ndarray:
        return vel.copy()

    k1 = derivative(pos)
    k2 = derivative(pos + 0.5 * dt * k1)
    k3 = derivative(pos + 0.5 * dt * k2)
    k4 = derivative(pos + dt * k3)

    return pos + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
