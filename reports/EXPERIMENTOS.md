# Histórico dos experimentos

- development_4b_partial/: checkpoints de uma tentativa parcial com qwen3:4b. Não usar como taxa global nem como comparação estatística completa. Houve respostas erradas e retenção de respostas por validação.
- development_selection/: 12 casos de desenvolvimento escolhidos explicitamente para investigar perguntas típicas e limites do 8B. A configuração foi ajustada depois, antes do teste final, para pedir contexto em sintomas vagos. Não chamar essa subamostra de teste reservado.
- release_evaluation/test/: execução final de todos os 60 casos reservados, com protocolo congelado e revisão de todas as orientações emitidas.
- development_retrieval.json: comparação dos três métodos de busca no desenvolvimento completo, sem geração.

O histórico parcial não é usado para alegar superioridade estatística do modelo maior. Não foram produzidos números artificiais para as execuções interrompidas. O teste final foi retomado pelos checkpoints sem alterar a configuração de geração. A interface, documentos e scripts de reprodução foram finalizados depois; os parâmetros e prompts avaliados foram preservados.
