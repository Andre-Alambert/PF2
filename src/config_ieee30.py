from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Limites padrão de despacho ativo do IEEE 30-Bus (literatura clássica de OPF).
# Referência: Lee, Park & Ortiz, IEE Trans. Power Apparatus & Systems, 1985.
CONFIG_IEEE30 = {
    # =========================
    # Paths
    # =========================
    "project_root": PROJECT_ROOT,
    "circuit_path": PROJECT_ROOT / "data" / "IEEETestCases" / "IEEE 30 Bus" / "Master.dss",

    # =========================
    # Elementos do circuito
    # =========================
    # Cinco geradores PV/PQ; o slack (B1/Vsource) permanece fixo em 1.06 pu.
    # Sem chave "vsource": tensão do slack não é variável de controle.
    "generators": [
        {"name": "B2",  "pg_min_kw":     0.0, "pg_max_kw":  80_000.0},
        {"name": "B5",  "pg_min_kw":     0.0, "pg_max_kw":  50_000.0},
        {"name": "B8",  "pg_min_kw":     0.0, "pg_max_kw":  35_000.0},
        {"name": "B11", "pg_min_kw":     0.0, "pg_max_kw":  30_000.0},
        {"name": "B13", "pg_min_kw":     0.0, "pg_max_kw":  40_000.0},
    ],

    # =========================
    # Limites operacionais
    # =========================
    # IEEE 30-Bus tem barras de 11 kV (B11, B13) com Vpu nominal 1.082/1.071,
    # logo a banda superior é alargada levemente para 1.10 pu.
    "voltage_lower_limit": 0.95,
    "voltage_upper_limit": 1.10,

    # =========================
    # Penalizações
    # =========================
    # As perdas neste circuito são da ordem de 10–30 MW (10.000–30.000 kW).
    # O peso de penalidade é mantido em 10.000 como ponto de partida;
    # pode ser calibrado via experimento se violações forem sistematicamente ignoradas.
    "voltage_penalty_weight": 10_000.0,
    "convergence_penalty": 1e6,

    # =========================
    # Parâmetros do GA (validação rápida)
    # =========================
    "population_size": 10,
    "num_generations": 10,
    "num_parents_mating": 5,

    # =========================
    # OpenDSS
    # =========================
    "allow_forms": False,
}
