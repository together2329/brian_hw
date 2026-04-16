# Lint Validation Test Plan (Scripts + Makefile Policies)

This plan defines a deterministic validation strategy for lint tooling in `sim/cocotb`.

## Goals

1. Validate **policy wiring** for `lint-fast`, `lint`, and `lint-ci` strictness tiers.
2. Validate lint script behavior for:
   - `lint_rtl_pyslang.py`
   - `cocotb_results_gate.py`
3. Validate `lint-report` behavior:
   - deterministic/stable formatting
   - stable path rendering (repo-relative)
   - non-gating exit semantics

## Scope

- `sim/cocotb/Makefile`
- `sim/cocotb/lint_rtl_pyslang.py`
- `sim/cocotb/cocotb_results_gate.py`
- Generated artifacts:
  - `sim/cocotb/lint_report.md`
  - `sim/cocotb/lint_rtl_report.json`
  - `sim/cocotb/lint_rtl_report.sarif`
  - `sim/cocotb/cocotb_results_gate.json`

## Test Matrix

### A) Makefile strictness-tier policy tests

| ID | Command | What it validates | Expected result |
|---|---|---|---|
| A1 | `make -C sim/cocotb -n lint-fast` | `lint-fast` wires `LINT_FAST_MYPY_BLOCKING` + `LINT_FAST_RTL_WARN_AS_ERROR` | Dry-run output shows `lint-type MYPY_BLOCKING=$(LINT_FAST_MYPY_BLOCKING)` and `lint-rtl-fast RTL_WARN_AS_ERROR=$(LINT_FAST_RTL_WARN_AS_ERROR)` |
| A2 | `make -C sim/cocotb -n lint` | full tier wires `LINT_FULL_MYPY_BLOCKING` + `LINT_FULL_RTL_WARN_AS_ERROR` | Dry-run output shows `lint-type MYPY_BLOCKING=$(LINT_FULL_MYPY_BLOCKING)` and `lint-rtl RTL_WARN_AS_ERROR=$(LINT_FULL_RTL_WARN_AS_ERROR)` |
| A3 | `make -C sim/cocotb -n lint-ci` | CI tier wires `LINT_CI_MYPY_BLOCKING`, `LINT_CI_RTL_WARN_AS_ERROR`, and `LINT_CI_REQUIRE_RESULTS` | Dry-run output shows all three propagated into child invocations |

### B) `lint_rtl_pyslang.py` policy tests

| ID | Command | What it validates | Expected result |
|---|---|---|---|
| B1 | `make -C sim/cocotb lint-rtl RTL_WARN_AS_ERROR=0` | warnings do not gate when warn-as-error disabled | exits 0 if no errors/new baseline violations |
| B2 | `make -C sim/cocotb lint-rtl RTL_WARN_AS_ERROR=1` | warnings can gate with warn-as-error enabled | exits non-zero when warnings exist |
| B3 | `make -C sim/cocotb lint-rtl LINT_RTL_BASELINE=lint_baseline_empty.json` | baseline mode only fails on new diagnostics | `counts.new_vs_baseline` and exit status match expected behavior |
| B4 | `make -C sim/cocotb lint-rtl LINT_RTL_INCLUDE='rtl/**/*.sv' LINT_RTL_EXCLUDE='rtl/dma.sv'` | include/exclude discovery and empty-set protection | deterministic error if no files discovered; otherwise discovered set respects filters |
| B5 | inspect `sim/cocotb/lint_rtl_report.json` + `.sarif` | structured artifact schema stability | required top-level keys present (`tool`, `policy`, `counts`, `diagnostics`, `status`) |

### C) `cocotb_results_gate.py` tests

| ID | Command | What it validates | Expected result |
|---|---|---|---|
| C1 | `make -C sim/cocotb lint-cocotb-results COCOTB_RESULTS_XML=results.xml` | pass/fail parsing and summary | exits 0 when no failing tests; non-zero on any failure/error; failing-test count verified via log/JSON summary artifact |
| C2 | `make -C sim/cocotb lint-cocotb-results COCOTB_RESULTS_XML=does_not_exist.xml` | missing file handling | non-zero exit with clear error message |
| C3 | run gate on synthetic XML with `<failure>` and `<error>` | both node types are treated as failures | failing test list includes both kinds |

### D) `lint-report` determinism + path normalization tests

| ID | Command | What it validates | Expected result |
|---|---|---|---|
| D1 | run twice: `make -C sim/cocotb lint-report LINT_CI_REQUIRE_RESULTS=0` then compare outputs | deterministic formatting/content ordering | generated `lint_report.md` is byte-identical across runs when inputs unchanged |
| D2 | inspect artifact paths in `lint_report.md` | stable path normalization | paths are repo-relative (`sim/cocotb/...`), no host-absolute prefixes |
| D3 | `make -C sim/cocotb lint-report LINT_CI_REQUIRE_RESULTS=0` when `lint-ci` fails | non-gating policy | target exits 0 and still emits report artifact |
| D4 | `make -C sim/cocotb help` | policy documentation consistency | help text explicitly describes lint-report as deterministic and non-gating |

## Execution Order

1. A-series (tier wiring, fast feedback via dry-run)
2. B-series (RTL policy + artifact schema)
3. C-series (results gate)
4. D-series (report determinism/path policy)

## Pass Criteria

- All A-series dry-run checks confirm exact variable propagation.
- B/C script behavior matches documented exit semantics and artifact expectations.
- D-series confirms deterministic report output and repo-relative path stability.
- No contradiction between behavior and `make help` text.

## Regression Triggers

Re-run this plan whenever any of the following changes:

- `sim/cocotb/Makefile` lint targets
- policy env vars (`LINT_*`, `RTL_*`, `COCOTB_RESULTS_*`)
- `lint_rtl_pyslang.py` or `cocotb_results_gate.py`
- lint artifact formats (`.md`, `.json`, `.sarif`)
