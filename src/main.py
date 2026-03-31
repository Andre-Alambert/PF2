from pathlib import Path
import sys

# Allow running this file directly (python src/main.py) while keeping absolute imports.
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.config import CONFIG
from src.genetic_algorithm.encoding import get_gene_space
from src.genetic_algorithm.runner import build_ga_instance, run_ga
from src.fitness.fitness_function import fitness_function


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