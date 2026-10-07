# Mentor notes

Two sessions (~2h each): Ex1-4 then Ex5-9. Pre-session: `make up && make check`; confirm `./verify.sh` runs. Reset VCL: `make reset`; load any solution with `make solution N=04-purge-grace`.

## Ex1

- Point out two IDs in `X-Varnish` on a hit.
- `/nocache` (no-store) becomes hit-for-miss: object is remembered as uncacheable for a short time.
- Common mistake: forgetting `make reload` after editing.
- Ask: where would you see the VCL path a request took? (`varnishlog`, `VCL_call` lines.)

## Ex2

- Trainee may put TTL logic in `vcl_recv`; it belongs in `vcl_backend_response` (the object is created there).
- `Age` resets only on refetch, not on `make reload`.

## Ex3

- Varnish refuses to cache responses with `Set-Cookie` by default; also skips cache for requests with `Cookie`.
- Discuss risk: stripping Set-Cookie globally leaks a session to other users. Limit to known static paths.
- Vary: `Vary: *` or high-cardinality headers (User-Agent) destroy hit ratio.

## Ex3b

- `set`/`unset` work on `req.http.*`, `bereq.http.*`, `beresp.http.*`, `resp.http.*`; which one is allowed depends on the subroutine (e.g. `resp` only in `vcl_deliver`/`vcl_synth`).
- Common trap: unsetting `req.http.Cookie` globally, or `unset resp.http.Server` in `vcl_recv` (compile error).
- `X-Backend` is also a header the backend sets; stripping it hides topology in production but the labs need it, so only unset `Server`.

## Ex4

- Purge returns 405 from containers if ACL misses the podman network; the solution allows private ranges.
- Purge vs ban: purge is exact URL+hash, ban is a regex against cached objects.
- Grace demo: use `/time` (TTL 5s). Toggle backend1 down, wait 7s, request: stale 200 is served until the 1m grace ends.
- Known trap (found while testing): without the `beresp.status >= 500 -> abandon` rule, the backend's 503 gets cached for the TTL and replaces the good stale object. Good discussion point: never cache errors.
- Remind trainees to toggle backend1 back up.

## Ex5 (backend + director in one step)

- Common mistakes: `import directors;` missing; director created outside `vcl_init`; forgot `set req.backend_hint`; leaving the `default` backend declared and unused (harmless, but VCL warns nothing).
- The first backend declared is the default; the director overrides it per request.
- Use `/nocache` for balancing demos: cached objects will hide alternation.

## Ex6

- Probe window 3, threshold 2, interval 2s: ~4-6s to flip. Don't give up early.
- `varnishadm backend.list` shows Healthy/Sick.
- Ask: what if both are sick? (503; grace may still serve stale.)

## Ex7

- Hit ratio = cache_hit / (cache_hit + cache_miss). Generate load: `for i in $(seq 200); do curl -s -o /dev/null localhost:8081/static; done`.
- `varnishlog -q` takes VSL query language, not grep.

## Ex8 (troubleshooting, broken VCLs)

- b1: regex `"static"` matches too much and sets `beresp.ttl = 0s` -> never HIT. Clue: `TTL` line in varnishlog shows 0. Fix: remove the block or anchor the regex.
- b2: `pool.add_backend(backend1)` missing -> only backend2 ever serves. Clue: `X-Backend`, and `backend.list` shows backend1 healthy but unused. Fix: add it.
- b3: `vcl_hash` adds `User-Agent` -> one object per client. Clue: `Hash` lines in varnishlog, MISS for different UA. Fix: remove `hash_data(req.http.User-Agent)`.
- Let them struggle ~5 min each; hint towards the tool, not the answer.

## Ex9 (demo)

- Lower `VARNISH_MEM` (e.g. 1m), request many unique URLs, show `MAIN.n_lru_nuked` rising.
- Message: size storage to the working set; tune threads only with evidence.

## Wrap-up questions

1. When is caching unsafe? 2. How would you roll out a VCL change safely (`vcl.load`, `vcl.use`, rollback)? 3. What does a low hit ratio point to?
