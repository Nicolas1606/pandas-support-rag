# 6. Implantação e monitoramento

Implantação realizada: serviço HTTP no computador local com interface web. Execução principal pela biblioteca padrão; adaptador FastAPI opcional, com dependências congeladas. Ollama fornece geração e embeddings. Pesos ficam fora do Git.

A distribuição prepara snapshot e índice automaticamente. scripts/verify_installation.py executa em dados temporários, sobe HTTP e verifica disponibilidade, interface e três fluxos com modelo real. Testes de software cobrem entradas inválidas, fontes, falhas, integridade e rollback.

Cada orientação registra request_id, versão do corpus, modelos, hashes de prompts, interpretação, fontes, verificação, uso e latência. Feedback está ligado à consulta. Painel operacional mostra volume e tempos; não estima acurácia factual de uso real.

Atualização: coletar candidata, inspecionar, indexar, comparar regressões, ativar com motivo, reiniciar. Rollback ativa corpus anterior. O corpus em uso não é substituído por uma coleta parcial.

A implantação é local e demonstrável. Não houve hospedagem pública, teste de carga empresarial, autenticação multiusuário ou observação de produção comercial. O uso previsto mantém revisão humana de cada orientação. Runbook em docs/OPERACAO.md.
