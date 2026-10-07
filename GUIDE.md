# Varnish 6.0 Hands-on Lab (participant guide)

Two sessions of ~2h. Session 1: Ex0-Ex4. Session 2: Ex5-Ex9.

Setup: `make up && make check` (must print varnish-6.0.18). Varnish: <http://localhost:8081>.
Backends direct: :8091 (backend1), :8092 (backend2). Edit `varnish/vcl/default.vcl`, apply with `make reload`, check with `./verify.sh N`.
Stuck? Ask your mentor for a hint. Start over with `make reset`.

Tip: `curl -sI localhost:8081/static` shows `X-Cache`, `Age`, `X-Varnish`, `X-Backend`.

## Ex0 - Setup (15 min, with slides)

`make up && make check`, then `curl -sI localhost:8081/static`. Read the headers.

## Ex1 - Request flow (30 min)

Read the starter VCL. Request `/static` twice. Explain MISS vs HIT, the two IDs in `X-Varnish`, and `Age`.
Then request `/nocache` twice: why is it never a HIT? Watch it in `varnishlog -g request` (`make vsh`).

## Ex2 - TTL (20 min)

`/time` is cached by backend `max-age=10`. In `vcl_backend_response`, override the TTL to 5s for `/time`. Verify with `Age`. Check: `./verify.sh 2`.

## Ex3 - Cookies and Vary (25 min)

`/cookie` sends `Set-Cookie`, so Varnish will not cache it. Strip the header for that path only; discuss why doing this globally is dangerous. Then call `/vary` with different `Accept-Language` headers (`curl -sI -H 'Accept-Language: pl' ...`) and see that each value is cached separately (MISS once per value).

## Ex4 - Invalidation and grace (20 min)

Add a PURGE method guarded by an ACL (return 405 otherwise). Add `beresp.grace = 1m`, and make `vcl_backend_response` abandon 5xx fetches (`if (beresp.status >= 500) { return (abandon); }`) so errors are never cached.
Test purge: `curl -X PURGE localhost:8081/static`.
Test grace: request `/time`, run `curl -X POST localhost:8091/toggle` (backend1 down), wait 7s (TTL is 5s), request `/time` again: you still get 200 from stale. Toggle backend1 back up when done.

## Ex5 - Add the second backend and a director (25 min)

One step: declare `backend2`, put both backends behind a `directors.round_robin()` created in `vcl_init`, and set `req.backend_hint = pool.backend()` in `vcl_recv`. Add a health probe on `/healthz` to both backends so sick ones are skipped.
Check with `/nocache` (uncached, shows `X-Backend` alternating): `./verify.sh 5`.

## Ex6 - Failover (10 min)

`curl -X POST localhost:8091/toggle` and wait ~6s. All traffic should go to backend2. Inspect with `varnishadm backend.list`. Toggle again and watch it recover. Check: `./verify.sh 6`.

## Ex7 - Monitoring (30 min)

Run `varnishstat` (hit ratio: `MAIN.cache_hit`, `MAIN.cache_miss`), `varnishlog -g request -q 'ReqURL ~ "static"'`, `varnishncsa`, `varnishtop -i ReqURL`. Generate load with a shell loop of curls.

## Ex8 - Troubleshooting: broken VCL (30 min)

Three faulty configs live in `broken/`. For each: `cp broken/bN.vcl varnish/vcl/default.vcl && make reload`, observe the symptom, diagnose with `varnishlog -g request`, `varnishstat`, `varnishadm backend.list`, then fix the VCL (do not copy from `solutions/`). Check: `./verify.sh 8`.
Symptoms to chase: (b1) `/static` is never a HIT; (b2) all traffic hits one backend; (b3) hits depend on the client.

Cheat sheet:

| Symptom | Look at |
|---|---|
| Never HIT | `varnishlog`: `TTL`, `Set-Cookie`, `Vary`, `Hash` lines |
| 503 | `varnishadm backend.list` (sick?), `FetchError` in log |
| Wrong backend | `X-Backend`, `BackendOpen`, director setup |
| VCL won't load | `varnishadm vcl.load` error text |
Community: <https://varnish-cache.org/docs/6.0/> , <https://github.com/varnishcache/varnish-cache> , <https://varnish-cache.org/lists/>

## Ex9 - Tuning demo (15 min, mentor-led)

Storage size (`VARNISH_MEM`), thread pools, and `MAIN.n_lru_nuked`.
Demo: `make down && VARNISH_MEM=1m make up`, then
`for i in $(seq 6000); do echo "url = \"localhost:8081/static?u=$i\""; done > /tmp/urls.txt; curl -s -o /dev/null -K /tmp/urls.txt --parallel`
and watch `varnishstat -1 -f MAIN.n_lru_nuked -f MAIN.n_object` (tested: ~2780 nuked, ~3200 objects kept at 1m). Restore with `make down && make up`.
