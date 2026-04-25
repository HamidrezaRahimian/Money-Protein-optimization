import csv
import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

BUDGET_EUR = 50.0
CALORIE_TARGET = 2300.0

# Try to read penalty settings from the shared representation B config if available.
try:
    from person2_core import load_representation_b_config
except Exception:
    load_representation_b_config = None


@dataclass(frozen=True)
class Product:
    id: int
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

    @property
    def calories_per_unit(self) -> float:
        return self.calories_per_pack

    @property
    def portions_per_unit(self) -> int:
        return self.estimated_portions


def load_products(csv_path: str) -> List[Product]:
    products: List[Product] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(
                Product(
                    id=int(row["id"]),
                    name=row["name"],
                    category=row["category"],
                    price_eur=float(row["price_eur"]),
                    weight_g=float(row["weight_g"]),
                    protein_per_100g=float(row["protein_per_100g"]),
                    calories_per_100g=float(row["calories_per_100g"]),
                    protein_per_pack_g=float(row["protein_per_pack_g"]),
                    calories_per_pack=float(row["calories_per_pack"]),
                    taste_score=float(row["taste_score"]),
                    estimated_portions=int(row["estimated_portions"]),
                    protein_type=row["protein_type"],
                    max_units=int(row["max_units"]),
                )
            )
    return products


@dataclass
class Solution:
    quantities: List[int]
    fitness: float = 0.0
    protein: float = 0.0
    cost: float = 0.0
    calories: float = 0.0
    portions: int = 0
    variety: int = 0
    average_taste: float = 0.0


class SolutionEvaluator:
    def __init__(self, products: List[Product], budget: float = BUDGET_EUR):
        self.products = products
        # prefer config values when possible
        self.budget = budget
        self.calorie_target = CALORIE_TARGET
        self.penalty_factor = 1.0 / 50.0
        self.under_mult = 0.1
        if load_representation_b_config is not None:
            try:
                cfg = load_representation_b_config()
                self.budget = float(cfg.budget_eur)
                self.calorie_target = float(cfg.kcal_target)
                # config stores penalty as 'calorie_penalty' (or 'penalty_kcal_factor')
                self.penalty_factor = float(cfg.weights.get("calorie_penalty", cfg.weights.get("penalty_kcal_factor", self.penalty_factor)))
                self.under_mult = float(cfg.weights.get("under_target_multiplier", self.under_mult))
            except Exception:
                # fall back to defaults if config read fails
                pass

    def evaluate(self, quantities: List[int]) -> Solution:
        cost = 0.0
        protein = 0.0
        calories = 0.0
        total_taste = 0.0
        total_units = 0
        portions = 0
        selected_types = set()

        for quantity, product in zip(quantities, self.products):
            if quantity <= 0:
                continue
            cost += product.price_eur * quantity
            protein += product.protein_per_pack_g * quantity
            calories += product.calories_per_pack * quantity
            total_taste += product.taste_score * quantity
            portions += product.estimated_portions * quantity
            total_units += quantity
            selected_types.add(product.protein_type)

        variety = len(selected_types)
        average_taste = total_taste / total_units if total_units > 0 else 0.0

        budget_violation = max(0.0, cost - self.budget)
        # Asymmetric kcal penalty around target (use same style as GA B)
        diff = calories - self.calorie_target

        kcal_penalty_amount = 0.0
        if diff > 0:
            kcal_penalty_amount = diff * self.penalty_factor
        else:
            kcal_penalty_amount = abs(diff) * (self.penalty_factor * self.under_mult)

        fitness = (
            protein
            + 2.0 * portions
            + 8.0 * variety
            + 15.0 * average_taste
            - 200.0 * budget_violation
            - kcal_penalty_amount
        )

        return Solution(
            quantities=list(quantities),
            fitness=fitness,
            protein=protein,
            cost=cost,
            calories=calories,
            portions=portions,
            variety=variety,
            average_taste=average_taste,
        )

    def is_valid(self, quantities: List[int]) -> bool:
        return self.evaluate(quantities).cost <= self.budget


def repair_solution(quantities: List[int], products: List[Product], budget: float) -> List[int]:
    repaired = list(quantities)
    cost = sum(p.price_eur * q for p, q in zip(products, repaired))
    while cost > budget:
        selected = [i for i, q in enumerate(repaired) if q > 0]
        if not selected:
            break
        index = random.choice(selected)
        repaired[index] -= 1
        cost = sum(p.price_eur * q for p, q in zip(products, repaired))
    for i, q in enumerate(repaired):
        repaired[i] = max(0, min(q, products[i].max_units))
    return repaired


def random_valid_solution(products: List[Product], budget: float) -> List[int]:
    quantities = [0] * len(products)
    indices = list(range(len(products)))
    random.shuffle(indices)

    for idx in indices:
        max_units = products[idx].max_units
        if max_units <= 0:
            continue
        if random.random() < 0.5:
            continue
        quantity = random.randint(0, max_units)
        quantities[idx] = quantity
        if sum(p.price_eur * q for p, q in zip(products, quantities)) > budget:
            quantities[idx] = 0
    return repair_solution(quantities, products, budget)


def greedy_protein_per_euro_solution(products: List[Product], budget: float) -> List[int]:
    quantities = [0] * len(products)
    remaining_budget = budget
    ranked = sorted(products, key=lambda p: p.protein_per_euro, reverse=True)
    for product in ranked:
        idx = products.index(product)
        while quantities[idx] < product.max_units and remaining_budget >= product.price_eur:
            quantities[idx] += 1
            remaining_budget -= product.price_eur
    return quantities


def mutate_quantities(quantities: List[int], products: List[Product], mutation_rate: float = 0.1) -> List[int]:
    child = list(quantities)
    for idx, product in enumerate(products):
        if random.random() < mutation_rate:
            change = random.choice([-1, 1])
            child[idx] = max(0, min(product.max_units, child[idx] + change))
            if random.random() < 0.1:
                child[idx] = random.randint(0, product.max_units)
    return child


def crossover_single_point(parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
    if len(parent1) != len(parent2):
        raise ValueError("Parent vectors must have equal length")
    point = random.randint(1, len(parent1) - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2


def tournament_selection(population: List[Solution], tournament_size: int = 3) -> Solution:
    competitors = random.sample(population, min(tournament_size, len(population)))
    return max(competitors, key=lambda s: s.fitness)


class IntegerQuantityGA:
    def __init__(
        self,
        products: List[Product],
        budget: float = BUDGET_EUR,
        population_size: int = 80,
        generations: int = 150,
        crossover_rate: float = 0.9,
        mutation_rate: float = 0.15,
        elitism_count: int = 4,
    ):
        self.products = products
        self.budget = budget
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count
        self.evaluator = SolutionEvaluator(products, budget)

    def initialize_population(self) -> List[Solution]:
        population: List[Solution] = []
        while len(population) < self.population_size:
            quantities = random_valid_solution(self.products, self.budget)
            solution = self.evaluator.evaluate(quantities)
            population.append(solution)
        return population

    def create_child(self, parent1: Solution, parent2: Solution) -> Solution:
        if random.random() < self.crossover_rate:
            child_quantities, _ = crossover_single_point(parent1.quantities, parent2.quantities)
        else:
            child_quantities = list(parent1.quantities)
        child_quantities = mutate_quantities(child_quantities, self.products, self.mutation_rate)
        child_quantities = repair_solution(child_quantities, self.products, self.budget)
        return self.evaluator.evaluate(child_quantities)

    def run(self, seed: Optional[int] = None) -> Solution:
        if seed is not None:
            random.seed(seed)
        population = self.initialize_population()
        best_solution = max(population, key=lambda s: s.fitness)

        for generation in range(self.generations):
            next_population: List[Solution] = []
            elites = sorted(population, key=lambda s: s.fitness, reverse=True)[: self.elitism_count]
            next_population.extend(elites)
            while len(next_population) < self.population_size:
                parent1 = tournament_selection(population)
                parent2 = tournament_selection(population)
                child = self.create_child(parent1, parent2)
                next_population.append(child)
            population = next_population
            current_best = max(population, key=lambda s: s.fitness)
            if current_best.fitness > best_solution.fitness:
                best_solution = current_best
        return best_solution


class HillClimbingLocalSearch:
    def __init__(
        self,
        products: List[Product],
        budget: float = BUDGET_EUR,
        max_iterations: int = 1500,
        restart_attempts: int = 5,
    ):
        self.products = products
        self.budget = budget
        self.max_iterations = max_iterations
        self.restart_attempts = restart_attempts
        self.evaluator = SolutionEvaluator(products, budget)

    def random_neighbor(self, quantities: List[int]) -> List[int]:
        neighbor = list(quantities)
        index = random.randrange(len(neighbor))
        if random.random() < 0.5:
            neighbor[index] = max(0, neighbor[index] - 1)
        else:
            neighbor[index] = min(self.products[index].max_units, neighbor[index] + 1)
        if random.random() < 0.2:
            alt_index = random.randrange(len(neighbor))
            if alt_index != index and neighbor[alt_index] > 0:
                neighbor[alt_index] = max(0, neighbor[alt_index] - 1)
                neighbor[index] = min(self.products[index].max_units, neighbor[index] + 1)
        return neighbor

    def improve(self, start_solution: List[int]) -> Solution:
        current = self.evaluator.evaluate(start_solution)
        best = current
        for iteration in range(self.max_iterations):
            candidate_quantities = self.random_neighbor(current.quantities)
            candidate_quantities = repair_solution(candidate_quantities, self.products, self.budget)
            candidate = self.evaluator.evaluate(candidate_quantities)
            if candidate.fitness > current.fitness:
                current = candidate
            if candidate.fitness > best.fitness:
                best = candidate
        return best

    def run(self, seed: Optional[int] = None) -> Solution:
        if seed is not None:
            random.seed(seed)

        best_solution: Optional[Solution] = None
        for _ in range(self.restart_attempts):
            start = greedy_protein_per_euro_solution(self.products, self.budget)
            candidate = self.improve(start)
            if best_solution is None or candidate.fitness > best_solution.fitness:
                best_solution = candidate
            random_start = random_valid_solution(self.products, self.budget)
            candidate = self.improve(random_start)
            if candidate.fitness > best_solution.fitness:
                best_solution = candidate
        assert best_solution is not None
        return best_solution


def summarize_solution(solution: Solution, products: List[Product]) -> Dict[str, object]:
    selected_items = [
        {
            "product_id": product.id,
            "name": product.name,
            "quantity": quantity,
            "cost": product.price_eur * quantity,
            "protein": product.protein_per_pack_g * quantity,
            "portions": product.estimated_portions * quantity,
        }
        for product, quantity in zip(products, solution.quantities)
        if quantity > 0
    ]
    return {
        "fitness": round(solution.fitness, 2),
        "protein": round(solution.protein, 2),
        "cost": round(solution.cost, 2),
        "calories": round(solution.calories, 2),
        "portions": solution.portions,
        "variety": solution.variety,
        "average_taste": round(solution.average_taste, 2),
        "selected_items": selected_items,
    }


def print_summary(title: str, summary: Dict[str, object]) -> None:
    print(f"--- {title} ---")
    print(f"Fitness: {summary['fitness']}")
    print(f"Protein: {summary['protein']} g")
    print(f"Cost: {summary['cost']} €")
    print(f"Calories: {summary['calories']} kcal")
    print(f"Portions: {summary['portions']}")
    print(f"Variety: {summary['variety']}")
    print(f"Average taste: {summary['average_taste']}")
    print("Selected items:")
    for item in summary["selected_items"]:
        print(
            f"  - {item['name']} x{item['quantity']} | cost={item['cost']:.2f} € | protein={item['protein']:.1f} g | portions={item['portions']}"
        )
    print()


def run_demo(csv_path: str = "data/lidl_products_30.csv") -> None:
    products = load_products(csv_path)
    ga = IntegerQuantityGA(products)
    ls = HillClimbingLocalSearch(products)

    ga_solution = ga.run(seed=42)
    ls_solution = ls.run(seed=42)

    print_summary("GA Variant (Integer Quantity)", summarize_solution(ga_solution, products))
    print_summary("Local Search Baseline (Hill Climbing)", summarize_solution(ls_solution, products))

    if ga_solution.fitness >= ls_solution.fitness:
        print("Winner: GA variant")
    else:
        print("Winner: Local search baseline")


if __name__ == "__main__":
    run_demo()
