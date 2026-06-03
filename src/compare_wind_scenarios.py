import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.configs import CONFIGS
from src.genetic_algorithm.nsga3_runner import run_nsga3
from src.opendss.opendss_interface import (
    create_dss, compile_circuit, solve_power_flow, get_all_bus_voltages_pu,
    add_wind_generators, apply_wind_scenario,
)
from src.results.pareto import plot_wind_scenario_comparison


DEFAULT_HOURS = [8, 12, 18]


def _run_scenario(base_config, hour):
    loadshape = base_config.get("wind_loadshape", [])
    kw_max    = base_config["wind_generators"][0]["kw_max"]
    factor    = loadshape[hour % len(loadshape)] if loadshape else 0.0
    kw        = factor * kw_max

    CONFIG = dict(base_config)
    CONFIG["wind_scenario_hour"] = hour

    dss = create_dss(allow_forms=CONFIG["allow_forms"])
    compile_circuit(dss, CONFIG["circuit_path"])
    add_wind_generators(dss, CONFIG)
    apply_wind_scenario(dss, CONFIG, hour)
    solve_power_flow(dss)
    v_refs = get_all_bus_voltages_pu(dss)

    res = run_nsga3(CONFIG, dss, v_refs, verbose=False)
    return res, kw, factor


def main():
    parser = argparse.ArgumentParser(description="Comparação de cenários eólicos — NSGA-III")
    parser.add_argument("case", choices=list(CONFIGS.keys()), help="Caso a executar")
    parser.add_argument("--hours", type=int, nargs="+", default=DEFAULT_HOURS, metavar="H",
                        help=f"Horas dos cenários (padrão: {DEFAULT_HOURS})")
    args = parser.parse_args()

    base_config = CONFIGS[args.case]
    case_name   = base_config["case_name"]
    results_dir = base_config["results_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)

    if not base_config.get("wind_generators"):
        print("Erro: caso sem geradores eólicos configurados.")
        return

    scenarios = {}

    for hour in sorted(args.hours):
        print(f"\n{'='*55}")
        print(f"Cenário: hora {hour}")
        print(f"{'='*55}")

        res, kw, factor = _run_scenario(base_config, hour)

        if res.F is None or len(res.F) == 0:
            print(f"  Nenhuma solução factível para hora {hour}.")
            continue

        F     = res.F
        label = f"Hora {hour}  ({kw:.0f} kW, {factor*100:.0f}%)"
        print(f"  {len(F)} soluções | "
              f"f1_min={F[:,0].min():.1f} $/h | "
              f"f2_min={F[:,1].min():.4f} pu | "
              f"f3_min={F[:,2].min():.3f} ton/h")

        scenarios[hour] = {"F": F, "label": label, "kw": kw, "factor": factor}

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
