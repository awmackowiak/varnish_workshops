"""Mock backend for the Varnish lab (stdlib only).

Endpoints:
  /static            Cache-Control: max-age=60
  /nocache           Cache-Control: no-store
  /slow?ms=2000      slow response (default 2000 ms), max-age=30
  /cookie            sets a Set-Cookie header, max-age=30
  /vary              varies on Accept-Language
  /time              body changes every request (shows caching)
  /error             returns 500
  /healthz           health probe; returns 503 after POST /toggle
  POST /toggle       flip health (for failover exercise)
  POST /health/up    set healthy (idempotent)
  POST /health/down  set unhealthy (idempotent)
"""

import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

NAME = os.environ.get("BACKEND_NAME", "backend")
healthy = True


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, headers=None):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Backend", NAME)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        global healthy
        path = urlparse(self.path).path
        if path in ("/health/up", "/health/down"):
            healthy = path == "/health/up"
            return self._send(200, f"{NAME} healthy={healthy}\n")
        if path == "/toggle":
            healthy = not healthy
            return self._send(200, f"{NAME} healthy={healthy}\n")
        self._send(404, "not found\n")

    def do_GET(self):
        u = urlparse(self.path)
        p = u.path
        if p == "/healthz":
            return self._send(200 if healthy else 503, f"{NAME} healthy={healthy}\n")
        if not healthy and p != "/healthz":
            return self._send(503, f"{NAME} down\n")
        if p == "/static":
            return self._send(
                200, f"static from {NAME}\n", {"Cache-Control": "max-age=60"}
            )
        if p == "/nocache":
            return self._send(
                200,
                f"nocache from {NAME} {time.time()}\n",
                {
                    "Cache-Control": "no-store",
                    "X-Seen-Workshop": self.headers.get("X-Workshop", ""),
                    "X-Seen-Remove-Me": self.headers.get("X-Remove-Me", ""),
                    "X-Seen-URL": self.path,
                },
            )
        if p == "/slow":
            ms = int(parse_qs(u.query).get("ms", ["2000"])[0])
            time.sleep(ms / 1000)
            return self._send(
                200, f"slow {ms}ms from {NAME}\n", {"Cache-Control": "max-age=30"}
            )
        if p == "/cookie":
            return self._send(
                200,
                f"cookie from {NAME}\n",
                {"Set-Cookie": "session=abc123; Path=/", "Cache-Control": "max-age=30"},
            )
        if p == "/vary":
            lang = self.headers.get("Accept-Language", "none")
            return self._send(
                200,
                f"lang={lang} from {NAME}\n",
                {"Vary": "Accept-Language", "Cache-Control": "max-age=30"},
            )
        if p == "/time":
            return self._send(
                200, f"{time.time()} from {NAME}\n", {"Cache-Control": "max-age=10"}
            )
        if p == "/error":
            return self._send(500, "boom\n")
        self._send(404, "not found\n")

    def log_message(self, fmt, *args):
        print(f"[{NAME}] {fmt % args}", flush=True)


ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
