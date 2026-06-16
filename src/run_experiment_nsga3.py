import argparse
import csv
import time
from datetime import datetime
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import numpy as np
from pymoo.indicators.hv import HV

from src.configs import CONFIGS
from src.fitness.objective_functions import compute_normalization_bounds
from src.genetic_algorithm.nsga3_runner import run_nsga3
from src.opendss.opendss_interface import (
    create_dss, compile_circuit, solve_power_flow, get_all_bus_voltages_pu,
    add_wind_generators, apply_wind_scenario,
)
from src.results.pareto import plot_hypervolume_pareto


# ---------------------------------------------------------------------------
# Grade de hiperparâmetros — edite conforme necessário
# n_partitions → nº de reference points (Das-Dennis, n_obj=3):
#   5 → 21 pts | 8 → 45 pts | 11 → 78 pts
# ---------------------------------------------------------------------------
PARAM_GRID = [
    {"n_partitions": nparts, "num_gen": gen, "sbx_eta": sbx, "pm_eta": pm}
    for nparts in [5, 8, 11]
    for gen    in [20, 40, 80]
    for sbx    in [10, 20]
    for pm     in [10, 20]
]

SEEDS = [42, 7, 99]


def main():
    parser = argparse.ArgumentParser(description="Experimento de hiperparâmetros NSGA-III")
    parser.add_argument("case", choices=list(CONFIGS.keys()), help="Caso a executar")
    parser.add_argument("--hour", type=int, choices=range(24), metavar="0-23",
                        help="Hora do cenário eólico")
    parser.add_argument("--seeds", type=int, default=3, metavar="N",
                        help="Número de seeds por configuração (padrão: 3)")
    args = parser.parse_args()

    CONFIG = dict(CONFIGS[args.case])
    case_name = CONFIG["case_name"]
    if args.hour is not None and CONFIG.get("wind_generators"):
        CONFIG["wind_scenario_hour"] = args.hour

    seeds = SEEDS[:args.seeds]
    n_configs = len(PARAM_GRID)
    n_runs = n_configs * len(seeds)

    print(f"\nExperimento NSGA-III | Caso: {case_name}")
    print(f"Configurações: {n_configs} | Seeds: {len(seeds)} | Total rodadas: {n_runs}")
    if CONFIG.get("wind_generators"):
        hour = CONFIG.get("wind_scenario_hour", 12)
        ls   = CONFIG.get("wind_loadshape", [])
        fac  = ls[hour % len(ls)] if ls else 0.0
        kw   = fac * CONFIG["wind_generators"][0]["kw_max"]
        print(f"Vento: hora={hour} | P={kw:.0f} kW ({fac*100:.0f}%)")
    print()

    # ── Setup OpenDSS (uma única vez para todo o experimento) ────────────────
    dss = create_dss(allow_forms=CONFIG["allow_forms"])
    compile_circuit(dss, CONFIG["circuit_path"])
    if CONFIG.get("wind_generators"):
        add_wind_generators(dss, CONFIG)
        apply_wind_scenario(dss, CONFIG, CONFIG.get("wind_scenario_hour", 12))
    solve_power_flow(dss)
    v_refs = get_all_bus_voltages_pu(dss)

    # ── Ponto de referência para hipervolume ─────────────────────────────────
    bounds = compute_normalization_bounds(CONFIG, v_refs)
    ref_point = np.array([
        bounds["f1_max"] * 1.05,
        bounds["f2_max"] * 1.05,
        bounds["f3_max"] * 1.05,
    ])
    hv_indicator = HV(ref_point=ref_point)
    print(f"Ponto de referência HV: f1={ref_point[0]:.1f}  f2={ref_point[1]:.4f}  f3={ref_point[2]:.3f}\n")

    # ── Varredura ────────────────────────────────────────────────────────────
    agg_rows = []
    run_count = 0
    t_experiment_start = time.perf_counter()

    for cfg_idx, params in enumerate(PARAM_GRID):
        hvs, elapsed_list = [], []

        print(f"[{cfg_idx + 1:>2}/{n_configs}] "
              f"n_parts={params['n_partitions']:>2}  gen={params['num_gen']:>2}  "
              f"sbx_eta={params['sbx_eta']:>2}  pm_eta={params['pm_eta']:>2}")

        for seed in seeds:
            run_count += 1
            t0 = time.perf_counter()
            res = run_nsga3(CONFIG, dss, v_refs,
                            overrides={**params, "seed": seed},
                            verbose=False)
            elapsed = time.perf_counter() - t0

            if res.F is not None and len(res.F) > 0:
                hv_val = float(hv_indicator.do(res.F))
            else:
                hv_val = 0.0

            hvs.append(hv_val)
            elapsed_list.append(elapsed)
            print(f"          seed={seed} | HV={hv_val:.4f} | t={elapsed:.1f}s "
                  f"({run_count}/{n_runs})")

        agg_rows.append({
            "n_partitions":      params["n_partitions"],
            "num_gen":           params["num_gen"],
            "sbx_eta":           params["sbx_eta"],
            "pm_eta":            params["pm_eta"],
            "median_hv":         float(np.median(hvs)),
            "std_hv":            float(np.std(hvs)),
            "median_elapsed_sec": float(np.median(elapsed_list)),
        })
        print(f"          -> HV mediano={agg_rows[-1]['median_hv']:.4f} "
              f"+/- {agg_rows[-1]['std_hv']:.4f}  "
              f"t={agg_rows[-1]['median_elapsed_sec']:.1f}s\n")

    total_elapsed = time.perf_counter() - t_experiment_start
    print(f"Experimento concluído em {total_elapsed/60:.1f} min\n")

    # ── Ranking final ────────────────────────────────────────────────────────
    ranked = sorted(agg_rows, key=lambda r: r["median_hv"], reverse=True)
    print(f"{'#':>3}  {'n_parts':>7}  {'gen':>4}  {'sbx_eta':>7}  {'pm_eta':>6}  "
          f"{'HV mediano':>12}  {'+/-std':>10}  {'t (s)':>7}")
    for i, r in enumerate(ranked):
        print(f"{i+1:>3}  {r['n_partitions']:>7}  {r['num_gen']:>4}  "
              f"{r['sbx_eta']:>5}  {r['pm_eta']:>5}  "
              f"{r['median_hv']:>12.4f}  {r['std_hv']:>10.4f}  "
              f"{r['median_elapsed_sec']:>7.1f}")

    # ── Salvar CSV ───────────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = CONFIG["results_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / f"experiment_nsga3_{case_name}_{timestamp}.csv"
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=agg_rows[0].keys())
        writer.writeheader()
        writer.writerows(agg_rows)
    print(f"\nCSV salvo: {csv_path}")

    # ── Salvar gráfico ───────────────────────────────────────────────────────
    plot_path = results_dir / f"experiment_nsga3_{case_name}_{timestamp}.png"
    plot_hypervolume_pareto(agg_rows, plot_path)
    print(f"Gráfico salvo: {plot_path}")


if __name__ == "__main__":
    main()
