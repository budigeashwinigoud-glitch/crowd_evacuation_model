"""Representation of an individual in the crowd."""

from __future__ import annotations

from typing import Optional

import numpy as np


class Person:
    """A person moving toward an exit while interacting with the crowd."""

    def __init__(self, person_id: int, x: float, y: float, normal_speed: float):
        self.id = person_id
        self.position = np.array([float(x), float(y)], dtype=float)
        self.velocity = np.array([0.0, 0.0], dtype=float)
        self.normal_speed = float(normal_speed)
        self.current_speed = 0.0
        self.evacuated = False
        self.selected_exit = None
        self.evacuation_time: Optional[float] = None

    def reset_velocity(self) -> None:
        self.velocity = np.array([0.0, 0.0], dtype=float)
        self.current_speed = 0.0

    def __repr__(self) -> str:
        return (
            f"Person(id={self.id}, position={self.position.tolist()}, "
            f"speed={self.current_speed:.3f}, evacuated={self.evacuated})"
        )
