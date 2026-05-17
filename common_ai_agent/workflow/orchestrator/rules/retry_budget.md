# Orchestrator Retry Budget

Persisted at `<ip>/handoff/orchestrator_state.json`:

```json
{
  "ip": "<ip>",
  "started_at": "2026-05-17T12:34:56Z",
  "budget": {
    "ssot-gen":  { "max": 3, "used": 0 },
    "rtl-gen":   { "max": 5, "used": 0 },
    "tb-gen":    { "max": 3, "used": 0 },
    "sim":       { "max": 2, "used": 0 },
    "sim_debug": { "max": 1, "used": 0 },
    "coverage":  { "max": 2, "used": 0 },
    "goal-audit":{ "max": 1, "used": 0 }
  },
  "last_dispatch": { "workflow": "rtl-gen", "at": "..." }
}
```

## Default Budgets

| Stage | Max retries | Reset on |
|---|---|---|
| ssot-gen | 3 | success (validator passes) |
| fl-model-gen | 2 | success |
| cl-model-gen | 2 | success |
| equiv-goals | 2 | success |
| rtl-gen | 5 | success |
| lint | 3 | clean |
| tb-gen | 3 | success |
| sim | 2 | clean cocotb pass |
| sim_debug | 1 | always escalate when exhausted |
| coverage | 2 | full bins |
| goal-audit | 1 | escalate when exhausted |
| syn | 2 | success |
| sta | 2 | success |
| pnr | 2 | success |
| sta-post | 1 | escalate when exhausted |

## Budget Exhaustion → Escalation

When `used >= max` for a stage:

1. Stop dispatching that stage.
2. Write a review card under `<ip>/review/budget_exhausted_<stage>.json` with:
   - last 3 failure summaries
   - evidence paths
   - suggested manual intervention
3. Surface in Pipeline chat: `Blocked on: <stage> exhausted retry budget`.
4. Wait for user approval (`/approve` slash command) or user reset (`/reset-budget <stage>`).

## Cross-Stage Cumulative Cap

Total dispatches across all stages capped at **40 per IP per run** (configurable via `ORCHESTRATOR_MAX_DISPATCHES`).

If reached, escalate regardless of per-stage budget. This prevents runaway loops between stages (e.g., `tb-gen` ↔ `sim_debug` ping-pong).

## User Override

Pipeline chat commands the orchestrator must honor:

- `/reset-budget <stage>` — set `used=0` for that stage
- `/reset-budget all` — reset every stage
- `/cap <stage> <n>` — change `max` for one stage in this run
- `/freeze` — pause all dispatch
- `/resume` — unfreeze
