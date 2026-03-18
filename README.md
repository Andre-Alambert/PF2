# PF2 - Otimização com OpenDSS + Algoritmo Genético

Este repositório contém um exemplo de otimização de controle de gerador (potência ativa) e fonte (tensão) em um circuito de distribuição elétrica usando **OpenDSS** e **Algoritmo Genético (pygad)**.

O objetivo principal é encontrar o ponto de operação que minimize perdas e mantenha as tensões dentro dos limites desejados.

---

## 🔧 Estrutura do projeto

- `data/` - casos de teste IEEE em formato OpenDSS (`.dss`) usados na simulação.
- `src/` - código-fonte do projeto:
  - `config.py` - configurações gerais (circuito, limites, parâmetros do GA, etc.)
  - `main.py` - entrypoint do programa (executa a otimização)
  - `test.py` - script simples para testar a avaliação de uma solução fixa
  - `opendss/` - abstração para comunicação com o OpenDSS
  - `fitness/` - função de fitness, cálculo de penalidades e avaliação de soluções
  - `genetic_algorithm/` - geração e execução do GA via `pygad`
- `requirements.txt` - dependências do projeto.

---

## ✅ Como usar

### 1) Instalar dependências

```bash
python -m pip install -r requirements.txt
```

> ⚠️ Este projeto usa o OpenDSS por meio do `py-dss-interface`. Certifique-se de ter o OpenDSS instalado no sistema (normalmente basta instalar o pacote oficial do OpenDSS). Em Windows, o `py-dss-interface` costuma encontrar o OpenDSS automaticamente.

### 2) Configurar o circuito e parâmetros

Edite `src/config.py` para apontar para o seu arquivo `.dss` (padrão: `data/IEEETestCases/4Bus-YY-Bal/4Bus-YY-Bal.dss`) e ajuste limites / parâmetros do GA.

### 3) Rodar a otimização

```bash
python -m src.main
```

Isso executa o algoritmo genético e imprime a melhor solução encontrada (valores de `P_g` e `V_g`), além da fitness.

### 4) Testar uma solução fixa (opcional)

```bash
python -m src.test
```

O `src/test.py` avalia uma solução fixa (`[500, 1.0]`) e imprime métricas como convergência, perdas e tensões.

---

## 🧠 Como funciona

1. O GA gera candidatos (`P_g`, `V_g`).
2. Cada candidato é aplicado no circuito OpenDSS (`Edit Generator`, `Edit Vsource`).
3. Executa-se fluxo de potência e mede-se perdas + tensões.
4. A função de fitness penaliza:
   - circuitos que não convergem
   - tensões fora da faixa especificada
   - perdas totais

---

## 📌 Personalização

- Para usar outro caso de teste OpenDSS, altere `CONFIG["circuit_path"]` em `src/config.py`.
- Ajuste os limites de `pg_min_kw`, `pg_max_kw`, `vg_min_pu`, `vg_max_pu` e os limites de tensão.
- Os parâmetros do GA (população, gerações, etc.) também estão em `src/config.py`.

---

## 📎 Observações

- Este projeto é um ponto de partida; para um estudo mais profundo, considere:
  - adicionar mais variáveis de decisão (tap changers, cargas, etc.)
  - usar múltiplos cenários de carga
  - salvar resultados / histórico do GA
