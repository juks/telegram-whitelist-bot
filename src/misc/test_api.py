#!/usr/bin/env python3
"""
Simple webserver to test ReaderApi class

Run:
  Without auth:
  
  python3 src/misc/test_api.py --port 8080

With auth:
  python3 src/misc/test_api.py --port 8080 --token secret123

Examples:
  curl 'http://localhost:8080/check-user/bob'
  curl 'http://localhost:8080/check-user?username=BillGates'
  curl -H 'Authorization: Bearer secret123' 'http://localhost:8080/check-user/JohnDoe'
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


KNOWN_USERS = {u.lower().lstrip('@') for u in ['gtjuks', 'bob', 'JohnDoe']}


class CheckUserHandler(BaseHTTPRequestHandler):
    configured_token = None

    def _send_json(self, obj, status_code=200):
        response_bytes = json.dumps(obj).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _unauthorized(self):
        self._send_json({'error': 'unauthorized'}, status_code=401)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path.startswith('/check-user'):
            if self.configured_token:
                auth_header = self.headers.get('Authorization')
                expected = f'Bearer {self.configured_token}'
                if auth_header != expected:
                    return self._unauthorized()

            username = self._extract_username(parsed)
            if username is None or username == '':
                return self._send_json({'error': 'username is required'}, status_code=400)

            normalized = username.lower().lstrip('@')
            allowed = normalized in KNOWN_USERS
            return self._send_json({'result': allowed})

        self._send_json({'error': 'not found'}, status_code=404)

    def log_message(self, format, *args):
        return

    def _extract_username(self, parsed):
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) >= 2 and parts[0] == 'check-user':
            return parts[1]

        params = parse_qs(parsed.query)
        if 'username' in params and len(params['username']) > 0:
            return params['username'][0]

        return None


def main():
    parser = argparse.ArgumentParser(description='Simple test API server with optional Bearer auth')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--token', default=None, help='If set, require Authorization: Bearer <token>')

    args = parser.parse_args()

    CheckUserHandler.configured_token = args.token

    server = HTTPServer((args.host, args.port), CheckUserHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()


