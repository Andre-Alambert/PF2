from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# IEEE 118-Bus — configuração para testes de escalabilidade.
# Slack: bus 89_clinchrv (138 kV, pu=1.005, definido no master_file.dss).
#
# Geradores controlados: 18 unidades com despacho ativo no caso base (kW > 0.001).
# Os demais geradores do .dss (kW=0.001) são condensadores síncronos / barras PV
# com suporte reativo apenas — não são variáveis de decisão do NSGA-II.
#
# Pmax: estimativas baseadas no MATPOWER case118 (Zimmerman et al. 2011).
# Coeficientes de custo: curvas quadráticas aproximadas por tipo/porte de unidade —
#   adequados para teste de escalabilidade; validar contra literatura para análise rigorosa.
# Coeficientes de emissão: mesma ordem de grandeza do benchmark El-Keib (1994) do 30-bus,
#   sem referência específica para 118-bus — substituir se houver dado validado.
CONFIG = {
    # =========================
    # Paths
    # =========================
    "case_name": "ieee118",
    "project_root": PROJECT_ROOT,
    "results_dir": PROJECT_ROOT / "results-wind" / "118bus",
    "circuit_path": PROJECT_ROOT / "data" / "IEEETestCases" / "IEEE118Bus" / "master_file.dss",

    # =========================
    # Geradores controláveis
    # =========================
    "generators": [
        # Grandes unidades de base (>300 MW)
        {"name": "Gen_at_10_1",  "pg_min_kw":       0.0, "pg_max_kw": 500_000.0,
         "cost_a": 0.00375, "cost_b": 2.00, "cost_c": 0.0,
         "emit_alpha": 0.04091, "emit_beta": -0.05554, "emit_gamma": 0.06490},

        {"name": "Gen_at_26_1",  "pg_min_kw":       0.0, "pg_max_kw": 414_000.0,
         "cost_a": 0.00400, "cost_b": 2.50, "cost_c": 0.0,
         "emit_alpha": 0.04258, "emit_beta": -0.05094, "emit_gamma": 0.04586},

        {"name": "Gen_at_65_1",  "pg_min_kw":       0.0, "pg_max_kw": 491_000.0,
         "cost_a": 0.00350, "cost_b": 2.20, "cost_c": 0.0,
         "emit_alpha": 0.04091, "emit_beta": -0.05554, "emit_gamma": 0.06490},

        {"name": "Gen_at_66_1",  "pg_min_kw":       0.0, "pg_max_kw": 492_000.0,
         "cost_a": 0.00350, "cost_b": 2.20, "cost_c": 0.0,
         "emit_alpha": 0.04091, "emit_beta": -0.05554, "emit_gamma": 0.06490},

        {"name": "Gen_at_69_1",  "pg_min_kw":       0.0, "pg_max_kw": 805_000.0,
         "cost_a": 0.00250, "cost_b": 2.00, "cost_c": 0.0,
         "emit_alpha": 0.04716, "emit_beta": -0.05940, "emit_gamma": 0.05660},

        {"name": "Gen_at_80_1",  "pg_min_kw":       0.0, "pg_max_kw": 577_000.0,
         "cost_a": 0.00300, "cost_b": 2.10, "cost_c": 0.0,
         "emit_alpha": 0.04258, "emit_beta": -0.05094, "emit_gamma": 0.04586},

        # Unidades médias (100–300 MW)
        {"name": "Gen_at_25_1",  "pg_min_kw":       0.0, "pg_max_kw": 320_000.0,
         "cost_a": 0.00500, "cost_b": 3.00, "cost_c": 0.0,
         "emit_alpha": 0.04716, "emit_beta": -0.05940, "emit_gamma": 0.05660},

        {"name": "Gen_at_49_1",  "pg_min_kw":       0.0, "pg_max_kw": 304_000.0,
         "cost_a": 0.00600, "cost_b": 3.50, "cost_c": 0.0,
         "emit_alpha": 0.05326, "emit_beta": -0.03550, "emit_gamma": 0.03970},

        {"name": "Gen_at_59_1",  "pg_min_kw":       0.0, "pg_max_kw": 255_000.0,
         "cost_a": 0.00834, "cost_b": 4.00, "cost_c": 0.0,
         "emit_alpha": 0.04716, "emit_beta": -0.05940, "emit_gamma": 0.05660},

        {"name": "Gen_at_61_1",  "pg_min_kw":       0.0, "pg_max_kw": 260_000.0,
         "cost_a": 0.00800, "cost_b": 4.00, "cost_c": 0.0,
         "emit_alpha": 0.04716, "emit_beta": -0.05940, "emit_gamma": 0.05660},

        {"name": "Gen_at_100_1", "pg_min_kw":       0.0, "pg_max_kw": 352_000.0,
         "cost_a": 0.00500, "cost_b": 3.00, "cost_c": 0.0,
         "emit_alpha": 0.04258, "emit_beta": -0.05094, "emit_gamma": 0.04586},

        # Unidades menores (<100 MW)
        {"name": "Gen_at_12_1",  "pg_min_kw":       0.0, "pg_max_kw": 185_000.0,
         "cost_a": 0.01750, "cost_b": 3.50, "cost_c": 0.0,
         "emit_alpha": 0.02543, "emit_beta": -0.06047, "emit_gamma": 0.05638},

        {"name": "Gen_at_31_1",  "pg_min_kw":       0.0, "pg_max_kw": 107_000.0,
         "cost_a": 0.02500, "cost_b": 8.00, "cost_c": 0.0,
         "emit_alpha": 0.05326, "emit_beta": -0.03550, "emit_gamma": 0.03970},

        {"name": "Gen_at_46_1",  "pg_min_kw":       0.0, "pg_max_kw": 119_000.0,
         "cost_a": 0.02500, "cost_b": 7.00, "cost_c": 0.0,
         "emit_alpha": 0.04716, "emit_beta": -0.05940, "emit_gamma": 0.05660},

        {"name": "Gen_at_54_1",  "pg_min_kw":       0.0, "pg_max_kw": 148_000.0,
         "cost_a": 0.02500, "cost_b": 7.00, "cost_c": 0.0,
         "emit_alpha": 0.04258, "emit_beta": -0.05094, "emit_gamma": 0.04586},

        {"name": "Gen_at_87_1",  "pg_min_kw":       0.0, "pg_max_kw": 104_000.0,
         "cost_a": 0.06250, "cost_b": 10.0, "cost_c": 0.0,
         "emit_alpha": 0.05326, "emit_beta": -0.03550, "emit_gamma": 0.03970},

        {"name": "Gen_at_103_1", "pg_min_kw":       0.0, "pg_max_kw": 140_000.0,
         "cost_a": 0.03000, "cost_b": 8.00, "cost_c": 0.0,
         "emit_alpha": 0.04716, "emit_beta": -0.05940, "emit_gamma": 0.05660},

        {"name": "Gen_at_111_1", "pg_min_kw":       0.0, "pg_max_kw": 136_000.0,
         "cost_a": 0.03200, "cost_b": 8.00, "cost_c": 0.0,
         "emit_alpha": 0.02543, "emit_beta": -0.06047, "emit_gamma": 0.05638},
    ],

    # =========================
    # Limites operacionais
    # =========================
    # O 118-bus opera naturalmente abaixo de 0.95 pu em alguns buses (e.g. bus 76: 0.943 pu).
    # Limites alargados para refletir o range real do sistema — ajustar após análise do caso base.
    "voltage_lower_limit": 0.90,
    "voltage_upper_limit": 1.10,

    # =========================
    # Parâmetros do GA
    # 18 variáveis de decisão → pop maior que o 30-bus (5 vars).
    # NSGA-II usa population_size; NSGA-III usa n_partitions (pop derivado automaticamente).
    # n_partitions=8 → 45 reference points (Das-Dennis, n_obj=3)
    # =========================
    "population_size": 80,
    "n_partitions": 12,
    "num_generations": 80,
    # sbx_eta/pm_eta: ótimo do experimento de hiperparâmetros (HV mediano mais alto,
    # ver results/118bus/experiment_nsga2_ieee118_2026-06-16_03-43-01.csv)
    "sbx_eta": 20,
    "pm_eta": 10,

    # =========================
    # OpenDSS
    # =========================
    "allow_forms": False,

}
