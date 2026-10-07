# Mentor Preflight Checklist

Run the day before and again 15 minutes before each session. `PLAN.md` defines scope and budgets; this checklist verifies readiness, not fixed test/performance counts.

## Machine

- [ ] Podman machine running on macOS (`podman machine start` if needed), or Docker available.
- [ ] Compose available (`podman-compose --version`); otherwise use the appropriate `COMPOSE` override, e.g. `make up COMPOSE="podman compose"`.
- [ ] Host Python 3.9+ available (`python3 --version`) for the verifier/tests; Node.js and npm available for `make slides`.
- [ ] Ports 8081, 8091 and 8092 free before startup (`lsof -i :8081 -i :8091 -i :8092`).
- [ ] First-build network access for Varnish 6.0.18 source and container images; pinned Marp build dependencies available.

## Automated Checks

- [ ] `make test` passes Python backend HTTP and verifier CLI tests, including invalid selectors and exit behavior.
- [ ] `make down && make up` completes; `make check` prints `varnish-6.0.18`.
- [ ] `make test-lab` passes integration checks, loading checkpoints sequentially, restoring the original file/active VCL and initial backend health, and discarding its temporary configurations. Cleanup attempts each restoration independently on failure.
- [ ] `make solution N=07-director`, then `./verify.sh` passes all end-state automated checks; do not run the no-argument suite against the starter.
- [ ] Selector checks agree with the docs: `1..7` and `9` accepted; `8`, `10` and invalid arguments rejected. Ex9 checks only the three broken-config symptoms.
- [ ] `make slides` regenerates `slides.html` from `slides.md` using pinned Marp; do not edit generated HTML or replace this with an unpinned `npx` invocation.

## Lab Smoke Test

- [ ] `make reset` restores `solutions/00-starter.vcl`; confirm with `diff varnish/vcl/default.vcl solutions/00-starter.vcl`.
- [ ] Starter declares bootstrap `backend default` at `backend1:8080`; Ex1 teaches replacing/renaming it to backend1, not compiling without a backend.
- [ ] GET `curl -sS -D - -o /dev/null http://localhost:8081/static` returns 200 with `X-Cache` and `X-Backend: backend1`; do not use HEAD.
- [ ] Ensure known healthy state with `curl -sS -X POST http://localhost:8091/health/up` and the same POST on port 8092; inspect both `/healthz` endpoints. `/toggle` is retained but not an idempotent recovery command.
- [ ] Rehearse exact Host/path routing with query preservation and negative cases; verify the forced backend1 route remains intact on the final director VCL.
- [ ] Rehearse warmed stale `/time` vs a cold foreground error, PURGE with matching Host/hash and unauthorized 403, and probe-driven failover/recovery.
- [ ] Confirm verifier overrides `V`, `B1`, `B2` default to `http://localhost:8081`, `http://localhost:8091`, `http://localhost:8092`. VCL uses container endpoints on port 8080.

## Materials

- [ ] Rendered slides display local topology/request-flow diagrams; check any external assets and documentation links before an offline session.
- [ ] Trainee has repo, editor and two terminals (HTTP requests and `make vsh`/logs).
- [ ] `GUIDE.md` available; solutions/mentor notes withheld until hints or recovery are needed.
- [ ] `OUTLINE.md` budgets total exactly 120 minutes per session, including breaks/recaps. Prepare one mandatory Ex9 fault, with others as follow-up.

## Between Activities

- [ ] Session 1 starts with `make reset`; session 2 starts with `make solution N=04-ttl-vary` and both backends up.
- [ ] Reload/reset does not empty cache or reset backend health. Use fresh cache-busters; retain one URL when testing a HIT. The verifier restores initial health, which may have been down.
- [ ] A full `make down && make up` resets cache and health but preserves the chosen on-disk VCL. Reload the intended checkpoint if required.
- [ ] Before Ex10: `make down && VARNISH_MEM=1m make up`; afterward `make down && make up`, restore the intended checkpoint and confirm health. No fixed eviction/object counts expected.
- [ ] If demonstrating invalid `resp.StatusCode`, confirm reload fails while the previous active VCL still serves, then restore valid `resp.status` and reload.

## Teaching Traps

- Built-in VCL still runs on fallthrough; early returns may bypass its safety checks.
- Varnish 6.0 treats backend `no-cache` as uncacheable by built-in policy; HTTP semantics permit storage but require validation. Do not conflate it with `no-store`.
- TTL expiry may serve stale while background refresh runs; cached delivery hides backend alternation.
- Cookie stripping applies only to exact public mock endpoints; grace/keep only to `/time`. Keep has no ETag/304 demonstration in this backend.
- Private-network PURGE access is lab-only; source-address denial cannot be demonstrated by spoofing an HTTP header.
