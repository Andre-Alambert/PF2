"""
Comparação definitiva NSGA-II vs NSGA-III — IEEE 118-Bus.

Parâmetros fixos (mesmos operadores, sementes idênticas):
  NSGA-II  : pop=80,  120 gen, SBX η=15, PM η=20
  NSGA-III : n_parts=12 (pop=91), 120 gen, SBX η=15, PM η=20
  Seeds    : 42, 7, 99

Saídas (results/118bus/):
  compare_summary_<ts>.csv       — HV, tamanho da frente, mínimos, tempo por rodada
  compare_pareto_nsga2_<ts>.csv  — frente de Pareto da melhor rodada NSGA-II
  compare_pareto_nsga3_<ts>.csv  — frente de Pareto da melhor rodada NSGA-III
  compare_plot_<ts>.png          — frentes sobrepostas + boxplot de HV
"""

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
from src.genetic_algorithm.encoding import get_gene_names
from src.genetic_algorithm.nsga2_runner import run_nsga2
from src.genetic_algorithm.nsga3_runner import run_nsga3
from src.opendss.opendss_interface import (
    create_dss, compile_circuit, solve_power_flow, get_all_bus_voltages_pu,
)
from src.results.pareto import plot_comparison

SEEDS = [42, 7, 99]

# Parâmetros por caso — derivados do grid search (ieee30) e escalonados (ieee118)
PARAMS_BY_CASE = {
    "ieee30": {
        "nsga2": {"pop_size": 80, "num_gen": 80,  "sbx_eta": 10, "pm_eta": 10},
        "nsga3": {"n_partitions": 11, "num_gen": 40,  "sbx_eta": 10, "pm_eta": 20},
    },
    "ieee118": {
        "nsga2": {"pop_size": 80, "num_gen": 120, "sbx_eta": 10, "pm_eta": 10},
        "nsga3": {"n_partitions": 12, "num_gen": 120, "sbx_eta": 10, "pm_eta": 20},
    },
}


def _run_block(label, runner, params, seeds, config, dss, v_refs, hv_indicator, total_runs, run_counter):
    results = []
    for seed in seeds:
        run_counter[0] += 1
        print(f"  [{run_counter[0]:>2}/{total_runs}] {label} seed={seed} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        res = runner(config, dss, v_refs, overrides={**params, "seed": seed}, verbose=False)
        elapsed = time.perf_counter() - t0

        if res.F is not None and len(res.F) > 0:
            hv  = float(hv_indicator.do(res.F))
            f1m = float(res.F[:, 0].min())
            f2m = float(res.F[:, 1].min())
            f3m = float(res.F[:, 2].min())
            n   = len(res.F)
        else:
            hv = f1m = f2m = f3m = 0.0
            n = 0

        print(f"HV={hv:.4e}  frente={n:>3}  t={elapsed:.0f}s")
        results.append({"seed": seed, "hv": hv, "pareto_size": n,
                        "f1_min": f1m, "f2_min": f2m, "f3_min": f3m,
                        "elapsed_sec": elapsed, "F": res.F, "X": res.X})
    return results


def _save_pareto_csv(runs, gene_names, label, results_dir, case_name, timestamp):
    best = max(runs, key=lambda r: r["hv"])
    if best["F"] is None:
        return
    path = results_dir / f"compare_pareto_{label}_{case_name}_{timestamp}.csv"
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sol"] + gene_names + ["cost_dh", "voltage_deviation_pu", "emissions_ton_h"])
        for i, (f, x) in enumerate(zip(best["F"], best["X"])):
            writer.writerow([i + 1] + list(x) + list(f))
    print(f"  CSV {label.upper()} salvo: {path.name}")


def main():
    parser = argparse.ArgumentParser(description="Comparação NSGA-II vs NSGA-III")
    parser.add_argument("case", choices=list(CONFIGS.keys()), help="Caso a executar")
    args = parser.parse_args()

    CONFIG = dict(CONFIGS[args.case])
    case_name = CONFIG["case_name"]

    case_params = PARAMS_BY_CASE.get(args.case, PARAMS_BY_CASE["ieee118"])
    NSGA2_PARAMS = case_params["nsga2"]
    NSGA3_PARAMS = case_params["nsga3"]

    total_runs = 2 * len(SEEDS)
    print(f"\nComparação NSGA-II vs NSGA-III | Caso: {case_name}")
    print(f"Seeds: {SEEDS}  |  Total rodadas: {total_runs}")
    print(f"NSGA-II  : pop={NSGA2_PARAMS['pop_size']}  gen={NSGA2_PARAMS['num_gen']}  sbx_eta={NSGA2_PARAMS['sbx_eta']}  pm_eta={NSGA2_PARAMS['pm_eta']}")
    print(f"NSGA-III : n_parts={NSGA3_PARAMS['n_partitions']}  gen={NSGA3_PARAMS['num_gen']}  sbx_eta={NSGA3_PARAMS['sbx_eta']}  pm_eta={NSGA3_PARAMS['pm_eta']}\n")

    dss = create_dss(allow_forms=CONFIG["allow_forms"])
    compile_circuit(dss, CONFIG["circuit_path"])
    solve_power_flow(dss)
    v_refs = get_all_bus_voltages_pu(dss)

    bounds = compute_normalization_bounds(CONFIG, v_refs)
    ref_point = np.array([
        bounds["f1_max"] * 1.05,
        bounds["f2_max"] * 1.05,
        bounds["f3_max"] * 1.05,
    ])
    hv_indicator = HV(ref_point=ref_point)
    print(f"Ponto de referência HV: f1={ref_point[0]:.1f}  f2={ref_point[1]:.4f}  f3={ref_point[2]:.3f}\n")

    run_counter = [0]
    t_start = time.perf_counter()

    print("-- NSGA-II ----------------------------------------------------------")
    nsga2_runs = _run_block("NSGA-II", run_nsga2, NSGA2_PARAMS, SEEDS,
                            CONFIG, dss, v_refs, hv_indicator, total_runs, run_counter)

    print("\n-- NSGA-III ---------------------------------------------------------")
    nsga3_runs = _run_block("NSGA-III", run_nsga3, NSGA3_PARAMS, SEEDS,
                            CONFIG, dss, v_refs, hv_indicator, total_runs, run_counter)

    total_elapsed = time.perf_counter() - t_start
    print(f"\nTempo total: {total_elapsed/60:.1f} min\n")

    # ── Resumo ───────────────────────────────────────────────────────────────
    print(f"{'':10} {'HV med':>12} {'HV std':>10} {'Frente med':>12} "
          f"{'f1_min':>10} {'f2_min':>10} {'f3_min':>12} {'t med (s)':>10}")
    for label, runs in [("NSGA-II", nsga2_runs), ("NSGA-III", nsga3_runs)]:
        hvs    = [r["hv"]          for r in runs]
        sizes  = [r["pareto_size"] for r in runs]
        f1s    = [r["f1_min"]      for r in runs]
        f2s    = [r["f2_min"]      for r in runs]
        f3s    = [r["f3_min"]      for r in runs]
        ts     = [r["elapsed_sec"] for r in runs]
        print(f"{label:<10} {np.median(hvs):>12.4e} {np.std(hvs):>10.4e} "
              f"{np.median(sizes):>12.0f} "
              f"{min(f1s):>10.1f} {min(f2s):>10.4f} {min(f3s):>12.1f} "
              f"{np.median(ts):>10.1f}")

    # ── Salvar arquivos ──────────────────────────────────────────────────────
    timestamp   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = CONFIG["results_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)
    gene_names  = get_gene_names(CONFIG)

    summary_path = results_dir / f"compare_summary_{case_name}_{timestamp}.csv"
    with open(summary_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "algorithm", "seed", "hv", "pareto_size",
            "f1_min", "f2_min", "f3_min", "elapsed_sec",
        ])
        writer.writeheader()
        for label, runs in [("nsga2", nsga2_runs), ("nsga3", nsga3_runs)]:
            for r in runs:
                writer.writerow({
                    "algorithm": label, "seed": r["seed"], "hv": r["hv"],
                    "pareto_size": r["pareto_size"], "f1_min": r["f1_min"],
                    "f2_min": r["f2_min"], "f3_min": r["f3_min"],
                    "elapsed_sec": r["elapsed_sec"],
                })
    print(f"\nCSV resumo salvo: {summary_path.name}")

    print()
    _save_pareto_csv(nsga2_runs, gene_names, "nsga2", results_dir, case_name, timestamp)
    _save_pareto_csv(nsga3_runs, gene_names, "nsga3", results_dir, case_name, timestamp)

    plot_path = results_dir / f"compare_plot_{case_name}_{timestamp}.png"
    plot_comparison(
        {"nsga2": nsga2_runs, "nsga3": nsga3_runs},
        plot_path,
        case_name=case_name,
    )
    print(f"Gráfico salvo: {plot_path.name}")


if __name__ == "__main__":
    main()
