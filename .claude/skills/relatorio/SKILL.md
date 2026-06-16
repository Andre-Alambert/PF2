name: escrever-relatorio

description: Use quando for escrever ou expandir uma seção do relatório final de PF2.

# Skill: Escrever Relatório PF2

## Contexto do projeto

Projeto de Formatura 2 (PF2) — Otimização de Fluxo de Potência Multiobjetivo.
Algoritmo: NSGA-III (pymoo). Simulação via OpenDSS (py_dss_interface).
Caso principal: IEEE 118-Bus (18 geradores controláveis). IEEE 30-Bus: pode aparecer pontualmente para validação de pipeline, mas sua inclusão no relatório ainda não está decidida — não trate como caso central.
Três objetivos: f1 = custo de geração [$/h], f2 = desvio de tensão [pu], f3 = emissões [ton/h].

## O que fazer quando esta skill for invocada

O usuário quer escrever ou expandir uma seção do relatório de PF2.
Pergunte qual seção ou subseção ele quer trabalhar se não estiver claro no comando.

## Diretrizes de escrita

- Linguagem: português técnico-acadêmico, sem informalidades.
- Tom: objetivo e direto; sem frases de preenchimento ("é importante notar que…").
- Estrutura: cada parágrafo tem uma tese, evidência dos dados e interpretação — nessa ordem.
- Números: sempre com unidade e fonte (tabela, figura ou CSV). Nunca invente valores.
- Equações: notação LaTeX inline (`$…$`) ou display (`$$…$$`).
- Figuras e tabelas: referencie pelo número ("Tabela 3", "Figura 2a") e descreva o que o leitor deve observar nelas.
- Números ausentes: marque com [PREENCHER] onde resultados definitivos ainda não estão disponíveis. Não bloqueie a escrita por falta de dados.
- Hipervolume: quando mencionar HV, explique brevemente que mede o volume do espaço dominado pela frente de Pareto — o leitor pode não conhecer a métrica.

## O que evitar

- Não repita o que já está no CLAUDE.md como se fosse novidade no relatório.
- Não use bullets onde o texto corrido flui melhor.
- Não escreva seções de "Conclusão" parciais — só quando o usuário pedir explicitamente.
- Não fabrique resultados: se um dado não estiver nos CSVs lidos, diga que precisa ser obtido.

## Arquivo de destino

O relatório é escrito em `reports/final_report.md`. Após aprovação do usuário, grave o conteúdo nesse arquivo — nunca antes.

## Fluxo típico

1. Ler os CSVs relevantes em `results/` para ter os números na mão.
2. Perguntar ao usuário o nível de detalhe desejado (parágrafo, subseção completa, etc.).
3. Escrever o texto e apresentar ao usuário para revisão.
4. Após aprovação, gravar em `reports/final_report.md`.
