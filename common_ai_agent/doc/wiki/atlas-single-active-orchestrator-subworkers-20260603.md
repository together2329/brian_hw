# Atlas Single Active And Orchestrator Subworkers

Date: 2026-06-03 — **IMPLEMENTED 2026-06-03**

This page captures the design and implementation of ATLAS single-active session
workers, orchestrator-mode worker chat visibility, and the deferred `rtl-gen`
subworker model. The single-active semantics stabilize the interactive control
plane before multi-subworker orchestration is enabled.

## Current Worker Model (Implemented)

`src/atlas_ui.py` is the Atlas UI server/control plane. It is not the session
worker itself. In process-per-session mode, the session worker is a
`core.session_worker` subprocess launched through the multi-user bridge and
`core/session_process_manager.py`.

Current `single-worker` mode should not be read as "exactly one OS worker
process globally." The current default session namespace is effectively:

```text
<owner>/<ip>/<workflow>
```

That means `brian/uart/ssot-gen` and `brian/uart/rtl-gen` can be different
session workers. `ATLAS_SESSION_WORKER_KEEPALIVE` can keep prior workflow
workers warm instead of killing them. `ATLAS_SINGLE_WORKER_PER_OWNER` /
`ATLAS_SINGLE_WORKER_PER_USER` can force one live process per owner, but this is
not the default because killing sibling workflow sessions can route prompts or
queued browser events into the wrong context.

The user-intended "single worker" concept was stricter: start one worker and
switch its workflow by command. The shipped implementation is closer to
"single-worker execution policy with session-scoped workers."

## Implemented Single-Active Session Worker Contract

The interactive session-worker feature is **IMPLEMENTED as of 2026-06-03**. The
contract is parsed by `core/session_worker_policy.py` and enforced by
`core/session_process_manager.py` and the `core/atlas_multiuser._MultiUserBridge`.

### Policy / Environment Variables

- `ATLAS_SESSION_WORKER_POLICY` = `session-scoped` (default) | `single-active-owner`
  - Default (`session-scoped`): unbounded session-per-IP-per-workflow spawning (preserves
    historical behavior). No global cap is enforced unless `ATLAS_SESSION_WORKER_MAX_ACTIVE`
    is explicitly set.
  - `single-active-owner`: one alive interactive session worker per owner slot at a time.
    The owner slot is the normalized owner segment (e.g., with `ATLAS_SESSION_PER_MODEL=1`
    one login `alice` splits into model-scoped slots like `alice__gpt_5`). When a workflow
    switch occurs, the previous owner-slot worker is terminated before the new one is spawned.

- `ATLAS_SESSION_WORKER_MAX_ACTIVE` = 30 (default in strict mode) | N (explicit cap) | <=0 (unbounded)
  - In `single-active-owner` mode, defaults to 30 (global cap across all owner slots).
  - In `session-scoped` mode, the cap is OFF unless explicitly set (e.g., `ATLAS_SESSION_WORKER_MAX_ACTIVE=30`).
  - Values <= 0 mean unbounded (cap disabled).

- `ATLAS_SESSION_WORKER_IDLE_TTL_SEC` = 900 (15 minutes; idle timeout for reaper)
- `ATLAS_SESSION_WORKER_REAPER_INTERVAL_SEC` = 15 (reaper checks every 15 seconds)
- `ATLAS_SESSION_WORKER_STOP_ACK_SEC` = 3 (wait for graceful stop acknowledgment)
- `ATLAS_SESSION_WORKER_KILL_GRACE_SEC` = 5 (force-kill grace period)
- `ATLAS_SESSION_WORKER_ENABLE_REAPER` = 1 (default on; set to 0 to disable idle reaper)

- **Legacy compatibility**: `ATLAS_SINGLE_WORKER_PER_OWNER` / `ATLAS_SINGLE_WORKER_PER_USER` = 1
  still enable strict mode, but **only when** `ATLAS_SESSION_WORKER_POLICY` is unset.
  The new policy variable always takes precedence (the new var always wins).
  Invalid policy values fail closed to `session-scoped` with a warning.

### Key Semantics

**Single active:** exactly ONE alive `core.session_worker` OS process per OWNER SLOT
(not per raw username). Status/API responses distinguish `authenticated_owner` from
`owner_slot`.

**Interactive vs. orchestrator workers:** Interactive session workers (the agent,
`core.session_worker` subprocesses managed by `core/session_process_manager.py`)
are a SEPARATE lane from orchestrator workflow/job workers (`atlas_api_jobs`).
The owner-slot cap **NEVER counts or kills** orchestrator job workers.

**Workflow switch in strict mode:** terminates the previous owner-slot worker
BEFORE warming/spawning the new one (no handoff overlap). A same-owner-slot
REPLACEMENT reserves the freed slot and is never cap-refused.

**Capacity wait:** a prompt that cannot spawn a worker yields
`agent_accepted{ok:false,error:"capacity_wait"}` with NO `agent_received` (frontend
retry/hold stays armed). An activation that is capacity-blocked returns HTTP 200
with `switch_status="active_no_worker"` + `session_worker_warmup.status="capacity_wait"`.

**Stale-input hygiene:** each spawn gets a `worker_epoch` (env `ATLAS_SESSION_WORKER_EPOCH`);
the worker fences epoch-mismatched/stale inbound rows at startup and ignores them.
Cleanup sets BOTH `delivered_at` AND `processed_at` so the runtime-DB non-forced
delete gate stays clean.

**Idle reaper:** runs OFF the asyncio broadcaster (on the `next_event` executor thread),
throttled to `reaper_interval_sec`, evicts only idle (not running) alive strict-mode
workers past `idle_ttl_sec`, emits PRIVATE `worker_evicted` event, clears the owner slot.

**Status endpoint:** `GET /api/session/worker/status` is user-scoped (only the caller's
owner slot; never another owner's session ids). An all-owner `owners[]` view appears
only for admin (via `admin_check` callback wired in `create_app`).

## Runbook: Strict Mode Operations

### Enable Strict Mode

Set the environment variable before starting the ATLAS server:

```bash
export ATLAS_SESSION_WORKER_POLICY=single-active-owner
export ATLAS_SESSION_WORKER_MAX_ACTIVE=30  # optional; defaults to 30 in strict mode
python3 src/atlas_ui.py
```

To use legacy flags instead (if policy env is unset):

```bash
export ATLAS_SINGLE_WORKER_PER_OWNER=1
python3 src/atlas_ui.py
```

### Inspect Worker Status

```bash
# User-scoped view (authenticated user's owner slot only)
curl -s http://127.0.0.1:5601/api/session/worker/status | python3 -m json.tool

# Expected response (user-scoped):
{
  "policy": "single-active-owner",
  "single_active_owner": true,
  "cap_enabled": true,
  "max_active": 30,
  "authenticated_owner": "alice__gpt_5",
  "owner_slot": "alice__gpt_5",
  "session_id": "sess_abc123",
  "pid": 1234,
  "alive": true,
  "idle_seconds": 45,
  "warmup": {
    "status": "ready",
    "started_at": "2026-06-03T10:15:30Z"
  }
}
```

For admin view (all owners), pass admin credentials; the endpoint includes
`owners[]` with active slots and their status.

### Debug a Capacity Wait

When spawning a new owner-slot worker is refused with `status="capacity_wait"`:

1. **Check the cap:**
   ```bash
   curl -s http://127.0.0.1:5601/api/session/worker/status | grep -E 'active_count|max_active'
   ```

2. **Raise the cap** (if legitimate):
   ```bash
   export ATLAS_SESSION_WORKER_MAX_ACTIVE=50
   # Restart the server
   ```

3. **Wait for idle reaper:** workers idle longer than `ATLAS_SESSION_WORKER_IDLE_TTL_SEC`
   (default 900 seconds = 15 minutes) are automatically evicted. Watch the
   backend logs for `[SessionWorker] worker_evicted: <owner_slot>`.

4. **Manual cleanup** (if needed):
   - Identify the idle session: `curl -s http://127.0.0.1:5601/api/sessions`
   - Kill the worker: `curl -X POST http://127.0.0.1:5601/api/session/stop?session_id=<id>`
   - This frees the owner slot immediately.

### Rollback to Session-Scoped Mode

```bash
unset ATLAS_SESSION_WORKER_POLICY
unset ATLAS_SESSION_WORKER_MAX_ACTIVE
# or explicitly:
export ATLAS_SESSION_WORKER_POLICY=session-scoped
python3 src/atlas_ui.py
```

This fully restores the prior behavior (unbounded session-per-IP-per-workflow spawning
with no global cap).

## Near-Term Decision

Stabilize **single active session worker semantics** before adding deeper
subworker orchestration.

The first correctness target is:

- workflow switch has a clear stop/keepalive/kill rule
- Atlas UI state matches the real session worker state
- stale `stop` / prompt queue records cannot leak into a new worker
- user/IP/workflow routing is deterministic
- `stop`, `shutdown`, and workflow switching are distinguishable in UI and backend

This order matters because subworker orchestration will multiply the number of
jobs, logs, cancellations, and session routes. If single-active semantics are
ambiguous, later failures will be hard to classify as session-routing bugs,
orchestrator-dispatch bugs, or subworker-merge bugs.

## Subworker Call Primitives

The primitives already exist, but they have different intended routes.

`dispatch_workflow` is the orchestrator-to-workflow-worker path. It can dispatch
one workflow or a list of stages, and supports serial/DAG scheduling through the
Atlas job dispatch layer.

`worker_call` / `worker_call_all` exist for generic worker or in-process
subagent calls. In default IPC/portless mode, workflow-worker targets should not
be called through raw HTTP-style `worker_call`; workflow targets must go through
the pipeline/IPC job path. Plain agent-type subtasks can still be routed as
in-process subagents.

`core/delegate_runner.py` also supports multiple delegate backends such as
`sub-agent`, `http-worker`, `codex`, `gemini`, and `api`.

Important source anchors:

- `src/orchestrator/tools.py::dispatch_workflow`
- `src/orchestrator/react_bridge.py::_dispatch_workflow`
- `src/atlas_api_jobs.py::_make_job_record`
- `src/atlas_api_jobs.py::_dispatch_job_to_ipc_worker`
- `core/agent_client.py::worker_call`
- `core/delegate_runner.py::DelegateRunner`

## Orchestrator Worker Chat Visibility

The current UI has worker visibility, but it is not yet a perfect "every worker
conversation is always visible inline" model.

What exists today:

- orchestrator chat shows active worker status strips/cards from
  `/api/orchestrator/workers`
- worker workflow sessions can poll `/api/pipeline/progress-debug` to map
  `(ip, workflow)` to an active `job_id`
- the worker chat feed then polls `/api/job/{job_id}/log` and appends worker
  `action`, `observation`, `response`, and `thought` rows
- `api_job_log` can read HTTP worker logs, IPC response entries, IPC stdout
  fallback logs, or session conversation fallback

Known risks:

- the live worker chat path currently assumes one active job per `(ip, workflow)`
- very fast jobs can finish before the worker session auto-resolves the active
  `job_id`
- IPC workers only produce structured response entries after completion; during
  execution the UI relies on stdout log parsing
- server restart weakens `_jobs` memory-backed job-to-log mapping
- orchestrator chat itself shows status and dispatch events, while full worker
  transcript visibility is strongest after opening the worker workflow chat or
  loading a specific job log

Recommended QA flow before subworkers:

```text
orchestrator chat -> dispatch rtl-gen -> open rtl-gen worker chat
-> confirm live action/obs/response rows -> wait for completion
-> reopen job log -> confirm same transcript remains inspectable
```

## Future RTL-GEN Subworker Model (Deferred)

**Multi-worker subworker fanout is DEFERRED** until worker chat/log visibility and
job-lane identity are stable. This plan only stabilizes the interactive control plane.

Adding multiple `rtl-gen` subworkers is feasible, but the current job identity
needs one more dimension.

Today, active job conflicts are scoped roughly by IP plus stage/workflow. If we
dispatch several jobs that all look like `workflow=rtl-gen` for the same IP,
dedupe/conflict logic can treat them as duplicates. The worker chat also maps
one `(ip, workflow)` to one active job, so multiple child jobs would race for
the same UI slot.

A robust model should add explicit child-job identity:

```text
parent_job_id
subworker_role
subtask_id
worker_lane
```

Possible `rtl-gen` child roles:

- `interface`
- `registers`
- `datapath`
- `fsm`
- `integration-review`
- `lint-precheck`

The conflict key should become:

```text
ip + workflow + worker_lane/subworker_role
```

The UI should render a parent `rtl-gen` coordinator job with child rows/chips,
then merge child logs by role in the parent worker chat. This keeps multiple
subworkers visible without pretending they are one linear transcript.

## Implementation Direction

Two viable routes exist.

Route A: split RTL work into separate workflows/stages such as
`rtl-iface-gen`, `rtl-regfile-gen`, `rtl-datapath-gen`, `rtl-fsm-gen`, and
`rtl-review`. This fits the existing `dispatch_workflow(stages=[...],
schedule="dag")` model, but increases workflow surface area.

Route B: keep `rtl-gen` as a coordinator and add child jobs under it. This is
closer to the intended future model, but requires job identity, conflict logic,
UI aggregation, and artifact merge policy changes.

Preferred sequence:

1. stabilize single active session worker semantics
2. verify orchestrator worker chat/log visibility end to end
3. add parent/child job identity for `rtl-gen` subworkers
4. add UI child-log aggregation and cancellation behavior
5. only then enable coordinator-style `rtl-gen` fanout

## Coverage Notes

The future coverage suite should include:

- user A/B isolation across identical IP/workflow names
- workflow switch while a worker is running
- stop versus shutdown versus keepalive behavior
- stale queue cleanup for `session_queue`
- orchestrator dispatch to a worker and live transcript visibility
- multiple child `rtl-gen` jobs with separate lanes
- child cancellation without killing the parent coordinator
- parent completion only after child artifacts are merged and reviewed
- UI reload/server restart with job log rehydration

The main architectural point: orchestrator mode benefits from session/workflow
isolation, but future multi-subworker RTL generation needs lane-level identity
on top of that isolation.
