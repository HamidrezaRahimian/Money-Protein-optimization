import csv
import json
import random
import time
from pathlib import Path

# --- 1. KONFIGURATION LADEN ---
def load_full_config():
    """Laedt die gesamte config.json relativ zum Skript-Ort."""
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / 'config.json'

    if not config_path.exists():
        config_path = script_dir.parent / 'config.json'

    if not config_path.exists():
        raise FileNotFoundError(f"Config-Datei nicht gefunden: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Globale Variablen initialisieren
FULL_CONFIG = load_full_config()
RS_CFG = FULL_CONFIG.get("RandomSearch", {})
FITNESS_CFG = FULL_CONFIG.get("fitness", {})

def load_database():
    database = {}
    raw_path = RS_CFG.get("paths", {}).get("database", "")
    script_dir = Path(__file__).parent.resolve()
    
    file_path = (script_dir / raw_path).resolve()
    if not file_path.exists():
        file_path = (script_dir.parent / raw_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"Datenbank nicht gefunden unter: {file_path}")

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

# --- 2. KERN-LOGIK ---

def get_stats_from_list(p_id_list, products):
    """Berechnet Statistiken fuer eine Liste von Produkt-IDs."""
    s = {"prot": 0, "price": 0, "taste_sum": 0, "port": 0, "kcal": 0, "unique_set": set(), "total_packs": 0}
    
    for p_id in p_id_list:
        if p_id in products:
            d = products[p_id]
            s["prot"] += d["prot"]
            s["price"] += d["price"]
            s["kcal"] += d["kcal"]
            s["port"] += d["port"]
            s["taste_sum"] += d["taste"]
            s["total_packs"] += 1
            s["unique_set"].add(p_id)
            
    s["taste"] = (s["taste_sum"] / s["total_packs"]) if s["total_packs"] > 0 else 0
    s["unique"] = len(s["unique_set"])
    return s

def calculate_fitness(stats):
    """Bewertet den Korb basierend auf der fitness Sektion."""
    w = FITNESS_CFG
    
    fitness_val = (w.get("protein", 0) * stats["prot"]) + \
                  (w.get("portions", 0) * stats["port"]) + \
                  (w.get("taste", 0) * stats["taste"]) + \
                  (w.get("variety", 0) * stats["unique"])
    
    target = RS_CFG.get("constraints", {}).get("kcal_target", 10000)
    diff = stats["kcal"] - target
    penalty_factor = w.get("calorie_penalty", 3.0)

    if diff > 0:
        fitness_val -= diff * penalty_factor
    else:
        milde = float(w.get("under_target_multiplier", 0.1))
        fitness_val -= abs(diff) * (penalty_factor * milde)
        
    return round(fitness_val, 2)

# --- 3. RANDOM ENGINE ---
def run_random_search():
    products = load_database()
    p_ids = list(products.keys())
    
    constraints = RS_CFG.get("constraints", {})
    settings = RS_CFG.get("settings", {})
    
    budget_limit = constraints.get("budget_limit", 50.0)
    total_runs = settings.get("total_runs", 50000)
    log_interval = settings.get("log_interval", 5000)

    best_fitness = -float('inf')
    best_solution_data = None
    
    # NEU: Startzeit und History-Liste initialisieren
    start_time = time.time()
    history = [] 
    # Startpunkt (0, 0)
    history.append((0.0, 0.0))

    print(f"Starte Random Search mit {total_runs} Durchlaeufen...")

    for i in range(1, total_runs + 1):
        current_v_len = random.randint(10, 30)
        current_list = [random.choice(p_ids) for _ in range(current_v_len)]
        
        s = get_stats_from_list(current_list, products)
        
        if s["price"] <= budget_limit:
            counts = {}
            valid_units = True
            for pid in current_list:
                counts[pid] = counts.get(pid, 0) + 1
                if counts[pid] > products[pid]['max_u']:
                    valid_units = False
                    break
            
            if valid_units:
                fit = calculate_fitness(s)
                
                # Wenn eine Verbesserung gefunden wurde, Zeit und Fitness speichern
                if fit > best_fitness:
                    best_fitness = fit
                    best_solution_data = (current_list, s)
                    # NEU: Nur bei tatsächlichen Sprüngen einen Punkt in die Kurve setzen
                    history.append((time.time() - start_time, best_fitness))

        if i % log_interval == 0:
            print(f"Run {i:6} | Best Fitness bisher: {best_fitness:8.2f}")

    # NEU: Endpunkt setzen, damit die Linie bis zum Ende der Laufzeit reicht
    history.append((time.time() - start_time, best_fitness))

    return best_solution_data, best_fitness, products, history
if __name__ == '__main__':
    try:
        # Erweitert auf 4 Rückgabewerte, um den 'history'-Fehler zu beheben
        best_res, fit, db, hist = run_random_search()
        
        if best_res:
            res_list, stats = best_res
            print("\n" + "="*60)
            print(f"{' FINALES ERGEBNIS RANDOM SEARCH ':^60}")
            print("="*60)
            
            # Gruppieren fuer die Anzeige
            final_counts = {}
            for pid in res_list:
                final_counts[pid] = final_counts.get(pid, 0) + 1
                
            for pid, count in final_counts.items():
                p = db[pid]
                print(f"{count:2}x {p['name']:25} | {p['prot']*count:6.1f}g Protein")
            
            print("-" * 60)
            print(f"FITNESS:   {fit:10.2f}")
            print(f"PROTEIN:   {stats['prot']:10.1f}g")
            print(f"KALORIEN:  {stats['kcal']:10.1f}kcal")
            print(f"PREIS:     {stats['price']:10.2f} Euro")
            print(f"ANZAHL:    {stats['total_packs']} Packungen")
            print("-" * 60)
        else:
            print("Keine gueltige Loesung innerhalb des Budgets gefunden.")
            
    except Exception as e:
        # Gibt die Fehlermeldung aus, falls das Entpacken fehlschlägt
        print(f"Fehler: {e}")