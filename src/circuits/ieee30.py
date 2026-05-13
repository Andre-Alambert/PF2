from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Limites padrão de despacho ativo do IEEE 30-Bus (literatura clássica de OPF).
# Referência: Lee, Park & Ortiz, IEE Trans. Power Apparatus & Systems, 1985.
CONFIG = {
    # =========================
    # Paths
    # =========================
    "case_name": "ieee30",
    "project_root": PROJECT_ROOT,
    "results_dir": PROJECT_ROOT / "results" / "30bus",
    "circuit_path": PROJECT_ROOT / "data" / "IEEETestCases" / "IEEE 30 Bus" / "Master.dss",

    # =========================
    # Elementos do circuito
    # =========================
    # Cinco geradores PV/PQ; o slack (B1/Vsource) permanece fixo em 1.06 pu.
    # Sem chave "vsource": tensão do slack não é variável de controle.
    # Coeficientes de custo (a [$/MW²h], b [$/MWh], c [$/h]) e emissão
    # (alpha [ton/h], beta [ton/MWh], gamma [ton/MW²h]) por gerador.
    # Fonte: Lee, Park & Ortiz (1985) / El-Keib (1994) — benchmark IEEE 30-bus.
    # Conversão de unidades: genes em kW → kw/1000 → MW dentro das funções objetivo.
    "generators": [
        {"name": "B2",  "pg_min_kw": 0.0, "pg_max_kw": 80_000.0,
         "cost_a": 0.00375, "cost_b": 2.00, "cost_c": 0.0,
         "emit_alpha": 0.04091, "emit_beta": -0.05554, "emit_gamma": 0.06490},
        {"name": "B5",  "pg_min_kw": 0.0, "pg_max_kw": 50_000.0,
         "cost_a": 0.01750, "cost_b": 1.75, "cost_c": 0.0,
         "emit_alpha": 0.02543, "emit_beta": -0.06047, "emit_gamma": 0.05638},
        {"name": "B8",  "pg_min_kw": 0.0, "pg_max_kw": 35_000.0,
         "cost_a": 0.06250, "cost_b": 1.00, "cost_c": 0.0,
         "emit_alpha": 0.04258, "emit_beta": -0.05094, "emit_gamma": 0.04586},
        {"name": "B11", "pg_min_kw": 0.0, "pg_max_kw": 30_000.0,
         "cost_a": 0.00834, "cost_b": 3.25, "cost_c": 0.0,
         "emit_alpha": 0.05326, "emit_beta": -0.03550, "emit_gamma": 0.03970},
        {"name": "B13", "pg_min_kw": 0.0, "pg_max_kw": 40_000.0,
         "cost_a": 0.02500, "cost_b": 3.00, "cost_c": 0.0,
         "emit_alpha": 0.04716, "emit_beta": -0.05940, "emit_gamma": 0.05660},
    ],

    # =========================
    # Limites operacionais
    # =========================
    # IEEE 30-Bus tem barras de 11 kV (B11, B13) com Vpu nominal 1.082/1.071,
    # logo a banda superior é alargada levemente para 1.10 pu.
    "voltage_lower_limit": 0.95,
    "voltage_upper_limit": 1.10,

    # =========================
    # Função objetivo agregada
    # =========================
    # Pesos da soma ponderada normalizada: F = w_cost·f1' + w_voltage·f2' + w_emissions·f3'
    # w_emissions=0 desativa emissões na Etapa 1; basta mudar o valor para ativá-las.
    "objective_weights": {"w_cost": 1.0, "w_voltage": 1.0, "w_emissions": 0.0},

    # =========================
    # Penalizações (restrições duras)
    # =========================
    # F normalizado fica em [0, 2]; voltage_penalty_weight recalibrado para essa escala.
    # Violação de 0.03 pu em 5 barras → pen_v ≈ 0.0009 × 5 × 100 = 0.45 >> F típico.
    "voltage_penalty_weight": 100.0,
    "convergence_penalty": 1e6,

    # =========================
    # Parâmetros do GA
    # Melhor configuração identificada pelo grid search (pop=40, gen=20, mut=20%):
    #   fitness mediano = 0.000262 | std = 4.67e-6 | conv. gen = 13 | t = 1.227s
    # =========================
    "population_size": 40,
    "num_generations": 40,
    "num_parents_mating": 20,
    "mutation_percent_genes": 20,

    # =========================
    # OpenDSS
    # =========================
    "allow_forms": False,
}
