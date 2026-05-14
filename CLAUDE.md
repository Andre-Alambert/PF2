# PF2 — Otimização de Fluxo de Potência via Algoritmo Genético

## Visão Geral

Projeto de Formatura 2 (PF2) de engenharia elétrica. Resolve um Optimal Power Flow (OPF) multiobjetivo usando **NSGA-II** (pymoo) com simulação de fluxo via OpenDSS (py_dss_interface). Caso principal: IEEE 30-Bus com 5 geradores controláveis e 1 gerador eólico (B30).

## Arquitetura

```
src/
  circuits/               # Configs por circuito
    ieee30.py             #   IEEE 30-Bus (caso principal)
    4bus.py               #   4-Bus (secundário)
  configs.py              # Registry de circuitos disponíveis
  nsga2.py                # Entrypoint: python -m src.nsga2 ieee30 [--hour H]
  fitness/
    evaluation.py         # Executa o fluxo e decodifica a solução
    objective_functions.py # f1, f2, f3 + normalização + bounds
    penalties.py          # Penalidade de violação de tensão (restrição dura)
  genetic_algorithm/
    encoding.py           # Gene space e decodificação da solução
    nsga2_runner.py       # OPFProblem (pymoo) + run_nsga2
  opendss/
    opendss_interface.py  # Interface com OpenDSS
  results/
    plotting.py           # Convergência e perfil de tensão
    pareto.py             # plot_pareto_nsga2: frente de Pareto 2D (f1×f3, f1×f2)
data/IEEETestCases/       # Arquivos .dss dos circuitos
results/30bus/            # CSVs e gráficos das rodadas IEEE 30-Bus
```

## Estado Atual — Etapas 1 e 2 concluídas

### Formulação NSGA-II

Três objetivos independentes — sem agregação por pesos:

- **f1** = custo de geração [$/h] — curvas quadráticas Lee/El-Keib 1985
- **f2** = desvio de tensão [pu] — referência **por barra** via fluxo base
- **f3** = emissões [ton/h] — coeficientes El-Keib 1994

Restrição dura via constraint do pymoo (`n_ieq_constr=1`):

```
g = Σ max(0, 0.95 - V)² + max(0, V - 1.10)²   (g ≤ 0 = factível)
```

O NSGA-II retorna a **frente de Pareto completa** em uma rodada — sem necessidade de pesos.

### Geração Eólica (Etapa 2)

Gerador Wind_B30 em B30 (33 kV), Pmax = 20 MW, não-despachável:

```
kW_vento = wind_loadshape[hora] × kw_max
```

Cenários: `--hour 8` (vento fraco 18%), `--hour 12` (médio 45%), `--hour 18` (forte 68%).

### Coeficientes IEEE 30-Bus (Lee 1985 / El-Keib 1994)

| Gen | cost_a   | cost_b | emit_alpha | emit_beta | emit_gamma |
|-----|----------|--------|------------|-----------|------------|
| B2  | 0.00375  | 2.00   | 0.04091    | -0.05554  | 0.06490    |
| B5  | 0.01750  | 1.75   | 0.02543    | -0.06047  | 0.05638    |
| B8  | 0.06250  | 1.00   | 0.04258    | -0.05094  | 0.04586    |
| B11 | 0.00834  | 3.25   | 0.05326    | -0.03550  | 0.03970    |
| B13 | 0.02500  | 3.00   | 0.04716    | -0.05940  | 0.05660    |

### Parâmetros do NSGA-II (ieee30.py)

- pop=40, gen=40, crossover=SBX(prob=0.9, eta=15), mutation=PM(prob=1/n_var, eta=20)
- Converge bem até gen 40 — sem estagnação prematura (diferença chave vs pygad)

### Último resultado (hora 18, 13.6 MW vento)

- 40 soluções não-dominadas na frente de Pareto
- Custo mínimo: 103.8 $/h | Vdev mínimo: 0.073 pu | Emissões mínimas: 19.7 ton/h
- vs pygad (melhor escalar): custo=178.6 $/h, vdev=0.372 pu, emit=58.9 ton/h

## Como Rodar

```bash
python -m src.nsga2 ieee30 --hour 18
```

Salva CSV com a frente de Pareto e gráfico em `results/30bus/`.

## Próximas Etapas

1. **Tuning de hiperparâmetros do NSGA-II** — reimplementar `run_experiment` para NSGA-II.
   - Métrica: **hipervolume** (substitui "melhor fitness" do pygad — mede o volume do espaço dominado pela frente de Pareto; quanto maior, melhor).
   - Estrutura: varrer combinações de `pop_size`, `num_generations`, `crossover eta`, `mutation eta`; para cada configuração rodar N vezes e reportar hipervolume mediano ± std.
   - Referência: `pymoo.indicators.hv.HV` com ponto de referência = [f1_max, f2_max, f3_max] dos bounds analíticos.

2. **Comparação de cenários eólicos** — rodar NSGA-II para hora 8, 12 e 18 e sobrepor as frentes de Pareto num único gráfico para mostrar o impacto do vento.

3. **Escalabilidade** — avaliar performance em redes maiores.

## Decisões Técnicas Importantes

- **Vref por barra** (não 1.0 pu): o IEEE 30-bus opera naturalmente acima de 1.0 pu. Referência uniforme distorcia f2.
- **Restrição de tensão como constraint** (não penalidade na fitness): pymoo exclui soluções infactíveis do ranqueamento de Pareto; mais limpo que penalidade ad-hoc.
- **Vento não-despachável**: kW fixo por cenário, o NSGA-II otimiza só os 5 térmicos — cada cenário de vento produz uma frente de Pareto diferente.
- **Genes em kW**: conversão kW→MW feita dentro das funções objetivo.
- **pygad removido**: substituído integralmente pelo NSGA-II. Os arquivos `runner.py`, `fitness_function.py`, `logger.py`, `run_experiment.py`, `grid_search.py` foram deletados.
