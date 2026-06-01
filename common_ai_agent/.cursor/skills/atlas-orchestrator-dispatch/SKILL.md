---
name: atlas-orchestrator-dispatch
description: Work on ATLAS orchestrator, worker handoff, pipeline dispatch, and UI/API product-flow validation. Use for orchestrator, pipeline, worker, handoff, or DAG debugging tasks.
---

# Atlas Orchestrator Dispatch

## Read First

- `doc/wiki/orchestrator-worker-handoff.md`
- `doc/wiki/orchestrator-loop-on-react-loop-plan.md`
- `doc/wiki/orchestrator-llm-loop-phase3.md`
- `doc/wiki/atlas-dag-ip-flow-runbook.md`
- `doc/wiki/pipeline-progress-debugging.md`
- `workflow/orchestrator/workspace.json`

## Control Rule

The orchestrator schedules work and convergence. It does not own SSOT, RTL, TB, coverage, or EDA artifacts.

Workers may emit evidence, feedback, and `suggested_handoff`. The orchestrator decides dispatch, persistence, retry, stale invalidation, or human review.

## Useful Commands

```bash
python3 src/atlas_ui.py --port 8765
python3 src/main.py --serve --all-workflows --port 5601
python3 src/headless_workflow.py --root <root> --ip <ip> --stages <stages>
```

For user-facing claims, validate through the UI/API/worker path when possible. Use headless runs for reproduction and regression.
