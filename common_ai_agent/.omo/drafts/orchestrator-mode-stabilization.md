# Draft: Orchestrator Mode Stabilization

## Requirements Confirmed
- User wants a detailed implementation plan for another agent.
- The plan must stabilize orchestrator mode after merge.
- The plan must preserve the concept already discussed: locked truth, contract/evidence, strict pass/fail/blocked, and owner workflow repair.
- The plan must not weaken strict evidence semantics to make tests green.

## Current Evidence
- Frontend exec-mode picker tests pass: orchestrator can be selected.
- Backend run-policy tests pass: `exec_mode=orchestrator` is accepted and persisted.
- Focused orchestrator Python suite result observed: 31 passed, 5 failed, 5 skipped.
- The failures show worker dispatch exists, but strict stage evidence gates convert fixture runs to `error` or downstream `blocked`.

## Technical Decisions
- Keep strict evidence gating as the production truth.
- Update tests and fixtures so "completed" only means worker completed and required stage evidence passed.
- Add explicit tests for blocked/error owner routing rather than treating it as a failed orchestrator plumbing path.
- Verify UI exposes failed/blocked stages and owner handoff state in orchestrator mode.

## Open Questions
- None blocking. Default: stabilize through deterministic tests and mock fixtures first, then browser UI smoke.

## Scope Boundaries
- INCLUDE: API dispatch semantics, worker mock fixture artifacts, stage evidence gate classification, DB status persistence, UI failed/blocked visibility tests.
- INCLUDE: focused regression commands and browser/UI smoke scenario.
- EXCLUDE: full live LLM orchestration, production EDA signoff, changing MCTP contract semantics.
