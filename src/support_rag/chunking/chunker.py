"""Segmentação por parâmetro/parágrafo; diagnósticos longos não viram evidências isoladas."""
import re
from support_rag.utils.io import sha

PARAMETER = re.compile(r"^(?:[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s+(?:str|bool|int|float|dict|list|tuple|scalar|array|label|object|callable|DataFrame|Series|Index|file|path|hashable|sequence|mapping|iterable)\b", re.I)
BOUNDARY = re.compile(r"^(Returns|Raises|See also|Notes|Examples|Parameters)\s*:?", re.I)

def trim_tracebacks(text):
    def replace(match):
        code = match.group(0)
        if 'Traceback (most recent call last)' not in code and not re.search(r'^\s*File .+, line |^\s*File .+:\d+, in ', code, re.M):
            return code
        errors = re.findall(r"^([A-Za-z_][\w.]*Error: .+)$", code, re.M)
        return "\nExemplo com exceção; pilha interna omitida.\n" + (errors[-1] if errors else '')
    return re.sub(r'```[^\n]*\n.*?```', replace, text, flags=re.S)

def split_text(text, limit):
    if limit < 100:
        raise ValueError('Limite pequeno demais')
    while len(text) > limit:
        cut = text.rfind('\n\n', 0, limit)
        if cut < limit // 3:
            cut = text.rfind('\n', 0, limit)
        if cut < limit // 3:
            cut = text.rfind(' ', 0, limit)
        if cut < limit // 3:
            cut = limit
        yield text[:cut].strip()
        text = text[cut:].lstrip()
    if text:
        yield text.strip()

def semantic_units(text):
    groups, current, label = [], [], ''
    fenced = False
    def flush():
        if current:
            groups.append((label, '\n'.join(current).strip()))
            current.clear()
    for line in trim_tracebacks(text).splitlines():
        stripped = line.strip()
        if stripped.startswith('```'):
            fenced = not fenced
        if not fenced and (PARAMETER.match(stripped) or BOUNDARY.fullmatch(stripped)):
            flush()
            label = stripped
        current.append(line)
    flush()
    return groups

def chunk_document(doc, limit=900):
    chunks = []
    for number, block in enumerate(doc['blocks']):
        for unit, (label, text) in enumerate(semantic_units(block['text'])):
            if not text:
                continue
            # Continuação de parâmetro repete a assinatura, não uma afirmação inventada.
            prefix = label + '\n' if label and PARAMETER.match(label) else ''
            pieces = list(split_text(text, max(100, limit-len(prefix))))
            for part, piece in enumerate(pieces):
                content = prefix + piece if part and prefix else piece
                chunks.append({
                    'id': sha(doc['url']+str(number)+str(unit)+str(part)+content)[:24],
                    'document_url':doc['url'],
                    'source_url':doc['url']+('#'+block['anchor'] if block.get('anchor') else ''),
                    'title':doc['title'], 'section':block['section']+(' — '+label if label else ''),
                    'text':content, 'kind':block['kind'], 'version':doc['version'],
                    'continued':len(pieces)>1, 'block_id':number, 'unit':unit, 'part':part,
                    'content_sha256':sha(content)
                })
    return chunks
