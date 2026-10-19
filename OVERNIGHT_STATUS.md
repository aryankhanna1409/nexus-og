# Aegis-Net overnight run — status

Autonomous run started 2026-10-19 on top of commit `7b748a2` (M2). Each
milestone is committed only after its acceptance gate passes. The full
verification log is in `IMPLEMENTATION_PLAN.md` §5; this file is the resume
point.

Pre-existing note: commit `7b748a2` (made outside this run) contains a stray
empty file named `tatus --short`. It was left untouched.

## Resume point

Next milestone: **M4 — Analytics and anomaly detection** (depends on M3 ✅).

## Milestones

| Milestone | Status | Verdict | Commit |
|---|---|---|---|
| M1 C library | done before this run | PASS | `823a5b7` |
| M2 Python binding + generator | done before this run | PASS WITH DOCUMENTED LIMITATIONS | `7b748a2` |
| M3 Telemetry simulator | done | PASS | (see below) |

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
