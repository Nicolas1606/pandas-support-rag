from html.parser import HTMLParser
from urllib.request import Request, urlopen
from datetime import datetime, timezone
from support_rag.utils.io import sha
BASE = 'https://pandas.pydata.org/pandas-docs/version/2.2.3/'

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.capture = None
        self.parts = []
        self.blocks = []
        self.section = ''
        self.anchor = ''
        self.title = ''
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('main', 'article'):
            self.active = True
        if not self.active:
            return
        if tag in ('script', 'style', 'nav'):
            self.skip += 1
        if self.skip:
            return
        if tag == 'section' and attrs.get('id'):
            self.anchor = attrs['id']
        if tag in ('h1', 'h2', 'h3', 'h4', 'p', 'pre', 'dt', 'dd', 'table', 'li') and self.capture is None:
            self.capture = tag
            self.parts = []
        elif self.capture and tag in ('br', 'tr', 'td', 'th', 'p', 'li'):
            self.parts.append('\n' if tag != 'td' else ' | ')

    def handle_data(self, data):
        if self.active and self.capture and (not self.skip):
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav') and self.skip:
            self.skip -= 1
            return
        if self.capture == tag:
            text = ''.join(self.parts).strip().replace('¶', '')
            if tag.startswith('h'):
                self.section = text
                if tag == 'h1':
                    self.title = text
            elif text:
                self.blocks.append({'section': self.section, 'anchor': self.anchor, 'kind': tag, 'text': text})
            self.capture = None
            self.parts = []
        if tag == 'main':
            self.active = False

def parse_html(html):
    p = Parser()
    p.feed(html)
    if not p.blocks:
        raise ValueError('Página sem conteúdo reconhecível')
    return (p.title, p.blocks)

def fetch(relative, timeout=40):
    if '..' in relative or relative.startswith('/') or '://' in relative:
        raise ValueError('Fonte inválida')
    url = BASE + relative
    with urlopen(Request(url, headers={'User-Agent': 'PortfolioResearch/0.2'}), timeout=timeout) as r:
        if not r.url.startswith(BASE):
            raise ValueError('Redirecionamento fora da versão')
        raw = r.read(8000001)
        if len(raw) > 8000000:
            raise ValueError('Documento grande demais')
    html = raw.decode('utf-8')
    title, blocks = parse_html(html)
    return {'url': url, 'title': title, 'version': '2.2.3', 'blocks': blocks, 'sha256': sha(html), 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'raw_html': html}
