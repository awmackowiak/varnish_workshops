---
marp: true
paginate: true
theme: default
---

# Varnish Cache 6.0 - Hands-on

Two sessions, ~2h each. Lab: `make up && make check` (Varnish 6.0.18)

Docs: <https://varnish-cache.org/docs/6.0/>

---

# Agenda

**Session 1:** intro, request flow, TTL, cookies/Vary, invalidation, grace
**Session 2:** backends + director, failover, monitoring, troubleshooting, tuning demo

---

# What Varnish is

- HTTP **reverse proxy cache** in front of the app
- Stores objects in memory (malloc storage)
- Behaviour fully programmable via VCL
- Our production: Varnish 6.0 LTS

Docs: <https://varnish-cache.org/docs/6.0/users-guide/intro.html>

---

# Reverse proxy

![w:860](img/reverse-proxy.svg)

---

# Why use it / use cases

- Fewer backend hits, lower latency
- Absorbs traffic spikes (flash sales, news peaks)
- Serves stale (grace) when the backend is down
- Central place for routing, headers, invalidation
- Good for: static assets, anonymous pages, API GETs
- Poor fit: per-user content, POST traffic, TLS (needs a terminator)

---

# Cache-Control: what it is

HTTP response header where the **origin tells caches how to treat the response**.

| Directive | Meaning |
|---|---|
| `max-age=60` | fresh for 60 s (any cache) |
| `s-maxage=60` | like max-age but only for shared caches (Varnish); wins over max-age |
| `no-store` | never store |
| `no-cache` | store, but revalidate before reuse |
| `private` | only the user's browser may cache (Varnish will not) |
| `public` | any cache may store |

Varnish sets TTL from `s-maxage`, then `max-age`, then `Expires`, else `default_ttl` (120 s). VCL can override with `beresp.ttl`.
Lab: `/static` (max-age=60), `/nocache` (no-store).
Docs: <https://varnish-cache.org/docs/6.0/users-guide/vcl-built-in-code.html>

---

# Request flow (simplified)

![w:860](img/request-flow.svg)

---

# Request flow (official Varnish diagrams)

![w:520](https://varnish-cache.org/docs/6.0/_images/cache_req_fsm.svg) ![w:360](https://varnish-cache.org/docs/6.0/_images/cache_fetch.svg)

Client side and backend side are separate threads.
Docs: <https://varnish-cache.org/docs/6.0/reference/states.html>
VCL reference: <https://varnish-cache.org/docs/6.0/reference/vcl.html>

---

# Ex1: First requests

`curl -sI localhost:8081/static` twice

- MISS then HIT, `Age`, `X-Varnish` (one ID = miss, two = hit)
- Why is `/nocache` never a HIT?

---

# Caching strategies

- TTL: from backend headers or `beresp.ttl` in VCL
- Cookies: `Set-Cookie` = not cacheable; strip carefully
- Vary: one variant per header value
- Invalidation: PURGE (one object), ban (pattern)
- Grace: serve stale while refreshing or backend sick

Best practices: cache only what is safe; normalise URLs/headers; never strip cookies globally; keep `Vary` low-cardinality; monitor hit ratio.
Docs: <https://varnish-cache.org/docs/6.0/users-guide/vcl-grace.html> , .../users-guide/purging.html , .../users-guide/vcl-hashing.html

---

# VCL headers: set and unset

```vcl
sub vcl_recv {
    set req.http.X-Forwarded-Proto = "http";
    if (req.url ~ "^/static") { unset req.http.Cookie; }
}
sub vcl_deliver {
    unset resp.http.Server;
    set resp.http.X-Cache-Hits = obj.hits;
}
```

- Objects: `req.http.*` (client request), `bereq.http.*` (to backend), `beresp.http.*` (from backend), `resp.http.*` (to client)
- Which one is writable depends on the subroutine (`resp` only in `vcl_deliver`/`vcl_synth`)
- Hide internals (`Server`, `Via`); never `unset req.http.Cookie` globally
- Docs: <https://varnish-cache.org/docs/6.0/reference/vcl.html#variables>

---

# TTL and grace

```vcl
sub vcl_backend_response {
    set beresp.ttl   = 5s;   # fresh: served as HIT
    set beresp.grace = 1m;   # stale: served while refetching / backend sick
}
```

- Object lifetime = `ttl` + `grace` (+ `keep`); `Age` counts from fetch
- Within TTL: HIT. After TTL, inside grace: stale served, one background refresh
- Backend down: stale kept serving until grace ends (needs a probe to know it is sick)
- Never cache errors: `if (beresp.status >= 500) { return (abandon); }`
- Docs: <https://varnish-cache.org/docs/6.0/users-guide/vcl-grace.html>

---

# Ex2-Ex4 (end of session 1)

Ex2 override TTL on `/time`
Ex3 strip cookie on `/cookie`, observe `/vary`
Ex3b `set`/`unset` request and response headers
Ex4 PURGE with ACL + grace

Break + recap

---

# Load balancing and failover (session 2)

- `probe` checks `/healthz`
- `directors.round_robin()` spreads traffic; sick backends skipped
- Ex5: add backend2 + director in one step
- Ex6: toggle backend1, watch failover (`varnishadm backend.list`)

Docs: <https://varnish-cache.org/docs/6.0/users-guide/vcl-backends.html> , <https://varnish-cache.org/docs/6.0/reference/vmod_directors.html>

---

# Monitoring

- `varnishstat`: hit ratio, n_lru_nuked, backend health
- `varnishlog -g request`: full transaction, VCL_call trace
- `varnishncsa`: access log
- `varnishtop -i ReqURL`: top URLs

Docs: <https://varnish-cache.org/docs/6.0/reference/varnishstat.html> , .../varnishlog.html , .../vsl-query.html

---

# Ex8: Troubleshooting - broken VCL

Three broken VCLs in `broken/`: `cp broken/b1.vcl varnish/vcl/default.vcl && make reload`
Find the cause with `varnishlog`, `varnishstat`, `varnishadm`, fix it, run `./verify.sh 8`.

Common issues: nothing is cached (cookies, TTL 0, Vary, hash), wrong backend, 503 (sick backend), VCL fails to compile.
Docs: <https://varnish-cache.org/docs/6.0/users-guide/troubleshooting.html>

---

# Tuning (demo)

- Storage size vs working set (`n_lru_nuked` > 0 = too small)
- Thread pools, `thread_pool_min/max`
- Measure first, tune second

Docs: <https://varnish-cache.org/docs/6.0/users-guide/performance.html> , .../reference/varnishd.html

---

# Documentation and community

- Docs 6.0: <https://varnish-cache.org/docs/6.0/>
- VCL reference: <https://varnish-cache.org/docs/6.0/reference/vcl.html>
- VMODs (std, directors): <https://varnish-cache.org/docs/6.0/reference/index.html>
- Source and issues: <https://github.com/varnishcache/varnish-cache>
- Mailing lists / community: <https://varnish-cache.org/lists/>
- Further: ESI, TLS termination, ban lurker, more VMODs
