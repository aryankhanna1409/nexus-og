"""Tiny diagram toolkit (boxes, groups, arrows, lifelines) on matplotlib.

The diagram *sources* live in `diagrams.py` as plain Python data and calls into this kit, so
every figure can be edited and regenerated with `build_all.sh` (no external diagram service
or CLI is needed). Each diagram is exported as a 220-dpi PNG and as an SVG.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "deliverables" / "assets" / "diagrams"

# ---- Shared palette (also used by the DOCX and PPTX builders) --------------------------------
INK = "#1B2A41"
NAVY = "#0B2545"
MUTED = "#5B6B7F"
LINE = "#8A99AD"
PAGE = "#FFFFFF"

# kind -> (fill, edge)
KINDS: dict[str, tuple[str, str]] = {
    "native": ("#FEF3C7", "#B45309"),    # C library
    "py": ("#DBEAFE", "#1D4ED8"),        # Python backend
    "ai": ("#EDE9FE", "#6D28D9"),        # LLM / RCA
    "store": ("#CCFBF1", "#0F766E"),     # databases, files
    "ui": ("#DCFCE7", "#15803D"),        # frontend
    "sec": ("#FEE2E2", "#B91C1C"),       # policy / security
    "ext": ("#F1F5F9", "#64748B"),       # synthetic sources / external
    "plain": ("#FFFFFF", "#64748B"),
}

_FONT_CANDIDATES = [Path("/mnt/c/Windows/Fonts/calibri.ttf"), Path("/mnt/c/Windows/Fonts/calibrib.ttf"),
                    Path("/mnt/c/Windows/Fonts/calibrii.ttf"), Path("/mnt/c/Windows/Fonts/consola.ttf")]
for _p in _FONT_CANDIDATES:
    if _p.is_file():
        font_manager.fontManager.addfont(str(_p))
_available = {f.name for f in font_manager.fontManager.ttflist}
FONT = "Calibri" if "Calibri" in _available else "DejaVu Sans"
MONO = "Consolas" if "Consolas" in _available else "DejaVu Sans Mono"
plt.rcParams["font.family"] = FONT
plt.rcParams["svg.fonttype"] = "none"


class Diagram:
    """A canvas measured in inches with the origin at the top-left (y grows downwards)."""

    def __init__(self, width: float, height: float, title: str | None = None) -> None:
        self.w, self.h = width, height
        self.fig = plt.figure(figsize=(width, height), dpi=220)
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(height, 0)
        self.ax.axis("off")
        self.fig.patch.set_facecolor(PAGE)
        if title:
            self.ax.text(0.12, 0.2, title, fontsize=11.5, fontweight="bold", color=NAVY, va="center")

    # -- shapes ---------------------------------------------------------------------------------
    def box(self, x: float, y: float, w: float, h: float, title: str, sub: str | None = None,
            kind: str = "py", fs: float = 9.0, sub_fs: float | None = None, mono_sub: bool = False,
            round_: float = 0.07, lw: float = 1.1, dashed: bool = False) -> tuple[float, float, float, float]:
        fill, edge = KINDS[kind]
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={round_}",
                                         fc=fill, ec=edge, lw=lw, ls="--" if dashed else "-", zorder=2))
        if sub:
            self.ax.text(x + w / 2, y + h * 0.33, title, ha="center", va="center", fontsize=fs,
                         fontweight="bold", color=INK, zorder=3, linespacing=1.05)
            self.ax.text(x + w / 2, y + h * 0.70, sub, ha="center", va="center",
                         fontsize=max(6.5, sub_fs or fs - 1.3), color=MUTED, zorder=3, linespacing=1.1,
                         family=MONO if mono_sub else FONT)
        else:
            self.ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=fs,
                         fontweight="bold", color=INK, zorder=3, linespacing=1.1)
        return (x, y, w, h)

    def cylinder(self, x: float, y: float, w: float, h: float, title: str, sub: str | None = None,
                 fs: float = 9.0) -> None:
        fill, edge = KINDS["store"]
        cap = min(0.2, h / 4)
        body_top, body_bot = y + cap / 2, y + h - cap / 2
        self.ax.add_patch(matplotlib.patches.Rectangle((x, body_top), w, body_bot - body_top, fc=fill, ec="none",
                                                       zorder=2))
        self.ax.plot([x, x], [body_top, body_bot], color=edge, lw=1.1, zorder=3)
        self.ax.plot([x + w, x + w], [body_top, body_bot], color=edge, lw=1.1, zorder=3)
        self.ax.add_patch(matplotlib.patches.Ellipse((x + w / 2, body_bot), w, cap, fc=fill, ec=edge, lw=1.1,
                                                     zorder=2))
        self.ax.add_patch(matplotlib.patches.Ellipse((x + w / 2, body_top), w, cap, fc=fill, ec=edge, lw=1.1,
                                                     zorder=4))
        mid = (body_top + body_bot) / 2 + cap * 0.1
        if sub:
            self.ax.text(x + w / 2, mid - 0.09, title, ha="center", va="center", fontsize=fs, fontweight="bold",
                         color=INK, zorder=5)
            self.ax.text(x + w / 2, mid + 0.13, sub, ha="center", va="center", fontsize=max(6.5, fs - 1.3),
                         color=MUTED, zorder=5)
        else:
            self.ax.text(x + w / 2, mid, title, ha="center", va="center", fontsize=fs, fontweight="bold",
                         color=INK, zorder=5)

    def group(self, x: float, y: float, w: float, h: float, label: str, fs: float = 8.5) -> None:
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.1",
                                         fc="#F8FAFC", ec="#CBD5E1", lw=1.0, ls=(0, (4, 3)), zorder=0))
        self.ax.text(x + 0.1, y + 0.13, label.upper(), fontsize=fs - 0.5, color=MUTED, fontweight="bold",
                     va="center", zorder=1)

    def text(self, x: float, y: float, s: str, fs: float = 8.5, color: str = INK, ha: str = "left",
             va: str = "center", bold: bool = False, italic: bool = False, mono: bool = False,
             rotation: float = 0.0, bg: str | None = None) -> None:
        self.ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va=va,
                     fontweight="bold" if bold else "normal", fontstyle="italic" if italic else "normal",
                     family=MONO if mono else FONT, rotation=rotation, zorder=5, linespacing=1.15,
                     bbox=dict(fc=bg, ec="none", pad=1.2) if bg else None)

    def arrow(self, pts: Sequence[tuple[float, float]], label: str | None = None, color: str = LINE,
              dashed: bool = False, lw: float = 1.3, label_at: float = 0.5, label_dy: float = -0.1,
              label_dx: float = 0.0, fs: float = 7.8, both: bool = False, head: float = 7.0,
              label_ha: str = "center") -> None:
        """Polyline with an arrow head at the end (and the start when `both`)."""
        for a, b in zip(pts[:-2], pts[1:-1]):
            self.ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls="--" if dashed else "-",
                         solid_capstyle="round", zorder=1)
        last_a, last_b = pts[-2], pts[-1]
        self.ax.add_patch(FancyArrowPatch(last_a, last_b, arrowstyle="-|>", mutation_scale=head, color=color,
                                          lw=lw, ls="--" if dashed else "-", shrinkA=0, shrinkB=0, zorder=1))
        if both:
            self.ax.add_patch(FancyArrowPatch(pts[1], pts[0], arrowstyle="-|>", mutation_scale=head,
                                              color=color, lw=lw, shrinkA=0, shrinkB=0, zorder=1))
        if label:
            # label position along the polyline (by cumulative length)
            segs = [((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for a, b in zip(pts[:-1], pts[1:])]
            target = sum(segs) * label_at
            acc = 0.0
            for (a, b), s in zip(zip(pts[:-1], pts[1:]), segs):
                if acc + s >= target:
                    t = (target - acc) / s if s else 0
                    lx, ly = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    break
                acc += s
            else:
                lx, ly = pts[-1]
            self.ax.text(lx + label_dx, ly + label_dy, label, fontsize=fs, color=MUTED, ha=label_ha,
                         va="center", zorder=5, bbox=dict(fc=PAGE, ec="none", pad=0.8))

    def diamond(self, cx: float, cy: float, w: float, h: float, text: str, fs: float = 8.2,
                kind: str = "sec") -> None:
        fill, edge = KINDS[kind]
        self.ax.add_patch(Polygon([(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)],
                                  closed=True, fc=fill, ec=edge, lw=1.1, zorder=2))
        self.ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, fontweight="bold", color=INK,
                     zorder=3, linespacing=1.1)

    def pill(self, x: float, y: float, w: float, h: float, text: str, kind: str = "plain", fs: float = 8.0,
             bold: bool = False) -> None:
        fill, edge = KINDS[kind]
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=fill,
                                         ec=edge, lw=1.0, zorder=2))
        self.ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
                     fontweight="bold" if bold else "normal", zorder=3)

    # -- output ----------------------------------------------------------------------------------
    def save(self, name: str) -> Path:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        png = OUT_DIR / f"{name}.png"
        self.fig.savefig(png, dpi=220, facecolor=PAGE)
        self.fig.savefig(OUT_DIR / f"{name}.svg", facecolor=PAGE)
        plt.close(self.fig)
        return png


def sequence(name: str, participants: Sequence[tuple[str, str]], messages: Sequence[dict[str, object]],
             width: float = 7.2, row: float = 0.34, top: float = 1.15, notes: Sequence[dict[str, object]] = (),
             part_w: float | None = None, title: str | None = None, fs: float = 7.8) -> Path:
    """UML-style sequence diagram.

    participants: (label, kind); messages: dicts with src, dst (indices), text, optional
    `dashed` (return), `y` (row index), `self` (self-call), `block` (grey activation note);
    notes: dicts with `row`, `text`, optional `span` (first, last participant index).
    """
    n = len(participants)
    rows = max(int(m.get("row", i)) for i, m in enumerate(messages)) + 1
    height = top + rows * row + 0.45
    d = Diagram(width, height, title)
    margin = 0.15
    pw = part_w or (width - 2 * margin) / n - 0.1
    xs = [margin + (width - 2 * margin) * (i + 0.5) / n for i in range(n)]
    for (label, kind), x in zip(participants, xs):
        d.box(x - pw / 2, 0.38 if title else 0.12, pw, 0.42, label, kind=kind, fs=8.2)
        d.ax.plot([x, x], [(0.8 if title else 0.54), height - 0.15], color="#B6C2D1", lw=0.9, ls=(0, (3, 3)),
                  zorder=0)
    for note in notes:
        first, last = note.get("span", (0, n - 1))  # type: ignore[misc]
        y = top + float(note["row"]) * row  # type: ignore[arg-type]
        x0, x1 = xs[int(first)] - pw / 2, xs[int(last)] + pw / 2
        d.ax.add_patch(FancyBboxPatch((x0, y - row * 0.36), x1 - x0, row * 0.72,
                                      boxstyle="round,pad=0,rounding_size=0.05", fc="#FFFBEB", ec="#D97706",
                                      lw=0.8, zorder=1))
        d.text((x0 + x1) / 2, y, str(note["text"]), fs=fs - 0.5, ha="center", color="#7C4A03")
    for i, m in enumerate(messages):
        r = int(m.get("row", i))
        y = top + r * row
        s, t = xs[int(m["src"])], xs[int(m["dst"])]  # type: ignore[call-overload]
        dashed = bool(m.get("dashed", False))
        color = "#1D4ED8" if not dashed else "#64748B"
        if m.get("self"):
            d.arrow([(s, y - 0.06), (s + 0.38, y - 0.06), (s + 0.38, y + 0.1), (s + 0.02, y + 0.1)], color=color,
                    lw=1.0, head=6)
            d.text(s + 0.46, y + 0.02, str(m["text"]), fs=fs, ha="left")
            continue
        d.arrow([(s, y), (t, y)], color=color, dashed=dashed, lw=1.1, head=6)
        mid = (s + t) / 2
        d.text(mid, y - 0.09, str(m["text"]), fs=fs, ha="center", bg=PAGE)
    return d.save(name)
