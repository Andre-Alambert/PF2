from .config import CONFIG
from .genetic_algorithm.encoding import get_gene_space
from .genetic_algorithm.runner import build_ga_instance, run_ga
from .fitness.fitness_function import fitness_function


def main():
    gene_space = get_gene_space(CONFIG)

    ga_instance = build_ga_instance(
        config=CONFIG,
        gene_space=gene_space,
        fitness_func=fitness_function,
    )

    run_ga(ga_instance)


if __name__ == "__main__":
    main()