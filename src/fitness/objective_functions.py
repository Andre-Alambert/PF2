def objective_generation_cost(generators_dispatched: list, config_generators: list) -> float:
    """f1 = Σ (aᵢ·Pᵢ² + bᵢ·Pᵢ + cᵢ) [$/h], P em MW."""
    cost = 0.0
    for gen, cfg in zip(generators_dispatched, config_generators):
        p_mw = gen["kw"] / 1000.0
        cost += cfg["cost_a"] * p_mw ** 2 + cfg["cost_b"] * p_mw + cfg["cost_c"]
    return cost


def objective_voltage_deviation(voltages_pu: list, v_ref: float = 1.0) -> float:
    """f2 = Σ |Vᵢ - Vref| [pu]."""
    return sum(abs(v - v_ref) for v in voltages_pu)


def objective_emissions(generators_dispatched: list, config_generators: list) -> float:
    """f3 = Σ (αᵢ + βᵢ·Pᵢ + γᵢ·Pᵢ²) [ton/h], P em MW."""
    emissions = 0.0
    for gen, cfg in zip(generators_dispatched, config_generators):
        p_mw = gen["kw"] / 1000.0
        emissions += cfg["emit_alpha"] + cfg["emit_beta"] * p_mw + cfg["emit_gamma"] * p_mw ** 2
    return emissions


def compute_normalization_bounds(config: dict) -> dict:
    """
    Computa limites analíticos para normalização de cada objetivo.
    f1 e f3: avaliados em pg_min e pg_max de cada gerador.
    f2: 0.0 no melhor caso; config["f2_max_pu"] no pior caso.
    """
    gens = config["generators"]

    def _cost(p_mw, g):
        return g["cost_a"] * p_mw ** 2 + g["cost_b"] * p_mw + g["cost_c"]

    def _emit(p_mw, g):
        return g["emit_alpha"] + g["emit_beta"] * p_mw + g["emit_gamma"] * p_mw ** 2

    f1_min = sum(_cost(g["pg_min_kw"] / 1000.0, g) for g in gens)
    f1_max = sum(_cost(g["pg_max_kw"] / 1000.0, g) for g in gens)
    f3_min = sum(_emit(g["pg_min_kw"] / 1000.0, g) for g in gens)
    f3_max = sum(_emit(g["pg_max_kw"] / 1000.0, g) for g in gens)

    # Garante que min <= max (f3 pode ser não-monotônica em Pmin muito baixo)
    if f3_min > f3_max:
        f3_min, f3_max = f3_max, f3_min

    return {
        "f1_min": f1_min,
        "f1_max": f1_max,
        "f2_min": 0.0,
        "f2_max": config.get("f2_max_pu", 3.0),
        "f3_min": f3_min,
        "f3_max": f3_max,
    }


def normalize(value: float, f_min: float, f_max: float) -> float:
    span = f_max - f_min
    if span < 1e-9:
        return 0.0
    return (value - f_min) / span
