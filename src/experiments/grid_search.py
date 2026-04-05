import time
import warnings
import itertools
import csv
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pygad

from src.config import CONFIG
from src.genetic_algorithm.encoding import get_gene_space
from src.fitness.fitness_function import make_fitness_function, clear_eval_cache, set_verbose

# ---------------------------------------------------------------------------
# Hyperparameter grid
# ---------------------------------------------------------------------------
PARAM_GRID = {
    "population_size":        [10, 20, 40],
    "num_generations":        [10, 20],
    "mutation_percent_genes": [20, 50],
}

SEEDS = [42, 7, 99]

# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

def _run_single(pop_size, num_gen, mutation_pct, seed, config=None):
    if config is None:
        config = CONFIG
    gene_space = get_gene_space(config)
    num_parents = max(2, pop_size // 2)
    fitness_function = make_fitness_function(config)

    fitness_history = []   # (generation, best_fitness)

    def _on_generation(ga_instance):
        if ga_instance.last_generation_fitness is None:
            return
        best = max(ga_instance.last_generation_fitness)
        fitness_history.append((ga_instance.generations_completed, best))

    # Seed numpy so PyGAD (which uses numpy internally) is reproducible
    np.random.seed(seed)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ga = pygad.GA(
            num_generations=num_gen,
            num_parents_mating=num_parents,
            sol_per_pop=pop_size,
            num_genes=len(gene_space),
            gene_space=gene_space,
            fitness_func=fitness_function,
            mutation_percent_genes=mutation_pct,
            save_best_solutions=False,
            on_generation=_on_generation,
        )

    clear_eval_cache()

    set_verbose(False)
    t0 = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ga.run()
    elapsed = time.perf_counter() - t0
    set_verbose(True)

    clear_eval_cache()

    if ga.last_generation_fitness is None or len(ga.last_generation_fitness) == 0:
        return None

    best_fitness = float(max(ga.last_generation_fitness))

    # First generation that reached 98 % of the final best fitness
    threshold = 0.98 * best_fitness
    conv_gen = num_gen
    for gen, f in fitness_history:
        if f >= threshold:
            conv_gen = gen
            break

    return {
        "pop_size":     pop_size,
        "num_gen":      num_gen,
        "mutation_pct": mutation_pct,
        "seed":         seed,
        "best_fitness": best_fitness,
        "conv_gen":     conv_gen,
        "elapsed_sec":  round(elapsed, 3),
    }


# ---------------------------------------------------------------------------
# Full experiment loop
# ---------------------------------------------------------------------------

def run_all_experiments(results_dir, config=None):
    if config is None:
        config = CONFIG
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    keys   = list(PARAM_GRID.keys())
    combos = list(itertools.product(*PARAM_GRID.values()))
    total  = len(combos) * len(SEEDS)

    print(f"\n{'='*55}")
    print(f"Experimento: {len(combos)} configs × {len(SEEDS)} seeds = {total} corridas")
    print(f"{'='*55}")

    rows = []
    done = 0

    for combo in combos:
        params = dict(zip(keys, combo))
        label = (
            f"pop={params['population_size']:>2} "
            f"gen={params['num_generations']:>2} "
            f"mut={params['mutation_percent_genes']:>2}%"
        )
        for seed in SEEDS:
            done += 1
            print(f"[{done:>3}/{total}] {label} | seed={seed:>3} … ", end="", flush=True)
            result = _run_single(
                pop_size=params["population_size"],
                num_gen=params["num_generations"],
                mutation_pct=params["mutation_percent_genes"],
                seed=seed,
                config=config,
            )
            if result:
                rows.append(result)
                print(
                    f"fitness={result['best_fitness']:.6f} | "
                    f"conv={result['conv_gen']:>2} | "
                    f"t={result['elapsed_sec']:.1f}s"
                )
            else:
                print("FALHOU")

    # --- Raw CSV ---
    raw_path = results_dir / f"experiment_raw_{timestamp}.csv"
    if rows:
        with open(raw_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nCSV bruto  : {raw_path}")

    # --- Aggregated CSV (median across seeds) ---
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r["pop_size"], r["num_gen"], r["mutation_pct"])].append(r)

    agg_rows = []
    for (pop, gen, mut), group in grouped.items():
        fits = [g["best_fitness"] for g in group]
        agg_rows.append({
            "pop_size":           pop,
            "num_gen":            gen,
            "mutation_pct":       mut,
            "median_fitness":     statistics.median(fits),
            "std_fitness":        statistics.stdev(fits) if len(fits) > 1 else 0.0,
            "median_conv_gen":    statistics.median([g["conv_gen"]     for g in group]),
            "median_elapsed_sec": statistics.median([g["elapsed_sec"]  for g in group]),
        })

    # Sort by median_fitness descending for easy reading
    agg_rows.sort(key=lambda r: r["median_fitness"], reverse=True)

    agg_path = results_dir / f"experiment_agg_{timestamp}.csv"
    if agg_rows:
        with open(agg_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(agg_rows[0].keys()))
            writer.writeheader()
            writer.writerows(agg_rows)
        print(f"CSV agregado: {agg_path}")

    return agg_rows, timestamp
