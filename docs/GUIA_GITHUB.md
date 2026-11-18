# Publicação

Crie um repositório vazio no GitHub e envie o conteúdo desta pasta. Não envie pesos, .venv ou logs pessoais. assets contém dados públicos derivados e é necessário para a reprodução.

Antes de publicar:
- Execute testes e abra a interface.
- Leia reports/RESULTADOS.md, especialmente falhas e revisão.
- Confira seu entendimento das decisões.
- Revise licença e ausência de segredos.
- O vídeo deve mostrar resultado observado e limites.

Com Git instalado:
~~~powershell
git init
git add .
git commit -m "Add end-to-end pandas support RAG project"
git branch -M main
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
~~~

A URL depende do repositório que você criar. O workflow fará sua primeira execução remota após o push; o repositório não declara CI remota como já executada.

Descrição sugerida:
Assistente RAG local para suporte pandas com corpus versionado, comparação de recuperação, citações rastreáveis, avaliação e operação conduzidas por CRISP-DM.

Use somente métricas do relatório final na postagem.
