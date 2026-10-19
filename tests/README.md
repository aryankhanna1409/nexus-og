# Tests

Test suites live next to the code they exercise; this directory exists to match the layout in
`PROJECT_SPEC.md` §18 and to explain where everything is.

| Suite | Location | Run |
|---|---|---|
| C library (unit, malformed input, memory, fault injection) | `c-library/tests/` | `make c-test`, `make c-test-asan` |
| Python unit and API tests | `backend/tests/test_*.py` | `make py-test` (also against the ASan library: `make py-test-asan`) |
| End-to-end chains of spec §22 and the offline demo | `backend/tests/test_e2e.py` | part of `make py-test` |
| Dashboard component tests | `frontend/src/test/` | `make frontend-test` |
| Python 3.12 compatibility | `scripts/container_py312_test.sh` | `make container-test` |
| Docker stack and browser check | `scripts/docker_smoke.sh`, `scripts/ui_check.mjs` | `make docker-smoke` (`SMOKE_UI_CHECK=1` for the browser check) |

`make test` runs the C, Python, type-check and dashboard suites.
