"""Crowd simulation engine for the evacuation model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

import numpy as np

from config import CELL_SIZE, EXIT_RADIUS, MAX_DENSITY, MAX_TIME, TIME_STEP
from mathematics.density import compute_density_metrics
from mathematics.distance import euclidean_distance, nearest_available_exit
from mathematics.numerical_methods import euler_step, rk4_step
from mathematics.velocity import direction_vector, velocity_components
from models.person import Person


class CrowdSimulator:
    """Advance a crowd of people toward their nearest available exit."""

    def __init__(
        self,
        building,
        exits,
        people,
        method: str = "euler",
        time_step: float = TIME_STEP,
        max_time: float = MAX_TIME,
        cell_size: float = CELL_SIZE,
        max_density: float = MAX_DENSITY,
        exit_radius: float = EXIT_RADIUS,
    ):
        self.building = building
        self.exits = exits
        self.people = people
        self.method = method.lower()
        self.time_step = float(time_step)
        self.max_time = float(max_time)
        self.cell_size = float(cell_size)
        self.max_density = float(max_density)
        self.exit_radius = float(exit_radius)
        self.current_time = 0.0
        self.history: List[Dict[str, Any]] = []

    def _local_density(self, position: np.ndarray, density_matrix: np.ndarray) -> float:
        if density_matrix.size == 0:
            return 0.0
        row_index = int(np.floor(position[1] / self.cell_size))
        col_index = int(np.floor(position[0] / self.cell_size))
        row_index = min(max(row_index, 0), density_matrix.shape[0] - 1)
        col_index = min(max(col_index, 0), density_matrix.shape[1] - 1)
        return float(density_matrix[row_index, col_index])

    def _nearest_exit(self, person: Person):
        if not self.exits:
            return None
        if person.selected_exit is not None and person.selected_exit.available:
            return person.selected_exit
        return nearest_available_exit(person.position, self.exits)

    def _update_person(self, person: Person, density_matrix: np.ndarray) -> None:
        if person.evacuated:
            return

        exit_point = self._nearest_exit(person)
        if exit_point is None:
            person.reset_velocity()
            return

        person.selected_exit = exit_point
        distance_to_exit = euclidean_distance(person.position, exit_point.position)

        if distance_to_exit <= self.exit_radius:
            person.evacuated = True
            person.evacuation_time = self.current_time
            person.velocity = np.array([0.0, 0.0], dtype=float)
            person.current_speed = 0.0
            exit_point.people_evacuated += 1
            return

        local_density = self._local_density(person.position, density_matrix)
        if self.max_density <= 0:
            speed = person.normal_speed
        else:
            speed = max(0.0, person.normal_speed * (1.0 - local_density / self.max_density))

        direction = direction_vector(person.position, exit_point.position)
        if np.allclose(direction, np.zeros(2)):
            direction = np.array([1.0, 0.0], dtype=float)

        person.velocity = velocity_components(speed, direction)
        person.current_speed = float(np.linalg.norm(person.velocity))

        previous_position = person.position.copy()
        if self.method == "euler":
            candidate = euler_step(previous_position, person.velocity, self.time_step)
        elif self.method == "rk4":
            candidate = rk4_step(previous_position, person.velocity, self.time_step)
        else:
            raise ValueError(f"Unsupported numerical method '{self.method}'.")

        candidate = self.building.keep_inside_bounds(candidate)
        if self.building.contains_point(candidate):
            candidate = previous_position.copy()
            person.velocity = np.array([0.0, 0.0], dtype=float)
            person.current_speed = 0.0

        person.position = candidate

        if euclidean_distance(person.position, exit_point.position) <= self.exit_radius:
            person.evacuated = True
            person.evacuation_time = self.current_time
            person.velocity = np.array([0.0, 0.0], dtype=float)
            person.current_speed = 0.0
            exit_point.people_evacuated += 1

    def _record_history(self) -> None:
        evacuated_count = sum(1 for person in self.people if person.evacuated)
        remaining_count = len(self.people) - evacuated_count

        active_speeds = [person.current_speed for person in self.people if not person.evacuated]
        average_speed = float(np.mean(active_speeds)) if active_speeds else 0.0

        density_matrix, average_density, maximum_density, _ = compute_density_metrics(
            self.people, self.building, self.cell_size
        )

        exit_counts = {exit.exit_id: exit.people_evacuated for exit in self.exits}
        total_usage = sum(exit_counts.values()) if exit_counts else 1
        exit_usage = {exit_id: (people_count / max(total_usage, 1)) * 100.0 for exit_id, people_count in exit_counts.items()}

        people_states = [
            {
                "id": person.id,
                "x": float(person.position[0]),
                "y": float(person.position[1]),
                "vx": float(person.velocity[0]),
                "vy": float(person.velocity[1]),
                "speed": float(person.current_speed),
                "evacuated": bool(person.evacuated),
            }
            for person in self.people
        ]

        self.history.append(
            {
                "time": self.current_time,
                "remaining_people": remaining_count,
                "evacuated_people": evacuated_count,
                "average_speed": average_speed,
                "maximum_density": maximum_density,
                "average_density": average_density,
                "exit_usage": exit_usage,
                "density_matrix": density_matrix,
                "people_positions": [person.position.copy() for person in self.people],
                "people_states": people_states,
            }
        )

    def run(self):
        """Run the simulation until everyone evacuates or the maximum time is reached."""
        self.current_time = 0.0
        self.history = []

        while self.current_time <= self.max_time:
            density_matrix, _, _, _ = compute_density_metrics(self.people, self.building, self.cell_size)
            for person in self.people:
                self._update_person(person, density_matrix)
            self._record_history()

            if all(person.evacuated for person in self.people):
                break

            self.current_time += self.time_step
            if self.current_time > self.max_time:
                break

        return self.history

    def summarize(self) -> Dict[str, Any]:
        """Return the final summary of the simulation records."""
        if not self.history:
            return {
                "Scenario": "Unknown",
                "Method": self.method.upper(),
                "Total People": 0,
                "Evacuated People": 0,
                "Evacuation Time": 0.0,
                "Average Speed": 0.0,
                "Maximum Density": 0.0,
                "Average Density": 0.0,
                "Exit Usage": {},
                "Density Matrix": np.zeros((1, 1)),
            }

        final_state = self.history[-1]
        exit_usage = final_state["exit_usage"]
        total_people = len(self.people)
        evacuated_people = int(final_state["evacuated_people"])
        evacuation_time = float(final_state["time"])
        average_speed = float(np.mean([entry["average_speed"] for entry in self.history])) if self.history else 0.0
        maximum_density = float(max(entry["maximum_density"] for entry in self.history)) if self.history else 0.0
        average_density = float(np.mean([entry["average_density"] for entry in self.history])) if self.history else 0.0

        summary = {
            "Scenario": "Simulation",
            "Method": self.method.upper(),
            "Total People": total_people,
            "Evacuated People": evacuated_people,
            "Evacuation Time": evacuation_time,
            "Average Speed": average_speed,
            "Maximum Density": maximum_density,
            "Average Density": average_density,
            "Exit Usage": exit_usage,
            "Density Matrix": final_state["density_matrix"],
        }
        return summary

    def deep_copy(self):
        return CrowdSimulator(
            self.building,
            deepcopy(self.exits),
            deepcopy(self.people),
            method=self.method,
            time_step=self.time_step,
            max_time=self.max_time,
            cell_size=self.cell_size,
            max_density=self.max_density,
            exit_radius=self.exit_radius,
        )
