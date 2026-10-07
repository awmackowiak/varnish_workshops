# Solutions (mentor only)

Each file is cumulative: it contains the previous exercise's solution plus the new change.
Apply with: `make solution N=<name without .vcl>` (e.g. `make solution N=02-ttl`). Reset to the starter with `make reset`.

| Exercise | File | Notes |
|---|---|---|
| Ex1 Request flow | `01-request-flow.vcl` | No code change; identical to the starter VCL |
| Ex2 TTL | `02-ttl.vcl` | `beresp.ttl = 5s` for `/time` |
| Ex3 Cookies, Vary | `03-cookies-vary.vcl` | `unset beresp.http.Set-Cookie` for `/cookie` only |
| Ex4 Purge, grace | `04-purge-grace.vcl` | PURGE ACL, `beresp.grace = 1m`, abandon 5xx |
| Ex5 Backend + director | `05-backend-director.vcl` | backend2, probe, `directors.round_robin`, `req.backend_hint` |
| Ex6 Failover | `05-backend-director.vcl` | Same file as Ex5; exercise is toggle-and-observe |
| Ex7 Monitoring | none | CLI tools only |
| Ex8 Broken VCL | `05-backend-director.vcl` | Fixing `broken/b1-b3.vcl` should end at this behaviour |
| Ex9 Tuning demo | none | `VARNISH_MEM=1m` demo, see GUIDE.md |
