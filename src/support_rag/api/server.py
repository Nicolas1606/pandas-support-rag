import json, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from support_rag.utils.io import save
from support_rag.pipeline import Pipeline
from support_rag.settings import settings

def make_server(config, host='127.0.0.1', port=8000):
    from support_rag.bootstrap import bootstrap
    bootstrap(config)
    if host not in ('127.0.0.1', 'localhost'):
        raise ValueError('Servidor restrito ao computador local')
    pipeline = Pipeline(config)

    class Handler(BaseHTTPRequestHandler):

        def respond(self, code, value, kind='application/json'):
            raw = (json.dumps(value, ensure_ascii=False) if kind == 'application/json' else value).encode()
            self.send_response(code)
            self.send_header('Content-Type', kind + '; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path == '/':
                return self.respond(200, (Path(config['root']) / 'ui/index.html').read_text(encoding='utf-8'), 'text/html')
            if self.path == '/health':
                return self.respond(200, {'status': 'alive'})
            if self.path == '/favicon.ico':
                return self.respond(204, '', 'text/plain')
            if self.path == '/stats':
                from support_rag.monitoring.report import report
                return self.respond(200, report(config['data_dir']))
            if self.path == '/ready':
                try:
                    llm = pipeline.controlled is None and pipeline.llm.ready()
                except Exception:
                    llm = False
                return self.respond(200, {'retrieval': True, 'generation': llm, 'answer_mode':config.get('answer_mode','experimental_llm'), 'semantic': (pipeline.store.path(pipeline.manifest['corpus_id'])/'vectors.json').exists(), 'default_method': config.get('default_method','bm25'), 'corpus_id': pipeline.manifest['corpus_id']})
            self.respond(404, {'error': 'not_found'})

        def do_POST(self):
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 20000:
                    return self.respond(413, {'error': 'body_too_large'})
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError('Objeto esperado')
                if self.path == '/feedback':
                    rid = body.get('request_id', '')
                    if not isinstance(rid, str) or len(rid) != 32 or any((c not in '0123456789abcdef' for c in rid)):
                        raise ValueError('ID inválido')
                    if not (Path(config['data_dir']) / 'logs' / f'{rid}.json').exists():
                        raise ValueError('Execução desconhecida')
                    if body.get('rating') not in ('useful', 'incorrect', 'incomplete'):
                        raise ValueError('Feedback inválido')
                    save(Path(config['data_dir']) / 'feedback' / f'{uuid.uuid4().hex}.json', {'request_id': rid, 'rating': body['rating']})
                    return self.respond(201, {'saved': True})
                question = body.get('question')
                context = body.get('context', '')
                method = body.get('method', config.get('default_method','bm25'))
                if self.path == '/search':
                    return self.respond(200, {'sources': pipeline.search(question, context, method)})
                if self.path == '/answer':
                    return self.respond(200, pipeline.answer(question, context, body.get('version'), method))
                self.respond(404, {'error': 'not_found'})
            except (ValueError, TypeError):
                self.respond(422, {'error': 'invalid_input'})
            except Exception as exc:
                self.respond(503, {'error': 'service_unavailable', 'type': type(exc).__name__})
    return ThreadingHTTPServer((host, port), Handler)

def serve(port=8000):
    server = make_server(settings(), port=port)
    print(f'Abra http://127.0.0.1:{port}')
    server.serve_forever()
