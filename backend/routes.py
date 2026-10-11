
"""REST API routes for the crowd evacuation simulation."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pandas as pd
from flask import Blueprint, jsonify, request, send_file

from config import (
    CELL_SIZE,
    EXIT_RADIUS,
    MAX_DENSITY,
    MAX_TIME,
    TIME_STEP,
)
from simulation.crowd_simulator import CrowdSimulator
from simulation.scenarios import (
    build_scenario_config,
    generate_people,
    make_building,
    make_exits,
)

api = Blueprint("api", __name__)

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
RESULTS_FILE = RESULTS_DIR / "simulation_results.csv"

LAST_RESULTS: dict[str, Any] = {
    "success": False,
    "message": "No simulation has run yet.",
}

SCENARIO_MAP = {
    "normal": "Normal Evacuation",
    "high_crowd": "High Crowd",
    "blocked_exit": "Blocked Exit",
    "three_exits": "Three Exits",
    "exit_locations": "Compare Exit Locations",
    "euler_vs_rk4": "Euler vs RK4",
}


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def to_list(value: Any) -> list:
    """Convert NumPy arrays and tuples into JSON-compatible lists."""
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def normalize_exit_usage(exit_usage: dict) -> dict[str, float]:
    if not exit_usage:
        return {}

    total = sum(float(value) for value in exit_usage.values())
    if total <= 0:
        return {}

    return {
        f"Exit {key}": round(float(value) / total * 100.0, 2)
        for key, value in sorted(exit_usage.items(), key=lambda item: str(item[0]))
    }


def serialize_people(people_states: list) -> list[dict]:
    people = []

    for person in people_states:
        people.append({
            "id": person.get("id"),
            "x": float(person.get("x", 0.0)),
            "y": float(person.get("y", 0.0)),
            "vx": float(person.get("vx", 0.0)),
            "vy": float(person.get("vy", 0.0)),
            "speed": float(person.get("speed", 0.0)),
            "evacuated": bool(person.get("evacuated", False)),
        })

    return people


def build_timeline(history: list[dict]) -> list[dict]:
    timeline = []

    for entry in history:
        density = entry.get("density_matrix")

        timeline.append({
            "time": float(entry.get("time", 0.0)),
            "remaining_people": int(entry.get("remaining_people", 0)),
            "evacuated_people": int(entry.get("evacuated_people", 0)),
            "average_speed": float(entry.get("average_speed", 0.0)),
            "maximum_density": float(entry.get("maximum_density", 0.0)),
            "average_density": float(entry.get("average_density", 0.0)),
            "density": to_list(density),
            "people": serialize_people(entry.get("people_states", [])),
        })

    return timeline


def build_payload(
    summary: dict,
    history: list[dict],
    scenario_name: str,
    method_name: str,
    building: Any,
    exits: list,
) -> dict:
    density = summary.get("Density Matrix")

    return {
        "success": True,
        "scenario": scenario_name,
        "method": method_name,
        "total_people": int(summary.get("Total People", 0)),
        "evacuated_people": int(summary.get("Evacuated People", 0)),
        "evacuation_time": float(summary.get("Evacuation Time", 0.0)),
        "average_speed": float(summary.get("Average Speed", 0.0)),
        "maximum_density": float(summary.get("Maximum Density", 0.0)),
        "average_density": float(summary.get("Average Density", 0.0)),
        "exit_usage": normalize_exit_usage(summary.get("Exit Usage", {})),
        "density_matrix": to_list(density),
        "history": [
            {
                "time": float(item.get("time", 0.0)),
                "remaining_people": int(item.get("remaining_people", 0)),
                "evacuated_people": int(item.get("evacuated_people", 0)),
                "average_speed": float(item.get("average_speed", 0.0)),
                "maximum_density": float(item.get("maximum_density", 0.0)),
                "average_density": float(item.get("average_density", 0.0)),
            }
            for item in history
        ],
        "timeline": build_timeline(history),
        "building": {
            "width": float(getattr(building, "width", 100.0)),
            "height": float(getattr(building, "height", 60.0)),
            "obstacles": [
                [float(x1), float(y1), float(x2), float(y2)]
                for x1, y1, x2, y2 in getattr(building, "obstacles", [])
            ],
        },
        "exits": [
            {
                "id": int(getattr(exit_item, "exit_id", index + 1)),
                "x": float(exit_item.position[0]),
                "y": float(exit_item.position[1]),
                "available": bool(getattr(exit_item, "available", True)),
            }
            for index, exit_item in enumerate(exits or [])
        ],
    }


def run_single_scenario(
    scenario_name: str,
    method: str,
    people_count: int,
) -> dict:
    config = build_scenario_config(scenario_name)
    config.people_count = people_count

    building = make_building(config)
    exits = make_exits(config.exit_positions)

    if scenario_name == "Blocked Exit" and len(exits) > 1:
        exits[1].block()

    people = generate_people(
        config.people_count,
        building,
        exits,
        config.normal_speed,
        config.random_seed,
    )

    simulator = CrowdSimulator(
        building=building,
        exits=exits,
        people=people,
        method=method,
        time_step=TIME_STEP,
        max_time=MAX_TIME,
        cell_size=CELL_SIZE,
        max_density=MAX_DENSITY,
        exit_radius=EXIT_RADIUS,
    )

    history = simulator.run()
    summary = simulator.summarize()

    return build_payload(
        summary,
        history,
        scenario_name,
        method.upper(),
        building,
        exits,
    )


def run_method_comparison(scenario_name: str, people_count: int) -> dict:
    config = build_scenario_config(scenario_name)
    config.people_count = people_count

    building = make_building(config)
    exits = make_exits(config.exit_positions)

    base_people = generate_people(
        config.people_count,
        building,
        exits,
        config.normal_speed,
        config.random_seed,
    )

    results = {}

    for method_name in ("euler", "rk4"):
        simulator = CrowdSimulator(
            building=building,
            exits=copy.deepcopy(exits),
            people=copy.deepcopy(base_people),
            method=method_name,
            time_step=TIME_STEP,
            max_time=MAX_TIME,
            cell_size=CELL_SIZE,
            max_density=MAX_DENSITY,
            exit_radius=EXIT_RADIUS,
        )

        history = simulator.run()
        summary = simulator.summarize()

        results[method_name] = build_payload(
            summary,
            history,
            scenario_name,
            method_name.upper(),
            building,
            simulator.exits,
        )

    return {
        "success": True,
        "scenario": scenario_name,
        "method": "comparison",
        "total_people": people_count,
        "summary": {
            "euler": results["euler"],
            "rk4": results["rk4"],
        },
        "comparisons": [results["euler"], results["rk4"]],
    }


@api.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Crowd Evacuation Simulation API is running",
    })


@api.route("/api/scenarios", methods=["GET"])
def get_scenarios():
    return jsonify({"scenarios": list(SCENARIO_MAP.keys())})


@api.route("/api/simulate", methods=["POST"])
def simulate():
    global LAST_RESULTS

    data = request.get_json(silent=True) or {}

    scenario_key = str(data.get("scenario", "normal")).strip().lower()
    method = str(data.get("method", "euler")).strip().lower()

    if scenario_key not in SCENARIO_MAP:
        return jsonify({
            "success": False,
            "error": "Invalid scenario name.",
        }), 400

    if method not in {"euler", "rk4"}:
        return jsonify({
            "success": False,
            "error": "Method must be 'euler' or 'rk4'.",
        }), 400

    try:
        people_count = int(data.get("people", 100))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Population must be a valid integer.",
        }), 400

    if not 1 <= people_count <= 1000:
        return jsonify({
            "success": False,
            "error": "Population must be between 1 and 1000.",
        }), 400

    try:
        scenario_name = SCENARIO_MAP[scenario_key]

        if scenario_key == "euler_vs_rk4":
            payload = run_method_comparison(scenario_name, people_count)
        else:
            payload = run_single_scenario(
                scenario_name,
                method,
                people_count,
            )

        ensure_results_dir()

        # Save the main result or comparison summary to CSV.
        if scenario_key == "euler_vs_rk4":
            rows = [
                {
                    "Scenario": scenario_name,
                    "Method": method_name.upper(),
                    "Total People": payload["summary"][method_name]["total_people"],
                    "Evacuated People": payload["summary"][method_name]["evacuated_people"],
                    "Evacuation Time": payload["summary"][method_name]["evacuation_time"],
                    "Average Speed": payload["summary"][method_name]["average_speed"],
                    "Maximum Density": payload["summary"][method_name]["maximum_density"],
                    "Average Density": payload["summary"][method_name]["average_density"],
                }
                for method_name in ("euler", "rk4")
            ]
        else:
            rows = [{
                "Scenario": scenario_name,
                "Method": method.upper(),
                "Total People": payload["total_people"],
                "Evacuated People": payload["evacuated_people"],
                "Evacuation Time": payload["evacuation_time"],
                "Average Speed": payload["average_speed"],
                "Maximum Density": payload["maximum_density"],
                "Average Density": payload["average_density"],
            }]

        pd.DataFrame(rows).to_csv(RESULTS_FILE, index=False)
        LAST_RESULTS = payload

        return jsonify(payload)

    except Exception as exc:
        # Full details appear in the Flask terminal for debugging.
        import traceback
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@api.route("/api/results", methods=["GET"])
def get_latest_results():
    return jsonify(LAST_RESULTS)


@api.route("/api/results/csv", methods=["GET"])
def download_results_csv():
    ensure_results_dir()

    if not RESULTS_FILE.exists():
        return jsonify({
            "success": False,
            "error": "No CSV result exists yet.",
        }), 404

    return send_file(
        RESULTS_FILE,
        as_attachment=True,
        download_name="simulation_results.csv",
    )
