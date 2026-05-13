# PF2 — Otimização de Fluxo de Potência via Algoritmo Genético

## Visão Geral

Projeto de Formatura 2 (PF2) de engenharia elétrica. Resolve um Optimal Power Flow (OPF) usando um Algoritmo Genético (pygad) com simulação de fluxo via OpenDSS (py_dss_interface). Caso principal: IEEE 30-Bus com 5 geradores controláveis.

## Arquitetura

```
src/
  circuits/        # Configs por circuito (ieee30.py, 4bus.py)
  fitness/
    fitness_function.py   # Factory do fitness (closure com DSS e bounds)
    objective_functions.py # f1, f2, f3 + normalização + bounds
    evaluation.py         # Executa o fluxo e decodifica a solução
    penalties.py          # Penalidade de violação de tensão (restrição dura)
  genetic_algorithm/      # Runner do pygad
  opendss/                # Interface com OpenDSS
  results/logger.py       # Salva CSV por run
data/IEEETestCases/       # Arquivos .dss dos circuitos
results/                  # CSVs de runs (30bus/, 4bus/)
```

## Estado Atual — Etapa 1 concluída

Função objetivo agregada (soma ponderada normalizada):

```
F = w_cost·f1' + w_voltage·f2' + w_emissions·f3'
fitness = 1 / (1 + F + pen_v)
```

- **f1** = custo de geração [$/h] — curvas quadráticas Lee/El-Keib 1985
- **f2** = desvio de tensão [pu] — referência **por barra** via fluxo base (não 1.0 pu uniforme)
- **f3** = emissões [ton/h] — w_emissions=0 (desativado na Etapa 1, basta mudar o peso)
- **pen_v** = penalidade de violação de banda [0.95, 1.10] pu (restrição dura, separada do objetivo)

### Coeficientes IEEE 30-Bus (Lee 1985 / El-Keib 1994)

| Gen | cost_a   | cost_b | emit_alpha | emit_beta | emit_gamma |
|-----|----------|--------|------------|-----------|------------|
| B2  | 0.00375  | 2.00   | 0.04091    | -0.05554  | 0.06490    |
| B5  | 0.01750  | 1.75   | 0.02543    | -0.06047  | 0.05638    |
| B8  | 0.06250  | 1.00   | 0.04258    | -0.05094  | 0.04586    |
| B11 | 0.00834  | 3.25   | 0.05326    | -0.03550  | 0.03970    |
| B13 | 0.02500  | 3.00   | 0.04716    | -0.05940  | 0.05660    |

### Parâmetros do GA (ieee30.py)

- pop=40, gen=20, parents=20, mutation=20%
- Ambos os runs estagnaram em torno da geração 17–18 → candidato a aumentar `num_generations`

### Último resultado (run_2026-05-02_19-50-52.csv)

- fitness final: 0.744 (vs 0.601 com Vref=1.0 — melhora de +23.7%)
- voltage_deviation: 0.158 pu (vs 1.097 pu anterior — queda de 86%)
- Despacho mais econômico: B8 caiu de 98% → 62% do máximo

## Próximas Etapas (PF2)

1. **Etapa 1 concluída.** Possível melhoria: aumentar `num_generations` para reduzir estagnação prematura.
2. **Etapa 2** — Integração de geração renovável via LoadShape profiles no OpenDSS.
3. **Etapa 3** — Escalabilidade + frente de Pareto com pymoo/NSGA-II (funções objetivo já isoladas em `objective_functions.py` — zero mudanças necessárias lá).

## Decisões Técnicas Importantes

- **Vref por barra** (não 1.0 pu): o IEEE 30-bus opera naturalmente acima de 1.0 pu (slack B1=1.06, B11~1.08). Referência uniforme distorcia f2 e causava over-despacho de B8.
- **voltage_penalty_weight=100.0**: recalibrado para a escala normalizada de F ∈ [0,2]. O valor original 10.000 era para escala de losses_kw.
- **w_emissions=0**: desativa emissões sem alterar código — basta mudar o peso em `ieee30.py`.
- **Genes em kW**: conversão kW→MW feita dentro das funções objetivo (`p_mw = gen["kw"] / 1000.0`).
