#!/usr/bin/env python3
"""Renders PDF pages to PNG and contact sheets for visual inspection (PyMuPDF)."""
import sys
from pathlib import Path
import fitz
from PIL import Image

pdf, outdir = Path(sys.argv[1]), Path(sys.argv[2])
per_sheet = int(sys.argv[3]) if len(sys.argv) > 3 else 8
dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 50
outdir.mkdir(parents=True, exist_ok=True)
doc = fitz.open(pdf)
print("pages:", len(doc))
imgs = []
for i, page in enumerate(doc, 1):
    pix = page.get_pixmap(dpi=dpi)
    p = outdir / f"page_{i:03d}.png"
    pix.save(p)
    imgs.append(p)
for s in range(0, len(imgs), per_sheet):
    chunk = [Image.open(p) for p in imgs[s:s + per_sheet]]
    w, h = chunk[0].size
    cols = 4 if per_sheet >= 8 else 3
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * 6, rows * h + (rows + 1) * 6), "#888888")
    for k, im in enumerate(chunk):
        sheet.paste(im, (6 + (k % cols) * (w + 6), 6 + (k // cols) * (h + 6)))
    sheet.save(outdir / f"sheet_{s // per_sheet + 1:02d}.png")
