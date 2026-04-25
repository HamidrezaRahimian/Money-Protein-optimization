import multiprocessing
import time
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Importe der existierenden Logik
from GA_Protein_Optimizer_C import run_ga_rep_c
from GA_B_1 import IntegerQuantityGA 
from hill_climb_solver import HillClimbingLocalSearch
from randomSearch import run_random_search
from core import load_products, load_representation_b_config

# --- KONFIGURATION ---
NUM_RUNS = 1000       # Anzahl der Durchläufe pro Methode
TIME_LIMIT = 2.0    # Zeitlimit in Sekunden
SUCCESS_THRESHOLD = 14388.0

def task_wrapper(method_name):
    """Führt eine einzelne Methode aus und gibt Rohdaten sowie Erfolg zurück."""
    start_time = time.time()
    try:
        if method_name == 'GA (Rep C)':
            # Erwartet Rückgabe: (best, fit, prods, n, dur, gen, history)
            res = run_ga_rep_c()
            fit = res[1]
            history = res[6]
            dur = history[-1][0] # Nutzt exakten Zeitstempel aus der History
            return method_name, fit, dur, history, fit >= SUCCESS_THRESHOLD
            
        elif method_name == 'GA (Rep B)':
            cfg = load_representation_b_config("Solver2")
            prods = load_products(cfg.paths.csv_path)
            solver = IntegerQuantityGA(prods, cfg)
            res, history = solver.run(time_limit=TIME_LIMIT, fitness_target=cfg.stop_at_target)
            dur = history[-1][0] # Nutzt exakten Zeitstempel aus der History
            return method_name, res.fitness, dur, history, res.fitness >= SUCCESS_THRESHOLD
            
        elif method_name == 'Hill Climbing':
            cfg = load_representation_b_config("Solver3")
            prods = load_products(cfg.paths.csv_path)
            solver = HillClimbingLocalSearch(prods, cfg)
            res, history = solver.run(time_limit=TIME_LIMIT, fitness_target=cfg.stop_at_target)
            dur = history[-1][0]
            return method_name, res.fitness, dur, history, res.fitness >= SUCCESS_THRESHOLD
            
        elif method_name == 'Random Search':
            res_data, fit, db, history = run_random_search()
            dur = history[-1][0]
            return method_name, fit, dur, history, fit >= SUCCESS_THRESHOLD
            
    except Exception as e:
        print(f"Fehler bei {method_name}: {e}")
        return None

def plot_extended_benchmarks(metrics):
    methods = list(metrics.keys())
    
    avg_fitness = [np.mean(metrics[m]['fitness']) for m in methods]
    std_fitness = [np.std(metrics[m]['fitness']) for m in methods]
    avg_time = [np.mean(metrics[m]['time']) for m in methods]
    std_time = [np.std(metrics[m]['time']) for m in methods]
    
    # Fehlerbalken nach unten auf 0 begrenzen
    time_err_low = [min(avg, std) for avg, std in zip(avg_time, std_time)]
    avg_conv = [avg_fitness[i] / avg_time[i] if avg_time[i] > 0 else 0 for i in range(len(methods))]

    style_cfg = {
        'GA (Rep C)': {'color': 'blue', 'label': 'GA (Rep C)'},
        'GA (Rep B)': {'color': 'green', 'label': 'GA (Rep B)'},
        'Hill Climbing': {'color': 'orange', 'label': 'Local Search'},
        'Random Search': {'color': 'black', 'label': 'Random Search', 'ls': '--'}
    }

    fig = plt.figure(figsize=(16, 11))
    plt.subplots_adjust(hspace=0.4, wspace=0.3)

    # 1. Maximale Fitness
    ax1 = fig.add_subplot(2, 2, 1)
    for i, m in enumerate(methods):
        ax1.bar(m, avg_fitness[i], yerr=std_fitness[i], color=style_cfg[m]['color'], edgecolor='black', capsize=5, alpha=0.7)
    ax1.axhline(y=SUCCESS_THRESHOLD, color='red', linestyle=':', label=f'Ziel {int(SUCCESS_THRESHOLD)}')
    ax1.set_title('Ø Maximale Fitness (Qualität)', fontweight='bold')
    ax1.legend(loc='lower right')

    # 2. Laufzeit (Korrektur der negativen Balken)
    ax2 = fig.add_subplot(2, 2, 2)
    for i, m in enumerate(methods):
        ax2.bar(m, avg_time[i], yerr=[[time_err_low[i]], [std_time[i]]], color=style_cfg[m]['color'], edgecolor='black', capsize=5, alpha=0.7)
    ax2.set_title('Ø Laufzeit (Sekunden)', fontweight='bold')
    ax2.set_ylabel('Zeit in s')

    # 3. Effizienz
    ax3 = fig.add_subplot(2, 2, 3)
    for i, m in enumerate(methods):
        ax3.bar(m, avg_conv[i], color=style_cfg[m]['color'], edgecolor='black', alpha=0.7)
    ax3.set_title('Ø Effizienz (Performance/Sekunde)', fontweight='bold')

    # 4. Spaghetti-Plot
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axhline(y=SUCCESS_THRESHOLD, color='red', linestyle=':', alpha=0.5)
    for m in methods:
        cfg = style_cfg[m]
        all_interp_fits = []
        common_time = np.linspace(0, TIME_LIMIT, 500)
        for hist in metrics[m]['histories']:
            t_vals, f_vals = zip(*hist)
            all_interp_fits.append(np.interp(common_time, t_vals, f_vals))
            ax4.step(t_vals, f_vals, where='post', color=cfg['color'], alpha=0.1, linewidth=0.8)
        mean_fit = np.mean(all_interp_fits, axis=0)
        ax4.step(common_time, mean_fit, where='post', color=cfg['color'], linestyle=cfg.get('ls', '-'), 
                 linewidth=2.5, label=f"Ø {cfg['label']} ({metrics[m]['success_count']}/{NUM_RUNS})")

    ax4.set_title('Echte Konvergenz (Einzelläufe & Schnitt)', fontweight='bold')
    ax4.set_xlabel('Zeit in Sekunden')
    ax4.legend(loc='lower right', fontsize=8)
    plt.suptitle(f'Erweiterte Benchmark-Analyse (n={NUM_RUNS}, t={TIME_LIMIT}s)', fontsize=16, fontweight='bold', y=0.98)
    plt.show()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    methods = ['GA (Rep C)', 'GA (Rep B)', 'Hill Climbing', 'Random Search']
    raw_results = {m: {'fitness': [], 'time': [], 'histories': [], 'success_count': 0} for m in methods}
    
    total_cores = multiprocessing.cpu_count()
    print(f"Starte parallelen Benchmark auf {total_cores} Kernen...")
    
    with multiprocessing.Pool(processes=total_cores) as pool:
        results = pool.map(task_wrapper, methods * NUM_RUNS)
        
    for r in results:
        if r:
            name, fit, dur, history, is_success = r
            raw_results[name]['fitness'].append(fit)
            raw_results[name]['time'].append(dur)
            raw_results[name]['histories'].append(history)
            if is_success: raw_results[name]['success_count'] += 1

    # --- TEXTAUSGABE ERFOLGSRATE ---
    print("\n" + "="*45)
    print(f"{'ERFOLGSRATE (Fit >= ' + str(SUCCESS_THRESHOLD) + ')':^45}")
    print("="*45)
    for m in methods:
        count = raw_results[m]['success_count']
        rate = (count / NUM_RUNS) * 100
        color = "\033[92m" if rate > 80 else "\033[93m" if rate > 0 else "\033[91m"
        print(f"{m:15}: {color}{count}/{NUM_RUNS} Erfolge ({rate:.1f}%)\033[0m")
    print("="*45 + "\n")

    plot_extended_benchmarks(raw_results)