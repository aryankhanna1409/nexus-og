# Aegis-Net overnight run — status

Autonomous run started 2026-10-19 on top of commit `7b748a2` (M2). Each
milestone is committed only after its acceptance gate passes. The full
verification log is in `IMPLEMENTATION_PLAN.md` §5; this file is the resume
point.

Pre-existing note: commit `7b748a2` (made outside this run) contains a stray
empty file named `tatus --short`. It was left untouched.

## Resume point

Next milestone: **M13 — make demo, E2E tests, README, final audit** (depends on M12 ✅).

## Milestones

| Milestone | Status | Verdict | Commit |
|---|---|---|---|
| M1 C library | done before this run | PASS | `823a5b7` |
| M2 Python binding + generator | done before this run | PASS WITH DOCUMENTED LIMITATIONS | `7b748a2` |
| M3 Telemetry simulator | done | PASS | `7d1edf6` |
| M4 Anomaly detection | done | PASS | `8172e7c` |
| M5 Correlation engine | done | PASS | `c4a7d85` |
| M6 Persistence/API/auth/audit | done | PASS | `c5881b6` (+ `a18b27c` whitespace fix) |
| M7 LLM providers + RCA | done | PASS (real-provider calls not verified) | `6d4f4b0` |
| M8 Reporting | done | PASS (PDF optional, not implemented) | `90232af` |
| M9 DevSecOps agent | done | PASS (rollback simulated by design) | `77184fd` |
| M10 Hardening + observability | done | PASS (OpenTelemetry not implemented) | `08f26c3` |
| M11 Docker | done | PASS | `3ace7ba` |
| M12 Dashboard | done | PASS | (this commit; see git log) |
| M13 Demo/E2E/audit | not started | — | — |

### M3 — Network telemetry simulation and seeded incidents

- Implementation: `backend/app/simulation/` (topology, 17-KPI catalogue,
  causal model, 9 incident injectors, events/deployments, rollback, CDRs, IO);
  `scripts/generate_network_metrics.py`, `scripts/simulate_incident.py`,
  `scripts/container_py312_test.sh`; `make network-data`, `make container-test`.
- Commands: `make test`; `scripts/container_py312_test.sh`; `.venv/bin/mypy`.
- Results: local Python 3.14: 155 passed (31 new), ASan run 148 passed +
  7 skipped, C 2/2 + 2/2, mypy clean. Container Python 3.12: 155 passed,
  mypy clean.
- Criterion amendment: Spearman instead of Pearson for CPU→latency (Pearson
  0.68–0.72, Spearman 0.87–0.97), with the reason recorded in the plan.
- Limitations: one fault per scenario is the tested configuration (multiple
  specs are supported but untested until M5). Memory-leak timing is minutes,
  not the 2-minute steps in the spec's illustrative timeline.

### M4 — Analytics and anomaly detection

- Implementation: `backend/app/analytics/` (`config.py` rules, `detectors.py`
  moving average / rolling std / z-score / EWMA / threshold / rate of change,
  `engine.py` episodes and spec §6 objects, `sources.py` adapters).
- Commands: `make test`; `scripts/container_py312_test.sh`; four mutation
  runs in a scratch copy.
- Results: local 179 passed, ASan run 172 + 7 skipped, C 2/2 + 2/2, mypy clean.
  Container 3.12: 179 passed.
- The seeded incident is detected on CELL-101..104 only, with onsets in causal
  order (memory 14:13 → CPU 14:31 → latency 14:40 → loss 14:50 → drops 14:53).
- False-positive bound: ≤ 1 per 100 series-days (measured 0.27).
- Limitations: Isolation Forest/DBSCAN not implemented (optional). A
  permanent level shift is reported until the 6 h re-baseline.

### M5 — Event correlation and incident management

- Implementation: `backend/app/analytics/correlation.py`, `causal_graph.py`,
  event adapters in `sources.py`.
- Commands: `make test`; `scripts/container_py312_test.sh`; 3 mutation runs;
  a 20-seed healthy-day incident count.
- Results: local 208 passed, ASan run 201 + 7 skipped, C 2/2 + 2/2, mypy clean.
  Container 3.12: 208 passed.
- Seeded: 1 CRITICAL incident; deployment hypothesis 0.895; distractor
  excluded; 0 incidents on 20 healthy days.
- Limitations: caller/per-call C anomalies are not turned into incidents.
  Overlapping independent faults on the *same* node with near-simultaneous
  onset would merge into one incident.
- Note: the working tree shows the stray `tatus --short` file deleted. That
  deletion was not made by this run and is left unstaged.

### M6 — Persistence, API, authentication and audit

- Implementation: SQLAlchemy models (19 tables), Alembic `0001`, FastAPI app
  factory with 13 endpoints, bearer-token RBAC (hashed tokens), hash-chained
  audit log, request IDs, pipeline service, `scripts/hash_token.py`,
  `.env.example`.
- Commands: `make test`; `scripts/container_py312_test.sh`; PostgreSQL run
  (`docker run postgres:16` on 127.0.0.1:55432, then the test with
  `AEGIS_TEST_POSTGRES_URL`).
- Results: local 235 passed + 1 skipped (PostgreSQL), ASan 228 + 8 skipped,
  mypy clean. PostgreSQL test 1 passed. Container 3.12: 235 passed + 1 skipped.
- Limitations: pipeline runs synchronously in the request (~3–5 s).
  Unauthenticated requests write audit rows, so flooding is a DoS vector
  until M10 rate limiting. TestClient deprecation warning (httpx2).

### M7 — AI provider abstraction and root-cause analysis

- Implementation: `app/llm/` (neutral interface, mock, Anthropic, OpenAI,
  local, factory with fallback reasons), `app/rca/` (9 read-only tools with
  strict schemas, bounded investigation loop, `RCAAnswer` schema with
  citation validation, deterministic mock investigator), `app/services/rca.py`,
  `POST /api/incidents/{id}/investigate`, `GET /api/incidents/{id}/rca`.
- Commands: `make test`; `scripts/container_py312_test.sh`; 2 mutation runs;
  SDK signature inspection.
- Results: local 279 passed + 2 skipped, ASan 272 + 9 skipped, mypy clean.
  Container 3.12: 279 + 2 skipped.
- Limitations: real LLM providers are untested against live APIs (no key; the
  test is opt-in). The mock provider is rule-based, not an LLM.
- Process note: a commit (`c5881b6`) was created despite a `git diff --check`
  warning (trailing whitespace) because of a `;` in the command chain. Fixed
  in `a18b27c`; commits are now gated with `&&`.

### M8 — Reporting engine

- Implementation: `app/reporting/` (document model, builder computing every
  figure from the DB, grounded LLM narrative with template fallback, Jinja2
  Markdown/HTML templates), `/api/reports/generate`, `/api/reports`,
  `/api/reports/{id}?format=`.
- Commands: `make test`; `scripts/container_py312_test.sh`; 3 mutation runs.
- Results: local 290 passed + 2 skipped, ASan 283 + 9 skipped, mypy clean.
  Container 3.12: 290 + 2 skipped.
- Limitations: no PDF output. Impact call counts cover the whole analysed
  call log for the affected cells, not only the incident window (stated in
  the report text).

### M9 — Autonomous DevSecOps agent

- Implementation: `app/agents/` (policy, sandboxed command runner,
  disposable git workspaces, synthetic DEMO-CVE advisory DB, 20 tools,
  deterministic playbooks, orchestration with approvals), `demo-workspace/`,
  `/api/agent/*`; pipeline gains `correlate_flag` and records incident specs
  for re-simulation.
- Commands: `make test`; `scripts/container_py312_test.sh`; 6 mutation runs.
- Results: local 325 passed + 2 skipped, ASan 318 + 9 skipped, mypy clean.
  Container 3.12: 325 + 2 skipped.
- Limitations: playbooks are deterministic (the LLM only influences RCA
  output); `restart_service` is registered but not modelled (always fails
  with an explanation); patch generation is revert-based only.

### M10 — Security hardening and observability

- Implementation: ASGI middleware (request id/access log/metrics/500 handler,
  security headers, body-size limit incl. streamed bodies, Redis/in-memory
  rate limiting), JSON logging with context stamping, Prometheus `/metrics`,
  RCA/agent log context and counters, `tests/test_security.py`.
- Results: local 346 passed + 3 skipped, ASan 339 + 10 skipped, mypy clean.
  Container 3.12: 346 + 3 skipped. Live Redis 7.4.11: 1 passed.
- Limitations: no OpenTelemetry/Grafana. `/metrics` is unauthenticated.

### M11 — Docker backend and infrastructure

- Implementation: `backend/Dockerfile` (C build + ctest stage, non-root
  runtime), `docker-entrypoint.sh` (migrations, idempotent bootstrap),
  `app/bootstrap.py`, `docker-compose.yml` (postgres, redis, backend; health
  checks, volumes, localhost-only port), `.dockerignore`,
  `scripts/init_env.py` (`make env`), `scripts/docker_smoke.sh`
  (`make docker-smoke`).
- Results: clean `--no-cache` smoke test passed end to end. Local 347 passed
  + 3 skipped, ASan 340 + 10 skipped, mypy clean. Container 3.12: 347 + 3.
- Defect fixed: pytest missing from the runtime image, which led the agent
  to misdiagnose (see the plan log).

### M12 — React dashboard

- Implementation: `frontend/` (React/TS/Vite/Tailwind/Recharts; 11 pages;
  typed API client; token sign-in in sessionStorage; sandboxed report
  iframe), `frontend/Dockerfile` + `nginx.conf`, compose `frontend`
  service, `GET /api/network/overview`, `make frontend-test`,
  `scripts/ui_check.mjs` (Playwright) wired into `docker_smoke.sh`.
- Results: Vitest 10 passed; Python 349 + 3 skipped (local and 3.12);
  Docker smoke and browser check passed on all 11 routes.
- Limitations: one page bundle per vendor chunk, no code-splitting per route;
  no frontend end-to-end tests of the approval flow in the browser (covered by
  API tests).
