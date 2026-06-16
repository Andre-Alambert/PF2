from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from py_dss_interface import DSS


def create_dss(allow_forms: bool = False) -> DSS:
    """
    Cria uma instância do OpenDSS.
    """
    dss = DSS()

    try:
        dss.dssinterface.allow_forms = allow_forms
    except Exception:
        pass

    return dss


def compile_circuit(dss: DSS, circuit_path: str | Path) -> None:
    """
    Compila o circuito principal.
    """
    circuit_path = Path(circuit_path).resolve()

    if not circuit_path.exists():
        raise FileNotFoundError(f"Circuit file not found: {circuit_path}")

    dss.text(f'Compile "{circuit_path}"')


def set_generator_kw(dss: DSS, gen_name: str, kw: float) -> None:
    """
    Edita potência ativa do gerador.
    """
    dss.text(f"Edit Generator.{gen_name} kW={kw}")


def set_source_pu(dss: DSS, source_name: str, pu: float) -> None:
    """
    Edita tensão da fonte.
    """
    dss.text(f"Edit Vsource.{source_name} pu={pu}")


def apply_solution(dss: DSS, decoded_solution: Dict, config: Dict) -> None:
    """
    Aplica variáveis da solução no circuito.
    Itera sobre todos os geradores e, se houver vsource no config, ajusta a tensão da fonte.
    """
    for gen in decoded_solution["generators"]:
        set_generator_kw(dss, gen["name"], gen["kw"])

    if decoded_solution.get("vsource_pu") is not None:
        set_source_pu(dss, config["vsource"]["name"], decoded_solution["vsource_pu"])


def solve_power_flow(dss: DSS) -> bool:
    """
    Resolve fluxo de potência.
    """
    dss.solution.solve()

    try:
        return dss.solution.converged == 1
    except Exception:
        return False


def get_total_losses_kw(dss: DSS) -> float:
    """
    Retorna perdas totais ativas em kW.
    """
    losses = dss.circuit.losses

    if not losses:
        raise RuntimeError("Could not read circuit losses.")

    p_loss_w = losses[0]

    return float(p_loss_w) / 1000.0


def get_all_bus_names(dss: DSS) -> List[str]:
    """
    Lista nomes das barras.
    """
    return list(dss.circuit.buses_names)


def get_bus_voltage_pu_by_name(dss: DSS, bus_name: str) -> List[float]:
    """
    Retorna tensões em pu de uma barra.
    """
    dss.circuit.set_active_bus(bus_name)

    pu_vals = dss.bus.vmag_angle_pu

    magnitudes = []

    if pu_vals:
        for i in range(0, len(pu_vals), 2):
            magnitudes.append(float(pu_vals[i]))

    return magnitudes


def get_all_bus_voltages_pu(dss: DSS) -> List[float]:
    """
    Retorna todas as tensões do sistema.
    """
    voltages = []

    for bus_name in get_all_bus_names(dss):
        voltages.extend(get_bus_voltage_pu_by_name(dss, bus_name))

    return voltages


def get_min_voltage_pu(dss: DSS) -> float:
    voltages = get_all_bus_voltages_pu(dss)
    return min(voltages)


def get_max_voltage_pu(dss: DSS) -> float:
    voltages = get_all_bus_voltages_pu(dss)
    return max(voltages)


def generate_loadshape_weibull(k: float, lam: float, seed: Optional[int] = None) -> List[float]:
    """
    Gera um loadshape de 24 pontos a partir da distribuição de Weibull.

    Parâmetros:
        k   : parâmetro de forma da Weibull
        lam : parâmetro de escala [m/s] (velocidade média)
        seed: semente para reprodutibilidade (None = aleatório a cada chamada)

    Curva de potência por partes (típica de aerogeradores):
        v < v_ci (3 m/s)          → P = 0  (cut-in)
        v_ci ≤ v < v_r (12 m/s)   → P = (v - v_ci) / (v_r - v_ci)  (rampa linear)
        v_r ≤ v ≤ v_co (25 m/s)   → P = 1  (potência nominal)
        v > v_co                   → P = 0  (cut-out)
    """
    rng = np.random.default_rng(seed)
    velocities = lam * rng.weibull(k, 24)
    v_ci, v_r, v_co = 3.0, 12.0, 25.0
    loadshape = []
    for v in velocities:
        if v < v_ci:
            p = 0.0
        elif v < v_r:
            p = (v - v_ci) / (v_r - v_ci)
        elif v <= v_co:
            p = 1.0
        else:
            p = 0.0
        loadshape.append(float(p))
    return loadshape


def resolve_loadshape(wind_config: Dict) -> List[float]:
    """
    Resolve o loadshape de 24 pontos a partir da configuração do cenário eólico.

    Prioridade:
        1. Campo "loadshape" no JSON — se for uma lista de exatamente 24 pontos.
        2. Campo "weibull" no JSON — gera estocasticamente (seed opcional).
    """
    ls = wind_config.get("loadshape")
    if isinstance(ls, list) and len(ls) == 24:
        return [float(v) for v in ls]

    weibull = wind_config.get("weibull", {})
    k    = float(weibull.get("k",      2.0))
    lam  = float(weibull.get("lambda", 8.0))
    seed = weibull.get("seed", None)
    return generate_loadshape_weibull(k, lam, seed)


def add_wind_generators(dss: DSS, wind_config: Dict) -> None:
    """
    Adiciona geradores eólicos como cargas negativas (injeção P, Q=0).
    Usar Load em vez de Generator mantém a barra como PQ bus, compatível
    com os geradores model=3 (PV bus) já presentes no circuito.
    wind_config: dict carregado do JSON de cenário eólico.
    Chamado uma vez após compile_circuit; kW inicial = -kw_max (ajustado em seguida).
    """
    for wg in wind_config.get("generators", []):
        dss.text(
            f"New Load.{wg['name']} Bus1={wg['bus']} Phases=3 "
            f"kV={wg['kv']} kW=-{wg['kw_max']:.1f} kvar=0 Model=1"
        )


def apply_wind_scenario(dss: DSS, wind_config: Dict) -> None:
    """
    Ajusta kW de cada gerador eólico para o fator de capacidade da hora definida no JSON.
    O loadshape é resolvido uma vez (Weibull ou hardcoded) e aplicado a todos os geradores.
    Geradores com kW < 0.1 (abaixo do cut-in) são desabilitados para não alterar a
    topologia do fluxo de potência.
    """
    hour = wind_config.get("hour", 12)
    loadshape = resolve_loadshape(wind_config)
    factor = loadshape[hour % len(loadshape)]
    for wg in wind_config.get("generators", []):
        kw = factor * wg["kw_max"]
        if kw < 0.1:
            dss.text(f"Edit Load.{wg['name']} Enabled=No")
        else:
            dss.text(f"Edit Load.{wg['name']} kW=-{kw:.1f} kvar=0 Enabled=Yes")


def reset_and_recompile(dss: DSS, circuit_path: str | Path) -> None:
    """
    Recompila o circuito (opcional para evitar efeitos acumulados).
    """
    dss.text("Clear")
    compile_circuit(dss, circuit_path)