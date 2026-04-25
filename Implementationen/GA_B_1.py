import random
import time
from core import SolutionEvaluator, repair_solution, random_valid_solution, load_products, load_representation_b_config, print_solution_card

class IntegerQuantityGA:
    def __init__(self, products, config):
        self.products = products
        self.config = config
        self.evaluator = SolutionEvaluator(self.products, self.config)

    def run(self, seed=None, time_limit=None, fitness_target=None):
        if seed is not None: random.seed(seed)
        start_time = time.time()
        history = []
        
        ga_cfg = self.config.ga
        pop = [self.evaluator.evaluate(random_valid_solution(self.products, self.config.budget_eur)) 
               for _ in range(ga_cfg["population_size"])]
        best = max(pop, key=lambda s: s.fitness)
        history.append((0.0, best.fitness))

        for gen in range(ga_cfg["generations"]):
            # PRIORITÄT 1: FITNESS-CHECK (Sofort-Stopp)
            if fitness_target is not None and best.fitness >= fitness_target:
                # WICHTIG: Speichere die exakte Zeit des Erfolgs!
                history.append((time.time() - start_time, best.fitness))
                break

            # PRIORITÄT 2: ZEIT-CHECK
            if time_limit and (time.time() - start_time) >= time_limit:
                history.append((time.time() - start_time, best.fitness))
                break

            # ... (Rest der Evolutions-Logik: Elitismus, Crossover, Mutation) ...
            elites = sorted(pop, key=lambda s: s.fitness, reverse=True)[:ga_cfg["elitism_count"]]
            nxt = list(elites)
            
            while len(nxt) < ga_cfg["population_size"]:
                p1, p2 = [max(random.sample(pop, k=ga_cfg["tournament_size"]), key=lambda s: s.fitness) for _ in range(2)]
                pt = random.randint(1, len(self.products)-1)
                child_q = p1.quantities[:pt] + p2.quantities[pt:]
                
                for i in range(len(child_q)):
                    if random.random() < ga_cfg["mutation_rate"]:
                        change = random.choice([-1, 1])
                        child_q[i] = max(0, min(self.products[i].max_units, child_q[i] + change))
                
                nxt.append(self.evaluator.evaluate(repair_solution(child_q, self.products, self.config.budget_eur)))
            
            pop = nxt
            curr_best = max(pop, key=lambda s: s.fitness)
            if curr_best.fitness > best.fitness:
                best = curr_best
                history.append((time.time() - start_time, best.fitness))
                
        # Finaler Punkt für die History
        history.append((time.time() - start_time, best.fitness))
        return best, history

if __name__ == "__main__":
    # 1. Konfiguration laden (Sektion Solver2 in config.json)
    try:
        cfg = load_representation_b_config("Solver2")
        prods = load_products(cfg.paths.csv_path)
        
        # 2. Solver instanziieren und starten
        # Wir fangen hier BEIDE Rückgabewerte auf (best_sol UND history)
        best_sol, history = IntegerQuantityGA(prods, cfg).run(
            seed=42, 
            time_limit=10.0, 
            fitness_target=getattr(cfg, 'stop_at_target', None)
        )
        
        # 3. Ergebnis ausgeben
        print_solution_card("GENETISCHER ALGORITHMUS RESULTAT (GA_B_1)", best_sol, prods)
        print(f"\nINFO: Der Algorithmus hat {len(history)} Verbesserungsschritte aufgezeichnet.")
        
    except Exception as e:
        print(f"Fehler beim Starten des GA: {e}")