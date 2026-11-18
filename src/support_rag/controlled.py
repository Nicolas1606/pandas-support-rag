"""Route requests to curated advice grounded in exact versioned passages."""
import re
import unicodedata
from support_rag.llm.contracts import attach_quotes, validate
from support_rag.utils.io import sha, canonical


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                   if not unicodedata.combining(c))


class ControlledAnswers:
    def __init__(self, catalog, chunks, version):
        self.catalog = catalog
        self.catalog_hash = sha(canonical(catalog))
        self.sources = {chunk['id']: chunk for chunk in chunks}
        self.version = version

    def answer(self, question, context, version):
        result = dict(action='handoff', message='', claims=[], sources=[],
                      answer_mode='controlled', model=None, method='contract_evidence',
                      catalog_sha256=self.catalog_hash, audit=None)

        def stop(action, reason, message):
            return dict(result, action=action, decision_reason=reason, message=message)

        query = normalize(question)
        request = normalize(question + ' ' + context)
        versions = re.findall(r'\bpandas\s+v?(\d+\.\d+(?:\.\d+)?)', request)
        if version and version.strip():
            versions.append(version.strip())
        if any(v != self.version for v in versions):
            return stop('handoff', 'unsupported_version',
                        f'Consulte a documentação da versão utilizada. Esta base cobre pandas {self.version}.')
        if re.search(r'\b(invente|revele|postgresql|kubernetes|prophet|spark|polars|xgboost|tensorflow|pytorch)\b|ignore.*(tarefa|instruc)', request):
            return stop('handoff', 'outside_scope', 'Encaminhe a solicitação. A base cobre apenas operações documentadas de pandas.')
        if re.search(r'\b(?:csv|read_csv|importar)\b', request) and re.search(
                r'zeros (?:a|na) esquerda|\b0\d+\b', request):
            numeric_use = re.search(r'\b(?:somar|soma|multiplicar|calcular|quantidade|quantidades)\b', request)
            unclear_role = not re.search(r'\b(?:codigos?|ids?|identificadores?|ceps?|matriculas?|texto)\b|zeros (?:a|na) esquerda', request)
            other_format = re.search(r'\b(?:excel|xlsx|parquet|json)\b', request)
            if other_format:
                return stop('handoff', 'file_format', 'Esta orientação de importação cobre arquivos CSV.')
            if numeric_use or unclear_role:
                return stop('clarify', 'column_role', 'Essa coluna identifica registros ou representa uma quantidade para cálculos? Os zeros iniciais precisam fazer parte do valor armazenado?')
        if re.search(r'\b(devo|melhor|correto|qual tipo|qual encoding|qual codificacao|posso substituir)\b|'
                     r'(?:meu|minha).*(?:duplic|estranh|nao abre|falh)|'
                     r'\b(?:numero ou texto|texto ou numero)\b', query):
            return stop('clarify', 'missing_context',
                        'Informe a operação, um exemplo mínimo e o resultado esperado. Inclua o significado dos campos quando a decisão envolver tipos ou ausentes.')
        if re.search(r'nao quero|em vez de|ao inves de|sem usar', query):
            return stop('clarify', 'alternative_operation', 'Confirme a operação desejada e a restrição.')
        # If the context introduces another supported operation, ask which one
        # to use instead of silently choosing based on the question alone.
        matches = [item for item in self.catalog if all(re.search(p, query) for p in item['patterns'])]
        if matches and context.strip():
            context_query = normalize(context)
            selected = {item['id'] for item in matches}
            if any(item['id'] not in selected and all(re.search(p, context_query) for p in item['patterns'])
                   for item in self.catalog):
                return stop('clarify', 'conflicting_context',
                            'A pergunta e o contexto indicam operações diferentes. Confirme qual deseja aplicar.')
        if len(matches) > 1:
            return stop('clarify', 'multiple_operations', 'Identifique uma operação e o resultado esperado.')
        if not matches and re.search(
                r'qual lado.*unic|tratar na\b|(?:converter|conversao).*texto inesperado|'
                r'(?:varios|muitos) \w+ por \w+', query):
            return stop('clarify', 'missing_semantics',
                        'Indique a operação e o resultado esperado. Em junções, qual tabela fica '
                        'à esquerda e em qual delas a chave deve ser única? Para valores ausentes '
                        'ou inválidos, qual valor deve ser preservado ou convertido?')
        if not matches:
            return stop('handoff', 'no_supported_contract', 'Consulte as fontes ou encaminhe para revisão. Não há orientação catalogada para esta formulação.')
        contract = matches[0]
        sources = []
        for ref in contract['evidence']:
            source = self.sources.get(ref['id'])
            if source is None or sha(source['text']) != ref['sha256']:
                return stop('handoff', 'missing_evidence', 'A passagem exigida está ausente ou mudou. Consulte a documentação.')
            sources.append(source)
        claims = [dict(text=contract['answer'], evidence_ids=[s['id'] for s in sources])]
        answer = dict(action='answer', message='', claims=claims)
        validate(attach_quotes(answer, sources), sources)
        return dict(result, **{**answer, 'sources': sources, 'contract_id': contract['id'],
                               'decision_reason': 'unique_contract_and_evidence'})
