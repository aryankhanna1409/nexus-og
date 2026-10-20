# Verification report

Date: 2026-10-20. Repository: commit `5d742e7` on `master` (working tree also holds the untracked documentation work and a pre-existing deleted file `tatus --short`, which was left alone).

This report separates three things: (1) commands that were actually run for this handbook and what they printed, (2) checks made on the generated documents, and (3) what could not be verified. Nothing marked "recorded" was re-executed; it comes from `IMPLEMENTATION_PLAN.md`.

## 1. Project verification commands run in this session

Working directory: repository root. All exit codes were 0.

| Command | Result |
|---|---|
| `make c-test` | CMake build with `-Werror` and strict warnings; ctest: "100% tests passed, 0 tests failed out of 2" |
| `make c-test-asan` | ASan/UBSan/LSan build; ctest: 2 of 2 passed |
| `make py-test` | pytest on Python 3.14.4: **352 passed, 3 skipped** in 207.68 s. Skips: PostgreSQL migration test (`AEGIS_TEST_POSTGRES_URL`), live Redis test (`AEGIS_TEST_REDIS_URL`), live Anthropic test (`AEGIS_RUN_LIVE_LLM_TESTS`) |
| `make py-typecheck` | mypy strict: "Success: no issues found in 86 source files" |
| `make demo` | 13 steps through the real API; INC-2026-001 CRITICAL; execute-before-approval returned HTTP 409; simulated rollback verified (`recovered=True`); incident resolved; audit chain valid (24 rows); "DEMO COMPLETED" |
| `make frontend-test` (Docker `node:22-alpine`) | `tsc` ok; Vitest 2 files, 10 tests passed; Vite build ok |
| `backend/.venv/bin/python scripts/documentation/extract_evidence.py` | One incident, CRITICAL, confidence 0.8947, 36 anomaly episodes; fingerprint begins `aed745627289` (matches the demo run) |

Spot checks against code: `ctypes.sizeof(CallRecord)` is 152 (matches the handbook's layout arithmetic); the audit table has no database trigger (searched the migration); the endpoint list was compared with every `@router` decorator and role dependency (26 routes plus `/metrics`); the 20 agent tools and 9 RCA tools were counted from their registries; table and test counts were counted from the code (19 tables; 355 collected tests).

**Not executed in this session** (so these are *unverified here*): `make py-test-asan` (plan records 345 passed), `make container-test`, `make docker-smoke` and the Docker stack (plan records a clean `--no-cache` smoke build and four-service start), the Playwright browser check (recorded), PostgreSQL and Redis tests, any live LLM call.

## 2. Checks on the generated documents

Generation: `scripts/documentation/build_all.sh` (or the individual scripts). Python tooling is isolated in `scripts/documentation/.venv-docs` (python-docx 1.2.0, python-pptx 1.0.2, Pillow, matplotlib 3.11.2, PyMuPDF 2.0; versions in `requirements.txt`). PDFs were produced from the final editable files by Microsoft Word 16 and PowerPoint 16 through PowerShell COM (`export_office.ps1`); Word also updated the table of contents, list of figures and cross-references and saved the DOCX, so page numbers in the editable file are correct. LibreOffice, pandoc and Mermaid are not installed here and were not used.

| Check | Result |
|---|---|
| Files exist and are non-empty | handbook DOCX and PDF, deck PPTX and PDF, presenter notes, handbook source, outline, source inventory, this report (`validate_outputs.py`) |
| Package integrity | DOCX and PPTX ZIP tests pass; both re-open in python-docx / python-pptx; Word and PowerPoint opened and exported both without error |
| Page and slide counts | Handbook PDF: 67 pages (cover, 4-page contents, figure list, 22 chapters, 3 appendices). Deck: 22 slides, 22 PDF pages. |
| Handbook structure | 22 numbered chapters plus Appendices A to C; 30 figures with numbered captions and cross-reference fields; 26 captioned tables (73 native Word tables including callouts and code boxes); no unresolved figure references |
| Native content | Text, tables, callouts and code blocks are Word text; only figures are pictures (30 inline pictures, none distorted); the deck's diagrams, 3 tables and 3 charts are native PowerPoint objects; 10 pictures (screenshots) in the deck, none distorted |
| Speaker notes | Present on all 22 slides and in `AegisNet_Presenter_Notes.md` (slides 1 to 22) |
| Layout bounds | No deck shape extends beyond the slide (checked from shape geometry) |
| Secrets | No secret-like pattern in any deliverable text; the four values in the local `.aegis-tokens` file were searched for by value (not printed) and do not appear |
| Screenshots | All 13 images in `docs/source/aegis.docx` extracted unmodified; each viewed; none shows a token, key or password |

### Visual inspection actually performed

- **Handbook:** every one of the 67 pages was rendered to PNG (PyMuPDF, 45 dpi) and inspected as contact sheets of 12 pages. This found and led to fixes for: wrapped status badges and headers in narrow table columns, a footer page number on a second line, a table-width regression (a squeezed column that inflated the document to 76 pages, caught and fixed), and the oversized Appendix B and C page breaks. Individual pages were *not* proofread at full resolution; small text inside dark screenshots is legible only when zoomed.
- **Deck:** all 22 slides were rendered by PowerPoint (1600 x 900) and inspected at reduced size in sheets of four. This found and led to fixes for: overlapping timeline labels (slide 10), text overlapping a note (slide 6), an overlapping connector label (slide 4), an empty card (slide 2), and a small screenshot (slide 8). The revised slides 2, 4, 6, 8, 10, 13, 14, 17, 20 and 22 were re-inspected after the fixes.
- **Diagrams and charts:** each PNG was viewed; the architecture, causal chain, risk, ER, correlation, RCA sequence, navigation and topology diagrams were corrected and re-viewed. `chart_seeded_kpis.png` was re-viewed after its last label edit.
- **Not possible:** an interactive check in the Word and PowerPoint windows, other renderers (no LibreOffice), and accessibility tooling beyond alt text on pictures.

## 3. Accuracy notes and discrepancies

- The handbook's numbers for the seeded incident (symptom onsets, scores 0.8947 and 0.675, temporal 0.766, chain consistency 1.0, confidence 0.8947) were recomputed from the repository's simulator, detectors and correlation engine, and match the demo run and the screenshots (RCA 85 %, correlation 89 %, health score 62).
- Screenshots differ from the demo in one respect: they come from an environment where high-risk actions were disabled (rollback shows blocked, incident still investigating). The demo enables them for itself. The handbook says so.
- Documentation discrepancies found: see `source_inventory.md` ("Discrepancies found between documents and code").
- External references (five official pages) were fetched on 2026-10-20 and used only for the narrow statements cited in Appendix C.

## 4. Remaining limitations of the deliverables

1. **Length.** The handbook is 67 pages against a 25 to 40 page target. The count comes from 22 mandatory chapters starting on new pages, 30 figures (including 11 full-width screenshots) and 26 tables; content was not padded, but the target was exceeded.
2. **Screenshot legibility.** The dashboard captures are about 1900 px wide and are shown at page width, so UI text is small in print. Three captures are cut off at the bottom in the source document.
3. **No live-LLM, Docker or PostgreSQL claims** are made as verified; they are labelled unverified here.
4. **Mutation testing** is described as hand-applied and recorded in the plan; it is not reproducible by command.
5. **Fonts.** Documents specify Calibri, Consolas and Cambria Math, which exist on Windows with Office; other systems substitute fonts and the page count may change.
6. **Reproducibility.** `build_all.sh` needs `backend/.venv` and, for PDFs and field updates, Windows Word and PowerPoint reachable from WSL. Without Office it still builds the DOCX and PPTX.
