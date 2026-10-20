#!/usr/bin/env python3
"""Extracts real, reproducible evidence from the Aegis-Net code for the handbook figures.

Run with the backend virtualenv (it needs numpy and the app package):

    backend/.venv/bin/python scripts/documentation/extract_evidence.py

Writes deliverables/assets/charts/evidence.json. Everything in it is computed by the
repository's own simulator, detectors and correlation engine (seed 7, the same
scenario as `make demo`); nothing is typed in by hand.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

import numpy as np  # noqa: E402

from app.analytics import detect_anomalies, series_from_simulation  # noqa: E402
from app.analytics.correlation import correlate  # noqa: E402
from app.analytics.detectors import ewma, moving_average, rolling_std  # noqa: E402
from app.analytics.engine import iso  # noqa: E402
from app.analytics.sources import events_from_simulation, series_lookup  # noqa: E402
from app.simulation import seeded_memory_leak_scenario, simulate  # noqa: E402

CHART_METRICS = ["memory_utilization", "cpu_utilization", "latency_ms", "packet_loss_pct", "call_drop_rate",
                 "throughput_mbps"]
CELLS = ["CELL-101", "CELL-105"]  # affected cell (pgw-1) and an unaffected control cell (pgw-2)


def main() -> None:
    scenario = seeded_memory_leak_scenario(seed=7)
    result = simulate(scenario)
    series = series_from_simulation(result)
    anomalies = detect_anomalies(series)
    incidents = correlate(anomalies, events_from_simulation(result), series=series_lookup(series))
    assert len(incidents) == 1, f"expected exactly one incident, got {len(incidents)}"
    incident = incidents[0]

    out: dict[str, object] = {
        "seed": 7,
        "start": iso(int(result.epochs[0])),
        "minutes": int(len(result.epochs)),
        "fingerprint": result.fingerprint(),
        "epochs": [int(e) for e in result.epochs],
        "series": {cell: {m: [round(float(v), 4) for v in result.metrics[cell][m]] for m in CHART_METRICS}
                   for cell in CELLS},
        "anomaly_count": len(anomalies),
        "anomalies_by_cell_metric": [
            {"cell": a.cell_id, "metric": a.metric, "onset": iso(a.start_epoch), "onset_epoch": a.start_epoch,
             "severity": a.severity, "score": a.anomaly_score, "baseline": round(a.baseline, 2),
             "worst": round(a.value, 2), "detectors": list(a.detectors)}
            for a in anomalies if a.metric in CHART_METRICS and a.cell_id in CELLS],
        "affected_cells": sorted({c for i in incidents for c in i.affected_cells}),
        "incident": incident.to_dict(),
        "deployments": [{"deployment_id": d.deployment_id, "epoch": d.epoch, "time": iso(d.epoch),
                         "node": d.node_id, "from": d.from_version, "to": d.to_version}
                        for d in result.deployments],
    }

    # Worked example for the handbook: a 10-point series with a step change.
    values = np.array([50.0, 51.0, 49.0, 50.0, 52.0, 50.0, 51.0, 49.0, 50.0, 80.0])
    epochs = np.arange(len(values), dtype=np.int64) * 60
    base = values[:-1]
    mean, std = float(base.mean()), float(base.std())
    out["worked_example"] = {
        "values": values.tolist(),
        "baseline_mean_first9": round(mean, 4),
        "baseline_std_first9": round(std, 4),
        "z_of_last": round((values[-1] - mean) / max(std, 1.0), 3),
        "moving_average_last_5min": round(float(moving_average(epochs, values, 300)[-1]), 4),
        "rolling_std_last_5min": round(float(rolling_std(epochs, values, 300)[-1]), 4),
        "ewma_tau900": [round(float(v), 4) for v in ewma(epochs, values, 900.0)],
        "score_at_z4": round(1 - math.pow(2, -4 / 4.0), 3),
        "score_at_z8": round(1 - math.pow(2, -8 / 4.0), 3),
        "score_at_z12": round(1 - math.pow(2, -12 / 4.0), 3),
    }

    target = REPO_ROOT / "deliverables" / "assets" / "charts" / "evidence.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"wrote {target.relative_to(REPO_ROOT)}: {len(anomalies)} anomaly episodes, "
          f"incident {incident.incident_id} {incident.severity}, confidence {incident.confidence}")


if __name__ == "__main__":
    main()
