from __future__ import annotations

import csv
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- 1. Hilfsklassen für die Konsole ---
class _Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

def _supports_color() -> bool:
    import sys
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    term = sys.environ.get("TERM", "") if hasattr(sys, "environ") else ""
    return term != "" and term != "dumb"

def _c(text: str, color: str) -> str:
    return f"{color}{text}{_Ansi.RESET}" if _supports_color() else text

def print_header(title: str) -> None:
    line = "=" * 72
    print(_c(line, _Ansi.CYAN))
    print(_c(title.center(72), _Ansi.BOLD + _Ansi.BLUE))
    print(_c(line, _Ansi.CYAN))

def print_kv(key: str, value: Any, color: str = "") -> None:
    prefix = _c(f"{key:20}", color) if color else f"{key:20}"
    print(f"{prefix}: {value}")

# --- 2. Standards ---
DEFAULT_BUDGET_EUR = 50.0
DEFAULT_KCAL_TARGET = 10000.0
DEFAULT_WEIGHTS = {
    "protein": 10.0, "portions": 1.5, "variety": 2.0, "taste": 5.0,
    "calorie_penalty": 3.0, "budget_penalty": 400.0,
}
DEFAULT_GA_SETTINGS = {
    "population_size": 80, "generations": 500, "crossover_rate": 0.90,
    "mutation_rate": 0.10, "elitism_count": 4, "tournament_size": 3,
}
DEFAULT_LOCAL_SEARCH_SETTINGS = {
    "max_iterations": 1500, "restart_attempts": 6,
}

@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    config_path: Path
    csv_path: Path

@dataclass(frozen=True)
class Product:
    id: int
    store: str
    name: str
    category: str
    price_eur: float
    weight_g: float
    protein_per_100g: float
    calories_per_100g: float
    protein_per_pack_g: float
    calories_per_pack: float
    taste_score: float
    estimated_portions: int
    protein_type: str
    max_units: int

    @property
    def protein_per_euro(self) -> float:
        return self.protein_per_pack_g / self.price_eur if self.price_eur > 0 else 0.0

@dataclass
class Solution:
    quantities: List[int]
    fitness: float
    protein: float
    cost: float
    calories: float
    portions: int
    category_variety: int
    average_taste: float
    budget_violation: float
    is_valid: bool

@dataclass(frozen=True)
class RepresentationBConfig:
    budget_eur: float
    kcal_target: float
    weights: Dict[str, float]
    ga: Dict[str, float]
    local_search: Dict[str, int]
    paths: ProjectPaths

# --- 3. Pfad- & Konfig-Logik ---
def discover_project_paths(config_path: Optional[str] = None, csv_path: Optional[str] = None) -> ProjectPaths:
    here = Path(__file__).resolve().parent
    candidates = [here, here.parent, Path.cwd().resolve()]
    config_file = None
    if config_path:
        cp = Path(config_path)
        config_file = cp if cp.is_absolute() else (Path.cwd() / cp).resolve()
    else:
        for root in candidates:
            candidate = root / "config.json"
            if candidate.exists():
                config_file = candidate.resolve()
                break
    if config_file is None: raise FileNotFoundError("config.json not found")
    
    project_root = config_file.parent
    if csv_path:
        csv_file = Path(csv_path)
        csv_file = csv_file if csv_file.is_absolute() else (Path.cwd() / csv_file).resolve()
    else:
        with open(config_file, "r", encoding="utf-8") as h:
            raw = json.load(h)
        db_p = raw.get("paths", {}).get("database", "./data/lidl_products_30.csv")
        csv_file = (project_root / db_p).resolve()
    return ProjectPaths(project_root, config_file, csv_file)

def load_representation_b_config(config_path: Optional[str] = None, csv_path: Optional[str] = None) -> RepresentationBConfig:
    paths = discover_project_paths(config_path, csv_path)
    with open(paths.config_path, "r", encoding="utf-8") as h:
        raw = json.load(h)
    c, w_in, ga_in = raw.get("constraints", {}), raw.get("weights", {}), raw.get("ga_settings", {})
    weights = dict(DEFAULT_WEIGHTS)
    weights.update({k: float(w_in[k]) for k in ["protein", "portions", "variety", "taste"] if k in w_in})
    if "penalty_kcal_factor" in w_in: weights["calorie_penalty"] = float(w_in["penalty_kcal_factor"])
    ga = dict(DEFAULT_GA_SETTINGS)
    ga.update({"population_size": int(ga_in.get("pop_size", ga["population_size"])),
               "generations": int(ga_in.get("generations", ga["generations"])),
               "mutation_rate": float(ga_in.get("mutation_rate", ga["mutation_rate"]))})
    return RepresentationBConfig(float(c.get("budget_limit", 50)), float(c.get("kcal_target", 10000)), weights, ga, DEFAULT_LOCAL_SEARCH_SETTINGS, paths)

def load_products(csv_path: str | Path) -> List[Product]:
    products = []
    with open(csv_path, newline="", encoding="utf-8") as h:
        for row in csv.DictReader(h):
            products.append(Product(int(row["id"]), row["store"], row["name"], row["category"], 
                                    float(row["price_eur"]), float(row["weight_g"]), float(row["protein_per_100g"]),
                                    float(row["calories_per_100g"]), float(row["protein_per_pack_g"]),
                                    float(row["calories_per_pack"]), float(row["taste_score"]),
                                    int(row["estimated_portions"]), row["protein_type"], int(row["max_units"])))
    return products

# --- 4. Evaluation & Hilfsfunktionen ---
class SolutionEvaluator:
    def __init__(self, products: List[Product], config: RepresentationBConfig):
        self.products, self.config = products, config

    def evaluate(self, quantities: List[int]) -> Solution:
        cost = protein = calories = total_taste = total_units = portions = 0.0
        unique_products_count = 0 
        for q, p in zip(quantities, self.products):
            if q <= 0: continue
            cost += p.price_eur * q
            protein += p.protein_per_pack_g * q
            calories += p.calories_per_pack * q
            total_taste += p.taste_score * q
            total_units += q
            portions += p.estimated_portions * q
            unique_products_count += 1
        avg_taste = total_taste / total_units if total_units > 0 else 0.0
        w = self.config.weights
        fitness = (w.get("protein", 0)*protein + w.get("portions", 0)*portions + 
                   w.get("taste", 0)*avg_taste + w.get("variety", 0)*unique_products_count)
        penalty = w.get("calorie_penalty", 3.0)
        diff = calories - self.config.kcal_target
        fitness -= (diff * penalty if diff > 0 else abs(diff) * penalty * 0.1)
        return Solution(list(quantities), fitness, protein, cost, calories, int(portions), unique_products_count, avg_taste, max(0.0, cost - self.config.budget_eur), cost <= self.config.budget_eur)

def repair_solution(quantities: List[int], products: List[Product], budget: float) -> List[int]:
    repaired = [max(0, min(q, p.max_units)) for q, p in zip(quantities, products)]
    while sum(p.price_eur * q for p, q in zip(products, repaired)) > budget:
        indices = [i for i, q in enumerate(repaired) if q > 0]
        if not indices: break
        repaired[min(indices, key=lambda i: products[i].protein_per_euro)] -= 1
    return repaired

def random_valid_solution(products: List[Product], budget: float) -> List[int]:
    quantities = [0] * len(products)
    indices = list(range(len(products)))
    random.shuffle(indices)
    rem = budget
    for i in indices:
        if random.random() < 0.45: continue
        allowed = min(products[i].max_units, int(rem // products[i].price_eur))
        if allowed > 0:
            qty = random.randint(0, allowed)
            quantities[i] = qty
            rem -= qty * products[i].price_eur
    return repair_solution(quantities, products, budget)

# --- 5. Algorithmen (GA & Local Search) ---
class IntegerQuantityGA:
    def __init__(self, products, config=None):
        self.products, self.config = products, config or load_representation_b_config()
        self.evaluator = SolutionEvaluator(self.products, self.config)
        self.history_best_fitness = []

    def run(self, seed=None, time_limit=None, fitness_target=None):
        if seed is not None: random.seed(seed)
        start_time = time.time()
        ga = self.config.ga
        pop = [self.evaluator.evaluate(random_valid_solution(self.products, self.config.budget_eur)) for _ in range(ga["population_size"])]
        best = max(pop, key=lambda s: s.fitness)
        self.history_best_fitness = []

        for _ in range(ga["generations"]):
            # NEU: Abbruchbedingungen
            if time_limit and (time.time() - start_time) >= time_limit: break
            if fitness_target and best.fitness >= fitness_target: break

            elites = sorted(pop, key=lambda s: s.fitness, reverse=True)[:ga["elitism_count"]]
            nxt = list(elites)
            while len(nxt) < ga["population_size"]:
                p1, p2 = [max(random.sample(pop, k=ga["tournament_size"]), key=lambda s: s.fitness) for _ in range(2)]
                pt = random.randint(1, len(self.products)-1)
                child_q = p1.quantities[:pt] + p2.quantities[pt:]
                for i in range(len(child_q)):
                    if random.random() < ga["mutation_rate"]:
                        child_q[i] = max(0, min(self.products[i].max_units, child_q[i] + random.choice([-1, 1])))
                nxt.append(self.evaluator.evaluate(repair_solution(child_q, self.products, self.config.budget_eur)))
            pop = nxt
            curr = max(pop, key=lambda s: s.fitness)
            if curr.fitness > best.fitness: best = curr
            self.history_best_fitness.append(curr.fitness)
        return best

class HillClimbingLocalSearch:
    def __init__(self, products, config=None):
        self.products, self.config = products, config or load_representation_b_config()
        self.evaluator = SolutionEvaluator(self.products, self.config)
        self.total_evaluations = 0 
        self.history_best_fitness = []

    def run(self, seed=None, time_limit=None, fitness_target=None):
        if seed is not None: random.seed(seed)
        start_time = time.time()
        self.total_evaluations = 0
        self.history_best_fitness = []
        ls_cfg = self.config.local_search
        best_overall = None
        
        for _ in range(ls_cfg["restart_attempts"]):
            if time_limit and (time.time() - start_time) >= time_limit: break
            curr = self.evaluator.evaluate(random_valid_solution(self.products, self.config.budget_eur))
            for _ in range(ls_cfg["max_iterations"]):
                if time_limit and (time.time() - start_time) >= time_limit: break
                self.total_evaluations += 1
                neighbor_q = list(curr.quantities)
                idx = random.randrange(len(neighbor_q))
                neighbor_q[idx] = max(0, min(self.products[idx].max_units, neighbor_q[idx] + random.choice([-1, 1])))
                cand = self.evaluator.evaluate(repair_solution(neighbor_q, self.products, self.config.budget_eur))
                if cand.fitness > curr.fitness: curr = cand
                if fitness_target and curr.fitness >= fitness_target: break
            self.history_best_fitness.append(curr.fitness)
            if best_overall is None or curr.fitness > best_overall.fitness: best_overall = curr
            if fitness_target and best_overall.fitness >= fitness_target: break
        return best_overall

# --- 6. Anzeige ---
def print_solution_card(title, solution, products):
    print_header(title)
    print_kv("Fitness", round(solution.fitness, 2), _Ansi.YELLOW)
    print_kv("Protein", round(solution.protein, 2), _Ansi.YELLOW)
    print_kv("Cost", round(solution.cost, 2), _Ansi.YELLOW)
    print_kv("Unique Products", solution.category_variety, _Ansi.YELLOW)
    print(_c("Selected items:", _Ansi.BOLD + _Ansi.CYAN))
    for p, q in zip(products, solution.quantities):
        if q > 0: print(f"  • {p.name:<28} x{q} ({p.protein_per_pack_g*q:.1f}g Protein)")
    print()

if __name__ == "__main__":
    cfg = load_representation_b_config()
    prods = load_products(cfg.paths.csv_path)
    ga_res = IntegerQuantityGA(prods, cfg).run(seed=42)
    ls_res = HillClimbingLocalSearch(prods, cfg).run(seed=42)
    print_solution_card("GA RESULT", ga_res, prods)
    print_solution_card("LOCAL SEARCH RESULT", ls_res, prods)