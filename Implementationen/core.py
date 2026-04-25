from __future__ import annotations
import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Hilfsklassen für die Konsole ---
class _Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RED = "\033[91m"

def _c(text: str, color: str) -> str:
    return f"{color}{text}{_Ansi.RESET}"

def print_header(title: str) -> None:
    line = "=" * 72
    print(_c(line, _Ansi.CYAN))
    print(_c(title.center(72), _Ansi.BOLD + _Ansi.BLUE))
    print(_c(line, _Ansi.CYAN))

def print_kv(key: str, value: Any, color: str = "") -> None:
    prefix = _c(f"{key:20}", color) if color else f"{key:20}"
    print(f"{prefix}: {value}")

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

# --- Konfigurations-Logik ---
def load_representation_b_config(section_name: str = "Solver2", config_file_name: str = "config.json") -> Any:
    """
    Laedt die Konfiguration fuer einen spezifischen Solver aus der config.json.
    Beruecksichtigt die globale 'fitness' Kategorie.
    """
    
    # 1. Interne Default-Struktur (falls Datei fehlt oder Keys fehlen)
    class Config:
        def __init__(self):
            self.budget_eur = 50.0
            self.kcal_target = 10000.0
            self.stop_at_target = None
            self.weights = {
                "protein": 10.0, "portions": 1.5, "taste": 5.0, 
                "variety": 2.0, "calorie_penalty": 3.0
            }
            self.ga = {
                "population_size": 100, "generations": 200, 
                "mutation_rate": 0.02, "elitism_count": 5, "tournament_size": 3
            }
            self.local_search = {
                "max_iterations": 1000, "restart_attempts": 5
            }
            self.random_search = {
                "total_runs": 10000, "log_interval": 1000
            }
            self.paths = type('Paths', (), {'csv_path': Path("./data/lidl_products_30.csv")})

    cfg = Config()

    # 2. Pfad-Findung (Relativ zum Skript-Ort fuer Linux-Stabilitaet)
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / config_file_name
    
    # Fallback: Suche im Parent-Ordner
    if not config_path.exists():
        config_path = script_dir.parent / config_file_name

    if not config_path.exists():
        print(f"Hinweis: {config_file_name} nicht gefunden. Nutze Defaults.")
        return cfg

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            full_config = json.load(f)

        # 3. Globale Fitness-Gewichte laden
        if "fitness" in full_config:
            cfg.weights.update(full_config["fitness"])

        # 4. Spezifischen Solver-Abschnitt laden (Solver1, Solver2, Solver3, RandomSearch)
        if section_name in full_config:
            s = full_config[section_name]
            
            # Pfade laden
            if "paths" in s:
                db_path = s["paths"].get("database")
                if db_path:
                    # Pfad relativ zur Config-Datei aufloesen
                    cfg.paths.csv_path = (config_path.parent / db_path).resolve()
            
            # Constraints laden
            if "constraints" in s:
                c = s["constraints"]
                cfg.budget_eur = float(c.get("budget_limit", cfg.budget_eur))
                cfg.kcal_target = float(c.get("kcal_target", cfg.kcal_target))
                # Optional fuer GA Representation C
                cfg.vector_length = c.get("vector_length", 36)
            
            # GA Settings laden
            if "ga_settings" in s:
                gs = s["ga_settings"]
                cfg.ga.update({
                    "population_size": gs.get("pop_size", cfg.ga["population_size"]),
                    "generations": gs.get("generations", cfg.ga["generations"]),
                    "mutation_rate": gs.get("mutation_rate", cfg.ga["mutation_rate"]),
                    "elitism_count": gs.get("elitism_count", cfg.ga["elitism_count"]),
                    "tournament_size": gs.get("tournament_size", cfg.ga["tournament_size"])
                })
            
            # Local Search Settings laden
            if "local_search_settings" in s:
                ls = s["local_search_settings"]
                cfg.local_search.update({
                    "max_iterations": ls.get("max_iterations", cfg.local_search["max_iterations"]),
                    "restart_attempts": ls.get("restart_attempts", cfg.local_search["restart_attempts"])
                })

            # Random Search Settings laden
            if "settings" in s and section_name == "RandomSearch":
                rs = s["settings"]
                cfg.random_search.update({
                    "total_runs": rs.get("total_runs", cfg.random_search["total_runs"]),
                    "log_interval": rs.get("log_interval", cfg.random_search["log_interval"])
                })
            
            # Globaler Stop-Wert
            if "stop_at_target" in s:
                cfg.stop_at_target = float(s["stop_at_target"])

            print(f"Konfiguration '{section_name}' erfolgreich geladen.")
        else:
            print(f"Warnung: Sektion '{section_name}' nicht in {config_file_name} gefunden.")

    except Exception as e:
        print(f"Fehler beim Laden der Config: {e}")

    return cfg
    
def load_products(csv_path: str | Path) -> List[Product]:
    products = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV Datei nicht gefunden: {path.absolute()}")
    with open(path, newline="", encoding="utf-8") as h:
        for row in csv.DictReader(h):
            products.append(Product(int(row["id"]), row["store"], row["name"], row["category"], 
                                    float(row["price_eur"]), float(row["weight_g"]), float(row["protein_per_100g"]),
                                    float(row["calories_per_100g"]), float(row["protein_per_pack_g"]),
                                    float(row["calories_per_pack"]), float(row["taste_score"]),
                                    int(row["estimated_portions"]), row["protein_type"], int(row["max_units"])))
    return products

class SolutionEvaluator:
    def __init__(self, products: List[Product], config: Any):
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
        diff = calories - self.config.kcal_target
        fitness -= (diff * w.get("calorie_penalty", 3.0) if diff > 0 else abs(diff) * w.get("calorie_penalty", 3.0) * 0.1)
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

def print_solution_card(title, solution, products):
    print_header(title)
    print_kv("Fitness", round(solution.fitness, 2), _Ansi.YELLOW)
    print_kv("Protein", f"{solution.protein:.1f}g", _Ansi.YELLOW)
    print_kv("Kosten", f"{solution.cost:.2f} €", _Ansi.YELLOW)
    print(_c("Gewählte Artikel:", _Ansi.BOLD + _Ansi.CYAN))
    for p, q in zip(products, solution.quantities):
        if q > 0: print(f"  • {p.name:<28} x{q} ({p.protein_per_pack_g*q:.1f}g Protein)")
    print()

if __name__ == "__main__":
    print("Core Modul geladen. Nutze die anderen Dateien zum Ausführen.")