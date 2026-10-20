# Presentation outline

22 slides. Source: `scripts/documentation/deck_notes.py` and `build_deck.py`.

| # | Section | Title (central message) | Visual |
|---|---|---|---|
| 1 | Aegis-Net | Aegis-Net: from network symptoms to audited remediation | Title slide with status vocabulary and the data notice. |
| 2 | The problem | Troubleshooting a degraded network means stitching together scattered evidence | Three cards: scattered evidence, cascading symptoms, decisions that need an audit trail; a cascade chain from memory to dropped calls. |
| 3 | Goals and capabilities | Six capabilities, each with an honest status | Six tiles with status tags. |
| 4 | End to end | One incident travels through ten stages, and later stages read stored evidence | Ten editable shapes in two rows with arrows. |
| 5 | Architecture | Four languages meet at three explicit interfaces | Layered architecture built from editable shapes. |
| 6 | Call analysis | A C library parses and analyses call records; Python only marshals results | Flow of four editable nodes; Call Analytics screenshot. |
| 7 | Telemetry | A causal simulator produces a repeatable memory-leak incident | Network Overview screenshot; causal chain chips. |
| 8 | Anomaly detection | Four interpretable detectors must agree before a point is flagged | Native line chart of the worked example; four detector cards; Anomalies screenshot. |
| 9 | Correlation | The correlation engine turns many symptoms into one ranked, caveated incident | Editable evidence-to-incident diagram with the scoring formula. |
| 10 | Incident timeline | The deployment outranks memory exhaustion because it preceded the first symptom on the same node | Editable timeline, native stacked bar chart of score contributions, Incidents screenshot. |
| 11 | AI root-cause analysis | The model can only ask read-only tools; the engine validates every answer | RCA screenshot and a short list of safeguards. |
| 12 | Reporting | Reports compute every figure from stored data; only the summary is prose | AI Reports screenshot and bullets. |
| 13 | DevSecOps agent | The agent is a deterministic, policy-controlled playbook, not an LLM planner | Editable lifecycle chevrons; Agent screenshot; scenario bullets. |
| 14 | Risk policy and audit | Policy is enforced in code at execution time, and every action leaves a hash-chained record | Editable risk-class table, audit and separation-of-duties screenshots. |
| 15 | Dashboard | One screen answers the six operator questions | Dashboard screenshot with six numbered answers. |
| 16 | API, database, services | Twenty-six routes and nineteen tables, with roles enforced per endpoint | Endpoint-group table and database table groups, both editable. |
| 17 | Docker deployment | Four containers start with one command; the backend image builds and tests the C library | Editable container topology and command box. |
| 18 | Testing | Layered tests give evidence, and the gaps are stated | Native table of results and a native bar chart of Python tests per module. |
| 19 | Live demo | The demo runs offline in seconds; the full stack needs Docker | Numbered steps with commands. |
| 20 | Status | What is verified, unverified, simulated or not implemented | Four-column status matrix. |
| 21 | Future work | Priorities for closing the largest gaps | Ordered roadmap. |
| 22 | Takeaways | Evidence-grounded, policy-controlled, and honest about limits | Five takeaway statements. |
