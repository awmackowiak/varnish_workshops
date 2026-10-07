# Varnish 6.0 Hands-On Lab

Two guided 120-minute sessions: Ex1-4, then Ex5-10. `OUTLINE.md` gives the exact budgets from `PLAN.md`. Ask your mentor for hints before using solutions.

## Setup And Workflow

Run `make up && make check`; the version must be `varnish-6.0.18`. Edit `varnish/vcl/default.vcl`, apply with `make reload`, then run `./verify.sh N` for the current checkpoint. The verifier accepts `1..7` and `9`; no argument checks all automated behavior on the final VCL. `8` and `10` are manual and rejected as selectors.

Use these defaults for examples and verifier overrides:

```sh
export V="${V:-http://localhost:8081}"
export B1="${B1:-http://localhost:8091}"
export B2="${B2:-http://localhost:8092}"
curl -sS -D - -o /dev/null "$V/static"
```

This is a GET with headers shown and body discarded, not HEAD (`curl -I`). Use `curl -sS "$V/time"` when comparing bodies. `V` is Varnish; `B1`/`B2` are direct backend URLs. Inside the compose network, VCL connects to `backend1:8080` and `backend2:8080`, not host ports 8091/8092.

`make reset` restores `solutions/00-starter.vcl`, a valid bootstrap with `backend default` pointing to `backend1:8080`. It does not empty the cache or reset backend health. Neither does `make reload`. Use a fresh query token for a new test, then repeat the *same* URL to test a HIT. `make down && make up` clears cache and resets health; it still uses the current VCL file.

Health controls are idempotent POSTs to `/health/up` and `/health/down`; `/toggle` remains available but is unsuitable for reliably restoring a known state. Inspect `/healthz`. The verifier restores each backend's initial health, including on failure; it does not guarantee both were initially up.

## Ex1 - Backend And VCL Fundamentals (20 Min)

Replace/rename the starter's `backend default` declaration to `backend backend1` using `.host = "backend1"` and `.port = "8080"`. Do not remove all backend declarations: a no-backend config will not compile. Reload and request `/static`; success is a 200 response from backend1. Check: `./verify.sh 1`.

Trace the hooks: `vcl_recv` handles the client request (`req`), `vcl_backend_response` handles backend response/cache policy (`bereq`, `beresp`), and `vcl_deliver` handles the client response (`resp`). Learn `if`, `==` (equality), `~` (regex), `set`, `unset` and `return`. Use `resp.status`, not `resp.StatusCode`.

User VCL normally falls through to the built-in VCL. Empty hooks do not mean pass-through; built-in policy still applies. An explicit `return` can bypass the remaining built-in logic, including safety checks.

## Ex2 - Routing, Headers And Logs (20 Min)

For exact `Host: example.com` and path `/test1` (optionally followed by a query), force backend1 and rewrite internally with `regsub(req.url, "^/test1", "/nocache")`. Preserve the query. This is not a redirect. Even after Ex7 adds a director, this route must still choose backend1.

In `vcl_recv`, set `req.http.X-Workshop = "varnish-lab"` and unset `req.http.X-Remove-Me`. In `vcl_deliver`, set `resp.http.X-Workshop = "varnish-lab"`, unset `resp.http.Server`, and set `resp.http.X-Cache-Hits = obj.hits`. Keep lab diagnostics `X-Backend` and `X-Cache` visible.

```sh
curl -sS -D - -o /dev/null -H 'Host: example.com' -H 'X-Remove-Me: secret' "$V/test1?route=ex2"
curl -sS -D - -o /dev/null -H 'Host: other.example' "$V/test1?route=negative-host"
curl -sS -D - -o /dev/null -H 'Host: example.com' "$V/test10?route=negative-path"
```

Success: the positive request reaches backend1 `/nocache` with its query intact; negative Host/path cases do not rewrite. Also exclude `/test1/child` and a non-exact Host such as `example.com:8081`. `/nocache` echoes received headers as `X-Seen-Workshop` and `X-Seen-Remove-Me`: expect `varnish-lab` and no removed value. `X-Seen-URL` shows the received path and query. In `make vsh`, run `varnishlog -g request` before sending requests from the other terminal; compare original `ReqURL` with rewritten `BereqURL` and inspect `BereqHeader`. Check: `./verify.sh 2`.

## Ex3 - Flow And Cache-Control (20 Min)

```sh
u="$V/static?cb=ex3-$RANDOM"
curl -sS -D - -o /dev/null "$u"
curl -sS -D - -o /dev/null "$u"
curl -sS -D - -o /dev/null "$V/nocache"
curl -sS -D - -o /dev/null "$V/nocache"
```

Success: `/static` goes MISS then HIT; explain `Age`, `X-Cache-Hits` and the two IDs commonly seen in `X-Varnish` on a hit. `/nocache` remains uncacheable. Follow `VCL_call`, `TTL` and fetch records in the log. Check: `./verify.sh 3`.

HTTP `no-cache` permits storage but requires validation before reuse; `no-store` forbids storage. Varnish 6.0's built-in policy treats backend `no-cache` responses as uncacheable rather than implementing a conditional-validation cache. Distinguish that implementation choice from HTTP semantics. An uncacheable response may create a hit-for-miss marker, not a reusable body.

## Ex4 - TTL, Public Lab Cookies And Vary (20 Min)

Override `beresp.ttl = 5s` for `/time` only. Strip request `Cookie` for `/static` only and backend `Set-Cookie` for `/cookie` only. Match exact endpoint boundaries, e.g. `^/static([?].*)?$`, allowing queries but not `/static-private` or `/static/child`; apply the same pattern shape to `/cookie` and `/time`.

These endpoints contain public mock content. Never generalize cookie stripping to session or personalized content: removing cache protections can expose one user's data to another.

```sh
u="$V/static?cb=ex4-$RANDOM"
curl -sS -D - -o /dev/null -H 'Cookie: session=lab' "$u"
curl -sS -D - -o /dev/null -H 'Cookie: session=lab' "$u"
u="$V/cookie?cb=ex4-$RANDOM"
curl -sS -D - -o /dev/null "$u"
curl -sS -D - -o /dev/null "$u"
u="$V/vary?cb=ex4-$RANDOM"
curl -sS -D - -o /dev/null -H 'Accept-Language: pl' "$u"
curl -sS -D - -o /dev/null -H 'Accept-Language: en' "$u"
curl -sS -D - -o /dev/null -H 'Accept-Language: pl' "$u"
```

Success: the public cookie cases cache; `/vary` has a separate initial MISS per language and a HIT on repeating a variant. Compare `/time` bodies within and after its 5s TTL; grace may return stale while a refresh runs, so expiry need not change the first response body immediately. Check: `./verify.sh 4`. Save checkpoint `04-ttl-vary.vcl` for session 2.

## Ex5 - TTL, Grace And Keep (20 Min)

For `/time` only, retain TTL 5s and set `beresp.grace = 1m`, `beresp.keep = 30s`. TTL is freshness, grace allows stale delivery, and keep retains an expired object for possible conditional revalidation. The mock backend has no ETag support; keep is conceptual, not a demonstrated 304 workflow.

For errors `beresp.status >= 500`, `return (abandon)` only when `bereq.is_bgfetch` is true, protecting the good stale object from a failed background refresh. Foreground errors must be delivered with TTL 0 and `beresp.uncacheable = true`, not abandoned indiscriminately.

```sh
curl -sS -X POST "$B1/health/up"
u="$V/time?cb=ex5-$RANDOM"
curl -sS "$u"
curl -sS -X POST "$B1/health/down"
sleep 7
curl -sS -D - "$u"
curl -sS -D - -o /dev/null "$V/time?cb=ex5-cold-$RANDOM"
curl -sS -X POST "$B1/health/up"
```

Success: the warmed URL serves stale 200 during grace while backend1 is down; a cold URL delivers the foreground error without caching it. After recovery, observe a refreshed body. Always restore health, even if a command fails. Check: `./verify.sh 5`.

## Ex6 - Authorized PURGE (15 Min)

Add a PURGE ACL for localhost and RFC1918 private networks. This is **lab-only**, accommodating container source addresses; production needs narrowly authorized callers. Deny unauthorized clients with 403. PURGE targets the URL/hash, including Host, so use the same Host and query as the GET.

```sh
u="$V/static?cb=ex6-$RANDOM"
curl -sS -D - -o /dev/null -H 'Host: example.com' "$u"
curl -sS -D - -o /dev/null -H 'Host: example.com' "$u"
curl -sS -D - -o /dev/null -X PURGE -H 'Host: example.com' "$u"
curl -sS -D - -o /dev/null -H 'Host: example.com' "$u"
```

Success: MISS, HIT, successful PURGE, then MISS. Test denial from a source outside the ACL using the lab integration check or mentor setup; a local request or forged forwarding header does not prove denial. A ban is a different invalidation mechanism, not this exact-hash PURGE exercise. Check: `./verify.sh 6`.

## Ex7 - Director, Probes And Recovery (20 Min)

Declare backend2, import `directors`, and create a `directors.round_robin()` pool in `vcl_init` with both backend1 and backend2. Select it with `req.backend_hint` for normal traffic, but preserve Ex2's forced-backend1 route. Probe `/healthz` on both backends: interval 2s, timeout 1s, window 3, threshold 2.

Use uncached `/nocache` requests to observe both `X-Backend` values. POST `$B1/health/down`, wait for probes to mark it sick, and confirm normal traffic uses backend2. POST `$B1/health/up`, wait for healthy status, and observe backend1 rejoin. Inspect `varnishadm backend.list` in `make vsh`; allow several probe intervals rather than expecting an immediate transition. Check: `./verify.sh 7`. The verifier restores initial backend health.

## Ex8 - Monitoring (15 Min, Manual)

In `make vsh`, run `varnishstat`, `varnishlog -g request -q 'ReqURL ~ "static"'`, `varnishncsa` and `varnishtop -i ReqURL`. Generate GET traffic to repeated and unique URLs. Record a request trace, hit/miss counter deltas, an access-log entry and a frequent URL. Explain what each tool tells you. No separate VCL or automated selector.

## Ex9 - Broken-VCL Diagnosis (20 Min)

Each `broken/bN.vcl` is the final VCL plus one fault. Load one with `cp broken/b1.vcl varnish/vcl/default.vcl && make reload`. Diagnose with logs, counters and backend health, then edit the fault instead of copying a solution. One diagnosis is required within the session; the others are optional follow-up.

| File | Symptom | Success After Repair |
|---|---|---|
| `broken/b1.vcl` | `/static` never HITs | Repeated GETs reuse the object |
| `broken/b2.vcl` | Only backend2 serves normal traffic | Both healthy backends serve uncached requests |
| `broken/b3.vcl` | Cache split per User-Agent | A second UA shares the object |

`./verify.sh 9` checks these three symptoms, not all other end-state settings. Use fresh tokens so old objects cannot mask a repair. Optional compilation-error demo: change `resp.status` to invalid `resp.StatusCode`, run `make reload`, observe the compiler error and confirm the previous active VCL still serves; fix the typo and reload.

| Symptom | Evidence |
|---|---|
| Never HIT | `TTL`, `Set-Cookie`, `Vary`, hash inputs and `VCL_call` |
| 503 | `varnishadm backend.list`, `FetchError`, cold vs stale request |
| Wrong backend | `X-Backend`, `BackendOpen`, pool membership and routing |
| VCL will not load | Compiler error; previous active VCL remains in use |

## Ex10 - Tuning And Wrap-Up (10 Min, Mentor Demo)

Lower storage with `make down && VARNISH_MEM=1m make up`, request many unique `/static?u=...` URLs, and watch `varnishstat -1 -f MAIN.n_lru_nuked -f MAIN.n_object`. No fixed object/eviction counts are expected. Evictions are a storage-pressure signal, not an automatic sizing verdict; consider working set, churn, hit ratio and latency. Tune threads only with evidence.

Restore with `make down && make up` and reload the desired checkpoint if needed. No automated selector. Further reading: <https://varnish-cache.org/docs/6.0/>, <https://github.com/varnishcache/varnish-cache>, <https://varnish-cache.org/lists/>.
