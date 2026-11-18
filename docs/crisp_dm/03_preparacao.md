# 3. Preparação

O pipeline conserva as fontes e gera dados derivados. Limpeza remove ações de navegação e normaliza links; segmentação preserva conjuntos de valores de parâmetros e condensa tracebacks longos. Mantém trechos de código úteis. A transformação é heurística e pode conservar resíduos de formatação.

Cada passagem tem ID, título, seção, URL, versão e hash. O ID do corpus depende do conteúdo canônico; a leitura verifica integridade. main.py rebuild reconstrói o snapshot distribuído e exige o mesmo ID: 81396567c3f64252.

Embeddings: embeddinggemma:latest via Ollama, vetores normalizados de 768 dimensões. O índice registra corpus_hash, modelo e digest dos pesos. Incompatibilidade bloqueia uso semântico e exige reindexação. Fonte e índice congelados permitem reproduzir sem coletar novamente.

Nova coleta por main.py ingest acessa as 30 URLs oficiais e cria uma candidata sem promover automaticamente. O snapshot HTML novo pode diferir do congelado Markdown; comparar e indexar antes de ativar. Dados de uso e ambientes são excluídos do Git.
