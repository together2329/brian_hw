# Atlas refactoring review - single-worker readiness (2026-05-28)

Review note for the Atlas UI/session refactor around single-worker keepalive,
workflow switching, and startup latency.

## Scope reviewed

- `core/atlas_multiuser.py`
- `src/atlas_api_sessions.py`
- `src/atlas_ui.py`
- `frontend/atlas/app.jsx`
- `frontend/atlas/workspace.jsx`
- `tests/test_multiuser_bridge.py`
- `tests/test_atlas_websocket_disconnect.py`
- `tests/test_atlas_multiuser_session_scope.py`
- `tests/test_atlas_pipeline_flow_theme.py`

The reviewed refactor removes eager worker spawn from WebSocket/session bind,
moves session worker warmup behind `/api/session/activate`, and caches static
frontend vendor assets.

## Verdict

Request changes before treating the refactor as product-ready.

The backend direction is sound: session bind is cheaper, activation schedules
the single-worker warmup asynchronously, and the process manager still owns the
actual spawn lock. The remaining risk is frontend readiness semantics: the UI
can dismiss the workflow-switch loading state before the session worker is
actually alive.

## Finding 1 - high - UI can accept input before the session worker is hot

Backend activation can return:

```json
{
  "session_worker_warmup": {
    "enabled": true,
    "status": "scheduled",
    "alive": false,
    "background": true
  }
}
```

That means the worker warmup has only been queued. It is not proof that the
single-worker process is ready to receive the next chat input.

Current frontend behavior in `frontend/atlas/workspace.jsx` still finishes the
workflow-ready overlay for this state:

```jsx
finishWorkflowReady(readySeq, {
  message: warm && warm.alive === true
    ? 'Session worker hot; ready to receive input'
    : 'Workflow session ready',
});
```

Risk:

- User switches workflow.
- `/api/session/activate` returns quickly with warmup `scheduled`.
- UI says ready and releases input.
- First chat input races the still-starting worker.
- Visible symptom: first input feels slow, appears ignored, or needs to be sent
  again.

Required fix:

- Do not call `finishWorkflowReady` while
  `warm.status === "scheduled" && warm.alive === false`.
- Keep input held until real worker-alive evidence arrives, or until a bounded
  timeout expires with explicit "still warming" status.
- Acceptable evidence sources include an `agent_state`/worker-alive event, a
  worker status poll, or an activation response that reports `alive: true`.

Minimum frontend regression test:

- Mock `/api/session/activate` to return `session_worker_warmup.status =
  "scheduled"` and `alive = false`.
- Assert the workflow-ready gate remains active.
- Assert submit is held instead of sending immediately.

## Finding 2 - medium - warmup scheduling has no per-session in-flight guard

`src/atlas_api_sessions.py` starts a daemon warmup thread whenever the target
session is not already alive.

The process manager lock should prevent duplicate real worker processes, but
rapid repeated activation can still enqueue redundant warmup threads for the
same session before the first one marks the process alive.

Risk:

- Rapid workflow/IP switching creates repeated activation calls.
- Each activation can schedule another warmup thread.
- Threads converge on the process-manager lock, but still add avoidable startup
  pressure and noisy state transitions.

Required fix:

- Add a process-local `warmup_in_flight` set or dict keyed by session id.
- Protect it with a lock.
- If a warmup is already in flight, return a scheduled/in-flight status without
  starting another thread.
- Clear the in-flight marker in a `finally` block after warmup succeeds or
  fails.

Suggested response shape:

```json
{
  "enabled": true,
  "status": "scheduled",
  "alive": false,
  "background": true,
  "in_flight": true
}
```

## What looked good

- Removing eager spawn from `bind_client` is the right latency move for WebSocket
  reconnects and session switches.
- Keeping warmup behind `/api/session/activate` matches the product model: a
  selected user/IP/workflow session should get hot, not every bound session.
- Static vendor asset caching is reasonable because the vendor script URLs carry
  explicit version query strings.
- Existing backend tests cover the main contract that activation returns quickly
  while background warmup still happens.

## Test gaps

Current tests prove pieces of the backend behavior, but not the user-visible
race:

- Covered: activation can schedule warmup in the background.
- Covered: binding a client does not eagerly spawn a worker.
- Covered: WebSocket disconnect noise is classified more quietly.
- Missing: frontend keeps workflow switching/loading state active while
  `session_worker_warmup` is only `scheduled`.
- Missing: repeated activation does not enqueue unbounded duplicate warmup
  threads for the same session.

## Product rule captured

Workflow switching should not say "ready" merely because routing and session
metadata are updated. In single-worker mode, "ready" means the selected
user/IP/workflow session has an alive worker or the UI is explicitly telling the
user that a bounded warmup is still in progress.
