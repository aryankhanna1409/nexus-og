#!/usr/bin/env python3
"""Charts for the handbook, drawn from deliverables/assets/charts/evidence.json.

evidence.json is produced by extract_evidence.py from the repository's own simulator, detectors and
correlation engine (seed 7), so every plotted value is computed by project code.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from diagram_kit import FONT, INK, MUTED, NAVY  # noqa: E402,F401

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = REPO_ROOT / "deliverables" / "assets" / "charts" / "evidence.json"
OUT = REPO_ROOT / "deliverables" / "assets" / "charts"

BLUE, TEAL, RED, AMBER, GREY, PURPLE = "#1D4ED8", "#0F766E", "#B91C1C", "#B45309", "#94A3B8", "#6D28D9"


def _dt(epoch: int) -> datetime:
    return datetime.fromtimestamp(epoch, tz=UTC)


def _style(ax) -> None:  # noqa: ANN001
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#CBD5E1")
    ax.tick_params(colors=MUTED, labelsize=7.5)
    ax.grid(axis="y", color="#E2E8F0", lw=0.6)
    ax.set_axisbelow(True)


def seeded_kpis(ev: dict) -> None:
    epochs = [_dt(e) for e in ev["epochs"]]
    deploy = next(d for d in ev["deployments"] if d["to"] == "2.4.1")
    hotfix = next(d for d in ev["deployments"] if "hotfix" in d["to"])
    panels = [("memory_utilization", "Memory (%)"), ("cpu_utilization", "CPU (%)"), ("latency_ms", "Latency (ms)"),
              ("packet_loss_pct", "Packet loss (%)"), ("call_drop_rate", "Call drop rate (%)")]
    fig, axes = plt.subplots(len(panels), 1, figsize=(7.2, 6.4), sharex=True, dpi=220)
    onset = {a["metric"]: a for a in ev["anomalies_by_cell_metric"] if a["cell"] == "CELL-101"}
    for ax, (metric, label) in zip(axes, panels):
        ax.plot(epochs, ev["series"]["CELL-105"][metric], color=GREY, lw=0.9, label="CELL-105 (pgw-2, unaffected)")
        ax.plot(epochs, ev["series"]["CELL-101"][metric], color=BLUE, lw=1.0, label="CELL-101 (pgw-1, affected)")
        ax.axvline(_dt(deploy["epoch"]), color=RED, lw=1.0, ls="--")
        ax.axvline(_dt(hotfix["epoch"]), color=GREY, lw=1.0, ls=":")
        if metric in onset:
            o = onset[metric]
            ax.plot([_dt(o["onset_epoch"])], [o["worst"] if False else ev["series"]["CELL-101"][metric][
                ev["epochs"].index(o["onset_epoch"])]], marker="o", ms=4.5, color=AMBER, zorder=5)
            ax.annotate(f"detected {o['onset'][11:16]}", xy=(_dt(o["onset_epoch"]), ev["series"]["CELL-101"][metric][
                ev["epochs"].index(o["onset_epoch"])]), xytext=(-8, 8), textcoords="offset points", fontsize=7,
                color=AMBER, ha="right", bbox=dict(fc="white", ec="none", alpha=0.9, pad=0.8), zorder=6)
        ax.set_ylabel(label, fontsize=8, color=INK)
        _style(ax)
    axes[0].axvline(_dt(deploy["epoch"]), color=RED, lw=1.0, ls="--")
    axes[0].text(_dt(deploy["epoch"]), axes[0].get_ylim()[1], " deploy 2.4.1 -> pgw-1 (14:05)", color=RED, fontsize=7.5,
                 va="top")
    axes[0].text(_dt(hotfix["epoch"]), axes[0].get_ylim()[1], " hotfix -> pgw-3 (13:10, distractor) ", color=MUTED,
                 fontsize=7.5, va="top", ha="right")
    axes[0].legend(loc="center left", fontsize=7.2, frameon=False)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axes[-1].xaxis.set_major_locator(mdates.HourLocator())
    axes[-1].set_xlabel("2026-03-01 UTC (synthetic data, seed 7)", fontsize=8, color=MUTED)
    fig.tight_layout(h_pad=0.5)
    fig.savefig(OUT / "chart_seeded_kpis.png", facecolor="white")
    plt.close(fig)


def detector_example(ev: dict) -> None:
    w = ev["worked_example"]
    values = w["values"]
    xs = list(range(len(values)))
    mean, std = w["baseline_mean_first9"], w["baseline_std_first9"]
    floor = 1.0
    fig, ax = plt.subplots(figsize=(7.2, 3.1), dpi=220)
    ax.plot(xs, values, color=BLUE, lw=1.4, marker="o", ms=4, label="value")
    ax.axhline(mean, color=TEAL, lw=1.0, ls="-", label=f"baseline mean (first 9 points) = {mean:.2f}")
    ax.axhline(mean + 4 * max(std, floor), color=RED, lw=1.0, ls="--",
               label=f"mean + 4 x max(std, floor) = {mean + 4 * max(std, floor):.2f}")
    ax.plot(xs, w["ewma_tau900"], color=PURPLE, lw=1.1, ls=":", label="EWMA, tau = 900 s (plain, includes the spike)")
    ax.annotate(f"z = ({values[-1]:.0f} - {mean:.2f}) / max({std:.2f}, {floor:.1f}) = {w['z_of_last']:.1f}", xy=(9, 80),
                xytext=(-190, -4), textcoords="offset points", fontsize=8, color=RED,
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.7))
    ax.set_xlabel("minute", fontsize=8, color=MUTED)
    ax.set_ylabel("example KPI", fontsize=8, color=INK)
    ax.legend(fontsize=7.2, frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.88))
    _style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "chart_detector_example.png", facecolor="white")
    plt.close(fig)


def score_curve() -> None:
    zs = [i / 10 for i in range(0, 241)]
    fig, ax = plt.subplots(figsize=(7.2, 2.9), dpi=220)
    for thr, col, lab in ((3.5, AMBER, "C library group z (threshold 3.5)"), (4.0, BLUE, "Python z-score / EWMA (4.0)"),
                          (5.0, PURPLE, "Python rate of change (5.0)")):
        ax.plot(zs, [1 - math.pow(2, -z / thr) for z in zs], color=col, lw=1.4, label=lab)
    for level, name in ((0.6, "medium"), (0.75, "high"), (0.9, "critical")):
        ax.axhline(level, color="#CBD5E1", lw=0.8, ls="--")
        ax.text(24, level + 0.01, f">= {level}: {name}", fontsize=7.2, color=MUTED, ha="right")
    ax.axhline(0.5, color=TEAL, lw=0.8, ls=":")
    ax.text(0.2, 0.52, "0.5 at the threshold", fontsize=7.2, color=TEAL)
    ax.set_xlabel("z (deviation in robust or ordinary standard-deviation units)", fontsize=8, color=MUTED)
    ax.set_ylabel("anomaly score", fontsize=8, color=INK)
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=7.2, frameon=False, loc="lower right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "chart_score_curve.png", facecolor="white")
    plt.close(fig)


def incident_timeline(ev: dict) -> None:
    inc = ev["incident"]
    rows = [e for e in inc["events"]]
    seen: set[str] = set()
    items = []
    for e in rows:
        if e["type"] == "application_log":
            continue
        label = e["description"].replace(" on CELL-101, CELL-102, CELL-103, CELL-104", "")
        if label in seen:
            continue
        seen.add(label)
        items.append((e["epoch"], e["type"], label))
    hot = next(d for d in ev["deployments"] if "hotfix" in d["to"])
    fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=220)
    colors = {"deployment": RED, "metric_anomaly": BLUE, "incident_created": AMBER}
    for i, (epoch, kind, label) in enumerate(items):
        y = len(items) - i
        ax.plot([_dt(epoch)], [y], marker="o", ms=6, color=colors.get(kind, GREY), zorder=3)
        ax.text(_dt(epoch), y, "  " + label + f"  ({_dt(epoch):%H:%M})", fontsize=7.4, va="center", color=INK)
    y_h = len(items) + 1
    ax.plot([_dt(hot["epoch"])], [y_h], marker="o", ms=6, color=GREY, zorder=3, mfc="white")
    ax.text(_dt(hot["epoch"]), y_h, f"  hotfix to pgw-3 ({_dt(hot['epoch']):%H:%M}): excluded, other node", fontsize=7.4,
            va="center", color=MUTED)
    ax.plot([_dt(items[0][0]), _dt(items[-1][0])], [len(items), 1], color="#E2E8F0", lw=0.0)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_xlim(_dt(hot["epoch"] - 600), _dt(items[-1][0] + 3600 * 1.15))
    ax.set_ylim(0.4, y_h + 0.8)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#CBD5E1")
    ax.tick_params(colors=MUTED, labelsize=7.5)
    ax.set_title("INC-2026-001 timeline as built by the correlation engine (red: deployment, blue: symptom onset)",
                 fontsize=8.6, color=NAVY, loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "chart_incident_timeline.png", facecolor="white")
    plt.close(fig)


def hypothesis_scores(ev: dict) -> None:
    causes = ev["incident"]["suspected_causes"]
    fig, ax = plt.subplots(figsize=(7.2, 2.2), dpi=220)
    names = [c["cause_type"] for c in causes][::-1]
    parts = [("temporal x 0.45", "temporal_score", 0.45, BLUE), ("mechanism x 0.35", "mechanism_score", 0.35, TEAL),
             ("topology x 0.20", "topology_score", 0.20, AMBER)]
    left = [0.0] * len(names)
    for label, key, weight, col in parts:
        vals = [c[key] * weight for c in causes][::-1]
        ax.barh(names, vals, left=left, color=col, height=0.5, label=label)
        for i, (v, l0) in enumerate(zip(vals, left)):
            ax.text(l0 + v / 2, i, f"{v:.3f}", ha="center", va="center", color="white", fontsize=7.2)
        left = [a + b for a, b in zip(left, vals)]
    for i, tot in enumerate(left):
        ax.text(tot + 0.01, i, f"score {tot:.4f}", va="center", fontsize=7.6, color=INK, fontweight="bold")
    ax.set_xlim(0, 1.15)
    ax.legend(fontsize=7.2, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.28))
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "chart_hypothesis_scores.png", facecolor="white")
    plt.close(fig)


def main() -> None:
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    seeded_kpis(ev)
    detector_example(ev)
    score_curve()
    incident_timeline(ev)
    hypothesis_scores(ev)
    print("charts written to", OUT.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
