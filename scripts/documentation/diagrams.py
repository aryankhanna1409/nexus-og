#!/usr/bin/env python3
"""Diagram sources for the Aegis-Net handbook and deck.

Each function below is the maintainable source of one figure: edit the data/coordinates and run
`scripts/documentation/build_all.sh` (or this file directly) to regenerate PNG + SVG under
deliverables/assets/diagrams/. Every box and arrow names a component that exists in the repository;
nothing planned-but-unbuilt is drawn (future work is not diagrammed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagram_kit import INK, LINE, MUTED, NAVY, Diagram, sequence  # noqa: E402


# 1 ---------------------------------------------------------------------------------------------
def architecture() -> None:
    d = Diagram(7.2, 6.5)
    d.group(0.1, 0.1, 7.0, 0.82, "Presentation (browser)")
    d.box(0.35, 0.42, 3.2, 0.42, "React + TypeScript dashboard", "Vite, Tailwind, Recharts - 11 pages", kind="ui", fs=8.6)
    d.box(3.85, 0.42, 3.0, 0.42, "nginx (Docker stack)", "serves the SPA, proxies /api only", kind="ui", fs=8.6)

    d.group(0.1, 1.08, 7.0, 1.0, "API layer - FastAPI (uvicorn)")
    d.box(0.35, 1.4, 4.9, 0.5, "FastAPI app + ASGI middleware", "request id, size limit, security headers, rate limit - Pydantic - bearer RBAC - audit",
          kind="py", fs=8.6, sub_fs=6.8)
    d.box(5.5, 1.4, 1.35, 0.5, "Redis", "rate-limit window", kind="store", fs=8.6, sub_fs=6.8)

    d.group(0.1, 2.24, 7.0, 1.6, "Services")
    d.box(0.3, 2.56, 1.5, 0.52, "Pipeline service", "simulate - analyse - store", kind="py", fs=8.4)
    d.box(1.95, 2.56, 1.7, 0.52, "RCA engine", "9 read-only tools", kind="ai", fs=8.4)
    d.box(3.8, 2.56, 1.4, 0.52, "Reporting", "JSON / MD / HTML", kind="py", fs=8.4)
    d.box(5.35, 2.56, 1.55, 0.52, "DevSecOps agent", "planner + policy", kind="sec", fs=8.4)
    d.box(1.95, 3.2, 1.7, 0.45, "LLM provider", "mock | anthropic | openai | local", kind="ai", fs=8.0, sub_fs=6.5)
    d.box(3.8, 3.2, 1.4, 0.45, "Jinja2 templates", "report.md / report.html", kind="py", fs=8.0, sub_fs=6.5)
    d.box(5.35, 3.2, 1.55, 0.45, "Sandbox workspace", "disposable git copy", kind="sec", fs=8.0, sub_fs=6.5)

    d.group(0.1, 4.0, 7.0, 1.12, "Analytics and native code")
    d.box(0.3, 4.34, 1.5, 0.62, "Telemetry simulator", "17 KPIs, 9 incident types", kind="ext", fs=8.3)
    d.box(1.95, 4.34, 1.55, 0.62, "Anomaly detectors", "z-score, EWMA, RoC, thresh.", kind="py", fs=8.3, sub_fs=6.5)
    d.box(3.65, 4.34, 1.45, 0.62, "Correlation engine", "clusters, causes, timeline", kind="py", fs=8.3, sub_fs=6.5)
    d.box(5.25, 4.34, 1.65, 0.62, "libcallanalyzer (C11)", "via ctypes binding", kind="native", fs=8.3)

    d.group(0.1, 5.28, 7.0, 1.12, "Persistence")
    d.cylinder(0.5, 5.58, 3.3, 0.74, "PostgreSQL 16 (Docker) / SQLite (demo)", "19 tables - Alembic 0001", fs=8.3)
    d.box(4.3, 5.62, 2.55, 0.62, "audit_logs", "append-only SHA-256 hash chain", kind="store", fs=8.3)

    d.arrow([(1.95, 0.84), (1.95, 1.4)], both=False)
    d.arrow([(5.35, 0.84), (5.35, 1.4)], "/api", label_ha="left", label_dx=0.08, label_dy=0.0, fs=7.2)
    d.arrow([(5.5, 1.65), (5.25, 1.65)], both=True)
    for x in (1.05, 2.8, 4.5, 6.1):
        d.arrow([(x, 1.9), (x, 2.56)])
    d.arrow([(2.8, 3.08), (2.8, 3.2)], both=True)
    d.arrow([(4.5, 3.08), (4.5, 3.2)])
    d.arrow([(6.1, 3.08), (6.1, 3.2)])
    d.arrow([(0.2, 2.82), (0.2, 4.34)], "runs the\npipeline", label_ha="left", label_dx=0.07, label_dy=0.0, fs=6.6)
    d.arrow([(1.8, 4.65), (1.95, 4.65)])
    d.arrow([(3.5, 4.65), (3.65, 4.65)])
    d.arrow([(5.1, 4.65), (5.25, 4.65)], dashed=True)
    d.arrow([(2.0, 4.96), (2.0, 5.6)], "store / read", label_ha="left", label_dx=0.08, label_dy=0.0, fs=7)
    d.arrow([(5.3, 4.96), (5.3, 5.62)], "audited writes", label_ha="left", label_dx=0.08, label_dy=0.0, fs=7)
    d.save("01_system_architecture")


# 2 ---------------------------------------------------------------------------------------------
def dataflow() -> None:
    d = Diagram(7.2, 4.6)
    steps = [
        ("1", "Generate", "simulator: 17 KPIs x 12 cells,\nevents, CDR CSV", "ext"),
        ("2", "Call analysis", "C library parses CSV,\nstats + robust outliers", "native"),
        ("3", "Detect", "4 detectors per KPI series\n-> anomaly episodes", "py"),
        ("4", "Correlate", "cluster, score causes,\nbuild timeline", "py"),
        ("5", "Store", "pipeline_runs, anomalies,\nincidents, events (DB)", "store"),
        ("6", "Investigate", "RCA engine + read-only\ntools + provider", "ai"),
        ("7", "Report", "JSON / Markdown / HTML\nfrom stored figures", "py"),
        ("8", "Act", "agent proposes; policy\ngates; approval; execute", "sec"),
        ("9", "Verify", "recovery check vs\npre-incident baseline", "py"),
        ("10", "Audit + show", "hash-chained log;\ndashboard reads API", "ui"),
    ]
    cols, bw, bh = 5, 1.28, 1.05
    gx = (7.2 - 0.2 - cols * bw) / (cols - 1)
    pos = []
    for i, (num, title, sub, kind) in enumerate(steps):
        r, c = divmod(i, cols)
        x, y = 0.1 + c * (bw + gx), 0.45 + r * 1.75
        d.box(x, y, bw, bh, f"{num}. {title}", sub, kind=kind, fs=8.6, sub_fs=7.0)
        pos.append((x, y))
    for i in range(len(steps) - 1):
        (x0, y0), (x1, y1) = pos[i], pos[i + 1]
        if i % cols != cols - 1:
            d.arrow([(x0 + bw, y0 + bh / 2), (x1, y1 + bh / 2)])
    # wrap-around arrow from step 5 to step 6
    x5, y5 = pos[4]
    x6, y6 = pos[5]
    d.arrow([(x5 + bw / 2, y5 + bh), (x5 + bw / 2, y5 + bh + 0.35), (x6 + bw / 2, y5 + bh + 0.35),
             (x6 + bw / 2, y6)], "state persisted: later steps read the database", label_at=0.5, label_dy=-0.12, fs=7.2)
    d.text(0.1, 0.2, "Synthetic data in, audited evidence out. Dashed line = persisted state boundary.", fs=8.2,
           color=MUTED, italic=True)
    # artefact strip
    d.text(0.1, 4.0, "Artefacts at each hand-off:", fs=8.2, bold=True)
    d.text(0.1, 4.25, "CSV + metric arrays  -  CallAnalysisResult  -  MetricAnomaly  -  Incident  -  DB rows  -  RCAAnswer  -  "
           "ReportDocument  -  AgentAction  -  recovered flag  -  AuditLogRecord", fs=7.5, color=MUTED)
    d.save("02_end_to_end_data_flow")


# 3 ---------------------------------------------------------------------------------------------
def binding_memory() -> None:
    sequence(
        "03_c_python_binding_memory",
        [("analyze_call_log()\n(Python)", "py"), ("_native.py\n(ctypes)", "py"), ("libcallanalyzer.so\n(C11)", "native"),
         ("Heap (malloc)", "store")],
        [
            {"src": 0, "dst": 1, "text": "get_library(): resolve path, load CDLL"},
            {"src": 1, "dst": 2, "text": "set argtypes / restype; check version + struct sizes"},
            {"src": 0, "dst": 2, "text": "parse_call_log_ex(path, &opts, &records, &count, &report)"},
            {"src": 2, "dst": 3, "text": "malloc CallRecord[count]"},
            {"src": 2, "dst": 0, "text": "pointer returned through out-parameter", "dashed": True},
            {"src": 0, "dst": 2, "text": "calculate_*_statistics(records, count, &out, &n)"},
            {"src": 2, "dst": 3, "text": "malloc result array (library owns until freed)"},
            {"src": 0, "dst": 0, "text": "copy each struct into dict / list (Python owns copies)", "self": True},
            {"src": 0, "dst": 2, "text": "free_*_statistics(out)  [in finally]"},
            {"src": 0, "dst": 2, "text": "free_call_records(records)  [in outer finally]"},
        ],
        notes=[{"row": 10.1, "text": "No native pointer escapes analyze_call_log(): every array is freed with its matching free_* function",
                "span": (0, 3)}],
        title="C to Python: call, ownership and release",
    )


# 4 ---------------------------------------------------------------------------------------------
def telemetry_causal() -> None:
    d = Diagram(7.2, 4.35)
    d.text(0.1, 0.2, "Simulator causal model (backend/app/simulation/model.py): each arrow is an explicit term in the code",
           fs=9.0, bold=True, color=NAVY)
    d.box(0.1, 0.6, 1.4, 0.95, "Exogenous drivers", "diurnal users, leak,\nradio penalty,\ninterface loss", kind="ext", fs=8.2, sub_fs=6.6)
    d.box(1.85, 0.45, 1.2, 0.42, "memory %", kind="py", fs=8.4)
    d.box(1.85, 1.2, 1.2, 0.42, "active users", kind="py", fs=8.4)
    d.box(3.35, 0.82, 1.2, 0.5, "CPU %", "GC pressure > 75% mem", kind="py", fs=8.4, sub_fs=6.5)
    d.box(4.85, 0.82, 1.15, 0.5, "latency", "queueing delay", kind="py", fs=8.4, sub_fs=6.8)
    d.box(6.2, 0.82, 0.9, 0.5, "jitter", kind="py", fs=8.4)
    d.box(1.85, 2.05, 1.5, 0.5, "radio penalty", "RSRP, RSSI, RSRQ, SINR", kind="py", fs=8.4, sub_fs=6.5)
    d.box(3.9, 2.05, 1.2, 0.5, "packet loss", "CPU sat., iface, radio", kind="py", fs=8.4, sub_fs=6.5)
    d.box(5.5, 2.05, 1.6, 0.5, "retransmissions", kind="py", fs=8.4)
    d.box(0.1, 3.1, 1.6, 0.46, "handover failures", kind="py", fs=8.4)
    d.box(1.95, 3.1, 1.6, 0.46, "call setup success", kind="py", fs=8.4)
    d.box(3.9, 3.1, 1.4, 0.46, "call drop rate", kind="py", fs=8.4)
    d.box(5.7, 3.1, 1.4, 0.46, "throughput", kind="py", fs=8.4)
    arrows = [((1.5, 0.9), (1.85, 0.66)), ((1.5, 1.25), (1.85, 1.42)), ((3.05, 0.66), (3.35, 0.97)),
              ((3.05, 1.42), (3.35, 1.17)), ((4.55, 1.07), (4.85, 1.07)), ((6.0, 1.07), (6.2, 1.07)),
              ((4.1, 1.32), (4.3, 2.05)), ((3.35, 2.3), (3.9, 2.3)), ((5.1, 2.3), (5.5, 2.3)),
              ((4.5, 2.55), (4.5, 3.1)), ((6.3, 2.55), (6.4, 3.1)), ((2.2, 2.55), (1.1, 3.1)),
              ((2.7, 2.55), (2.75, 3.1)), ((1.7, 3.33), (1.95, 3.33))]
    for a, b in arrows:
        d.arrow([a, b], lw=1.0, head=6)
    d.text(0.1, 3.82, "Omitted for legibility: latency also lowers throughput and call setup success and raises drops; packet loss also lowers "
           "call setup success.", fs=7.3, color=MUTED, italic=True)
    d.text(0.1, 4.08, "The seeded leak adds to memory only; every later symptom is produced by these terms, not injected directly.",
           fs=7.8, bold=True)
    d.save("04_telemetry_causal_chain")


# 5 ---------------------------------------------------------------------------------------------
def detector_pipeline() -> None:
    d = Diagram(7.2, 3.9)
    d.box(0.1, 0.45, 1.15, 0.7, "KPI series", "epochs[], values[]\nper cell, metric", kind="ext", fs=8.4, sub_fs=6.6)
    d.group(1.5, 0.15, 3.1, 2.0, "Per point, in time order (evaluate_series)")
    d.box(1.65, 0.5, 1.35, 0.4, "z-score", "window mean / std", kind="py", fs=8.0, sub_fs=6.5)
    d.box(3.1, 0.5, 1.35, 0.4, "EWMA", "tau = 900 s", kind="py", fs=8.0, sub_fs=6.5)
    d.box(1.65, 1.0, 1.35, 0.4, "rate of change", "median / MAD", kind="py", fs=8.0, sub_fs=6.5)
    d.box(3.1, 1.0, 1.35, 0.4, "static threshold", "warning / critical", kind="py", fs=8.0, sub_fs=6.5)
    d.box(1.65, 1.55, 2.8, 0.4, "practical deviation gate (min_delta)", kind="sec", fs=7.8)
    d.box(4.85, 0.5, 1.15, 0.9, "Flag rule", "threshold OR\n(z AND EWMA) OR\n(RoC AND one)", kind="py", fs=8.4, sub_fs=6.4)
    d.box(6.2, 0.5, 0.9, 0.9, "Episode", "gap <= 5 min,\n>= 2 pts or\nscore >= .85", kind="py", fs=8.4, sub_fs=6.2)
    d.box(6.2, 1.75, 0.9, 0.62, "MetricAnomaly", "severity, score", kind="py", fs=7.8, sub_fs=6.3)
    d.box(4.85, 1.75, 1.15, 0.62, "Baseline update", "only |z| < 2.5", kind="store", fs=8.0, sub_fs=6.5)
    d.arrow([(1.25, 0.8), (1.5, 0.8)])
    d.arrow([(4.6, 0.95), (4.85, 0.95)])
    d.arrow([(6.0, 0.95), (6.2, 0.95)])
    d.arrow([(6.65, 1.4), (6.65, 1.75)])
    d.arrow([(5.4, 1.4), (5.4, 1.75)], "not flagged + |z|<2.5", label_dy=-0.0, label_dx=0.08, label_ha="left", fs=6.6)
    d.arrow([(4.85, 2.06), (4.1, 2.06), (4.1, 1.95)], dashed=True, color="#0F766E")
    d.text(0.1, 2.6, "Scoring: score = 1 - 2^(-z / threshold)  (0.5 at the threshold)", fs=8.4, bold=True)
    d.text(0.1, 2.88, "Severity from score: >= 0.9 critical, >= 0.75 high, >= 0.6 medium, otherwise low.", fs=8.2)
    d.text(0.1, 3.14, "Re-baseline: after 6 h with no admitted points, the baseline is re-seeded from current values.", fs=8.2)
    d.text(0.1, 3.4, "Baseline freeze: flagged or extreme points never update the baseline, so a slow ramp cannot hide itself.",
           fs=8.2)
    d.text(0.1, 3.68, "Source: backend/app/analytics/detectors.py, engine.py, config.py.", fs=7.6, color=MUTED, italic=True)
    d.save("05_anomaly_detector_pipeline")


# 6 ---------------------------------------------------------------------------------------------
def correlation_incident() -> None:
    d = Diagram(7.2, 4.35)
    d.group(0.1, 0.1, 2.0, 3.0, "Evidence in")
    d.box(0.25, 0.45, 1.7, 0.6, "Metric anomalies", "36 episodes (seeded run)", kind="py", fs=8.4, sub_fs=6.8)
    d.box(0.25, 1.2, 1.7, 0.6, "Operational events", "deploy, config, IDS, logs", kind="ext", fs=8.4, sub_fs=6.8)
    d.box(0.25, 1.95, 1.7, 0.6, "C call anomalies", "cell + window outliers", kind="native", fs=8.4, sub_fs=6.8)
    d.box(0.25, 2.7, 1.7, 0.3, "Causal graph (static)", kind="plain", fs=7.6)
    d.group(2.3, 0.1, 3.0, 3.0, "correlate()")
    d.box(2.45, 0.45, 2.7, 0.52, "1. Cluster", "per cell <= 15 min; same node merge", kind="py", fs=8.3, sub_fs=6.8)
    d.box(2.45, 1.07, 2.7, 0.52, "2. Gate", ">= 2 metrics and one severity >= high", kind="py", fs=8.3, sub_fs=6.8)
    d.box(2.45, 1.69, 2.7, 0.52, "3. Score causes", "0.45 time + 0.35 mechanism + 0.2 topology", kind="py", fs=8.3, sub_fs=6.8)
    d.box(2.45, 2.31, 2.7, 0.6, "4. Confidence + caveats", "top x (0.6 + 0.4 consistency), cap 0.95", kind="py", fs=8.3, sub_fs=6.8)
    d.group(5.55, 0.1, 1.55, 3.0, "Incident")
    d.box(5.65, 0.45, 1.35, 0.55, "symptoms", "ordered by onset", kind="store", fs=8.2, sub_fs=6.6)
    d.box(5.65, 1.1, 1.35, 0.55, "suspected causes", "status: hypothesis", kind="store", fs=8.2, sub_fs=6.6)
    d.box(5.65, 1.75, 1.35, 0.55, "excluded", "with reasons", kind="store", fs=8.2, sub_fs=6.6)
    d.box(5.65, 2.4, 1.35, 0.55, "timeline", "caveats, call evid.", kind="store", fs=8.2, sub_fs=6.6)
    d.arrow([(1.95, 0.75), (2.45, 0.71)], lw=1.1)
    d.arrow([(1.95, 1.5), (2.45, 1.33)], lw=1.1)
    d.arrow([(1.95, 2.25), (2.45, 1.95)], lw=1.1)
    d.arrow([(1.95, 2.85), (2.45, 2.05)], lw=1.1, dashed=True)
    d.arrow([(5.15, 1.95), (5.65, 1.37)])
    d.arrow([(5.15, 2.61), (5.65, 2.67)])
    d.group(0.1, 3.3, 7.0, 0.95, "What the engine computes")
    d.text(0.25, 3.78, "Temporal precedence, topology match and agreement with a fixed causal graph; the output is a ranked list of hypotheses.", fs=8.1)
    d.text(0.25, 4.03, "It does not prove causation: confidence is capped at 0.95 and every incident carries a caveat saying so.", fs=8.1)
    d.save("06_event_correlation_incident_formation")


# 7 ---------------------------------------------------------------------------------------------
def rca_sequence() -> None:
    msgs = [
        {"src": 0, "dst": 1, "text": "investigate(incident)"},
        {"src": 1, "dst": 2, "text": "system prompt + ids and symptom names + 9 tool schemas"},
        {"src": 2, "dst": 1, "text": "tool_calls: name + JSON arguments", "dashed": True},
        {"src": 1, "dst": 3, "text": "strict schema + Pydantic validation, then run"},
        {"src": 3, "dst": 4, "text": "SELECT scoped to the incident's run"},
        {"src": 4, "dst": 3, "text": "rows (bounded)", "dashed": True},
        {"src": 3, "dst": 1, "text": "JSON result <= 16 KB, tool_call_id", "dashed": True},
        {"src": 1, "dst": 2, "text": "tool results (errors flagged is_error)"},
        {"src": 2, "dst": 1, "text": "final text: one JSON object", "dashed": True},
        {"src": 1, "dst": 1, "text": "validate RCAAnswer + citations (<= 3 attempts)", "self": True},
        {"src": 1, "dst": 4, "text": "persist RCA, tool calls, recommendations"},
        {"src": 1, "dst": 0, "text": "completed | failed (never invented)", "dashed": True},
    ]
    for i, m in enumerate(msgs):
        m["row"] = i + (1 if i >= 3 else 0)
    sequence(
        "07_llm_tool_calling_rca_sequence",
        [("API\n/investigate", "py"), ("RCA engine", "ai"), ("LLMProvider", "ai"), ("Tool registry\n(read-only)", "sec"),
         ("Database", "store")],
        msgs,
        notes=[{"row": 3, "text": "loop (steps 2 to 8): up to 10 steps, at most 8 tool calls per step", "span": (1, 3)}],
        title="RCA investigation: model asks, engine validates and executes",
        row=0.36,
    )


# 8 ---------------------------------------------------------------------------------------------
def agent_lifecycle() -> None:
    d = Diagram(7.2, 3.3)
    names = [("OBSERVE", "read-only inspection"), ("ANALYZE", "RCA, diff, deps"), ("PLAN", "propose action +\nrationale"),
             ("ACT", "policy gate;\napproval"), ("VERIFY", "tests, re-scan,\nrecovery check"), ("CLOSE", "report,\nresolve")]
    w, gap = 1.0, 0.2
    x0 = (7.2 - (6 * w + 5 * gap)) / 2
    for i, (n, s) in enumerate(names):
        kind = "sec" if n == "ACT" else "py"
        d.box(x0 + i * (w + gap), 0.5, w, 0.95, n, s, kind=kind, fs=9.0, sub_fs=7.0)
        if i:
            d.arrow([(x0 + i * (w + gap) - gap, 0.97), (x0 + i * (w + gap), 0.97)])
    # early exit
    d.arrow([(x0 + 2 * (w + gap) + w / 2, 1.45), (x0 + 2 * (w + gap) + w / 2, 1.95), (x0 + 5 * (w + gap) + w / 2, 1.95),
             (x0 + 5 * (w + gap) + w / 2, 1.45)], "denied or blocked: skip ACT, close with a report", label_dy=0.14,
            dashed=True, color="#B91C1C", fs=7.4)
    d.text(0.1, 0.2, "Run phase never moves backwards; the planner is deterministic (one playbook per scenario).", fs=8.4,
           color=MUTED, italic=True)
    d.text(0.1, 2.35, "Every action row stores tool, risk class, rationale (before execution), arguments and result.", fs=8.2)
    d.text(0.1, 2.62, "Every proposal, block, approval, denial, execution and closure writes a hash-chained audit row.", fs=8.2)
    d.text(0.1, 2.89, "Scenarios: vulnerable_dependency, failed_ci, production_anomaly. The LLM never picks tools or arguments.",
           fs=8.2)
    d.save("08_devsecops_agent_lifecycle")


# 9 ---------------------------------------------------------------------------------------------
def risk_approval() -> None:
    d = Diagram(7.2, 4.55)
    heads = [("Risk class", 0.1, 1.45), ("Policy decision", 1.75, 1.4), ("Approval", 3.35, 1.45), ("Execution", 5.0, 1.4),
             ("Recorded", 6.6, 0.5)]
    for t, x, w in heads:
        d.text(x + w / 2, 0.25, t, fs=8.6, bold=True, color=NAVY, ha="center")
    rows = [
        ("READ_ONLY / LOW_RISK", "ui", "allow", "none needed", "runs automatically", "ui"),
        ("REQUIRES_APPROVAL", "sec", "needs_approval", "approver who is not\nthe run's initiator", "operator or higher\n(policy re-checked)", "sec"),
        ("HIGH_RISK\n(default: flag off)", "sec", "deny: disabled\nby policy", "-", "status: blocked;\nRCA recommends a human", "plain"),
        ("HIGH_RISK\n(AGENT_ALLOW_HIGH_RISK)", "sec", "needs_approval", "approver who is not\nthe run's initiator", "admin only\n(policy re-checked)", "sec"),
        ("BLOCKED", "sec", "deny: never runs", "-", "no implementation\n(delete_infrastructure)", "plain"),
    ]
    for i, (cls, ck, pol, app, exe, ek) in enumerate(rows):
        y = 0.5 + i * 0.78
        h = 0.62
        d.box(0.1, y, 1.45, h, cls, kind=ck, fs=7.8)
        d.box(1.75, y, 1.4, h, pol, kind="py", fs=7.8)
        d.box(3.35, y, 1.45, h, app, kind="sec" if app != "-" else "plain", fs=7.6)
        d.box(5.0, y, 1.4, h, exe, kind=ek if ek != "plain" else "plain", fs=7.4)
        d.box(6.6, y, 0.5, h, "audit", kind="store", fs=7.0)
        for x0, x1 in ((1.55, 1.75), (3.15, 3.35), (4.8, 5.0), (6.4, 6.6)):
            d.arrow([(x0, y + h / 2), (x1, y + h / 2)], lw=1.0, head=5)
    d.text(0.1, 4.45, "Source: backend/app/agents/policy.py (evaluate, executor_role); service.py (execute_action re-checks every rule).",
           fs=7.4, color=MUTED, italic=True)
    d.save("09_risk_classification_approval")


# 10 --------------------------------------------------------------------------------------------
def er_diagram() -> None:
    from matplotlib.patches import Rectangle

    from diagram_kit import KINDS

    d = Diagram(7.2, 8.6)
    rowh = 0.185

    def table(x: float, y: float, w: float, name: str, cols: list[str], kind: str = "py") -> tuple[float, float, float, float]:
        h = 0.3 + rowh * len(cols)
        d.box(x, y, w, h, "", kind=kind, round_=0.05)
        d.ax.add_patch(Rectangle((x, y), w, 0.27, fc=KINDS[kind][1], ec=KINDS[kind][1], alpha=0.22, zorder=2))
        d.text(x + w / 2, y + 0.135, name, fs=8.0, bold=True, ha="center")
        for i, c in enumerate(cols):
            d.text(x + 0.07, y + 0.4 + i * rowh, c, fs=6.8, mono=True)
        return (x, y, w, h)

    A, B, C = 0.1, 2.55, 5.0
    wa, wb, wc = 2.2, 2.2, 2.1
    nm = table(A, 0.15, wa, "network_metrics", ["PK id", "FK run_id", "epoch, cell_id, node_id", "metric, value"])
    pr = table(B, 0.15, wb, "pipeline_runs", ["PK id", "scenario, seed, status", "data_start/end_epoch", "fingerprint, params"], "store")
    an = table(C, 0.15, wc, "anomalies", ["PK anomaly_id", "FK run_id", "metric, cell_id, node_id", "start/end_epoch, value", "severity, anomaly_score"])
    ev = table(A, 1.55, wa, "operational_events", ["PK event_id", "FK run_id", "type, source, severity", "node_id, cell_id", "message, attributes"])
    ca = table(B, 1.55, wb, "call_analysis_runs", ["PK id", "FK run_id", "totals, rates", "failure_codes (JSON)"])
    cn = table(C, 1.55, wc, "call_anomalies", ["FK analysis_id", "type, severity, subject", "value, baseline, z_score"])
    dp = table(A, 3.0, wa, "deployments", ["PK deployment_id", "FK run_id", "service, node_id", "from/to_version", "status, rolled_back_epoch"])
    cc = table(B, 3.0, wb, "call_cell_statistics", ["FK analysis_id", "cell_id, rates", "signal, packet loss"])
    au = table(C, 3.0, wc, "audit_logs", ["PK id", "epoch, actor, role, action", "resource, outcome", "request_id, details", "prev_hash, hash (unique)"], "store")
    ic = table(A, 4.6, wa, "incident_cells", ["FK incident_id", "cell_id, node_id"])
    inc = table(B, 4.6, wb, "incidents", ["PK incident_id", "FK run_id", "severity, status", "confidence, top_cause_type", "symptoms, causes (JSON)"])
    rca = table(C, 4.6, wc, "root_cause_analyses", ["PK id", "FK incident_id", "provider, model, status", "confidence", "facts, hypotheses (JSON)"], "ai")
    ia = table(A, 5.4, wa, "incident_anomalies", ["FK incident_id", "FK anomaly_id"])
    ie = table(A, 6.2, wa, "incident_events", ["FK incident_id", "epoch, type, actor"])
    rp = table(B, 6.2, wb, "reports", ["PK report_id", "FK incident_id", "FK rca_id (SET NULL)", "payload, markdown, html"], "ai")
    rec = table(C, 6.15, wc, "recommendations", ["PK id", "FK rca_id", "action, risk_class, agent_tool"], "ai")
    sf = table(A, 7.4, wa, "security_findings", ["PK finding_id", "source, category, severity", "status, details"], "sec")
    ag = table(B, 7.4, wb, "agent_runs", ["PK run_id", "scenario, state, status", "incident_id (no FK)"], "sec")
    aa = table(C, 7.4, wc, "agent_actions", ["PK action_id", "FK run_id", "tool, risk_class, status"], "sec")
    col = "#475569"
    # run_id bus between columns A and B (pipeline_runs -> network_metrics, operational_events, deployments)
    d.arrow([(B, 0.5), (2.42, 0.5), (2.42, 0.5), (A + wa, 0.5)], color=col, lw=0.9, head=5)
    d.ax.plot([2.42, 2.42], [0.5, 3.35], color=col, lw=0.9, zorder=1)
    d.arrow([(2.42, 1.9), (A + wa, 1.9)], color=col, lw=0.9, head=5)
    d.arrow([(2.42, 3.35), (A + wa, 3.35)], color=col, lw=0.9, head=5)
    d.arrow([(B + wb, 0.5), (C, 0.5)], color=col, lw=0.9, head=5)
    d.arrow([(B + wb / 2, pr[1] + pr[3]), (B + wb / 2, 1.55)], color=col, lw=0.9, head=5)
    d.arrow([(B + wb, 1.95), (C, 1.95)], color=col, lw=0.9, head=5)
    d.arrow([(B + wb / 2, ca[1] + ca[3]), (B + wb / 2, 3.0)], color=col, lw=0.9, head=5)
    # incidents bus to A
    d.ax.plot([2.42, 2.42], [4.95, 6.55], color=col, lw=0.9, zorder=1)
    d.arrow([(B, 4.95), (2.42, 4.95)], color=col, lw=0.9, head=5)
    for y in (4.95, 5.7, 6.5):
        d.arrow([(2.42, y), (A + wa, y)], color=col, lw=0.9, head=5)
    d.arrow([(B + wb, 5.2), (C, 5.2)], color=col, lw=0.9, head=5)
    d.arrow([(B + wb / 2, inc[1] + inc[3]), (B + wb / 2, 6.2)], color=col, lw=0.9, head=5)
    d.arrow([(C + wc / 2, rca[1] + rca[3]), (C + wc / 2, 6.15)], color=col, lw=0.9, head=5)
    d.arrow([(B + wb, 7.9), (C, 7.9)], color=col, lw=0.9, head=5)
    d.text(0.1, 8.35, "Arrows run from parent (PK) to child (FK). Not drawn: pipeline_runs -> incidents (run_id); anomalies -> incident_anomalies; ",
           fs=6.9, color=MUTED)
    d.text(0.1, 8.5, "root_cause_analyses -> reports (rca_id). audit_logs and security_findings are standalone tables (no foreign keys).",
           fs=6.9, color=MUTED)
    d.save("10_database_entity_relationships")


# 11 --------------------------------------------------------------------------------------------
def deployment_topology() -> None:
    d = Diagram(7.2, 4.35)
    d.group(0.1, 0.1, 7.0, 3.75, "Docker Compose project: aegis-net (host ports bound to 127.0.0.1)")
    d.box(0.3, 0.55, 1.7, 0.75, "frontend", "nginx 1.27-alpine\n:80 -> host :8080", kind="ui", fs=8.8, sub_fs=7.0)
    d.box(2.55, 0.55, 2.1, 0.75, "backend", "python:3.12-slim, non-root\nuvicorn :8000 -> host :8000", kind="py", fs=8.8, sub_fs=6.9)
    d.cylinder(5.2, 0.45, 1.7, 0.95, "postgres:16", "volume pgdata", fs=8.8)
    d.box(5.2, 1.95, 1.7, 0.7, "redis:7", "no persistence\nrate-limit store", kind="store", fs=8.8, sub_fs=6.9)
    d.box(2.55, 1.95, 2.1, 0.7, "volume aegis-data", "/data: agent workspaces", kind="store", fs=8.6, sub_fs=6.9)
    d.arrow([(2.0, 0.92), (2.55, 0.92)], "/api only", label_dy=-0.12, fs=7)
    d.arrow([(4.65, 0.8), (5.2, 0.8)], "SQLAlchemy", label_dy=-0.12, fs=7)
    d.arrow([(4.1, 1.3), (5.4, 1.95)], "rate limit", label_dy=0.0, fs=7, label_at=0.55, label_dx=0.25)
    d.arrow([(3.6, 1.3), (3.6, 1.95)])
    d.text(0.3, 1.75, "depends_on: backend healthy", fs=7.4, color=MUTED, italic=True)
    d.text(0.3, 1.97, "-> frontend starts after /api/health", fs=7.4, color=MUTED, italic=True)
    d.box(0.3, 2.85, 6.6, 0.82, "Backend image: two stages", "1) build and ctest libcallanalyzer (gcc, cmake)   2) runtime: .so in /usr/local/lib, pip deps, git, user aegis\n"
          "entrypoint: print library version -> alembic upgrade head -> optional demo bootstrap -> uvicorn", kind="native", fs=8.4, sub_fs=6.9)
    d.text(0.1, 4.05, "Browser -> http://127.0.0.1:8080 (dashboard); API docs at http://127.0.0.1:8000/docs. /metrics is not proxied by nginx.",
           fs=8.0, color=MUTED)
    d.save("11_deployment_container_topology")


# 12 --------------------------------------------------------------------------------------------
def dashboard_navigation() -> None:
    d = Diagram(7.2, 4.55)
    d.box(0.1, 1.3, 1.1, 0.7, "Sign in", "token kept in\nsessionStorage", kind="ui", fs=8.6, sub_fs=6.8)
    d.group(1.4, 0.1, 5.7, 3.1, "Layout: sidebar navigation, 11 routes")
    items = [("/", "Dashboard"), ("/network", "Network Overview"), ("/calls", "Call Analytics"), ("/anomalies", "Anomalies"),
             ("/incidents", "Incidents"), ("/incidents/:id", "Incident detail"), ("/rca", "Root Cause Analysis"),
             ("/reports", "AI Reports"), ("/agent", "DevSecOps Agent"), ("/security", "Security"), ("/audit", "Audit Log")]
    pos = {}
    for i, (route, name) in enumerate(items):
        row, col = divmod(i, 4)
        x, y = 1.55 + col * 1.4, 0.45 + row * 0.9
        d.box(x, y, 1.3, 0.68, name, route, kind="ui", fs=7.8, sub_fs=6.8, mono_sub=True)
        pos[route] = (x, y)
    d.arrow([(1.2, 1.5), (1.55, 0.79)], lw=1.0)
    ix, iy = pos["/incidents"]
    dx, dy = pos["/incidents/:id"]
    d.arrow([(ix + 1.3, iy + 0.34), (dx, dy + 0.34)], "open", fs=6.8, label_dy=-0.12)
    d.text(0.1, 3.5, "Key workflows", fs=8.8, bold=True, color=NAVY)
    d.text(0.1, 3.78, "1. Triage: Dashboard -> Incidents -> Incident detail -> Investigate (RCA) -> Generate report.", fs=8.0)
    d.text(0.1, 4.03, "2. Remediate: DevSecOps Agent -> Run scenario -> Approve (approver) -> Execute (operator / admin) -> Audit Log.", fs=8.0)
    d.text(0.1, 4.3, "Buttons show for every signed-in user; the server enforces the role on each call (Chapter 11).", fs=7.8, color=MUTED, italic=True)
    d.save("12_dashboard_navigation_workflows")


# 13 end-to-end sequence --------------------------------------------------------------------------
def e2e_sequence() -> None:
    sequence(
        "13_end_to_end_sequence",
        [("Operator\n/ demo", "ui"), ("API", "py"), ("Pipeline", "py"), ("C library", "native"), ("Analytics", "py"),
         ("DB", "store"), ("RCA + LLM", "ai"), ("Agent", "sec")],
        [
            {"src": 0, "dst": 1, "text": "POST /pipeline/run"},
            {"src": 1, "dst": 2, "text": "simulate()"},
            {"src": 2, "dst": 3, "text": "CDR CSV"},
            {"src": 3, "dst": 2, "text": "stats + anomalies", "dashed": True},
            {"src": 2, "dst": 4, "text": "KPI series + events"},
            {"src": 4, "dst": 2, "text": "incident", "dashed": True},
            {"src": 2, "dst": 5, "text": "persist run"},
            {"src": 0, "dst": 1, "text": "POST /incidents/{id}/investigate"},
            {"src": 1, "dst": 6, "text": "tools + validate"},
            {"src": 6, "dst": 5, "text": "read evidence / save RCA"},
            {"src": 0, "dst": 1, "text": "POST /reports/generate"},
            {"src": 1, "dst": 5, "text": "figures from DB + narrative"},
            {"src": 0, "dst": 1, "text": "POST /agent/investigate"},
            {"src": 1, "dst": 7, "text": "playbook, policy"},
            {"src": 7, "dst": 5, "text": "action: awaiting_approval"},
            {"src": 0, "dst": 1, "text": "approve (approver) + execute (admin)"},
            {"src": 1, "dst": 7, "text": "re-check policy, run"},
            {"src": 7, "dst": 5, "text": "verify, resolve, audit rows"},
            {"src": 0, "dst": 1, "text": "GET dashboard views / audit verify"},
        ],
        width=7.2, row=0.31, top=1.0, fs=7.2,
        title="One incident, end to end (API calls shown as the dashboard or demo issues them)",
    )


def main() -> None:
    for fn in (architecture, dataflow, binding_memory, telemetry_causal, detector_pipeline, correlation_incident,
               rca_sequence, agent_lifecycle, risk_approval, er_diagram, deployment_topology, dashboard_navigation,
               e2e_sequence):
        fn()
        print("rendered", fn.__name__)


if __name__ == "__main__":
    main()
