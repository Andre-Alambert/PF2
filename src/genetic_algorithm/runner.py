import pygad

from src.fitness.fitness_function import get_eval_cache


def _make_on_generation(logger=None):
    def on_generation(ga_instance):
        if ga_instance.last_generation_fitness is None:
            return

        best_idx = max(
            range(len(ga_instance.last_generation_fitness)),
            key=lambda i: ga_instance.last_generation_fitness[i],
        )
        solution = ga_instance.population[best_idx]
        solution_fitness = ga_instance.last_generation_fitness[best_idx]

        metrics = get_eval_cache().get(best_idx, {})

        if logger:
            logger.log_generation(
                generation=ga_instance.generations_completed,
                best_fitness=solution_fitness,
                best_solution=solution,
                metrics=metrics,
            )

        print("\n===== FIM DA GERAÇÃO =====")
        print(f"Geração: {ga_instance.generations_completed}")
        print(f"Melhor solução: {solution}")
        print(f"Melhor fitness: {solution_fitness}")
        print("=" * 40)

    return on_generation


def build_ga_instance(config, gene_space, fitness_func, logger=None):
    ga_instance = pygad.GA(
        num_generations=config["num_generations"],
        num_parents_mating=config["num_parents_mating"],
        sol_per_pop=config["population_size"],
        num_genes=len(gene_space),
        gene_space=gene_space,
        fitness_func=fitness_func,
        mutation_percent_genes=50,
        save_best_solutions=False,
        on_generation=_make_on_generation(logger),
    )
    return ga_instance


def run_ga(ga_instance):
    ga_instance.run()

    if ga_instance.last_generation_fitness is None:
        raise RuntimeError("GA finished without fitness values.")

    solution_idx = max(
        range(len(ga_instance.last_generation_fitness)),
        key=lambda i: ga_instance.last_generation_fitness[i],
    )
    solution = ga_instance.population[solution_idx]
    solution_fitness = ga_instance.last_generation_fitness[solution_idx]

    print("\n=== MELHOR SOLUÇÃO FINAL ===")
    print("solution =", solution)
    print("fitness =", solution_fitness)
    print("solution_idx =", solution_idx)

    return solution, solution_fitness, solution_idx