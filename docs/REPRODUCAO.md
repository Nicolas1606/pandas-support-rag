# Reprodução

1. scripts/prepare_models.py.
2. main.py serve.
3. /ready e consulta.
4. unittest.
5. main.py rebuild.
6. scripts/verify_installation.py.
7. scripts/compare_retrieval.py.
8. scripts/evaluate_release.py --split test --output-dir reports/reproduction/test_01, somente para reprodução.

Temperatura zero e seed não garantem identidade em qualquer ambiente. Digests e ambiente estão nos relatórios.

assets/raw_markdown.json.gz é a entrada congelada; corpus.json.gz contém passagens e manifesto; vectors.json.gz contém vetores derivados. Pesos não estão incluídos.

ingest cria outra candidata a partir do HTML oficial. rebuild reconstrói o corpus distribuído. Alterar corpus, encoder ou parser exige nova avaliação.
