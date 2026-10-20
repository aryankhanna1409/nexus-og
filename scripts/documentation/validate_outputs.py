#!/usr/bin/env python3
"""Integrity checks for the documentation deliverables. Prints a report; exits 1 on any failure.

Checks: files exist and are non-empty; ZIP packages are intact; the DOCX and PPTX re-open; figures and
screenshots keep their aspect ratio; every slide has speaker notes and a title; presenter notes cover every
slide; PDF page and slide counts; no secret-like strings (including the values in a local .aegis-tokens file,
which are compared without being printed) appear in any deliverable text.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document
from PIL import Image
from pptx import Presentation
from pptx.util import Emu

REPO = Path(__file__).resolve().parents[2]
D = REPO / "deliverables"
FILES = {
    "handbook docx": D / "handbook" / "AegisNet_Technical_Handbook.docx",
    "handbook pdf": D / "handbook" / "AegisNet_Technical_Handbook.pdf",
    "deck pptx": D / "presentation" / "AegisNet_Technical_Presentation.pptx",
    "deck pdf": D / "presentation" / "AegisNet_Technical_Presentation.pdf",
    "presenter notes": D / "presentation" / "AegisNet_Presenter_Notes.md",
    "handbook source": D / "documentation" / "handbook_source.md",
    "outline": D / "documentation" / "presentation_outline.md",
    "source inventory": D / "documentation" / "source_inventory.md",
    "verification report": D / "documentation" / "verification_report.md",
}
failures: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("PASS  " if ok else "FAIL  ") + message)
    if not ok:
        failures.append(message)


def main() -> int:
    for name, path in FILES.items():
        check(path.is_file() and path.stat().st_size > 0, f"{name}: exists and non-empty ({path.relative_to(REPO)})")
    for key in ("handbook docx", "deck pptx"):
        check(zipfile.ZipFile(FILES[key]).testzip() is None, f"{key}: ZIP package intact")

    # DOCX
    doc = Document(FILES["handbook docx"])
    headings = [p for p in doc.paragraphs if p.style.name.startswith("Heading")]
    chapters = [p for p in headings if p.style.name == "Heading 1"]
    check(len(chapters) >= 25, f"docx: {len(chapters)} level-1 headings (22 chapters + appendices + front matter)")
    check(len(doc.inline_shapes) == 30, f"docx: {len(doc.inline_shapes)} inline pictures (expected 30 figures)")
    bad = 0
    for shape in doc.inline_shapes:
        blip = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
        part = doc.part.related_parts[blip]
        import io
        with Image.open(io.BytesIO(part.blob)) as im:
            iw, ih = im.size
        if abs(shape.width / shape.height - iw / ih) > 0.01 * iw / ih:
            bad += 1
    check(bad == 0, f"docx: every picture keeps its original aspect ratio ({bad} distorted)")
    check(len(doc.tables) > 40, f"docx: {len(doc.tables)} tables (native Word tables, not images)")
    body_text = "\n".join(p.text for p in doc.paragraphs)
    check("Open in Word and press F9" not in body_text, "docx: table of contents field was populated")
    check("Figure ?" not in body_text, "docx: no unresolved figure references")

    # PPTX
    prs = Presentation(FILES["deck pptx"])
    n = len(prs.slides)
    check(n == 22, f"pptx: {n} slides (target 18 to 24)")
    no_notes = [i for i, s in enumerate(prs.slides, 1) if not s.has_notes_slide or not s.notes_slide.notes_text_frame.text.strip()]
    check(not no_notes, f"pptx: speaker notes on every slide (missing: {no_notes})")
    no_title = [i for i, s in enumerate(prs.slides, 1) if not any(sh.name == "title" and sh.has_text_frame and sh.text_frame.text.strip() for sh in s.shapes)]
    check(not no_title, f"pptx: every slide has a title (missing: {no_title})")
    distorted, pics, charts, tables, native_shapes = 0, 0, 0, 0, 0
    shots = {p.stem: p for p in (D / "assets" / "screenshots").glob("*.png")}
    for s in prs.slides:
        for sh in s.shapes:
            if sh.shape_type == 13:  # picture
                pics += 1
                with Image.open(__import__("io").BytesIO(sh.image.blob)) as im:
                    iw, ih = im.size
                vis_w = iw * (1 - sh.crop_left - sh.crop_right)
                vis_h = ih * (1 - sh.crop_top - sh.crop_bottom)
                if abs((sh.width / sh.height) - vis_w / vis_h) > 0.02 * vis_w / vis_h:
                    distorted += 1
            elif sh.has_chart if hasattr(sh, "has_chart") else False:
                charts += 1
            elif sh.has_table if hasattr(sh, "has_table") else False:
                tables += 1
            else:
                native_shapes += 1
    check(distorted == 0, f"pptx: {pics} pictures, none distorted ({distorted})")
    check(charts >= 3 and tables >= 3, f"pptx: native charts={charts}, native tables={tables}, other native shapes/text={native_shapes}")
    out_of_bounds = [
        (i, sh.name) for i, s in enumerate(prs.slides, 1) for sh in s.shapes
        if sh.left < 0 or sh.top < 0 or sh.left + sh.width > prs.slide_width + Emu(10) or sh.top + sh.height > prs.slide_height + Emu(10)
    ]
    check(not out_of_bounds, f"pptx: no shape extends beyond the slide ({out_of_bounds[:3]})")

    # Notes file
    notes = FILES["presenter notes"].read_text(encoding="utf-8")
    covered = {int(m) for m in re.findall(r"^## Slide (\d+):", notes, re.M)}
    check(covered == set(range(1, n + 1)), f"presenter notes cover slides 1..{n}")

    # PDFs
    for key, expect in (("handbook pdf", None), ("deck pdf", 22)):
        pages = len(fitz.open(FILES[key]))
        check(pages > 0 and (expect is None or pages == expect), f"{key}: {pages} pages" + (f" (expected {expect})" if expect else ""))

    # Secrets
    texts: list[tuple[str, str]] = [(k, FILES[k].read_text(encoding="utf-8")) for k in ("presenter notes", "handbook source", "outline", "source inventory", "verification report") if FILES[k].is_file()]
    texts.append(("docx text", body_text + "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)))
    texts.append(("pptx text", "\n".join(sh.text_frame.text for s in prs.slides for sh in s.shapes if sh.has_text_frame)))
    patterns = [r"sk-[A-Za-z0-9]{20,}", r"sk-ant-[A-Za-z0-9_-]{10,}", r"Bearer\s+[A-Za-z0-9_\-]{30,}", r"[A-Z_]*API_KEY=\S{8,}", r"-----BEGIN [A-Z ]*PRIVATE KEY"]
    hits = [(name, p) for name, t in texts for p in patterns if re.search(p, t)]
    check(not hits, f"no secret-like strings in deliverable text ({hits})")
    tokens_file = REPO / ".aegis-tokens"
    if tokens_file.is_file():
        values = [ln.split("=", 1)[1].strip() for ln in tokens_file.read_text().splitlines() if "=" in ln]
        leaked = [name for name, t in texts if any(v and v in t for v in values)]
        check(not leaked, f"values from .aegis-tokens do not appear in deliverable text ({len(values)} values checked)")
    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
