import runpy
from pathlib import Path
import math

# execute person2_core.py in an isolated namespace and grab symbols
core_path = Path(__file__).resolve().parents[1] / 'hamid-folder' / 'person2_core.py'
ns = runpy.run_path(str(core_path))
person2_core = ns

# convenience aliases
Product = person2_core['Product']
SolutionEvaluator = person2_core['SolutionEvaluator']
repair_solution = person2_core['repair_solution']
RepresentationBConfig = person2_core['RepresentationBConfig']
ProjectPaths = person2_core['ProjectPaths']


def make_cfg(kcal_target=100.0, budget=50.0, penalty=3.0, under_mult=0.1):
    weights = {
        'protein': 10.0,
        'portions': 1.5,
        'taste': 5.0,
        'variety': 2.0,
        # support both keys; evaluator checks both
        'calorie_penalty': penalty,
        'under_target_multiplier': under_mult,
    }
    paths = ProjectPaths(Path.cwd(), Path('config.json'), Path('data.csv'))
    return RepresentationBConfig(budget_eur=budget, kcal_target=kcal_target, weights=weights, ga={}, local_search={}, paths=paths)


def test_exact_target_no_penalty():
    p = Product(
        id=1,
        store='s',
        name='one',
        category='c',
        price_eur=2.0,
        weight_g=100.0,
        protein_per_100g=10.0,
        calories_per_100g=100.0,
        protein_per_pack_g=10.0,
        calories_per_pack=100.0,
        taste_score=4.0,
        estimated_portions=1,
        protein_type='t',
        max_units=10,
    )
    cfg = make_cfg(kcal_target=100.0)
    ev = SolutionEvaluator([p], cfg)
    sol = ev.evaluate([1])
    # compute expected positive contribution
    expected = (
        cfg.weights['protein'] * (p.protein_per_pack_g * 1)
        + cfg.weights['portions'] * (p.estimated_portions * 1)
        + cfg.weights['taste'] * (p.taste_score)
        + cfg.weights['variety'] * 1
    )
    # no kcal penalty expected because calories == target
    assert math.isclose(sol.fitness, expected, rel_tol=1e-6)


def test_under_vs_exact_improves():
    # product with 50 kcal per pack, target 100
    p = Product(
        id=1,
        store='s',
        name='one',
        category='c',
        price_eur=2.0,
        weight_g=100.0,
        protein_per_100g=10.0,
        calories_per_100g=50.0,
        protein_per_pack_g=10.0,
        calories_per_pack=50.0,
        taste_score=4.0,
        estimated_portions=1,
        protein_type='t',
        max_units=10,
    )
    cfg = make_cfg(kcal_target=100.0, penalty=3.0, under_mult=0.1)
    ev = SolutionEvaluator([p], cfg)
    sol_one = ev.evaluate([1])
    sol_two = ev.evaluate([2])
    # two packs exactly meet target -> should be better than one pack (which is under-target penalized)
    assert sol_two.fitness > sol_one.fitness


def test_repair_solution_respects_budget():
    p = Product(
        id=1,
        store='s',
        name='one',
        category='c',
        price_eur=10.0,
        weight_g=100.0,
        protein_per_100g=10.0,
        calories_per_100g=100.0,
        protein_per_pack_g=10.0,
        calories_per_pack=100.0,
        taste_score=4.0,
        estimated_portions=1,
        protein_type='t',
        max_units=10,
    )
    quantities = [2]  # cost 20
    repaired = repair_solution(quantities, [p], budget=15.0)
    total_cost = sum(p.price_eur * q for p, q in zip([p], repaired))
    assert total_cost <= 15.0
