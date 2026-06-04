# Atlas Plan Mode Across The Process Boundary

Date: 2026-06-04 — **IMPLEMENTED 2026-06-04**

This page documents why plan mode (the read-only "make a TODO plan, wait for the
user to approve before executing" mode) silently failed in the Atlas web UI
while working correctly in the Textual TUI, and the fix that propagates plan
state across the web-server → session-worker process boundary.

## Symptom

In the Atlas web UI, turning on plan mode and submitting a task produced todos
that immediately went to `in_progress` and executed — no approval gate. The
Textual TUI (`textual main`) gated correctly: todos stayed `pending` until the
user confirmed.

## Root cause: plan mode never crossed the process boundary

Plan mode has two pieces of state that must agree **in the same process as the
agent's react loop**:

```text
agent_mode (local var in src/main.py chat_loop)  -> system prompt / toolset
os.environ["PLAN_MODE"]                           -> the gate (core/tools.py:3672)
```

- **Textual / CLI = one process.** `/plan` runs `src/main.py:2270`, which sets
  *both* `agent_mode="plan_q"` and `os.environ["PLAN_MODE"]="true"` in the very
  process where `chat_loop` and `tools.py` run. Gate engages.
- **Atlas = two processes.** The agent runs in a separate
  `core.session_worker` subprocess (`core/session_process_manager.py`, Popen'd
  with a frozen env snapshot). The plan toggle is handled in the **web-server**
  process (`src/atlas_ui.py`: the `AGENT_MODE:` handler ~4985 and
  `PLAN_AND_RUN` ~5042), which sets `os.environ["PLAN_MODE"]`/`_plan_mode_cv`
  **there** and updates the UI pill — but:
  - the `AGENT_MODE:` (pill) handler `return`s without forwarding anything to
    the worker (the dedicated forward block at ~10615 is dead code — the generic
    slash handler at ~10612 consumes `/plan` first);
  - `submit_prompt_for_session` → `_send_process_input_for_session(..., "prompt",
    {"text": text})` carried only the text; the worker's `input()` returned only
    `_message_text(msg)`.

So the worker's agent always ran in **normal** mode: full toolset + ungated
`todo_update`. The web process's `PLAN_MODE="true"` was invisible to it.

## The fix (per-turn envelope)

Carry plan mode *with each prompt* into the worker and apply it per turn. One
consistent env-based source of truth that `tools.py` already reads.

1. **Stamp the envelope** — `core/atlas_multiuser.py
   _send_process_input_for_session`: when plan mode is active
   (`PLAN_MODE=="true"` or `AGENT_MODE_OVERRIDE` in `plan`/`plan_q`), add
   `plan_mode`/`agent_mode` to the `prompt` payload. Normal prompts carry **no**
   key (byte-identical envelope, no bloat).
2. **Apply in the worker** — `core/session_worker.py SessionWorker.input()`: for
   a `prompt`, set this process's `os.environ["PLAN_MODE"]` /
   `AGENT_MODE_OVERRIDE` from the payload. A **key-absent prompt resets to
   normal**, which also clears a worker left in plan by a prior unconfirmed plan
   turn. `interrupt` messages are left untouched (they inject text mid-turn and
   must not flip the running turn's mode).
3. **Reconcile in main.py** — `src/main.py chat_loop()`: after reading
   `user_input`, reconcile the local `agent_mode` from `AGENT_MODE_OVERRIDE`
   (rebuild the system prompt on change). **Coarse plan↔normal only** — the
   `plan_q→plan→normal` progression is owned by `process_chat_turn`
   (`core/chat_loop.py`), so an in-flight plan is never downgraded to `plan_q`.
   No-op under Textual/CLI, where `AGENT_MODE_OVERRIDE` is unset.
4. **Gate the UI bypass** — `src/atlas_ui.py` `/api/todos/update`: reject
   (HTTP 409) a UI status transition while `PLAN_MODE=="true"`, mirroring the
   agent-tool gate at `core/tools.py:3672`. Content/detail/criteria/priority
   edits still allowed; no-op (same-status) writes pass through.

## Known edges (follow-ups, not regressions)

- **Confirm stickiness.** After `y` confirms a plan, `process_chat_turn` flips
  the *worker* to normal, but the *web* process keeps `AGENT_MODE_OVERRIDE`=
  `plan_q` (no worker→web sync-back). The next prompt re-enters plan until the
  user clicks NORMAL. This is fail-safe (it over-gates). A cheap mitigation is a
  worker→web `mode_change` sync-back that resets the contextvar on confirm.
- **Multi-user global env.** The envelope is stamped from process-global
  `os.environ` in the web server, correct for the **single-active session
  policy** (see [[atlas-single-active-orchestrator-subworkers-20260603]]). True
  per-session isolation would stamp from the per-connection plan contextvar.

The gate direction is always safe: every edge over-gates (waits for approval),
never under-gates.

## Tests

- `tests/test_atlas_plan_mode_propagation.py` — envelope carries plan only when
  active / stays minimal when normal; worker `input()` applies + resets the env;
  the resulting env is exactly what `core/tools.py:3672` checks.
- `tests/test_atlas_todo_tab.py` — `/api/todos/update` plan-mode gate presence.

## Related

- [[atlas-single-active-orchestrator-subworkers-20260603]]
- [[multi-user-worker-isolation]]
- [[orchestrator-worker-handoff]]
