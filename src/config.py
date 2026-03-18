from pathlib import Path

# raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    # =========================
    # Paths
    # =========================
    "project_root": PROJECT_ROOT,
    "circuit_path": PROJECT_ROOT / "data" / "IEEETestCases" / "4Bus-YY-Bal" / "4Bus-YY-Bal.dss",

    # =========================
    # Circuit elements
    # =========================
    # Ajuste conforme seu circuito
    "generator_name": "G1",
    "source_name": "source",

    # =========================
    # Decision variables
    # =========================
    # potência do gerador
    "pg_min_kw": 0.0,
    "pg_max_kw": 1000.0,

    # tensão da fonte
    "vg_min_pu": 0.95,
    "vg_max_pu": 1.05,

    # =========================
    # Operational limits
    # =========================
    "voltage_lower_limit": 0.95,
    "voltage_upper_limit": 1.05,

    # =========================
    # Fitness / penalties
    # =========================
    "voltage_penalty_weight": 1000.0,
    "convergence_penalty": 1e6,

    # =========================
    # GA parameters
    # =========================
    "population_size": 20,
    "num_generations": 30,
    "num_parents_mating": 10,

    # =========================
    # OpenDSS settings
    # =========================
    "allow_forms": False,
}