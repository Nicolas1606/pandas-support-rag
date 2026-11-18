# Resultados reais da release 1.0

Data: 17/11/2026. Implantação local Windows/Python 3.14, aproximadamente 16 GB RAM e RTX 3060 Laptop. Configuração e hashes no protocolo.

## Decisão de uso

O fluxo de engenharia está reproduzido de ponta a ponta. A geração **não foi aprovada para atendimento autônomo**. A revisão encontrou 24 respostas plenamente corretas e sustentadas entre 49 orientações emitidas (49,0%); 15 casos receberam marcação de erro crítico pela rubrica. O verificador do próprio modelo deixou erros passarem. O uso demonstrável é de apoio, com revisão do atendente e acesso às fontes. Não apresentar como solução de acurácia elevada ou como produção empresarial.

## Software e instalação

- 73 testes unitários e de integração passaram, incluindo HTTP e FastAPI: test_all.txt.
- Instalação em dados temporários e HTTP real passou: clean_installation.json.
- Três fluxos conhecidos com modelo real: cardinalidade muitos para um; dúvida Spark fora do escopo; sintoma de duplicação sem exemplo mínimo. Todos passaram nessa reprodução.
- Reconstrução a partir do snapshot reproduziu o corpus 81396567c3f64252, 30 páginas e 1.068 passagens.
- Nova ingestão HTTP das 30 páginas foi executada como candidata separada. Não foi promovida como se fosse o corpus avaliado.
- CI configurada; nenhuma execução remota no GitHub foi alegada.

## Recuperação no desenvolvimento

60 consultas, das quais 38 têm evidência de referência. Hit@5 mede presença de um trecho compatível por URL/termos. Referências incluem APIs equivalentes. A consulta é a pergunta original; esta comparação não inclui o planejador da geração.

| Método | Hit@5 | MRR | Mediana de busca |
|---|---:|---:|---:|
| bm25 | 52.63% (20/38) | 0.289 | 3.5 ms |
| dense | 73.68% (28/38) | 0.527 | 131.0 ms |
| hybrid | 65.79% (25/38) | 0.533 | 138.8 ms |

Escolha semântica feita no desenvolvimento. A atualização das referências para APIs equivalentes foi anterior ao teste final; não representa um ganho de algoritmo. Resultados em development_retrieval.json.

## Teste reservado

60 casos em 30 famílias diferentes das famílias de desenvolvimento. 40 esperavam resposta, 8 esclarecimento e 12 encaminhamento. Parâmetros e prompts congelados antes da execução; checkpoints retomados após interrupção, sem trocar configuração.

| Indicador | Resultado |
|---|---:|
| Casos executados | 60/60 |
| Ação coincide com referência | 49/60 (81,7%) |
| Orientações emitidas | 49 |
| Orientações plenamente corretas e sustentadas | 24/49 (49,0%) |
| Resolução correta entre casos respondíveis | 24/40 (60,0%) |
| Mediana total, todos os casos | 15,45 s |
| P95 total, todos os casos | 20,74 s |
| Casos com erro crítico na revisão | 15/60 |

Acertar a ação answer não significa responder corretamente. Há 7 respostas emitidas quando deveria pedir contexto e 3 quando deveria encaminhar. A revisão dos 49 answers está completa. O revisor foi um assistente de IA: **não houve avaliação humana externa independente**. Wilson 95% descritivo para aprovação entre respostas: 35,6%–62,5%; as paráfrases são dependentes, portanto não interpretar esse intervalo como garantia de generalização. Precisão por citação e cobertura semântica por citação não foram anotadas individualmente; os campos permanecem nulos, em vez de inventar 100%.

## Falhas representativas

| Caso | Falha | Consequência |
|---|---|---|
| 006-1 / 006-2 | Sugere na_values=[NA] para preservar NA textual | Produz o comportamento oposto |
| 004-2 / 028-2 | Traduz nome literal de coluna | Exemplo deixa de respeitar o esquema |
| 024-1 | Confunde método com parâmetro homônimo | Explica outra API |
| 026-1 | Omite how=left/outer ao procurar left_only | Merge inner elimina exclusivos |
| 032-2 / 052-2 | Confunde igualdade de NaN com junção de nulos | Explicação errada |
| 040 / 042 | Decide tipo/imputação sem significado de negócio | Falta esclarecimento |
| 058-1 / 060-1 | Orientação sem relação com o pedido | Falha de escopo apesar das fontes reais |

Os JSONs originais, fontes, interpretação, verificação automática e tempos estão em release_evaluation/test/results.json. As notas estão em semantic_review.csv e a agregação em semantic_summary.json. Referências de qualidade auditadas em evaluation/source_audit.json. Nenhum resultado negativo foi removido do teste final.

## O que foi demonstrado

Coleta, preparação, comparação de buscas, geração local real, contratos, API, interface, avaliação, logs, feedback, controle de corpus e reprodução. O resultado experimental mostra por que recuperar fonte oficial e verificar com o mesmo modelo ainda não basta para aprovar uma resposta. O notebook apresenta essa conclusão e as decisões.

## Próxima hipótese de qualidade

Investigar interpretação e verificação mais confiáveis em desenvolvimento, preservar identificadores e validar exemplos mínimos executáveis. Exigir revisão humana externa e outro conjunto de teste antes de elevar o nível de autonomia. Não ajustar sobre estes 60 casos e continuar chamando-os de reservados. Não houve medição de ganho de receita, tempo de atendimento humano, adoção ou qualidade em produção.
