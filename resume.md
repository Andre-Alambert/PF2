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
main.py                        ← Entrypoint: monta o GA e executa
config.py                      ← Dicionário CONFIG central (caminhos, limites, parâmetros)
test.py                        ← Script de teste manual com soluções fixas

genetic_algorithm/
  encoding.py                  ← decode_solution (vetor → dict) e get_gene_space
  runner.py                    ← build_ga_instance, on_generation callback, run_ga

fitness/
  fitness_function.py          ← fitness_function(ga, sol, idx): avalia e retorna fitness
  evaluation.py                ← evaluate_solution: aplica no DSS e coleta métricas
  penalties.py                 ← voltage_penalty (quadrática) e convergence_penalty
  objective_functions.py       ← Stubs (ainda não implementados)

opendss/
  opendss_interface.py         ← Abstração OpenDSS: create, compile, apply, solve, leitura
```

---

## Fluxo de execução (`main.py`)

```
main()
  │
  ├─ get_gene_space(CONFIG)         → define limites de P_g e V_g para o PyGAD
  │
  ├─ build_ga_instance(...)         → cria instância pygad.GA (pop=6, ger=5, mut=50%)
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
            │
            └─ Se convergiu:
                  total_cost = losses_kw + 10000 × voltage_penalty(voltages)
                  fitness = 1 / (1 + total_cost)
```

---

## O que já foi feito

1. **Estrutura do projeto** — organização modular em pacotes (`fitness`, `genetic_algorithm`, `opendss`) com `__init__.py` em cada um.
2. **Interface OpenDSS** — funções para criar instância DSS, compilar circuito, editar gerador/fonte, resolver fluxo de potência e ler tensões/perdas.
3. **Codificação do AG** — mapeamento vetor ↔ variáveis físicas (`encoding.py`).
4. **Função de fitness completa** — avaliação via simulação, penalização quadrática de tensão e penalização de não-convergência.
5. **Runner do GA** — montagem e execução do PyGAD com callback de geração.
6. **Modificação do circuito IEEE 4-Bus** — inclusão do gerador G1 para ser otimizado.
7. **Script de teste** (`test.py`) — avaliação de soluções fixas para validar o pipeline.
8. **Correção de imports** — todos padronizados em caminho absoluto (`from src...`).
9. **Correção de bug do PyGAD** — `on_generation` e `run_ga` adaptados para usar `last_generation_fitness` em vez de `best_solution()` (que falhava com `IndexError`).

---

## O que ainda não foi feito / pendente

- `objective_functions.py` — funções `objective_losses` e `objective_voltage_deviation` estão como stubs (`pass`), não são usadas no fluxo atual.
- Pasta `results/` está vazia — sem salvamento de resultados em arquivo.
- Parâmetros do GA estão em modo de validação rápida (pop=6, ger=5); precisam ser escalados para otimização real.
- Não há multi-objetivo formal (ex.: NSGA-II); a fitness atual é mono-objetivo com penalização.
- Não há exportação de gráficos, logs estruturados ou análise pós-otimização.
