# ANDRÉ LIMA ALAMBERT

**Estudo da performance do algoritmo genético na resolução do Fluxo de Potência Ótimo multiobjetivo com inserção de renováveis.**

Relatório Parcial 1 da disciplina de Projeto de Formatura II, apresentado à Escola Politécnica da Universidade de São Paulo

Área de Concentração: Sistemas de Potência

Orientador: Prof. Dr. Silvio Giuseppe

São Paulo — 2026

---

## RESUMO

Este relatório parcial documenta a primeira etapa do Projeto de Formatura II, cujo objetivo central é analisar a performance do Algoritmo Genético (AG) na resolução do Fluxo de Potência Ótimo (FPO) multiobjetivo com inserção de geração renovável. Nesta etapa, foi implementado e validado o pipeline computacional que integra o AG ao simulador OpenDSS, utilizado como motor de cálculo do fluxo de potência. A implementação adota uma formulação mono-objetivo simplificada — combinando perdas ativas e penalização de desvios de tensão em uma única métrica escalar — com o propósito explícito de validar o pipeline de ponta a ponta antes de avançar para a formulação multiobjetivo. Em seguida, foi realizada uma calibração sistemática dos hiperparâmetros do AG por meio de busca em grade com análise de fronteira de Pareto entre qualidade de solução e tempo computacional. Os resultados confirmam a viabilidade técnica do pipeline e identificam a configuração de hiperparâmetros mais adequada para as próximas etapas.

**Palavras-Chave:** Fluxo de Potência Ótimo. Algoritmo Genético. Otimização. OpenDSS. Hiperparâmetros.

---

## 1 INTRODUÇÃO

O Projeto de Formatura I estabeleceu a base teórica e metodológica necessária para a resolução do problema do Fluxo de Potência Ótimo (FPO) multiobjetivo com inserção de fontes renováveis por meio do Algoritmo Genético (AG). Ao final do PF1, o ambiente de simulação com OpenDSS havia sido validado por meio de casos de teste IEEE, a modelagem da geração eólica fora desenvolvida e testada, e a arquitetura teórica de integração AG + OpenDSS havia sido definida — mas nenhum código de otimização havia sido implementado.

O presente relatório parcial documenta a **primeira etapa prática do PF2**: a implementação do pipeline computacional AG + OpenDSS e a calibração inicial de seus hiperparâmetros. A formulação utilizada neste estágio é deliberadamente simplificada — mono-objetivo e com poucas variáveis de controle — com o objetivo de validar o fluxo completo de otimização (codificação → avaliação → evolução → resultado) antes de introduzir a complexidade da otimização multiobjetivo, da geração renovável estocástica e de circuitos de maior porte.

O relatório está organizado da seguinte forma: a Seção 2 retoma brevemente os elementos do PF1 relevantes para este estágio; a Seção 3 descreve a implementação do pipeline; a Seção 4 apresenta a metodologia e os resultados da calibração de hiperparâmetros; a Seção 5 analisa os resultados obtidos; a Seção 6 detalha os próximos passos; e a Seção 7 apresenta a conclusão parcial.

---

## 2 RETOMADA DO PF1

Os elementos fundamentais estabelecidos no PF1 e diretamente utilizados nesta etapa são:

**Formulação do FPO adotada.** O problema é formulado como a minimização de funções objetivo (custo de geração, perdas e desvio de tensão) sujeita a restrições de igualdade (balanço de potência nas barras) e de desigualdade (limites de geração, tensão e fluxo nas linhas). O OpenDSS é responsável pela resolução das equações do fluxo de potência a cada avaliação, dispensando a implementação manual das equações BIM.

**Mapeamento das variáveis para o AG.** Conforme definido teoricamente no PF1, cada indivíduo da população do AG representa um vetor de variáveis de controle do sistema elétrico. Nesta etapa de prova de conceito, foram adotadas duas variáveis: a potência ativa do gerador $P_g$ (kW) e a tensão da fonte $V_g$ (pu).

**Motor de simulação.** O OpenDSS, controlado via a biblioteca Python `py-dss-interface`, atua como motor de cálculo do fluxo de potência: recebe os parâmetros do circuito, resolve as equações e retorna tensões, fluxos e perdas para a função de fitness.

**Circuito de referência.** O circuito IEEE 4-Bus-YY-Bal, já utilizado no PF1 para validações experimentais, foi estendido com um gerador distribuído controlável e adotado como caso de teste para o pipeline.

---

## 3 IMPLEMENTAÇÃO DO PIPELINE AG + OPENDSS

### 3.1 Arquitetura Geral

O pipeline implementado integra o AG, a interface Python do OpenDSS e uma camada de logging conforme a seguinte sequência de execução:

```
Inicialização
  ├── Compilar circuito no OpenDSS
  └── Inicializar população do AG

Para cada geração:
  └── Para cada candidato (P_g, V_g):
        ├── Aplicar (P_g, V_g) ao circuito via comandos Edit
        ├── Resolver fluxo de potência (OpenDSS)
        ├── Extrair métricas: perdas [kW], tensões [pu]
        └── Calcular fitness escalar
  └── Operadores genéticos: seleção → crossover → mutação
  └── Registrar geração: melhor fitness, solução, métricas

Saída
  ├── CSV por geração
  └── Gráficos: convergência e perfil de tensão
```

A instância do OpenDSS é criada uma única vez e compartilhada entre todas as avaliações da mesma execução do AG, evitando o custo de recompilação do circuito a cada chamada. A aplicação dos parâmetros se dá por comandos `Edit` enviados ao OpenDSS em tempo real:

```
Edit Generator.G1 kW={P_g}
Edit Vsource.source pu={V_g}
```

A biblioteca utilizada para o AG é a **PyGAD**, que fornece os operadores de seleção, crossover e mutação, e expõe um callback `on_generation` utilizado para o registro dos resultados por geração.

### 3.2 Codificação das Variáveis de Controle

O cromossomo de cada indivíduo é um vetor real de dois genes:

| Gene | Variável | Domínio |
|------|----------|---------|
| $g_1$ | $P_g$ — potência ativa do gerador | $[0,\ 1500]$ kW |
| $g_2$ | $V_g$ — tensão da fonte em valor por unidade | $[0{,}95,\ 1{,}05]$ pu |

A codificação em números reais foi adotada conforme indicado no PF1, evitando erros de arredondamento e acelerando a convergência em relação à codificação binária. Os limites de $P_g$ são compatíveis com a capacidade nominal do gerador inserido no circuito 4-Bus; os limites de $V_g$ correspondem à faixa operacional padrão de ±5% da tensão nominal.

### 3.3 Função de Fitness

O objetivo do FPO nesta etapa é **minimizar as perdas ativas** do sistema, respeitando limites de tensão nas barras. Como o PyGAD **maximiza** a função de fitness, adotou-se a inversão da função de custo penalizada:

$$\text{fitness}(x) = \frac{1}{1 + C(x)}$$

onde $C(x)$ é o custo total dado por:

$$C(x) = P_{\text{loss}}\ [\text{kW}]\ +\ w_v \cdot \sum_{i} \left[\max\!\left(0,\ V_{\min} - V_i\right)^2 + \max\!\left(0,\ V_i - V_{\max}\right)^2\right]$$

com os seguintes parâmetros:

| Parâmetro | Valor |
|-----------|-------|
| $V_{\min}$ | 0,95 pu |
| $V_{\max}$ | 1,05 pu |
| $w_v$ (peso da penalização de tensão) | 10.000 |
| Penalização por não convergência | $C(x) = 10^6$ |

O peso $w_v = 10.000$ foi escolhido para garantir que uma violação de tensão de 0,01 pu em uma única barra adicione 1 kW equivalente ao custo, tornando as restrições de tensão fortemente desencorajadas sem eliminar a busca em regiões próximas aos limites. Quando o fluxo de potência não converge, aplica-se diretamente $C(x) = 10^6$, assegurando que soluções inviáveis recebam fitness mínimo.

Esta formulação escalar é uma **prova de conceito**: consolida a arquitetura do pipeline, mas não representa a formulação multiobjetivo prevista para as etapas seguintes do PF2.

### 3.4 Interface AG ↔ OpenDSS

A avaliação de cada candidato envolve três passos executados sequencialmente pela função `evaluate_solution`:

1. **Decodificação:** o vetor de genes $[g_1, g_2]$ é mapeado diretamente para $\{P_g, V_g\}$ (sem decodificação binária, dado o uso de genes reais).
2. **Aplicação:** os valores são enviados ao OpenDSS via `Edit Generator.G1 kW={P_g}` e `Edit Vsource.source pu={V_g}`.
3. **Resolução e extração:** `dss.solution.solve()` é chamado; em seguida são extraídos perdas totais (`dss.circuit.losses`) e tensões em todas as barras (`dss.circuit.buses_vmag_pu`).

Um cache `_eval_cache` armazena as métricas de cada candidato avaliado na geração corrente, permitindo que o callback `on_generation` acesse as métricas do melhor indivíduo sem reavaliação.

### 3.5 Logging e Visualização

A cada geração, os seguintes dados são registrados em CSV:

| Campo | Descrição |
|-------|-----------|
| `generation` | Número da geração |
| `best_fitness` | Maior fitness da geração |
| `P_g` | Potência do gerador na melhor solução (kW) |
| `V_g` | Tensão da fonte na melhor solução (pu) |
| `losses_kw` | Perdas ativas totais (kW) |
| `v_min` / `v_max` | Tensão mínima e máxima entre as barras (pu) |
| `converged` | Indicador de convergência do fluxo de potência |

Ao término de cada execução, são gerados automaticamente: (i) gráfico de convergência do fitness ao longo das gerações e (ii) gráfico do perfil de tensão nas barras para a melhor solução encontrada.

---

## 4 CALIBRAÇÃO DOS HIPERPARÂMETROS DO AG

### 4.1 Metodologia

A calibração foi conduzida por meio de uma **busca em grade fatorial completa** sobre os seguintes hiperparâmetros:

| Hiperparâmetro | Valores testados |
|----------------|-----------------|
| Tamanho da população (`pop_size`) | 10, 20, 40 |
| Número de gerações (`num_gen`) | 10, 20 |
| Taxa de mutação (`mutation_pct`) | 20%, 50% |

A combinação de 3 × 2 × 2 = **12 configurações** foi executada com **3 sementes aleatórias fixas** (42, 7 e 99), totalizando **36 execuções independentes**. O uso de sementes fixas garante reprodutibilidade e permite avaliar a variância do AG frente à aleatoriedade intrínseca dos operadores de inicialização e genéticos.

Para cada execução foram registrados: fitness final (`best_fitness`), tempo de execução (`elapsed_sec`) e **geração de convergência** — definida como a primeira geração em que o fitness atingiu pelo menos 98% do fitness final da corrida.

Os resultados das 36 execuções foram agregados por configuração (mediana e desvio padrão do fitness entre seeds, mediana da geração de convergência e do tempo de execução), produzindo 12 linhas comparáveis.

### 4.2 Resultados Agregados

A Tabela 1 apresenta as 12 configurações ordenadas por fitness mediano decrescente.

**Tabela 1 — Resultados agregados da busca em grade (ordenado por fitness mediano)**

| `pop` | `gen` | `mut` (%) | Fitness mediano | Desvio padrão | Conv. (geração) | Tempo (s) |
|-------|-------|-----------|----------------|---------------|-----------------|-----------|
| 40    | 20    | 50        | 0,003106        | 2,84 × 10⁻⁵   | 8               | 0,233     |
| 20    | 20    | 50        | 0,003085        | 3,95 × 10⁻⁵   | 13              | 0,110     |
| 40    | 10    | 20        | 0,003076        | 2,35 × 10⁻⁵   | 4               | 0,122     |
| 10    | 20    | 20        | 0,003075        | 6,21 × 10⁻⁵   | 15              | 0,059     |
| 40    | 10    | 50        | 0,003069        | 4,78 × 10⁻⁵   | 7               | 0,119     |
| 40    | 20    | 20        | 0,003065        | 1,44 × 10⁻⁵   | 2               | 0,221     |
| 20    | 10    | 50        | 0,003045        | 5,25 × 10⁻⁵   | 8               | 0,054     |
| 20    | 20    | 20        | 0,003026        | 4,75 × 10⁻⁵   | 9               | 0,106     |
| 10    | 20    | 50        | 0,002999        | 1,11 × 10⁻⁴   | 15              | 0,091     |
| 20    | 10    | 20        | 0,002980        | 2,76 × 10⁻⁵   | 4               | 0,062     |
| 10    | 10    | 20        | 0,002963        | 5,75 × 10⁻⁵   | 4               | 0,031     |
| 10    | 10    | 50        | 0,002910        | 1,10 × 10⁻⁴   | 4               | 0,031     |

**Observações gerais:**
- A variação total de fitness entre a melhor e a pior configuração é de ~6,6% — uma faixa estreita, o que sugere que o problema de 2 variáveis é relativamente simples para o AG em qualquer configuração razoável.
- Configurações com populações maiores (`pop=40`) tendem a apresentar menor desvio padrão entre seeds, indicando maior robustez.
- Populações pequenas (`pop=10`) com alta mutação (`mut=50%`) apresentam os maiores desvios padrão (1,10 × 10⁻⁴), revelando instabilidade entre execuções.

### 4.3 Análise de Fronteira de Pareto: Qualidade × Tempo Computacional

Analisar apenas o fitness máximo para escolha de hiperparâmetros ignora o custo computacional da configuração — relevante dado que, nas próximas etapas, o circuito será maior e cada avaliação de fitness exigirá mais tempo de simulação. Para endereçar esse trade-off, foi computada a **fronteira de Pareto** sobre o espaço bidimensional (tempo, fitness), com os dois objetivos a minimizar sendo:

- $-\text{fitness mediano}$ (maximizar qualidade → minimizar negativo)
- $\text{tempo mediano de execução}$

Uma configuração é Pareto-ótima se nenhuma outra configuração alcança simultaneamente maior fitness e menor tempo. A análise identificou três configurações na fronteira:

| Configuração | Fitness mediano | Tempo (s) | Interpretação |
|---|---|---|---|
| `pop=10, gen=10, mut=20%` | 0,002963 | 0,031 | Melhor custo-benefício em tempo |
| `pop=10, gen=20, mut=20%` | 0,003075 | 0,059 | Equilíbrio |
| `pop=40, gen=20, mut=50%` | 0,003106 | 0,233 | Melhor qualidade absoluta |

As demais 9 configurações são **dominadas** — existe pelo menos uma configuração que as supera em ambas as dimensões simultaneamente.

### 4.4 Configuração Selecionada

A configuração **`pop=40, gen=20, mut=50%`** foi selecionada como referência para as próximas etapas, pelos seguintes motivos:

1. **Maior fitness mediano** entre todas as 12 configurações (0,003106).
2. **Menor desvio padrão relativo** entre as três configurações Pareto-ótimas (2,84 × 10⁻⁵), indicando maior robustez frente à aleatoriedade.
3. **Tempo de execução aceitável** (0,233 s por corrida no circuito de 4 barras): ao escalar para circuitos maiores, o tempo por avaliação aumentará, mas o número de avaliações pode ser mantido ou reduzido com o ganho de qualidade da população maior.

A taxa de mutação de 50% — elevada em relação a valores clássicos da literatura (tipicamente 1–5% em codificação binária) — é compatível com o uso de genes reais e com o espaço de busca contínuo deste problema, onde a mutação atua como perturbação de valores reais dentro dos limites do gene, não como flipagem de bits.

---

## 5 ANÁLISE DOS RESULTADOS

### 5.1 Melhor Solução Encontrada

Com a configuração selecionada (`pop=40, gen=20, mut=50%`), a melhor solução encontrada em uma execução representativa apresentou as seguintes características:

| Variável | Valor |
|----------|-------|
| $P_g$ (potência do gerador) | ~1441 kW |
| $V_g$ (tensão da fonte) | ~1,048 pu |
| Perdas totais | ~422 kW |
| $V_{\min}$ (tensão mínima) | ~0,840 pu |
| $V_{\max}$ (tensão máxima) | ~1,016 pu |
| Convergência do FP | Sim |

O AG convergiu já a partir da **geração 1**, com o fitness se estabilizando rapidamente — comportamento coerente com o esperado para um problema de apenas 2 variáveis contínuas.

### 5.2 Limitação Central: Violação de Tensão

O resultado mais relevante desta análise não é o valor ótimo encontrado, mas uma **limitação estrutural da formulação atual**: a tensão mínima identificada, $V_{\min} \approx 0{,}840$ pu, está **significativamente abaixo** do limite operacional de 0,95 pu, mesmo na melhor solução encontrada.

Isso indica que, na configuração atual do circuito com a carga nominal, nenhuma combinação de $P_g$ e $V_g$ dentro dos domínios definidos é capaz de elevar todas as tensões para dentro da faixa aceitável. Em outras palavras: **as duas variáveis de controle disponíveis são insuficientes** para satisfazer simultaneamente o critério de redução de perdas e o perfil de tensão para o circuito em questão.

Este resultado tem três implicações diretas para os próximos passos:

1. **Motivação para a formulação multiobjetivo:** ao tratar perdas e desvio de tensão como objetivos separados (não agregados em um escalar), o AG poderá explorar explicitamente o trade-off entre os dois critérios e revelar a fronteira de Pareto entre eles.
2. **Ampliação do espaço de variáveis de controle:** ao migrar para circuitos maiores (IEEE 13-Bus, 123-Bus), haverá mais pontos de injeção de geração e mais transformadores com TAP controlável, aumentando a capacidade de regulação do perfil de tensão.
3. **Integração de renováveis:** a inserção de geração distribuída em barras estratégicas é, por si só, um mecanismo documentado de melhoria do perfil de tensão local — como demonstrado nas simulações estáticas do PF1.

### 5.3 Validação do Pipeline

A despeito da limitação identificada, o pipeline cumpriu seu objetivo de **prova de conceito**:

- O AG foi executado com sucesso em 36 corridas independentes sem erros de integração com o OpenDSS.
- A função de fitness retornou valores coerentes com as métricas elétricas de cada candidato.
- O logging automático por geração funcionou corretamente.
- A análise de hiperparâmetros produziu resultados reproduzíveis entre seeds para as melhores configurações.

O pipeline está tecnicamente pronto para receber a formulação multiobjetivo e circuitos de maior porte na continuação do trabalho.

---

## 6 PRÓXIMOS PASSOS

Os próximos relatórios parciais do PF2 serão orientados pelas seguintes etapas, em sequência:

**Etapa 1 — Formulação multiobjetivo real.**
Implementar os dois objetivos separados identificados no PF1: minimização de perdas ($f_1$) e minimização do desvio de tensão ($f_2 = \sum_i |V_i - V_{\text{ref}}|$). Isso requer substituir a função de fitness escalar por uma abordagem Pareto-based, tipicamente o **NSGA-II**, disponível em bibliotecas como `pymoo`. O resultado esperado é uma fronteira de Pareto de soluções, não um único ótimo.

**Etapa 2 — Integração de geração renovável.**
Conectar perfis de geração intermitente ao circuito via `LoadShape` no OpenDSS, conforme modelado no PF1 (distribuição de Weibull para velocidade do vento → curva de potência da turbina → vetor de multiplicadores). O FPO passará a ser avaliado em múltiplos instantes do dia, introduzindo variabilidade na função objetivo.

**Etapa 3 — Escalabilidade para circuitos maiores.**
Migrar do 4-Bus para o **IEEE 13-Bus** ou **IEEE 123-Bus**, já disponíveis em `data/IEEETestCases/`. O espaço de variáveis de controle será ampliado com múltiplos geradores e, eventualmente, TAPs de transformadores (variáveis discretas, exigindo codificação mista).

**Etapa 4 — Avaliação de performance do AG.**
Com os experimentos multiobjetivo em circuitos representativos, definir métricas formais de performance: hipervolume da fronteira de Pareto obtida, diversidade de soluções, taxa de convergência e comparação com PSO ou com um solver determinístico de referência.

---

## 7 CONCLUSÃO PARCIAL

Este relatório apresentou a implementação e validação da prova de conceito do pipeline AG + OpenDSS como primeira entrega do Projeto de Formatura II. O pipeline foi construído com base no planejamento teórico do PF1 e demonstra a viabilidade técnica da integração entre o Algoritmo Genético e o simulador OpenDSS como motor de cálculo do fluxo de potência.

A calibração sistemática de hiperparâmetros, conduzida por busca em grade com análise de fronteira de Pareto qualidade × tempo, identificou a configuração `pop=40, gen=20, mut=50%` como referência para as etapas seguintes. A principal limitação observada — a incapacidade das duas variáveis de controle atuais de satisfazerem os limites de tensão — não representa uma falha do pipeline, mas sim a motivação natural para a extensão multiobjetivo com circuitos de maior porte planejada para a continuação do trabalho.

O Projeto de Formatura II segue, portanto, com infraestrutura computacional validada e rumo experimental claramente definido.

---

*Relatório Parcial 1 — Abril de 2026*
