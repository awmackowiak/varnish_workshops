## Goal

A hands-on Varnish Cache 6.0.18 onboarding for a new Dev/Ops employee, delivered in two guided 120-minute sessions. The trainee uses a preconfigured Podman/Docker Compose lab with mock backends, configures and traces requests before learning caching, then adds resilience and operational diagnosis. `PLAN.md` is the authoritative plan.

## Scope

1. Introduction and setup: reverse proxy, topology, `make up && make check`.
2. VCL fundamentals and backend declaration (Ex1); Host/path routing, headers and logs (Ex2).
3. Request flow, MISS/HIT and Cache-Control (Ex3); TTL, public lab cookies and Vary (Ex4).
4. TTL/grace/keep and stale delivery (Ex5); authorized PURGE (Ex6).
5. Backend2, the `directors` VMOD, probes, failover and recovery (Ex7).
6. Monitoring with varnishstat/log/ncsa/top (Ex8, manual evidence).
7. Broken-VCL diagnosis (Ex9, one fault required; remaining faults optional).
8. Storage pressure and evidence-led tuning (Ex10, mentor demo).

Success means the trainee can trace a request, configure safe caching, distinguish lifetime windows, invalidate an object, observe failover/recovery and diagnose a fault with evidence. Automated checkpoints are Ex1-7 and Ex9; Ex8 and Ex10 are manual. No-argument `./verify.sh` checks all automated behavior against the final end-state VCL.

## Out Of Scope

Native installation on Windows/macOS/Linux, TLS termination, ESI, additional VMODs and deep performance tuning. A full ban lab, conditional 304 revalidation, all three troubleshooting faults and deep thread tuning are optional follow-up material, not requirements within four hours. `keep` is taught conceptually; the mock backend has no ETag/conditional revalidation support.

## Deliverables

`Dockerfile`/compose lab, `GUIDE.md`, `OUTLINE.md`, `MENTOR.md`, `PREFLIGHT.md`, cumulative `solutions/`, single-fault `broken/` configs, `verify.sh` and tests. `slides.md` is the presentation source; regenerate `slides.html` with the pinned Marp build rather than editing generated HTML.
