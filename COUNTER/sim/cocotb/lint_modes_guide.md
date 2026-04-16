# Cocotb Lint Modes Guide

This guide documents lint modes, strictness controls, and CI/report integration in `sim/cocotb/Makefile`.

## Overview

There are three lint tiers:

- **Fast** (`make -C sim/cocotb lint-fast`)
  - Intended for pre-commit / quick local feedback.
  - Runs: `lint-py` + `lint-type` + `lint-rtl-fast`.

- **Full** (`make -C sim/cocotb lint`)
  - Intended for complete local static checks before push.
  - Runs: `lint-py` + `lint-type` + `lint-rtl`.

- **CI** (`make -C sim/cocotb lint-ci`)
  - Intended for CI gating.
  - Runs: `lint-py` + `lint-type` + `lint-rtl` + `lint-cocotb-results`.

## Strictness controls

Defaults are tiered so fast/full are permissive and CI is strict:

- Fast:
  - `LINT_FAST_MYPY_BLOCKING=0`
  - `LINT_FAST_RTL_WARN_AS_ERROR=0`
- Full:
  - `LINT_FULL_MYPY_BLOCKING=0`
  - `LINT_FULL_RTL_WARN_AS_ERROR=0`
- CI:
  - `LINT_CI_MYPY_BLOCKING=1`
  - `LINT_CI_RTL_WARN_AS_ERROR=1`
  - `LINT_CI_REQUIRE_RESULTS=1`

## Target details

### `lint-py`
Python static checks:
- `python3 -m py_compile $(TEST_DIR)/*.py`
- `ruff` if available, otherwise `flake8`

### `lint-type`
Optional mypy check:
- `MYPY_BLOCKING=1` => blocking failures
- `MYPY_BLOCKING=0` => non-blocking warnings

### `lint-rtl`
Runs pyslang lint over discovered RTL/TB files.

Key controls:
- `LINT_RTL_INCLUDE` (default: `rtl/**/*.sv,tb/**/*.sv`)
- `LINT_RTL_EXCLUDE` (default: empty)
- `LINT_RTL_BASELINE` (optional; fail only on new diagnostics)
- `RTL_WARN_AS_ERROR` (passed from tier targets)

Artifacts:
- `LINT_RTL_JSON` (default `sim/cocotb/lint_rtl_report.json`)
- `LINT_RTL_SARIF` (default `sim/cocotb/lint_rtl_report.sarif`)

### `lint-rtl-fast`
Runs lightweight RTL subset lint for pre-commit.

Key controls:
- `LINT_RTL_FAST_INCLUDE` (default: `rtl/dma.sv,tb/dma_cocotb_top.sv,tb/ram_model.sv`)
- `LINT_RTL_FAST_EXCLUDE` (default: empty)

### `lint-cocotb-results`
Parses cocotb JUnit XML and applies a gate:
- input: `COCOTB_RESULTS_XML` (default: `sim/cocotb/results.xml`)
- returns 0 when no failing tests
- returns non-zero on any `<failure>` / `<error>`
- emits JSON summary at `COCOTB_RESULTS_JSON`

### `lint-report`
Generates deterministic markdown report at `sim/cocotb/lint_report.md` with:
- stable section ordering
- PASS/FAIL summary table
- repo-relative artifact paths

`lint-report` is **non-gating**: it always emits the report artifact and does not fail the target solely because checks failed.

## Usage examples

### Fast lint

```sh
make -C sim/cocotb lint-fast
```

### Full lint

```sh
make -C sim/cocotb lint
```

### CI-equivalent lint gate

```sh
make -C sim/cocotb lint-ci
```

### RTL baseline mode

```sh
make -C sim/cocotb lint-rtl LINT_RTL_BASELINE=lint_baseline_empty.json
```

### Results gate against default XML in `sim/cocotb`

```sh
make -C sim/cocotb lint-cocotb-results COCOTB_RESULTS_XML=results.xml
```

### Generate deterministic report

```sh
make -C sim/cocotb lint-report LINT_CI_REQUIRE_RESULTS=0
```

## Pre-commit integration

Repository root `.pre-commit-config.yaml` provides local hooks:

- `cocotb-lint-py` → `make -C sim/cocotb lint-py`
- `cocotb-lint-rtl-fast` → `make -C sim/cocotb lint-rtl-fast`

```sh
pre-commit install
pre-commit run --all-files
```
