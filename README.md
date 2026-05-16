# PF2 — Otimização de Fluxo de Potência Multiobjetivo via NSGA-II

Projeto de Formatura 2 (PEA 3500) — Engenharia Elétrica, Escola Politécnica da USP.

**Tema:** Estudo da performance de algoritmos meta-heurísticos na resolução do Fluxo de Potência Ótimo (FPO) multiobjetivo com inserção de geração renovável.

**Aluno:** André Lima Alambert | **Orientador:** Prof. Silvio Giuseppe Di Santo

---

## Visão Geral

O projeto resolve um **Optimal Power Flow (OPF) multiobjetivo** no circuito IEEE 30-Bus com 5 geradores térmicos controláveis e 1 gerador eólico não-despachável. O otimizador é o **NSGA-II** (pymoo), que retorna uma **frente de Pareto completa** — um conjunto de soluções não-dominadas que representam os trade-offs reais entre os três objetivos — em vez de uma única solução escalar. O motor de simulação é o **OpenDSS** (py-dss-interface).

---

## Evolução do Projeto

### Relatório Parcial I — Pipeline mono-objetivo + calibração de hiperparâmetros

A primeira entrega do PF2 implementou e validou o pipeline **AG (PyGAD) + OpenDSS** com formulação mono-objetivo simplificada: minimizar perdas ativas penalizando desvios de tensão em uma única métrica escalar. O objetivo era validar a integração ponta a ponta antes de adicionar complexidade.

A calibração sistemática de hiperparâmetros foi conduzida por busca em grade (12 configurações × 3 seeds = 36 execuções), com análise de fronteira de Pareto entre qualidade de solução e tempo computacional. A configuração `pop=40, gen=20, mut=20%` foi selecionada como referência.

**Limitações identificadas:** sem função de custo de geração, o AG convergiu para injeção máxima em todos os geradores (comportamento fisicamente coerente, mas economicamente inútil). A formulação mono-objetivo também não captura os trade-offs reais entre custo, tensão e emissões.

### Estado Atual — NSGA-II multiobjetivo com geração eólica

Todas as etapas planejadas no Relatório Parcial I foram implementadas:

| Etapa | Status | Descrição |
|-------|--------|-----------|
| Função de custo de geração | ✅ Concluído | Curvas quadráticas por gerador (Lee/El-Keib 1985) |
| Formulação multiobjetivo (3 objetivos) | ✅ Concluído | NSGA-II com frente de Pareto completa |
| Integração de geração renovável | ✅ Concluído | Gerador eólico Wind_B30 com LoadShape por hora |
| PyGAD → NSGA-II | ✅ Concluído | Substituição integral; pymoo 0.6.1.6 |
| Calibração de hiperparâmetros (NSGA-II) | ✅ Concluído | Varredura 24 configs × 3 seeds; métrica: hipervolume |
| Comparação de cenários eólicos | ✅ Concluído | Sobreposição das frentes hora 8 / 12 / 18 num único gráfico |

---

## Formulação do OPF Multiobjetivo

Três objetivos **independentes** — sem agregação por pesos:

| Objetivo | Fórmula | Referência |
|----------|---------|-----------|
| **f1** — Custo de geração [$/h] | `Σ (a·Pg² + b·Pg + c)` | Lee/El-Keib 1985 |
| **f2** — Desvio de tensão [pu] | `Σ |V_i - V_ref_i|` | Referência **por barra** via fluxo base |
| **f3** — Emissões [ton/h] | `Σ (α·Pg² + β·Pg + γ)` | El-Keib 1994 |

**Restrição dura** via constraint do pymoo (`n_ieq_constr=1`):

```
g = Σ max(0, 0.95 − V)² + max(0, V − 1.10)²   (g ≤ 0 = factível)
```

Soluções infactíveis são excluídas do ranqueamento de Pareto pelo NSGA-II — sem penalidade ad-hoc na função objetivo.

> **Por que referência por barra?** O IEEE 30-Bus opera naturalmente acima de 1,0 pu (slack B1 = 1,06 pu). Usar 1,0 pu uniforme distorcia f2 penalizando tensões eletricamente corretas.

### Coeficientes dos geradores (IEEE 30-Bus)

| Gen | Barra | Pg min–max (MW) | cost\_a | cost\_b | emit\_α | emit\_β | emit\_γ |
|-----|-------|-----------------|---------|---------|---------|---------|---------|
| G1  | B2    | 0 – 80          | 0.00375 | 2.00    | 0.04091 | −0.05554 | 0.06490 |
| G2  | B5    | 0 – 50          | 0.01750 | 1.75    | 0.02543 | −0.06047 | 0.05638 |
| G3  | B8    | 0 – 35          | 0.06250 | 1.00    | 0.04258 | −0.05094 | 0.04586 |
| G4  | B11   | 0 – 30          | 0.00834 | 3.25    | 0.05326 | −0.03550 | 0.03970 |
| G5  | B13   | 0 – 40          | 0.02500 | 3.00    | 0.04716 | −0.05940 | 0.05660 |

---

## Geração Eólica

Gerador `Wind_B30` em B30 (33 kV), Pmax = 20 MW, **não-despachável**: a potência é fixada antes da otimização conforme o cenário de hora.

```
kW_vento = wind_loadshape[hora] × kw_max
```

O NSGA-II otimiza apenas os 5 térmicos; cada cenário eólico produz uma frente de Pareto diferente.

| Cenário | Hora | Fator de capacidade | Potência eólica |
|---------|------|---------------------|-----------------|
| Vento fraco  | `--hour 8`  | 18% | ~3,6 MW |
| Vento médio  | `--hour 12` | 45% | ~9,0 MW |
| Vento forte  | `--hour 18` | 68% | ~13,6 MW |

---

## Resultados

### Frente de Pareto — hora 18 (13,6 MW eólico)

40 soluções não-dominadas. Extremos da frente:

| Métrica | Mínimo na frente |
|---------|------------------|
| Custo de geração | 103,8 $/h |
| Desvio de tensão | 0,073 pu |
| Emissões | 19,7 ton/h |

### Comparação com formulação anterior (PyGAD mono-objetivo)

| Formulação | Custo ($/h) | Vdev (pu) | Emissões (ton/h) |
|------------|-------------|-----------|------------------|
| PyGAD escalar (Relatório I) | 178,6 | 0,372 | 58,9 |
| NSGA-II (melhor de cada objetivo) | **103,8** | **0,073** | **19,7** |

---

## Como Usar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

> **Windows:** o `py-dss-interface` localiza o OpenDSS automaticamente se instalado no sistema. Baixe o instalador oficial em [opendsscmd.com](https://www.opendsscmd.com/).

### 2. Rodar o NSGA-II

```bash
python -m src.nsga2 ieee30
```

Com cenário eólico por hora (0–23):

```bash
python -m src.nsga2 ieee30 --hour 18
```

O script:
1. Compila o circuito no OpenDSS e adiciona o gerador eólico
2. Resolve o fluxo base e calcula as referências de tensão por barra
3. Executa o NSGA-II (pop=40, gen=40, SBX + PM)
4. Imprime a frente de Pareto completa (tabela com f1, f2, f3 por solução)
5. Salva CSV e gráfico em `results/30bus/`

### 3. Saída

```
results/30bus/
  pareto_nsga2_ieee30_<timestamp>.csv   # Frente de Pareto com genes e objetivos
  pareto_nsga2_ieee30_<timestamp>.png   # Dois painéis 2D da frente de Pareto
```

O gráfico mostra:
- **Esquerda:** custo × emissões, colorido por desvio de tensão
- **Direita:** custo × desvio de tensão, colorido por emissões

---

## Parâmetros do NSGA-II

Configurados em `src/circuits/ieee30.py`:

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `population_size` | 40 | Indivíduos por geração |
| `num_generations` | 40 | Gerações totais |
| Crossover | SBX (prob=0.9, η=15) | Simulated Binary Crossover |
| Mutação | PM (prob=1/n\_var, η=20) | Polynomial Mutation |

---

## Calibração de Hiperparâmetros (NSGA-II)

Implementada em `src/run_experiment_nsga2.py`. A varredura cobre 24 configurações (3 pop × 2 gen × 2 sbx_η × 2 pm_η) com 3 seeds cada, totalizando 72 rodadas. A métrica é o **hipervolume** da frente de Pareto (`pymoo.indicators.hv.HV`), que mede o volume do espaço dominado — quanto maior, melhor.

**Grade de parâmetros:**

| Parâmetro | Valores testados |
|-----------|-----------------|
| `pop_size` | 20, 40, 80 |
| `num_gen` | 20, 40 |
| `sbx_eta` (η crossover SBX) | 10, 20 |
| `pm_eta` (η mutação PM) | 10, 20 |

**Ponto de referência HV:** `[f1_max × 1,05, f2_max × 1,05, f3_max × 1,05]` a partir dos bounds analíticos.

Para cada configuração o experimento reporta hipervolume mediano ± desvio padrão e tempo mediano de execução, e ao final salva um CSV e um gráfico de barras ranqueado.

### Como rodar o experimento

```bash
python -m src.run_experiment_nsga2 ieee30 --hour 18
```

Saída em `results/30bus/`:

```
experiment_nsga2_ieee30_<timestamp>.csv   # HV mediano/std por configuração
experiment_nsga2_ieee30_<timestamp>.png   # Ranking visual por hipervolume
```

---

## Estrutura do Projeto

```
src/
  nsga2.py                      # Entrypoint principal
  run_experiment_nsga2.py       # Varredura de hiperparâmetros (HV como métrica)
  compare_wind_scenarios.py     # Comparação de cenários eólicos (hora 8 / 12 / 18)
  configs.py                    # Registry de circuitos disponíveis
  circuits/
    ieee30.py                   # Configuração IEEE 30-Bus (caso principal)
    4bus.py                     # Configuração 4-Bus (secundário)
  fitness/
    evaluation.py               # Executa o fluxo e decodifica a solução
    objective_functions.py      # f1, f2, f3 + normalização + bounds analíticos
    penalties.py                # Penalidade de violação de tensão (restrição dura)
  genetic_algorithm/
    encoding.py                 # Gene space e decodificação da solução
    nsga2_runner.py             # OPFProblem (pymoo) + run_nsga2 (aceita overrides)
  opendss/
    opendss_interface.py        # Interface com OpenDSS + funções de vento
  results/
    plotting.py                 # Convergência e perfil de tensão
    pareto.py                   # plot_pareto_nsga2 + plot_hypervolume_pareto + plot_wind_scenario_comparison
data/IEEETestCases/             # Arquivos .dss dos circuitos
results/30bus/                  # CSVs e gráficos das rodadas IEEE 30-Bus
reports/                        # Relatórios parciais (PF1 e PF2)
```

---

## Comparação de Cenários Eólicos

Implementada em `src/compare_wind_scenarios.py`. Roda o NSGA-II de forma independente para cada hora especificada (padrão: 8, 12 e 18), com v_refs recalculados por cenário, e sobrepõe as frentes de Pareto num único gráfico para visualizar o impacto da geração eólica nos três objetivos.

```bash
python -m src.compare_wind_scenarios ieee30
```

Com horas customizadas:

```bash
python -m src.compare_wind_scenarios ieee30 --hours 8 12 18
```

Saída em `results/30bus/`:

```
wind_comparison_ieee30_<timestamp>.csv   # Frentes de todos os cenários combinadas
wind_comparison_ieee30_<timestamp>.png   # Gráfico com sobreposição (f1×f3 e f1×f2)
```

---

## Próximos Passos

1. **Escalabilidade:** avaliar performance em redes maiores (mais barras e variáveis de controle).
