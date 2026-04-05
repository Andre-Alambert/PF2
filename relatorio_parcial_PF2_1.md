# ANDRÉ LIMA ALAMBERT

**Estudo da performance do algoritmo genético na resolução do Fluxo de Potência Ótimo multiobjetivo com inserção de renováveis.**

Relatório Parcial 1 da disciplina de Projeto de Formatura II, apresentado à Escola Politécnica da Universidade de São Paulo

Área de Concentração: Sistemas de Potência

Orientador: Prof. Dr. Silvio Giuseppe

São Paulo — 2026

---

## RESUMO

Este relatório parcial documenta a primeira etapa do Projeto de Formatura II, cujo objetivo central é analisar a performance do Algoritmo Genético (AG) na resolução do Fluxo de Potência Ótimo (FPO) multiobjetivo com inserção de geração renovável. Nesta etapa, foi implementado e validado o pipeline computacional que integra o AG ao simulador OpenDSS, utilizado como motor de cálculo do fluxo de potência, aplicado ao circuito de referência **IEEE 30-Bus** com despacho ativo de cinco geradores como variáveis de controle. A implementação adota uma formulação mono-objetivo simplificada — combinando perdas ativas e penalização de desvios de tensão em uma única métrica escalar — com o propósito explícito de validar o pipeline de ponta a ponta antes de avançar para a formulação multiobjetivo. Em seguida, foi realizada uma calibração sistemática dos hiperparâmetros do AG por meio de busca em grade com análise de fronteira de Pareto entre qualidade de solução e tempo computacional. Os resultados confirmam a viabilidade técnica do pipeline e identificam a configuração de hiperparâmetros mais adequada para as próximas etapas.

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

**Mapeamento das variáveis para o AG.** Conforme definido teoricamente no PF1, cada indivíduo da população do AG representa um vetor de variáveis de controle do sistema elétrico. Nesta etapa, foram adotadas cinco variáveis de despacho ativo: as potências injetadas pelos geradores nas barras B2, B5, B8, B11 e B13 ($P_{B2}$, $P_{B5}$, $P_{B8}$, $P_{B11}$, $P_{B13}$), em kW. Os setpoints de tensão são mantidos fixos nos valores nominais.

**Motor de simulação.** O OpenDSS, controlado via a biblioteca Python `py-dss-interface`, atua como motor de cálculo do fluxo de potência: recebe os parâmetros do circuito, resolve as equações e retorna tensões, fluxos e perdas para a função de fitness.

**Circuito de referência.** O circuito **IEEE 30-Bus**, benchmark consolidado na literatura de FPO, foi adotado como caso de teste. O circuito possui 30 barras, 34 linhas, 7 transformadores e 21 cargas (~324 MW de carga total). Cinco geradores distribuídos nas barras B2, B5, B8, B11 e B13 são controlados pelo AG; o slack na barra B1 (132 kV) permanece fixo em 1,06 pu.

---

## 3 IMPLEMENTAÇÃO DO PIPELINE AG + OPENDSS

### 3.1 Arquitetura Geral

O pipeline implementado integra o AG, a interface Python do OpenDSS e uma camada de logging conforme a seguinte sequência de execução:

```
Inicialização
  ├── Compilar circuito no OpenDSS
  └── Inicializar população do AG

Para cada geração:
  └── Para cada candidato (P_B2, P_B5, P_B8, P_B11, P_B13):
        ├── Aplicar potências ao circuito via comandos Edit
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
Edit Generator.B2  kW={P_B2}
Edit Generator.B5  kW={P_B5}
Edit Generator.B8  kW={P_B8}
Edit Generator.B11 kW={P_B11}
Edit Generator.B13 kW={P_B13}
```

A biblioteca utilizada para o AG é a **PyGAD**, que fornece os operadores de seleção, crossover e mutação, e expõe um callback `on_generation` utilizado para o registro dos resultados por geração.

### 3.2 Codificação das Variáveis de Controle

O cromossomo de cada indivíduo é um vetor real de cinco genes, um por gerador:

| Gene | Variável | Domínio |
|------|----------|---------|
| $g_1$ | $P_{B2}$ — potência ativa do gerador na barra B2 | $[0,\ 80{.}000]$ kW |
| $g_2$ | $P_{B5}$ — potência ativa do gerador na barra B5 | $[0,\ 50{.}000]$ kW |
| $g_3$ | $P_{B8}$ — potência ativa do gerador na barra B8 | $[0,\ 35{.}000]$ kW |
| $g_4$ | $P_{B11}$ — potência ativa do gerador na barra B11 | $[0,\ 30{.}000]$ kW |
| $g_5$ | $P_{B13}$ — potência ativa do gerador na barra B13 | $[0,\ 40{.}000]$ kW |

A codificação em números reais foi mantida, evitando erros de arredondamento em relação à codificação binária. Os limites de cada gene correspondem à capacidade nominal de despacho ativo de cada gerador segundo o benchmark padrão IEEE 30-Bus. Os setpoints de tensão permanecem fixos nos valores nominais (despacho ativo puro, sem controle de tensão nesta etapa).

### 3.3 Função de Fitness

O objetivo do FPO nesta etapa é **minimizar as perdas ativas** do sistema, respeitando limites de tensão nas barras. Como o PyGAD **maximiza** a função de fitness, adotou-se a inversão da função de custo penalizada:

$$\text{fitness}(x) = \frac{1}{1 + C(x)}$$

onde $C(x)$ é o custo total dado por:

$$C(x) = P_{\text{loss}}\ [\text{kW}]\ +\ w_v \cdot \sum_{i} \left[\max\!\left(0,\ V_{\min} - V_i\right)^2 + \max\!\left(0,\ V_i - V_{\max}\right)^2\right]$$

com os seguintes parâmetros:

| Parâmetro | Valor |
|-----------|-------|
| $V_{\min}$ | 0,95 pu |
| $V_{\max}$ | 1,10 pu |
| $w_v$ (peso da penalização de tensão) | 10.000 |
| Penalização por não convergência | $C(x) = 10^6$ |

O peso $w_v = 10.000$ foi escolhido para garantir que uma violação de tensão de 0,01 pu em uma única barra adicione 1 kW equivalente ao custo, tornando as restrições de tensão fortemente desencorajadas sem eliminar a busca em regiões próximas aos limites. Quando o fluxo de potência não converge, aplica-se diretamente $C(x) = 10^6$, assegurando que soluções inviáveis recebam fitness mínimo.

Esta formulação escalar é uma **prova de conceito**: consolida a arquitetura do pipeline, mas não representa a formulação multiobjetivo prevista para as etapas seguintes do PF2.

### 3.4 Interface AG ↔ OpenDSS

A avaliação de cada candidato envolve três passos executados sequencialmente pela função `evaluate_solution`:

1. **Decodificação:** o vetor de cinco genes $[g_1, \ldots, g_5]$ é mapeado diretamente para $\{P_{B2}, P_{B5}, P_{B8}, P_{B11}, P_{B13}\}$ (genes reais, sem decodificação binária).
2. **Aplicação:** os cinco valores são enviados ao OpenDSS por comandos `Edit Generator.{Bx} kW={P_{Bx}}`, um por gerador.
3. **Resolução e extração:** `dss.solution.solve()` é chamado; em seguida são extraídos perdas totais (`dss.circuit.losses`) e tensões em todas as barras (`dss.circuit.buses_vmag_pu`).

Um cache `_eval_cache` armazena as métricas de cada candidato avaliado na geração corrente, permitindo que o callback `on_generation` acesse as métricas do melhor indivíduo sem reavaliação.

### 3.5 Logging e Visualização

A cada geração, os seguintes dados são registrados em CSV:

| Campo | Descrição |
|-------|-----------|
| `generation` | Número da geração |
| `best_fitness` | Maior fitness da geração |
| `P_B2`, `P_B5`, `P_B8`, `P_B11`, `P_B13` | Potências ativas dos geradores na melhor solução (kW) |
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

A Tabela 1 apresenta as 12 configurações testadas (3 seeds cada, 36 corridas no total) ordenadas por fitness mediano decrescente.

**Tabela 1 — Resultados agregados da busca em grade — IEEE 30-Bus (ordenado por fitness mediano)**

| `pop` | `gen` | `mut` (%) | Fitness mediano | Desvio padrão | Conv. (geração) | Tempo (s) |
|-------|-------|-----------|----------------|---------------|-----------------|-----------|
| 40 | 20 | 20 | 2,619 × 10⁻⁴ | 4,67 × 10⁻⁶ | 13 | 1,227 |
| 20 | 20 | 20 | 2,616 × 10⁻⁴ | 5,49 × 10⁻⁶ | 13 | 0,575 |
| 20 | 10 | 20 | 2,538 × 10⁻⁴ | 8,31 × 10⁻⁶ | 10 | 0,375 |
| 40 | 10 | 50 | 2,476 × 10⁻⁴ | 8,32 × 10⁻⁶ |  6 | 0,614 |
| 20 | 20 | 50 | 2,458 × 10⁻⁴ | 1,85 × 10⁻⁵ |  6 | 0,577 |
| 40 | 20 | 50 | 2,453 × 10⁻⁴ | 4,70 × 10⁻⁶ |  5 | 1,219 |
| 10 | 20 | 20 | 2,450 × 10⁻⁴ | 1,01 × 10⁻⁵ | 11 | 0,276 |
| 10 | 20 | 50 | 2,436 × 10⁻⁴ | 6,98 × 10⁻⁶ |  7 | 0,336 |
| 40 | 10 | 20 | 2,410 × 10⁻⁴ | 1,33 × 10⁻⁵ |  9 | 0,632 |
| 20 | 10 | 50 | 2,410 × 10⁻⁴ | 6,81 × 10⁻⁶ |  2 | 0,328 |
| 10 | 10 | 20 | 2,337 × 10⁻⁴ | 1,70 × 10⁻⁵ |  9 | 0,152 |
| 10 | 10 | 50 | 2,275 × 10⁻⁴ | 2,09 × 10⁻⁵ |  6 | 0,173 |
| 40 | 20 | 20 | 2,619 × 10⁻⁴ | 4,67 × 10⁻⁶ | 13 | 1,227 |
| 20 | 20 | 20 | 2,616 × 10⁻⁴ | 5,49 × 10⁻⁶ | 13 | 0,575 |
| 20 | 10 | 20 | 2,538 × 10⁻⁴ | 8,31 × 10⁻⁶ | 10 | 0,375 |
| 40 | 10 | 50 | 2,476 × 10⁻⁴ | 8,32 × 10⁻⁶ |  6 | 0,614 |
| 20 | 20 | 50 | 2,458 × 10⁻⁴ | 1,85 × 10⁻⁵ |  6 | 0,577 |
| 40 | 20 | 50 | 2,453 × 10⁻⁴ | 4,70 × 10⁻⁶ |  5 | 1,219 |
| 10 | 20 | 20 | 2,450 × 10⁻⁴ | 1,01 × 10⁻⁵ | 11 | 0,276 |
| 10 | 20 | 50 | 2,436 × 10⁻⁴ | 6,98 × 10⁻⁶ |  7 | 0,336 |
| 40 | 10 | 20 | 2,410 × 10⁻⁴ | 1,33 × 10⁻⁵ |  9 | 0,632 |
| 20 | 10 | 50 | 2,410 × 10⁻⁴ | 6,81 × 10⁻⁶ |  2 | 0,328 |
| 10 | 10 | 20 | 2,337 × 10⁻⁴ | 1,70 × 10⁻⁵ |  9 | 0,152 |
| 10 | 10 | 50 | 2,275 × 10⁻⁴ | 2,09 × 10⁻⁵ |  6 | 0,173 |

**Observações gerais:**
- Ordenando por fitness mediano, as configurações com `mut=20%` ocupam as três primeiras posições — situação inversa ao caso 4-Bus, onde `mut=50%` dominava. Com 5 variáveis de decisão, uma taxa de mutação menor favorece a exploração local mais fina.
- A variação total de fitness entre a melhor e a pior configuração é de ~13%, mais ampla que os ~6,6% do 4-Bus, indicando que a escolha de hiperparâmetros impõe mais impacto quando o espaço de busca é maior.
- O tempo mediano por corrida é 5 a 8× superior ao do 4-Bus (0,152 a 1,227 s vs. 0,031 a 0,233 s), refletindo o custo adicional de simular 30 barras, 34 linhas e 7 transformadores.
- Populações maiores (`pop=40`) continuam apresentando menor desvio padrão entre seeds.

### 4.3 Análise de Fronteira de Pareto: Qualidade × Tempo Computacional

Analisar apenas o fitness máximo para escolha de hiperparâmetros ignora o custo computacional da configuração — relevante dado que, nas próximas etapas, o circuito será maior e cada avaliação de fitness exigirá mais tempo de simulação. Para endereçar esse trade-off, foi computada a **fronteira de Pareto** sobre o espaço bidimensional (tempo, fitness), com os dois objetivos a minimizar sendo:

- $-\text{fitness mediano}$ (maximizar qualidade → minimizar negativo)
- $\text{tempo mediano de execução}$

Uma configuração é Pareto-ótima se nenhuma outra configuração alcança simultaneamente maior fitness e menor tempo. A análise identificou **cinco** configurações na fronteira, todas com `mut=20%`:

| Configuração | Fitness mediano | Tempo (s) | Interpretação |
|---|---|---|---|
| `pop=10, gen=10, mut=20%` | 2,337 × 10⁻⁴ | 0,152 | Melhor custo-benefício em tempo |
| `pop=10, gen=20, mut=20%` | 2,450 × 10⁻⁴ | 0,276 | |
| `pop=20, gen=10, mut=20%` | 2,538 × 10⁻⁴ | 0,375 | Equilíbrio |
| `pop=20, gen=20, mut=20%` | 2,616 × 10⁻⁴ | 0,575 | |
| `pop=40, gen=20, mut=20%` | 2,619 × 10⁻⁴ | 1,227 | Melhor qualidade absoluta |

As 7 configurações restantes são **dominadas**. Nota-se que todas as configurações Pareto-ótimas utilizam `mut=20%`, confirmando que, para um espaço de 5 variáveis contínuas, uma taxa de mutação moderada equilibra melhor exploração e convergência. Esse resultado contrasta diretamente com o caso 4-Bus, onde todas as Pareto-ótimas usavam `mut=50%`.

### 4.4 Configuração Selecionada

A configuração **`pop=40, gen=20, mut=20%`** foi selecionada como referência para o pipeline IEEE 30-Bus, pelos seguintes motivos:

1. **Maior fitness mediano** entre todas as 12 configurações (2,619 × 10⁻⁴).
2. **Menor desvio padrão** entre as cinco configurações Pareto-ótimas (4,67 × 10⁻⁶), indicando maior estabilidade entre seeds.
3. **Tempo aceitável** (1,227 s por corrida) para validação e iteração do pipeline.

Observa-se que a taxa de mutação selecionada (20%) é inferior à do caso 4-Bus (50%). Para um espaço de 5 variáveis, uma mutação menor por gene permite exploração local mais fina e convergência mais estável; uma mutação muito alta tende a dispersar a população excessivamente, dificultando a otimização conjunta das cinco dimensões.

---

## 5 ANÁLISE DOS RESULTADOS

### 5.1 Melhor Solução Encontrada

Com a configuração selecionada (`pop=40, gen=20, mut=20%`), a melhor solução encontrada em uma execução representativa apresentou as seguintes características:

| Variável | Valor |
|----------|-------|
| $P_{B2}$ (potência ativa — barra B2) | ~69.178 kW (~69,2 MW) |
| $P_{B5}$ (potência ativa — barra B5) | ~48.787 kW (~48,8 MW) |
| $P_{B8}$ (potência ativa — barra B8) | ~34.803 kW (~34,8 MW) |
| $P_{B11}$ (potência ativa — barra B11) | ~29.602 kW (~29,6 MW) |
| $P_{B13}$ (potência ativa — barra B13) | ~34.073 kW (~34,1 MW) |
| Perdas totais | ~3.892 kW (~3,9 MW) |
| $V_{\min}$ (tensão mínima) | ~0,993 pu |
| $V_{\max}$ (tensão máxima) | ~1,082 pu |
| Convergência do FP | Sim |
| Geração de convergência | 10 |

O AG convergiu na **geração 10**, com melhorias progressivas até esse ponto e estabilidade completa nas gerações seguintes — comportamento coerente com o esperado para um espaço de busca de 5 variáveis, que exige mais iterações do que o caso de 2 variáveis do 4-Bus.

### 5.2 Perfil de Tensão e Estratégia de Despacho

**Perfil de tensão:** Diferentemente do caso 4-Bus, onde $V_{\min} \approx 0{,}840$ pu violava significativamente os limites operacionais, a melhor solução do IEEE 30-Bus apresentou **todas as tensões dentro da faixa [0,95; 1,10] pu** ($V_{\min} = 0{,}993$ pu; $V_{\max} = 1{,}082$ pu). O circuito dispõe de capacidade reativa suficiente em seus cinco geradores para sustentar o perfil de tensão mesmo sob carga plena.

**Estratégia emergente de despacho:** A análise dos valores ótimos revela que o AG empurrou as potências dos geradores próximas aos seus limites superiores: B5 a 97,6%, B8 a 99,4% e B11 a 98,7% dos respectivos máximos. Esse comportamento é fisicamente coerente: na formulação adotada, sem função de custo de geração, a única pressão do fitness é minimizar perdas na rede — e a injeção de potência ativa próxima às cargas reduz o fluxo nas linhas e, consequentemente, as perdas ôhmicas $I^2R$. O AG encontrou, portanto, a estratégia de máxima injeção distribuída como ótimo mono-objetivo da formulação atual.

**Implicação para a próxima etapa:** Este resultado evidencia a necessidade de incluir uma **função de custo de geração** na formulação. No despacho econômico clássico, cada gerador possui uma curva de custo própria, e o ótimo é o ponto que equilibra custo marginal de geração com a redução de perdas de transmissão — não o ponto de máxima injeção. A formulação multiobjetivo planejada separará explicitamente os objetivos de custo e perdas, revelando o trade-off real entre geração econômica e minimização de perdas.

### 5.3 Validação do Pipeline

O pipeline cumpriu seu objetivo de **validação em circuito de referência realístico**:

- O AG foi executado com sucesso em 36 corridas independentes sem erros de integração com o OpenDSS.
- A generalização para N geradores foi validada: 5 variáveis de controle, genes independentes por gerador.
- A função de fitness retornou valores coerentes com as métricas elétricas de cada candidato.
- O logging automático por geração produziu colunas dinâmicas corretas ($P_{B2}$…$P_{B13}$) para todas as 36 corridas.
- A análise de hiperparâmetros produziu resultados reproduzíveis entre seeds para as melhores configurações.

O pipeline está tecnicamente pronto para receber a função de custo de geração, a formulação multiobjetivo e circuitos de maior porte na continuação do trabalho.

---

## 6 PRÓXIMOS PASSOS

Os próximos relatórios parciais do PF2 serão orientados pelas seguintes etapas, em sequência:

**Etapa 1 — Função de custo de geração.**
Os resultados do IEEE 30-Bus mostram que, sem custo de geração, o AG converge para injeção máxima em todos os geradores. A próxima etapa incorpora curvas de custo quadráticas por gerador ($C_i(P_i) = a_i P_i^2 + b_i P_i + c_i$), transformando o problema em um despacho econômico real com trade-off entre custo de geração e perdas de transmissão.

**Etapa 2 — Formulação multiobjetivo (NSGA-II).**
Substituir a função de fitness escalar por dois objetivos separados: $f_1 =$ custo total de geração e $f_2 =$ perdas ativas na rede (ou desvio de tensão). Utilizar **NSGA-II** (`pymoo`) para obter a fronteira de Pareto de soluções não dominadas, revelando explicitamente o trade-off entre operação econômica e eficiência elétrica.

**Etapa 3 — Integração de geração renovável.**
Conectar perfis de geração intermitente ao circuito via `LoadShape` no OpenDSS, conforme modelado no PF1 (distribuição de Weibull → curva de potência → vetor de multiplicadores horários). O FPO será avaliado em múltiplos instantes do dia, introduzindo variabilidade na função objetivo.

**Etapa 4 — Escalabilidade e avaliação de performance.**
Migrar para o **IEEE 123-Bus** (já disponível em `data/IEEETestCases/`), ampliando o número de variáveis de controle. Ao final, definir métricas formais de performance: hipervolume da fronteira de Pareto, diversidade de soluções, taxa de convergência e comparação com referências da literatura.

---

## 7 CONCLUSÃO PARCIAL

Este relatório apresentou a implementação e validação da prova de conceito do pipeline AG + OpenDSS como primeira entrega do Projeto de Formatura II. O pipeline foi construído com base no planejamento teórico do PF1 e demonstra a viabilidade técnica da integração entre o Algoritmo Genético e o simulador OpenDSS como motor de cálculo do fluxo de potência.

A calibração sistemática de hiperparâmetros, conduzida por busca em grade com análise de fronteira de Pareto qualidade × tempo, identificou a configuração `pop=40, gen=20, mut=20%` como referência para o circuito IEEE 30-Bus. Diferentemente do caso inicial com 2 variáveis, o pipeline generalizado para 5 geradores apresentou perfil de tensão inteiramente dentro dos limites operacionais ($V_{\min} = 0{,}993$ pu; $V_{\max} = 1{,}082$ pu), validando tanto a generalização da implementação quanto a capacidade do AG de encontrar soluções viáveis em espaços de busca de maior dimensão. A ausência de violações de tensão, combinada à convergência na geração 10, confirma que o pipeline está pronto para incorporar a função de custo de geração e a formulação multiobjetivo nas próximas etapas.

O Projeto de Formatura II segue, portanto, com infraestrutura computacional validada, resultados experimentais concretos no benchmark IEEE 30-Bus e rumo técnico claramente definido.

---

*Relatório Parcial 1 — Abril de 2026*
