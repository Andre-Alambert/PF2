import pygad


def on_generation(ga_instance):
    solution, solution_fitness, _ = ga_instance.best_solution()
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
        save_best_solutions=True,
        on_generation=on_generation,
    )
    return ga_instance


def run_ga(ga_instance):
    ga_instance.run()

    solution, solution_fitness, solution_idx = ga_instance.best_solution()

    print("\n=== MELHOR SOLUÇÃO FINAL ===")
    print("solution =", solution)
    print("fitness =", solution_fitness)
    print("solution_idx =", solution_idx)

    return solution, solution_fitness, solution_idx