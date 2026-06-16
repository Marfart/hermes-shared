"""Hydra HTTP test target - simple login form"""
from http.server import HTTPServer, BaseHTTPRequestHandler

VALID_PASS = "TestPass123!"

class LoginHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        params = {}
        for p in body.split('&'):
            if '=' in p:
                k, v = p.split('=', 1)
                params[k] = v
        
        pwd = params.get('pass', '')
        if pwd == VALID_PASS:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Login successful')
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Login failed')
    
    def log_message(self, format, *args):
        pass  # quiet

server = HTTPServer(('127.0.0.1', 3333), LoginHandler)
print(f"HTTP test server on 127.0.0.1:3333, password: {VALID_PASS}")
server.serve_forever()
