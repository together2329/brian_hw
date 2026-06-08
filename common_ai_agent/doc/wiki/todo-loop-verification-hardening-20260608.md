# Todo Loop Verification Hardening

Date: 2026-06-08

This page records the verification policy added after the Atlas TODO loop
incident where the same underlying task could pass or fail depending on the
LLM's tool-call order.

## Incident

The visible symptom was:

```text
todo_update(index=1, status='completed')
-> Completion blocked: no tools were called since starting this task

read_file / write_file / run_command

todo_update(index=1, status='completed')
-> still blocked

todo_update(index=1, status='rejected',
  reason='Todo engine refuses completion ...')
-> task recorded as rejected
```

This was not an RTL/req/task failure. It was a workflow-state failure.

## Follow-up: TODO Left Open But Worker Stopped

Later on 2026-06-08, the same class of bug appeared in a different branch of
the loop:

```text
active TODO remains pending/in_progress
LLM replies with prose only, no Action
runtime guard says "next response must start with Action"
next LLM turn does not receive the exact TODO continuation prompt
retry/watchdog eventually stops the loop
```

The TODO did not disappear and the task was not complete. The loop stopped
because execution is LLM-action driven: with an unfinished TODO, the model must
emit a tool Action such as `todo_update(...)`, `read_file(...)`,
`run_command(...)`, or `write_file(...)`. The no-action guard correctly noticed
the missing Action, but it only injected a generic warning. It did not reattach
`TodoTracker.get_continuation_prompt()`, so the next model call saw "use an
Action" without the precise current-state transition, for example:

```text
[Task 1/8  IN PROGRESS] ...
-> todo_update(index=1, status='completed') when all criteria met
```

`core/react_loop.py` also deduplicates prompt-only TODO injection by
`(current_index, status)` to avoid spamming the same reminder every iteration.
That dedup is normally useful, but after a text-only/no-action turn it meant the
normal pre-LLM TODO prompt could be skipped because the task/status had not
changed.

The fix in commit `5739ccbc` makes both no-output branches append the active
TODO continuation prompt:

- thinking-only response -> nudge plus active TODO continuation.
- text-only/no-action response -> runtime guard plus active TODO continuation.

This is not an infinite-loop change. The existing retry, text-only watchdog, and
stagnation guards still stop the worker if the model repeatedly refuses to use
tools. The change only ensures each retry contains the exact TODO transition
needed to make progress.

## Root Causes

1. **The recovery instruction did not match the state machine.**

   The tool told the LLM to "call a tool, then retry completed", but the
   implementation only consumed tool credit from `tools_since_in_progress`.
   Tool calls made while the task was still `pending` were buffered as
   `_pending_tool_credit` and were only consumed by `mark_in_progress()`.
   Therefore the documented recovery path looped forever unless the LLM happened
   to restart the task with `status='in_progress'`.

2. **Atlas chat mode and Textual TUI had different loop behavior.**

   `get_continuation_prompt()` correctly produced prompts for `pending`,
   `completed`, and `rejected` states. But Atlas/web chat mode could stop after
   one tool iteration (`EXECUTION_MODE=chat`, `CHAT_MAX_ITERATIONS=1`) before
   the rejected/completed continuation prompt reached the next LLM call. Textual
   kept looping, so it looked correct there.

3. **Tracker failure was allowed to become task failure.**

   A reason like "TodoTracker says no tools were called" describes bookkeeping,
   not an unmet task criterion. Recording that as `rejected` polluted the todo
   ledger and sent the workflow down the wrong repair path.

4. **No-action recovery lost the actionable TODO transition.**

   Runtime no-action nudges told the LLM to call a tool, but did not include the
   current `get_continuation_prompt()` output. Combined with same-task/status
   prompt deduplication, the next prompt could lack the exact
   `todo_update(index=N, status='...')` instruction even though the TODO was
   still open.

## Prevention Policy

### 1. Every Tool Error Must Have An Executed Recovery Test

If a tool returns an instruction such as:

```text
Call read_file/run_command/write_file, then retry todo_update(completed).
```

then a regression test must execute exactly that sequence. It is not enough to
test the happy path.

Required matrix for `todo_update(completed)`:

| Sequence | Expected |
|---|---|
| `in_progress -> no tool -> completed` | blocked, state unchanged |
| `in_progress -> run/read/write -> completed` | completed |
| `pending -> completed blocked -> run/read/write -> completed` | completed |
| `pending -> completed blocked -> rejected(reason=tracker bookkeeping)` | rejection blocked, state unchanged |

### 2. Prompt Generation And Prompt Delivery Are Separate Gates

Testing `TodoTracker.get_continuation_prompt()` only proves that text can be
generated. It does not prove the LLM saw it.

Every TODO state that depends on continuation must have both tests:

| Layer | What it proves |
|---|---|
| `get_continuation_prompt()` unit test | the right prompt text exists |
| `react_loop` LLM-input test | the prompt is present in the actual messages passed to the next LLM call |

Required states:

- `pending`: start prompt with `todo_update(..., in_progress)`.
- `in_progress`: completion prompt with `todo_update(..., completed)`.
- `completed`: review prompt with approve/reject instructions.
- `rejected`: repair prompt with rejection reason and restart instruction.
- blocked `todo_update`: recovery prompt with active task context.
- no-action retry while TODO is open: runtime guard plus the active
  continuation prompt in the same LLM input.

### 3. UI/Worker Parity Is A Product Gate

If Textual and Atlas/web call the same conceptual workflow, they must share the
same behavioral tests at the react-loop level. A UI rendering test is not enough.

Required parity checks:

- Atlas/web chat mode must not stop before continuation prompts for open TODOs.
- Plan/normal mode confirmation must be applied in the worker process, not only
  in the web process.
- Atlas/web TODO status edits must use the same transition engine as
  `core.tools.todo_update`; direct `todo.status = ...` writes are not allowed
  for workflow statuses.
- Sidebar rendering (`blocked`, `rejected`, `completed`) must match the actual
  todo state transition and must not substitute for prompt injection.

### 4. Tracker Bookkeeping Is Not A Rejection Reason

`rejected` means "the task deliverable failed a criterion". It must not mean
"the todo engine got confused".

Rules:

- If the reason contains a tracker/bookkeeping blocker (`Completion blocked`,
  `no tools were called`, `TodoTracker`, `todo engine refuses completion`) and
  the task is not in review (`completed`), block the rejection.
- Preserve the task state.
- Surface the valid recovery transition, normally
  `todo_update(index=N, status='completed')`.

## Required Verification Commands

When changing TODO loop, prompt injection, plan mode, or worker loop behavior,
run:

```bash
python3 -m pytest \
  tests/test_todo_tracking.py \
  tests/test_core/test_react_loop.py \
  tests/test_display_todo_update.py \
  tests/test_todo_workflow.py \
  tests/test_atlas_plan_mode_propagation.py -q
```

For Atlas UI changes, also run from `frontend/atlas`:

```bash
npx tsc --noEmit
npm test -- --run \
  __tests__/workspace-feed-step-update.test.tsx \
  __tests__/workspace-render-smoke.test.tsx \
  __tests__/use-sticky-chat-scroll.test.tsx
npm run build
```

Then run the real server/browser smoke:

```bash
SKIP_VITEST=1 ATLAS_E2E_PORT=3028 PYTHON=python3 \
  scripts/atlas_vite_e2e_verify.sh
```

For prompt-delivery regressions, add a cheap real-LLM smoke with a unique marker
when credentials are available. The point is not model quality; it proves the
injected marker reached the model input path.

## Regression Tests Added

- `tests/test_todo_tracking.py`
  - `test_gate_check_consumes_pending_tool_credit_after_blocked_completion`
  - `test_rejecting_tracker_bookkeeping_blocker_is_blocked_not_recorded`
- `tests/test_core/test_react_loop.py`
  - `test_chat_mode_does_not_stop_before_blocked_todo_recovery_prompt`
  - `test_chat_mode_injects_rejected_todo_prompt_before_stopping`
  - `test_no_action_guard_reinjects_exact_todo_transition`
- `tests/test_atlas_multiuser_session_scope.py`
  - `test_todos_update_uses_shared_status_transition_gates`

## Design Rule

Do not verify only the state object, only the prompt text, or only the UI card.
For workflow-control changes, verify all three:

```text
state transition -> prompt delivery to LLM input -> user-visible UI/worker path
```

If any one layer is missing, the system can be green while still broken.

## Related

- [[testing-methodology]]
- [[golden-todo-evidence]]
- [[atlas-plan-mode-process-boundary-20260604]]
- [[pipeline-progress-debugging]]
- [[atlas-vite-e2e-verification]]
