from pathlib import Path
import sys
import argparse
import csv
import json
from datetime import datetime

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.configs import CONFIGS
from src.genetic_algorithm.encoding import get_gene_names
from src.genetic_algorithm.nsga2_runner import run_nsga2
from src.opendss.opendss_interface import (
    create_dss, compile_circuit, solve_power_flow, get_all_bus_voltages_pu,
    add_wind_generators, apply_wind_scenario, resolve_loadshape,
)
from src.results.pareto import plot_pareto_nsga2


def main():
    parser = argparse.ArgumentParser(description="OPF multiobjetivo — NSGA-II")
    parser.add_argument("case", choices=list(CONFIGS.keys()), help="Caso a executar")
    parser.add_argument("--wind-config", type=Path, metavar="JSON",
                        help="Arquivo JSON com configuração dos geradores eólicos")
    parser.add_argument("--label", default="base",
                        help="Subdiretório em results_dir para organizar a rodada (ex.: base, h00, h11, h17)")
    args = parser.parse_args()

    CONFIG = dict(CONFIGS[args.case])
    case_name = CONFIG["case_name"]

    wind_config = None
    if args.wind_config:
        with open(args.wind_config) as f:
            wind_config = json.load(f)

    print(f"\nNSGA-II | Circuito: {CONFIG['circuit_path'].name}")
    print(f"Pop={CONFIG['population_size']}  Gen={CONFIG['num_generations']}  Objetivos=3 (custo, tensão, emissões)")

    if wind_config:
        hour      = wind_config["hour"]
        loadshape = resolve_loadshape(wind_config)
        factor    = loadshape[hour % len(loadshape)]
        for wg in wind_config["generators"]:
            kw = factor * wg["kw_max"]
            print(f"Vento    : {wg['name']} @ {wg['bus']} | hora={hour} | "
                  f"P={kw:.0f} kW ({factor*100:.0f}% de {wg['kw_max']:.0f} kW)")
    print()

    dss = create_dss(allow_forms=CONFIG["allow_forms"])
    compile_circuit(dss, CONFIG["circuit_path"])
    if wind_config:
        add_wind_generators(dss, wind_config)
        apply_wind_scenario(dss, wind_config)
    solve_power_flow(dss)
    v_refs = get_all_bus_voltages_pu(dss)

    print("Iniciando NSGA-II...\n")
    res = run_nsga2(CONFIG, dss, v_refs)

    if res.X is None:
        print("\nNenhuma solução factível encontrada.")
        return

    F = res.F  # (n_pareto, 3): [custo, vdev, emissões]
    X = res.X  # (n_pareto, n_var)

    print(f"\n=== FRENTE DE PARETO — {len(F)} soluções ===")
    print(f"{'#':>3}  {'Custo ($/h)':>12}  {'Vdev (pu)':>10}  {'Emissões (ton/h)':>16}")
    for i, f in enumerate(F):
        print(f"{i+1:>3}  {f[0]:>12.1f}  {f[1]:>10.4f}  {f[2]:>16.3f}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = CONFIG["results_dir"] / args.label
    results_dir.mkdir(parents=True, exist_ok=True)

    gene_names = get_gene_names(CONFIG)
    csv_path = results_dir / f"pareto_nsga2_{case_name}_{timestamp}.csv"
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sol"] + gene_names + ["cost_dh", "voltage_deviation_pu", "emissions_ton_h"])
        for i, (f, x) in enumerate(zip(F, X)):
            writer.writerow([i + 1] + list(x) + list(f))
    print(f"\nCSV salvo: {csv_path}")

    plot_path = results_dir / f"pareto_nsga2_{case_name}_{timestamp}.png"
    plot_pareto_nsga2(F, plot_path, case_name=case_name)
    print(f"Gráfico salvo: {plot_path}")


if __name__ == "__main__":
    main()
