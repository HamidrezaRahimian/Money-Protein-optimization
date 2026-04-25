import csv
import json
import os
import random
import multiprocessing
import time
from pathlib import Path

# --- 1. KONFIGURATION ---
def load_full_config():
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / 'config.json'
    if not config_path.exists():
        config_path = script_dir.parent / 'config.json'
    if not config_path.exists():
        raise FileNotFoundError(f"Config-Datei nicht gefunden.")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

FULL_CONFIG = load_full_config()
SOLVER_CFG = FULL_CONFIG.get("Solver1", {})
FITNESS_CFG = FULL_CONFIG.get("fitness", {})
# Kompatibilitätsalias für ältere Auswertungs- und Benchmark-Skripte
CONFIG = SOLVER_CFG

def load_database():
    database = {}
    raw_path = SOLVER_CFG.get("paths", {}).get("database", "")
    script_dir = Path(__file__).parent.resolve()
    file_path = (script_dir / raw_path).resolve()
    if not file_path.exists():
        file_path = (script_dir.parent / raw_path).resolve()

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_id = int(row['id'])
            database[p_id] = {
                "id": p_id, "name": row['name'], "price": float(row['price_eur']),
                "prot": float(row['protein_per_pack_g']), "port": int(row.get('estimated_portions', 0)),
                "taste": float(row['taste_score']), "kcal": float(row['calories_per_pack']),
                "max_u": int(row['max_units'])
            }
    return database

# --- 2. STATISTIK & REPARATUR ---
def get_stats_rep_c(vector_c, products, num_products):
    v_b = [0] * num_products
    for p_id in vector_c:
        if 0 < p_id <= num_products:
            v_b[p_id - 1] += 1
    s = {"prot": 0, "price": 0, "taste_sum": 0, "port": 0, "kcal": 0, "unique": 0, "total_packs": 0}
    for i, count in enumerate(v_b):
        if count > 0:
            d = products[i+1]
            s["prot"] += d["prot"] * count
            s["price"] += d["price"] * count
            s["kcal"] += d["kcal"] * count
            s["port"] += d["port"] * count
            s["taste_sum"] += d["taste"] * count
            s["total_packs"] += count
            s["unique"] += 1
    s["taste"] = (s["taste_sum"] / s["total_packs"]) if s["total_packs"] > 0 else 0
    return s

def repair_rep_c(individual, products, num_products):
    constraints = SOLVER_CFG.get("constraints", {})
    budget_limit = constraints.get("budget_limit", 50.0)
    counts = {}
    for idx, p_id in enumerate(individual):
        if p_id == 0: continue
        counts[p_id] = counts.get(p_id, 0) + 1
        if counts[p_id] > products[p_id]['max_u']:
            individual[idx] = 0 
    current_price = sum(products[pid]['price'] for pid in individual if pid != 0)
    if current_price > budget_limit:
        occupied = [i for i, val in enumerate(individual) if val != 0]
        random.shuffle(occupied)
        while current_price > budget_limit and occupied:
            idx = occupied.pop()
            current_price -= products[individual[idx]]['price']
            individual[idx] = 0
    return individual

# --- 3. WORKER FUNKTIONEN ---
def worker_calculate_fitness_c(args):
    vector_c, products, num_products = args
    s = get_stats_rep_c(vector_c, products, num_products)
    w = FITNESS_CFG
    fitness = (w.get("protein", 0) * s["prot"]) + (w.get("portions", 0) * s["port"]) + \
              (w.get("taste", 0) * s["taste"]) + (w.get("variety", 0) * s["unique"])
    target = SOLVER_CFG.get("constraints", {}).get("kcal_target", 10000)
    diff = s["kcal"] - target
    penalty = w.get("calorie_penalty", 3.0)
    fitness -= abs(diff) * penalty if diff > 0 else abs(diff) * (penalty * 0.1)
    return round(fitness, 2)

def worker_evolve_c(args):
    p1, p2, products, num_products, p_ids = args
    ga_settings = SOLVER_CFG.get("ga_settings", {})
    child = [p1[i] if random.random() < 0.5 else p2[i] for i in range(len(p1))]
    for i in range(len(child)):
        if random.random() < ga_settings.get("mutation_rate", 0.01):
            child[i] = random.choice([0] + p_ids)
    return repair_rep_c(child, products, num_products)

# --- 4. GA ENGINE ---
def run_ga_rep_c():
    start_time = time.time()
    products = load_database()
    p_ids = list(products.keys())
    num_products = max(p_ids)
    constraints = SOLVER_CFG.get("constraints", {})
    ga = SOLVER_CFG.get("ga_settings", {})
    
    # NEU: History-Liste
    history = []
    
    population = [repair_rep_c([random.choice([0] + p_ids) for _ in range(constraints.get("vector_length", 36))], 
                  products, num_products) for _ in range(ga.get('pop_size', 100))]
    
    best_overall_fitness = -float('inf')
    best_overall_individual = None
    generation_found = ga.get('generations', 100)

    # Parallelisierungs-Check
    num_cores = ga.get('parallel_cores', 1)
    is_child = multiprocessing.current_process().daemon
    pool = multiprocessing.Pool(processes=num_cores) if (num_cores > 1 and not is_child) else None
    mapper = pool.map if pool else map

    try:
        for gen in range(ga.get('generations', 100) + 1):
            scores = list(mapper(worker_calculate_fitness_c, [(ind, products, num_products) for ind in population]))
            sorted_indices = sorted(range(len(scores)), key=lambda k: scores[k], reverse=True)
            
            if scores[sorted_indices[0]] > best_overall_fitness:
                best_overall_fitness = scores[sorted_indices[0]]
                best_overall_individual = population[sorted_indices[0]][:]
                # NEU: History Punkt setzen
                history.append((time.time() - start_time, best_overall_fitness))

            if gen % ga.get('log_interval', 10) == 0:
                print(f"Gen {gen:4} | Max Fit: {best_overall_fitness:8.2f}")

            if best_overall_fitness >= SOLVER_CFG.get('stop_at_target', float('inf')):
                generation_found = gen
                break 

            elite = [population[i][:] for i in sorted_indices[:ga.get('elitism_count', 2)]]
            needed = ga.get('pop_size', 100) - len(elite)
            parents = [population[max(random.sample(range(len(population)), ga.get('tournament_size', 3)), key=lambda i: scores[i])][:] for _ in range(needed)]
            population = elite + list(mapper(worker_evolve_c, [(parents[i], parents[(i+1)%needed], products, num_products, p_ids) for i in range(needed)]))
    finally:
        if pool: pool.close(); pool.join()

    duration = time.time() - start_time
    history.append((duration, best_overall_fitness))
    # Rückgabe von 7 Werten
    return best_overall_individual, best_overall_fitness, products, num_products, duration, generation_found, history

# --- 5. MAIN BLOCK ---
if __name__ == '__main__':
    try:
        # KORREKTUR: 7 Variablen empfangen
        res_vec, res_fit, db, n_prod, duration, gen_found, hist = run_ga_rep_c()
        
        print("\n" + "="*60)
        print(f"{' FINALE AUSWERTUNG (SOLVER 1 - REPRESENTATION C) ':^60}")
        print("="*60)
        
        counts = {}
        for p_id in res_vec:
            if p_id > 0: counts[p_id] = counts.get(p_id, 0) + 1
        
        for p_id, count in counts.items():
            p = db[p_id]
            print(f"{count:2}x {p['name']:25} | {p['prot']*count:6.1f}g Protein")
        
        print("-" * 60)
        print(f"FITNESS:  {res_fit:10.2f}")
        print(f"DAUER:    {duration:.2f}s (Gefunden in Gen {gen_found})")
        print(f"HISTORY:  {len(hist)} Datenpunkte aufgezeichnet")
        print("-" * 60)
    except Exception as e:
        print(f"Fehler: {e}")