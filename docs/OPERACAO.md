# Operação

## Pré-condições
Ollama, qwen3:8b e embeddinggemma:latest. Snapshot e índice são preparados automaticamente. /ready verifica disponibilidade, não qualidade.

## Falhas e resposta
- Modelo ausente: executar scripts/prepare_models.py.
- Índice incompatível ou digest alterado: reconstruir index para o corpus correto.
- Fonte inválida: reter a orientação e conservar evidências.
- Verificador reprovou: encaminhar com motivo no registro.
- Modelo ocupado: busy; aguardar.
- Timeout: conferir registros e recursos; não repetir cliques.
- Versão não coberta: encaminhar.
- Sintoma sem exemplo mínimo: esclarecer.
- Corpus corrompido: bloquear; restaurar snapshot confiável.

A interface mostra tempo e desabilita cliques simultâneos. Desconectar o navegador não garante cancelamento da computação no Ollama.

## Dados de operação
Logs contêm reformulação, conteúdo gerado, fontes, hashes e tempos. Podem conter informações do usuário: esta demonstração usa apenas conteúdo não sensível. Definir retenção antes de uso real.

## Atualização
Coletar candidata -> inspecionar -> indexar -> comparar regressões -> ativar com motivo -> reiniciar. Rollback: activate com ID anterior. O histórico preserva o motivo.

## Hardware
Windows, aproximadamente 16 GB de RAM, NVIDIA RTX 3060 Laptop. A inferência pode usar CPU/RAM e GPU conjuntamente. Não extrapolar os tempos para outro equipamento.
