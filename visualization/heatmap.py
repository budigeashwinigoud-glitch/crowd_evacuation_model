"""Heatmap visualization for crowd density."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_density_heatmap(density_matrix, save_path: str = "results/density_heatmap.png", title: str = "Crowd Density") -> str:
    """Save a density heatmap for a given density matrix."""
    fig, ax = plt.subplots(figsize=(8, 5))
    image = ax.imshow(density_matrix, cmap="YlOrRd", origin="lower", aspect="auto")
    ax.set_title(title)
    ax.set_xlabel("Grid Column")
    ax.set_ylabel("Grid Row")
    fig.colorbar(image, ax=ax, label="Persons/m²")
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    return save_path
