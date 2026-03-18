from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    # =========================
    # Paths
    # =========================
    "project_root": PROJECT_ROOT,
    "circuit_path": PROJECT_ROOT / "data" / "IEEETestCases" / "4Bus-YY-Bal" / "4Bus-YY-Bal-Modified.dss",

    # =========================
    # Elementos do circuito
    # =========================
    "generator_name": "G1",
    "source_name": "source",

    # =========================
    # Variáveis de decisão
    # =========================
    # potência do gerador (kW)
    "pg_min_kw": 0.0,
    "pg_max_kw": 1500.0,

    # tensão da fonte (pu)
    "vg_min_pu": 0.95,
    "vg_max_pu": 1.05,

    # =========================
    # Limites operacionais
    # =========================
    "voltage_lower_limit": 0.95,
    "voltage_upper_limit": 1.05,

    # =========================
    # Penalizações
    # =========================
    "voltage_penalty_weight": 10000.0,   # bem alto no começo
    "convergence_penalty": 1e6,

    # =========================
    # Parâmetros do GA (validação)
    # =========================
    "population_size": 6,
    "num_generations": 5,
    "num_parents_mating": 3,

    # =========================
    # OpenDSS
    # =========================
    "allow_forms": False,
}