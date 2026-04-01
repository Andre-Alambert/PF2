# Projeto — AG para FPO Multiobjetivo com Renováveis
## Visão Geral

O objetivo geral do projeto é analisar a **performance do Algoritmo Genético (AG) na resolução do Fluxo de Potência Ótimo (FPO) multiobjetivo** em sistemas de distribuição com geração renovável.

---

## Onde estávamos antes deste repositório

- O simulador de fluxo de potência havia sido escolhido e validado: **OpenDSS via `py-dss-interface`**.
- Ainda não havia nada definido sobre o AG: nenhuma codificação, nenhuma função objetivo, nenhum experimento.

---

## O que foi construído neste repositório

### 1. Prova de conceito end-to-end
Construção de um pipeline completo de otimização: o AG recebe candidatos, o OpenDSS simula o fluxo de potência, e uma função de fitness avalia a qualidade elétrica de cada solução. O circuito usado foi o **IEEE 4-Bus** com um gerador adicionado para ser controlado.

### 2. Formulação mono-objetivo simplificada
As duas variáveis de controle escolhidas foram **potência ativa do gerador (P_g)** e **tensão da fonte (V_g)**. A função de fitness penaliza perdas e violações de tensão em uma única métrica escalar — uma simplificação deliberada para validar o pipeline antes de avançar para múltiplos objetivos.

### 3. Infraestrutura de análise
Toda a maquinaria necessária para analisar resultados foi implementada:
- Exportação automática de CSV e gráficos de convergência e perfil de tensão a cada corrida.
- Experimento automatizado de hiperparâmetros: grid search com múltiplas seeds, CSV agregado com medianas e gráfico de fronteira de Pareto (qualidade × tempo computacional).

### 4. Primeiro resultado de calibração
Com o circuito simples de 4 barras, o melhor custo/benefício identificado foi **pop=40, gen=10, mut=20%** — convergência rápida (geração 4), baixa variância entre seeds, tempo < 0.1s.

---

## Diretrizes de próximos passos

**1. Expandir para FPO multiobjetivo real**
Implementar múltiplos objetivos simultaneamente — minimizar perdas e minimizar desvio de tensão como objetivos separados, sem colapsar em um único escalar. Isso exige um algoritmo Pareto-based, tipicamente **NSGA-II**.

**2. Incluir geração renovável (PV/eólica)**
Conectar perfis de geração intermitente ao circuito (loadshapes no OpenDSS). O FPO passa a ser dependente do tempo, o que aumenta a complexidade e é o núcleo do objetivo geral do projeto.

**3. Escalar para circuito mais representativo**
Migrar do 4-Bus para o **IEEE 13-Bus ou 123-Bus** (já presentes em `data/`). Mais barras = mais variáveis de controle, espaço de busca maior, e resultados mais próximos de cenários reais.

**4. Métricas de performance do AG**
Definir formalmente o que significa "boa performance" do AG neste contexto: taxa de convergência, distância à fronteira de Pareto ótima, diversidade de soluções, robustez a variações de geração renovável.

**5. Comparação com outros métodos**
Para validar o AG, comparar com pelo menos um método de referência — por exemplo, otimização por enxame de partículas (PSO) ou um solver determinístico (scipy) no caso mono-objetivo.
