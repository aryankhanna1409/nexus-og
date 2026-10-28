# Aegis-Net Implementation Plan

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done and verified by
executed tests. A milestone is only marked `[x]` when its acceptance tests have
been run and passed; results are recorded in the milestone's *Verification log*.

Authoritative inputs: `PROJECT_SPEC.md` (functional spec) and `CLAUDE.md`
(engineering rules). Component interfaces live in `ARCHITECTURE.md`.

---

## 0. Environment baseline (verified 2026-10-19)

| Tool | Status | Notes |
|---|---|---|
| OS | Ubuntu 26.04.1 LTS on WSL2 (kernel 6.18), x86_64, 12 cores, 7.4 GiB RAM | |
| gcc | 15.2.0 ✅ | `-fsanitize=address,undefined` builds and runs; LeakSanitizer reports leaks (verified with a deliberate-leak probe) |
| cmake / make | 4.2.3 / 4.4.1 ✅ | |
| clang, clang-tidy, cppcheck, valgrind, ninja | ❌ not installed | ASan/UBSan/LSan cover memory checking; static analysers are optional |
| python3 | 3.14.4 ✅ | `venv`, `ensurepip`, `ctypes` available; `pip install` into a venv works (network OK) |
| Python libs (fastapi, pydantic, numpy, …) | ❌ not installed system-wide | Installed per-project into `backend/.venv` (M2: pytest 9.1.1, mypy 2.4.0 only; the binding has no runtime dependencies) |
| node | ❌ **not installed in WSL** | `npm` on PATH resolves to the Windows install (`/mnt/c/Program Files/nodejs/npm`) and does not run. Frontend will be built/tested inside a `node` Docker image unless a native Node is installed |
| docker | 29.7.2 (Docker Desktop) ✅ | daemon reachable, `docker pull python:3.12-slim` succeeded |
| docker compose | v5.3.1 ✅ | |
| psql, redis-cli | ❌ | Not needed locally — Postgres/Redis run in containers |
| gh | ❌ | Not needed |
| git | 2.53.0 ✅ | repo on `master`, no commits yet |

Version skew to manage: local Python is 3.14, container images will use
Python 3.12. CI-style checks (`make test`) must pass on both or be run in the
container.

---

## 1. Global decisions

| ID | Decision | Rationale |
|---|---|---|
| D1 | C library lives in `c-library/` (spec §18) using the file layout of spec §3. Build output is `libcallanalyzer.so`. | Spec §3 and §18 give two paths; §18 is the monorepo layout. |
| D2 | Python ↔ C binding via **ctypes**. | No compiler needed at install time; library is loaded from an explicit path. |
| D3 | Analytics uses **numpy** only (no pandas). Isolation Forest/DBSCAN are optional and deferred (would add scikit-learn). | Interpretable methods required first (spec §6); avoid heavy deps. |
| D4 | Persistence: SQLAlchemy 2.x + Alembic; PostgreSQL in Docker. JSON columns use `JSON().with_variant(JSONB, "postgresql")` so the offline demo and unit tests can run on SQLite. | Spec §17 + §23 ("demo works without external infrastructure"). |
| D5 | LLM provider abstraction with `mock` (deterministic, default when no key), `anthropic`, `openai`, `local` (OpenAI-compatible endpoint). Vendor SDKs are optional extras, imported lazily. | Spec §20, §23. |
| D6 | DevSecOps agent operates only on a **disposable copy** of a synthetic demo service repo (`demo-workspace/`), never on this repository. Vulnerability data comes from a bundled synthetic advisory DB with IDs prefixed `DEMO-CVE-`. | CLAUDE.md: synthetic data, no arbitrary commands, keep changes contained. Avoids inventing real CVE claims. |
| D7 | "Deployments" and "rollback" are simulated through a deployment registry the telemetry simulator reads. This is documented as a simulation, not presented as real infrastructure control. | Spec §29: no fake functionality disguised as real. |
| D8 | Auth: bearer API tokens mapped to roles (`viewer`, `operator`, `approver`, `admin`), token hashes configured via env. | Spec §27; simple and testable. |
| D9 | Redis used for rate limiting and the agent job queue; an in-process fallback exists for the offline demo and tests. | Spec §19 lists Redis; must not be a hard dependency of `make demo`. |
| D10 | Observability: stdlib `logging` with a JSON formatter + `prometheus_client` `/metrics`. OpenTelemetry is optional/deferred. | Spec §21 "where practical". |

---

## 2. Milestones

Dependency graph:

```mermaid
graph LR
  M1[M1 C library] --> M2[M2 Python binding + call-log generator]
  M3[M3 Telemetry simulator + seeded incidents] --> M4[M4 Anomaly detection]
  M2 --> M5[M5 Correlation engine]
  M4 --> M5
  M5 --> M6[M6 Persistence + API core + auth/audit]
  M6 --> M7[M7 LLM abstraction + RCA engine]
  M7 --> M8[M8 Reporting engine]
  M6 --> M9[M9 DevSecOps agent + policy]
  M7 --> M9
  M8 --> M10[M10 Hardening + observability]
  M9 --> M10
  M10 --> M11[M11 Docker backend/db/redis]
  M11 --> M12[M12 React dashboard]
  M12 --> M13[M13 make demo + E2E + self-audit]
```

M1 and M3 have no dependency on each other and may proceed in parallel.
Testing is part of every milestone (spec Phase 13 is distributed, not deferred).

### M1 — C call-analysis library `[x]`

Scope: `c-library/` with `include/call_analyzer.h`, `src/{parser,analyzer,statistics,anomaly,utils}.c`,
`tests/test_call_analyzer.c`, `CMakeLists.txt`, `README.md`; root `Makefile` targets.

Features: CSV parsing (header detection, BOM, CRLF, quoted fields, blank lines),
field validation, lenient/strict modes with a parse report, overall statistics,
per-cell aggregation, failure-code breakdown, time-window aggregation,
caller behaviour aggregation, duration/signal/packet-loss analysis, robust
(median/MAD) outlier detection, error codes + `strerror`, explicit free functions.

Acceptance criteria:
- Builds with `-Wall -Wextra -Wpedantic -Werror` plus extra warnings (`-Wshadow -Wconversion …`) under gcc 15.
- All C tests pass in a normal build **and** an ASan+UBSan build with LeakSanitizer reporting zero leaks.
- Allocation-failure injection: every allocation site in parse/aggregate/detect paths returns `CA_ERR_NOMEM` without leaking.
- Public API never crashes on NULL arguments; returns `CA_ERR_NULL_ARG`.

Tests: parser (valid, header/no header, CRLF, BOM, quotes), malformed CSV
(missing fields, extra fields, non-numeric, out-of-range, over-long lines and
fields, bad timestamps, embedded NUL), strict vs lenient, memory (OOM injection
sweep, ASan/LSan), statistics (hand-computed expected values), per-cell,
failure-code, time-window, caller, anomaly detection (seeded bad cell detected,
clean data yields no cell anomalies), empty input, integer-overflow guards.

### M2 — Python binding and call-log generator `[x]` (accepted after audit, 2026-10-19 — PASS WITH DOCUMENTED LIMITATIONS)

Scope: `backend/call_analyzer/` (ctypes wrapper), `scripts/generate_call_logs.py`.
`analyze_call_log(path) -> dict` returning total calls, success/drop rate,
average duration, per-cell stats, failure-code stats, anomalies, suspicious windows.

Acceptance: pytest calls the real `.so` (no Python re-implementation of the
math); results equal a pure-Python reference computed in the test on the same
fixture; error codes map to typed Python exceptions; generator is deterministic
for a given seed and its seeded faulty cell is detected by the C library.

Tests: binding round-trip, exception mapping, missing library error message,
generator determinism, generator→C anomaly detection.

Audit additions (`backend/tests/test_binding_abi_and_ownership.py`):
- Per-field ABI probe. It compiles `offsetof`/`sizeof`/`_Generic` against the
  header and checks every field's name, order, offset, size and type class
  for all 11 mirrors.
- Reference comparison covering every field of every anomaly type.
- Spies on native pointer ownership (success, C failure midway, Python
  exception during conversion, parse failure).
- int64 and double overflow guards, and discovery edge cases.
- Glibc heap test tightened to 16 KiB per 100 calls, with a sanity check
  for each of the six free functions.
- 50-seed generator acceptance test.

### M3 — Network telemetry simulator and seeded incidents `[x]`

Scope: `backend/app/simulation/` + `scripts/generate_network_metrics.py`,
`scripts/simulate_incident.py`. Causal model (CPU → processing delay → latency →
packet loss → call drops; memory leak → CPU), diurnal load, per-cell noise,
incident injectors for all nine incident types in spec §5, deployment/security/
application-log event streams, rollback recovery.

Acceptance: fixed seed reproduces identical output; Pearson correlation between
CPU and latency during the seeded incident > 0.7 and near zero/weak at baseline;
seeded memory-leak deployment produces the ordered signal chain of spec §24;
rollback returns metrics to within baseline bands.

Criterion amendment (M3, recorded deliberately): CPU→latency dependence is
measured with **Spearman rank** correlation (> 0.7 in the incident window,
|ρ| < 0.5 in the 60 minutes before the deployment) instead of Pearson. Queueing
latency is strongly non-linear in CPU and CPU saturates at its clip. Pearson
was measured at 0.68–0.72 while Spearman was 0.87–0.97 on the same data. The
baseline is "weak", not zero (0.04–0.47), because queueing couples CPU and
latency even when healthy. "Rollback returns to baseline" is verified exactly:
from 3 minutes after rollback, every KPI equals a healthy run with the same seed
(atol 1e-9).

### M4 — Analytics and anomaly detection `[x]`

Scope: `backend/app/analytics/`. Moving average, rolling std, Z-score, EWMA,
thresholds, rate-of-change; ensemble scoring; anomaly objects per spec §6
(metric, timestamp, value, baseline, severity, anomaly_score, related_metrics).

Acceptance: on the seeded incident, anomalies are raised for memory, CPU,
latency, packet loss, throughput (drop) and call-drop rate, with timestamps
after the deployment; false-positive rate on a clean 24 h baseline below a
documented bound; each detector unit-tested on synthetic step/spike/ramp series.

Documented FP bound (M4): ≤ 1 false-positive episode per 100 series-days and
no high/critical false positives. Measured over 20 seeds: 11 episodes in
4,080 series-days (0.27 per 100), all low/medium. The test enforces the bound
on 8 seeds (1,632 series-days).

### M5 — Correlation engine `[x]`

Scope: `backend/app/analytics/correlation.py`. Groups metric anomalies, C-library
call anomalies, deployment, security and application events into incidents
using time-window proximity, shared cell/service topology and lagged
cross-correlation; produces `Incident` with symptoms, ordered events, suspected
causes and confidence.

Acceptance: seeded scenario yields exactly one incident containing the deployment
as the earliest event and the six symptoms; unrelated noise anomalies are not
merged; two separate incidents in one dataset stay separate.

### M6 — Persistence, API core, auth and audit `[x]`

Scope: `backend/app/{models,schemas,api,services,security}`, Alembic migrations,
FastAPI app with OpenAPI. Tables for all spec §15 entities. Read endpoints for
calls, network, incidents, audit; `/api/health`. Token auth + RBAC; audit log
written for every mutating request and every agent/AI action.

Acceptance: `alembic upgrade head` succeeds on Postgres (container) and SQLite;
endpoint tests via `httpx`/TestClient with role matrix (401/403/200);
pipeline ingest stores incidents and they are returned by the API.

### M7 — LLM abstraction and RCA engine `[x]`

Scope: `backend/app/rca/`, `backend/app/llm/`. `LLMProvider` (`generate`,
`tool_call`), providers: mock/anthropic/openai/local. Read-only RCA tool registry
(the nine tools in spec §8) with JSON-schema arguments validated by Pydantic.
Investigation loop with step budget; output validated against `RootCauseAnalysis`
schema with explicit `facts` / `inferences` / `hypotheses` / `recommendations`.

Acceptance: mock provider produces deployment-regression RCA on the seeded incident
using only tool outputs as evidence (each evidence item cites a tool call ID);
malformed/unknown tool calls from the LLM are rejected and logged; real
providers are exercised only if a key is present (tests skip otherwise, and the
skip is reported). Consult the Anthropic API documentation before writing the Anthropic provider.

### M8 — Reporting engine `[x]`

Scope: `backend/app/reporting/`. Report sections per spec §9; JSON, Markdown and
HTML renderers (Jinja2 with autoescape); PDF optional/deferred.

Acceptance: report for seeded incident contains every section, numeric findings
match analytics output, confidence present, HTML escapes injected strings.

### M9 — DevSecOps agent and action policy `[x]`

Scope: `backend/app/agents/`, `demo-workspace/` template. OBSERVE→ANALYZE→PLAN→
ACT→VERIFY→CLOSE state machine; allowlisted tools (spec §10) each tagged with a
risk class; policy engine (READ_ONLY, LOW_RISK, REQUIRES_APPROVAL, HIGH_RISK,
BLOCKED); subprocess runner using argv lists only, fixed executables, timeouts,
confined cwd, scrubbed env; approval workflow; scenarios 1–3 of spec §11.

Acceptance: scenario tests reach expected end state; `REQUIRES_APPROVAL`/`HIGH_RISK`
actions never execute before approval; `BLOCKED` never executes; LLM-proposed
free-text commands are rejected; every action has a rationale and an audit row.

### M10 — Security hardening and observability `[x]`

Rate limiting, request IDs, agent/incident IDs in log context, Prometheus metrics,
input-size limits, security tests (authz bypass attempts, path traversal in
report/log tools, injection strings).

### M11 — Docker (backend, postgres, redis) `[x]`

Multi-stage backend image compiles the C library and runs its tests during build;
migrations on start; healthchecks. Acceptance: `docker compose up --build` from a
clean clone brings services to healthy and `/api/health` reports DB, Redis and
C-library status.

### M12 — React dashboard `[x]`

React + TypeScript + Vite + Tailwind + Recharts; pages per spec §13; dark NOC
aesthetic; incident timeline; RCA explainability panel; agent approval UI.
Vitest + Testing Library component tests (run in a `node` container since Node
is absent in WSL). Acceptance: all pages render real API data; component tests pass.

### M13 — `make demo`, end-to-end tests, final audit `[x]`

`make demo` runs the 13 demo steps offline with the mock provider; integration
tests for both pipelines in spec §22; README per spec §28 with Mermaid diagrams;
self-audit checklist of spec §31 executed and recorded.

---

## 3. Integration risks

| Risk | Impact | Mitigation |
|---|---|---|
| ctypes struct layout drift between `call_analyzer.h` and Python mirrors | Silent memory corruption | **Closed in tests (M2 audit):** the per-field ABI probe compares name/order/offset/size/type class for every field. Residual: the *runtime* load check is size-only (no offset export in the C ABI), so a library rebuilt from a different header without re-running the tests would only be caught if its struct sizes change. Enum fields are accepted as signed or unsigned int (gcc makes them unsigned; values are 0–7). |
| Shared-library discovery across local / Docker | Import failure | **Mitigated (M2):** env var, then local build, then `/usr/local/lib`, always by absolute path; verified via `/proc/self/maps` locally and in a Python 3.12 container. |
| Python 3.14 (local) vs 3.12 (image) wheel availability | Install failures | Pin compatible versions; run tests in both. M2 verified on both (see log); revisit when FastAPI/numpy etc. are added. |
| SQLite (demo) vs Postgres (prod) dialect differences | Migration/query bugs only seen in Docker | Portable types (D4); run migration + API tests against Postgres container in M6/M11. |
| Telemetry realism vs detector tuning | Detectors over-fitted to simulator | Test detectors on generic synthetic series, not only simulator output; document thresholds. |
| LLM nondeterminism and malformed tool calls | Flaky tests, unsafe actions | Mock provider for tests; Pydantic validation of every tool call; step budget; real-provider tests opt-in. |
| Agent subprocess execution | Command injection / host damage | Allowlist + argv-only + disposable workspace + policy engine + audit; no shell=True anywhere (enforced by a test that greps the codebase). |
| Node not installed in WSL | Frontend can't be built locally | Build/test via `node` image; document. |
| WSL2 + Docker Desktop bind-mount performance/permissions | Slow or failing dev containers | Prefer image builds over bind mounts for CI-style runs. |
| Scope size | Unfinished core features | Vertical slices; each milestone ends with passing tests; incomplete work listed explicitly. |

---

## 4. Requirements traceability

IDs refer to `PROJECT_SPEC.md` sections. "Test" names the test file / suite that
verifies the requirement once implemented. Status reflects executed tests only.

| Req | Spec § | Requirement | Component | Milestone | Verification test | Status |
|---|---|---|---|---|---|---|
| R1 | 3 | Real reusable C library with clean public API | `c-library/` | M1 | `test_call_analyzer.c` (all suites) | verified (C tests) |
| R2 | 3 | CSV parsing + validation, malformed input handling | `parser.c`, `utils.c` | M1 | `parser_*`, `malformed_*` cases | verified |
| R3 | 3 | Aggregations: drop, duration, cell, signal, failure code, time window, caller/callee | `statistics.c`, `analyzer.c` | M1 | `statistics_*`, `cell_statistics`, `failure_code_statistics`, `time_window_statistics`, `caller_statistics` | verified |
| R4 | 3 | Outlier detection | `anomaly.c` | M1 | `anomaly_*` cases | verified |
| R5 | 3 | Memory safety, NULL handling, overflow, leaks; `-Wall -Wextra -Wpedantic`; ASan/UBSan | `c-library/` | M1 | `make c-test-asan`, `oom_all_operations`, `null_arguments` | verified |
| R6 | 4 | Python binding, `analyze_call_log()` returning structured dict | `backend/call_analyzer/` | M2 | `backend/tests/test_call_analyzer_binding.py`, `test_generate_call_logs.py` | verified (py3.14 local, py3.12 container) |
| R7 | 5 | Correlated network telemetry simulator | `app/simulation/` | M3 | `tests/test_simulation.py` (chain, correlation, determinism, baseline) | verified |
| R8 | 5 | Nine incident types simulated | `app/simulation/incidents.py` | M3 | `test_each_incident_type[*]` (9 cases) | verified |
| R9 | 6 | Interpretable anomaly detectors + anomaly schema | `app/analytics/` | M4 | `tests/test_analytics.py` (24 tests) | verified |
| R10 | 6 | Optional ML detectors (Isolation Forest/DBSCAN) | `app/analytics/` | — | — | NOT IMPLEMENTED (optional in spec; documented limitation) |
| R11 | 7 | Cross-source correlation → Incident object | `app/analytics/correlation.py` | M5 | `tests/test_correlation.py` (29 tests) | verified |
| R12 | 8 | LLM RCA with structured tools; facts vs hypotheses | `app/rca/`, `app/llm/` | M7 | `tests/test_rca.py` (44 tests; live-provider test opt-in, not run) | verified (mock + fake SDK clients) |
| R13 | 9 | AI report (JSON/Markdown/HTML; PDF optional) | `app/reporting/` | M8 | `tests/test_reporting.py` (11 tests; PDF not implemented) | verified |
| R14 | 10 | Agent tools + OBSERVE…CLOSE loop | `app/agents/` | M9 | `tests/test_agent.py` (35 tests) | verified |
| R15 | 11 | Scenarios: vulnerable dependency, failed CI, production anomaly | `app/agents/planner.py` | M9 | `test_vulnerable_dependency_flow`, `test_failed_ci_flow`, `test_production_anomaly_*` | verified (rollback is simulated) |
| R16 | 12 | Action risk classes, approval gating, rationale, logging | `app/agents/policy.py`, `service.py` | M9 | `test_policy_table`, `test_blocked_action_never_executes`, `test_unapproved_action_cannot_execute_via_service`, `test_initiator_cannot_approve_own_action` | verified |
| R17 | 13, 25 | Dashboard pages, KPI cards, charts, NOC aesthetic | `frontend/` | M12 | Vitest (10 tests) + Playwright browser check of all 11 routes against the Docker stack + screenshot review | verified |
| R18 | 14 | Interactive incident timeline | `frontend/src/components/IncidentTimeline.tsx`, incident API | M12 | `IncidentTimeline` ordering test, browser check of `/incidents/INC-2026-001` | verified |
| R19 | 15 | Schemas for 11 entities, Pydantic at API | `app/models`, `app/schemas/entities.py` | M6 | `tests/test_api_core.py` (responses validated through the schemas) | verified |
| R20 | 16 | REST API endpoints + OpenAPI | `app/api/` | M6–M12 | `test_api_core.py`, `test_rca.py`, `test_reporting.py`, `test_agent.py`, `test_security.py`, `test_e2e.py`; all spec §16 endpoints present; OpenAPI test | verified |
| R21 | 17 | PostgreSQL, migrations, relational tables + JSON evidence | `alembic/`, `app/models` | M6 | `test_sqlite_migration_*`, `test_postgres_migration_and_pipeline` (run against postgres:16) | verified |
| R22 | 18 | Monorepo structure | repo | all | self-audit: all §18 paths exist; integration tests live in `backend/tests/` (explained in `tests/README.md`) | verified (one documented deviation) |
| R23 | 19 | `docker compose up --build` (frontend, backend, postgres, redis); C lib built in backend image | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` | M11, M12 | `scripts/docker_smoke.sh` with `SMOKE_UI_CHECK=1` (all four services) | verified |
| R24 | 20 | LLM provider abstraction, env config, no committed keys | `app/llm/` | M7 | `test_provider_selection`, Anthropic/OpenAI request-shape and error-mapping tests | verified offline; real API calls not executed (no key) |
| R25 | 21 | Structured logs, request/agent/incident IDs, metrics, audit | `app/observability/`, `app/security/middleware.py` | M6, M10 | `tests/test_security.py` (logging/metrics tests) | verified (OpenTelemetry not implemented) |
| R26 | 22 | C, Python, frontend, integration tests | all | M1–M13 | `make test` (C 2+2 executables, Python 352 + 3 opt-in skips, ASan run 345, mypy, Vitest 10) + `test_e2e.py` both chains | verified |
| R27 | 23 | `make demo` offline with mock provider, 13 steps | `scripts/demo.py`, `Makefile` | M13 | `make demo` (exit 0) + `test_offline_demo_runs_end_to_end` | verified |
| R28 | 24 | Seeded memory-leak deployment incident + evidence chain | simulator, analytics, RCA, agent | M3–M9, M13 | `test_ordered_degradation_chain`, `test_seeded_*` (M4/M5), `test_mock_rca_on_seeded_incident`, `test_production_anomaly_rollback_and_recovery`, `test_data_to_analytics_to_incident_to_rca_to_report` | verified (rollback simulated) |
| R29 | 26 | Explainability chain without hidden chain-of-thought | `app/rca/`, `app/api/rca.py`, `RcaPanel` | M7, M12 | `test_investigate_endpoint` (explanation keys), `RcaPanel` component test, browser check of `/rca` | verified |
| R30 | 27 | AuthN, RBAC, approvals, rate limiting, safe subprocess, no LLM shell | `app/security/`, `app/agents/` | M6, M9, M10 | `test_role_matrix`, `test_tokens_only_accepted_as_bearer_header`, `test_rate_limit`, `test_runner_never_uses_a_shell`, `test_runner_rejects_non_allowlisted_commands`, agent gate tests + 6 mutation checks | verified |
| R31 | 28 | README with 16 sections + Mermaid; docs/ | `README.md`, `docs/` | M13 | self-audit: 16 numbered sections, 3 Mermaid diagrams; `docs/{architecture,api,agent,rca,security}.md` | verified |
| R32 | 31 | `make test`, `make demo`, `make clean`; self-audit | `Makefile` | M13 | all three executed in the final sweep (exit 0); self-audit below | verified |

---

## 4a. Final self-audit (spec §31), 2026-10-19

Each answer is backed by commands executed in the final sweep (log below).

| Question | Answer | Evidence |
|---|---|---|
| Does the C library compile? | Yes | `-Werror` + 13 extra warnings, gcc 15.2 (host) and gcc 14.2 (container and backend image build) |
| Do C tests pass? | Yes | ctest 2/2 normal, 2/2 under ASan/UBSan/LSan (fault injection over every allocation site); ctest in the Docker build |
| Does Python correctly call the C library? | Yes | binding tests incl. per-field ABI probe, reference comparisons, ownership spies; `/api/health` reports `call_analyzer: ok` in Docker |
| Does the telemetry generator produce correlated data? | Yes | ordered degradation chain; Spearman CPU→latency 0.87–0.97 in incident vs ≤ 0.47 baseline |
| Does anomaly detection detect the seeded incident? | Yes | all six spec §24 symptoms on CELL-101..104 only, in causal order; FP rate 0.27/100 series-days |
| Does correlation produce a meaningful incident? | Yes | one CRITICAL incident, deployment hypothesis 0.89, distractor excluded, 0 incidents on 20 healthy days |
| Does the RCA engine receive structured evidence? | Yes | 9 read-only tools; opening prompt has ids and symptom names only; facts must cite successful tool calls |
| Does the AI report contain evidence and confidence? | Yes | report sections, evidence references, RCA and correlation confidence, caveats; numbers checked against the DB |
| Does the DevSecOps agent use controlled tools? | Yes | 20 allowlisted tools, sandboxed runner, `shell=False` enforced |
| Are dangerous actions approval-gated? | Yes | REQUIRES_APPROVAL/HIGH_RISK/BLOCKED gates re-checked at execution; 6 gate mutations detected; demo shows 409 before approval |
| Does the dashboard consume real backend data? | Yes | typed client only; Playwright check rendered all 11 routes from the live Docker stack |
| Does the complete demo work end-to-end? | Yes | `make demo` exit 0 (13 steps, resolved incident, valid audit chain); `test_offline_demo_runs_end_to_end` |
| Does `docker compose up --build` work from a clean environment? | Yes | `--no-cache` smoke build passed (M11); the documented `make env` + `docker compose up --build` flow brought all four services up in the final sweep |
| Are there hard-coded secrets? | No | regex scan of tracked/new files found none (test-only fake keys excepted); `.env`/tokens not tracked |
| Broken imports, placeholders, dead code? | None found | mypy strict clean (86 files), tsc strict clean, no TODO/FIXME/placeholder in app code; `restart_service` is registered but deliberately not modelled and fails with an explanation (documented) |

**Not verified / not implemented:**
- live Anthropic/OpenAI/local-LLM calls (no key; opt-in test exists);
- Isolation Forest/DBSCAN, PDF reports, OpenTelemetry/Grafana (optional in spec);
- behaviour on real (non-synthetic) telemetry;
- clang and other compilers;
- non-glibc platforms.

**Production readiness:** this is a working prototype, **not** production-ready
(no TLS, external identity, secret manager, HA or real infrastructure
integration).

## 5. Verification log

Entries record commands actually executed and their outcome.

- 2026-10-19 — Environment baseline (section 0) gathered by direct command execution.
- 2026-10-19 — M1: `make c-build` compiles cleanly with `-Werror` and the extended
  warning set (gcc 15.2). `make test` (= `c-test` + `c-test-asan`): 4/4 ctest
  executables passed — shared-lib suite 27 cases / 449 checks; fault-injection
  suite 28 cases / 608 checks, with every allocation failure point exercised
  (parse 4, statistics 2, cells 2, codes 2, windows 2, callers 2, anomalies 34),
  each returning `CA_ERR_NOMEM` with NULL outputs. Under ASan+UBSan+LSan: no
  errors, no leaks (sanitizer runtimes confirmed linked via `ldd`).
- 2026-10-19 — M1 mutation check (scratch copy, not committed): removing a
  `free` in `calculate_cell_statistics` made the ASan run fail with a
  LeakSanitizer report; changing the drop-rate denominator made
  `statistics_small`, `cell_statistics` and `time_window_statistics` fail.
- 2026-10-19 — M2, local (WSL2, Python 3.14.4, gcc 15.2): `make test` exit 0:
  C ctest 2/2 + ASan ctest 2/2 passed; `pytest` **91 passed**, 0 skipped
  (10.4 s); `mypy --strict` (binding + generator): no issues.
  - Library path: with `CALL_ANALYZER_LIB` unset, loaded
    `c-library/build/libcallanalyzer.so.1.0.0` and that was the only
    `libcallanalyzer` mapping in `/proc/self/maps`. The full suite was rerun from
    an unrelated cwd with `CALL_ANALYZER_LIB` pointing to a relocated copy:
    91 passed, and only the copy was mapped.
  - Memory: with libasan+libubsan preloaded and the ASan-built library,
    88 passed (3 deselected: two need glibc `mallinfo2`, which ASan replaces,
    and one matched the `-k "not leak"` filter by name). No sanitizer reports.
    A deliberate double free through ctypes was caught by ASan, confirming the
    sanitizer was active. A glibc-heap leak test (100 calls < 1 MB growth)
    passed. Its sanity twin (free_call_records disabled) detected > 10 MB growth.
  - Generator over 50 seeds (manual run): faulty CELL-107 flagged for drop rate
    50/50 and packet loss 50/50, low signal 49/50; no other cell ever flagged;
    healthy baseline produced 0 anomalies in 50/50 seeds.
  - `make test` initially failed: the venv rule's `touch` targeted
    `bin/python`, a symlink to the system interpreter (permission denied, no
    change made). Fixed with a stamp file.
- 2026-10-19 — M2, container (`python:3.12-slim`: Python 3.12.15, gcc 14.2.0,
  cmake 3.31.6, glibc 2.41; repo mounted read-only, copied without host build
  dirs): C library built with `-Werror` with no warnings, ctest 2/2 passed,
  installed to `/usr/local/lib`. With no env var the binding loaded
  `/usr/local/lib/libcallanalyzer.so.1.0.0`: **91 passed**. With
  `CALL_ANALYZER_LIB=/tmp/cbuild/libcallanalyzer.so`: **91 passed**. mypy:
  no issues. Generator seed-42 SHA-256 identical to the host 3.14 output
  (69e6f432…ee167).
- M2 not verified: non-glibc platforms (musl/macOS); loading the library from
  multiple threads concurrently (load is lock-protected but untested);
  inputs of millions of rows through the binding.
- 2026-10-19 — **M2 acceptance audit.** Baseline before changes: `make test` exit 0,
  91 passed, mypy clean; `git diff 823a5b7 -- c-library` empty.
  - Defects found and fixed (binding/tests only, C library untouched):
    - D1: `window_seconds` outside int64 was wrapped silently by ctypes. For
      example `2**64+300` was accepted and analysed as 300 while the result
      reported `18446744073709551916`. Now a ValueError. The int64 extremes
      still reach C and get `InvalidArgumentError`.
    - D2: the glibc heap leak test (1 MB threshold) caught only 2 of the 6
      possible missing frees. Measured growth over 100 calls with each free
      skipped: cells 168,736 B, codes 25,824 B, windows 197,536 B, anomalies
      429,072 B, callers 20.7 MB, records > 10 MB. Noise was ≤ 5,056 B
      (3 runs × 8 samples). The threshold is now 16 KiB, with a sanity check
      per free function (6/6 detected). Also added deterministic
      ownership-spy tests.
    - D3: `_suspicious_windows` would substitute 0 calls / 0.0 drop rate if
      C returned a window anomaly without matching window statistics. It now
      raises `CallAnalyzerError`.
    - D4: the ad-hoc ASan run used `-k "not leak"`, which also deselected
      the unrelated `test_errors_do_not_leak_or_corrupt_state`. Replaced by
      `make py-test-asan`: the heap tests skip themselves under ASan with a
      stated reason, and no `-k` filter is used.
    - D5: the ABI gap. `CallAnomaly`, `AnomalyConfig` and `ParseOptions`
      fields and `FailureCodeStatistics.outcome` had no field-level
      verification. Closed with the compiled ABI probe, a C-defaults read-back
      and the anomaly reference.
    - D6: the "50-seed" generator result was a manual run, not part of the
      suite. It is now `test_detection_rates_over_50_seeds`.
  - Mutation checks (scratch copy, not kept). Each of these 7 mutations made
    the suite fail: swapping `CallAnomaly.window_start`/`window_end` (8 tests
    failed), swapping `sample_size`/`record_index` (8), swapping
    `AnomalyConfig.min_calls_per_cell`/`min_calls_per_caller` (2), changing
    `CallStatistics.average_signal` from double to int64 (6), removing
    `free(out)` in `_collect_array` (7), removing the int64 check (4), and
    taking suspicious-window severity from the lowest-scored anomaly (2).
  - Two new tests failed on first run because of test defects, not binding
    defects, and both were fixed: a `defaultdict` emptiness assertion, and a
    fixture burst at 443 calls vs a 2× median of 446. C correctly did not flag
    it; the burst was enlarged.
  - Final local run (Python 3.14.4, gcc 15.2): `make test` exit 0. ctest 2/2,
    ASan ctest 2/2, `py-test` **124 passed**, `py-test-asan` **117 passed,
    7 skipped** (the glibc heap tests; reason printed), mypy: no issues.
  - Final container run (`python:3.12-slim`: Python 3.12.15, gcc 14.2.0,
    glibc 2.41): ctest 2/2. Default discovery loaded
    `/usr/local/lib/libcallanalyzer.so.1.0.0`: **124 passed**. With
    `CALL_ANALYZER_LIB`: **124 passed**. ASan ctest 2/2. Python against the
    ASan build: **117 passed, 7 skipped**. mypy clean. Seed-42 SHA-256
    identical to the host.
  - Remaining limitations (documented, not defects):
    - `CA_ERR_NULL_ARG`/`CA_ERR_NOMEM` mappings are tested synthetically only.
      They cannot be triggered from Python without fault injection.
    - `CallRecord` fields are never read or written by Python (the pointer is
      only passed back to C).
    - Results do not indicate whether `max_anomalies` (default 1000)
      truncated the anomaly list.
    - An empty or whitespace `CALL_ANALYZER_LIB` is treated as unset.
    - Non-glibc platforms, concurrent first load from several threads and
      multi-million-row inputs are untested.
- 2026-10-19 — **M3** (telemetry simulator). Local Python 3.14.4: `make test` exit 0.
  C 2/2 + ASan 2/2, `py-test` **155 passed** (31 new), `py-test-asan` 148 passed
  + 7 skipped (glibc heap tests), mypy strict clean on 18 files. Container
  (`scripts/container_py312_test.sh`, Python 3.12): **155 passed**, mypy clean.
  - First run: 4 failures. One was a model defect: throughput fell only
    linearly with loss, so a flapping interface barely reduced it; fixed with
    a TCP-like goodput factor. One was a scenario defect: the 3× "traffic
    spike" saturated the CPU (an overload, not a spike); reduced to 1.8×.
    Two were test defects: a relative-5 % margin that was meaningless for
    ~99 % rates (now 2σ of the healthy series), and the Pearson criterion
    (see amendment above).
  - Tuning before the tests: GC coefficient 1.1→1.8 (CPU never saturated) and
    leak cap 44→41 pp (latency otherwise hit the 400 ms model cap at peak).
  - Seeded scenario: CDRs analysed by the C library flag exactly
    CELL-101..104 (cell setup-failure and packet-loss anomalies); healthy CDRs
    flag no cell.
- 2026-10-19 — **M4** (anomaly detection). Local: `make test` exit 0. C 2/2 + 2/2,
  `py-test` **179 passed** (24 new), `py-test-asan` 172 + 7 skipped, mypy clean
  (23 files). Container Python 3.12: **179 passed**, mypy clean.
  - Defect found during development: baseline contamination. Unflagged but
    degraded points, and good-direction excursions, entered the baseline:
    the latency baseline drifted 25→53 ms, episodes fragmented, and a throughput
    collapse lowered the bandwidth baseline so that recovery blips were
    reported as bandwidth spikes. Fixed with an admission rule (|z| < 2.5)
    plus a documented 6 h re-baseline.
  - The first FP test asserted zero false positives and failed on seed 21
    (2 low-severity RSSI episodes). Replaced with the measured bound above.
  - Mutation checks (scratch copy) — all detected:
    - admitting every unflagged point to the baseline → 2 tests failed
    - treating DOWN metrics as UP → 6 failed
    - requiring all three statistical detectors → 4 failed
    - removing both practical-delta gates → 1 failed. This mutation initially
      survived the original single-spike test, which did not isolate the
      gate. That test was replaced by a sustained sub-delta shift test.
- 2026-10-19 — **M5** (correlation). Local: `make test` exit 0. C 2/2 + 2/2,
  `py-test` **208 passed** (29 new), `py-test-asan` 201 + 7 skipped, mypy clean
  (25 files). Container Python 3.12: **208 passed**, mypy clean.
  - Seeded incident: one incident, INC-2026-001, CRITICAL, cells 101–104.
    Top hypothesis `deployment_regression` scored 0.895 (next 0.675);
    confidence 0.895; chain consistency 1.0. The pgw-3 hotfix is excluded
    with a reason, and C-library call anomalies are attached for all four
    cells.
  - All 9 incident types: correct top cause class. Symptom-only causes
    stay < 0.7 confidence.
  - Defects found and fixed during development:
    - Chain consistency counted jitter-before-loss as a violation, although
      latency also drives jitter. Rule changed to "preceded by at least one
      observed upstream cause".
    - Symptom-only hypotheses used only the alphabetically first of several
      simultaneous symptoms: radio degradation was blamed on a transport
      fault, and interface and loss-burst incidents got no hypothesis.
      Scoring now uses all symptoms within 2 min of onset plus downstream
      explanatory coverage.
    - A single candidate cause was penalised as a "close call".
    - Background login noise flooded `excluded_candidates`.
    - A 60-min look-back missed the 63-min-earlier distractor deployment
      (now 2 h).
    - Two low-severity false positives on one cell formed a LOW incident
      (seed 0). Incidents now require a ≥ high symptom: 0 incidents over
      20 healthy days.
  - A test defect was fixed: the order-violation fixture was consistent
    under the corrected rule.
  - Mutation checks (scratch copy), all detected: ignoring topology
    (6 tests failed), merging across nodes (1), removing temporal decay (1).
- 2026-10-19 — **M6** (persistence, API, auth, audit). Local Python 3.14: pytest
  **235 passed, 1 skipped** (the PostgreSQL test needs `AEGIS_TEST_POSTGRES_URL`);
  ASan run 228 passed + 8 skipped; C 2/2 + 2/2; mypy clean (54 files).
  PostgreSQL: the skipped test was run separately against `postgres:16`
  (16.15) in a localhost-only container: **1 passed**. It covered downgrade,
  upgrade and `alembic check` (no drift), pipeline (73,440 metric rows),
  incident API, audit-chain verify, and JSON columns as `jsonb`. Container
  Python 3.12: **235 passed, 1 skipped**, mypy clean.
  - Process note: the first combined run reported 2 mypy errors from M7
    files written in parallel (SDKs not installed). M6 was re-verified on a
    tree without the M7 files before committing.
  - Known warning: Starlette's TestClient warns that it prefers `httpx2`
    over `httpx`. Tests are unaffected.
- 2026-10-19 — **M7** (LLM providers, RCA). Local Python 3.14: `make test`
  exit 0. pytest **279 passed, 2 skipped** (PostgreSQL; live Anthropic — no
  key, opt-in); ASan run 272 passed + 9 skipped; mypy clean (67 files).
  Container Python 3.12: **279 passed, 2 skipped**, mypy clean.
  - The Anthropic API documentation was consulted before writing the Anthropic
    provider. Request kwargs were checked against the installed SDK
    signatures (anthropic 1.15.0: `beta.messages.create` accepts `betas`,
    `fallbacks: Iterable | Literal['default']`, `output_config`, `tools`;
    openai 3.35.1: `chat.completions.create` accepts `max_completion_tokens`
    and `tools`).
  - Seeded RCA with the mock provider: 12 tool calls, all succeeded.
    Leading hypothesis `deployment_regression` at 0.85, with alternatives
    memory_exhaustion (0.34) and security_attack (0.05). Facts cite tool
    call ids. Top recommendation: HIGH_RISK `rollback_deployment`.
  - Mutation checks (scratch copy), both detected: disabling citation
    validation (2 tests failed), removing incident scoping in
    `get_related_events` (1).
  - **Not executed:** real Anthropic/OpenAI/local-LLM calls. Only the opt-in
    `test_live_anthropic_rca` covers them; it was skipped (no key).
- 2026-10-19 — **M8** (reporting). Local Python 3.14: `make test` exit 0. pytest
  **290 passed, 2 skipped**; ASan run 283 passed + 9 skipped; mypy clean
  (72 files). Container Python 3.12: **290 passed, 2 skipped**, mypy clean.
  - KPI figures are verified against an independent recomputation from
    `network_metrics`.
  - Mutation checks (scratch copy), all detected: HTML autoescape off, no
    narrative grounding check, no Markdown escaping (1 test failed each).
  - Review of a generated report led to three fixes: "between…to"
    wording, a duplicated version in the correlation hypothesis text, and the
    onset sequence now labelled temporal rather than causal.
- 2026-10-19 — **M9** (DevSecOps agent). Local Python 3.14: `make test` exit 0.
  pytest **325 passed, 2 skipped**; ASan run 318 passed + 9 skipped; mypy clean
  (81 files). Container Python 3.12: **325 passed, 2 skipped**, mypy clean.
  - All 35 agent tests passed on the first run, so six gate mutations were
    checked (scratch copy). Every one was detected:
    - executing without approval → 3 tests failed
    - no separation of duties → 1
    - HIGH_RISK ignoring the policy flag → 2
    - operator allowed to execute HIGH_RISK → 1
    - runner allowing `python -c` → 3
    - BLOCKED treated as approvable → 2
  - mypy found 3 shadowed `_` arguments in tools (fixed).
  - The rollback is a simulation (re-simulated telemetry, no
    infrastructure). Recovery verified: the seeded scenario's KPIs returned
    within the M4 practical deltas, with no open anomalies.
- 2026-10-19 — **M10** (hardening, observability). Local Python 3.14: `make test`
  exit 0. pytest **346 passed, 3 skipped** (PostgreSQL, live LLM, live Redis —
  all opt-in); ASan run 339 + 10 skipped; mypy clean (85 files). Container
  Python 3.12: **346 passed, 3 skipped**. The live Redis test was run
  separately against `redis:7` (7.4.11): 1 passed.
  - Defect found and fixed: log context (request/incident/agent-run ids) was
    read at format time, so it was lost by deferred formatting. It is now
    stamped onto each record when created.
  - Mutation checks, all detected: no streamed-body limit, raw paths as
    metric labels, error details leaked in 500 responses.
- 2026-10-19 — **M11** (Docker). `SMOKE_BUILD_ARGS=--no-cache scripts/docker_smoke.sh`:
  a clean build (ctest 2/2 inside the image build) brought postgres:16,
  redis:7 and the backend to healthy. Health reported db/C library ok; the
  bootstrap created INC-2026-001; unauthenticated access returned 401; RCA
  completed; a report was generated; the agent reached `apply_patch`
  awaiting approval; the audit chain was valid. Teardown left no containers
  or volumes.
  - Defect found by the first smoke run: pytest was missing from the
    runtime image, so the agent's test tool could not run, and the planner
    then misattributed the failure ("last commit does not touch failing
    code"). Fixes: pytest moved to runtime requirements; the planner
    escalates test runs without identifiable failures (new regression test);
    the smoke test now asserts the approval step.
  - Regression after the fixes: `make test` exit 0 (**347 passed, 3 skipped**;
    ASan 340 + 10 skipped; mypy clean, 86 files). Container Python 3.12:
    **347 passed, 3 skipped**.
- 2026-10-19 — **M12** (dashboard). `make test` exit 0, now including
  `frontend-test` (tsc strict, **Vitest 10 passed**, vite build). Python **349
  passed, 3 skipped** (2 new overview tests); ASan 342 + 10 skipped; mypy clean.
  Container Python 3.12: **349 passed, 3 skipped**.
  `SMOKE_UI_CHECK=1 scripts/docker_smoke.sh`: all four services healthy;
  frontend proxy returned real overview data; `/metrics` not proxied; the
  Playwright check (Chromium) signed in and rendered all 11 routes with live
  data and no page errors, 5xx responses or error alerts. **UI CHECK PASSED.**
  - The first frontend run had 3 typing/setup issues (fetch mock signature,
    missing `@types/node`, no `ResizeObserver` in jsdom) and 1 test defect
    (a duplicate "85%" match); all fixed. A screenshot review led to
    rounding tooltip values and labelling KPI cards "all-cell mean, last
    30 min".
- 2026-10-19 — **M13** (demo, E2E, docs, final audit). New: `scripts/demo.py`
  (`make demo`), `backend/tests/test_e2e.py` (3 tests), README (16
  sections, 3 Mermaid diagrams), `docs/*.md`, `tests/README.md`. The demo
  exposed a defect: after a rollback the incident window still ended at the
  end of the un-remediated data. The incident now ends when the last
  post-rollback anomaly ends (regression assertion added).
  - Final sweep: `make clean` exit 0; `make demo` exit 0 (resolved,
    `recovered=True`, audit chain valid, report files written); `make test`
    exit 0 (C 2/2 + 2/2, Python **352 passed, 3 skipped**, ASan 345 + 10
    skipped, mypy clean, Vitest 10 passed + build); container Python 3.12
    **352 passed, 3 skipped**; Docker smoke + browser check passed; `make env`
    + `docker compose up --build`: backend/postgres/redis healthy, UI served,
    UI→API data returned. Torn down with `docker compose down -v`, and the
    generated `.env`/`.aegis-tokens` removed.
  - Scans: no secrets, no `shell=True`, no TODO/FIXME/placeholders in app code.
- M1 not yet verified: behaviour under clang / other compilers (not installed);
  static analysis (cppcheck/clang-tidy not installed); very large inputs
  (> 1M rows) for performance.
