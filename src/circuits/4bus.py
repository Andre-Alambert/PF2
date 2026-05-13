from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

CONFIG = {
    # =========================
    # Paths
    # =========================
    "case_name": "4bus",
    "project_root": PROJECT_ROOT,
    "results_dir": PROJECT_ROOT / "results" / "4bus",
    "circuit_path": PROJECT_ROOT / "data" / "IEEETestCases" / "4Bus-YY-Bal" / "4Bus-YY-Bal-Modified.dss",

    # =========================
    # Elementos do circuito
    # =========================
    # Lista de geradores: cada entrada define nome e limites de despacho ativo.
    "generators": [
        {"name": "G1", "pg_min_kw": 0.0, "pg_max_kw": 1500.0,
         "cost_a": 0.01750, "cost_b": 1.75, "cost_c": 0.0,
         "emit_alpha": 0.02543, "emit_beta": -0.06047, "emit_gamma": 0.05638},
    ],
    # Fonte de tensão (opcional). Se presente, V_source é adicionado como gene.
    "vsource": {"name": "source", "vg_min_pu": 0.95, "vg_max_pu": 1.05},

    # =========================
    # Limites operacionais
    # =========================
    "voltage_lower_limit": 0.95,
    "voltage_upper_limit": 1.05,

    # =========================
    # Função objetivo agregada
    # =========================
    "objective_weights": {"w_cost": 1.0, "w_voltage": 1.0, "w_emissions": 0.0},

    # =========================
    # Penalizações (restrições duras)
    # =========================
    "voltage_penalty_weight": 100.0,
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
