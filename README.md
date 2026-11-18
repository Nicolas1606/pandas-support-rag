# Pandas Support

**Assistente local de suporte ao pandas 2.2.3.** Faça uma pergunta em português sobre leitura de CSV, conversão de tipos ou junções de tabelas. A aplicação oferece uma orientação com a passagem da documentação oficial ou indica o que falta para responder.

## Por onde começar

| Quero… | Onde ler |
|---|---|
| Entender para que serve | [Problema e exemplo](#problema-e-exemplo) |
| Abrir a aplicação | [Como executar](#como-executar) |
| Entender como foi construída | [Arquitetura](#arquitetura) |
| Conferir resultados e limitações | [Avaliação](#avaliação) |
| Localizar qualquer artefato | [Mapa do repositório](#mapa-do-repositório) |

## Problema e exemplo

Pandas é uma biblioteca Python para trabalhar com dados em tabelas. Um CSV é um arquivo de texto com linhas e colunas, comum em exportações de sistemas. Ao importar um cadastro, o código `0007` pode virar `7` se o programa interpretar a coluna como número. Isso pode impedir que o código seja encontrado em outro sistema.

O assistente recebe uma pergunta, contexto opcional e a versão do pandas. Para preservar `0007`, pode sugerir `pd.read_csv(arquivo, dtype={"codigo": "string"})` e mostrar a passagem oficial que explica o parâmetro. A orientação pressupõe que a coluna se chama `codigo`. Se a mesma coluna também precisar ser somada, o assistente pede contexto sobre o significado do valor.

Uma junção, chamada *merge* no pandas, combina duas tabelas por uma chave comum. Muitos pedidos podem ter o mesmo cliente. Com pedidos à esquerda e clientes à direita, `validate="many_to_one"` verifica que o cadastro da direita tem uma única linha por cliente. Se o cadastro tiver duplicatas, o pandas recusa a junção.

A aplicação foi pensada para alguém que consulta ou revisa suporte técnico. A entrada é texto. O código proposto é apresentado para revisão e execução no ambiente de quem o solicitou.

## Como executar

1. Instale Python 3.11 ou superior. Python executa o projeto. Pandas 2.2.3 identifica a versão da documentação estudada.
2. Extraia o projeto e abra no VS Code a pasta que contém `main.py`. Abra o terminal nessa pasta.
3. Execute o comando abaixo. A base distribuída é preparada na primeira execução. O modo controlado usa a biblioteca padrão do Python e dispensa Ollama.

~~~powershell
python main.py serve
~~~

Se o Windows mostrar a Microsoft Store ao chamar `python` e você tiver instalado o Python 3.14 no local padrão por usuário, execute:

~~~powershell
& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" main.py serve
~~~

Deixe o terminal aberto. Abra [a aplicação local](http://127.0.0.1:8000), digite uma pergunta e clique em **Obter orientação**. Use **Conferir evidências** para abrir a passagem usada e **Consultar fontes** para explorar a documentação. Encerre o servidor com Ctrl+C.

| Pergunta para experimentar | O que procurar na interface |
|---|---|
| Ao importar códigos 0007 e 0020 como texto como preservo os dígitos? | Definir o tipo da coluna durante a leitura. |
| Como validar muitos pedidos para um cliente no merge? | `many_to_one` ou `m:1`, com chave única à direita. |
| Preciso preservar os códigos 007 no CSV e somar a mesma coluna. Como importar? | Pedido de esclarecimento sobre identificador ou quantidade. |
| Como validar um merge m:1 no Polars? | Encaminhamento, pois a base cobre pandas. |

Os botões **Útil**, **Incorreta** e **Incompleta** registram a avaliação do rascunho no ambiente local. Em caso de erro, confirme que está na pasta do projeto e rode `python main.py doctor`. Veja também [operação](docs/OPERACAO.md).

## Arquitetura

### Preparação da documentação

As URLs oficiais estão em `configs/sources.json`. A ingestão coleta ou lê a entrada congelada, remove a navegação e divide o conteúdo em passagens. A distribuição inclui **30 páginas e 1.068 passagens**. Cada passagem registra origem e versão. O *hash* funciona como uma impressão digital do texto. O catálogo usa esse valor para conferir se a passagem recuperada continua idêntica à que foi revisada.

### Atendimento da pergunta

~~~mermaid
flowchart TD
    U["Pergunta no navegador"] --> T["Interpretar a operação"]
    T -->|Falta contexto| C["Pedir esclarecimento"]
    T -->|Fora da cobertura| H["Encaminhar para revisão"]
    T -->|Operação reconhecida| E["Verificar passagem oficial"]
    E -->|Passagem disponível| R["Mostrar rascunho e evidência"]
    E -->|Passagem ausente ou alterada| H
~~~

A interface envia a pergunta à API, o ponto de comunicação entre o navegador e o código Python. O pipeline coordena a consulta. O modo padrão usa regras de reconhecimento e um catálogo de orientações redigidas previamente. A API devolve a ação e, quando aplicável, a orientação com as fontes. A busca **BM25** compara termos da pergunta com termos das passagens na consulta de fontes.

### Por que o modo padrão mudou

**RAG** significa recuperação aumentada por geração. Na abordagem experimental, a busca recupera passagens e um modelo de linguagem redige uma resposta a partir delas. O projeto também comparou busca por palavras, busca por similaridade de significado e combinação de rankings. O experimento original localizou fontes relevantes, mas ainda produziu inversões de cardinalidade, nomes de colunas alterados e interpretações incorretas de dados ausentes.

A V2 introduziu orientações controladas e a V3 ampliou a cobertura. A V5 melhorou o reconhecimento de descrições do cotidiano, como pedidos por cliente. A V5.2 corrigiu a importação de códigos com zeros iniciais e incluiu a regressão na integração contínua. O catálogo dá previsibilidade para operações selecionadas. Novas operações e novas formas de fazer a mesma pergunta podem exigir novas regras e testes.

A geração experimental usa Ollama local e pode ser selecionada com `RAG_ANSWER_MODE=experimental_llm` após preparar os modelos com `python scripts/prepare_models.py`. Os pesos são baixados separadamente. Veja [arquitetura detalhada](docs/ARQUITETURA.md), [decisões](docs/DECISOES.md) e [experimentos](reports/EXPERIMENTOS.md).

## Avaliação

| Evidência | Resultado e interpretação |
|---|---|
| Auditoria pública de perguntas respondíveis | 8/20 na V3, 19/20 na V5 e 20/20 na V5.2 na seleção da orientação esperada. |
| Auditoria pública de triagem | 10/10 na V5.2 na escolha entre esclarecimento e encaminhamento. |
| Casos públicos adicionais | 10/10, cobrindo ordem das tabelas, ambiguidades, formato, versão e IDs com zeros iniciais. |
| Suíte Python | 75 testes aprovados na preparação local da V5.2. |
| Teste manual do autor | Três comportamentos conferidos na interface. O código foi preservado como texto na orientação, a junção recebeu a cardinalidade esperada e o conflito de requisitos gerou pedido de contexto. |
| Avaliação independente e estudo com usuários | Aguardam coleta. O ensaio do autor mostrou registro de quatro tentativas e ficha pendente de correção. |

Para conferir a execução em sua máquina:

~~~powershell
python main.py setup
python -m unittest discover -s tests -v
python scripts/benchmark_intencao.py
~~~

O benchmark confere a ação e o identificador da orientação esperada, caso a caso. Os 40 casos são públicos e foram usados no desenvolvimento. Uma divergência retorna código 1 no terminal. Confira [resultados](reports/benchmark_v52.json) e [respostas completas](reports/resultado_v52/responses.json).

Na avaliação histórica da geração livre, 49 de 60 casos receberam a ação esperada. A revisão assistida por IA aprovou integralmente 24 das 49 orientações emitidas. O protocolo reservado da versão atual prevê perguntas novas, revisão independente e uma comparação pareada de correção e tempo. Os critérios incluem 95% de respostas emitidas corretas e sustentadas, 70% de resolução, 90% de triagem e zero erros críticos observados. O estudo prevê pelo menos cinco pessoas e dez pares de tarefas, com meta de redução mediana de 20% no tempo e correção assistida igual ou superior. O tempo mostrado na interface mede processamento da consulta. O tempo da tarefa humana é coletado no piloto. [Relatório histórico](reports/RESULTADOS.md) · [Protocolo](docs/PILOTO.md) · [Como coletar](docs/COLETA.md)

## Mapa do repositório

A raiz é a pasta que contém este README. Nomes terminados em `/` representam pastas. Padrões como `case-*.json` representam arquivos de um mesmo tipo, um para cada pergunta. Arquivos `__init__.py` indicam pacotes Python.

### Raiz e configuração

| Arquivo | Para que serve |
|---|---|
| [.env.example](.env.example) | Exemplo de variáveis de ambiente para configurar serviços e caminhos. |
| [.gitattributes](.gitattributes) | Padroniza terminações de linha e marca arquivos comprimidos como binários. |
| [.gitignore](.gitignore) | Exclui dados locais, ambientes virtuais e arquivos temporários do Git. |
| [.github/workflows/tests.yml](.github/workflows/tests.yml) | Executa testes, avaliação e verificações em eventos do GitHub. |
| [.vscode/launch.json](.vscode/launch.json) | Configura atalhos de execução e depuração no VS Code. |
| [.vscode/settings.json](.vscode/settings.json) | Configura o editor para este projeto. |
| `README.md` | Guia de uso, metodologia, resultados e inventário. |
| [LICENSE](LICENSE) | Licença do código do projeto. |
| [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) | Créditos e condições dos materiais de terceiros. |
| [Iniciar.ps1](Iniciar.ps1) | Atalho PowerShell para iniciar a aplicação. |
| [main.py](main.py) | Entrada dos comandos da aplicação. |
| [config.json](config.json) | Configuração do corpus, busca e modelos. |
| [pyproject.toml](pyproject.toml) | Metadados do pacote e requisitos de Python. |
| [requirements.txt](requirements.txt) | Dependências declaradas para o núcleo. |
| [requirements-api.lock.txt](requirements-api.lock.txt) | Versões fixadas das dependências da API opcional. |

### Base e interface

| Arquivo | Para que serve |
|---|---|
| [assets/corpus.json.gz](assets/corpus.json.gz) | Passagens tratadas do pandas 2.2.3 e seus identificadores. |
| [assets/raw_markdown.json.gz](assets/raw_markdown.json.gz) | Documentação de entrada congelada para reconstrução. |
| [assets/vectors.json.gz](assets/vectors.json.gz) | Vetores para busca semântica e identificação da base correspondente. |
| [assets/manifest.json](assets/manifest.json) | Identificação do corpus e suas origens. |
| [configs/answer_contracts.json](configs/answer_contracts.json) | Regras, orientações redigidas e passagens exigidas. |
| [configs/sources.json](configs/sources.json) | Lista das fontes oficiais usadas na ingestão. |
| [ui/index.html](ui/index.html) | Página, estilos e JavaScript da interface. |

### Documentação e caderno

| Arquivo | Para que serve |
|---|---|
| [notebooks/01_crisp_dm.ipynb](notebooks/01_crisp_dm.ipynb) | Caderno que percorre as etapas do projeto. |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Componentes, responsabilidades e fluxo de dados. |
| [docs/DECISOES.md](docs/DECISOES.md) | Motivos e limites das escolhas técnicas. |
| [docs/DEMO_E_ENTREVISTA.md](docs/DEMO_E_ENTREVISTA.md) | Roteiro para demonstrar o projeto e explicar decisões. |
| [docs/GUIA_GITHUB.md](docs/GUIA_GITHUB.md) | Como publicar o projeto e conferir a primeira execução remota. |
| [docs/OPERACAO.md](docs/OPERACAO.md) | Inicialização, diagnóstico e manutenção. |
| [docs/PILOTO.md](docs/PILOTO.md) | Protocolo e critérios da avaliação independente. |
| [docs/REPRODUCAO.md](docs/REPRODUCAO.md) | Condições e comandos para reconstruir experimentos. |
| [docs/COLETA.md](docs/COLETA.md) | Procedimento de coleta com revisores e participantes. |
| [docs/piloto_campo/SESSAO.md](docs/piloto_campo/SESSAO.md) | Tarefas, condições experimentais e instruções de correção. |
| [docs/crisp_dm/01_negocio.md](docs/crisp_dm/01_negocio.md) | Problema, público e objetivos. |
| [docs/crisp_dm/02_dados.md](docs/crisp_dm/02_dados.md) | Origem e características da documentação. |
| [docs/crisp_dm/03_preparacao.md](docs/crisp_dm/03_preparacao.md) | Limpeza, segmentação e preparação do corpus. |
| [docs/crisp_dm/04_modelagem.md](docs/crisp_dm/04_modelagem.md) | Métodos de recuperação e resposta. |
| [docs/crisp_dm/05_avaliacao.md](docs/crisp_dm/05_avaliacao.md) | Métricas, conjuntos e critérios. |
| [docs/crisp_dm/06_implantacao.md](docs/crisp_dm/06_implantacao.md) | Distribuição, uso local e operação. |

### Conjuntos de teste

| Arquivo | Para que serve |
|---|---|
| [evaluation/cases.json](evaluation/cases.json) | Casos históricos com perguntas, referência e ação esperada. |
| [evaluation/REVIEW_RUBRIC.md](evaluation/REVIEW_RUBRIC.md) | Critérios para julgar as respostas. |
| [evaluation/splits.json](evaluation/splits.json) | Registro das divisões de desenvolvimento e teste. |
| [evaluation/source_audit.json](evaluation/source_audit.json) | Auditoria das fontes de referência. |
| [evaluation/user_study.csv](evaluation/user_study.csv) | Modelo de registro para estudo com participantes. |
| [evaluation/pilot_freeze.json](evaluation/pilot_freeze.json) | Hashes da versão vigente congelada para o piloto. |
| `evaluation/pilot_freeze*.json` | Registros de congelamento de versões anteriores. |
| `evaluation/regression_v*.json` | Casos públicos de regressão das versões anteriores. |
| [evaluation/auditoria_publica/casos.jsonl](evaluation/auditoria_publica/casos.jsonl) | Trinta perguntas públicas da auditoria. |
| [evaluation/inversao_v5.jsonl](evaluation/inversao_v5.jsonl) | Casos de inversão de tabelas, ambiguidade e versão. |
| [evaluation/identificadores_v52.jsonl](evaluation/identificadores_v52.jsonl) | Casos de códigos com zeros iniciais e situações que exigem triagem. |

### Comandos auxiliares

| Arquivo | Para que serve |
|---|---|
| [scripts/benchmark_intencao.py](scripts/benchmark_intencao.py) | Executa os 40 casos públicos da versão atual e sinaliza divergências. |
| [scripts/campo.py](scripts/campo.py) | Cronometra sessões, prepara correção cega e agrega o piloto. |
| [scripts/pilot.py](scripts/pilot.py) | Congela, executa e avalia perguntas privadas. |
| [scripts/check_release.py](scripts/check_release.py) | Verificação histórica de requisitos da distribuição. |
| [scripts/compare_retrieval.py](scripts/compare_retrieval.py) | Compara métodos de busca de passagens. |
| [scripts/compare_runs.py](scripts/compare_runs.py) | Compara resultados de execuções experimentais. |
| [scripts/demo_task.py](scripts/demo_task.py) | Executa uma tarefa sintética de CSV e junção com pandas 2.2.3 instalado. |
| [scripts/evaluate_release.py](scripts/evaluate_release.py) | Executa a avaliação da geração experimental. |
| [scripts/evaluate_v2.py](scripts/evaluate_v2.py) | Reexecuta avaliações históricas da V2. |
| [scripts/evaluate_v3.py](scripts/evaluate_v3.py) | Executa regressões da V3 e reprocessa casos históricos. |
| [scripts/prepare_models.py](scripts/prepare_models.py) | Prepara os modelos locais para experimentos. |
| [scripts/review_results.py](scripts/review_results.py) | Processa avaliações de respostas. |
| [scripts/smoke_real.py](scripts/smoke_real.py) | Exercita fluxos básicos da aplicação em execução. |
| [scripts/verify_installation.py](scripts/verify_installation.py) | Verifica a instalação isolada e o fluxo HTTP. |

### Código da aplicação

| Arquivo | Para que serve |
|---|---|
| `src/support_rag/**/__init__.py` | Identifica os pacotes Python da aplicação. |
| [src/support_rag/__init__.py](src/support_rag/__init__.py) | Identifica o pacote principal. |
| [src/support_rag/api/routes.py](src/support_rag/api/routes.py) | Definições compartilhadas das operações da API. |
| [src/support_rag/api/server.py](src/support_rag/api/server.py) | Servidor que disponibiliza a interface e a API. |
| [src/support_rag/bootstrap.py](src/support_rag/bootstrap.py) | Prepara o corpus e o índice local. |
| [src/support_rag/chunking/chunker.py](src/support_rag/chunking/chunker.py) | Divide os documentos em passagens. |
| [src/support_rag/cli.py](src/support_rag/cli.py) | Implementa os comandos do terminal. |
| [src/support_rag/controlled.py](src/support_rag/controlled.py) | Aplica regras de intenção e verifica a evidência catalogada. |
| [src/support_rag/embeddings/embedder.py](src/support_rag/embeddings/embedder.py) | Obtém vetores de texto para busca semântica. |
| [src/support_rag/evaluation/metrics.py](src/support_rag/evaluation/metrics.py) | Calcula métricas de busca e avaliação. |
| [src/support_rag/evaluation/review.py](src/support_rag/evaluation/review.py) | Valida e agrega registros de revisão. |
| [src/support_rag/evaluation/runner.py](src/support_rag/evaluation/runner.py) | Executa casos e registra resultados. |
| [src/support_rag/ingestion/cleaner.py](src/support_rag/ingestion/cleaner.py) | Remove ruídos de navegação e normaliza texto. |
| [src/support_rag/ingestion/loader.py](src/support_rag/ingestion/loader.py) | Carrega os documentos de entrada. |
| [src/support_rag/ingestion/markdown.py](src/support_rag/ingestion/markdown.py) | Interpreta a estrutura dos documentos Markdown. |
| [src/support_rag/llm/client.py](src/support_rag/llm/client.py) | Comunica-se com o modelo local. |
| [src/support_rag/llm/contracts.py](src/support_rag/llm/contracts.py) | Valida saídas e vincula citações às passagens. |
| [src/support_rag/monitoring/report.py](src/support_rag/monitoring/report.py) | Resume consultas, ações, erros e latência. |
| [src/support_rag/pipeline.py](src/support_rag/pipeline.py) | Coordena consulta, recuperação e resposta. |
| [src/support_rag/policy.py](src/support_rag/policy.py) | Regras compartilhadas de pré-condições e triagem. |
| [src/support_rag/prompts/planner.txt](src/support_rag/prompts/planner.txt) | Instruções de interpretação para o modo experimental. |
| [src/support_rag/prompts/template.txt](src/support_rag/prompts/template.txt) | Instruções para gerar a orientação experimental. |
| [src/support_rag/prompts/verifier.txt](src/support_rag/prompts/verifier.txt) | Instruções para revisar a saída experimental. |
| [src/support_rag/retrieval/retriever.py](src/support_rag/retrieval/retriever.py) | Implementa a busca lexical, semântica e híbrida. |
| [src/support_rag/settings.py](src/support_rag/settings.py) | Carrega e valida configuração. |
| [src/support_rag/utils/io.py](src/support_rag/utils/io.py) | Funções de leitura, gravação e hash. |
| [src/support_rag/vectordb/store.py](src/support_rag/vectordb/store.py) | Armazena, verifica e ativa versões do corpus. |

### Testes automatizados

| Arquivo | Para que serve |
|---|---|
| [tests/fixtures/documents.json](tests/fixtures/documents.json) | Documentos pequenos usados como entrada de testes. |
| [tests/test_campo.py](tests/test_campo.py) | Verifica coleta e cálculo do piloto com dados sintéticos. |
| [tests/test_cleaner.py](tests/test_cleaner.py) | Verifica limpeza de documentos. |
| [tests/test_controlled.py](tests/test_controlled.py) | Testa o vínculo entre orientação e passagem. |
| [tests/test_evidence_and_api.py](tests/test_evidence_and_api.py) | Verifica evidência e fluxos da API. |
| [tests/test_http_handlers.py](tests/test_http_handlers.py) | Testa os tratamentos do servidor HTTP. |
| [tests/test_release_policy.py](tests/test_release_policy.py) | Testa regras e condições da versão distribuída. |
| [tests/test_segmentation.py](tests/test_segmentation.py) | Confere a divisão da documentação em passagens. |
| [tests/test_system.py](tests/test_system.py) | Testa integrações e comportamentos do sistema. |

### Evidências e relatórios

| Arquivo | Para que serve |
|---|---|
| [reports/RESULTADOS.md](reports/RESULTADOS.md) | Resumo e limitações da avaliação histórica. |
| [reports/EXPERIMENTOS.md](reports/EXPERIMENTOS.md) | Histórico de experimentos e comparações. |
| [reports/auditoria_publica/LEIA-ME.md](reports/auditoria_publica/LEIA-ME.md) | Interpretação da primeira auditoria pública. |
| `reports/*/responses.json` | Saídas completas congeladas das rodadas de auditoria. |
| `reports/*/review.csv` | Ficha de correção associada à rodada, com campos para revisão. |
| `reports/**/case-*.json` | Resultado individual de cada caso experimental. |
| `reports/**/protocol.json` | Condições e parâmetros das rodadas experimentais. |
| `reports/**/results.json` | Resumo e denominadores das rodadas experimentais. |
| `reports/benchmark_v*.json` | Resultados por caso do benchmark público de cada versão. |
| `reports/clean_installation*.json` | Verificações de instalação e funcionamento em ambiente isolado. |
| `reports/validation_v*.json` | Resultados públicos e históricos das versões correspondentes. |
| `reports/tests_v*.txt` | Logs dos testes executados nas versões indicadas. |
| [reports/test_all.txt](reports/test_all.txt) | Log histórico de testes. |
| [reports/demo_task.json](reports/demo_task.json) | Saídas da demonstração com dados sintéticos. |
| [reports/development_retrieval.json](reports/development_retrieval.json) | Métricas da busca nos casos de desenvolvimento. |
| [reports/distribution_validation.json](reports/distribution_validation.json) | Verificações históricas da distribuição. |
| [reports/file_checksums.json](reports/file_checksums.json) | Hashes dos arquivos desta distribuição. |
| [reports/ingestion_verification.json](reports/ingestion_verification.json) | Verificação da preparação das fontes. |
| [reports/model_versions.json](reports/model_versions.json) | Identificação dos modelos usados nos experimentos. |
| [reports/package_manifest.json](reports/package_manifest.json) | Manifesto histórico da distribuição. |
| [reports/pilot_status.json](reports/pilot_status.json) | Estado registrado à época da preparação do piloto. |
| [reports/real_smoke.json](reports/real_smoke.json) | Resultado histórico da verificação funcional. |
| [reports/release_check.json](reports/release_check.json) | Resultado histórico das verificações de distribuição. |
| [reports/review_annotations.json](reports/review_annotations.json) | Anotações dos casos revisados. |
| [reports/semantic_review.csv](reports/semantic_review.csv) | Julgamento histórico, linha a linha, da correção e sustentação. |
| [reports/semantic_summary.json](reports/semantic_summary.json) | Resumo da revisão semântica histórica. |

A pasta `data/` é criada na primeira execução. Ela guarda o índice local e, se você realizar o piloto, os registros de sessão. O Git ignora essa pasta. Pesos de modelos experimentais são obtidos separadamente.

## Como o trabalho foi conduzido

CRISP-DM é um roteiro para organizar projetos de dados. Aqui ele conecta seis etapas. O problema define o que um atendente precisa decidir. A análise de dados examina as fontes oficiais. A preparação transforma as páginas em passagens. A modelagem compara busca e modos de orientação. A avaliação testa perguntas representativas do uso e cenários sintéticos de desenvolvimento. A implantação empacota a aplicação para rodar localmente e define como operá-la. Veja o [caderno do projeto](notebooks/01_crisp_dm.ipynb) e os documentos das seis etapas no mapa acima.

Para apresentar o projeto, comece pelo código `0007`, mostre a passagem que sustenta a orientação e depois acrescente a necessidade de somar a coluna. O pedido de contexto mostra como uma mesma entrada passa a exigir uma decisão diferente. Os [resultados públicos](reports/benchmark_v52.json) permitem reproduzir a evolução e o [protocolo de coleta](docs/COLETA.md) descreve como medir o benefício para usuários.

Para publicar, siga o [guia do GitHub](docs/GUIA_GITHUB.md). Consulte a [licença](LICENSE) e os [avisos de terceiros](THIRD_PARTY_NOTICES.md) para reutilização.
