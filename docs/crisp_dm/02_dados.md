# 2. Entendimento dos dados

30 páginas oficiais da documentação pandas 2.2.3. Lista em configs/sources.json; proveniência e hashes em assets/manifest.json. Snapshot de entrada congelado em assets/raw_markdown.json.gz, corpus derivado com 1.068 passagens. Licença de terceiros preservada.

Principais problemas observados: navegação misturada à explicação, links Markdown brutos, pilhas internas de erro, exemplos de cardinalidades diferentes e definição cortada entre blocos. A fonte ser oficial não garante que qualquer passagem responda à pergunta.

Benchmark: 120 cenários autorais, 60 famílias com duas formulações; famílias ímpares em desenvolvimento e pares em teste. CSV/Excel, tipos e joins; também ambiguidade, fora de escopo, premissas falsas e instruções adversariais. Referências auditadas com assistência de IA em evaluation/source_audit.json. Não houve revisão humana externa independente nem chamados reais.

Riscos: corpus pequeno e domínio restrito; dependência entre paráfrases; viés dos autores nas perguntas e referências; páginas oficiais podem mudar. Não usar contagem de documentos como medida de qualidade.
