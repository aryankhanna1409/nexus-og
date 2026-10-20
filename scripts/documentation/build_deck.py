#!/usr/bin/env python3
"""Builds AegisNet_Technical_Presentation.pptx, AegisNet_Presenter_Notes.md and presentation_outline.md.

Diagrams, tables and charts are native PowerPoint objects (editable); screenshots are the original
images from docs/source/aegis.docx placed without distortion. Slide text and notes come from deck_notes.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deck_kit import (  # noqa: E402
    BLUE, INK, MUTED, NAVY, SH, SW, arrow, bar_chart, blank, chip, header, line_chart, new_presentation, node, picture,
    rect, source_note, table, text,
)
from deck_notes import SLIDES  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DELIV = REPO / "deliverables"
SHOTS = DELIV / "assets" / "screenshots"
OUT = DELIV / "presentation" / "AegisNet_Technical_Presentation.pptx"
NOTES_MD = DELIV / "presentation" / "AegisNet_Presenter_Notes.md"
OUTLINE_MD = DELIV / "documentation" / "presentation_outline.md"
EV = json.loads((DELIV / "assets" / "charts" / "evidence.json").read_text(encoding="utf-8"))
TOTAL = len(SLIDES)

SHOT = {k: next(SHOTS.glob(f"shot_{k:02d}_*.png")) for k in range(1, 14)}


def head_commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def s_title(prs):  # noqa: ANN001, ANN201
    s = blank(prs)
    rect(s, 0, 0, SW, SH, NAVY, None, shape=MSO_SHAPE.RECTANGLE, name="background")
    rect(s, 0.8, 2.0, 0.12, 2.2, "3B82F6", None, shape=MSO_SHAPE.RECTANGLE, name="accent")
    text(s, 1.15, 1.85, 11, 0.9, "AEGIS-NET", size=60, color="FFFFFF", bold=True, name="title")
    text(s, 1.15, 2.95, 11, 1.2, "From network symptoms to audited remediation", size=30, color="BFDBFE", name="subtitle")
    text(s, 1.15, 4.1, 11, 0.5, "Technical walkthrough: C analysis, anomaly detection, correlation, AI root-cause analysis, "
         "and a policy-gated DevSecOps agent", size=16, color="DBEAFE", name="description")
    x = 1.15
    for label, kind, w in (("VERIFIED", "V", 1.3), ("UNVERIFIED HERE", "U", 1.9), ("SIMULATED", "S", 1.3), ("NOT IMPLEMENTED", "N", 1.9)):
        chip(s, x, 5.2, w, label, kind, size=11, h=0.34)
        x += w + 0.15
    text(s, 1.15, 5.7, 11, 0.4, "Status tags used on the following slides", size=12, color="93C5FD", italic=True)
    text(s, 1.15, 6.6, 11.5, 0.5, f"All data is synthetic. Prototype, not production. Repository commit {head_commit()} - "
         f"{date.today().isoformat()}", size=12, color="93C5FD", name="notice")
    return s


def s_problem(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    cards = [
        ("Evidence is scattered", [("Metrics", "ext"), ("Deployments", "ext"), ("IDS alerts", "ext"), ("Logs", "ext")],
         "Four tools, four formats, one question: what changed?"),
        ("Symptoms arrive in a cascade", None, "One fault, nine alerts. The first symptom is rarely the one people notice."),
        ("Decisions need an audit trail", [("Rollback?", "sec"), ("Approval", "sec"), ("Record", "store")],
         "A production rollback is risky and must be justified, approved and recorded."),
    ]
    for i, (title, items, body) in enumerate(cards):
        x = 0.55 + i * 4.15
        rect(s, x, 1.6, 3.95, 3.1, "F8FAFC", "CBD5E1", name=f"card {i + 1}")
        text(s, x + 0.2, 1.7, 3.6, 0.5, title, size=17, color=NAVY, bold=True)
        if items is None:
            text(s, x + 0.2, 2.2, 3.6, 0.9, [[("9 alerts ", {"size": 34, "bold": True, "color": "B91C1C"}), ("\u2192 1 fault", {"size": 34, "bold": True, "color": NAVY})]], size=34)
            text(s, x + 0.2, 3.1, 3.6, 0.6, "memory, CPU, latency, jitter, loss, retransmits, drops, setup success, throughput", size=11.5, color=MUTED)
        if items:
            for k, (lab, kind) in enumerate(items):
                node(s, x + 0.25 + (k % 2) * 1.8, 2.35 + (k // 2) * 0.62, 1.65, 0.5, lab, kind=kind, size=12)
        text(s, x + 0.2, 3.85, 3.6, 0.8, body, size=13, color=INK)
    chain = [("memory", "py"), ("CPU", "py"), ("latency", "py"), ("packet loss", "py"), ("dropped calls", "sec")]
    text(s, 0.55, 4.95, 6, 0.3, "The seeded incident as an operator sees it", size=13, color=NAVY, bold=True)
    for k, (lab, kind) in enumerate(chain):
        x = 0.55 + k * 2.1
        node(s, x, 5.3, 1.7, 0.6, lab, kind=kind, size=13)
        if k < 4:
            arrow(s, x + 1.7, 5.6, x + 2.1, 5.6)
    text(s, 0.55, 6.1, 12.2, 0.55, [[("Automated: ", {"bold": True, "color": NAVY}), ("evidence gathering, ordering, bookkeeping.   ", {}),
                                    ("Still human: ", {"bold": True, "color": "B91C1C"}), ("judgement, approval, accepting risk.", {})]],
         size=14)
    return s


def s_goals(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    tiles = [
        ("C call analysis", "Strict CSV parsing, per-cell and per-window statistics, robust outliers", [("VERIFIED", "V", 1.2)]),
        ("Telemetry and detection", "17 KPIs, 9 incident types, 4 interpretable detectors", [("SIMULATED DATA", "S", 1.55), ("VERIFIED", "V", 1.2)]),
        ("Correlation and RCA", "Ranked hypotheses; nine read-only tools; schema-validated answers", [("MOCK VERIFIED", "V", 1.5), ("LIVE LLM UNVERIFIED", "U", 2.0)]),
        ("Reports", "JSON, Markdown, HTML computed from stored figures", [("VERIFIED", "V", 1.2), ("NO PDF", "N", 1.0)]),
        ("DevSecOps agent", "Deterministic playbooks, risk classes, approvals, sandbox", [("VERIFIED", "V", 1.2), ("ROLLBACK SIMULATED", "S", 2.0)]),
        ("Platform", "FastAPI, RBAC, hash-chained audit, React dashboard, Docker", [("VERIFIED", "V", 1.2), ("DOCKER NOT RE-RUN", "U", 1.9)]),
    ]
    for i, (title, body, chips) in enumerate(tiles):
        col, row = i % 3, i // 3
        x, y = 0.55 + col * 4.15, 1.65 + row * 2.55
        rect(s, x, y, 3.95, 2.35, "F8FAFC", "CBD5E1", name=f"tile {i + 1}")
        text(s, x + 0.2, y + 0.12, 3.6, 0.45, title, size=18, color=NAVY, bold=True)
        text(s, x + 0.2, y + 0.62, 3.6, 0.95, body, size=13)
        cx = x + 0.2
        for label, kind, w in chips:
            chip(s, cx, y + 1.75, w, label, kind, size=10.5)
            cx += w + 0.12
    return s


def s_flow(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    steps = [("1 Generate", "simulator, events, CDR CSV", "ext"), ("2 Call analysis", "C library, ctypes", "native"),
             ("3 Detect", "4 detectors per KPI", "py"), ("4 Correlate", "cluster, score causes", "py"),
             ("5 Store", "19 tables", "store"), ("6 Investigate", "RCA + read-only tools", "ai"),
             ("7 Report", "JSON / MD / HTML", "py"), ("8 Act", "playbook + policy gate", "sec"),
             ("9 Verify", "recovery vs baseline", "py"), ("10 Audit + show", "hash chain, dashboard", "ui")]
    w, h, gap = 2.2, 1.35, 0.3
    for i, (t, sub, kind) in enumerate(steps):
        r, c = divmod(i, 5)
        x, y = 0.55 + c * (w + gap), 1.7 + r * 2.1
        node(s, x, y, w, h, t, sub, kind=kind, size=15, sub_size=12)
        if c < 4:
            arrow(s, x + w, y + h / 2, x + w + gap, y + h / 2)
    xr, xl, yb, yt = 0.55 + 4 * (w + gap) + w / 2, 0.55 + w / 2, 1.7 + h, 1.7 + 2.1
    ym = (yb + yt) / 2
    arrow(s, xr, yb, xr, ym, head=False, color="64748B")
    arrow(s, xr, ym, xl, ym, head=False, color="64748B")
    arrow(s, xl, ym, xl, yt, color="64748B")
    text(s, 3.2, ym - 0.36, 6.4, 0.3, "state persisted: later stages read the database", size=11.5, color=MUTED, italic=True,
         align=PP_ALIGN.CENTER)
    rect(s, 0.55, 5.95, 12.2, 0.7, "F0FDF4", "86EFAC", name="recorded result")
    text(s, 0.75, 6.02, 11.8, 0.55, [[("Recorded run: ", {"bold": True, "color": "14532D"}),
                                      ("make demo (seed 7) - INC-2026-001 CRITICAL, 13 steps, exit 0, rollback verified, audit chain valid (24 rows).", {})]],
         size=14, anchor=MSO_ANCHOR.MIDDLE)
    return s


def s_arch(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    layers = [
        ("Presentation", 1.55, [("React + TypeScript dashboard", "11 pages", "ui", 5.2), ("nginx", "serves SPA, proxies /api", "ui", 4.6)]),
        ("API", 2.55, [("FastAPI + ASGI middleware", "Pydantic, bearer RBAC, limits, audit", "py", 7.6), ("Redis", "rate limit", "store", 2.2)]),
        ("Services", 3.55, [("Pipeline", "simulate, analyse, store", "py", 2.3), ("RCA engine + LLM provider", "9 read-only tools", "ai", 3.2),
                            ("Reporting", "JSON / MD / HTML", "py", 2.2), ("DevSecOps agent", "planner, policy, sandbox", "sec", 2.4)]),
        ("Analytics + native", 4.55, [("Simulator", "17 KPIs", "ext", 2.0), ("Detectors", "z, EWMA, RoC, thresh.", "py", 2.4),
                                      ("Correlation", "causes, timeline", "py", 2.2), ("libcallanalyzer (C11)", "ctypes binding", "native", 2.9)]),
        ("Persistence", 5.55, [("PostgreSQL 16 / SQLite", "19 tables, Alembic", "store", 5.2), ("audit_logs", "SHA-256 hash chain", "store", 4.4)]),
    ]
    for label, y, nodes in layers:
        rect(s, 0.55, y - 0.08, 12.2, 0.9, "F8FAFC", "E2E8F0", dashed=True, name=f"layer {label}")
        text(s, 0.65, y - 0.06, 1.6, 0.3, label.upper(), size=10, color=MUTED, bold=True)
        x = 2.0
        for title, sub, kind, w in nodes:
            node(s, x, y + 0.04, w, 0.7, title, sub, kind=kind, size=12.5, sub_size=10)
            x += w + 0.25
    for y in (2.47, 3.47, 4.47, 5.47):
        arrow(s, 6.4, y, 6.4, y + 0.12, lw=1.5)
    source_note(s, "Interfaces: C header, REST API (OpenAPI), database schema. Trust boundaries: CSV, LLM output, HTTP, agent to OS.", 6.62)
    return s


def s_call(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    flow = [("CDR CSV", "8 columns", "ext"), ("libcallanalyzer", "parse, aggregate, outliers", "native"),
            ("ctypes binding", "struct check, free_*", "py"), ("Result dict", "stats + anomalies", "store")]
    for i, (t, sub, kind) in enumerate(flow):
        y = 1.6 + i * 0.95
        node(s, 0.55, y, 3.0, 0.7, t, sub, kind=kind, size=14, sub_size=11)
        if i < 3:
            arrow(s, 2.05, y + 0.7, 2.05, y + 0.95)
    text(s, 0.55, 5.3, 3.4, 0.95, [
        "- strict warnings, -Werror",
        "- ASan/UBSan/LSan + fault injection",
        "- drop = dropped / (completed + dropped)",
    ], size=11.5)
    picture(s, SHOT[3], 4.0, 1.6, 8.75, 4.55, "Call Analytics page: totals, drop rate by cell, status codes and C-library anomalies")
    source_note(s, "Screenshot: Call Analytics page (supplied document, synthetic data). Bars CELL-101 to 104 are the cells behind the faulty gateway. "
                "Status-code classes are this project's convention.", 6.35)
    chip(s, 0.55, 6.72, 1.2, "VERIFIED", "V")
    text(s, 1.85, 6.7, 8.5, 0.3, "make c-test and make c-test-asan: 2 of 2 passed each; 28 test functions", size=11, color=MUTED)
    return s


def s_telemetry(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    picture(s, SHOT[2], 0.55, 1.55, 8.0, 3.9, "Network Overview page: eight KPI cards and a 12-cell latency chart")
    text(s, 0.55, 5.5, 8.0, 0.3, "Screenshot: Network Overview (supplied document, synthetic data)", size=10.5, color=MUTED, italic=True)
    chain = [("deploy 2.4.1\n14:05, pgw-1", "ext"), ("memory leak", "py"), ("GC pressure -> CPU", "py"), ("queueing latency", "py"),
             ("packet loss", "py"), ("dropped calls", "sec")]
    for i, (t, kind) in enumerate(chain):
        y = 1.55 + i * 0.68
        node(s, 9.0, y, 3.7, 0.52, t, kind=kind, size=12)
        if i < 5:
            arrow(s, 10.85, y + 0.52, 10.85, y + 0.68, lw=1.5)
    text(s, 9.0, 5.7, 3.8, 0.9, ["- 17 KPIs x 12 cells x 1 min, seed 7", "- distractor: hotfix on pgw-3 at 13:10"], size=12)
    chip(s, 0.55, 5.95, 1.3, "SIMULATED", "S")
    text(s, 2.0, 5.92, 6.6, 0.8, "A testing instrument, not real traffic. Detector results here do not show how detectors "
         "would perform on production telemetry.", size=12, color="7F1D1D")
    return s


def s_detect(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    w = EV["worked_example"]
    line_chart(s, 0.55, 1.5, 5.0, 3.1, [str(i) for i in range(10)],
               {"value": w["values"], "baseline mean (9 pts)": [w["baseline_mean_first9"]] * 10,
                "EWMA tau 900 s": w["ewma_tau900"]}, ["1D4ED8", "0F766E", "6D28D9"], "Worked example: step from ~50 to 80",
               size=10)
    picture(s, SHOT[4], 5.8, 1.5, 6.95, 3.1, "Anomalies page: critical episodes with onset, baseline, worst value and detectors",
            crop=(0.0, 0.0, 0.0, 0.2))
    cards = [("z-score", "(x - mean) / max(std, floor), 60 min window"), ("EWMA", "alpha = 1 - exp(-dt/tau), tau 900 s"),
             ("Threshold", "warning / critical per KPI, e.g. latency 100 / 200 ms"), ("Rate of change", "per-minute change vs median / MAD, z >= 5")]
    for i, (t, sub) in enumerate(cards):
        node(s, 0.55 + i * 3.08, 4.8, 2.95, 1.05, t, sub, kind="py", size=14, sub_size=11)
    text(s, 0.55, 5.95, 12.2, 0.75, [[("Flag: ", {"bold": True, "color": NAVY}),
                                      ("threshold OR (z AND EWMA) OR (RoC AND one), and the deviation must pass a practical minimum.  ", {}),
                                      ("Score: ", {"bold": True, "color": NAVY}), ("1 - 2^(-z / threshold); 0.5 at the threshold.  ", {}),
                                      ("Baseline: ", {"bold": True, "color": NAVY}), ("only |z| < 2.5 points update it.", {})]], size=12.5)
    source_note(s, "Chart data from the repository's own EWMA helper. Screenshot: Anomalies page, critical filter (supplied document, synthetic data).", 6.72)
    return s


def s_corr(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    ev = [("Metric anomalies", "36 episodes", "py"), ("Operational events", "deploy, config, IDS", "ext"),
          ("C call anomalies", "cell + window", "native"), ("Causal graph", "fixed, hand-written", "plain")]
    for i, (t, sub, kind) in enumerate(ev):
        node(s, 0.55, 1.6 + i * 1.0, 2.5, 0.8, t, sub, kind=kind, size=13, sub_size=10.5)
        arrow(s, 3.05, 2.0 + i * 1.0, 3.55, 3.2, lw=1.25)
    steps = [("1 Cluster", "per cell <= 15 min; same node merges"), ("2 Gate", ">= 2 metrics, one severity >= high"),
             ("3 Score causes", "0.45 time + 0.35 mechanism + 0.20 topology"), ("4 Confidence", "top x (0.6 + 0.4 consistency); cap 0.95")]
    for i, (t, sub) in enumerate(steps):
        node(s, 3.55, 1.6 + i * 1.0, 4.3, 0.8, t, sub, kind="py", size=14, sub_size=11)
        if i < 3:
            arrow(s, 5.7, 2.4 + i * 1.0, 5.7, 2.6 + i * 1.0, lw=1.5)
    outs = [("symptoms", "ordered by onset"), ("suspected causes", "status: hypothesis"), ("excluded", "with reasons"), ("timeline + caveats", "")]
    for i, (t, sub) in enumerate(outs):
        node(s, 10.0, 1.6 + i * 1.0, 2.75, 0.8, t, sub or None, kind="store", size=13, sub_size=10.5)
        arrow(s, 7.85, 3.2, 10.0, 2.0 + i * 1.0, lw=1.25)
    rect(s, 0.55, 5.75, 12.2, 0.95, "FFFBEB", "FCD34D", name="caveat")
    text(s, 0.75, 5.8, 11.8, 0.85, [[("Correlation is not causation. ", {"bold": True, "color": "92400E"}),
                                     ("The engine ranks hypotheses by time order, topology and a fixed causal graph; every cause carries status "
                                      "\"hypothesis\" and the incident carries a caveat to that effect.", {})]], size=14, anchor=MSO_ANCHOR.MIDDLE)
    chip(s, 0.55, 6.78, 1.2, "VERIFIED", "V")
    text(s, 1.85, 6.76, 9, 0.3, "29 tests; 0 incidents over 20 healthy days (recorded); seeded run recomputed for this handbook", size=11, color=MUTED)
    return s


def s_timeline(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    inc = EV["incident"]
    t0, t1 = 13 * 60, 15 * 60  # 13:00 to 15:00
    ax_x, ax_w, ax_y = 0.8, 6.6, 3.25

    def xpos(h: int, m: int) -> float:
        return ax_x + ax_w * ((h * 60 + m) - t0) / (t1 - t0)

    rect(s, ax_x, ax_y - 0.02, ax_w, 0.04, "94A3B8", None, shape=MSO_SHAPE.RECTANGLE, name="time axis")
    for h, m, label in ((13, 0, "13:00"), (14, 0, "14:00"), (15, 0, "15:00")):
        text(s, xpos(h, m) - 0.35, ax_y + 0.12, 0.7, 0.25, label, size=10.5, color=MUTED, align=PP_ALIGN.CENTER)
    events = [(14, 5, "deploy", "sec", 1), (14, 13, "memory", "py", 2), (14, 31, "CPU", "py", 1), (14, 40, "latency", "py", 2),
              (14, 50, "loss", "py", 3), (14, 53, "drops", "sec", 1)]
    for h, m, label, kind, lvl in events:
        x = xpos(h, m)
        col = "B91C1C" if kind == "sec" else "1D4ED8"
        yy = ax_y - 0.3 - lvl * 0.4
        arrow(s, x, yy + 0.3, x, ax_y - 0.02, color=col, lw=1.25)
        text(s, x - 0.55, yy, 1.1, 0.3, [[(f"{h}:{m:02d} ", {"bold": True, "color": col}), (label, {})]], size=10.5, align=PP_ALIGN.CENTER)
    xh = xpos(13, 10)
    arrow(s, xh, ax_y + 0.55, xh, ax_y + 0.02, color="64748B", lw=1.25, dashed=True)
    text(s, xh - 0.5, ax_y + 0.58, 3.4, 0.5, "13:10 hotfix to pgw-3: excluded (other node)", size=10.5, color=MUTED)
    text(s, 0.55, 1.42, 7, 0.3, "INC-2026-001 timeline (UTC, recomputed from seed 7)", size=13, color=NAVY, bold=True)
    causes = inc["suspected_causes"]
    cats = [c["cause_type"].replace("_", " ") for c in causes]
    bar_chart(s, 7.6, 1.45, 5.2, 2.9, cats,
              {"temporal x 0.45": [round(c["temporal_score"] * 0.45, 3) for c in causes],
               "mechanism x 0.35": [round(c["mechanism_score"] * 0.35, 3) for c in causes],
               "topology x 0.20": [round(c["topology_score"] * 0.20, 3) for c in causes]},
              ["1D4ED8", "0F766E", "B45309"], "Cause score = sum of weighted terms", stacked=True, horizontal=True, size=10)
    picture(s, SHOT[5], 0.55, 4.45, 7.0, 2.05, "Incidents page: INC-2026-001, critical, leading hypothesis deployment_regression 89%")
    text(s, 7.8, 4.5, 5.0, 2.0, [
        [("0.8947 ", {"bold": True, "color": NAVY, "size": 18}), ("deployment_regression", {})],
        [("0.675 ", {"bold": True, "color": NAVY, "size": 18}), ("memory_exhaustion", {})],
        "- deployment was 8 min before onset: temporal exp(-8/30) = 0.766",
        "- chain consistency 1.0, margin 0.22: confidence 0.8947",
    ], size=13)
    source_note(s, "Screenshot: Incidents page (supplied document). 89% is the correlation confidence; the RCA states 85% separately.", 6.6)
    return s


def s_rca(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    picture(s, SHOT[6], 0.55, 1.5, 7.6, 4.1, "RCA page: observed evidence with tool-call ids, hypotheses and recommended remediation")
    text(s, 0.55, 5.65, 7.6, 0.3, "Screenshot: Root Cause Analysis page, provider mock (supplied document, synthetic data)", size=10.5,
         color=MUTED, italic=True)
    text(s, 8.45, 1.5, 4.3, 3.4, [
        [("Model asks, engine decides", {"bold": True, "color": NAVY, "size": 15})],
        "- 9 read-only, incident-scoped tools",
        "- arguments validated twice (JSON schema, Pydantic)",
        "- results capped at 16 KB; at most 10 steps, 8 calls per step",
        "- answer: one JSON object (RCAAnswer)",
        "- facts must cite successful tool calls",
        "- leading hypothesis = root cause; confidence <= 0.95",
        "- 3 attempts, then status failed; nothing invented",
    ], size=12.5)
    rect(s, 8.45, 5.0, 4.3, 1.55, "FEF2F2", "FCA5A5", name="mock warning")
    text(s, 8.6, 5.05, 4.0, 1.45, [[("The mock is not an LLM. ", {"bold": True, "color": "7F1D1D"}),
                                    ("It is a rule-based investigator using the same tools and validation. Live providers were never called.", {})]],
         size=12.5, anchor=MSO_ANCHOR.MIDDLE)
    chip(s, 0.55, 6.1, 1.5, "MOCK VERIFIED", "V")
    chip(s, 2.15, 6.1, 2.0, "LIVE LLM UNVERIFIED", "U")
    text(s, 0.55, 6.5, 7.6, 0.3, "12 tool calls in the seeded run; RCA confidence 85%", size=11.5, color=MUTED)
    return s


def s_report(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    picture(s, SHOT[7], 0.55, 1.5, 7.9, 4.35, "AI Reports page: executive summary and KPI table for INC-2026-001")
    text(s, 0.55, 5.9, 7.9, 0.3, "Screenshot: AI Reports page (supplied document, synthetic data)", size=10.5, color=MUTED, italic=True)
    text(s, 8.75, 1.5, 4.0, 4.3, [
        [("Grounded by construction", {"bold": True, "color": NAVY, "size": 15})],
        "- every figure computed from the database",
        "- baseline = mean of the hour before onset",
        "- summary prose accepted only if all its numbers appear in the context; else template",
        "- JSON, Markdown, HTML from one document model",
        "- HTML autoescaped; CSP default-src 'none'; sandboxed iframe in the UI",
        "- root cause always labelled a hypothesis",
    ], size=12.5)
    chip(s, 8.75, 5.95, 1.2, "VERIFIED", "V")
    chip(s, 10.05, 5.95, 1.6, "PDF NOT BUILT", "N")
    return s


def s_agent(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    phases = [("OBSERVE", "py"), ("ANALYZE", "py"), ("PLAN", "py"), ("ACT", "sec"), ("VERIFY", "py"), ("CLOSE", "py")]
    for i, (p, kind) in enumerate(phases):
        node(s, 0.55 + i * 2.05, 1.5, 1.75, 0.55, p, kind=kind, size=13)
        if i < 5:
            arrow(s, 0.55 + i * 2.05 + 1.75, 1.775, 0.55 + (i + 1) * 2.05, 1.775, lw=1.5)
    picture(s, SHOT[8], 0.55, 2.3, 7.7, 3.7, "DevSecOps Agent page: a closed production-anomaly run and runs awaiting approval")
    text(s, 0.55, 6.05, 7.7, 0.3, "Screenshot: DevSecOps Agent page (supplied document, synthetic data; bottom edge cropped in the source)",
         size=10.5, color=MUTED, italic=True)
    text(s, 8.55, 2.3, 4.2, 3.7, [
        [("Three scenarios", {"bold": True, "color": NAVY, "size": 15})],
        "- vulnerable dependency: scan, pin bump (approval), tests, re-scan",
        "- failed CI: reproduce, diff, revert patch (approval), tests + linter",
        "- production anomaly: RCA, rollback proposal (HIGH_RISK), verify",
        [("Not an LLM planner: ", {"bold": True, "color": "7F1D1D"}), ("playbooks are pure functions of earlier results; rationale stored before execution.", {})],
    ], size=12.5)
    chip(s, 8.55, 6.2, 1.2, "VERIFIED", "V")
    chip(s, 9.85, 6.2, 2.1, "ROLLBACK SIMULATED", "S")
    return s


def s_policy(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    rows = [["Risk class", "Policy", "Approval", "Executed by"],
            ["READ_ONLY / LOW_RISK", "allow", "none", "agent, automatically"],
            ["REQUIRES_APPROVAL", "needs approval", "approver, not the initiator", "operator or higher"],
            ["HIGH_RISK (flag off)", "deny: blocked", "-", "nobody (human acts)"],
            ["HIGH_RISK (flag on)", "needs approval", "approver, not the initiator", "admin only"],
            ["BLOCKED", "deny", "-", "never"]]
    table(s, 0.55, 1.5, 7.3, rows, [2.0, 1.45, 2.2, 1.65], size=11.5, row_h=0.42, name="risk table")
    text(s, 0.55, 4.2, 7.3, 2.4, [
        "- policy re-checked inside execute_action, immediately before running",
        "- separation of duties: the run's initiator cannot approve",
        "- 20 allowlisted tools; commands: python -m pytest|pyflakes and 9 git subcommands, no shell",
        "- audit row hash = SHA-256(content + previous hash); verify needs admin",
        "- rewriting a whole suffix could forge the chain: external anchoring not implemented",
    ], size=12.5)
    picture(s, SHOT[11], 8.15, 1.5, 4.6, 3.1, "Audit Log page: hash chain valid, 38 rows", crop=(0.0, 0.0, 0.0, 0.0))
    text(s, 8.15, 4.62, 4.6, 0.5, "Audit log: chain valid (38 rows); policy block and denied self-approval visible", size=10.5, color=MUTED, italic=True)
    picture(s, SHOT[9], 8.15, 5.2, 4.6, 0.95, "Separation-of-duties message")
    chip(s, 8.15, 6.3, 1.2, "VERIFIED", "V")
    text(s, 9.45, 6.27, 3.4, 0.3, "36 agent tests, 22 security tests", size=10.5, color=MUTED)
    return s


def s_dashboard(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    picture(s, SHOT[1], 0.55, 1.5, 8.6, 4.5, "Dashboard: health score, incident, RCA headline, KPI cards, latency chart, agent run")
    text(s, 0.55, 6.05, 8.6, 0.3, "Screenshot: Dashboard (supplied document, synthetic data)", size=10.5, color=MUTED, italic=True)
    qs = [("Healthy?", "score 62 = 100 - 30 (critical) - 8 (4 cells)"), ("What, how severe?", "INC-2026-001, CRITICAL, CELL-101..104"),
          ("Why?", "RCA headline, 85%, a hypothesis"), ("KPIs and chart", "latency on affected cells, anomaly window shaded"),
          ("What is the AI doing?", "agent run and its actions"), ("Did it work?", "not yet: incident investigating")]
    for i, (q, a) in enumerate(qs):
        y = 1.5 + i * 0.75
        s1 = node(s, 9.4, y, 0.5, 0.6, str(i + 1), kind="ui", size=15)
        text(s, 10.0, y - 0.02, 2.8, 0.7, [[(q, {"bold": True, "color": NAVY})], a], size=11.5)
    text(s, 9.4, 6.05, 3.4, 0.6, "Token in sessionStorage; roles enforced by the server.", size=11, color=MUTED, italic=True)
    return s


def s_api(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    rows = [["Endpoint group", "Minimum role", "Routes"],
            ["health", "public", "1"], ["pipeline run / list", "operator / viewer", "2"], ["calls, network, incidents (reads)", "viewer", "7"],
            ["investigate (RCA), report generate, agent start", "operator", "3"], ["reports, RCA, deployments, findings, agent reads", "viewer", "9"],
            ["agent approve", "approver", "1"], ["agent execute", "operator (admin if HIGH_RISK)", "1"],
            ["audit list / verify", "operator / admin", "2"]]
    table(s, 0.55, 1.5, 7.2, rows, [3.7, 2.4, 1.1], size=11.5, row_h=0.4, name="endpoint table")
    text(s, 0.55, 5.25, 7.2, 1.4, [
        "- bodies use extra=\"forbid\"; ids, metrics and cells are pattern-checked",
        "- 401 / 403 / 404 / 409 / 413 / 422 / 429 mapped; 500 carries only a request id",
        "- every response has X-Request-ID; /metrics is not proxied",
    ], size=12)
    groups = [("Run data", "pipeline_runs, network_metrics, anomalies, operational_events, deployments", "py"),
              ("Call analysis", "call_analysis_runs, call_cell_statistics, call_anomalies", "native"),
              ("Incidents and AI", "incidents, incident_cells, incident_anomalies, incident_events, root_cause_analyses, recommendations, reports", "ai"),
              ("Agent and audit", "agent_runs, agent_actions, security_findings, audit_logs", "sec")]
    text(s, 8.1, 1.45, 4.6, 0.3, "19 tables (one Alembic migration)", size=14, color=NAVY, bold=True)
    for i, (t, sub, kind) in enumerate(groups):
        node(s, 8.1, 1.85 + i * 1.18, 4.65, 1.05, t, sub, kind=kind, size=13, sub_size=10)
    chip(s, 8.1, 6.62, 1.2, "VERIFIED", "V")
    chip(s, 9.4, 6.62, 2.8, "POSTGRESQL TEST SKIPPED HERE", "U", size=9.5)
    return s


def s_docker(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    rect(s, 0.55, 1.5, 8.2, 4.1, "F8FAFC", "CBD5E1", dashed=True, name="compose project")
    text(s, 0.7, 1.55, 6, 0.3, "COMPOSE PROJECT aegis-net  (ports bound to 127.0.0.1)", size=10, color=MUTED, bold=True)
    node(s, 0.85, 2.1, 2.0, 1.0, "frontend", "nginx :80 -> :8080", kind="ui", size=14, sub_size=11)
    node(s, 3.45, 2.1, 2.3, 1.0, "backend", "uvicorn :8000, non-root", kind="py", size=14, sub_size=11)
    node(s, 6.35, 2.1, 2.1, 1.0, "postgres:16", "volume pgdata", kind="store", size=14, sub_size=11)
    node(s, 6.35, 3.8, 2.1, 0.9, "redis:7", "rate limit, no persistence", kind="store", size=14, sub_size=10.5)
    node(s, 3.45, 3.8, 2.3, 0.9, "aegis-data", "agent workspaces", kind="store", size=14, sub_size=11)
    arrow(s, 2.85, 2.6, 3.45, 2.6)
    text(s, 2.95, 2.3, 0.5, 0.25, "/api", size=10, color=MUTED)
    arrow(s, 5.75, 2.6, 6.35, 2.6)
    arrow(s, 4.6, 3.1, 4.6, 3.8)
    arrow(s, 5.5, 3.1, 6.7, 3.8)
    node(s, 0.85, 4.95, 7.6, 0.5, "backend image: stage 1 builds + ctests the C library; stage 2 runs migrations, optional demo bootstrap, uvicorn",
         kind="native", size=11.5)
    rect(s, 9.05, 1.5, 3.7, 4.1, "0B2545", None, name="command box")
    text(s, 9.25, 1.6, 3.4, 3.9, [
        [("$ make env", {"color": "BFDBFE"})], [("  hashed tokens -> .env", {"color": "93C5FD", "size": 11})],
        [("$ docker compose up --build", {"color": "BFDBFE"})], [("  dashboard :8080, API docs :8000/docs", {"color": "93C5FD", "size": 11})],
        [("$ make docker-smoke", {"color": "BFDBFE"})], [("  isolated build + API checks, then clean-up", {"color": "93C5FD", "size": 11})],
        [("$ docker compose down", {"color": "BFDBFE"})], [("  keeps volumes", {"color": "93C5FD", "size": 11})],
    ], size=13, font="Consolas")
    chip(s, 0.55, 5.85, 2.9, "STACK NOT RE-RUN IN THIS SESSION", "U", size=10)
    text(s, 3.6, 5.82, 9.1, 0.8, "A clean --no-cache smoke build and four-service start are recorded in the implementation plan. "
         "Required secrets fail fast with a hint to run make env; no credentials appear in the deliverables.", size=12, color=MUTED)
    return s


def s_testing(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    rows = [["Layer (command)", "Result run for this handbook"],
            ["C tests (make c-test)", "2 of 2 passed"], ["C + ASan/UBSan/LSan + fault injection", "2 of 2 passed"],
            ["Python (make py-test)", "352 passed, 3 skipped (207.7 s)"], ["mypy --strict", "86 files, no issues"],
            ["Dashboard (make frontend-test)", "tsc ok, Vitest 10/10, build ok"], ["Offline demo (make demo)", "exit 0; audit chain valid (24)"],
            ["Docker smoke, ASan Python, PostgreSQL, Redis, live LLM", "not run here (recorded or opt-in)"]]
    table(s, 0.55, 1.5, 6.6, rows, [3.6, 3.0], size=11.5, row_h=0.46, name="test results")
    names = ["agent", "analytics", "api_core", "abi+owner.", "binding", "correlation", "e2e", "generator", "rca", "reporting", "security", "simulation"]
    counts = [36, 24, 30, 28, 61, 29, 3, 35, 45, 11, 22, 31]
    bar_chart(s, 7.4, 1.45, 5.4, 3.9, names, {"tests": counts}, ["1D4ED8"], "pytest tests collected per module (355)",
              horizontal=True, size=10, legend=False, number_format="0")
    rect(s, 0.55, 5.4, 12.2, 1.2, "FFFBEB", "FCD34D", name="not proven")
    text(s, 0.75, 5.45, 11.8, 1.1, [[("Not proven: ", {"bold": True, "color": "92400E"}),
                                     ("live LLM behaviour, PostgreSQL and Redis paths (3 opt-in skips), Docker in this session, real telemetry. "
                                      "Simulator, thresholds and tests were written together, so results show internal consistency, not field accuracy.", {})]],
         size=13, anchor=MSO_ANCHOR.MIDDLE)
    return s


def s_demo(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    steps = [("1", "make demo", "offline: SQLite, mock LLM, 13 steps through the real API"),
             ("2", "make env  +  docker compose up --build", "dashboard :8080 with the seeded incident"),
             ("3", "Sign in", "token from .aegis-tokens: viewer, operator, approver, admin"),
             ("4", "Incidents > INC-2026-001 > Investigate", "RCA with tool-call ids (operator)"),
             ("5", "AI Reports > Generate", "JSON / Markdown / HTML report (operator)"),
             ("6", "DevSecOps Agent > run failed_ci", "approve with a different user, then execute"),
             ("7", "Audit Log > Verify chain", "admin; read proposals, blocks, denials")]
    for i, (num, cmd, desc) in enumerate(steps):
        y = 1.55 + i * 0.7
        node(s, 0.55, y, 0.55, 0.55, num, kind="ui", size=15)
        text(s, 1.3, y - 0.02, 5.7, 0.6, cmd, size=14, bold=True, color=NAVY, font="Consolas" if cmd.startswith("make") else "Calibri",
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, 7.1, y - 0.02, 5.6, 0.6, desc, size=13, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, 0.55, 6.5, 12.2, 0.5, "F0FDF4", "86EFAC", name="no key")
    text(s, 0.75, 6.52, 11.8, 0.45, [[("No LLM key needed. ", {"bold": True, "color": "14532D"}),
                                      ("The mock provider is the default; a missing key or SDK falls back to it and reports why.", {})]],
         size=12.5, anchor=MSO_ANCHOR.MIDDLE)
    return s


def s_status(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    cols = [
        ("VERIFIED", "V", ["C library (tests + sanitizers)", "ctypes binding and ABI checks", "detectors, correlation", "API, RBAC, audit chain",
                           "agent policy and sandbox", "offline demo, dashboard tests"]),
        ("UNVERIFIED HERE", "U", ["Anthropic, OpenAI, local providers (no key)", "Docker stack (recorded, not re-run)", "PostgreSQL migration test (skipped)",
                                  "live Redis test (skipped)", "py-test-asan (recorded)"]),
        ("SIMULATED", "S", ["all telemetry, CDRs, events", "incidents and deployments", "DEMO-CVE advisories", "production rollback",
                            "mock provider as the \"LLM\""]),
        ("NOT IMPLEMENTED", "N", ["PDF reports", "Isolation Forest, DBSCAN", "OpenTelemetry, Grafana", "restart_service model",
                                  "TLS, external identity, HA", "anything on real telemetry"]),
    ]
    for i, (title, kind, items) in enumerate(cols):
        x = 0.55 + i * 3.1
        chip(s, x, 1.55, 2.9, title, kind, size=13, h=0.42)
        rect(s, x, 2.05, 2.9, 3.6, "F8FAFC", "CBD5E1", name=f"column {title}")
        text(s, x + 0.12, 2.2, 2.7, 3.4, ["- " + t for t in items], size=13.5)
    source_note(s, "Each item traces to a test, a command in Appendix B of the handbook, or a recorded result in IMPLEMENTATION_PLAN.md.", 6.6)
    return s


def s_future(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    items = [("1", "Scored live-LLM RCA evaluation", "largest unverified claim; include adversarial log lines"),
             ("2", "Validate on recorded, anonymised telemetry", "measure precision and recall outside the simulator"),
             ("3", "Asynchronous pipeline and agent runs", "requests return immediately; job queue"),
             ("4", "Seasonal baselines + a model-based detector", "keep interpretable explanations beside it"),
             ("5", "OIDC, TLS, secret manager, anchored audit head", "close the production security gaps"),
             ("6", "Patches beyond reverts, real CI hooks", "validated in the sandbox"),
             ("7", "OpenTelemetry traces", "API, RCA and agent")]
    for i, (num, t, why) in enumerate(items):
        y = 1.55 + i * 0.7
        node(s, 0.55, y, 0.55, 0.55, num, kind="py", size=15)
        text(s, 1.3, y - 0.02, 6.4, 0.6, t, size=15, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
        text(s, 7.8, y - 0.02, 5.0, 0.6, why, size=13, anchor=MSO_ANCHOR.MIDDLE)
    chip(s, 0.55, 6.55, 2.2, "RECOMMENDATIONS ONLY", "N", size=10.5)
    text(s, 2.9, 6.52, 9.5, 0.4, "None of these exists in the repository today.", size=12.5, color=MUTED)
    return s


def s_takeaways(prs, n):  # noqa: ANN001, ANN201
    s = blank(prs)
    header(s, SLIDES[n - 1]["kicker"], SLIDES[n - 1]["title"], n, TOTAL)
    pts = [("Native where it matters", "A C library does the risky parsing; tests fail allocations on purpose."),
           ("Interpretable detection", "Four detectors that must agree; every cause is a hypothesis with a cap of 0.95."),
           ("AI that can only read", "Allowlisted read-only tools; answers validated and cited; no hidden reasoning stored."),
           ("Policy enforced in code", "Risk classes re-checked at execution; separation of duties; hash-chained audit."),
           ("Honest limits", "Synthetic data, mock AI by default, simulated rollback, unverified live providers.")]
    for i, (t, d) in enumerate(pts):
        y = 1.6 + i * 1.03
        rect(s, 0.55, y, 12.2, 0.88, "F8FAFC", "CBD5E1", name=f"takeaway {i + 1}")
        node(s, 0.7, y + 0.14, 0.6, 0.6, str(i + 1), kind="py", size=16)
        text(s, 1.55, y + 0.08, 4.0, 0.72, t, size=18, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
        text(s, 5.6, y + 0.08, 7.0, 0.72, d, size=14, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 0.55, 6.8, 12.2, 0.3, "Start reading: call_analyzer.h, _native.py, model.py, detectors.py, correlation.py, rca/engine.py, agents/policy.py, security/audit.py",
         size=11.5, color=MUTED, italic=True)
    return s


BUILDERS = [None, s_problem, s_goals, s_flow, s_arch, s_call, s_telemetry, s_detect, s_corr, s_timeline, s_rca, s_report,
            s_agent, s_policy, s_dashboard, s_api, s_docker, s_testing, s_demo, s_status, s_future, s_takeaways]


def build() -> None:
    assert len(BUILDERS) == TOTAL == 22, (len(BUILDERS), TOTAL)
    prs = new_presentation()
    for n in range(1, TOTAL + 1):
        slide = s_title(prs) if n == 1 else BUILDERS[n - 1](prs, n)
        meta = SLIDES[n - 1]
        notes = slide.notes_slide.notes_text_frame
        notes.text = (f"SAY: {meta['say']}\n\nREADING THE VISUAL: {meta['figure']}\n\nLIKELY QUESTIONS: {meta['qa']}")
    prs.core_properties.title = "Aegis-Net Technical Presentation"
    prs.core_properties.author = "Aegis-Net project documentation (generated)"
    prs.core_properties.subject = "Technical walkthrough of the Aegis-Net prototype"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)

    lines = ["# Aegis-Net presenter notes", "",
             f"Deck: `deliverables/presentation/AegisNet_Technical_Presentation.pptx` ({TOTAL} slides, about 15 to 20 minutes). "
             "The same text is embedded as speaker notes in the PPTX. Status tags: verified, unverified here, simulated, not implemented.",
             "", "General guidance: say the data is synthetic in the first minute; never describe the mock provider as a language model; "
             "describe the rollback as a simulation; describe every cause as a hypothesis.", ""]
    for n, m in enumerate(SLIDES, 1):
        lines += [f"## Slide {n}: {m['title']}", "", f"**What to say.** {m['say']}", "", f"**How to read the visual.** {m['figure']}", "",
                  f"**Questions you may get.** {m['qa']}", ""]
    NOTES_MD.write_text("\n".join(lines), encoding="utf-8")
    out = ["# Presentation outline", "", f"{TOTAL} slides. Source: `scripts/documentation/deck_notes.py` and `build_deck.py`.", "",
           "| # | Section | Title (central message) | Visual |", "|---|---|---|---|"]
    for n, m in enumerate(SLIDES, 1):
        out.append(f"| {n} | {m['kicker']} | {m['title']} | {m['visual']} |")
    OUTLINE_MD.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({TOTAL} slides), notes and outline")


if __name__ == "__main__":
    build()
