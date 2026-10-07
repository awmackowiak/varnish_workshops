# Mentor Notes

Follow `PLAN.md` and the exact 120-minute budgets in `OUTLINE.md`: session 1 Ex1-4, session 2 Ex5-10. Run `PREFLIGHT.md` before teaching. Scaffold edits and give tool-oriented hints; only one Ex9 diagnosis is mandatory. All three faults, a ban lab, conditional revalidation and deep thread tuning are optional follow-up.

## Lab State

- `make reset` restores valid `solutions/00-starter.vcl`: bootstrap `backend default` at `backend1:8080`. Ex1 replaces/renames it to backend1; never give trainees a no-backend config that cannot compile.
- Load cumulative checkpoints with `make solution N=04-ttl-vary` (session 2 start) or `make solution N=07-director` (final).
- Reload/reset does not flush cache or reset backend health. Use fresh query tokens; repeat an identical URL for a HIT. `make down && make up` resets cache and health but retains the VCL file.
- Prefer POST `/health/up` and `/health/down` over the retained `/toggle`; check `/healthz`. Verifier health-changing checks restore each backend's initial state even on failure, not necessarily both up.
- `V`, `B1`, `B2` default to `http://localhost:8081`, `http://localhost:8091`, `http://localhost:8092`. Host ports differ from container endpoints `backend1:8080`/`backend2:8080`.
- Inspect GET headers with `curl -sS -D - -o /dev/null`, not `curl -I`. `./verify.sh` accepts `1..7` and `9`; no argument checks all automated behavior on the final VCL. `8`/`10` are rejected, manual activities.

## Session 1

**Ex1, 20 minutes:** Explain hooks and `req`/`bereq`/`beresp`/`resp`, `if`, `==`, `~`, `set`, `unset`, `return`. User hooks fall through to built-in VCL unless they return; an empty hook is not pass-through. Show the backend declaration, reload, and a successful GET. Forgetting to reload is a common mistake.

**Ex2, 20 minutes:** Match exact `Host: example.com` and `/test1` with an optional query; `regsub(req.url, "^/test1", "/nocache")` preserves the query. Require backend1 even after the director is added. Test other Host, Host with port, `/test10` and `/test1/child` negatives. Set request and response `X-Workshop: varnish-lab`, remove request `X-Remove-Me`, remove response `Server`, and expose `X-Cache-Hits = obj.hits`. `/nocache` echoes `X-Seen-Workshop` and `X-Seen-Remove-Me`; inspect original `ReqURL`, rewritten `BereqURL` and `BereqHeader`. Keep `X-Backend` for the lab.

**Ex3, 20 minutes:** Compare MISS/HIT, `Age`, `X-Varnish` and `X-Cache-Hits`. `/nocache` is uncacheable; hit-for-miss remembers that fact, not a reusable body. HTTP `no-cache` means validate before reuse, whereas `no-store` forbids storage. Varnish 6.0 built-in policy makes backend `no-cache` responses uncacheable; do not present this as the general HTTP meaning.

**Ex4, 20 minutes:** TTL belongs in `vcl_backend_response`; set `/time` to 5s. Strip request Cookie only on `/static`, response Set-Cookie only on `/cookie`. Exact boundaries permit queries, not suffixes or child paths. This is public mock content, never a safe default for session data. Demonstrate language variants on `/vary`; high-cardinality Vary can fragment the cache. `Age` does not reset on reload; expiry may first serve stale during a refresh. Save `04-ttl-vary` for session 2.

## Session 2

**Ex5, 20 minutes:** TTL 5s, grace 1m and keep 30s apply only to `/time`. Warm a fresh URL before making backend1 sick; compare stale 200 with a cold foreground error. Abandon `>=500` only for `bereq.is_bgfetch`; foreground errors get TTL 0, uncacheable true, and delivery. Indiscriminate abandon hides foreground errors and confuses diagnosis. Keep supports retention for potential conditional revalidation, but the mock has no ETag support, so do not promise a 304 demo. Restore health and observe refresh/recovery.

**Ex6, 15 minutes:** Localhost plus RFC1918 PURGE ACL is lab-only, not production authorization guidance. Denial is 403. GET/PURGE must use the same Host, path and query/hash; forwarding headers do not change the ACL client address. Use the integration check or an outside-ACL source for denial evidence. Contrast exact-hash PURGE with bans without expanding into a full ban lab.

**Ex7, 20 minutes:** `import directors`, create the round-robin pool in `vcl_init`, add both backends and set `req.backend_hint`. Preserve the forced backend1 route. Probe `/healthz` with interval 2s, timeout 1s, window 3, threshold 2. Allow multiple intervals for state changes and inspect `backend.list`. Use `/nocache`, since cached responses hide balancing. Demonstrate down, backend2-only normal traffic, up, and rejoining. Forced backend1 routing intentionally does not fail over to backend2.

**Ex8, 15 minutes, manual:** Obtain evidence from varnishstat, request-grouped varnishlog, varnishncsa and varnishtop. Hit ratio is `cache_hit / (cache_hit + cache_miss)` when the denominator is nonzero; prefer counter deltas for the workload being discussed. `varnishlog -q` uses VSL query language, not grep. Ask the trainee to distinguish cached delivery from backend selection.

**Ex9, 20 minutes:** Choose one fault, allow time to gather evidence, then hint toward a tool rather than the answer. Each broken config is final VCL plus a single fault:

| Fault | Evidence | Repair |
|---|---|---|
| b1: `/static` TTL 0 block | `TTL` records, repeated MISS | Remove the block; anchoring the regex does not fix TTL 0 |
| b2: missing backend1 pool membership | Healthy backend1 but normal traffic only backend2 | Add backend1 to the pool |
| b3: User-Agent in hash | Different UA gives MISS for the same URL | Remove `hash_data(req.http.User-Agent)` |

`./verify.sh 9` checks these symptoms only, not every other setting. Remaining faults are follow-up work. Optional compile-error demonstration: use invalid `resp.StatusCode` instead of `resp.status`; reload fails and the previous active VCL remains in service. Repair the file and reload before continuing.

**Ex10, 10 minutes including wrap-up, mentor demo:** Lower `VARNISH_MEM`, generate unique public URLs and watch `MAIN.n_lru_nuked`/`MAIN.n_object`. Do not promise fixed counts. Evictions indicate pressure; sizing requires working-set/churn, hit-ratio and latency evidence. Deep thread tuning is follow-up. Restore normal memory with `make down && make up`; load the intended VCL and confirm health.

Prepare images before class. Use the same workload at normal storage and 1m,
capturing counters inside `make vsh` before/after each run:

```sh
# Host terminal; use a new demo token for every run.
demo="ex10-$RANDOM"
seq 1 6000 | xargs -P 8 -I{} curl -fsS -o /dev/null \
  "http://localhost:8081/static?demo=$demo-{}"
# Container terminal:
varnishstat -1 -f MAIN.n_lru_nuked -f MAIN.n_object
```

This demonstrates cache churn, not a production capacity recommendation. Do not
use a personalized endpoint or compare different workloads as a tuning result.

## Wrap-Up Questions

1. When is caching unsafe, and which built-in protections could an early return bypass?
2. How would you load/use/roll back a VCL safely, and what state survives reload?
3. Which evidence distinguishes cache fragmentation, storage pressure and a sick backend?
