from pathlib import Path
from typing import Dict, List

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


def add_wind_generators(dss: DSS, wind_config: Dict) -> None:
    """
    Adiciona geradores eólicos ao circuito via comandos DSS.
    wind_config: dict carregado do JSON de cenário eólico.
    Chamado uma vez após compile_circuit; kW inicial = kw_max (ajustado em seguida).
    """
    for wg in wind_config.get("generators", []):
        dss.text(
            f"New Generator.{wg['name']} Bus1={wg['bus']} "
            f"kV={wg['kv']} kW={wg['kw_max']:.1f} Model=1"
        )


def apply_wind_scenario(dss: DSS, wind_config: Dict) -> None:
    """
    Ajusta kW de cada gerador eólico para o fator de capacidade da hora definida no JSON.
    Cada gerador tem seu próprio loadshape.
    """
    hour = wind_config.get("hour", 12)
    for wg in wind_config.get("generators", []):
        loadshape = wg.get("loadshape", [])
        factor = loadshape[hour % len(loadshape)] if loadshape else 0.0
        kw = factor * wg["kw_max"]
        dss.text(f"Edit Generator.{wg['name']} kW={kw:.1f}")


def reset_and_recompile(dss: DSS, circuit_path: str | Path) -> None:
    """
    Recompila o circuito (opcional para evitar efeitos acumulados).
    """
    dss.text("Clear")
    compile_circuit(dss, circuit_path)