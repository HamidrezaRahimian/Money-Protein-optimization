import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from Implementationen.GA_Protein_Optimizer_C import run_ga_rep_c, CONFIG

# --- SETUP: BITTE HIER DEN AKTUELLEN REKORDWERT EINTRAGEN ---
# (Nach dem ersten Lauf des neuen Hauptskripts anpassen!)
TARGET_FITNESS = 14388.00  
MUTATION_RATES = [  0.01, 0.05, 0.1, 0.5,  ]
ITERATIONS_PER_RATE =10    

def run_efficiency_study():
    if not os.path.exists("./logs"):
        os.makedirs("./logs")

    results = []

    print(f"EFFIZIENZ-STUDIE: Suche nach Fitness-Ziel {TARGET_FITNESS}")
    print("=" * 70)

    for mr in MUTATION_RATES:
        print(f"\n>>> Teste mr: {mr}")
        gens_to_success = []
        durations = []
        success_count = 0

        for i in range(ITERATIONS_PER_RATE):
            CONFIG['ga_settings']['mutation_rate'] = mr
            # Stelle das Ziel in CONFIG bereit (einige Versionen lesen CONFIG['stop_at_target'] oder CONFIG['ga_settings']['stop_at_target'])
            CONFIG['stop_at_target'] = TARGET_FITNESS
            CONFIG['ga_settings']['stop_at_target'] = TARGET_FITNESS
            # GA starten (Early-Exit wird über CONFIG gesteuert)
            res = run_ga_rep_c()
            best_vec, best_fit, db, n_prod, duration, gen_found = res
            
            if best_fit >= (TARGET_FITNESS - 0.1):
                success_count += 1
                gens_to_success.append(gen_found)
                durations.append(duration)
                print(f"  Lauf {i+1:2}: ERFOLG in Gen {gen_found:4}")
            else:
                print(f"  Lauf {i+1:2}: FAIL (Max Fit {best_fit:.2f})")

        if success_count > 0:
            results.append({
                "mr": mr,
                "success_rate": (success_count / ITERATIONS_PER_RATE) * 100,
                "avg_gen": np.mean(gens_to_success),
                "avg_sec": np.mean(durations)
            })
        else:
            results.append({
                "mr": mr, "success_rate": 0, "avg_gen": CONFIG['ga_settings']['generations'], 
                "avg_sec": 0
            })

    df = pd.DataFrame(results)
    df.to_csv("./logs/mutation_efficiency_results.csv", index=False)
    
    # --- PLOTTING ---
    create_efficiency_plot(df)

    print("\n" + "=" * 70)
    print(f"{'FINALE EFFIZIENZ-TABELLE':^70}")
    print("=" * 70)
    print(df.to_string(index=False))
    print("=" * 70)

def create_efficiency_plot(df):
    plt.figure(figsize=(12, 6))
    
    # Balken für Generationen
    bars = plt.bar(df['mr'].astype(str), df['avg_gen'], color='skyblue', edgecolor='navy', alpha=0.8)
    
    # Achsen beschriften
    plt.ylabel('Durchschnittliche Generationen bis zum Ziel')
    plt.xlabel('Mutationsrate (mr)')
    plt.title(f'Effizienz-Vergleich: Generationen bis Fitness {TARGET_FITNESS}')
    
    # Erfolgsqote über den Balken einblenden
    for i, bar in enumerate(bars):
        yval = bar.get_height()
        success = df.loc[i, 'success_rate']
        plt.text(bar.get_x() + bar.get_width()/2, yval + 10, f"{success}% Success", 
                 ha='center', va='bottom', fontweight='bold', color='darkred' if success < 100 else 'darkgreen')

    plt.grid(axis='y', linestyle='--', alpha=0.6)
    
    # Speichern und Anzeigen
    plot_path = "./logs/mutation_efficiency_plot.png"
    plt.savefig(plot_path)
    print(f"\nGraph wurde gespeichert unter: {plot_path}")
    plt.show()

if __name__ == '__main__':
    run_efficiency_study()