# Exercise Outline

Two guided sessions of exactly 120 minutes, following `PLAN.md`. Lab: Varnish 6.0.18 at `http://localhost:8081`, direct backends at `http://localhost:8091` and `http://localhost:8092`. Container VCL uses `backend1:8080` and `backend2:8080`, not the host ports.

Edit `varnish/vcl/default.vcl`, then `make reload`. `make reset` restores the compilable `solutions/00-starter.vcl` with bootstrap `backend default` pointing to `backend1:8080`. Ex1 replaces/renames that declaration to `backend1`, rather than starting with an uncompilable no-backend config.

## Session 1

| Topic | Minutes | Activity / Checkpoint |
|---|---:|---|
| Intro, reverse proxy, topology, setup | 15 | `make up && make check`; GET smoke test |
| VCL fundamentals and backend1 (Ex1) | 20 | Hooks, built-in fallthrough, declare backend; `01-backend.vcl` |
| Routing, headers and logs (Ex2) | 20 | Exact Host/path rewrite, negative tests; `02-routing.vcl` |
| Flow and Cache-Control (Ex3) | 20 | MISS/HIT, uncacheable responses; `03-cache.vcl` |
| Break | 10 | |
| TTL, cookies and Vary (Ex4) | 20 | `/time` TTL 5s, safe endpoint boundaries, variants; `04-ttl-vary.vcl` |
| Recap and checkpoint | 15 | Explain a request trace; save Ex4 for session 2 |
| **Total** | **120** | |

## Session 2

| Topic | Minutes | Activity / Checkpoint |
|---|---:|---|
| Recap and restore checkpoint | 10 | `make solution N=04-ttl-vary`; ensure both backends up |
| TTL/grace/keep (Ex5) | 20 | Stale `/time`, background vs foreground errors; `05-grace.vcl` |
| PURGE (Ex6) | 15 | Lab-only ACL, matching Host/hash, denial 403; `06-purge.vcl` |
| Director, probes, failover and recovery (Ex7) | 20 | Both pool members, idempotent health controls; `07-director.vcl` |
| Break | 10 | |
| Monitoring (Ex8) | 15 | Manual evidence from four tools, no separate VCL |
| Troubleshooting (Ex9) | 20 | Repair one final-VCL-plus-one-fault config; others optional |
| Tuning demo and wrap-up (Ex10) | 10 | Mentor-led storage pressure demo; restore lab |
| **Total** | **120** | |

## Verification

`./verify.sh N` accepts `1` through `7` and `9`; selectors `8` and `10` are rejected because those activities are manual. No argument runs all automated checks on `07-director.vcl`. Ex9 checks the three fault symptoms, not every end-state setting. See `solutions/README.md` for cumulative checkpoints.

Verifier environment overrides: `V=http://localhost:8081`, `B1=http://localhost:8091`, `B2=http://localhost:8092` by default. Use GET header inspection (`curl -sS -D - -o /dev/null`), not HEAD. Reload does not flush cached objects or reset backend health; use fresh cache-busters. `make down && make up` is a full cache/health reset, not a replacement for restoring the desired VCL file.
