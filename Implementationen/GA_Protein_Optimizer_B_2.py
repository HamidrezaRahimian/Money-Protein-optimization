import csv
import json
import os
import random
import multiprocessing
import time
from pathlib import Path

# --- 1. KONFIGURATION MIT SPEZIFISCHEM ZUGRIFF ---
def load_full_config():
    """Lädt die gesamte config.json Datei sicher."""
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / 'config.json'

    if not config_path.exists():
        config_path = script_dir.parent / 'config.json'

    if not config_path.exists():
        raise FileNotFoundError(f"Config-Datei nicht gefunden unter: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Laden der gesamten Datei
FULL_CONFIG = load_full_config()

# Extraktion der spezifischen Sektionen für diesen Solver
# Wir nutzen .get() mit Fallbacks, um Abstürze bei fehlenden Keys zu vermeiden
SOLVER_CFG = FULL_CONFIG.get("Solver1", {})
FITNESS_CFG = FULL_CONFIG.get("fitness", {})

def load_database():
    database = {}
    # Pfad aus Solver2 -> paths -> database
    raw_path = SOLVER_CFG.get("paths", {}).get("database", "./data/lidl_products_30.csv")
    script_dir = Path(__file__).parent.resolve()
    
    file_path = (script_dir / raw_path).resolve()
    if not file_path.exists():
        file_path = (script_dir.parent / raw_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"Datenbank nicht gefunden: {file_path}")

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_id = int(row['id'])
            database[p_id] = {
                "id": p_id,
                "name": row['name'],
                "price": float(row['price_eur']),
                "prot": float(row['protein_per_pack_g']),
                "port": int(row.get('estimated_portions', 0)),
                "taste": float(row['taste_score']),
                "kcal": float(row['calories_per_pack']),
                "max_u": int(row['max_units'])
            }
    return database

# --- 2. STATISTIKEN ---
def get_stats_rep_b(vector_b, products):
    s = {"prot": 0, "price": 0, "taste_sum": 0, "port": 0, "kcal": 0, "unique": 0, "total_packs": 0}
    for i, count in enumerate(vector_b):
        if count > 0:
            p_id = i + 1
            if p_id in products:
                d = products[p_id]
                s["prot"] += d["prot"] * count
                s["price"] += d["price"] * count
                s["kcal"] += d["kcal"] * count
                s["port"] += d["port"] * count
                s["taste_sum"] += d["taste"] * count
                s["total_packs"] += count
                s["unique"] += 1
    s["taste"] = (s["taste_sum"] / s["total_packs"]) if s["total_packs"] > 0 else 0
    return s

# --- 3. REPARATUR ---
def repair_bitstring(individual, products):
    num_products = len(individual)
    # Budget aus Solver2 -> constraints
    constraints = SOLVER_CFG.get("constraints", {})
    budget_limit = constraints.get("budget_limit", 50.0)
    pack_limit = constraints.get("vector_length", 36)
    
    for i in range(num_products):
        p_id = i + 1
        if p_id in products and individual[i] > products[p_id]['max_u']:
            individual[i] = products[p_id]['max_u']

    while True:
        current_price = sum(individual[i] * products[i+1]['price'] for i in range(num_products) if (i+1) in products)
        current_packs = sum(individual)
        if current_price <= budget_limit and current_packs <= pack_limit:
            break
        active = [i for i, val in enumerate(individual) if val > 0]
        if not active: break
        idx = random.choice(active)
        individual[idx] -= 1
    return individual

# --- 4. FITNESS (NUTZT FITNESS_CFG) ---
def worker_calculate_fitness_b(args):
    vector_b, products = args
    s = get_stats_rep_b(vector_b, products)
    w = FITNESS_CFG # Nutzt die globale fitness-Sektion
    
    fitness = (w.get("protein", 0) * s["prot"]) + \
              (w.get("portions", 0) * s["port"]) + \
              (w.get("taste", 0) * s["taste"]) + \
              (w.get("variety", 0) * s["unique"])
    
    # Kalorien Penalty aus Solver2 constraints & fitness
    target = SOLVER_CFG.get("constraints", {}).get("kcal_target", 10000)
    diff = s["kcal"] - target
    penalty_factor = w.get("calorie_penalty", 3.0)

    if diff > 0:
        fitness -= diff * penalty_factor
    else:
        # 10% Penalty für Unterschreitung als Standard
        fitness -= abs(diff) * (penalty_factor * 0.1)
    return round(fitness, 2)

# --- 5. EVOLUTION ---
def worker_evolve_b(args):
    p1, p2, products = args
    num_products = len(p1)
    ga_settings = SOLVER_CFG.get("ga_settings", {})
    mut_rate = ga_settings.get("mutation_rate", 0.01)
    
    child = [p1[i] if random.random() < 0.5 else p2[i] for i in range(num_products)]
    for i in range(num_products):
        if random.random() < mut_rate:
            p_id = i + 1
            if p_id in products:
                child[i] = random.randint(0, products[p_id]['max_u'])
    return repair_bitstring(child, products)

# --- 6. GA ENGINE ---
def run_ga_bitstring():
    products = load_database()
    num_products = len(products)
    ga = SOLVER_CFG.get("ga_settings", {})
    stop_target = SOLVER_CFG.get("stop_at_target", float('inf'))
    
    population = []
    for _ in range(ga.get("pop_size", 100)):
        ind = [random.randint(0, 2) for _ in range(num_products)]
        population.append(repair_bitstring(ind, products))
        
    best_overall_fitness = -float('inf')
    best_overall_individual = None

    # --- ÄNDERUNG: Sicherer Umgang mit Pools ---
    num_cores = ga.get('parallel_cores', 1)
    is_child = multiprocessing.current_process().daemon

    if num_cores > 1 and not is_child:
        pool = multiprocessing.Pool(processes=num_cores)
        mapper = pool.map
    else:
        pool = None
        mapper = map

    try:
        for gen in range(ga.get("generations", 100) + 1):
            fit_args = [(ind, products) for ind in population]
            scores = list(mapper(worker_calculate_fitness_b, fit_args))
            
            sorted_indices = sorted(range(len(scores)), key=lambda k: scores[k], reverse=True)
            
            if scores[sorted_indices[0]] > best_overall_fitness:
                best_overall_fitness = scores[sorted_indices[0]]
                best_overall_individual = population[sorted_indices[0]][:]

            if gen % ga.get('log_interval', 10) == 0:
                print(f"Gen {gen:4} | Max Fit: {best_overall_fitness:8.2f}")
            
            if best_overall_fitness >= stop_target:
                break

            elite_size = ga.get('elitism_count', 2)
            elite = [population[i][:] for i in sorted_indices[:elite_size]]
            needed = ga.get("pop_size", 100) - elite_size
            
            parents = []
            t_size = ga.get('tournament_size', 3)
            for _ in range(needed):
                idx = max(random.sample(range(len(population)), t_size), key=lambda i: scores[i])
                parents.append(population[idx][:])
            
            evo_args = [(parents[i], parents[(i+1)%needed], products) for i in range(needed)]
            offspring = list(mapper(worker_evolve_b, evo_args))
            population = elite + offspring
    finally:
        if pool:
            pool.close()
            pool.join()

    return best_overall_individual, best_overall_fitness, products

if __name__ == '__main__':
    try:
        res_vec, res_fit, db = run_ga_bitstring()
        print("\n" + "="*60)
        print(f"{' FINALE AUSWERTUNG (SOLVER 1 & FITNESS) ':^60}")
        print("="*60)
        stats = get_stats_rep_b(res_vec, db)
        for i, count in enumerate(res_vec):
            if count > 0:
                p_id = i + 1
                if p_id in db:
                    p = db[p_id]
                    print(f"{count:2}x {p['name']:25} | {p['prot']*count:6.1f}g Protein")
        
        print("-" * 60)
        print(f"FITNESS:   {res_fit:10.2f}")
        print(f"PROTEIN:   {stats['prot']:10.1f}g")
        print(f"KALORIEN:  {stats['kcal']:10.1f}kcal")
        print(f"GESCHMACK: {stats['taste']:10.1f}/5.0")
        print("-" * 60)
        print(f"VEKTOR: {res_vec}")
    except Exception as e:
        print(f"\033[91mFehler: {e}\033[0m")