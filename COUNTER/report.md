# Cocotb Environment Test Expansion Report

## Summary
Added and validated a new set of cocotb environment-focused unit tests covering configuration parsing, Makefile behavior, artifact naming, and reproducibility checks.

## New Test Files
- `sim/cocotb/tests/test_config_env.py`
- `sim/cocotb/tests/test_makefile_dryrun.py`
- `sim/cocotb/tests/test_artifact_naming.py`
- `sim/cocotb/tests/test_reproducibility.py`

## Coverage Added

### 1) Config environment override tests
`test_config_env.py`
- Valid decimal env overrides (e.g., `DMA_DATA_WIDTH=512`, `DMA_NUM_RANDOM=20`)
- Valid hex env overrides (e.g., `DMA_DATA_WIDTH=0x200`, `DMA_SEED=0x3039`)
- Invalid env values with exact `ValueError` assertions:
  - non-integer value
  - byte-alignment violation
  - lane-alignment violation
  - derived power-of-two violation
  - insufficient address width
- Missing env vars fallback to defaults + derived-parameter sanity checks

### 2) Makefile dry-run + guard behavior tests
`test_makefile_dryrun.py`
- `make -n smoke` propagates:
  - `DMA_SEED=101`
  - `DMA_NUM_RANDOM=5`
  - `DMA_ARTIFACT_TAG=smoke_seed101_n5`
- `make -n regress` propagates:
  - `DMA_SEED=12345`
  - `DMA_NUM_RANDOM=20`
  - `DMA_ARTIFACT_TAG=regress_seed12345_n20`
- `make -n stress` propagates:
  - `DMA_SEED=424242`
  - `DMA_NUM_RANDOM=100`
  - `DMA_ARTIFACT_TAG=stress_seed424242_n100`
- Missing cocotb availability guard path:
  - `check-cocotb` fails with clear message when unavailable
  - `sim` target fails fast with same guard message when `cocotb-config` is hidden from `PATH`

### 3) Deterministic artifact naming tests
`test_artifact_naming.py`
- `_artifact_name()` uses explicit `DMA_ARTIFACT_TAG` when set
- `_artifact_name()` falls back to `seed{SEED}_n{NUM_RANDOM}` when unset

### 4) Fixed-seed reproducibility checks
`test_reproducibility.py`
- Same seed + same trial count => identical fingerprint
- Different seed => different fingerprint
- `config.SEED` + `config.NUM_RANDOM` produce stable repeated outcomes

## Validation Evidence
Combined unittest execution passed:
- `Ran 18 tests in 0.381s`
- `OK`

## Outcome
Environment-level cocotb test coverage is now significantly stronger for:
- deterministic behavior
- guard/failure-path checks
- configuration robustness
- artifact naming consistency
