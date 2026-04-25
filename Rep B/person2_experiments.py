from __future__ import annotations

"""
Experiments and evaluation runner for Person 2.
Adapted to the team's file structure.
"""

import argparse
import csv
import statistics
from itertools import product
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt

from person2_core import (
    HillClimbingLocalSearch,
    IntegerQuantityGA,
    RepresentationBConfig,
    Solution,
    _Ansi,
    _c,
    load_products,
    load_representation_b_config,
    print_header,
    print_kv,
    print_solution_card,
)


def repeated_runs_ga(products, runs: int, config: RepresentationBConfig, **ga_kwargs) -> List[Solution]:
    return [IntegerQuantityGA(products, config=config, **ga_kwargs).run(seed=seed) for seed in range(runs)]


def repeated_runs_local_search(products, runs: int, config: RepresentationBConfig, **ls_kwargs) -> List[Solution]:
    return [HillClimbingLocalSearch(products, config=config, **ls_kwargs).run(seed=seed) for seed in range(runs)]


def metrics_from_results(results: List[Solution]) -> Dict[str, float]:
    fitness_values = [r.fitness for r in results]
    protein_values = [r.protein for r in results]
    cost_values = [r.cost for r in results]
    valid_count = sum(1 for r in results if r.is_valid)
    return {
        "runs": len(results),
        "best_fitness": max(fitness_values),
        "mean_fitness": statistics.mean(fitness_values),
        "std_fitness": statistics.pstdev(fitness_values) if len(results) > 1 else 0.0,
        "best_protein": max(protein_values),
        "mean_protein": statistics.mean(protein_values),
        "mean_cost": statistics.mean(cost_values),
        "valid_rate": valid_count / len(results) if results else 0.0,
    }


def save_rows_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_boxplot(path: Path, ga_results: List[Solution], ls_results: List[Solution]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.boxplot([
        [r.fitness for r in ga_results],
        [r.fitness for r in ls_results],
    ], labels=["GA-B", "HillClimbing-B"])
    plt.ylabel("Fitness")
    plt.title("Representation B: Final fitness over repeated runs")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_convergence(path: Path, products, config: RepresentationBConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ga = IntegerQuantityGA(products, config=config)
    ls = HillClimbingLocalSearch(products, config=config)
    ga.run(seed=123)
    ls.run(seed=123)

    plt.figure(figsize=(8, 5))
    if ga.history_best_fitness:
        plt.plot(range(1, len(ga.history_best_fitness) + 1), ga.history_best_fitness, label="GA-B")
    if ls.history_best_fitness:
        plt.plot(range(1, len(ls.history_best_fitness) + 1), ls.history_best_fitness, label="HillClimbing-B")
    plt.xlabel("Iteration / restart index")
    plt.ylabel("Best fitness")
    plt.title("Representation B: convergence overview")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def run_parameter_study(products, config: RepresentationBConfig, output_dir: Path, runs_per_setting: int = 5) -> None:
    study_grid = {
        "population_size": [50, 80],
        "generations": [120, 180],
        "mutation_rate": [0.05, 0.10],
        "elitism_count": [2, 4],
    }
    rows: List[Dict[str, object]] = []
    for population_size, generations, mutation_rate, elitism_count in product(
        study_grid["population_size"],
        study_grid["generations"],
        study_grid["mutation_rate"],
        study_grid["elitism_count"],
    ):
        results = repeated_runs_ga(
            products,
            runs=runs_per_setting,
            config=config,
            population_size=population_size,
            generations=generations,
            mutation_rate=mutation_rate,
            elitism_count=elitism_count,
        )
        rows.append({
            "population_size": population_size,
            "generations": generations,
            "mutation_rate": mutation_rate,
            "elitism_count": elitism_count,
            **metrics_from_results(results),
        })
    save_rows_csv(output_dir / "person2_parameter_study.csv", rows)


def print_solution(title: str, solution: Solution, products) -> None:
    summary = summarize_solution(solution, products)
    print(f"\n{title}")
    print(f"  fitness = {summary['fitness']}")
    print(f"  protein = {summary['protein']} g")
    print(f"  cost = {summary['cost']} €")
    print(f"  calories = {summary['calories']} kcal")
    print(f"  valid = {summary['is_valid']}")


def run_full_demo(runs: int = 20, output_dir: Optional[str] = None, config_path: Optional[str] = None, csv_path: Optional[str] = None) -> None:
    config = load_representation_b_config(config_path=config_path, csv_path=csv_path)
    products = load_products(config.paths.csv_path)
    output = Path(output_dir) if output_dir else (config.paths.project_root / "results" / "person2")

    ga_results = repeated_runs_ga(products, runs=runs, config=config)
    ls_results = repeated_runs_local_search(products, runs=runs, config=config)

    ga_metrics = {"algorithm": "GA-B", **metrics_from_results(ga_results)}
    ls_metrics = {"algorithm": "HillClimbing-B", **metrics_from_results(ls_results)}

    save_rows_csv(output / "person2_metrics.csv", [ga_metrics, ls_metrics])
    plot_boxplot(output / "person2_boxplot.png", ga_results, ls_results)
    plot_convergence(output / "person2_convergence.png", products, config)
    run_parameter_study(products, config, output, runs_per_setting=max(3, min(5, runs)))

    print_solution("Best GA-B result", max(ga_results, key=lambda s: s.fitness), products)
    print_solution("Best HillClimbing-B result", max(ls_results, key=lambda s: s.fitness), products)
    print(f"\nSaved results to: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--output", default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()
    run_full_demo(runs=args.runs, output_dir=args.output, config_path=args.config, csv_path=args.csv)
