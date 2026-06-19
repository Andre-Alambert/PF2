"""
Compara o perfil de tensão por barra da solução de compromisso entre o caso
base e os 3 cenários eólicos (h17, h11, h00), lendo os CSVs já salvos em
results-wind/118bus/<label>/pareto_nsga2_*.csv — sem rodar o NSGA-II de novo.

Refluxa cada solução de compromisso no OpenDSS (como em analyze_results.py)
para obter as tensões por barra, e sobrepõe os 4 perfis em um único gráfico,
destacando as 3 barras eólicas e suas vizinhas elétricas diretas.

Uso:
    python -m src.compare_wind_voltage_profiles
"""

import csv
import glob
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.configs import CONFIGS
from src.analyze_results import (
    load_pareto_csv, find_special_points, run_and_read_voltages, _bus_number,
)

CASE_CONFIG = CONFIGS["ieee118"]
RESULTS_DIR = CASE_CONFIG["results_dir"]
PROJECT_ROOT = CASE_CONFIG["project_root"]

# (rank de ordenação, label, subpasta, JSON de vento ou None)
SCENARIOS = [
    (0, "Base (sem vento)",    "base", None),
    (1, "h17 — 2,3% (99 MW)",  "h17",  "wind_scenarios/ieee118_3wind_h17.json"),
    (2, "h11 — 8,4% (357 MW)", "h11",  "wind_scenarios/ieee118_3wind_h11.json"),
    (3, "h00 — 14,1% (600 MW)","h00",  "wind_scenarios/ieee118_3wind_h00.json"),
]

COLORS  = {"base": "tab:gray", "h17": "tab:green", "h11": "tab:orange", "h00": "tab:red"}
MARKERS = {"base": "o",        "h17": "^",          "h11": "s",          "h00": "D"}

# Barras eólicas e vizinhas elétricas diretas (adjacência verificada em lines.dss)
WIND_BUSES = ["17_sorenson", "53_wooster", "118_whuntngd"]
NEIGHBOR_BUSES = [
    "15_ftwayne", "16_ne", "18_mckinley", "31_deercrk", "113_deercrk",
    "52_scoshoct", "54_torrey",
    "75_sthpoint", "76_darrah",
]


def find_csv(label_dir: str) -> Path:
    pattern = str(RESULTS_DIR / label_dir / "pareto_nsga2_*.csv")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {pattern}")
    return Path(matches[0])


def main():
    profiles = {}

    for _, label, subdir, wind_json in SCENARIOS:
        csv_path = find_csv(subdir)
        F, rows = load_pareto_csv(csv_path)
        idx = find_special_points(F)["min_vdev"]

        wind_config = None
        if wind_json:
            with open(PROJECT_ROOT / wind_json) as fh:
                wind_config = json.load(fh)

        print(f"Calculando tensões — {label} (solução de mínimo desvio de tensão, "
              f"sol #{idx + 1}, f2={F[idx, 1]:.4f} pu)...")
        profiles[subdir] = run_and_read_voltages(CASE_CONFIG, rows, idx, wind_config)

    # ── Gráfico ──────────────────────────────────────────────────────────────
    all_buses = sorted(
        set(b for vdict in profiles.values() for b in vdict),
        key=_bus_number,
    )
    x = np.arange(len(all_buses))

    fig, ax = plt.subplots(figsize=(18, 6))
    ax.set_title(
        "Perfil de Tensão — Solução de Mínimo Desvio de Tensão, Base × Cenários Eólicos (IEEE 118-Bus)",
        fontsize=13, fontweight="bold",
    )

    for _, label, subdir, _ in SCENARIOS:
        y = [profiles[subdir].get(b, np.nan) for b in all_buses]
        ax.plot(x, y, marker=MARKERS[subdir], color=COLORS[subdir],
                 markersize=4, linewidth=1.2, alpha=0.85, label=label, zorder=3)

    v_lower = CASE_CONFIG["voltage_lower_limit"]
    v_upper = CASE_CONFIG["voltage_upper_limit"]
    ax.axhline(v_lower, color="red", linestyle="--", linewidth=1.2,
               label=f"Lim. inferior ({v_lower} pu)")
    ax.axhline(v_upper, color="red", linestyle=":", linewidth=1.2,
               label=f"Lim. superior ({v_upper} pu)")
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8, alpha=0.5, label="1,0 pu")

    for wb in WIND_BUSES:
        if wb in all_buses:
            xi = all_buses.index(wb)
            ax.axvspan(xi - 0.5, xi + 0.5, color="purple", alpha=0.12, zorder=1)
    for nb in NEIGHBOR_BUSES:
        if nb in all_buses:
            xi = all_buses.index(nb)
            ax.axvspan(xi - 0.5, xi + 0.5, color="purple", alpha=0.05, zorder=1)

    tick_step = max(1, len(all_buses) // 25)
    ax.set_xticks(x[::tick_step])
    ax.set_xticklabels([all_buses[i] for i in range(0, len(all_buses), tick_step)],
                        rotation=45, ha="right", fontsize=7)
    ax.set_xlabel("Barra (faixas roxas = barras eólicas e vizinhas elétricas diretas)", fontsize=10)
    ax.set_ylabel("Tensão média (pu)", fontsize=10)
    ax.legend(fontsize=8, loc="lower right", ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    plot_path = RESULTS_DIR / "voltage_comparison_3gen.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nGráfico salvo: {plot_path}")

    # ── CSV completo ─────────────────────────────────────────────────────────
    csv_path = RESULTS_DIR / "voltage_comparison_3gen.csv"
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["scenario", "bus", "voltage_pu"])
        for _, label, subdir, _ in SCENARIOS:
            for bus in all_buses:
                v = profiles[subdir].get(bus)
                if v is not None:
                    writer.writerow([label, bus, f"{v:.6f}"])
    print(f"CSV salvo: {csv_path}")

    # ── Resumo no terminal: tensão nas barras eólicas e vizinhas ─────────────
    focus_buses = sorted(set(WIND_BUSES) | set(NEIGHBOR_BUSES), key=_bus_number)
    header = f"{'Barra':<14}" + "".join(f"{subdir:>12}" for _, _, subdir, _ in SCENARIOS)
    print(f"\n{header}")
    print("=" * len(header))
    for bus in focus_buses:
        row = f"{bus:<14}"
        for _, _, subdir, _ in SCENARIOS:
            v = profiles[subdir].get(bus)
            row += f"{v:>12.4f}" if v is not None else f"{'--':>12}"
        print(row)


if __name__ == "__main__":
    main()
