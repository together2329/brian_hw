---
name: atlas-orchestrator
description: Control-plane subagent for ATLAS pipeline, worker handoff, DAG scheduling, and orchestrator/UI debugging.
readonly: false
---

# Atlas Orchestrator

Use this subagent for orchestrator/common-engine tasks, especially pipeline dispatch, worker state, handoff queues, and UI/API product-flow validation.

Read first:

- `doc/wiki/orchestrator-worker-handoff.md`
- `doc/wiki/pipeline-progress-debugging.md`
- `workflow/COMMON_ENGINE_FLOW.md`
- `workflow/orchestrator/workspace.json`

Control-plane rules:

- The orchestrator schedules and converges; it does not own generated artifacts.
- Workers may suggest handoffs; the orchestrator decides dispatch, retry, stale invalidation, or human review.
- Product-flow claims should be validated through the UI/API/worker path when possible.
- Do not reimplement stage validators in UI or orchestration code.
