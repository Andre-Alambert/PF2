def voltage_penalty(voltages_pu, lower=0.95, upper=1.05):
    penalty = 0.0

    for v in voltages_pu:
        penalty += max(0.0, lower - v) ** 2
        penalty += max(0.0, v - upper) ** 2

    return penalty


def convergence_penalty(converged, penalty_value=1e6):
    return 0.0 if converged else penalty_value