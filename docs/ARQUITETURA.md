# Arquitetura e contratos

Validação -> pré-condição de contexto -> interpretação -> recuperação -> seleção/deduplicação -> geração -> passagens reais -> validação -> verificador -> resposta e log.

A interpretação reformula em inglês para reduzir ambiguidade. Ela é registrada e também pode errar. O gerador fornece texto e IDs; o programa anexa o conteúdo real. Isso evita erros de transcrição, mas não demonstra sustentação semântica.

O verificador usa LLM para suporte, aderência à pergunta e idioma. Pode aprovar conteúdo incorreto ou reter conteúdo correto. Os experimentos registram esse risco.

## API
GET /, /health, /ready, /stats, /favicon.ico.
POST /search, /answer, /feedback.
FastAPI acrescenta /docs e /openapi.json.

Query: question 3–3000 caracteres; context até 3000; version opcional; method bm25/dense/hybrid.
Feedback: request_id existente e rating useful/incorrect/incomplete.
Saída: answer, clarify, handoff ou error. Falha técnica não deve ser contada como encaminhamento semântico.

## Proporcionalidade
Registro e vetores locais são suficientes para a base pequena. Identificadores e hashes ligam fonte, corpus e encoder. Candidata precisa de ativação explícita e permite rollback.

Não há autenticação corporativa, SLA multiusuário, execução de código arbitrário ou persistência distribuída. O servidor fica em localhost e não recebe arquivos do usuário.
