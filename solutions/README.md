# Solutions (Mentor Only)

Checkpoints are cumulative. Apply with `make solution N=<name without .vcl>`, e.g. `make solution N=02-routing`. `make reset` restores `00-starter.vcl`, a compilable bootstrap declaring `backend default` at `backend1:8080`. Ex1 replaces/renames it to backend1; a no-backend configuration is not a valid teaching starting point.

| Exercise | Checkpoint | Success Criteria |
|---|---|---|
| Starter | `00-starter.vcl` | Valid bootstrap, built-in policy and basic cache diagnostics |
| 1 Backend | `01-backend.vcl` | Declare backend1, reload, receive 200 from backend1 |
| 2 Routing | `02-routing.vcl` | Exact `Host: example.com`, `/test1` with optional query rewrites to `/nocache`; query preserved, backend1 forced, headers/logs checked |
| 3 Cache flow | `03-cache.vcl` | `/static` MISS then HIT; `/nocache` uncacheable; explain built-in Cache-Control behavior |
| 4 TTL and Vary | `04-ttl-vary.vcl` | `/time` TTL 5s; strip Cookie only on `/static`, Set-Cookie only on `/cookie`; language variants |
| 5 Grace | `05-grace.vcl` | `/time` grace 1m, keep 30s; abandon failed background refresh only; deliver uncacheable foreground errors with TTL 0 |
| 6 PURGE | `06-purge.vcl` | Localhost/RFC1918 lab-only ACL; unauthorized 403; invalidate matching Host/URL hash |
| 7 Director | `07-director.vcl` | Both backends in pool; probes interval 2s, timeout 1s, window 3, threshold 2; failover and recovery; preserve forced backend1 route |
| 8 Monitoring | No separate VCL | Manual evidence from varnishstat/log/ncsa/top |
| 9 Broken configs | Final VCL plus one fault per `broken/bN.vcl` | Repair TTL 0 block, missing backend1 membership or User-Agent hash input |
| 10 Tuning | No separate VCL | Mentor demo, evidence of storage pressure, restore normal lab |

Ex2 sets request/response `X-Workshop: varnish-lab`, removes request `X-Remove-Me` and response `Server`, and sets response `X-Cache-Hits` from `obj.hits`. Backend `/nocache` echoes request values in `X-Seen-Workshop` and `X-Seen-Remove-Me`. Negative Host/path tests must not rewrite. Endpoint rules allow queries but exclude suffixes/child paths; cookie stripping is safe only for this public mock content. Keep is conceptual: no mock ETag/conditional 304 support.

`./verify.sh N` accepts `1..7` and `9`. No argument runs all automated checks on `07-director.vcl`; manual `8`/`10` are rejected. Ex9 checks the three fault symptoms, not all other final settings. For b1, remove the offending TTL 0 block: merely anchoring the regex does not restore caching. One fault is mandatory in the session; others are optional follow-up.

Verifier overrides default to `V=http://localhost:8081`, `B1=http://localhost:8091`, `B2=http://localhost:8092`. Inspect GET headers with `curl -sS -D - -o /dev/null`, not HEAD. POST `/health/up` and `/health/down` are idempotent (`/toggle` retained); verifier checks restore initial health. `make test-lab` loads checkpoints sequentially and restores original VCL plus health.

Reload/reset does not flush cache or reset health. Use fresh query tokens to avoid old objects masking behavior, and the same Host/query for GET and PURGE. `make down && make up` fully resets cache/health but retains the VCL file. Optional invalid `resp.StatusCode` demo shows compile failure without replacing the previous active VCL; restore valid `resp.status` afterward.
