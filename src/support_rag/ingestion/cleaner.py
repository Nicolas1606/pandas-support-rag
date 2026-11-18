"""Limpeza determinística de Markdown preservando texto de links e código."""
import re
from copy import deepcopy
LINK = re.compile(r'\[([^\]]+)\]\((?:[^()]|\([^()]*\))*\)')
def inline(text):
    text = re.sub(r'\[\\?#\]\([^\n]*?\)', '', text)
    for _ in range(3):
        changed = LINK.sub(r'\1', text)
        if changed == text:
            break
        text = changed
    text = re.sub(r'\\([_*\[\]#])', r'\1', text)
    return text.replace('**', '').replace('¶', '').strip()
def clean_document(document):
    doc = deepcopy(document)
    doc['title'] = inline(doc['title'])
    cleaned = []
    for block in doc['blocks']:
        section = inline(block['section'])
        text = block['text']
        # Preamble coletado antes do H1: menus, seletor de versões e navegação.
        if block['section'].endswith('.html') or block['section'] == doc['url']:
            continue
        lines = []
        fenced = False
        for line in text.splitlines():
            value = line.strip()
            if value.startswith('```'):
                fenced = not fenced
                lines.append(line)
                continue
            if not fenced and (
                value in ('Back to top', 'Copy to clipboard', 'On this page', 'Show Source', 'Next', 'Previous')
                or value.startswith('[Show Source]')
                or value.startswith('[Skip to ')
                or 'Link to this heading' in value and not value.startswith('#')
            ):
                continue
            lines.append(line if fenced else inline(line))
        text = '\n'.join(lines).strip()
        text = re.sub(r'\n{3,}', '\n\n', text)
        if not text or re.fullmatch(r'[`\s#|\-]+', text):
            continue
        cleaned.append(dict(block, section=section, text=text))
    doc['blocks'] = cleaned
    return doc
