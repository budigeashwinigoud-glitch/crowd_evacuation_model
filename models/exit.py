"""Exit representation for the evacuation model."""

from __future__ import annotations

import numpy as np


class Exit:
    """A building exit with a position and usage counter."""

    def __init__(self, exit_id: int, x: float, y: float, available: bool = True):
        self.exit_id = exit_id
        self.position = np.array([float(x), float(y)], dtype=float)
        self.available = available
        self.people_evacuated = 0

    def block(self) -> None:
        self.available = False

    def unblock(self) -> None:
        self.available = True

    def __repr__(self) -> str:
        return f"Exit(id={self.exit_id}, position={self.position.tolist()}, available={self.available})"
