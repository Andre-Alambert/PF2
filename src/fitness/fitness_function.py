from src.fitness.evaluation import evaluate_solution
from src.fitness.penalties import voltage_penalty, convergence_penalty
from src.fitness.objective_functions import (
    objective_generation_cost,
    objective_voltage_deviation,
    objective_emissions,
    compute_normalization_bounds,
    normalize,
)
from src.opendss.opendss_interface import (
    create_dss, compile_circuit, solve_power_flow, get_all_bus_voltages_pu,
    add_wind_generators, apply_wind_scenario,
)

_eval_cache = {}
_verbose = True


def get_eval_cache():
    return _eval_cache


def clear_eval_cache():
    _eval_cache.clear()


def set_verbose(value: bool):
    global _verbose
    _verbose = value


def make_fitness_function(config):
    """
    Fábrica que cria e compila uma instância dedicada do OpenDSS para o circuito
    definido em `config`, e retorna uma função de fitness compatível com o pygad.

    Função objetivo agregada (soma ponderada normalizada):
        F = w_cost·f1' + w_voltage·f2' + w_emissions·f3'
    onde f1=custo de geração [$/h], f2=desvio de tensão [pu], f3=emissões [ton/h].
    Penalidade de restrição dura (violação de banda de tensão) é somada separadamente.
    """
    dss = create_dss(allow_forms=config["allow_forms"])
    compile_circuit(dss, config["circuit_path"])
    if config.get("wind_generators"):
        add_wind_generators(dss, config)
        apply_wind_scenario(dss, config, config.get("wind_scenario_hour", 12))
    solve_power_flow(dss)
    v_refs_pu = get_all_bus_voltages_pu(dss)
    bounds = compute_normalization_bounds(config, v_refs_pu)

    def fitness_fn(ga_instance, solution, solution_idx):
        metrics = evaluate_solution(dss, solution, config)

        if not metrics["converged"]:
            _eval_cache[tuple(solution)] = metrics
            total_cost = convergence_penalty(
                metrics["converged"],
                penalty_value=config["convergence_penalty"]
            )
            fitness = 1.0 / (1.0 + total_cost)

            if _verbose:
                print(f"[{solution_idx}] sol={solution} | NÃO CONVERGIU | fitness={fitness}")
            return fitness

        f1 = objective_generation_cost(metrics["generators_dispatched"], config["generators"])
        f2 = objective_voltage_deviation(metrics["voltages_pu"], v_refs_pu)
        f3 = objective_emissions(metrics["generators_dispatched"], config["generators"])

        f1_n = normalize(f1, bounds["f1_min"], bounds["f1_max"])
        f2_n = normalize(f2, bounds["f2_min"], bounds["f2_max"])
        f3_n = normalize(f3, bounds["f3_min"], bounds["f3_max"])

        w = config["objective_weights"]
        F = w["w_cost"] * f1_n + w["w_voltage"] * f2_n + w["w_emissions"] * f3_n

        pen_v = config["voltage_penalty_weight"] * voltage_penalty(
            metrics["voltages_pu"],
            lower=config["voltage_lower_limit"],
            upper=config["voltage_upper_limit"]
        )

        total_cost = F + pen_v
        fitness = 1.0 / (1.0 + total_cost)

        metrics["generation_cost_dh"] = f1
        metrics["emissions_ton_h"] = f3
        metrics["voltage_deviation_pu"] = f2
        _eval_cache[tuple(solution)] = metrics

        if _verbose:
            print(
                f"[{solution_idx}] sol={solution} | "
                f"cost={f1:.2f} $/h | vdev={f2:.4f} pu | emit={f3:.5f} ton/h | "
                f"F={F:.4f} | pen_v={pen_v:.4f} | fitness={fitness:.8f}"
            )

        return fitness

    return fitness_fn
