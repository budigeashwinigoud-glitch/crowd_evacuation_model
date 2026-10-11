"""Crowd density calculations over grid cells."""

from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np


def calculate_density_grid(people: Iterable, building, cell_size: float) -> np.ndarray:
    """Create a 2D density matrix where each cell stores persons per square meter."""
    rows = max(1, int(np.ceil(building.height / cell_size)))
    cols = max(1, int(np.ceil(building.width / cell_size)))
    grid = np.zeros((rows, cols), dtype=float)

    for person in people:
        if person.evacuated:
            continue
        x_index = int(np.floor(person.position[0] / cell_size))
        y_index = int(np.floor(person.position[1] / cell_size))
        x_index = min(max(x_index, 0), cols - 1)
        y_index = min(max(y_index, 0), rows - 1)
        grid[y_index, x_index] += 1.0

    cell_area = float(cell_size * cell_size)
    if cell_area <= 0:
        raise ValueError("Cell area must be positive.")
    return grid / cell_area


def compute_density_metrics(people: Iterable, building, cell_size: float) -> Tuple[np.ndarray, float, float, float]:
    """Return the density matrix, average density, maximum density, and cell count."""
    density_matrix = calculate_density_grid(people, building, cell_size)
    average_density = float(np.mean(density_matrix)) if density_matrix.size else 0.0
    maximum_density = float(np.max(density_matrix)) if density_matrix.size else 0.0
    cell_count = float(density_matrix.size)
    return density_matrix, average_density, maximum_density, cell_count
