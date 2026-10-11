"""Animation generation for the crowd motion."""

from __future__ import annotations

from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def create_animation(history: List[dict], building, exits, save_path: str = "results/crowd_animation.gif"):
    """Create a simple animation of the crowd based on recorded positions in the history."""
    if not history:
        return save_path

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, building.width)
    ax.set_ylim(0, building.height)
    ax.set_aspect("equal")
    ax.set_title("Crowd Evacuation Animation")

    for x1, y1, x2, y2 in building.obstacles:
        rect = plt.Rectangle((x1, y1), x2 - x1, y2 - y1, facecolor="gray", edgecolor="black")
        ax.add_patch(rect)

    for exit_item in exits:
        ax.plot(exit_item.position[0], exit_item.position[1], "o", markersize=12, color="green")

    scatter = ax.scatter([], [], s=25, c="royalblue", alpha=0.8)
    time_text = ax.text(0.02, 0.95, "", transform=ax.transAxes)

    def animate(frame_index):
        state = history[min(frame_index, len(history) - 1)]
        positions = state.get("people_positions", [])
        if positions:
            positions_array = [[float(point[0]), float(point[1])] for point in positions]
            scatter.set_offsets(positions_array)
        else:
            scatter.set_offsets([])
        time_text.set_text(f"Time: {state['time']:.1f} s")
        return scatter, time_text

    anim = FuncAnimation(fig, animate, frames=len(history), interval=80, blit=False)
    anim.save(save_path, writer="pillow", fps=10)
    plt.close(fig)
    return save_path
