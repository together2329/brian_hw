# Full Flow Pipeline

## Canonical DAG

```text
requirement
  -> ssot-gen
  -> {fl-model-gen, cl-model-gen}
  -> equiv-goals
  -> rtl-gen
  -> {lint, tb-gen, syn}

tb-gen -> sim -> {coverage, sim-debug}
coverage -> truth-coverage
syn -> {sta, pnr}
pnr -> post-sta
all requested evidence -> goal-audit -> signoff
```

ATLAS Web UI, Textual UI, and headless tests must call the same common engine
path. UI code renders and queues work; it does not own stage logic.

The orchestrator agent owns multi-stage convergence. Workspace views can still
run one workflow at a time, but pipeline mode routes owner-classified feedback
across workflow boundaries. See [[orchestrator-worker-handoff]].

Cross-workflow repair is orchestrator-centered. Workers may emit suggested
handoffs, but they do not directly dispatch other workflow workers. The
Pipeline UI renders orchestrator state from `/api/pipeline/state`; Workspace
can claim JSON handoffs through `/take`.

The UI pipeline scheduler defaults to `schedule: "auto"`:

- one resolved worker URL -> serial execution
- multiple resolved worker URLs -> DAG execution
- no resolved worker -> write durable handoff JSON for `/take`

Explicit `schedule: "dag"` and `schedule: "serial"` remain available for
benchmark/debug runs.

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
| Truth Coverage | `python3 workflow/reqcov/scripts/check_truth_coverage.py <ip> --root <ip-parent>` | `signoff/truth_coverage.json` |
| Debug | `/sim-debug <ip>` | mismatch classification and wave/source evidence |
| Audit | `/goal-audit <ip>` | final FL-vs-RTL goal audit |

## Reference Run

[[arm-m0-min-pipeline-run]] (2026-05-15) — minimal ARMv6-M Thumb CPU walked
through ssot-gen → fl-model-gen → rtl-gen → tb-gen → sim → lint on the
headless surface with `gpt-5.3-codex` + `/mode pipeline`. compile/lint/sim
equivalence/coverage all green. Use this as the worked example for a fresh
CPU-class IP.

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
- [[workflow-feedback-and-scheduling]]
- [[orchestrator-worker-handoff]]
- [[golden-todo-evidence]]
