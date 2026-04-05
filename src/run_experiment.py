from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.config import CONFIG
from src.experiments.grid_search import run_all_experiments
from src.results.pareto import plot_pareto


def main():
    results_dir = CONFIG["results_dir"]

    agg_rows, timestamp = run_all_experiments(results_dir)

    if not agg_rows:
        print("Nenhum resultado para plotar.")
        return

    pareto_path = results_dir / f"pareto_{timestamp}.png"
    plot_pareto(agg_rows, pareto_path)
    print(f"\nGráfico Pareto: {pareto_path}")

    # Print top-3 ranking in console
    print("\n-- Top 3 configuracoes (por fitness mediano) --")
    for rank, r in enumerate(agg_rows[:3], 1):
        print(
            f"  #{rank}  pop={r['pop_size']:>2}  gen={r['num_gen']:>2}  "
            f"mut={r['mutation_pct']:>2}%  |  "
            f"fitness={r['median_fitness']:.6f}  "
            f"std={r['std_fitness']:.2e}  "
            f"conv_gen={r['median_conv_gen']:.0f}  "
            f"t={r['median_elapsed_sec']:.1f}s"
        )


if __name__ == "__main__":
    main()
