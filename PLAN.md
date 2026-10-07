# Varnish Workshop Implementation Plan

## Goal

Deliver a beginner-friendly Varnish Cache 6.0.18 onboarding in two guided
120-minute sessions. Configure and observe requests before teaching caching,
then add resilience and operational diagnosis. Keep slides.md as the presentation
source and regenerate slides.html rather than editing generated HTML.

## Agreed Test Interfaces

- Backend HTTP: response status, body and headers, including HEAD and health controls.
- Varnish HTTP: Host/path routing, headers, caching, Vary, PURGE, grace and failover.
- verify.sh CLI: exercise selection, invalid arguments, assertions and exit status.
- Document consistency and slide rendering are separate manual/build checks.

Use vertical TDD slices: add one behavioral test, observe red, implement the
smallest correction, rerun green. Do not replace real HTTP with mocked internals.

## Review Findings

- curl -I sends HEAD, but the mock backend currently implements only GET/POST.
- Trainees need to declare backend1 before learning directors or cache policy.
- Add example.com/test1 -> backend1 /nocache as an internal rewrite, not a redirect.
- Explain VCL hooks, built-in fallthrough, if/==/~, set/unset and return.
- Use resp.status, not resp.StatusCode; distinguish req/bereq/beresp/resp.
- Explain host :8091 versus container backend1:8080; Varnish is at host :8081.
- Teach logs early, including original ReqURL and rewritten BereqURL.
- Explain TTL/grace/keep, cookie safety, Vary variants and hash-based PURGE.
- Scope failed background-refresh handling; do not abandon all foreground 5xx.
- Label private-network PURGE ACLs lab-only and test unauthorized access.
- Strengthen verification: status, bodies, negative routing, recovery and invalid selectors.
- Fix broken-VCL hints, align cumulative solutions and remove stale test counts.
- Explain eviction counters as pressure signals, not automatic sizing verdicts.

## Exercise Checkpoints

| Exercise | Topic | Checkpoint |
|---|---|---|
| 1 | Declare backend1 and reload | 01-backend.vcl |
| 2 | Host/path rewrite, headers and logs | 02-routing.vcl |
| 3 | Request flow, MISS/HIT, Cache-Control | 03-cache.vcl |
| 4 | TTL, public lab cookies and Vary | 04-ttl-vary.vcl |
| 5 | TTL/grace/keep and stale delivery | 05-grace.vcl |
| 6 | Authorized PURGE and invalidation | 06-purge.vcl |
| 7 | Backend2, director, probes and failover | 07-director.vcl |
| 8 | Monitoring | Manual evidence, no separate VCL |
| 9 | Broken-VCL diagnosis | Repair one fault at a time |
| 10 | Tuning | Mentor demo |

## Session Budgets

| Session 1 | Minutes |
|---|---:|
| Intro, reverse proxy, topology, setup | 15 |
| VCL fundamentals and backend1 (Ex1) | 20 |
| Routing, headers and logs (Ex2) | 20 |
| Flow and Cache-Control (Ex3) | 20 |
| Break | 10 |
| TTL, cookies and Vary (Ex4) | 20 |
| Recap and checkpoint | 15 |
| Total | 120 |

| Session 2 | Minutes |
|---|---:|
| Recap and restore checkpoint | 10 |
| TTL/grace/keep (Ex5) | 20 |
| PURGE (Ex6) | 15 |
| Director, probes, failover and recovery (Ex7) | 20 |
| Break | 10 |
| Monitoring (Ex8) | 15 |
| Troubleshooting (Ex9) | 20 |
| Tuning demo and wrap-up (Ex10) | 10 |
| Total | 120 |

## Work

1. Fix backend and verifier reliability with red/green tests and request timeouts.
2. Add cumulative checkpoint VCLs, routing and safe path boundaries.
3. Test cache variants, invalidation, stale delivery and health recovery over HTTP.
4. Synchronize Goal.md, GUIDE.md, OUTLINE.md, MENTOR.md, PREFLIGHT.md and solutions/README.md.
5. Rewrite slides into the teaching sequence; improve local diagrams and regenerate HTML.
6. Rehearse all checkpoints against the actual pinned Varnish version.
7. Review the diff, commit only intended changes and create a PR with Summary,
   Before/After Evidence and Merge Danger sections.

## Acceptance

Every automated exercise passes from its documented checkpoint. Both sessions
fit the budgets with scaffolding and mentor help. A trainee can trace a request,
configure safe caching, distinguish lifetime windows, invalidate an object,
observe failover/recovery and diagnose a fault with evidence. A full ban lab,
conditional 304 revalidation, all three troubleshooting faults and deep thread
tuning are optional follow-up material, not mandatory within four hours.

## Implementation And Evidence

The lab, cumulative checkpoints, single-fault troubleshooting configs, guides
and 35-slide deck are implemented. HTML is generated with Marp 4.5.1. Tests use
Python's standard library and the actual Varnish 6.0.18 container.

| Contract | Observed red | Observed green |
|---|---|---|
| Backend HEAD | 501 instead of 200 | GET-equivalent headers, empty body |
| Idempotent health controls | 404 | Repeated down/up changes and restores health |
| Header/URL observation | Missing echo headers | Only explicit lab values echoed |
| Invalid verifier selector | Exit 0 without running checks | Usage and exit 2 |
| Unreachable lab override | Ignored override, reported success | HTTP failure and exit 1 |
| Internal routing | /test1 returned 404 | backend1 /nocache, query and header checks |
| TTL/cookie policy | Ten-second freshness and uncached cookie response | Five-second expiry and narrowly scoped caching |
| Extended grace | 503 after default grace expired | Stale 200 survives outage and refreshes after recovery |
| PURGE | Unsupported method 501 | Correct Host/hash variants invalidated |
| Director | Only backend1 observed | Both backends, failover and recovery |
| Redirect visibility | Client hid 302 behind final 200 | Contract observes original 302 |
| Direct verifier invocation | Permission denied | Executable CLI works |

Rehearsal also checks denied PURGE with a restrictive ACL fixture, failed VCL
compilation leaving active routing available, and all three deliberate faults
failing their contract before the repaired checkpoint passes. Cleanup restores
the original file, active VCL and backend health independently and discards only
configurations created by that rehearsal. Screenshot rendering is a presentation
check, not an automated HTTP test. Actual trainee pacing still needs a human
rehearsal; performance counters are demonstration evidence, not sizing targets.

The documented 6,000-URL tuning workload was also run: normal 128m storage
reported zero LRU evictions; 1m storage reported 2,776 on this machine. These
observations are not expected counts for another environment. The normal memory
configuration and starter VCL are restored after the demonstration.
