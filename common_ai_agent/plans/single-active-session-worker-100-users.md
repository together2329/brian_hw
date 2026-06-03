# Single Active Session Worker 100-User Plan

Date: 2026-06-03

## Summary

Implement a strict **single active interactive session worker per owner slot**
policy for ATLAS while keeping orchestrator workflow/job workers as a separate
lane.

This plan does not implement `rtl-gen` subworker fanout. It first makes the
interactive worker lifecycle deterministic, visible, and capacity-bounded so
later multi-worker RTL generation has a stable control plane.

## Key Decisions

- `src/atlas_ui.py` remains the Atlas UI/control plane. It is not the session
  worker.
- Interactive session workers are alive `core.session_worker` OS subprocesses
  managed by `core/session_process_manager.py`.
- "Single active" means **one alive interactive session-worker process per
  owner slot**, not one running prompt while several warm idle processes remain.
- The owner slot key is the normalized owner used in the session namespace after
  `_session_owner_with_model()`. This is intentionally an **owner slot**, not
  always the raw authenticated username: when `ATLAS_SESSION_PER_MODEL=1`, one
  login can have separate model-scoped owner slots such as `alice__gpt_5`.
- Status/API responses that mention ownership must distinguish
  `authenticated_owner` from `owner_slot` whenever both are known.
- Persisted session identity remains `<owner>/<ip>/<workflow>` for history,
  DB rows, artifacts, and UI routing.
- Workflow/IP switch in strict mode must terminate the previous owner-slot
  worker before warming or spawning the new context worker. No handoff overlap.
- `preserve_running=true` is allowed only for orchestrator workflow/job focus
  changes. It must not keep an extra interactive session worker alive in strict
  single-active mode.
- `ATLAS_SESSION_WORKER_KEEPALIVE` in strict mode means "keep the current owner
  slot worker warm"; it must never keep sibling workflow workers alive.
- Backpressure is visible and non-lossy: prompt delivery that cannot spawn a
  worker must emit `agent_accepted{ok:false,error:"capacity_wait"}` and must not
  emit `agent_received`, so the existing frontend retry/hold path remains armed.
- 100-user readiness target for this plan is **100 registered/logged-in session
  namespaces with bounded active worker concurrency**. Claiming 100 simultaneous
  high-output workers depends on the runtime DB/queue work in
  `plans/atlas-runtime-db-100-users.md`.

## Existing Anchors

- `src/atlas_ui.py:1108` creates the FastAPI control plane.
- `src/atlas_ui.py:1132` reads `ATLAS_SINGLE_WORKER_PER_OWNER` /
  `ATLAS_SINGLE_WORKER_PER_USER`; default is false at `src/atlas_ui.py:1145`.
- `src/atlas_ui.py:1167` instantiates `_MultiUserBridge`.
- `src/atlas_ui.py:1312` runs the single broadcaster loop over bridge events.
- `src/atlas_ui.py:1746` stop calls `bridge.request_stop_for_session`.
- `src/atlas_ui.py:1764` shutdown calls `bridge.exit_session`.
- `src/atlas_api_sessions.py:74` enables keepalive by default in
  `single-worker` exec mode.
- `src/atlas_api_sessions.py:276` handles triple-change stop/keepalive logic.
- `src/atlas_api_sessions.py:508` schedules session worker warmup.
- `src/atlas_api_sessions.py:1207` has the session-id activate endpoint.
- `core/atlas_multiuser.py:326` defines `_MultiUserBridge`.
- `core/atlas_multiuser.py:621` currently kills owner siblings only when
  `_single_worker_per_owner` is true and only at spawn time.
- `core/atlas_multiuser.py:725` activates sessions without necessarily warming.
- `core/atlas_multiuser.py:907` sends process input and handles prompt-delivery
  failure.
- `core/atlas_multiuser.py:1012` sends stop input; `core/atlas_multiuser.py:1018`
  exits/kills a session.
- `core/session_process_manager.py:452` spawns `python -m core.session_worker`.
- `core/session_process_manager.py:503` kills a tracked worker process.
- `core/session_process_manager.py:553` lists alive session worker processes.
- `src/atlas_api_jobs.py:119` has orchestrator IPC worker limits; these do not
  cap interactive session workers.
- `src/atlas_api_jobs.py:6213` dispatches orchestrator workflow jobs.
- `frontend/atlas/agent-worker-status.tsx` shows worker status, currently mixing
  interactive agent state and workflow worker summaries.
- `doc/wiki/atlas-single-active-orchestrator-subworkers-20260603.md` captures
  the design discussion and future `rtl-gen` subworker direction.

## Scope

### In Scope

- Interactive session-worker lifecycle policy.
- Owner-level active slot enforcement.
- Stop/exit/kill ordering on workflow/IP switch.
- Idle TTL reaping for warm interactive workers.
- Global active-worker admission cap.
- Visible capacity/backpressure state.
- New/updated UI/API state for interactive session workers.
- Regression tests for prompt ack semantics, owner isolation, switch races,
  TTL, and capacity.
- Orchestrator worker chat/log visibility verification.

### Out Of Scope

- Implementing multi-lane `rtl-gen` subworkers.
- Changing orchestrator IPC worker scheduling semantics.
- Redis/Postgres/NATS migration.
- Reworking the existing runtime DB router plan.
- Git commit creation. Only commit if explicitly requested later.

## Environment Contract

Add a first-class interactive session-worker policy. Do not make implementers
infer behavior from scattered flags.

```text
ATLAS_SESSION_WORKER_POLICY=session-scoped|single-active-owner
ATLAS_SESSION_WORKER_MAX_ACTIVE=30
ATLAS_SESSION_WORKER_IDLE_TTL_SEC=900
ATLAS_SESSION_WORKER_REAPER_INTERVAL_SEC=15
ATLAS_SESSION_WORKER_STOP_ACK_SEC=3
ATLAS_SESSION_WORKER_KILL_GRACE_SEC=5
ATLAS_SESSION_WORKER_ENABLE_REAPER=1
```

Compatibility rules:

- If `ATLAS_SESSION_WORKER_POLICY` is unset, keep current behavior:
  `session-scoped`.
- If legacy `ATLAS_SINGLE_WORKER_PER_OWNER=1` or
  `ATLAS_SINGLE_WORKER_PER_USER=1` is set and the new policy is unset, treat it
  as `single-active-owner`.
- To preserve current behavior, the global admission cap is enforced only when
  either `ATLAS_SESSION_WORKER_POLICY=single-active-owner` is active or
  `ATLAS_SESSION_WORKER_MAX_ACTIVE` is explicitly set by the operator. In
  default `session-scoped` mode with no new env vars, capacity is unbounded.
- In strict `single-active-owner`, ignore sibling-preserving keepalive. The only
  warm process allowed for an owner is the current owner slot.
- Rollback is setting `ATLAS_SESSION_WORKER_POLICY=session-scoped`.

## Corrected Implementation Contracts

These contracts close review gaps that must be resolved before implementation.

### Result Objects

Do not add a rich `SpawnResult` only to collapse it back to `bool`.

- `SessionProcessManager.spawn_result(...) -> SpawnResult` is the admission
  source of truth.
- `spawn(...) -> bool` remains only for old tests/callers.
- New bridge/API paths must pass structured results through:
  `_spawn_process_session`, `warm_session`, `_send_process_input_for_session`,
  `submit_prompt_for_session`, and the websocket prompt ack path.
- Add a `PromptDeliveryResult` or equivalent with:
  `ok`, `status`, `reason`, `session_id`, `owner_slot`, `msg_id`,
  `spawn_result`, and `error`.
- `capacity_wait` must survive all the way to
  `agent_accepted{ok:false,error:"capacity_wait"}` with no `agent_received`.

### Capacity And Activation Semantics

- Capacity admission is evaluated only for a **new** interactive subprocess
  after dead entries are cleaned up.
- If the target session already has a live tracked process, it is ready and does
  not consume an additional slot.
- In strict mode, activation may succeed as a focus change even when warmup is
  capacity-blocked. The response must show:
  `switch_status:"active_no_worker"` and
  `session_worker_warmup.status:"capacity_wait"`.
- A capacity-blocked activation updates `owner_active_session` to the new
  canonical session only after any old owner-slot worker has been terminated or
  explicitly reported as termination-failed.
- A capacity-blocked prompt returns delivery failure and leaves the frontend
  retry/hold path armed.

### Queue Marker Semantics

Current inbound queue polling uses `poll_messages(..., direction="in")`, which
filters on `delivered_at IS NULL`. Therefore stale input cleanup cannot only set
`processed_at`.

- Stale inbound `prompt`, `stop`, `interrupt`, and `answer` rows must be hidden
  from `core.session_worker` by setting `delivered_at`.
- Also set `processed_at` when practical for diagnostics, but `delivered_at` is
  the required marker for the current poll path.
- If the implementation later switches inbound reads to `dequeue_message()`,
  update this contract and tests in the same change.

### Graceful Stop Semantics

`ATLAS_SESSION_WORKER_STOP_ACK_SEC` means: wait for the process to exit or emit
`worker_stopped`/`worker_exited` after a `stop` input is enqueued. Merely
observing a queue row's marker is not sufficient.

- `terminate_session()` may include `worker_epoch` in stop payloads when an
  epoch exists.
- It must not require epoch support until the epoch task has landed.
- If graceful stop does not complete in time, proceed to `terminate()` then
  `kill()` within the configured grace.

### Locking And Switch Semantics

- Use a per-owner-slot lock to serialize activation, warmup, and prompt spawn for
  the same owner slot.
- Do not hold `_sessions_lock` while waiting on process termination.
- Do not hold a broad global bridge lock while sleeping for stop/kill grace.
- Unrelated owner slots must be able to make progress while one owner slot is
  terminating.
- If old worker termination fails, do not silently spawn a sibling. Return
  `switch_status:"termination_failed"` and surface a visible error/status event.

### Status Endpoint Scope

The first implementation of `GET /api/session/worker/status` is user-scoped.
It must not expose other users' session IDs. An admin all-owner view is optional
only if `register_sessions_routes()` is explicitly passed an admin-check
callback or an existing admin-auth route owns that response.

## Work Plan

### Task 1: Add Failing Contract Tests First

**What to do**

- Add `tests/test_session_worker_policy.py` for env parsing and policy defaults.
- Add or extend tests in `tests/test_process_based_sessions.py` for owner-slot
  behavior.
- Add or extend tests in `tests/test_atlas_multiuser_session_scope.py` for
  `/api/session/activate` behavior in strict mode.
- Add tests in `tests/test_atlas_worker_warmup_input.py` proving capacity wait
  emits no `agent_received`.
- Add frontend expectations in `frontend/atlas/__tests__/agent-worker-status.test.tsx`
  for separate interactive worker status text.

**Required RED cases**

- With `ATLAS_SESSION_WORKER_POLICY=single-active-owner`, activating
  `alice/ip_a/rtl-gen` after `alice/ip_a/ssot-gen` leaves at most one alive
  process for owner `alice`.
- `bob/ip_a/rtl-gen` is not killed when Alice switches workflow.
- `preserve_running=true` does not preserve Alice's previous interactive worker
  in strict mode.
- Capacity refusal produces `agent_accepted ok=false error=capacity_wait` and no
  `agent_received`.

**Acceptance criteria**

- The new tests fail on current behavior for the exact reasons above.
- Existing tests are not rewritten to hide current behavior before the policy is
  implemented.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_session_worker_policy.py \
  tests/test_process_based_sessions.py \
  tests/test_atlas_multiuser_session_scope.py \
  tests/test_atlas_worker_warmup_input.py

cd frontend/atlas && npm test -- \
  __tests__/agent-worker-status.test.tsx
```

### Task 2: Introduce `SessionWorkerPolicy`

**What to do**

- Create `core/session_worker_policy.py`.
- Define a typed/dataclass policy with these fields:
  `policy`, `single_active_owner`, `max_active`, `idle_ttl_sec`,
  `reaper_interval_sec`, `stop_ack_sec`, `kill_grace_sec`, and
  `reaper_enabled`.
- Add `SessionWorkerPolicy.from_env(os.environ)` with the exact env contract
  above.
- Preserve legacy flags as compatibility aliases only when
  `ATLAS_SESSION_WORKER_POLICY` is unset.
- Treat `max_active <= 0` as unbounded. In default `session-scoped` mode with no
  explicit `ATLAS_SESSION_WORKER_MAX_ACTIVE`, preserve current unbounded spawn
  behavior.
- In `src/atlas_ui.py`, build this policy once during `create_app()` and pass it
  into `_MultiUserBridge`.
- Keep the old `single_worker_per_owner` constructor argument for tests and
  backwards compatibility, but internally convert it into a policy.

**Must not do**

- Do not change source behavior yet except env parsing and bridge wiring.
- Do not make policy defaults depend on frontend state.

**Acceptance criteria**

- `SessionWorkerPolicy.from_env({})` returns `session-scoped`.
- `ATLAS_SESSION_WORKER_POLICY=single-active-owner` enables strict mode.
- `ATLAS_SESSION_WORKER_MAX_ACTIVE` is parsed, but default session-scoped mode
  remains unbounded when the env var is absent.
- `ATLAS_SINGLE_WORKER_PER_OWNER=1` enables strict mode only when the new policy
  is absent.
- Invalid policy values fail closed to `session-scoped` and expose a warning
  string in the policy object for diagnostics.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_session_worker_policy.py \
  tests/test_process_based_sessions.py::test_single_worker_per_owner_kills_previous_owner_worker
```

### Task 3: Enforce Owner Slot Before Activation, Warmup, And Prompt Spawn

**What to do**

- In `core/atlas_multiuser.py`, add an owner-slot lock:
  `self._owner_slot_lock = threading.RLock()`.
- Add helper methods:
  `owner_slot_key(session_id)`, `owner_active_session(owner)`,
  `_prepare_owner_slot_for_session(session_id, reason)`, and
  `_clear_owner_slot(session_id)`.
- `_prepare_owner_slot_for_session` must run before:
  `activate_session`, `warm_session`, and `_send_process_input_for_session`
  when `spawn=True`.
- In strict mode, if the current owner slot points to another session:
  1. emit `worker_switching` on the old and new sessions,
  2. terminate the old process through the process manager,
  3. mark old session `agent_running=False`, `agent_alive=False`,
  4. emit `agent_state`, `worker_exited`, and `done` for the old session,
  5. remove old output cursor,
  6. update `_owner_active_sessions[owner] = new_session_id`,
  7. only then allow new warmup/spawn.
- If process mode is disabled, keep current thread-mode behavior but still
  update owner active mapping.
- Add `_clear_owner_slot(session_id)` calls for `exit_session`,
  `delete_session`, process death, and idle reaper eviction.
- Return or store a structured switch result so API responses can expose
  `switch_status`, `previous_session`, and `terminated_session` without parsing
  emitted events.

**Must not do**

- Do not kill sessions belonging to another owner.
- Do not allow `preserve_running` to bypass this method in strict mode.
- Do not call `manager.kill()` while holding `_sessions_lock`; acquire locks in
  a consistent order, and do not sleep while holding `_sessions_lock` or a broad
  global bridge lock. Per-owner-slot waiting is allowed; unrelated owners must
  keep progressing.
- Do not spawn the new session if old owner-slot termination fails.

**Acceptance criteria**

- Switching Alice from `ssot-gen` to `rtl-gen` leaves no alive Alice sibling
  process before `rtl-gen` spawn returns.
- Switching Alice does not alter Bob's process.
- Repeated activation of the same canonical session is idempotent.
- Warmup cannot spawn a sibling after activation already switched the owner slot.
- Exit/delete/process-death clears the owner slot only if it still points at the
  exited/deleted session.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_process_based_sessions.py \
  tests/test_multiuser_bridge.py
```

### Task 4: Add Process Metadata, Graceful Termination, And Admission Results

**What to do**

- In `core/session_process_manager.py`, replace bare process-entry dict usage
  with a small typed entry shape containing:
  `proc`, `session_id`, `owner`, `started_at`, `last_active_at`,
  `last_input_at`, `last_output_at`, `worker_epoch`, and `state`.
- Add a `SpawnResult` dataclass with:
  `ok`, `status`, `reason`, `session_id`, `owner`, `pid`, `active_count`,
  `max_active`.
- Add `spawn_result(session_id, db_path=None, policy=None) -> SpawnResult`.
- Keep existing `spawn()` as a compatibility wrapper returning
  `spawn_result(...).ok`.
- Before spawning, enforce global cap:
  if `active_count >= policy.max_active`, return
  `SpawnResult(ok=False,status="capacity_wait",reason="max_active")`.
- Add `terminate_session(session_id, reason, stop_timeout_sec,
  kill_grace_sec) -> bool`.
- `terminate_session` must:
  1. try graceful stop by enqueuing a `stop` for the tracked worker; include
     `worker_epoch` only if epoch support already exists,
  2. wait up to `stop_timeout_sec`,
  3. call `proc.terminate()`,
  4. wait up to `kill_grace_sec`,
  5. call `proc.kill()` if needed,
  6. evict DB handles,
  7. remove the process entry.
- Existing `kill(session_id)` should delegate to `terminate_session` with
  hard-stop defaults so old callers keep working.

**Must not do**

- Do not block process-manager lock while sleeping if that blocks unrelated
  owner sessions from making progress.
- Do not count orchestrator workflow/job workers toward this cap.

**Acceptance criteria**

- `list_active()` still returns only alive interactive session IDs.
- `list_active_metadata()` returns owner/session/status data for the new status
  endpoint.
- Capacity refusal does not spawn a process and does not enqueue a prompt.
- New bridge/API code uses `spawn_result`; the old `spawn()` bool wrapper is not
  used where `capacity_wait` must be surfaced.
- Existing process-based session tests continue to pass.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_process_based_sessions.py \
  tests/test_process_based_sessions_runtime.py \
  tests/test_lazy_worker_idle_ttl.py \
  tests/test_lazy_worker_reaper.py
```

### Task 5: Add Worker Epochs And Stale Input Hygiene

**What to do**

- Generate a new `worker_epoch` on every successful interactive session-worker
  spawn.
- Pass the epoch to the worker through env
  `ATLAS_SESSION_WORKER_EPOCH=<epoch>`.
- In `SessionProcessManager.send_input`, inject `worker_epoch` into the JSON
  payload for `prompt`, `interrupt`, `answer`, and `stop` when strict mode is on.
- In `core/session_worker.py`, before acting on an inbound message, compare
  `payload.worker_epoch` with `ATLAS_SESSION_WORKER_EPOCH`.
- If the payload epoch is present and does not match, acknowledge/mark the row
  delivered and emit/log `stale_input_ignored`; do not execute it.
- Add an `AtlasDB` helper for scoped cleanup:
  `mark_stale_session_inputs_delivered(session_id, before_epoch=None,
  msg_types=None)`, optionally also setting `processed_at` for diagnostics.
- On owner-slot switch, mark pending old-epoch `stop`, `interrupt`, and
  `answer` rows delivered for the old session.

**Must not do**

- Do not delete output rows during switch.
- Do not drop current-epoch prompts.
- Do not require schema changes to `session_queue`; epoch lives in payload JSON.
- Do not rely on `processed_at` alone for stale inbound rows while
  `SessionWorker` uses `poll_messages()` for input.

**Acceptance criteria**

- A stale `stop` from an old process cannot stop the newly spawned worker for
  the same canonical session.
- A stale prompt from an older epoch is acknowledged as stale and is not run.
- Stale inbound rows are no longer returned by the current
  `poll_messages(..., direction="in")` path because `delivered_at` is set.
- Current prompt ack behavior from `tests/test_atlas_worker_warmup_input.py`
  remains intact.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_session_worker_ssot_qa.py \
  tests/test_atlas_worker_warmup_input.py \
  tests/test_runtime_queue_hardening.py
```

### Task 6: Update Session Activation APIs For Strict Single-Active Mode

**What to do**

- In `src/atlas_api_sessions.py`, route both `/api/session/activate` and
  `/api/sessions/{session_id}/activate` through the same strict switch helper.
- When strict mode is on and `prev != canonical`, force
  `preserve_running=False` for the interactive session-worker lane.
- Keep `preserve_running` in the response, but add:
  `preserve_running_effective`, `session_worker_policy`,
  `single_active_owner`, `previous_session`, `terminated_session`, and
  `switch_status`.
- `_schedule_session_worker_warmup` must return `capacity_wait` details when
  the process manager refuses a spawn because of `max_active`.
- If activation succeeds but warmup is capacity-blocked, return HTTP 200 with
  `session_worker_warmup.status="capacity_wait"`; do not pretend the worker is
  ready.
- In strict mode, make the admission part of session-worker warmup synchronous
  enough to return `ready`, `started`, or `capacity_wait`; do not hide admission
  failure inside the background warmup thread.
- If a prompt submission is capacity-blocked, return/emit delivery failure so
  `_prompt_ack_frames(ok=False,error="capacity_wait")` is used.

**Must not do**

- Do not return `ready` unless `manager.is_alive(canonical)` is true.
- Do not let `/api/sessions/{session_id}/activate` bypass the same strict
  policy.

**Acceptance criteria**

- Activation response shows when an old session was terminated.
- Single-active switch is deterministic even when `preserve_running=true`.
- Response includes `preserve_running_effective=false` for the interactive
  session-worker lane when strict mode forced a termination.
- Frontend prompt retry remains armed on capacity wait because no
  `agent_received` is sent.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_atlas_multiuser_session_scope.py \
  tests/test_atlas_workflow_switch.py \
  tests/test_atlas_ws_prompt_ack_errors.py \
  tests/test_atlas_input_deep_runtime.py
```

### Task 7: Add Idle Reaper And Interactive Worker Status API

**What to do**

- Add `bridge.reap_idle_session_workers(now=None)` in `core/atlas_multiuser.py`.
- Call it from the broadcaster poll path in `src/atlas_ui.py` no more often
  than `ATLAS_SESSION_WORKER_REAPER_INTERVAL_SEC`.
- Reap only strict-mode interactive session workers where:
  `agent_running is False`, process is alive, and idle age is greater than
  `ATLAS_SESSION_WORKER_IDLE_TTL_SEC`.
- Add `GET /api/session/worker/status` in `src/atlas_api_sessions.py`.
- User-scoped response:

```json
{
  "policy": "single-active-owner",
  "single_active_owner": true,
  "max_active": 30,
  "active_count": 3,
  "owner": "alice",
  "owner_active_session": "alice/ip_a/rtl-gen",
  "worker": {
    "session_id": "alice/ip_a/rtl-gen",
    "alive": true,
    "running": false,
    "pid": 1234,
    "state": "ready",
    "idle_age_sec": 12.3
  }
}
```

- Admin/debug response may include all owner slots only for admin users or
  existing admin-auth paths.
- If no admin-auth callback is available inside `register_sessions_routes()`,
  ship only the user-scoped response in this task and defer all-owner inventory.

**Must not do**

- Do not expose other users' session IDs to normal users.
- Do not use `/api/orchestrator/workers` for interactive worker inventory.

**Acceptance criteria**

- Reaper kills idle warm worker after TTL and emits `worker_evicted`.
- Reaper does not kill a running prompt.
- User endpoint shows only the caller's owner slot.
- Endpoint returns both `authenticated_owner` and `owner_slot` when they differ.
- Orchestrator worker list remains unchanged.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_process_based_sessions.py \
  tests/test_atlas_multiuser_session_scope.py \
  tests/test_atlas_admin_auth.py
```

### Task 8: Separate Frontend Interactive Agent Status From Workflow Workers

**What to do**

- In `frontend/atlas/agent-status-panel.tsx`, fetch
  `/api/session/worker/status` alongside `/api/orchestrator/workers`.
- In `frontend/atlas/agent-worker-status.tsx`, render two distinct concepts:
  "agent" for interactive session worker, and "workflow workers" for
  orchestrator/job workers.
- Define a typed prop shape for interactive worker status instead of inferring
  agent liveness from `/api/orchestrator/workers`.
- Poll interactive worker status on the same cadence as the current worker
  status panel, pause while the tab is hidden, and keep orchestrator worker
  errors visually separate from agent status errors.
- Add visible states:
  `ready`, `starting`, `capacity_wait`, `switching`, `stopping`, `evicted`,
  `failed`.
- Keep existing `/api/orchestrator/workers` cards for workflow/job workers.
- Do not show `no active workflow workers` as if the interactive session worker
  is dead.

**Must not do**

- Do not collapse orchestrator job workers into the owner slot.
- Do not add decorative UI; keep the status compact and operational.

**Acceptance criteria**

- Single-worker mode with a live interactive process shows `agent ready`.
- Orchestrator mode with no workflow jobs shows `agent ready` and
  `no active workflow workers`.
- Capacity wait is visible and does not look like backend disconnect.
- Existing worker status tests still pass after expected text updates.

**QA command**

```bash
cd frontend/atlas && npm test -- \
  __tests__/agent-worker-status.test.tsx \
  __tests__/submitmsg-dispatch.test.tsx \
  __tests__/adversarial-bugfixes.test.tsx
```

### Task 9: Verify Orchestrator Worker Chat Visibility Without Adding Subworkers

**What to do**

- Keep orchestrator workflow/job worker scheduling unchanged.
- Add/extend tests proving orchestrator dispatch still creates job records and
  worker status rows after interactive single-active policy is enabled.
- Verify worker chat/log routes by specific `job_id` when available, and by
  `(ip, workflow)` only as a fallback.
- Before relying on `/api/job/{job_id}/log`, cite the existing route in the
  implementation notes or add it as part of this task if absent.
- In UI code that opens worker chat from orchestrator status, prefer explicit
  `job_id` from `/api/orchestrator/workers` or progress-debug data.
- If a job finishes quickly, worker chat must still be inspectable from
  `/api/job/{job_id}/log`.

**Must not do**

- Do not enable multiple `rtl-gen` child jobs in this task.
- Do not weaken existing active-job conflict logic.

**Acceptance criteria**

- Orchestrator chat prompt still POSTs `/api/pipeline/orchestrator/chat`.
- `dispatch_workflow` still creates workflow job workers.
- Worker chat/log view shows at least action/observation/response rows for the
  dispatched worker in tests or smoke.
- Interactive owner-slot enforcement does not kill orchestrator workflow job
  workers.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_orchestrator_workers_route.py \
  tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_multiuser_job_isolation.py \
  tests/test_jobs_rehydration.py \
  tests/test_orchestrator_route.py \
  tests/test_orchestrator_chat_messages.py

cd frontend/atlas && npm test -- \
  __tests__/submitmsg-dispatch.test.tsx \
  __tests__/agent-worker-status.test.tsx
```

### Task 10: Add 100-User Synthetic Capacity Harness

**What to do**

- Add a pytest-backed synthetic harness, preferably
  `tests/test_session_worker_capacity.py`.
- Use `FakeProcessManager` for deterministic 100-user logic without launching
  100 real Python workers.
- Scenario A:
  `ATLAS_SESSION_WORKER_POLICY=single-active-owner`,
  `ATLAS_SESSION_WORKER_MAX_ACTIVE=30`, 100 owners activate sessions.
- Scenario B:
  same owner switches 20 workflows rapidly; exactly one live process remains.
- Scenario C:
  100 owners with `ATLAS_SESSION_WORKER_MAX_ACTIVE=100` and fake processes;
  every owner has one slot and no routing crosses owners.
- Scenario D:
  capacity-blocked prompt emits delivery failure and no transport ack.
- Add a smaller real-process smoke with max active 3, not 100, to avoid CI
  import storms.
- Add at least one API-level smoke with distinct authenticated request scopes so
  the "100 registered/logged-in namespaces" claim is not proven only through a
  bridge-only fake manager.

**Must not do**

- Do not claim real 100 high-output workers from the fake harness.
- Do not make the test depend on external LLM calls.

**Acceptance criteria**

- Scenario A: `active_count <= 30`, 70 capacity-wait activations, zero wrong
  owner kills.
- Scenario B: final active session is the newest workflow; all previous owner
  sibling processes are killed.
- Scenario C: 100 fake owners map to 100 independent owner slots.
- Scenario D: no `agent_received` on capacity failure.
- Real smoke proves the manager enforces cap with actual subprocess handles.
- API smoke proves owner-slot isolation uses the same authenticated/user-scoped
  path that Atlas runs in production.

**QA command**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_session_worker_capacity.py \
  tests/test_process_based_sessions.py
```

### Task 11: Update Wiki And Runbook

**What to do**

- Update `doc/wiki/atlas-single-active-orchestrator-subworkers-20260603.md`
  with the final policy/env contract and the distinction between interactive
  owner slots and orchestrator job workers.
- Add a short runbook section:
  enable strict mode, inspect status, debug capacity wait, rollback to
  session-scoped.
- Update `doc/wiki/index.md` and `doc/wiki/log.md` only if this page is not
  already linked.

**Acceptance criteria**

- Wiki states that strict single-active mode is one alive interactive
  `core.session_worker` process per owner slot.
- Wiki states that `rtl-gen` subworkers are deferred until worker chat/log
  visibility and job-lane identity are stable.
- Rollback command is explicit:
  `ATLAS_SESSION_WORKER_POLICY=session-scoped`.

## Final Verification Wave

Run these after all tasks are complete:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
  tests/test_session_worker_policy.py \
  tests/test_session_worker_capacity.py \
  tests/test_process_based_sessions.py \
  tests/test_process_based_sessions_runtime.py \
  tests/test_atlas_multiuser_session_scope.py \
  tests/test_atlas_workflow_switch.py \
  tests/test_atlas_worker_warmup_input.py \
  tests/test_atlas_input_deep_runtime.py \
  tests/test_runtime_queue_hardening.py \
  tests/test_session_worker_ssot_qa.py \
  tests/test_orchestrator_workers_route.py \
  tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_multiuser_job_isolation.py \
  tests/test_jobs_rehydration.py \
  tests/test_orchestrator_route.py

cd frontend/atlas && npm test -- \
  __tests__/agent-worker-status.test.tsx \
  __tests__/submitmsg-dispatch.test.tsx \
  __tests__/adversarial-bugfixes.test.tsx
```

Manual/product-flow smoke, using the same UI/API/worker path the user runs:

```text
1. Start Atlas with ATLAS_SESSION_WORKER_POLICY=single-active-owner and max_active=3.
2. Log in as Alice; activate ip_a/ssot-gen; submit a prompt.
3. Switch Alice to ip_a/rtl-gen; confirm ssot-gen worker exits before rtl-gen is ready.
4. Log in as Bob; activate ip_a/rtl-gen; confirm Alice's switch never kills Bob.
5. Submit orchestrator chat that dispatches rtl-gen; open the worker chat/log view.
6. Confirm interactive agent status and workflow worker status are shown separately.
7. Set max_active=1; try Alice and Bob concurrently; confirm capacity_wait is visible
   and blocked prompt is not transport-acked as delivered.
```

## Rollback

- Runtime rollback:
  `ATLAS_SESSION_WORKER_POLICY=session-scoped`.
- Keep legacy:
  `ATLAS_SINGLE_WORKER_PER_OWNER=1` should continue to behave like strict mode
  only when the new policy env is absent.
- Do not remove current session-scoped behavior until the single-active policy
  has passed the final verification wave and product-flow smoke.

## Future RTL-GEN Subworker Follow-Up

After this plan is implemented and verified, create a separate plan for
multi-lane `rtl-gen`:

- add `parent_job_id`, `subworker_role`, `subtask_id`, and `worker_lane`,
- change conflict keys from `(ip, workflow)` to `(ip, workflow, lane)`,
- render parent coordinator job plus child worker logs,
- support child cancellation without killing the parent,
- require parent completion only after merge/review evidence exists.
