# 4. Modelagem

Baseline lexical BM25; busca por similaridade cosseno; fusão RRF dos rankings. Os três métodos foram executados nas mesmas famílias de desenvolvimento. O resultado dessa comparação está em reports/development_retrieval.json. A busca semântica foi escolhida pela recuperação de evidências; não se assume que a fusão seja sempre superior.

Geração local qwen3:8b. O qwen3:4b foi investigado e apresentou inversões e respostas incorretas mesmo com passagens relevantes. A mudança para 8B é uma decisão apoiada no desenvolvimento, sem garantia de ausência de erro.

Interpretação traduz a pergunta para recuperar documentação em inglês. Seleção de contexto deduplica e prioriza definições explicitamente solicitadas. O gerador produz orientação curta e IDs; o programa anexa os trechos reais do corpus. Um segundo passe do mesmo modelo verifica suporte e aderência à pergunta. Formato, IDs e trechos também são validados por código.

Limites: o planejador pode interpretar mal; o verificador compartilha vieses do gerador. Não é uma validação independente. IDs e citações corretos não provam a conclusão. Nenhuma resposta específica sobre merge foi codificada na aplicação. Regras de sintomas vagos apenas pedem contexto.
