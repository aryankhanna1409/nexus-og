#!/usr/bin/env bash
# Regenerates every documentation deliverable under deliverables/.
#   scripts/documentation/build_all.sh --setup   create the isolated documentation virtualenv first
#   scripts/documentation/build_all.sh           evidence, diagrams, charts, handbook, deck, PDFs
# Needs: backend/.venv (make py-venv) for extract_evidence.py; Microsoft Word and PowerPoint (via WSL
# PowerShell COM) for the PDF export and field update. Without Office the .docx/.pptx are still produced.
set -euo pipefail
cd "$(dirname "$0")/../.."
VENV=scripts/documentation/.venv-docs
if [ "${1:-}" = "--setup" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -r scripts/documentation/requirements.txt
  exit 0
fi
PY="$VENV/bin/python"
backend/.venv/bin/python scripts/documentation/extract_evidence.py
"$PY" scripts/documentation/diagrams.py
"$PY" scripts/documentation/charts.py
"$PY" scripts/documentation/build_handbook.py
"$PY" scripts/documentation/build_deck.py
if command -v powershell.exe >/dev/null 2>&1; then
  scripts/documentation/export_pdf.sh docx deliverables/handbook/AegisNet_Technical_Handbook.docx deliverables/handbook/AegisNet_Technical_Handbook.pdf
  scripts/documentation/export_pdf.sh pptx deliverables/presentation/AegisNet_Technical_Presentation.pptx deliverables/presentation/AegisNet_Technical_Presentation.pdf deliverables/_render/deck
else
  echo "powershell.exe not found: skipped PDF export (open the files in Word/PowerPoint to export)"
fi
