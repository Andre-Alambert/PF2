from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.config_ieee30 import CONFIG_IEEE30 as CONFIG
from src.genetic_algorithm.encoding import get_gene_space, decode_solution, get_gene_names
from src.genetic_algorithm.runner import build_ga_instance, run_ga
from src.fitness.fitness_function import make_fitness_function
from src.results.logger import RunLogger
from src.results.plotting import plot_convergence, plot_voltage_profile
from src.opendss.opendss_interface import (
    create_dss,
    compile_circuit,
    apply_solution,
    solve_power_flow,
    get_all_bus_names,
    get_bus_voltage_pu_by_name,
)


def main():
    logger = RunLogger(CONFIG["results_dir"])

    gene_space = get_gene_space(CONFIG)
    fitness_function = make_fitness_function(CONFIG)

    print(f"\nCircuito : {CONFIG['circuit_path'].name}")
    print(f"Genes    : {get_gene_names(CONFIG)}")
    print(f"Pop={CONFIG['population_size']}  Gen={CONFIG['num_generations']}\n")

    ga_instance = build_ga_instance(
        config=CONFIG,
        gene_space=gene_space,
        fitness_func=fitness_function,
        logger=logger,
    )

    solution, solution_fitness, _ = run_ga(ga_instance)

    # --- Save CSV ---
    csv_path = logger.save_csv()
    if csv_path:
        print(f"\nResultados salvos em: {csv_path}")

    # --- Convergence plot ---
    if logger.history:
        conv_path = logger.results_dir / f"convergence_ieee30_{logger.timestamp}.png"
        plot_convergence(logger.history, conv_path)
        print(f"Gráfico de convergência: {conv_path}")

    # --- Decode and display best solution ---
    decoded = decode_solution(solution, CONFIG)
    print("\n=== MELHOR SOLUÇÃO — DESPACHO ATIVO ===")
    for gen in decoded["generators"]:
        print(f"  {gen['name']:>4}: P = {gen['kw']:>10.1f} kW")

    # --- Voltage profile of best solution ---
    dss = create_dss(allow_forms=CONFIG["allow_forms"])
    compile_circuit(dss, CONFIG["circuit_path"])
    apply_solution(dss, decoded, CONFIG)
    solve_power_flow(dss)

    bus_names = get_all_bus_names(dss)
    bus_voltages = [get_bus_voltage_pu_by_name(dss, name) for name in bus_names]

    volt_path = logger.results_dir / f"voltage_profile_ieee30_{logger.timestamp}.png"
    plot_voltage_profile(
        bus_names,
        bus_voltages,
        limits=(CONFIG["voltage_lower_limit"], CONFIG["voltage_upper_limit"]),
        save_path=volt_path,
    )
    print(f"Perfil de tensão: {volt_path}")


if __name__ == "__main__":
    main()
