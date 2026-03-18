import pygad


def build_ga_instance(config, gene_space, fitness_func):
    ga_instance = pygad.GA(
        num_generations=config["num_generations"],
        num_parents_mating=config["num_parents_mating"],
        sol_per_pop=config["population_size"],
        num_genes=len(gene_space),
        gene_space=gene_space,
        fitness_func=fitness_func,
        mutation_percent_genes=20,
        save_best_solutions=True,
    )
    return ga_instance


def run_ga(ga_instance):
    ga_instance.run()

    solution, solution_fitness, solution_idx = ga_instance.best_solution()

    print("\n=== MELHOR SOLUÇÃO ENCONTRADA ===")
    print("solution =", solution)
    print("fitness =", solution_fitness)
    print("solution_idx =", solution_idx)

    return solution, solution_fitness, solution_idx