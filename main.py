"""Command-line interface for the crowd evacuation modeling project."""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pandas as pd

from config import BUILDING_HEIGHT, BUILDING_WIDTH, CELL_SIZE, EXIT_RADIUS, MAX_DENSITY, MAX_TIME, NORMAL_SPEED, RANDOM_SEED, TIME_STEP
from models.building import Building
from models.exit import Exit
from simulation.crowd_simulator import CrowdSimulator
from simulation.scenarios import build_scenario_config, generate_people, make_building, make_exits
from visualization.animation import create_animation
from visualization.graphs import plot_comparison_graph, plot_density_curve, plot_evacuation_curve, plot_exit_use, plot_speed_curve
from visualization.heatmap import plot_density_heatmap

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_FOLDER = PROJECT_ROOT / "results"
RESULTS_FOLDER.mkdir(exist_ok=True)


def run_simulation_for_scenario(scenario_name: str, method: str = "euler", show_plots: bool = False):
    config = build_scenario_config(scenario_name)
    building = make_building(config)
    exits = make_exits(config.exit_positions)
    people = generate_people(config.people_count, building, exits, config.normal_speed, config.random_seed)

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
    summary["Scenario"] = scenario_name

    density_matrix = summary["Density Matrix"]
    if density_matrix.size:
        if show_plots:
            plot_density_heatmap(density_matrix, save_path=str(RESULTS_FOLDER / "density_heatmap.png"), title=f"{scenario_name} Density")
        else:
            plot_density_heatmap(density_matrix, save_path=str(RESULTS_FOLDER / "density_heatmap.png"), title=f"{scenario_name} Density")

    if history:
        plot_evacuation_curve(history, save_path=str(RESULTS_FOLDER / "evacuation_curve.png"))
        plot_speed_curve(history, save_path=str(RESULTS_FOLDER / "speed_curve.png"))
        plot_density_curve(history, save_path=str(RESULTS_FOLDER / "density_curve.png"))
        exit_usage = {exit.exit_id: exit.people_evacuated for exit in exits}
        if exit_usage:
            total = max(sum(exit_usage.values()), 1)
            normalized = {k: (v / total) * 100.0 for k, v in exit_usage.items()}
            plot_exit_use(normalized, save_path=str(RESULTS_FOLDER / "exit_use.png"))

    summary_row = {
        "Scenario": scenario_name,
        "Method": method.upper(),
        "Total People": summary["Total People"],
        "Evacuated People": summary["Evacuated People"],
        "Evacuation Time": summary["Evacuation Time"],
        "Average Speed": summary["Average Speed"],
        "Maximum Density": summary["Maximum Density"],
        "Average Density": summary["Average Density"],
    }

    for exit_number in range(1, max(1, len(exits) + 1)):
        exit_key = f"Exit {exit_number} Usage"
        usage_value = summary["Exit Usage"].get(exit_number, 0.0)
        summary_row[exit_key] = usage_value

    print_summary(summary_row)
    return summary_row, simulator


def run_method_comparison():
    import time

    scenario_name = "Euler vs RK4"
    config = build_scenario_config(scenario_name)
    building = make_building(config)
    exits = make_exits(config.exit_positions)
    base_people = generate_people(config.people_count, building, exits, config.normal_speed, config.random_seed)

    start = time.perf_counter()
    euler_simulator = CrowdSimulator(
        building=building,
        exits=[copy.deepcopy(exit_obj) for exit_obj in exits],
        people=copy.deepcopy(base_people),
        method="euler",
        time_step=TIME_STEP,
        max_time=MAX_TIME,
        cell_size=CELL_SIZE,
        max_density=MAX_DENSITY,
        exit_radius=EXIT_RADIUS,
    )
    euler_history = euler_simulator.run()
    euler_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    rk4_simulator = CrowdSimulator(
        building=building,
        exits=[copy.deepcopy(exit_obj) for exit_obj in exits],
        people=copy.deepcopy(base_people),
        method="rk4",
        time_step=TIME_STEP,
        max_time=MAX_TIME,
        cell_size=CELL_SIZE,
        max_density=MAX_DENSITY,
        exit_radius=EXIT_RADIUS,
    )
    rk4_history = rk4_simulator.run()
    rk4_elapsed = time.perf_counter() - start

    euler_summary = euler_simulator.summarize()
    rk4_summary = rk4_simulator.summarize()
    euler_summary["Scenario"] = scenario_name
    rk4_summary["Scenario"] = scenario_name

    comparison_rows = [
        {
            "Scenario": scenario_name,
            "Method": "Euler",
            "Total People": len(base_people),
            "Evacuated People": euler_summary["Evacuated People"],
            "Evacuation Time": euler_summary["Evacuation Time"],
            "Average Speed": euler_summary["Average Speed"],
            "Maximum Density": euler_summary["Maximum Density"],
            "Average Density": euler_summary["Average Density"],
            "Exit 1 Usage": euler_summary["Exit Usage"].get(1, 0.0),
            "Exit 2 Usage": euler_summary["Exit Usage"].get(2, 0.0),
            "Exit 3 Usage": euler_summary["Exit Usage"].get(3, 0.0),
            "Computation Time": euler_elapsed,
        },
        {
            "Scenario": scenario_name,
            "Method": "RK4",
            "Total People": len(base_people),
            "Evacuated People": rk4_summary["Evacuated People"],
            "Evacuation Time": rk4_summary["Evacuation Time"],
            "Average Speed": rk4_summary["Average Speed"],
            "Maximum Density": rk4_summary["Maximum Density"],
            "Average Density": rk4_summary["Average Density"],
            "Exit 1 Usage": rk4_summary["Exit Usage"].get(1, 0.0),
            "Exit 2 Usage": rk4_summary["Exit Usage"].get(2, 0.0),
            "Exit 3 Usage": rk4_summary["Exit Usage"].get(3, 0.0),
            "Computation Time": rk4_elapsed,
        },
    ]

    df = pd.DataFrame(comparison_rows)
    df.to_csv(RESULTS_FOLDER / "simulation_results.csv", index=False)

    plot_comparison_graph(comparison_rows, save_path=str(RESULTS_FOLDER / "method_comparison.png"))
    print_comparison_table(comparison_rows)
    return comparison_rows


def print_summary(summary: dict) -> None:
    print("\n----------------------------------------")
    print("Simulation Results")
    print("----------------------------------------")
    print(f"Scenario           : {summary.get('Scenario', 'Unknown')}")
    print(f"Numerical Method   : {summary.get('Method', 'Unknown')}")
    print(f"Total People       : {summary.get('Total People', 0)}")
    print(f"Evacuated          : {summary.get('Evacuated People', 0)}")
    print(f"Evacuation Time    : {summary.get('Evacuation Time', 0.0):.2f} seconds")
    print(f"Average Speed      : {summary.get('Average Speed', 0.0):.2f} m/s")
    print(f"Maximum Density    : {summary.get('Maximum Density', 0.0):.2f} persons/m²")
    print(f"Average Density    : {summary.get('Average Density', 0.0):.2f} persons/m²")

    usage = summary.get("Exit Usage", {})
    for key in sorted(usage):
        percentage = usage[key]
        print(f"Exit {key} Usage       : {percentage:.0f}%")

    print("----------------------------------------\n")


def print_comparison_table(rows: list) -> None:
    print("\n----------------------------------------")
    print("Euler vs RK4 Comparison")
    print("----------------------------------------")
    headers = ["Method", "Evacuation Time", "Avg Speed", "Computation Time"]
    print(f"{headers[0]:<10} {headers[1]:>18} {headers[2]:>12} {headers[3]:>18}")
    for row in rows:
        computation_time = row.get("Computation Time", 0.0)
        print(f"{row['Method']:<10} {row['Evacuation Time']:>18.2f} {row['Average Speed']:>12.2f} {computation_time:>18.6f}")
    print("----------------------------------------\n")


def run_all_scenarios():
    scenario_names = [
        "Normal Evacuation",
        "High Crowd",
        "Blocked Exit",
        "Three Exits",
        "Compare Exit Locations",
    ]
    rows = []
    for scenario_name in scenario_names:
        row, _ = run_simulation_for_scenario(scenario_name, method="euler", show_plots=False)
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_FOLDER / "simulation_results.csv", index=False)
    return rows


def print_menu():
    print("========================================")
    print(" Crowd Evacuation Modeling and Simulation")
    print("========================================")
    print("1. Normal Evacuation")
    print("2. High Crowd")
    print("3. Blocked Exit")
    print("4. Three Exits")
    print("5. Compare Exit Locations")
    print("6. Compare Euler vs RK4")
    print("7. Run All Scenarios")
    print("8. Exit")


def main():
    while True:
        try:
            print_menu()
            choice = input("\nEnter your choice: ").strip()
        except EOFError:
            print("\nInput stream closed. Exiting gracefully.")
            break

        if choice == "1":
            run_simulation_for_scenario("Normal Evacuation", method="euler", show_plots=True)
        elif choice == "2":
            run_simulation_for_scenario("High Crowd", method="euler", show_plots=True)
        elif choice == "3":
            run_simulation_for_scenario("Blocked Exit", method="euler", show_plots=True)
        elif choice == "4":
            run_simulation_for_scenario("Three Exits", method="euler", show_plots=True)
        elif choice == "5":
            run_simulation_for_scenario("Compare Exit Locations", method="euler", show_plots=True)
        elif choice == "6":
            run_method_comparison()
        elif choice == "7":
            run_all_scenarios()
        elif choice == "8":
            print("Exiting the crowd evacuation simulation.")
            break
        else:
            print("Invalid menu input. Please choose a valid option.")

        if choice != "8":
            try:
                input("\nPress Enter to return to the menu...")
            except EOFError:
                print("\nInput stream closed. Exiting gracefully.")
                break


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - user-friendly guard
        print(f"Simulation error: {exc}")
        sys.exit(1)
