# Exercise outline (two sessions, ~2h each)

Lab: `make up` -> <http://localhost:8081> (Varnish 6.0.18), :8091/:8092 (backends direct).
Edit `varnish/vcl/default.vcl`, then `make reload`. Check with `./verify.sh N`.

## Session 1 (~2h)

| # | Time | Topic | Exercise |
|---|------|-------|----------|
| 0 | 15m | Intro + setup | slides: reverse proxy, Cache-Control, flow; `make up && make check` |
| 1 | 30m | VCL fundamentals | request flow, MISS/HIT, `/static`, `/nocache` |
| 2 | 20m | TTL | override TTL on `/time` |
| 3 | 25m | Cookies and Vary | strip Set-Cookie on `/cookie`, `/vary` |
| 4 | 20m | Invalidation, grace | PURGE ACL, grace |
| - | 10m | Break + recap | |

## Session 2 (~2h)

| # | Time | Topic | Exercise |
|---|------|-------|----------|
| 5 | 25m | Load balancing | ONE step: add backend2 + `directors.round_robin` + probe |
| 6 | 10m | Failover | toggle backend1, watch probe and traffic |
| 7 | 25m | Monitoring | varnishstat, varnishlog, varnishncsa, varnishtop |
| 8 | 30m | Troubleshooting | 3 broken VCLs in `broken/` |
| 9 | 15m | Tuning demo | mentor-led |
| - | 15m | Recap + docs/community | |

Solutions: `solutions/01-...05-*.vcl` (see `solutions/README.md`). Status: verified on 6.0.18, `./verify.sh` 12/12 with `05-backend-director.vcl` applied.
