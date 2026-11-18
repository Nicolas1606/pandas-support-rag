# Sessão com participantes
O facilitador entrega uma tarefa por vez. Use a documentação pandas 2.2.3 em todas as tarefas. Na condição assistida disponibilize também o aplicativo com sua configuração padrão. Cada participante entrega a linha de código e uma frase explicando o resultado. Comece o cronômetro ao revelar o enunciado e pare na entrega. Tempo limite de 300 segundos. Registre tentativas incompletas com 300 segundos e correção zero.

| Tarefa | Enunciado entregue |
|---|---|
| A1 | Pedidos tem cliente_id [8,8,9]. Clientes tem cliente_id [8,9]. Junte pedidos à esquerda com clientes à direita por cliente_id e faça a operação falhar caso o cadastro passe a ter dois registros para o cliente 8. |
| A2 | Lojas tem loja_id [4,5]. Visitas tem loja_id [4,4,5]. Junte lojas à esquerda com visitas à direita por loja_id e faça a operação falhar se a loja 4 aparecer duas vezes no cadastro de lojas. |
| B1 | Em pedidos.csv a coluna regiao contém NA, BR e AUSENTE. NA designa uma região válida. Leia o arquivo preservando a região NA e convertendo AUSENTE em valor ausente somente nessa coluna. |
| B2 | Em estoque.csv a coluna setor contém NA, SUL e SEM_DADO. NA é um setor válido. Leia o arquivo preservando o setor NA e convertendo SEM_DADO em valor ausente somente nessa coluna. |

## Distribuição prévia
Para P01 e P05 use A1 manual, B2 assistida, A2 assistida, B1 manual. Para P02 use A1 assistida, B2 manual, A2 manual, B1 assistida. Para P03 use B1 assistida, A2 manual, B2 manual, A1 assistida. Para P04 use B1 manual, A2 assistida, B2 assistida, A1 manual. Cada participante contribui com dois pares. Entregue somente o enunciado da vez. Obtenha consentimento antes da sessão.

## Correção cega
Envie a um revisor externo o enunciado e a entrega identificada por código, em ordem embaralhada. Guarde condição, tempo e participante com o facilitador até concluir a correção. A1 exige chave e ordem corretas e many_to_one ou m:1. A2 exige chave e ordem corretas e one_to_many ou 1:m. B1 e B2 exigem preservação do literal NA e conversão restrita à coluna indicada. Aceite código equivalente que passe esses exemplos. Registre 1 se cumprir todos os requisitos, 0 caso contrário. Guarde motivo e entrega original. Use evaluation/user_study.csv com task_pair A ou B. O comando de análise está em docs/PILOTO.md.

## Revisão independente da aplicação
Um autor externo escreve privadamente 20 casos respondíveis e 10 de triagem antes da execução. Um revisor externo registra a ação, a correção da orientação e a sustentação de cada afirmação pelas fontes, usando a ficha gerada por pilot.py. Para conferir cardinalidade, verifique o lado único no exemplo e no texto. A auditoria pública serve para reprodução e desenvolvimento. Preserve um novo conjunto privado para a decisão de publicação.
