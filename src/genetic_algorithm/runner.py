import pygad


def on_generation(ga_instance):
    if ga_instance.last_generation_fitness is None:
        return

    best_idx = max(
        range(len(ga_instance.last_generation_fitness)),
        key=lambda i: ga_instance.last_generation_fitness[i],
    )
    solution = ga_instance.population[best_idx]
    solution_fitness = ga_instance.last_generation_fitness[best_idx]
    print("\n===== FIM DA GERAÇÃO =====")
    print(f"Geração: {ga_instance.generations_completed}")
    print(f"Melhor solução: {solution}")
    print(f"Melhor fitness: {solution_fitness}")
    print("=" * 40)


def build_ga_instance(config, gene_space, fitness_func):
    ga_instance = pygad.GA(
        num_generations=5,
        num_parents_mating=3,
        sol_per_pop=6,
        num_genes=len(gene_space),
        gene_space=gene_space,
        fitness_func=fitness_func,
        mutation_percent_genes=50,
        save_best_solutions=False,
        on_generation=on_generation,
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