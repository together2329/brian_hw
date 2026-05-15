# Workflow Ownership And Boundaries

## Rule

Do not directly patch generated IP artifacts during a pipeline test. Use the
owning common_ai_agent workflow, collect evidence, and let validators approve or
reject the result.

Direct manual edits are allowed only when the explicit task is to fix workflow
source code or docs. Even then, do not edit generated IP artifacts to fake a
pipeline pass.

## Ownership Table

| Artifact | Owner workflow | Manual pipeline-test action |
| --- | --- | --- |
| `req/` intent and acceptance criteria | human + `ssot-gen` | ask/review, do not invent |
| `yaml/<ip>.ssot.yaml` | `ssot-gen` | repair through SSOT workflow or human gate |
| `model/functional_model.py` | `fl-model-gen` | regenerate from SSOT |
| `model/cycle_model.py` | `cl-model-gen` | regenerate from SSOT |
| `rtl/`, `list/`, `rtl_contract.json` | `rtl-gen` | run RTL workflow/repair loop |
| `tb/`, `tc/`, scoreboard | `tb-gen` | run TB workflow/repair loop |
| `sim/`, waveforms, scoreboard rows | `sim` | rerun sim, do not edit logs |
| `cov/coverage*.json` | `coverage` | rerun coverage, do not lower goals |
| `lint/`, `syn/`, `sta/`, `pnr/` reports | owning EDA workflow | rerun workflow, preserve evidence |

## Failure Handling

When a stage fails:

1. Read stage logs and evidence artifacts.
2. Classify owner: `ssot-gen`, `fl-model-gen`, `cl-model-gen`, `rtl-gen`, `tb-gen`, `sim`, `coverage`, `tool-fix`, or `human`.
3. Route the repair through the owner workflow.
4. Rerun the validator.
5. Report the evidence and remaining blocker.

## Forbidden During Pipeline Tests

- Editing RTL by hand because sim failed.
- Editing TB by hand because the validator found mismatch, unless the active owner is `tb-gen` and the edit is performed as a workflow fix.
- Editing SSOT, FL, CL, coverage goals, or timing targets to match observed RTL.
- Marking todo rows approved based only on model confidence.
- Deleting evidence files or stale logs to hide a failure.

## Related

- [[full-flow-pipeline]]
- [[golden-todo-evidence]]
- [[human-review-and-escalation]]
