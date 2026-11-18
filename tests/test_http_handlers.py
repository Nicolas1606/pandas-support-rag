import io, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_system import Base
from support_rag.api.server import make_server

class Socket:

    def __init__(self, raw):
        self.input = io.BytesIO(raw)
        self.output = bytearray()

    def makefile(self, *args, **kwargs):
        return self.input

    def sendall(self, data):
        self.output.extend(data)

class HandlerTests(Base):

    def call(self, path, body=None):
        server = make_server(self.c, port=0)
        try:
            payload = json.dumps(body).encode() if body is not None else b''
            verb = 'POST' if body is not None else 'GET'
            raw = f'{verb} {path} HTTP/1.0\r\nHost: localhost\r\nContent-Length: {len(payload)}\r\n\r\n'.encode() + payload
            sock = Socket(raw)
            server.RequestHandlerClass(sock, ('127.0.0.1', 1), server)
            head, data = bytes(sock.output).split(b'\r\n\r\n', 1)
            return (int(head.split()[1]), data)
        finally:
            server.server_close()

    def test_health_handler(self):
        status, body = self.call('/health')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['status'], 'alive')

    def test_search_handler(self):
        status, body = self.call('/search', {'question': 'merge validate'})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)['sources'])

    def test_invalid_handler(self):
        self.assertEqual(self.call('/search', {})[0], 422)

    def test_ui_handler(self):
        self.assertIn('Suporte pandas', self.call('/')[1].decode())

    def test_missing_feedback_execution(self):
        self.assertEqual(self.call('/feedback', {'request_id': 'a' * 32, 'rating': 'useful'})[0], 422)
