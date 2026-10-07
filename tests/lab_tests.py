"""HTTP contracts for each cumulative VCL checkpoint (requires the running lab)."""

import os
import time
import unittest
import uuid
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

V = os.environ.get("V", "http://localhost:8081")
B1 = os.environ.get("B1", "http://localhost:8091")
B2 = os.environ.get("B2", "http://localhost:8092")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_):
        return None


def request(path, headers=None, method="GET", base=V):
    try:
        response = build_opener(NoRedirect).open(
            Request(base + path, headers=headers or {}, method=method), timeout=5,
        )
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


def fresh(path):
    return path + "?cb=" + uuid.uuid4().hex


def preserve_health(test, base):
    status = request("/healthz", base=base)[0]
    if status not in (200, 503):
        raise AssertionError("unexpected health status: %s" % status)
    restore = "/health/up" if status == 200 else "/health/down"
    test.addCleanup(request, restore, method="POST", base=base)
    test.assertEqual(request("/health/up", method="POST", base=base)[0], 200)


class BackendTests(unittest.TestCase):
    def test_backend1_is_reachable_through_varnish(self):
        status, headers, body = request(fresh("/static"))
        self.assertEqual(status, 200)
        self.assertIn(headers["X-Backend"], ("backend1", "backend2"))
        self.assertTrue(body.startswith(b"static from backend"))


class BackendDeclarationTests(unittest.TestCase):
    def test_first_backend_is_backend1(self):
        status, headers, body = request(fresh("/static"))
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Backend"], "backend1")
        self.assertEqual(body, b"static from backend1\n")


class RoutingTests(unittest.TestCase):
    def test_host_path_rewrite_and_headers_reach_backend1(self):
        url = fresh("/test1")
        for _ in range(2):
            status, headers, body = request(url, {
                "Host": "example.com", "X-Workshop": "spoof", "X-Remove-Me": "remove",
            })
            self.assertEqual(status, 200)
            self.assertTrue(body.startswith(b"nocache from backend1 "))
            self.assertEqual(headers["X-Backend"], "backend1")
            self.assertEqual(headers["X-Seen-Workshop"], "varnish-lab")
            self.assertEqual(headers["X-Seen-Remove-Me"], "")
            self.assertEqual(headers["X-Seen-URL"], url.replace("/test1", "/nocache", 1))
            self.assertEqual(headers["X-Workshop"], "varnish-lab")
            self.assertEqual(headers["X-Cache-Hits"], "0")
            self.assertEqual(headers["X-Cache"], "MISS")
            self.assertIsNone(headers["Server"])
            self.assertIsNone(headers["Location"])

    def test_other_hosts_and_similar_paths_are_not_rewritten(self):
        for path, host in (("/test1", "other.example"), ("/test10", "example.com"),
                           ("/test1/child", "example.com"), ("/test1", "example.com:8081")):
            self.assertEqual(request(fresh(path), {"Host": host})[0], 404)

    def test_exact_path_without_query_is_also_rewritten(self):
        status, headers, _ = request("/test1", {"Host": "example.com"})
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Seen-URL"], "/nocache")


class CacheTests(unittest.TestCase):
    def test_static_miss_then_hit_with_same_body(self):
        url = fresh("/static")
        status, headers, body = request(url)
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Cache"], "MISS")
        status, headers, cached = request(url)
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Cache"], "HIT")
        self.assertEqual(cached, body)
        self.assertIsNotNone(headers["Age"])

    def test_no_store_fetches_each_time(self):
        url = fresh("/nocache")
        first = request(url)
        second = request(url)
        self.assertEqual(first[0], 200)
        self.assertEqual(second[0], 200)
        self.assertEqual(second[1]["X-Cache"], "MISS")
        self.assertNotEqual(first[2], second[2])


class TTLVaryTests(unittest.TestCase):
    def test_public_mock_cookie_response_can_be_cached(self):
        url = fresh("/cookie")
        status, headers, body = request(url)
        self.assertEqual(status, 200)
        self.assertIsNone(headers["Set-Cookie"])
        status, headers, cached = request(url)
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Cache"], "HIT")
        self.assertEqual(cached, body)

    def test_vary_keeps_language_variants_separate(self):
        url = fresh("/vary")
        for lang, cache in (("en", "MISS"), ("pl", "MISS"), ("en", "HIT"), ("pl", "HIT")):
            status, headers, body = request(url, {"Accept-Language": lang})
            self.assertEqual(status, 200)
            self.assertEqual(headers["X-Cache"], cache)
            self.assertTrue(body.startswith(("lang=" + lang + " ").encode()))

    def test_request_cookie_removed_only_for_static(self):
        url = fresh("/static")
        request(url, {"Cookie": "session=private"})
        self.assertEqual(request(url, {"Cookie": "session=private"})[1]["X-Cache"], "HIT")
        url = fresh("/vary")
        for _ in range(2):
            status, headers, _ = request(url, {"Cookie": "session=private"})
            self.assertEqual(status, 200)
            self.assertEqual(headers["X-Cache"], "MISS")
        url = fresh("/static-private")
        for _ in range(2):
            status, headers, _ = request(url, {"Cookie": "session=private"})
            self.assertEqual(status, 404)
            self.assertEqual(headers["X-Cache"], "MISS")

    def test_time_expires_at_five_seconds_not_origin_ten(self):
        url = fresh("/time")
        first = request(url)
        self.assertEqual(first[0], 200)
        time.sleep(2)
        second = request(url)
        self.assertEqual(second[0], 200)
        self.assertEqual(second[2], first[2])
        time.sleep(3.5)
        # Default grace may return stale once while a background fetch completes.
        request(url)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            status, _, body = request(url)
            self.assertEqual(status, 200)
            if body != first[2]:
                return
            time.sleep(0.1)
        self.fail("/time remained fresh beyond the configured five-second TTL")


class GraceTests(unittest.TestCase):
    def test_foreground_origin_error_is_delivered_but_not_cached(self):
        url = fresh("/error")
        for _ in range(2):
            status, headers, body = request(url)
            self.assertEqual(status, 500)
            self.assertEqual(body, b"boom\n")
            self.assertEqual(headers["X-Cache"], "MISS")

    def test_stale_survives_outage_beyond_default_grace(self):
        preserve_health(self, B1)
        preserve_health(self, B2)
        url = fresh("/time")
        status, _, body = request(url)
        self.assertEqual(status, 200)
        self.assertEqual(request("/health/down", method="POST", base=B1)[0], 200)
        self.assertEqual(request("/health/down", method="POST", base=B2)[0], 200)
        time.sleep(16)  # Beyond 5s TTL + default 10s grace, inside configured 1m grace.
        for _ in range(2):
            status, headers, stale = request(url)
            self.assertEqual(status, 200)
            self.assertEqual(stale, body)
            self.assertEqual(headers["X-Cache"], "HIT")
            self.assertGreaterEqual(int(headers["Age"]), 15)
            time.sleep(0.2)
        for base in (B1, B2):
            self.assertEqual(request("/health/up", method="POST", base=base)[0], 200)
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            status, _, refreshed = request(url)
            self.assertEqual(status, 200)
            if refreshed != body:
                return
            time.sleep(0.2)
        self.fail("stale object was not refreshed after backend recovery")


class PurgeTests(unittest.TestCase):
    def test_purge_invalidates_variants_for_same_host_and_url_only(self):
        url = fresh("/vary")
        for host in ("example.com", "other.example"):
            for lang in ("en", "pl"):
                status, _, _ = request(url, {"Host": host, "Accept-Language": lang})
                self.assertEqual(status, 200)
                self.assertEqual(request(url, {"Host": host, "Accept-Language": lang})[1]["X-Cache"], "HIT")
        self.assertEqual(request(url, {"Host": "example.com"}, "PURGE")[0], 200)
        for lang in ("en", "pl"):
            status, headers, _ = request(url, {"Host": "example.com", "Accept-Language": lang})
            self.assertEqual(status, 200)
            self.assertEqual(headers["X-Cache"], "MISS")
            self.assertEqual(request(url, {"Host": "other.example", "Accept-Language": lang})[1]["X-Cache"], "HIT")


class PurgeDeniedTests(unittest.TestCase):
    """Run only with the rehearsal's deliberately restrictive ACL fixture."""

    def test_unauthorized_purge_is_denied_and_cached_object_survives(self):
        url = fresh("/static")
        self.assertEqual(request(url)[0], 200)
        self.assertEqual(request(url, method="PURGE")[0], 403)
        status, headers, _ = request(url)
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Cache"], "HIT")


class DirectorTests(unittest.TestCase):
    def test_balancing_failover_and_recovery(self):
        preserve_health(self, B1)
        preserve_health(self, B2)
        self.wait_for_backends({"backend1", "backend2"})
        self.assertEqual(request("/health/down", method="POST", base=B1)[0], 200)
        self.wait_for_backends({"backend2"})
        for _ in range(4):
            status, headers, _ = request(fresh("/nocache"))
            self.assertEqual(status, 200)
            self.assertEqual(headers["X-Backend"], "backend2")
        self.assertEqual(request("/health/up", method="POST", base=B1)[0], 200)
        self.wait_for_backends({"backend1", "backend2"})

    def wait_for_backends(self, expected):
        deadline = time.monotonic() + 12
        seen = set()
        while time.monotonic() < deadline:
            responses = [request(fresh("/nocache")) for _ in range(6)]
            seen = {headers["X-Backend"] for status, headers, _ in responses if status == 200}
            if all(status == 200 for status, _, _ in responses) and seen == expected:
                return
            time.sleep(0.25)
        self.fail("expected backends %r, observed %r" % (expected, seen))


class TroubleshootingTests(unittest.TestCase):
    def test_static_is_cacheable_after_repair(self):
        CacheTests.test_static_miss_then_hit_with_same_body(self)

    def test_user_agent_does_not_fragment_default_hash(self):
        url = fresh("/static")
        first = request(url, {"User-Agent": "A"})
        second = request(url, {"User-Agent": "B"})
        self.assertEqual(first[0], 200)
        self.assertEqual(second[0], 200)
        self.assertEqual(second[1]["X-Cache"], "HIT")
        self.assertEqual(second[2], first[2])

    def test_both_backends_are_in_the_pool(self):
        DirectorTests.wait_for_backends(self, {"backend1", "backend2"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
