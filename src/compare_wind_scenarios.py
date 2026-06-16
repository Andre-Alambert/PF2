import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.configs import CONFIGS
from src.genetic_algorithm.nsga2_runner import run_nsga2
from src.opendss.opendss_interface import (
    create_dss, compile_circuit, solve_power_flow, get_all_bus_voltages_pu,
    add_wind_generators, apply_wind_scenario,
)
from src.results.pareto import plot_wind_scenario_comparison


def _run_scenario(base_config, wind_config):
    dss = create_dss(allow_forms=base_config["allow_forms"])
    compile_circuit(dss, base_config["circuit_path"])
    add_wind_generators(dss, wind_config)
    apply_wind_scenario(dss, wind_config)
    solve_power_flow(dss)
    v_refs = get_all_bus_voltages_pu(dss)

    res = run_nsga2(base_config, dss, v_refs, verbose=False)

    hour = wind_config["hour"]
    total_kw = sum(
        wg.get("loadshape", [])[hour % len(wg["loadshape"])] * wg["kw_max"]
        for wg in wind_config["generators"]
        if wg.get("loadshape")
    )
    return res, total_kw


def main():
    parser = argparse.ArgumentParser(description="Comparação de cenários eólicos — NSGA-II")
    parser.add_argument("case", choices=list(CONFIGS.keys()), help="Caso a executar")
    parser.add_argument("--wind-configs", type=Path, nargs="+", required=True, metavar="JSON",
                        help="Arquivos JSON dos cenários eólicos a comparar")
    args = parser.parse_args()

    base_config = CONFIGS[args.case]
    case_name   = base_config["case_name"]
    results_dir = base_config["results_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)

    scenarios = {}

    for json_path in args.wind_configs:
        with open(json_path) as f:
            wind_config = json.load(f)

        hour = wind_config["hour"]
        print(f"\n{'='*55}")
        print(f"Cenário: {json_path.name}  (hora {hour})")
        print(f"{'='*55}")

        res, total_kw = _run_scenario(base_config, wind_config)

        if res.F is None or len(res.F) == 0:
            print(f"  Nenhuma solução factível para hora {hour}.")
            continue

        F = res.F
        label = f"Hora {hour}  ({total_kw:.0f} kW)"
        print(f"  {len(F)} soluções | "
              f"f1_min={F[:,0].min():.1f} $/h | "
              f"f2_min={F[:,1].min():.4f} pu | "
              f"f3_min={F[:,2].min():.3f} ton/h")

        scenarios[hour] = {"F": F, "label": label, "kw": total_kw}

    if not scenarios:
        print("Nenhum cenário com solução factível.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    csv_path = results_dir / f"wind_comparison_{case_name}_{timestamp}.csv"
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["hour", "kw_wind", "sol", "cost_dh", "voltage_deviation_pu", "emissions_ton_h"])
        for hour, data in sorted(scenarios.items()):
            for i, f in enumerate(data["F"]):
                writer.writerow([hour, f"{data['kw']:.1f}", i + 1] + [f"{v:.6f}" for v in f])
    print(f"\nCSV salvo: {csv_path}")

    plot_path = results_dir / f"wind_comparison_{case_name}_{timestamp}.png"
    plot_wind_scenario_comparison(scenarios, plot_path, case_name=case_name)
    print(f"Gráfico salvo: {plot_path}")


if __name__ == "__main__":
    main()
