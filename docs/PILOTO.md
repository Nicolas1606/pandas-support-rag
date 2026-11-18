# Avaliação independente e piloto com usuários

## Teste reservado

A versão e o protocolo são identificados por hash em evaluation/pilot_freeze.json. Convide profissionais de dados que não desenvolveram o sistema. Um autor externo prepara ao menos 20 casos respondíveis dentro do escopo e 10 de triagem, com exemplos de esclarecimento e encaminhamento. Varie linguagem, contexto e operações. Mantenha as perguntas privadas até congelar as saídas. Registre por escrito quem escreveu os casos e quando. Entregue ao avaliador apenas as referências, as fontes e as saídas, de preferência em ordem aleatória.

Cada linha do JSONL privado tem id, question, expected_action e reference. Os campos context e version são opcionais. Para cada referência, descreva condições essenciais, resultado esperado e passagem oficial. Use answer, clarify ou handoff como ação.

```sh
python scripts/pilot.py run casos-privados.jsonl data/piloto01
python scripts/pilot.py analyze --run data/piloto01 --study data/medicoes.csv
```

O revisor humano independente preenche review.csv. correct vale 1 se a ação e o conteúdo atendem à tarefa. supported vale 1 nas respostas com sustentação completa. Para triagem, preencha supported com 0. critical vale 1 se a saída puder induzir uma decisão materialmente errada, como inverter cardinalidade, apagar informação ou alterar o significado de ausentes. Registre divergências antes da adjudicação. O script mede as notas recebidas. Independência, sigilo e procedência são verificados pelo responsável pelo estudo.

## Tarefa e comparação

Recrute pelo menos cinco pessoas. Em duas tarefas pareadas por participante, peça uma orientação verificável para um colega. Alterne a ordem manual e assistida entre pessoas e use variantes equivalentes para reduzir memorização. Fixe limite de cinco minutos por tarefa e registre cinco minutos e nota zero se não houver entrega. Cronometre da leitura da tarefa até a submissão. A pessoa avaliadora recebe apenas o texto final e a referência.

- Par A usa junções entre pedidos e cadastros com exigência de unicidade. As variantes trocam o lado único e os nomes das chaves.
- Par B usa CSV com um marcador literal NA e um marcador diferente de valor ausente. As variantes trocam os nomes das colunas e o outro marcador.

Na condição manual, ofereça a documentação oficial congelada. Na assistida, ofereça a mesma documentação e a aplicação. Registre ordem, variante e comentários em formulário separado. Informe o uso das medições, obtenha consentimento e use IDs pseudônimos. Copie evaluation/user_study.csv para data/medicoes.csv e preencha uma linha por condição e tarefa. Use manual ou assisted no campo method. O revisor atribui correct como 0 ou 1 com a mesma rubrica nas duas condições.

## Critérios propostos para este piloto

| Dimensão | Critério |
|---|---|
| Respostas emitidas | Pelo menos 95% corretas e sustentadas |
| Resolução | Pelo menos 70% dos casos respondíveis resolvidos corretamente |
| Triagem | Pelo menos 90% dos casos de esclarecimento e encaminhamento tratados corretamente |
| Erros críticos | Zero observados na amostra |
| Utilidade | Pelo menos 10 pares completos de cinco pessoas ou mais |
| Tempo e correção | Mediana assistido/manual de até 0,80, com correção assistida igual ou superior à manual |

Esses limiares são critérios de avanço do piloto. Amostra pequena, dependência entre tarefas e seleção de participantes limitam as conclusões. Contabilize todas as tentativas. Registre exclusões e publique denominadores. Caso haja mudanças guiadas pelos resultados, congele outra versão e forme outro conjunto reservado.
