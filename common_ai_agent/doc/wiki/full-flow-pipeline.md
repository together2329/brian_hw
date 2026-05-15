# Full Flow Pipeline

## Canonical Path

```text
requirement
  -> ssot-gen
  -> fl-model-gen
  -> cl-model-gen
  -> equiv-goals
  -> rtl-gen
  -> lint
  -> tb-gen
  -> sim
  -> coverage
  -> sim-debug
  -> goal-audit
  -> syn
  -> sta
  -> pnr
  -> post-sta
```

ATLAS Web UI, Textual UI, and headless tests must call the same common engine
path. UI code renders and queues work; it does not own stage logic.

## Stage Summary

| Stage | Main command | Output evidence |
| --- | --- | --- |
| SSOT | `/new-ip`, `/grill-me`, `/to-ssot` | `yaml/<ip>.ssot.yaml`, Q&A/review cards |
| FL | `/ssot-fl-model <ip>` | `model/functional_model.py`, `cov/fcov_plan.json` |
| CL | `/ssot-cycle-model <ip>` | `model/cycle_model.py`, CL self-check |
| Equiv | `/ssot-equiv-goals <ip>` | `verify/equivalence_goals.json` |
| RTL | `/ssot-rtl <ip>` | RTL files, filelist, `rtl_todo_plan.json`, compile/lint evidence |
| Lint | `/lint <ip>` | `lint/dut_lint.json` and lint todo evidence |
| TB | `/ssot-tb <ip>` | cocotb/pyuvm TB, manifest, scoreboard |
| Sim | `/sim <ip>` | `results.xml`, VCD, `scoreboard_events.jsonl` |
| Coverage | `/coverage <ip>` | function/cycle/static coverage reports |
| Debug | `/sim-debug <ip>` | mismatch classification and wave/source evidence |
| Audit | `/goal-audit <ip>` | final FL-vs-RTL goal audit |

## Pipeline Modes

- `interactive`: human answers `ask_user` and review cards.
- `auto-select`: benchmark mode; SSOT Q&A picks explicit suggested/default safe answers and records them for review.
- `pipeline`: keep flowing through non-blocking work; collect human gates.
- `ci`: fail fast on blockers or missing evidence.

## Success Criteria

The flow is successful only when required stage evidence is fresh, every required
todo ledger row is approved by evidence or human authority, and no unresolved
owner-classified mismatch remains.

## Related

- [[common-ai-agent-map]]
- [[workflow-ownership-and-boundaries]]
- [[golden-todo-evidence]]
