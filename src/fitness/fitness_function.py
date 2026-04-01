from src.config import CONFIG
from src.fitness.evaluation import evaluate_solution
from src.fitness.penalties import voltage_penalty, convergence_penalty
from src.opendss.opendss_interface import create_dss, compile_circuit

dss = create_dss(allow_forms=CONFIG["allow_forms"])
compile_circuit(dss, CONFIG["circuit_path"])

_eval_cache = {}
_verbose = True


def get_eval_cache():
    return _eval_cache


def clear_eval_cache():
    _eval_cache.clear()


def set_verbose(value: bool):
    global _verbose
    _verbose = value


def fitness_function(ga_instance, solution, solution_idx):
    metrics = evaluate_solution(dss, solution, CONFIG)
    _eval_cache[solution_idx] = metrics

    if not metrics["converged"]:
        total_cost = convergence_penalty(
            metrics["converged"],
            penalty_value=CONFIG["convergence_penalty"]
        )
        fitness = 1.0 / (1.0 + total_cost)

        if _verbose:
            print(f"[{solution_idx}] sol={solution} | NÃO CONVERGIU | fitness={fitness}")
        return fitness

    losses_kw = metrics["losses_kw"]

    pen_v_raw = voltage_penalty(
        metrics["voltages_pu"],
        lower=CONFIG["voltage_lower_limit"],
        upper=CONFIG["voltage_upper_limit"]
    )

    pen_v = CONFIG["voltage_penalty_weight"] * pen_v_raw
    total_cost = losses_kw + pen_v
    fitness = 1.0 / (1.0 + total_cost)

    if _verbose:
        print(
            f"[{solution_idx}] sol={solution} | "
            f"losses={losses_kw:.3f} | "
            f"vmin={metrics['v_min']:.3f} | vmax={metrics['v_max']:.3f} | "
            f"pen_v={pen_v:.3f} | fitness={fitness:.8f}"
        )

    return fitness