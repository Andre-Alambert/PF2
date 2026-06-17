"""
Compara as frentes de Pareto já calculadas do caso base e dos cenários eólicos
(3 geradores: Wind_B17, Wind_B53, Wind_B118), lendo os CSVs salvos em
results-wind/118bus/<label>/pareto_nsga2_*.csv — sem rodar o NSGA-II de novo.

Uso:
    python -m src.compare_wind_results
"""

import csv
import glob
from pathlib import Path

import numpy as np

from src.configs import CONFIGS
from src.results.pareto import plot_wind_scenario_comparison

RESULTS_DIR = CONFIGS["ieee118"]["results_dir"]

# (rank de ordenação, label, kw_total, subpasta)
SCENARIOS = [
    (0, "Base (sem vento)",        0,      "base"),
    (1, "h17 — 2,3% (99 MW)",      99400,  "h17"),
    (2, "h11 — 8,4% (357 MW)",     356600, "h11"),
    (3, "h00 — 14,1% (600 MW)",    600000, "h00"),
]


def load_csv(label_dir: str) -> np.ndarray:
    pattern = str(RESULTS_DIR / label_dir / "pareto_nsga2_*.csv")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {pattern}")
    with open(matches[0], newline="") as fh:
        rows = list(csv.DictReader(fh))
    f1 = [float(r["cost_dh"]) for r in rows]
    f2 = [float(r["voltage_deviation_pu"]) for r in rows]
    f3 = [float(r["emissions_ton_h"]) for r in rows]
    return np.column_stack([f1, f2, f3])


def main():
    scenarios = {}
    for rank, label, kw, subdir in SCENARIOS:
        F = load_csv(subdir)
        scenarios[rank] = {"F": F, "label": label, "kw": kw}
        print(f"{label:<26} {len(F):>3} soluções | "
              f"f1_min={F[:,0].min():>9.1f} $/h | "
              f"f2_min={F[:,1].min():.4f} pu | "
              f"f3_min={F[:,2].min():>9.1f} ton/h")

    plot_path = RESULTS_DIR / "wind_comparison_3gen.png"
    plot_wind_scenario_comparison(scenarios, plot_path, case_name="ieee118 (3 geradores eólicos)")
    print(f"\nGráfico salvo: {plot_path}")

    csv_path = RESULTS_DIR / "wind_comparison_3gen.csv"
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["scenario", "kw_wind", "sol", "cost_dh", "voltage_deviation_pu", "emissions_ton_h"])
        for rank, label, kw, _ in SCENARIOS:
            F = scenarios[rank]["F"]
            for i, f in enumerate(F):
                writer.writerow([label, kw, i + 1] + [f"{v:.6f}" for v in f])
    print(f"CSV salvo: {csv_path}")


if __name__ == "__main__":
    main()
