import time
import matplotlib.pyplot as plt
import random
import numpy as np
import importlib.util
from pathlib import Path
import sys
import multiprocessing
import concurrent.futures

# --- IMPORTE AUS DEINEN MODULEN ---
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
# ZENTRALE STEUERUNG
# ==========================================
BENCHMARK_DURATION = 2  # Sekunden pro Lauf
NUM_RUNS = 50           # Anzahl der Wiederholungen
NUM_SAMPLES = 100       # Datenpunkte für die Zeitachse

def run_single_benchmark(algo_type, duration, products, p_ids):
    """Führt einen einzelnen Benchmark-Lauf aus (Sequentiell innerhalb des Workers)."""
    num_products = max(p_ids)
    budget_limit = CONFIG['constraints']['budget_limit']
    
    start_time = time.time()
    history_t = [0]
    history_f = [0]
    best_fit = 0
    
    if algo_type == "GA":
        v_len = CONFIG['constraints']['vector_length']
        pop_size = CONFIG['ga_settings']['pop_size']
        population = [repair_rep_c([random.choice([0] + p_ids) for _ in range(v_len)], 
                      products, num_products) for _ in range(pop_size)]

    while (time.time() - start_time) < duration:
        if algo_type == "Random":
            ind = generate_random_solution(p_ids)
            s = stats(ind, products, num_products)
            current_fit = fitness(s) if s["price"] <= budget_limit else -1
        else: # GA (Rep C)
            fit_args = [(ind, products, num_products) for ind in population]
            scores = [worker_calculate_fitness_c(arg) for arg in fit_args]
            current_fit = max(scores)
            
            # Evolution (Tournament & Crossover)
            sorted_indices = sorted(range(len(scores)), key=lambda k: scores[k], reverse=True)
            elite = [population[i][:] for i in sorted_indices[:CONFIG['ga_settings']['elite_size']]]
            offspring = []
            needed = pop_size - len(elite)
            for _ in range(needed):
                p1_idx = max(random.sample(range(len(scores)), CONFIG['ga_settings']['tournament_size']), key=lambda i: scores[i])
                p2_idx = max(random.sample(range(len(scores)), CONFIG['ga_settings']['tournament_size']), key=lambda i: scores[i])
                # Wichtig: Mutation_rate wird aus CONFIG gelesen
                child = worker_evolve_c((population[p1_idx], population[p2_idx], products, num_products, p_ids))
                offspring.append(child)
            population = elite + offspring

        if current_fit > best_fit:
            best_fit = current_fit
            history_t.append(time.time() - start_time)
            history_f.append(best_fit)
            
    history_t.append(duration)
    history_f.append(best_fit)
    return history_t, history_f

def run_full_cycle_worker(run_id, products, p_ids):
    """
    Worker-Funktion: Führt alle Algorithmen für einen einzelnen Run-Index aus.
    Diese Funktion läuft parallel in einem eigenen Prozess.
    """
    # Deaktiviere inneres Multiprocessing für diesen Worker
    CONFIG['ga_settings']['parallel_cores'] = 1
    common_grid = np.linspace(0, BENCHMARK_DURATION, NUM_SAMPLES)
    
    # 1. Random Search
    t_r, f_r = run_single_benchmark("Random", BENCHMARK_DURATION, products, p_ids)
    interp_r = np.interp(common_grid, t_r, f_r)
    
    # 2. GA (Rep C)
    t_g, f_g = run_single_benchmark("GA", BENCHMARK_DURATION, products, p_ids)
    interp_g = np.interp(common_grid, t_g, f_g)

    # 3. Person2 GA
    interp_pb = np.zeros(NUM_SAMPLES)
    try:
        cfg_b = load_rep_b_config()
        products_b = load_products_b(cfg_b.paths.csv_path)
        ga_b = IntegerQuantityGA(products_b, config=cfg_b)
        t0 = time.time()
        best_b = ga_b.run(seed=run_id)
        elapsed = time.time() - t0
        hist = getattr(ga_b, 'history_best_fitness', [])
        t_pb = [0.0] + [min(elapsed, BENCHMARK_DURATION) * (i+1)/len(hist) for i in range(len(hist))] if hist else [0, BENCHMARK_DURATION]
        f_pb = [0.0] + hist if hist else [best_b.fitness, best_b.fitness]
        interp_pb = np.interp(common_grid, t_pb, f_pb)
    except: pass

    # 4. Person2 Local Search
    interp_pl = np.zeros(NUM_SAMPLES)
    try:
        ls_b = HillClimbingLocalSearch(products_b, config=cfg_b)
        t0 = time.time()
        best_ls = ls_b.run(seed=run_id)
        elapsed = time.time() - t0
        lhist = getattr(ls_b, 'history_best_fitness', [])
        t_pl = [0.0] + [min(elapsed, BENCHMARK_DURATION) * (i+1)/len(lhist) for i in range(len(lhist))] if lhist else [0, BENCHMARK_DURATION]
        f_pl = [0.0] + lhist if lhist else [best_ls.fitness, best_ls.fitness]
        interp_pl = np.interp(common_grid, t_pl, f_pl)
    except: pass

    return interp_r, interp_g, interp_pb, interp_pl

SUCCESS_THRESHOLD = 14388

def evaluate_study_parallel():
    products = load_database()
    p_ids = list(products.keys())
    common_time_grid = np.linspace(0, BENCHMARK_DURATION, NUM_SAMPLES)
    
    all_random, all_ga, all_p2_ga, all_p2_ls = [], [], [], []

    print(f"\n{'='*60}")
    print(f"{'STARTE PARALLELE STUDIE (' + str(NUM_RUNS) + ' LÄUFE)':^60}")
    print(f"{'Ziel-Fitness: > ' + str(SUCCESS_THRESHOLD):^60}")
    print(f"{'='*60}\n")

    start_study = time.time()
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_full_cycle_worker, i, products, p_ids) for i in range(NUM_RUNS)]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            res_r, res_g, res_pb, res_pl = future.result()
            all_random.append(res_r)
            all_ga.append(res_g)
            all_p2_ga.append(res_pb)
            all_p2_ls.append(res_pl)
            if (i + 1) % 5 == 0:
                print(f"Fortschritt: {i+1}/{NUM_RUNS} Läufe abgeschlossen...")

    # --- ERFOLGSQUOTEN BERECHNEN ---
    # Wir schauen uns jeweils den letzten Fitness-Wert (Index -1) jedes Laufs an
    success_ga_c = sum(1 for run in all_ga if run[-1] >= SUCCESS_THRESHOLD)
    success_ga_b = sum(1 for run in all_p2_ga if run[-1] >= SUCCESS_THRESHOLD)
    success_ls   = sum(1 for run in all_p2_ls if run[-1] >= SUCCESS_THRESHOLD)
    success_rand = sum(1 for run in all_random if run[-1] >= SUCCESS_THRESHOLD)

    # Mittelwerte berechnen
    avg_r = np.mean(all_random, axis=0)
    avg_g = np.mean(all_ga, axis=0)
    avg_p2g = np.mean(all_p2_ga, axis=0)
    avg_p2l = np.mean(all_p2_ls, axis=0)

    # --- PLOTTING ---
    plt.figure(figsize=(14, 9))
    
    # Horizontale Linie für den Zielwert
    plt.axhline(y=SUCCESS_THRESHOLD, color='red', linestyle=':', alpha=0.5, label=f'Zielwert {SUCCESS_THRESHOLD}')

    # Einzelne Läufe (Hintergrund) - Alle 4 Algos werden nun geplottet
    for i in range(NUM_RUNS):
        # GA Rep C (Blau)
        plt.plot(common_time_grid, all_ga[i], color='royalblue', alpha=0.2, linewidth=0.8)
        # GA Rep B (Grün)
        plt.plot(common_time_grid, all_p2_ga[i], color='green', alpha=0.2, linewidth=0.8)
        # Local Search (Orange)
        plt.plot(common_time_grid, all_p2_ls[i], color='darkorange', alpha=0.1, linewidth=0.8)
        # Random Search (Grau/Schwarz)
        plt.plot(common_time_grid, all_random[i], color='black', alpha=0.1, linewidth=0.8)

    # Durchschnittslinien (Vordergrund - deutlich dicker)
    plt.plot(common_time_grid, avg_g, color='blue', linewidth=3, 
             label=f'Ø GA (Rep C) - Erfolge: {success_ga_c}/{NUM_RUNS}')
    plt.plot(common_time_grid, avg_p2g, color='green', linewidth=3, 
             label=f'Ø GA (Rep B) - Erfolge: {success_ga_b}/{NUM_RUNS}')
    plt.plot(common_time_grid, avg_p2l, color='darkorange', linewidth=2.5, 
             label=f'Ø Local Search - Erfolge: {success_ls}/{NUM_RUNS}')
    plt.plot(common_time_grid, avg_r, color='black', linestyle='--', linewidth=2, 
             label=f'Ø Random Search - Erfolge: {success_rand}/{NUM_RUNS}')

    plt.title(f"Parallele Benchmark (n={NUM_RUNS}, t={BENCHMARK_DURATION}s)\nEinzelläufe und Erfolgsraten (Schwelle >= {SUCCESS_THRESHOLD})")
    plt.xlabel("Zeit in Sekunden")
    plt.ylabel("Fitness Score")
    plt.legend(loc='lower right', fontsize='small', frameon=True, shadow=True)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    
    # --- FINALE KONSOLEN-AUSGABE ---
    duration_total = time.time() - start_study
    print(f"\n{'#'*60}")
    print(f"{'FINALE STATISTIK (Schwelle: ' + str(SUCCESS_THRESHOLD) + ')':^60}")
    print(f"{'#'*60}")
    print(f"GA (Rep C):      {success_ga_c}/{NUM_RUNS} Läufe erfolgreich ({success_ga_c/NUM_RUNS*100:.1f}%)")
    print(f"GA (Rep B):      {success_ga_b}/{NUM_RUNS} Läufe erfolgreich ({success_ga_b/NUM_RUNS*100:.1f}%)")
    print(f"Local Search:    {success_ls}/{NUM_RUNS} Läufe erfolgreich ({success_ls/NUM_RUNS*100:.1f}%)")
    print(f"Random Search:   {success_rand}/{NUM_RUNS} Läufe erfolgreich ({success_rand/NUM_RUNS*100:.1f}%)")
    print(f"Gesamtdauer:     {duration_total:.2f}s")
    print(f"{'#'*60}\n")

    plt.savefig(f"studie_erfolg_stat_parallel.png")
    plt.show()

if __name__ == "__main__":
    evaluate_study_parallel()

