"""Exercise the mock origin over HTTP, without importing its internals."""

import os
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class BackendHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.base = "http://127.0.0.1:%s" % port
        cls.process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "backend/app.py")],
            env=dict(os.environ, PORT=str(port), BACKEND_NAME="test-backend"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        cls.addClassCleanup(cls.stop_backend)
        for _ in range(100):
            if cls.process.poll() is not None:
                raise RuntimeError(cls.process.stderr.read().decode())
            try:
                with urlopen(cls.base + "/healthz", timeout=0.2):
                    return
            except URLError:
                time.sleep(0.05)
        raise RuntimeError("backend did not become ready")

    @classmethod
    def stop_backend(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)
        cls.process.stderr.close()

    def request(self, path, method="GET", headers=None):
        try:
            response = urlopen(Request(self.base + path, method=method, headers=headers or {}), timeout=3)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.headers, response.read()

    def test_static_get_has_success_and_cache_policy(self):
        status, headers, body = self.request("/static")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "max-age=60")
        self.assertEqual(body, b"static from test-backend\n")

    def test_head_has_get_headers_and_no_body(self):
        status, headers, body = self.request("/static", method="HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "max-age=60")
        self.assertEqual(int(headers["Content-Length"]), len(b"static from test-backend\n"))
        self.assertEqual(body, b"")

    def test_health_controls_are_idempotent_and_recover(self):
        self.addCleanup(self.request, "/health/up", "POST")
        for _ in range(2):
            self.assertEqual(self.request("/health/down", "POST")[0], 200)
            self.assertEqual(self.request("/healthz")[0], 503)
            self.assertEqual(self.request("/nocache")[0], 503)
        for _ in range(2):
            self.assertEqual(self.request("/health/up", "POST")[0], 200)
            self.assertEqual(self.request("/healthz")[0], 200)
            self.assertEqual(self.request("/nocache")[0], 200)

    def test_nocache_echoes_only_workshop_headers(self):
        status, headers, _ = self.request("/nocache", headers={
            "X-Workshop": "varnish-lab", "X-Remove-Me": "test", "Authorization": "secret",
        })
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Seen-Workshop"], "varnish-lab")
        self.assertEqual(headers["X-Seen-Remove-Me"], "test")
        self.assertIsNone(headers["Authorization"])

    def test_nocache_reports_received_url_in_lab_header(self):
        status, headers, _ = self.request("/nocache?test=preserved")
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Seen-URL"], "/nocache?test=preserved")
