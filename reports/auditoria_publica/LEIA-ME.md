# Auditoria pública de desenvolvimento
A versão congelada foi executada em modo controlado com 30 perguntas redigidas por IA. A ação esperada e a referência foram escritas antes da execução. O resultado bruto de cada caso está em responses.json e as entradas estão em evaluation/auditoria_publica/casos.jsonl.

| Indicador | Observação |
|---|---|
| Ação answer nas perguntas respondíveis | 8 de 20 (40%) |
| Encaminhamentos nas perguntas respondíveis | 12 de 20 |
| Esclarecimentos esperados atendidos | 2 de 5 |
| Encaminhamentos esperados atendidos | 4 de 5 |
| Ação de triagem correta | 6 de 10 (60%) |

A inspeção por IA encontrou orientação compatível com as referências nas oito respostas emitidas. A17 informa o lado único, mas poderia dizer explicitamente que a direita aceita repetições. A1 encaminhou uma dúvida prática sobre pedidos e clientes. A16 respondeu corretamente quando a pergunta incluiu m:1. A29 pediu contexto numa questão sobre PostgreSQL. O reconhecimento de formulações do usuário precisa melhorar. Mesmo aprovando todas as oito respostas em revisão humana, a resolução máxima seria 40% nesta amostra. Os critérios propostos são 70% de resolução e 90% de triagem.

A amostra é pública, pequena e intencional. A avaliação humana independente e o estudo de tempo com usuários estão pendentes. Para reproduzir, execute na raiz do projeto:

    python scripts/pilot.py run evaluation/auditoria_publica/casos.jsonl data/repro_auditoria

Use um diretório de saída novo a cada execução.
