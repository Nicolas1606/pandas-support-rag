# Decisões

| Decisão | Evidência |
|---|---|
| Versão fixa | Evitar mistura de comportamento das APIs |
| Limpar navegação | Menus e links brutos apareciam no topo |
| Preservar parâmetros | validate era cortado antes de many_to_one |
| Condensar traceback | Pilhas internas dominavam o contexto |
| Comparar buscas | Embeddings superaram BM25 no diagnóstico |
| Deduplicar | API e wrapper repetiam a passagem |
| Gerar texto e IDs | Cópias de citações tinham erros de transcrição |
| Verificar suporte | IDs reais não impediram inversões |
| Não confiar cegamente no verificador | Foram observados falsos resultados |
| Interpretar a pergunta | Modelo menor inverteu cardinalidade mesmo com a definição |
| Comparar modelo maior | Falhas importantes do 4B persistiram |
| Pedir reprodução de sintomas | Evitar sugerir validação sem conhecer a relação |
| Preservar resultados negativos | Decisões precisam ser auditáveis |

Alterações foram orientadas pelo desenvolvimento. O teste final não foi usado para selecionar a configuração final.
