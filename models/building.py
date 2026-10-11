"""Building geometry and obstacle handling."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


class Building:
    """Simple rectangular building with obstacle rectangles."""

    def __init__(self, width: float, height: float):
        self.width = float(width)
        self.height = float(height)
        self.obstacles: List[Tuple[float, float, float, float]] = []

    def add_obstacle(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Store a rectangular obstacle defined by two corners."""
        left = min(x1, x2)
        right = max(x1, x2)
        bottom = min(y1, y2)
        top = max(y1, y2)
        self.obstacles.append((left, bottom, right, top))

    def contains_point(self, point: np.ndarray) -> bool:
        x, y = float(point[0]), float(point[1])
        if x < 0 or y < 0 or x > self.width or y > self.height:
            return False
        for x1, y1, x2, y2 in self.obstacles:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        return False

    def keep_inside_bounds(self, point: np.ndarray) -> np.ndarray:
        """Clamp position to stay inside the building boundaries."""
        x = min(max(float(point[0]), 0.0), self.width)
        y = min(max(float(point[1]), 0.0), self.height)
        point[0] = x
        point[1] = y
        return point

    def is_valid_position(self, point: np.ndarray) -> bool:
        """Check whether the given point is inside the building and not in an obstacle."""
        if point[0] < 0 or point[1] < 0 or point[0] > self.width or point[1] > self.height:
            return False
        for x1, y1, x2, y2 in self.obstacles:
            if x1 <= point[0] <= x2 and y1 <= point[1] <= y2:
                return False
        return True
