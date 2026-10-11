"""Scenario definitions and initial crowd generation for the evacuation experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np

from config import BUILDING_HEIGHT, BUILDING_WIDTH, CELL_SIZE, MAX_DENSITY, NORMAL_SPEED, RANDOM_SEED
from math import ceil
from models.building import Building
from models.exit import Exit
from models.person import Person


@dataclass
class ScenarioConfig:
    name: str
    people_count: int
    exit_positions: Sequence[Tuple[float, float]]
    obstacle_rectangles: Sequence[Tuple[float, float, float, float]]
    building_width: float = BUILDING_WIDTH
    building_height: float = BUILDING_HEIGHT
    random_seed: int = RANDOM_SEED
    normal_speed: float = NORMAL_SPEED
    max_density: float = MAX_DENSITY
    cell_size: float = CELL_SIZE


def build_scenario_config(name: str) -> ScenarioConfig:
    scenarios = {
        "Normal Evacuation": ScenarioConfig(
            name="Normal Evacuation",
            people_count=100,
            exit_positions=[(15.0, 30.0), (85.0, 30.0)],
            obstacle_rectangles=[(45.0, 15.0, 55.0, 25.0), (40.0, 42.0, 60.0, 52.0)],
            random_seed=42,
        ),
        "High Crowd": ScenarioConfig(
            name="High Crowd",
            people_count=300,
            exit_positions=[(15.0, 30.0), (85.0, 30.0)],
            obstacle_rectangles=[(45.0, 15.0, 55.0, 25.0), (40.0, 42.0, 60.0, 52.0)],
            random_seed=42,
        ),
        "Blocked Exit": ScenarioConfig(
            name="Blocked Exit",
            people_count=300,
            exit_positions=[(15.0, 30.0), (85.0, 30.0)],
            obstacle_rectangles=[(45.0, 15.0, 55.0, 25.0), (40.0, 42.0, 60.0, 52.0)],
            random_seed=42,
        ),
        "Three Exits": ScenarioConfig(
            name="Three Exits",
            people_count=300,
            exit_positions=[(15.0, 30.0), (50.0, 10.0), (85.0, 30.0)],
            obstacle_rectangles=[(28.0, 22.0, 38.0, 32.0), (62.0, 22.0, 72.0, 32.0)],
            random_seed=42,
        ),
        "Compare Exit Locations": ScenarioConfig(
            name="Compare Exit Locations",
            people_count=200,
            exit_positions=[(15.0, 15.0), (85.0, 45.0)],
            obstacle_rectangles=[(40.0, 16.0, 60.0, 26.0), (40.0, 34.0, 60.0, 44.0)],
            random_seed=42,
        ),
        "Euler vs RK4": ScenarioConfig(
            name="Euler vs RK4",
            people_count=120,
            exit_positions=[(20.0, 30.0), (80.0, 30.0)],
            obstacle_rectangles=[(45.0, 18.0, 55.0, 30.0)],
            random_seed=42,
        ),
    }
    return scenarios[name]


def generate_people(
    count: int,
    building: Building,
    exits: Sequence[Exit],
    normal_speed: float = NORMAL_SPEED,
    seed: int = RANDOM_SEED,
) -> List[Person]:
    """Generate people uniformly at random inside the building without placing them in obstacles or on exits."""
    rng = np.random.default_rng(seed)
    people: List[Person] = []
    attempts = 0
    if count <= 0:
        return people

    while len(people) < count and attempts < count * 500:
        x = rng.uniform(4.0, building.width - 4.0)
        y = rng.uniform(4.0, building.height - 4.0)
        position = np.array([x, y], dtype=float)

        inside_obstacle = building.contains_point(position)
        too_close_to_exit = any(np.linalg.norm(position - exit.position) < 3.5 for exit in exits)

        if not inside_obstacle and not too_close_to_exit:
            person = Person(len(people) + 1, x, y, normal_speed)
            people.append(person)
        attempts += 1

    if len(people) != count:
        raise ValueError(f"Could not generate {count} valid starting positions.")
    return people


def make_building(config: ScenarioConfig) -> Building:
    building = Building(config.building_width, config.building_height)
    for obstacle in config.obstacle_rectangles:
        building.add_obstacle(*obstacle)
    return building


def make_exits(exit_positions: Sequence[Tuple[float, float]]) -> List[Exit]:
    return [Exit(index + 1, x, y) for index, (x, y) in enumerate(exit_positions)]
