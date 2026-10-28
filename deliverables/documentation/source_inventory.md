# Source inventory

Everything below was opened and read (or, for generated/binary items, inspected) while writing the handbook and deck. Claims in the handbook rest on source code, tests, configuration and commands run in this session; planning documents were used to find things, not as proof.

## Specification and planning documents

| File | Used for |
|---|---|
| `PROJECT_SPEC.md` (1361 lines) | Authority on intended behaviour; consulted by section number (§5 incidents, §6 detectors, §7 incident object, §8 RCA, §12 policy, §24 seeded scenario). Not re-read line by line; behaviour was checked against code. |
| `ENGINEERING.md` | Engineering rules (milestones, honesty about tests, no secrets, allowlisted agent tools). |
| `IMPLEMENTATION_PLAN.md` | Milestones, requirement traceability (R1 to R32), final self-audit, recorded verification results (labelled "recorded" in the handbook). |
| `ARCHITECTURE.md` | Component contracts; every contract used in the handbook was re-checked against the code. |
| `README.md`, `OVERNIGHT_STATUS.md`, `docs/*.md` | Commands, limitations, status table. |

## Code read

| Area | Files |
|---|---|
| C library | `c-library/include/call_analyzer.h`, `src/ca_internal.h`, `src/parser.c` (header, `split_csv`, `build_record`, `parse_source`), `src/utils.c` (`call_outcome_for_status`, allocation wrappers, robust z-score, score), `src/analyzer.c` (`calculate_cell_statistics`), `src/anomaly.c` (defaults, `robust_scores`, `detect_cells`), `CMakeLists.txt`, `tests/test_call_analyzer.c` (test list, `test_oom_all_operations`) |
| Binding | `backend/call_analyzer/_native.py`, `analysis.py`, `errors.py` |
| Simulation | `backend/app/simulation/` (`metrics.py`, `model.py`, `incidents.py`, `scenario.py`, `topology.py`) |
| Analytics | `backend/app/analytics/` (`config.py`, `detectors.py`, `engine.py`, `causal_graph.py`, `correlation.py`, `sources.py`) |
| Persistence and API | `backend/app/models/*.py`, `api/*.py` (all routes and role dependencies), `schemas/api.py` (request models), `services/pipeline.py`, `main.py`, `config.py`, `alembic/versions/0001_initial_schema.py` (searched for triggers) |
| Security | `security/tokens.py`, `audit.py`, `api/deps.py`; middleware behaviour from `ARCHITECTURE.md` §3.7a cross-checked by `tests/test_security.py` names |
| AI | `backend/app/llm/base.py`, `factory.py`, `mock.py`, `anthropic_provider.py` (headers, error handling), `openai_provider.py` (key lines), `rca/engine.py`, `schemas.py`, `tools.py` (tool list, argument models), `mock_investigator.py` (header) |
| Reporting | `reporting/document.py`, `render.py`, `builder.py` |
| Agent | `agents/policy.py`, `runner.py`, `planner.py`, `service.py`, `workspace.py`, `tools.py` (registry, `rollback_deployment`), `data/advisories.json`, `demo-workspace/requirements.txt` |
| Frontend | `frontend/package.json`, `src/App.tsx`, `src/services/api.ts`, `src/hooks/useApi.ts`; page and component list |
| Deployment | `docker-compose.yml`, `backend/Dockerfile`, `docker-entrypoint.sh`, `frontend/Dockerfile`, `nginx.conf`, `.env.example`, `Makefile`, `scripts/docker_smoke.sh`, `init_env.py`, `hash_token.py`, `demo.py` (header), `backend/app/bootstrap.py` |

Not read in full: `backend/tests/*.py` (names and counts only), `frontend/src/pages/*.tsx` and components (structure only), `PROJECT_SPEC.md` (by section).

## Discrepancies found between documents and code

- `OVERNIGHT_STATUS.md` records "13 endpoints" at milestone M6; the current code has 26 routes plus `/metrics` (RCA, report, agent and network routes were added later). The handbook uses the code.
- `ARCHITECTURE.md` and the README call the audit log "append-only". The code only inserts, but no database trigger or permission prevents UPDATE or DELETE. The handbook says so.
- `agent_runs.incident_id` has no foreign key (the ER diagram says so).
- The simulated rollback is a re-simulation of the same model, so its "recovery verified" result is a control-flow check, not an independent validation (stated in Chapters 15 and 20).
- Python test count: plan says "352 passed + 3 skips"; this session collected 355, ran 352, skipped 3 (consistent).
- The working tree contains a deleted file named `tatus --short` that predates this work and was left alone and unstaged.

## Screenshot inventory

Source: `docs/source/aegis.docx` (present; 13 embedded images extracted unmodified to `deliverables/assets/screenshots/`; the document's only text is the label "Viewer:" before the last two images). Order below is document order.

| File | Size (px) | Shows | Handbook figure | Slide | Limitations |
|---|---|---|---|---|---|
| `shot_01_src-image11.png` | 1917 x 939 | Dashboard (health 62, incident, RCA headline, KPI cards, chart, agent run) | Fig. 28 | 15 | Small text at page width; readable zoomed |
| `shot_02_src-image8.png` | 1919 x 784 | Network Overview (8 KPI cards, 12-cell latency chart) | Fig. 8 | 7 | Same |
| `shot_03_src-image6.png` | 1919 x 962 | Call Analytics (totals, drop rate by cell, status codes, C anomalies) | Fig. 4 | 6 | Same |
| `shot_04_src-image5.png` | 1897 x 753 | Anomalies, critical filter | Fig. 12 | 8 (bottom 20 % cropped) | Table continues beyond the capture |
| `shot_05_src-image12.png` | 1919 x 562 | Incidents list | Fig. 16 | 10 | none |
| `shot_06_src-image9.png` | 1897 x 988 | RCA page | Fig. 22 | 11 | Bottom edge cuts off the recommendations list |
| `shot_07_src-image13.png` | 1918 x 881 | AI Reports | Fig. 23 | 12 | Report body scrolls beyond the capture |
| `shot_08_src-image7.png` | 1899 x 906 | DevSecOps Agent | Fig. 26 | 13 | Third run is cut off |
| `shot_09_src-image3.png` | 1007 x 197 | Separation-of-duties message | Fig. 19 | 14 | Cropped panel |
| `shot_10_src-image4.png` | 1696 x 323 | Security findings | Fig. 27 | (not used) | none |
| `shot_11_src-image10.png` | 1688 x 849 | Audit log, chain valid (38 rows) | Fig. 20 | 14 | Cut off at the bottom |
| `shot_12_src-image1.png` | 1689 x 268 | Audit page as a viewer: role error | (not embedded; same message as shot 13) | (not used) | none |
| `shot_13_src-image2.png` | 1670 x 178 | Verify unavailable for a viewer | Fig. 18 | (not used) | none |

Sensitive-data check (visual inspection of every image): no token, key, password, private address or `.env` content appears. Audit-log images show actor names (`local-admin`, `agent:AGR-...`), short request ids and synthetic timestamps only.

## Figure plan (diagrams from maintainable source)

Source: `scripts/documentation/diagrams.py` (boxes and arrows as Python data) rendered with `diagram_kit.py` to PNG and SVG in `deliverables/assets/diagrams/`. Charts: `charts.py` from `deliverables/assets/charts/evidence.json` (produced by `extract_evidence.py` from the repository's own simulator, detectors and correlation engine).

| # | Required diagram | File |
|---|---|---|
| 1 | System architecture | `01_system_architecture` |
| 2 | End-to-end data flow | `02_end_to_end_data_flow` (and `13_end_to_end_sequence`) |
| 3 | C-to-Python binding and memory ownership | `03_c_python_binding_memory` |
| 4 | Telemetry causal chain | `04_telemetry_causal_chain` |
| 5 | Detector pipeline | `05_anomaly_detector_pipeline` |
| 6 | Correlation and incident formation | `06_event_correlation_incident_formation` |
| 7 | LLM tool-calling and RCA sequence | `07_llm_tool_calling_rca_sequence` |
| 8 | Agent lifecycle | `08_devsecops_agent_lifecycle` |
| 9 | Risk classification and approval | `09_risk_classification_approval` |
| 10 | Database entity relationships | `10_database_entity_relationships` |
| 11 | Deployment topology | `11_deployment_container_topology` |
| 12 | Dashboard navigation and workflows | `12_dashboard_navigation_workflows` |

Charts: `chart_seeded_kpis`, `chart_detector_example`, `chart_score_curve`, `chart_incident_timeline`, `chart_hypothesis_scores`. The deck redraws the architecture, flow, correlation, lifecycle, risk table, topology, timeline and test charts as native PowerPoint shapes, tables and charts.
