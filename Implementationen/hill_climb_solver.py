import random
import time
from core import SolutionEvaluator, repair_solution, random_valid_solution, load_products, load_representation_b_config, print_solution_card

class HillClimbingLocalSearch:
    def __init__(self, products, config):
        self.products, self.config = products, config
        self.evaluator = SolutionEvaluator(self.products, self.config)

    def run(self, seed=None, time_limit=None, fitness_target=None):
        if seed is not None: random.seed(seed)
        start_time = time.time()
        best_overall = None
        history = []
        
        ls_cfg = self.config.local_search
        for _ in range(ls_cfg["restart_attempts"]):
            if time_limit and (time.time() - start_time) >= time_limit: break
            
            curr = self.evaluator.evaluate(random_valid_solution(self.products, self.config.budget_eur))
            if best_overall is None or curr.fitness > best_overall.fitness:
                best_overall = curr
                history.append((time.time() - start_time, best_overall.fitness))

            for _ in range(ls_cfg["max_iterations"]):
                if time_limit and (time.time() - start_time) >= time_limit: break
                
                neighbor_q = list(curr.quantities)
                idx = random.randrange(len(neighbor_q))
                neighbor_q[idx] = max(0, min(self.products[idx].max_units, neighbor_q[idx] + random.choice([-1, 1])))
                
                cand = self.evaluator.evaluate(repair_solution(neighbor_q, self.products, self.config.budget_eur))
                
                if cand.fitness > curr.fitness: 
                    curr = cand
                    if curr.fitness > best_overall.fitness:
                        best_overall = curr
                        history.append((time.time() - start_time, best_overall.fitness))
                
                if fitness_target and curr.fitness >= fitness_target: break
            
            if fitness_target and best_overall.fitness >= fitness_target: break
            
        return best_overall, history # Rückgabe erweitert
    
    
if __name__ == "__main__":
    # WICHTIG: Hier "Solver3" angeben!
    cfg = load_representation_b_config("Solver3")
    prods = load_products(cfg.paths.csv_path)
    
    # run() kann nun optional auch ein time_limit erhalten
    res = HillClimbingLocalSearch(prods, cfg).run(
        fitness_target=cfg.stop_at_target,
        time_limit=30.0 # optional: nach 30 sekunden aufhören
    )
    print_solution_card("LOCAL SEARCH (HILL CLIMBING)", res, prods)