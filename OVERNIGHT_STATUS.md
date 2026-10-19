# Aegis-Net overnight run — status

Autonomous run started 2026-10-19 on top of commit `7b748a2` (M2). Each
milestone is committed only after its acceptance gate passes. The full
verification log is in `IMPLEMENTATION_PLAN.md` §5; this file is the resume
point.

Pre-existing note: commit `7b748a2` (made outside this run) contains a stray
empty file named `tatus --short`. It was left untouched.

## Resume point

Next milestone: **M5 — Correlation engine** (depends on M2 ✅, M4 ✅).

## Milestones

| Milestone | Status | Verdict | Commit |
|---|---|---|---|
| M1 C library | done before this run | PASS | `823a5b7` |
| M2 Python binding + generator | done before this run | PASS WITH DOCUMENTED LIMITATIONS | `7b748a2` |
| M3 Telemetry simulator | done | PASS | `7d1edf6` |
| M4 Anomaly detection | done | PASS | (this commit; see git log) |

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
