import csv
import numpy as np
import os  # <--- Das hat gefehlt!
import pandas as pd
import matplotlib.pyplot as plt
from Implementationen.GA_Protein_Optimizer_C import run_ga, CONFIG, get_stats_standalone

def run_parameter_study():
    # Zu testende Mutationsraten
    mutation_rates = [0.01, 0.05, 0.1, 0.2, 0.4]
    iterations_per_rate = 5  # Wie oft jeder Wert getestet wird (für Statistik)
    
    results = []

    print(f"Starte Parameterstudie: {len(mutation_rates)} Raten à {iterations_per_rate} Läufe...")

    for mr in mutation_rates:
        print(f"\nTeste Mutationsrate: {mr}")
        temp_protein_values = []
        temp_durations = []

        for i in range(iterations_per_rate):
            # Config dynamisch anpassen
            CONFIG['ga_settings']['mutation_rate'] = mr
            
            # GA ausführen
            best_vec, best_fit, db, n_prod, duration = run_ga()
            
            if best_vec:
                stats = get_stats_standalone(best_vec, db, n_prod)
                temp_protein_values.append(stats['prot'])
                temp_durations.append(duration)
                print(f"  Lauf {i+1}: {stats['prot']:.1f}g Protein")

        # Statistische Auswertung für diese Rate
        results.append({
            "mutation_rate": mr,
            "avg_protein": np.mean(temp_protein_values),
            "max_protein": np.max(temp_protein_values),
            "std_dev": np.std(temp_protein_values),
            "avg_duration": np.mean(temp_durations)
        })

    # 1. Speichern in CSV
    df = pd.DataFrame(results)
    df.to_csv("./logs/mutation_study_results.csv", index=False)
    print("\nErgebnisse in './logs/mutation_study_results.csv' gespeichert.")

    # 2. Visualisierung (Boxplot oder Errorbar)
    create_plots(df)

def create_plots(df):
    plt.figure(figsize=(10, 6))
    plt.errorbar(df['mutation_rate'], df['avg_protein'], yerr=df['std_dev'], fmt='-o', capsize=5)
    plt.title('Einfluss der Mutationsrate auf das Gesamtprotein')
    plt.xlabel('Mutationsrate (mr)')
    plt.ylabel('Durchschnittliches Protein (g)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('./logs/mutation_impact_plot.png')
    plt.show()

if __name__ == '__main__':
    # Sicherstellen, dass der Log-Ordner existiert
    if not os.path.exists("./logs"):
        os.makedirs("./logs")
    run_parameter_study()