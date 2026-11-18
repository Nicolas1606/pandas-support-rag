# 5. Avaliação

Separar três níveis: testes de software; recuperação de evidência; qualidade final da orientação. O arquivo reports/RESULTADOS.md contém contagens, denominadores, falhas e tempos reais desta execução.

Recuperação: Hit@5, recall de grupos de evidência e MRR no desenvolvimento. Correspondência usa URL e termos de referência e é uma aproximação, não um julgamento semântico completo. URLs equivalentes foram incluídas nas referências antes do teste final.

Teste final: 60 casos de famílias reservadas, configuração e hashes congelados em reports/release_evaluation/test/protocol.json. Checkpoint por caso; sem selecionar apenas respostas boas. A revisão semântica foi feita com assistência de IA, registrada por caso em reports/semantic_review.csv; não equivale a avaliadores humanos independentes.

Rubrica: correção e sustentação de 0 a 2, erro crítico 0/1, com notas. Um acerto exige atender à pergunta e às condições, não só citar a função. A ação esperada também é comparada. Para respostas não emitidas, distinguir encaminhamento seguro de resolução útil.

Falhas observadas devem permanecer visíveis. Não reajustar o prompt sobre este teste e continuar chamando-o de reservado. Uma nova iteração precisa de novos casos independentes. Testes passaram não significa precisão factual de 100%.
