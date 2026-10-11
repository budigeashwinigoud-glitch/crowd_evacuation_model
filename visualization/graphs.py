"""Plot analysis graphs for the crowd evacuation study."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_evacuation_curve(history, save_path: str = "results/evacuation_curve.png") -> str:
    times = [entry["time"] for entry in history]
    evacuated = [entry["evacuated_people"] for entry in history]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(times, evacuated, marker="o", linewidth=2)
    ax.set_title("Number of Evacuated People vs Time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Evacuated People")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    return save_path


def plot_speed_curve(history, save_path: str = "results/speed_curve.png") -> str:
    times = [entry["time"] for entry in history]
    speeds = [entry["average_speed"] for entry in history]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(times, speeds, marker="s", linewidth=2, color="darkgreen")
    ax.set_title("Average Speed vs Time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Average Speed (m/s)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    return save_path


def plot_density_curve(history, save_path: str = "results/density_curve.png") -> str:
    times = [entry["time"] for entry in history]
    densities = [entry["maximum_density"] for entry in history]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(times, densities, marker="^", linewidth=2, color="crimson")
    ax.set_title("Maximum Crowd Density vs Time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Maximum Density (persons/m²)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    return save_path


def plot_exit_use(exit_usage: dict, save_path: str = "results/exit_use.png") -> str:
    fig, ax = plt.subplots(figsize=(7, 5))
    if exit_usage:
        labels = [f"Exit {key}" for key in sorted(exit_usage)]
        values = [exit_usage[key] for key in sorted(exit_usage)]
        ax.bar(labels, values, color=["steelblue", "orange", "green"][: len(values)])
        ax.set_title("Exit Utilization")
        ax.set_ylabel("Usage (%)")
        ax.set_xlabel("Exit")
        ax.grid(axis="y", alpha=0.3)
    else:
        ax.text(0.5, 0.5, "No exits available", ha="center", va="center")
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    return save_path


def plot_comparison_graph(results: list, save_path: str = "results/method_comparison.png") -> str:
    methods = [item["Method"] for item in results]
    evacuation_times = [item["Evacuation Time"] for item in results]
    speeds = [item["Average Speed"] for item in results]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].bar(methods, evacuation_times, color=["dodgerblue", "tomato"])
    axes[0].set_title("Evacuation Time Comparison")
    axes[0].set_ylabel("Time (s)")
    axes[0].grid(axis="y", alpha=0.3)

    axes[1].bar(methods, speeds, color=["forestgreen", "indigo"])
    axes[1].set_title("Average Speed Comparison")
    axes[1].set_ylabel("Speed (m/s)")
    axes[1].grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    return save_path
