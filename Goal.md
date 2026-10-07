## Goal

A hands-on Varnish Cache 6.0 onboarding for a new Dev/Ops employee, run as two guided sessions of about 2 hours each. The trainee works in a preconfigured, containerized lab (Podman/Docker Compose, Varnish 6.0.18 built from source, mock backends) and finishes able to configure, operate, monitor and troubleshoot Varnish in our setup.

## Scope (covered)

1. **Introduction**: what a reverse proxy cache is, benefits, use cases (slides)
2. **Setup**: containerized lab (`make up && make check`); native installs are out of scope
3. **Basic configuration**: VCL, backends, caching rules, testing (Ex1-2)
4. **Caching strategies**: Cache-Control and TTL, cookies, Vary, purge, grace, best practices (Ex2-4)
5. **Advanced**: backends + director, health probes, failover (Ex5-6); VMODs limited to `directors`
6. **Monitoring and tuning**: varnishstat/log/ncsa/top (Ex7); tuning as a mentor demo (Ex9)
7. **Troubleshooting**: broken-VCL exercise, cheat sheet, docs and community links (Ex8)

## Out of scope

Windows/macOS/Linux native installation, TLS termination, ESI, additional VMODs, deep performance tuning (further reading).

## Deliverables

`Dockerfile`/compose lab, `GUIDE.md`, `OUTLINE.md`, `MENTOR.md`, `PREFLIGHT.md`, `solutions/`, `broken/`, `verify.sh`, `slides.md`.
