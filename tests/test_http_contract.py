"""Do not hide a Varnish redirect behind the final origin response."""

import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from lab_tests import request


class RedirectHTTPTests(unittest.TestCase):
    def test_contract_client_observes_redirect_without_following_it(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302 if self.path == "/redirect" else 200)
                if self.path == "/redirect":
                    self.send_header("Location", "/final")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        status, headers, _ = request("/redirect", base="http://127.0.0.1:%s" % server.server_port)
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/final")
