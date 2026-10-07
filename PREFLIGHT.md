# Mentor pre-flight checklist

Run this the day before, and again 15 minutes before each session.

## Machine
- [ ] Podman machine running: `podman machine start` (Apple Silicon Mac)
- [ ] `podman-compose` installed (`podman-compose --version`); otherwise `make up COMPOSE="podman compose"`
- [ ] Ports 8081, 8091, 8092 are free (`lsof -i :8081 -i :8091 -i :8092`)
- [ ] Network access during the first build (downloads Varnish 6.0.18 source from varnish-cache.org and the Python and Debian base images)

## Lab
- [ ] `make down; make up` completes (first build takes a few minutes)
- [ ] `make check` prints `varnish-6.0.18`
- [ ] `varnish/vcl/default.vcl` equals the starter: `diff varnish/vcl/default.vcl solutions/01-request-flow.vcl`
- [ ] `curl -sI localhost:8081/static` shows `X-Cache` and `X-Backend: backend1`
- [ ] Both backends healthy: `curl -s localhost:8091/healthz localhost:8092/healthz`
- [ ] Dry run of the end state: `make solution N=05-backend-director && sleep 8 && ./verify.sh` shows `failed=0`, then `make reset`

## Materials
- [ ] Slides rendered (`npx @marp-team/marp-cli slides.md --html`); delete the old `slides.html` first
- [ ] Slide check: reverse-proxy and request-flow diagrams display; the two official Varnish diagrams load (they are hotlinked; download them if you are offline)
- [ ] Documentation links on the slides open
- [ ] Trainee has the repo, an editor, and 2 terminals (one for `curl`, one for `make vsh` / `varnishlog`)
- [ ] `GUIDE.md` handed over; `solutions/`, `MENTOR.md` and `verify.sh` kept out of the trainee's reach until needed (or tell them not to peek)

## Between sessions / exercises
- [ ] Reset VCL: `make reset`
- [ ] Make sure both backends are up (a trainee may leave backend1 toggled down): `curl -s -X POST localhost:8091/toggle` flips it, check with `/healthz`
- [ ] Session 2 start: begin from the Ex4 solution (`make solution N=04-purge-grace`) so Ex5 builds on a clean base
- [ ] Before the tuning demo (Ex9): `make down && VARNISH_MEM=1m make up`; afterwards `make down && make up`

## Known quirks
- Varnish serves a stale object once after TTL expiry (default grace 10s), so a changed `/time` body appears one request later
- A cached object hides load balancing: use `/nocache` for balancing demos
- The official Varnish diagram slide needs internet access
