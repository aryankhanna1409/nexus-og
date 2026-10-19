# Aegis-Net Architecture

This document describes components, data flow, and the contracts between them.
Where a contract is implemented in code, the code is authoritative and this
document is updated alongside it (CLAUDE.md). Sections marked *(planned)* are
designs for milestones not yet implemented — see `IMPLEMENTATION_PLAN.md`.

## 1. Component overview

```mermaid
flowchart TB
  subgraph Sources["Data sources (synthetic)"]
    CDR[Call logs / CDR CSV]
    NET[Network counters]
    APP[Application metrics + logs]
    SEC[Security events]
    DEP[Deployment / CI events]
    GIT[Demo service git repo]
  end

  subgraph Ingest["Ingestion"]
    CLIB["libcallanalyzer.so (C)"]
    BIND["call_analyzer (ctypes)"]
    SIM["Telemetry simulator"]
  end

  subgraph Analytics["Analytics & detection (Python/numpy)"]
    DET[Anomaly detectors]
    COR[Correlation engine]
  end

  subgraph AI["AI investigation"]
    LLM["LLMProvider (mock / anthropic / openai / local)"]
    TOOLS[RCA read-only tool registry]
    RCA[RCA engine]
  end

  REP[Reporting engine]
  AGT[DevSecOps agent + policy engine + executor]
  DB[(PostgreSQL)]
  RDS[(Redis)]
  API[FastAPI REST API]
  UI[React dashboard]

  CDR --> CLIB --> BIND --> COR
  SIM --> NET & APP & SEC & DEP
  NET & APP --> DET --> COR
  SEC & DEP --> COR
  COR --> DB
  RCA --> LLM
  RCA --> TOOLS --> DB
  RCA --> REP
  AGT --> RCA
  AGT --> GIT
  AGT --> DB
  REP --> DB
  API --> DB
  API --> RDS
  API --> RCA & REP & AGT
  UI --> API
```

| Component | Location | Language | Responsibility |
|---|---|---|---|
| Call analyzer library | `c-library/` | C11 | Parse/validate CDR CSV, aggregate, detect call-level outliers |
| Binding | `backend/call_analyzer/` | Python (ctypes) | Load `.so`, marshal structs → dicts, map errors to exceptions |
| Telemetry simulator | `backend/app/simulation/` | Python | Causal time-series model, incident injection, event streams *(planned M3)* |
| Analytics | `backend/app/analytics/` | Python/numpy | Detectors, scoring, correlation into incidents *(planned M4–M5)* |
| LLM layer | `backend/app/llm/` | Python | Provider abstraction *(planned M7)* |
| RCA engine | `backend/app/rca/` | Python | Tool-driven investigation loop, schema-validated output *(planned M7)* |
| Reporting | `backend/app/reporting/` | Python/Jinja2 | JSON/Markdown/HTML reports *(planned M8)* |
| DevSecOps agent | `backend/app/agents/` | Python | State machine, allowlisted tools, policy, approvals *(planned M9)* |
| API | `backend/app/api/` | FastAPI | REST + OpenAPI, auth, RBAC, rate limits *(planned M6/M10)* |
| Database | `backend/alembic/` | PostgreSQL | Relational entities + JSON evidence *(planned M6)* |
| Frontend | `frontend/` | React/TS | NOC dashboard *(planned M12)* |

## 2. End-to-end data flow

```mermaid
sequenceDiagram
  participant Sim as Simulator
  participant C as libcallanalyzer
  participant An as Detectors
  participant Co as Correlation
  participant DB as Postgres
  participant R as RCA engine
  participant L as LLMProvider
  participant Rep as Reporting
  participant Ag as Agent
  Sim->>C: call_logs.csv
  Sim->>An: metric series + events
  C-->>Co: call stats + call anomalies
  An-->>Co: metric anomalies
  Co->>DB: Incident + IncidentEvents
  Ag->>R: investigate(incident_id)
  loop bounded steps
    R->>L: messages + tool schemas
    L-->>R: tool_call(name, args) | final answer
    R->>DB: read via allowlisted tool
  end
  R->>DB: RootCauseAnalysis (+ evidence JSON)
  R->>Rep: generate report
  Ag->>DB: AgentAction (proposed, risk class)
  Note over Ag: executes only if policy allows / approved
  Ag->>DB: AuditLog rows for every step
```

## 3. Interfaces

### 3.1 C library (`c-library/include/call_analyzer.h`) — implemented (M1)

The header is the authoritative contract. Conventions:

- All functions returning `int` return `CA_OK` (0) or a negative `CaStatus`
  error; `call_analyzer_strerror()` gives a static message.
- Output arrays are allocated by the library and released only with the
  matching `free_*` function. Outputs are set to `NULL`/0 on failure.
- No global mutable state; functions are re-entrant and thread-safe given
  distinct outputs.
- Fixed-size string fields (`char[32]`) are always NUL-terminated; inputs that
  would not fit are rejected, never truncated.

Input CSV schema (header optional, columns in this order):

```
timestamp,caller,callee,cell_id,duration,status_code,signal_strength,packet_loss
2026-03-01T14:05:00Z,+15550001,+15550002,CELL-102,184,200,-82,1
```

| Field | Type | Valid range |
|---|---|---|
| timestamp | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SS[Z]` | years 1970–9999 |
| caller, callee | `[0-9A-Za-z+*#._-]`, 1–31 chars | |
| cell_id | `[0-9A-Za-z._-]`, 1–31 chars | |
| duration | integer seconds | 0–86400 |
| status_code | integer, see below | 100–999 |
| signal_strength | integer dBm | −150–0 |
| packet_loss | integer percent | 0–100 |

Status-code classification (SIP-inspired, defined by Aegis-Net):

| Range | Class | Meaning |
|---|---|---|
| 200–299 | `CALL_COMPLETED` | Call completed normally |
| 900–999 | `CALL_DROPPED` | Established call terminated abnormally (e.g. 901 radio link failure, 902 handover failure, 903 congestion, 904 core timeout) |
| 300–899 | `CALL_SETUP_FAILED` | Call never established (e.g. 408 timeout, 486 busy, 503 unavailable) |
| 100–199 | `CALL_UNKNOWN` | Provisional — not counted as success or failure |

Rates: `success_rate = completed / total`; `drop_rate = dropped / (completed + dropped)`
(drops relative to established calls, the conventional definition);
`setup_failure_rate = setup_failed / total`.

Main entry points (see header for full signatures and struct definitions):

```c
int parse_call_log(const char *filepath, CallRecord **records, size_t *count);
int parse_call_log_ex(const char *filepath, const ParseOptions *opts,
                      CallRecord **records, size_t *count, ParseReport *report);
int parse_call_log_buffer(const char *data, size_t len, const ParseOptions *opts,
                          CallRecord **records, size_t *count, ParseReport *report);
int calculate_statistics(const CallRecord *, size_t, CallStatistics *);
int calculate_cell_statistics(const CallRecord *, size_t, CellStatistics **, size_t *);
int calculate_failure_code_statistics(const CallRecord *, size_t, FailureCodeStatistics **, size_t *);
int calculate_time_window_statistics(const CallRecord *, size_t, int64_t window_seconds,
                                     TimeWindowStatistics **, size_t *);
int calculate_caller_statistics(const CallRecord *, size_t, CallerStatistics **, size_t *);
int detect_call_anomalies(const CallRecord *, size_t, const AnomalyConfig *,
                          CallAnomaly **, size_t *);
```

Anomaly detection uses robust z-scores, `z = (x − median) / max(1.4826·MAD, floor)`,
across cells, time windows, callers and individual durations, with minimum
sample sizes and absolute-difference floors to suppress noise. Score is
`1 − 2^(−z/threshold)` (0.5 at the threshold), mapped to severity bands.

### 3.2 Python binding — *(planned M2)*

```python
from call_analyzer import analyze_call_log
result: dict = analyze_call_log("data/call_logs/call_logs.csv", window_seconds=300)
```

Returned dict keys: `total_calls, successful_calls, failed_setup_calls,
dropped_calls, success_rate, drop_rate, average_duration, average_signal,
average_packet_loss, cells[], failure_codes[], time_windows[], callers[],
anomalies[], suspicious_time_windows[], parse_report{}`. Errors raise
`CallAnalyzerError` subclasses carrying the C status code. Library path:
`CALL_ANALYZER_LIB` env var, else `c-library/build/libcallanalyzer.so`, else
`/usr/local/lib/libcallanalyzer.so` (Docker).

### 3.3 Analytics and correlation — *(planned M4–M5)*

```python
@dataclass(frozen=True) class MetricSeries: metric: str; cell_id: str | None; timestamps: np.ndarray; values: np.ndarray
class Detector(Protocol):
    def detect(self, series: MetricSeries) -> list[DetectorHit]: ...
def detect_anomalies(series: Iterable[MetricSeries], cfg: DetectionConfig) -> list[AnomalySchema]
def correlate(metric_anoms, call_anoms, events, topology, cfg) -> list[IncidentSchema]
```

`AnomalySchema` matches spec §6 exactly; `IncidentSchema` matches spec §7 and
adds `events: list[IncidentEventSchema]` (ordered, typed: deployment, metric_anomaly,
call_anomaly, security, lifecycle).

### 3.4 LLM provider and RCA tools — *(planned M7)*

```python
class LLMProvider(ABC):
    def generate(self, messages: list[Message], *, max_tokens: int) -> LLMResponse
    def tool_call(self, messages: list[Message], tools: list[ToolSpec], *, max_tokens: int) -> LLMResponse  # text and/or ToolCall list
```

RCA tools are read-only Python functions registered with a Pydantic argument
model; the registry validates arguments, enforces time-range limits, and returns
JSON-serialisable results tagged with a `tool_call_id`. The RCA result schema is
spec §8 plus `facts`, `inferences`, `hypotheses` lists; each evidence item must
reference a `tool_call_id`, otherwise the result is rejected.

### 3.5 DevSecOps agent — *(planned M9)*

```python
class RiskClass(StrEnum): READ_ONLY, LOW_RISK, REQUIRES_APPROVAL, HIGH_RISK, BLOCKED
@dataclass class AgentTool: name; risk: RiskClass; args_model: type[BaseModel]; run: Callable
class PolicyEngine: def decide(tool, args, context) -> PolicyDecision  # allow | needs_approval | deny
class CommandRunner: def run(argv: Sequence[str], cwd: Path, timeout_s: float) -> CommandResult  # executable allowlist, no shell
```

The LLM may only select a tool name and structured arguments; it never supplies
a command string. Every proposed action is stored as an `AgentAction` with
`rationale`, `risk_class`, `status` (proposed → approved → executing → succeeded/failed,
or denied) and audit rows. Execution happens in a disposable copy of
`demo-workspace/`.

### 3.6 Database — *(planned M6)*

Relational tables: `call_records` (optional bulk import), `call_analysis_runs`,
`network_metrics` (metric, cell_id, ts, value; indexed on (metric, cell_id, ts)),
`anomalies`, `incidents`, `incident_events`, `root_cause_analyses`,
`recommendations`, `agent_actions`, `security_findings`, `deployments`,
`reports`, `audit_logs`. JSON columns only for `evidence`, `tool_outputs`,
`report_payload`, `action_args`.

### 3.7 REST API — *(planned M6–M10)*

Endpoints of spec §16 under `/api`, OpenAPI at `/docs`. Auth: `Authorization:
Bearer <token>`. Role requirements: `viewer` for GET, `operator` for
investigate/report generation, `approver` for approve, `admin` for HIGH_RISK
execution. All mutating endpoints write `audit_logs`.

### 3.8 Frontend — *(planned M12)*

React/TS SPA served by nginx; talks only to the REST API through a typed
client in `frontend/src/services/api.ts` whose types mirror the Pydantic schemas.

## 4. Trust boundaries

1. CSV input → C parser: untrusted; bounded line/field lengths, strict validation.
2. LLM output → RCA/agent: untrusted; schema-validated, allowlisted tools only.
3. HTTP clients → API: authenticated, RBAC, rate-limited, size-limited.
4. Agent → OS: fixed executables, argv lists, timeouts, confined cwd, minimal env.

## 5. Development and deployment strategy

Local development (WSL2):

- C: `make c-build`, `make c-test`, `make c-test-asan` (CMake out-of-tree builds under `c-library/build*`).
- Python: `backend/.venv`, `pytest`; the binding finds the locally built `.so`.
- Frontend: Node is not installed in WSL; use the `node` container (`make frontend-test`) *(planned)*.

Docker (`docker compose up --build`) *(planned M11–M12)*:

| Service | Image | Notes |
|---|---|---|
| `postgres` | `postgres:16` | volume, healthcheck |
| `redis` | `redis:7` | rate limit + queue |
| `backend` | multi-stage: stage 1 builds + tests the C library with CMake; stage 2 `python:3.12-slim` with `.so` in `/usr/local/lib` | runs `alembic upgrade head` then uvicorn |
| `frontend` | multi-stage: `node` build → `nginx` | proxies `/api` to backend |

Secrets come only from `.env` (git-ignored); `.env.example` documents variables.
With no `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`, `LLM_PROVIDER` falls back to `mock`.
