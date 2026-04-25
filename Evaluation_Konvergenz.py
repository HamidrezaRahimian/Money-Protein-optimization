import time
import matplotlib.pyplot as plt
import random
import numpy as np
import importlib.util
from pathlib import Path
import sys
import multiprocessing
import concurrent.futures

# --- DEINE MODUL-IMPORTE ---
from Implementationen.GA_Protein_Optimizer_C import (
    load_database, repair_rep_c, worker_calculate_fitness_c,
    get_stats_rep_c, CONFIG, worker_evolve_c,
)
from Implementationen.randomSearch import generate_random_solution, stats, fitness

# Dynamisches Laden von person2_core
core_path = Path(__file__).resolve().parent / 'hamid-folder' / 'person2_core.py'
spec = importlib.util.spec_from_file_location('person2_core', str(core_path))
person2_core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = person2_core
spec.loader.exec_module(person2_core)

# Aliases
load_rep_b_config = person2_core.load_representation_b_config
load_products_b = person2_core.load_products
IntegerQuantityGA = person2_core.IntegerQuantityGA
HillClimbingLocalSearch = person2_core.HillClimbingLocalSearch

# ==========================================
# KONFIGURATION DER KONVERGENZSTUDIE
# ==========================================
MAX_TIMEOUT = 10.0       # Abbrechen nach 10 Sekunden
SUCCESS_THRESHOLD = 14388 # Ziel-Fitness
NUM_RUNS = 50            # Anzahl der parallelen Testläufe

def measure_convergence_ga_c(products, p_ids):
    """Spezifische Zeitmessung für deinen GA (Rep C)."""
    num_products = max(p_ids)
    v_len = CONFIG['constraints']['vector_length']
    pop_size = CONFIG['ga_settings']['pop_size']
    
    start_time = time.time()
    population = [repair_rep_c([random.choice([0] + p_ids) for _ in range(v_len)], 
                  products, num_products) for _ in range(pop_size)]

    while (time.time() - start_time) < MAX_TIMEOUT:
        fit_args = [(ind, products, num_products) for ind in population]
        scores = [worker_calculate_fitness_c(arg) for arg in fit_args]
        
        current_best = max(scores)
        if current_best >= SUCCESS_THRESHOLD:
            return time.time() - start_time # Ziel erreicht!

        # Evolution
        sorted_indices = sorted(range(len(scores)), key=lambda k: scores[k], reverse=True)
        elite = [population[i][:] for i in sorted_indices[:CONFIG['ga_settings']['elite_size']]]
        offspring = []
        for _ in range(pop_size - len(elite)):
            p1_idx = max(random.sample(range(len(scores)), CONFIG['ga_settings']['tournament_size']), key=lambda i: scores[i])
            p2_idx = max(random.sample(range(len(scores)), CONFIG['ga_settings']['tournament_size']), key=lambda i: scores[i])
            offspring.append(worker_evolve_c((population[p1_idx], population[p2_idx], products, num_products, p_ids)))
        population = elite + offspring
    
    return None

def measure_convergence_random(products, p_ids):
    """Zeitmessung für Random Search."""
    num_products = max(p_ids)
    budget_limit = CONFIG['constraints']['budget_limit']
    start_time = time.time()
    
    while (time.time() - start_time) < MAX_TIMEOUT:
        ind = generate_random_solution(p_ids)
        s = stats(ind, products, num_products)
        if s["price"] <= budget_limit:
            if fitness(s) >= SUCCESS_THRESHOLD:
                return time.time() - start_time
    return None

def run_parallel_worker(run_id, products, p_ids):
    """Führt die Messungen für einen Run-Slot aus."""
    # Internes Multiprocessing im GA ausschalten (wichtig!)
    CONFIG['ga_settings']['parallel_cores'] = 1
    
    t_c = measure_convergence_ga_c(products, p_ids)
    t_r = measure_convergence_random(products, p_ids)
    
    # Person 2 GA (Rep B)
    t_b = None
    try:
        cfg_b = load_rep_b_config()
        products_b = load_products_b(cfg_b.paths.csv_path)
        ga_b = IntegerQuantityGA(products_b, config=cfg_b)
        t0 = time.time()
        res = ga_b.run(seed=run_id, time_limit=MAX_TIMEOUT, fitness_target=SUCCESS_THRESHOLD)      
        dur = time.time() - t0
        if res.fitness >= SUCCESS_THRESHOLD and dur <= MAX_TIMEOUT:
            t_b = dur
    except: pass

    return t_c, t_b, t_r

def evaluate_study():
    products = load_database()
    p_ids = list(products.keys())
    
    results = {"GA_C": [], "GA_B": [], "Random": []}

    print(f"\n{'='*60}")
    print(f"{'PARALLELE KONVERGENZSTUDIE':^60}")
    print(f"{'Ziel: >=' + str(SUCCESS_THRESHOLD) + ' | Max: ' + str(MAX_TIMEOUT) + 's':^60}")
    print(f"{'='*60}\n")

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_parallel_worker, i, products, p_ids) for i in range(NUM_RUNS)]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            tc, tb, tr = future.result()
            if tc: results["GA_C"].append(tc)
            if tb: results["GA_B"].append(tb)
            if tr: results["Random"].append(tr)
            print(f" Fortschritt: {i+1}/{NUM_RUNS} Läufe abgeschlossen...")

    # --- STATISTIK AUSGEBEN ---
    print("\n" + "#"*60)
    for key, times in results.items():
        count = len(times)
        if count > 0:
            print(f"{key:10}: {count:2}/{NUM_RUNS} Erfolge | Ø Zeit: {np.mean(times):.3f}s | Min: {np.min(times):.3f}s")
        else:
            print(f"{key:10}:  0/{NUM_RUNS} Erfolge (Timeout)")
    print("#"*60)

    # Boxplot
    valid_data = [times for times in results.values() if len(times) > 0]
    valid_labels = [name for name, times in results.items() if len(times) > 0]
    
    if valid_data:
        plt.figure(figsize=(10, 6))
        plt.boxplot(valid_data, labels=valid_labels)
        plt.ylabel("Zeit bis Zielerreichung (Sekunden)")
        plt.title(f"Konvergenzgeschwindigkeit (Parallele Messung, n={NUM_RUNS})")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.show()

if __name__ == "__main__":
    evaluate_study()