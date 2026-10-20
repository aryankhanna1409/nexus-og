#!/usr/bin/env bash
# export_pdf.sh <docx|pptx> <file> <pdf-out> [png-dir]
# Copies the file to the Windows temp directory (Office cannot open WSL paths reliably), exports with
# export_office.ps1, then copies the PDF (and the field-updated .docx) back.
set -euo pipefail
kind="$1"; src="$(readlink -f "$2")"; pdf_out="$(readlink -f -m "$3")"; png_dir="${4:-}"
here="$(cd "$(dirname "$0")" && pwd)"
wintmp="$(wslpath -u "$(powershell.exe -NoProfile -Command 'Write-Output $env:TEMP' | tr -d '\r')")/aegis_docs_export"
rm -rf "$wintmp"; mkdir -p "$wintmp"
cp "$src" "$wintmp/in.$kind"; cp "$here/export_office.ps1" "$wintmp/export_office.ps1"
args=(-NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w "$wintmp/export_office.ps1")" -Kind "$kind"
      -Path "$(wslpath -w "$wintmp/in.$kind")" -Pdf "$(wslpath -w "$wintmp/out.pdf")")
if [ -n "$png_dir" ]; then mkdir -p "$wintmp/png"; args+=(-PngDir "$(wslpath -w "$wintmp/png")"); fi
powershell.exe "${args[@]}" | tr -d '\r'
mkdir -p "$(dirname "$pdf_out")"
cp "$wintmp/out.pdf" "$pdf_out"
if [ "$kind" = "docx" ]; then cp "$wintmp/in.docx" "$src"; fi
if [ -n "$png_dir" ]; then mkdir -p "$png_dir"; cp "$wintmp"/png/* "$png_dir"/; fi
rm -rf "$wintmp"
echo "exported $pdf_out"
