# Resumo do Projeto PF2

## Objetivo

Otimizar o ponto de operação de um sistema de distribuição elétrica usando **Algoritmo Genético (PyGAD)** acoplado ao simulador **OpenDSS (py-dss-interface)**.  
A meta é encontrar valores de **potência ativa do gerador (P_g)** e **tensão da fonte (V_g)** que minimizem as **perdas elétricas** mantendo as **tensões dentro dos limites** (0.95–1.05 pu).

---

## Circuito utilizado

- **Caso base:** IEEE 4-Bus Y-Y Balanced (`4Bus-YY-Bal-Modified.DSS`).
- Modificação feita: adição de um **gerador trifásico G1** na barra `n4` (4.16 kV, kW variável, pf=1) para ser controlado pelo AG.
- Carga original: 5400 kW, pf=0.9, modelo de potência constante.
- Transformador: 12.47/4.16 kV, Y-Y, 6 MVA.

---

## Variáveis de decisão (genes)

| Gene | Descrição                  | Faixa           |
|------|----------------------------|-----------------|
| P_g  | Potência do gerador (kW)  | 0 – 1500        |
| V_g  | Tensão da fonte (pu)      | 0.95 – 1.05     |

---

## Estrutura do código (`src/`)

```
main.py                        ← Entrypoint: monta o GA, executa, salva CSV e gráficos
run_experiment.py              ← Entrypoint do experimento de hiperparâmetros
config.py                      ← Dicionário CONFIG central (caminhos, limites, parâmetros)
test.py                        ← Script de teste manual com soluções fixas

genetic_algorithm/
  encoding.py                  ← decode_solution (vetor → dict) e get_gene_space
  runner.py                    ← build_ga_instance (usa CONFIG), on_generation, run_ga

fitness/
  fitness_function.py          ← fitness_function + cache de métricas + flag verbose
  evaluation.py                ← evaluate_solution: aplica no DSS e coleta métricas
  penalties.py                 ← voltage_penalty (quadrática) e convergence_penalty
  objective_functions.py       ← Stubs (não usados ainda)

opendss/
  opendss_interface.py         ← Abstração OpenDSS: create, compile, apply, solve, leitura

results/
  logger.py                    ← RunLogger: acumula métricas por geração, exporta CSV
  plotting.py                  ← plot_convergence e plot_voltage_profile (backend Agg)
  pareto.py                    ← compute_pareto_front e plot_pareto (scatter + ranking)

experiments/
  grid_search.py               ← Grid search de hiperparâmetros com múltiplas seeds
```

---

## Fluxo de execução (`main.py`)

```
main()
  │
  ├─ RunLogger(results/)            → prepara logger com timestamp
  ├─ get_gene_space(CONFIG)         → define limites de P_g e V_g
  ├─ build_ga_instance(logger=...)  → cria pygad.GA com CONFIG e callback logado
  │
  └─ run_ga(ga_instance)            → executa o loop evolutivo
       │
       └─ Para cada indivíduo → fitness_function()
            │
            ├─ evaluate_solution(dss, sol, CONFIG)
            │     ├─ decode_solution(sol)        → {P_g, V_g}
            │     ├─ apply_solution(dss, ...)    → edita Generator.G1 e Vsource.source
            │     ├─ solve_power_flow(dss)       → roda o fluxo de potência
            │     └─ coleta: losses_kw, voltages_pu, v_min, v_max, converged
            │
            ├─ Se não convergiu → convergence_penalty (1e6) → fitness ≈ 0
            └─ Se convergiu:
                  total_cost = losses_kw + 10000 × voltage_penalty(voltages)
                  fitness = 1 / (1 + total_cost)
       │
       └─ on_generation callback    → loga métricas via RunLogger
  │
  ├─ logger.save_csv()              → results/run_<timestamp>.csv
  ├─ plot_convergence(...)          → results/convergence_<timestamp>.png
  └─ plot_voltage_profile(...)      → results/voltage_profile_<timestamp>.png
```

## Fluxo do experimento de hiperparâmetros (`run_experiment.py`)

```
run_all_experiments()
  │
  ├─ Grid: pop ∈ {10,20,40} × gen ∈ {10,20} × mut ∈ {20%,50%} = 12 configs
  ├─ Seeds: [42, 7, 99]  →  36 corridas no total
  │
  └─ Para cada (config, seed):
       _run_single() → GA completo → {best_fitness, conv_gen, elapsed_sec}
  │
  ├─ experiment_raw_<timestamp>.csv    ← 36 linhas (uma por corrida)
  ├─ experiment_agg_<timestamp>.csv    ← 12 linhas (mediana das seeds por config)
  └─ plot_pareto(agg_rows)             ← pareto_<timestamp>.png
       ├─ Scatter: fitness mediano × tempo  (★ = Pareto-ótimo)
       └─ Ranking horizontal por fitness mediano
```

---

## O que já foi feito

1. **Estrutura do projeto** — organização modular em pacotes com `__init__.py` em cada um.
2. **Interface OpenDSS** — funções para criar instância DSS, compilar circuito, editar gerador/fonte, resolver fluxo de potência e ler tensões/perdas.
3. **Codificação do AG** — mapeamento vetor ↔ variáveis físicas (`encoding.py`).
4. **Função de fitness completa** — avaliação via simulação, penalização quadrática de tensão e penalização de não-convergência.
5. **Runner do GA** — `build_ga_instance` usa os valores de `CONFIG` em vez de hardcoded; callback logado via `RunLogger`.
6. **Modificação do circuito IEEE 4-Bus** — inclusão do gerador G1 para ser otimizado.
7. **Script de teste** (`test.py`) — avaliação de soluções fixas para validar o pipeline.
8. **Correção de imports** — todos padronizados em caminho absoluto (`from src...`) com bootstrap de `sys.path`.
9. **Correção de bug do PyGAD** — `on_generation` e `run_ga` adaptados para usar `last_generation_fitness`.
10. **Logger de corridas** (`results/logger.py`) — `RunLogger` acumula métricas por geração e exporta CSV com timestamp.
11. **Gráfico de convergência** (`results/plotting.py`) — curva fitness × geração com eixo secundário de perdas (kW).
12. **Gráfico de perfil de tensão** (`results/plotting.py`) — barplot de tensão por barra com linhas de limite 0.95/1.05 pu.
13. **Cache de avaliações** (`fitness_function.py`) — `_eval_cache` expõe as últimas métricas por índice; `set_verbose` silencia prints durante experimentos.
14. **Experimento de hiperparâmetros** (`experiments/grid_search.py`) — grid search automático com múltiplas seeds, exporta CSV bruto e CSV agregado com medianas.
15. **Gráfico de Pareto** (`results/pareto.py`) — scatter qualidade × tempo com fronteira de Pareto destacada e ranking horizontal por configuração.

---

## Resultados do experimento de hiperparâmetros (4-Bus, 3 seeds)

| Rank | pop | gen | mut | Fitness mediano | Std    | Gen convergência | Tempo |
|------|-----|-----|-----|----------------|--------|-----------------|-------|
| #1   | 40  | 20  | 50% | 0.003106        | 2.8e-05 | 8               | 0.2s  |
| #2   | 20  | 20  | 50% | 0.003085        | 3.9e-05 | 13              | 0.1s  |
| #3   | 40  | 10  | 20% | 0.003076        | 2.4e-05 | 4               | 0.1s  |

**Conclusão:** `pop=40, gen=10, mut=20%` é o Pareto-ótimo de custo/benefício — converge na geração 4, menor std, tempo praticamente igual às configs menores. `pop=40, gen=20, mut=50%` dá a melhor qualidade absoluta a custo ainda trivial (~0.2s) neste circuito de 4 barras.

---

## O que ainda não foi feito / pendente

- `objective_functions.py` — stubs `objective_losses` e `objective_voltage_deviation` não são usados.
- Não há multi-objetivo formal (ex.: NSGA-II); fitness atual é mono-objetivo com penalização.
- Barra `n4` fica abaixo de 0.95 pu na melhor solução atual — indica que o peso de penalidade de tensão ou o espaço de busca precisam de ajuste para circuitos com mais carregamento.
- Sem critério de parada por estagnação (o GA sempre roda todas as gerações).
