# PF2 — Otimização de Fluxo de Potência (OPF) via Algoritmo Genético

Projeto de Formatura 2 de engenharia elétrica. Resolve um **Optimal Power Flow (OPF)** usando um Algoritmo Genético ([pygad](https://pygad.readthedocs.io/)) com simulação de fluxo via OpenDSS ([py-dss-interface](https://py-dss-interface.readthedocs.io/)). Caso principal: **IEEE 30-Bus** com 5 geradores controláveis.

---

## Estrutura do projeto

```
src/
  main.py              # Entrypoint: uma rodada do GA
  run_experiment.py    # Entrypoint: grid search de hiperparâmetros
  configs.py           # Registry de circuitos disponíveis
  circuits/            # Configurações por circuito
    ieee30.py          #   Caso IEEE 30-Bus (principal)
    4bus.py            #   Caso 4-Bus (secundário)
  fitness/
    fitness_function.py    # Factory do fitness (closure com DSS e bounds)
    objective_functions.py # f1 (custo), f2 (tensão), f3 (emissões) + normalização
    evaluation.py          # Executa o fluxo e decodifica a solução
    penalties.py           # Penalidade de violação de tensão (restrição dura)
  genetic_algorithm/
    encoding.py        # Gene space e decodificação da solução
    runner.py          # Build e execução do pygad
  opendss/
    opendss_interface.py  # Abstração de comunicação com o OpenDSS
  results/
    logger.py          # Salva histórico e CSV por run
    plotting.py        # Gráficos de convergência e perfil de tensão
    pareto.py          # Plot da frente de Pareto (grid search)
  experiments/
    grid_search.py     # Varredura de hiperparâmetros do GA
data/IEEETestCases/    # Arquivos .dss dos circuitos
results/
  30bus/               # CSVs e gráficos das rodadas IEEE 30-Bus
  4bus/                # CSVs e gráficos das rodadas 4-Bus
```

---

## Como usar

### 1. Instalar dependências

```bash
python -m pip install -r requirements.txt
```

> **Windows**: o `py-dss-interface` localiza o OpenDSS automaticamente se ele estiver instalado no sistema. Baixe o instalador oficial em [opendsscmd.com](https://www.opendsscmd.com/).

### 2. Rodar a otimização (uma rodada)

```bash
python -m src.main ieee30
```

Ou para o caso 4-Bus:

```bash
python -m src.main 4bus
```

O script executa o GA, salva os resultados em `results/30bus/` (CSV + gráfico de convergência + perfil de tensão) e imprime o melhor despacho encontrado.

### 3. Grid search de hiperparâmetros (opcional)

```bash
python -m src.run_experiment ieee30
```

Varre combinações de `population_size`, `num_generations` e `mutation_percent_genes`, agrega métricas (fitness mediano, desvio-padrão, geração de convergência, tempo) e gera um gráfico de Pareto em `results/30bus/`.

---

## Como funciona

1. O GA gera candidatos de despacho ativo `P_g` (kW) para cada gerador.
2. Cada candidato é aplicado no circuito OpenDSS (`Edit Generator`) e o fluxo de potência é resolvido.
3. A função de fitness é calculada como:

```
F = w_cost · f1' + w_voltage · f2' + w_emissions · f3'
fitness = 1 / (1 + F + pen_v)
```

| Componente | Significado |
|---|---|
| `f1` | Custo de geração [$/h] — curvas quadráticas (Lee 1985) |
| `f2` | Desvio de tensão [pu] — referência por barra via fluxo base |
| `f3` | Emissões [ton/h] — desativado por padrão (`w_emissions=0`) |
| `pen_v` | Penalidade por violação da faixa [0,95; 1,10] pu |

> A referência de tensão é calculada **por barra** via fluxo base (não 1,0 pu uniforme), pois o IEEE 30-Bus opera naturalmente acima de 1,0 pu (slack B1 = 1,06 pu).

---

## Personalização

Edite `src/circuits/ieee30.py` para ajustar:

- **Pesos dos objetivos** (`objective_weights`): altere `w_cost`, `w_voltage` ou `w_emissions`.
- **Limites de despacho** (`pg_min_kw`, `pg_max_kw` em cada gerador).
- **Parâmetros do GA** (`population_size`, `num_generations`, `num_parents_mating`, `mutation_percent_genes`).
- **Limites de tensão** (`voltage_lower_limit`, `voltage_upper_limit`).

Para adicionar um novo circuito, crie `src/circuits/meu_caso.py` seguindo a estrutura de `ieee30.py` e registre-o em `src/configs.py`.
