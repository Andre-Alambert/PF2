from ..genetic_algorithm.encoding import decode_solution
from ..opendss.opendss_interface import (
    apply_solution,
    solve_power_flow,
    get_total_losses_kw,
    get_all_bus_voltages_pu,
)


def evaluate_solution(dss, solution, config):
    """
    Avalia uma solução candidata no circuito OpenDSS.
    Retorna métricas elétricas que depois serão usadas na fitness.
    """
    decoded_solution = decode_solution(solution)

    apply_solution(dss, decoded_solution, config)

    converged = solve_power_flow(dss)

    if not converged:
        return {
            "converged": False,
            "losses_kw": None,
            "voltages_pu": [],
            "v_min": None,
            "v_max": None,
        }

    voltages_pu = get_all_bus_voltages_pu(dss)

    return {
        "converged": True,
        "losses_kw": get_total_losses_kw(dss),
        "voltages_pu": voltages_pu,
        "v_min": min(voltages_pu) if voltages_pu else None,
        "v_max": max(voltages_pu) if voltages_pu else None,
    }