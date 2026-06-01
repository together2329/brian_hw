---
name: atlas-artifact-owner-routing
description: Classify failed or stale IP artifacts by owner workflow. Use when sim, lint, coverage, SSOT, RTL, TB, or signoff evidence fails or looks stale.
---

# Atlas Artifact Owner Routing

Read `doc/wiki/workflow-ownership-and-boundaries.md` before repairing generated IP artifacts.

## Owner Map

- `req/`: human plus `ssot-gen`.
- `yaml/<ip>.ssot.yaml`: `ssot-gen`.
- `model/functional_model.py`: `fl-model-gen`.
- `model/cycle_model.py`: `cl-model-gen`.
- `rtl/`, `list/`, `rtl_contract.json`: `rtl-gen`.
- `tb/`, `tc/`, scoreboard logic: `tb-gen`.
- `sim/`, waveforms, scoreboard rows: `sim`.
- `cov/coverage*.json`: `coverage`.
- `lint/`, `syn/`, `sta/`, `pnr/`: owning EDA workflow.

## Failure Loop

1. Read stage logs and evidence artifacts.
2. Classify owner.
3. Route the repair through the owner workflow.
4. Rerun the validator.
5. Report evidence and blockers.

Forbidden during pipeline tests: lowering goals, editing logs, deleting evidence, or approving from model confidence alone.
