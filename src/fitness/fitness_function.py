from ..config import CONFIG
from .evaluation import evaluate_solution
from .penalties import voltage_penalty, convergence_penalty
from ..opendss.opendss_interface import create_dss, compile_circuit

# Instância global do OpenDSS
dss = create_dss(allow_forms=CONFIG["allow_forms"])
compile_circuit(dss, CONFIG["circuit_path"])


def fitness_function(ga_instance, solution, solution_idx):
    """
    Fitness chamada pelo pygad.
    O pygad maximiza, então convertemos custo em fitness.
    """
    metrics = evaluate_solution(dss, solution, CONFIG)

    if not metrics["converged"]:
        total_cost = convergence_penalty(
            metrics["converged"],
            penalty_value=CONFIG["convergence_penalty"]
        )
        return 1.0 / (1.0 + total_cost)

    losses_kw = metrics["losses_kw"]

    pen_v = CONFIG["voltage_penalty_weight"] * voltage_penalty(
        metrics["voltages_pu"],
        lower=CONFIG["voltage_lower_limit"],
        upper=CONFIG["voltage_upper_limit"]
    )

    total_cost = losses_kw + pen_v

    return 1.0 / (1.0 + total_cost)