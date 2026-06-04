# Orchestrator Worker Handoff

This page defines the control-plane concept for cross-workflow repair and
pipeline execution.

> Status: mixed as-built plus target design. Shipped today:
> `/api/pipeline/state` orchestrator fields, durable
> `<ip>/handoff/{pending,claimed,done,review,suggested}` JSON queue,
> `headless_workflow.py --stages take --workflow <wf>`, and
> `/api/pipeline/dispatch` using `WORKER_URL_*` HTTP workers with root
> routes such as `/run`, `/status/<id>`, and `/result/<id>`. Verified on
> 2026-05-16 by `tests/test_pipeline_orchestrator_worker_integration.py`.
> Not shipped yet: single-port worker gateway, worker capacity/lease DB,
> and an autonomous always-on orchestrator agent that closes repair loops.
> See [[orchestrator-worker-handoff-review]] for the spec-vs-shipped audit.

The target distinction is:

```text
worker mode     -> live agents receive handoffs in real time
non-worker mode -> handoff JSON is persisted; another workspace takes it later
```

Workspace remains a one-stage-at-a-time surface. Pipeline/orchestrator is the
multi-stage control plane.

## Orchestrator Mode

Target switch:

```text
ATLAS_ORCHESTRATOR_MODE=1
```

When Orchestrator Mode is implemented and enabled, the Pipeline screen is the control plane.
Workspace/Workflow screens become detail surfaces for the selected worker,
workflow, artifacts, logs, todo tracker, and evidence.

Important UI behavior:

```text
Orchestrator Mode ON:
  workflow change = navigate detail view
  running workers continue
  no "stop current agent?" prompt is needed

Orchestrator Mode OFF:
  workflow change = existing single-workspace behavior
  if one local agent is running, ask whether to stop before switching
```

This avoids mixing two mental models. In orchestrator mode, "agent running" is
not a single global Workspace state; it is per worker/job/stage. The Pipeline
screen owns the running state, and Workspace merely shows details for whichever
workflow the user selects.

## Architecture Decision

Decision: **orchestrator-centered handoff**.

Workers must not directly dispatch work to other workers. A worker may emit a
`suggested_handoff` or write workflow feedback, but the orchestrator decides
whether to dispatch it live, persist it as JSON, retry, mark downstream stale,
or stop at Review Decision Needed.

```text
worker -> suggested_handoff/evidence -> orchestrator -> next worker
```

Rejected default: worker-to-worker direct dispatch.

Why rejected:

- it hides ownership and version boundaries
- retry budgets become distributed and hard to stop
- cost/token accounting becomes fragmented
- failed workers can lose handoff context
- stale evidence invalidation becomes inconsistent
- two workers can ping-pong the same mismatch without a single stop rule

Allowed exception: a worker may call helper tooling only for a local,
workflow-owned subtask that does not cross artifact ownership boundaries. For
example, `rtl-gen` may call a local syntax/lint helper before returning its RTL
result. It may not call `tb-gen` or `coverage` directly; cross-workflow
handoff still returns to the orchestrator.

## Roles

### Orchestrator Agent

The orchestrator agent owns scheduling and convergence. It does not own SSOT,
RTL, TB, coverage, or EDA artifacts.

Responsibilities:

- read stage results, todo state, evidence files, versions, and run history
- decide which workflow owns the next repair
- dispatch work to a live worker when worker mode is available
- persist durable handoff JSON when no live worker is available
- mark downstream evidence stale when upstream artifacts change
- stop on pass, retry budget exhaustion, repeated mismatch, or Review Decision Needed
- verify worker output from disk artifacts before claiming done

The orchestrator is not allowed to directly patch generated IP artifacts to
make a run pass.

### User Input

The orchestrator may receive user input. In orchestrator mode, user input is a
pipeline-level decision, not a private worker chat message.

Good orchestrator-level user inputs:

- approve/reject a Review Decision Needed item
- choose one option when the SSOT or product semantics are ambiguous
- continue SSOT requirement Q&A during early IP authoring
- set run policy such as pipeline/CI/interactive behavior
- pause, resume, cancel, or retry a pipeline run
- allow a workflow owner to change authority artifacts such as SSOT, RTL, TB,
  model, or coverage plan

Workers may propose questions, but the orchestrator presents them to the user,
records the answer, and routes the structured decision back to the owner
workflow.

```text
worker detects ambiguity
  -> suggested_user_decision
  -> orchestrator user input queue
  -> user answers in Pipeline screen
  -> orchestrator persists decision
  -> owner workflow receives structured decision/handoff
```

The answer must be durable. It should be written as review/decision or handoff
metadata, not only stored in transient chat history.

In early IP authoring, most orchestrator decisions will naturally be SSOT
decisions. The Pipeline screen should not replace the SSOT Q&A workbench. It
should route the user to the right detail surface.

Recommended behavior:

```text
Pipeline SSOT-GEN decision click
  -> open Workspace
  -> select ssot-gen workflow
  -> focus Q&A Session / requirement decision card

Pipeline RTL-GEN issue click
  -> open Workspace
  -> select rtl-gen workflow
  -> focus todo/evidence/repair card

Pipeline SIM-DEBUG mismatch click
  -> open Workspace
  -> select sim-debug workflow
  -> focus mismatch classification and owner routing evidence
```

The same rule applies to every workflow. Pipeline decides and routes;
Workspace/Workflow provides the detailed interactive surface.

### Workflow Worker

A workflow worker owns exactly one workflow boundary such as `rtl-gen`,
`tb-gen`, `lint`, `coverage`, `sim-debug`, `syn`, `sta`, or `pnr`.

Responsibilities:

- consume a handoff addressed to its workflow
- read only the authority/evidence listed in the handoff plus its normal
  workflow inputs
- edit only artifacts owned by that workflow
- write fresh output artifacts and result evidence
- return a structured result to the orchestrator

Worker delivery forms:

- in-process Python call for direct invocation
- subprocess CLI such as `headless_workflow.py`
- remote worker URL over HTTP via `WORKER_URL_*`
- cmux session for an interactive shell worker
- user-driven Workspace command such as a future `/take`

Workers can write:

```text
<ip>/handoff/suggested/<handoff_id>.json
```

but this is only a proposal. The orchestrator must promote it to `pending`,
dispatch it live, or move it to review.

## Worker Mode

Worker mode is active when the orchestrator can resolve a live worker endpoint
or live agent for the target workflow.

## Worker Ports

Current shipped behavior: one port per worker process. `WORKER_URL_<WF>` or
`WORKER_URL_DEFAULT` resolves to a root-route worker that serves `/run`,
`/status/<id>`, and so on (`core/delegate_runner.py:212`,
`src/atlas_api_jobs.py:562`). The target replacement described below is not
shipped.

Target UX: one Atlas/Orchestrator port.

Separate worker processes cannot bind the same host/port directly, so the
single-port design requires a gateway/coordinator route in front of workers.
The Pipeline UI and operator should only need one base port, while workflow
workers are addressed by path:

```text
ATLAS_ORCHESTRATOR_MODE=1
ATLAS_WORKER_GATEWAY_MODE=1

WORKER_URL_RTL_GEN=http://localhost:8000/api/workers/rtl-gen
WORKER_URL_TB_GEN=http://localhost:8000/api/workers/tb-gen
WORKER_URL_LINT=http://localhost:8000/api/workers/lint
WORKER_URL_SIM_DEBUG=http://localhost:8000/api/workers/sim-debug
```

The client appends `/run`, `/status/<id>`, `/result/<id>`, `/log/<id>`, and
`/cancel/<id>` to the configured worker URL. Therefore the gateway must serve:

```text
/api/workers/rtl-gen/run
/api/workers/rtl-gen/status/<id>
/api/workers/rtl-gen/result/<id>
/api/workers/rtl-gen/log/<id>
/api/workers/rtl-gen/cancel/<id>
```

In this design, URL string count is not the scheduler authority. Scheduling
uses gateway capacity metadata:

```text
one available worker capacity     -> serial scheduling
multiple available capacities      -> DAG/parallel scheduling is allowed
no live worker capacity            -> write pending handoff JSON for /take
same path prefix, one backend slot -> serial for that capacity group
```

Minimum gateway worker metadata:

```json
{
  "workflow": "rtl-gen",
  "state": "running",
  "capacity_group": "local-rtl-0",
  "slots_total": 1,
  "slots_available": 0,
  "current_task": "repair EQ_GPIO_READBACK",
  "last_heartbeat_at": "2026-05-16T12:34:56Z"
}
```

Do not expose one port per workflow in the ATLAS UX. If existing root-route
worker code needs adaptation, add a gateway/router layer rather than teaching
users to manage many ports.

## Multi-User Isolation

In multi-user mode, the orchestrator must not be a global singleton.

Current ATLAS already has useful building blocks:

- DB-backed `users`
- DB-backed `sessions`
- per-IP `ip_permissions`
- session APIs that filter by authenticated user
- chat room permission checks
- `.session/<session>/<ip>/<workflow>/` filesystem scoping

That is enough to make multi-user possible, but not enough by itself for
production orchestrator isolation. The orchestrator/gateway layer must carry
the same scope through every worker lease, log stream, handoff, decision, and
artifact write.

Required ownership:

```text
user_id                                -> one assigned user orchestrator
user orchestrator                      -> owns session/pipeline contexts
session_id + pipeline_run_id           -> one orchestrator run context
orchestrator run context               -> owns assigned worker leases
worker lease                           -> scoped to user/session/workspace/ip/workflow
```

`pipeline_run_id` is the durable, DB-backed run identifier this design needs.
It is distinct from the existing in-memory `pipeline_id` used by
`src/atlas_api_jobs.py` to group queued jobs (`atlas_api_jobs.py:144,427,747`).
The future implementation should either rename the in-memory field or store
the durable identifier in a new DB column so the two names do not collide.

This prevents one user's backend output, questions, handoffs, or artifacts from
being delivered to another user's UI.

Required isolation keys:

- `user_id`
- `session_id`
- `pipeline_id`
- `workspace_id`
- `ip_id`
- `workflow`
- `worker_id`
- `lease_id`

Worker allocation in multi-user mode:

```text
Pipeline starts for user A/session S1
  -> create or resume user A orchestrator OA
  -> OA creates/resumes run context for S1/pipeline P1
  -> OA leases workers for needed workflows
  -> workers receive user/session/ip/workflow scope
  -> all logs, decisions, handoffs, and results carry OA + S1/P1 scope

Pipeline starts for user B/session S2
  -> create or resume separate user B orchestrator OB
  -> OB creates/resumes run context for S2/pipeline P2
  -> OB cannot read or claim OA's handoffs unless permission allows it
```

One physical worker process may still serve multiple users, but only through
leased jobs with strict scope metadata. A worker must not reuse chat history,
todo state, output streams, or artifact roots across leases.

The Pipeline UI should show only the current user's orchestrator and worker
leases unless the user has admin permission.

Implementation rule: when a request enters the Pipeline screen, derive the
user orchestrator from the authenticated user, then derive the run context from
the active session/pipeline. Do not let the frontend pass an arbitrary `user_id`
to claim another user's orchestrator.

Current implementation rule for worker startup and snapshots:

```text
worker identity key:
  user / workspace_session / ip / workflow

request surfaces that must preserve the key:
  /api/pipeline/dispatch
  /api/pipeline/state
  /api/pipeline/progress-debug
  /api/pipeline/orchestrator/chat
  /api/orchestrator/workers
  /api/orchestrator/workers/warm
  core.tools.dispatch_workflow
  src.orchestrator.tools.read_pipeline_state
  src.orchestrator.tools.dispatch_workflow
```

This means worker processes may still be reused internally, but user-visible
state, sessions, warm workers, runtime snapshots, IPC jobs, chat history, todo
files, and artifact roots are scoped to the authenticated user and workspace
session. Ownerless legacy DB rows and unscoped IPC jobs are hidden from scoped
multi-user responses; IPC process metadata is filtered through the same visible
run set. Explicit `session_id` or `orchestrator_session_id` inputs are accepted
only when they match the authenticated
`user/workspace_session/ip/workflow` context.

The orchestrator React bridge must pass `ctx.session_id` and the trusted
runtime `ctx.user_id` into `src.orchestrator.tools.read_pipeline_state`.
Otherwise an LLM tool call can fall back to `ATLAS_ACTIVE_SESSION`, default
workspace state, or display-owner-only filtering even though the HTTP route was
correctly scoped.

## Orchestrator Supervisor IPC Runtime

As of commit `a96dbf29`, orchestrator chat no longer has to run the
orchestrator loop inside the ATLAS web server thread. The route now resolves an
orchestrator runtime through `src.orchestrator.runtime.get_orchestrator_runtime`
and selects the transport from environment:

```text
ATLAS_ORCHESTRATOR_TRANSPORT=thread  -> legacy in-process OrchestratorRunner
ATLAS_ORCHESTRATOR_TRANSPORT=ipc     -> supervisor subprocess runtime
ATLAS_EXEC_MODE=orchestrator         -> defaults to ipc when no transport is set
```

The current as-built path is:

```text
UI /api/pipeline/orchestrator/chat
  -> src.atlas_api_jobs api_pipeline_orchestrator_chat
  -> src.orchestrator.runtime.get_orchestrator_runtime(...)
  -> src.orchestrator.supervisor_runtime.OrchestratorSupervisorRuntime
  -> python -m src.atlas_orchestrator_supervisor_ipc --request ... --response ...
  -> src.orchestrator.react_bridge.OrchestratorReactLoop
  -> stage workers / workflow dispatch
```

This makes the orchestrator a supervisor runtime, not a normal stage worker.
The supervisor owns conversation/run lifecycle, wakeups, cancellation intent,
job visibility, and crash isolation. Stage workers still own SSOT, RTL, TB,
simulation, coverage, and other workflow artifacts.

Runtime files:

- `src/orchestrator/runtime.py` chooses thread vs IPC and caches IPC runtimes
  per `(atlas.db, project_root)`.
- `src/orchestrator/runtime_types.py` holds the shared `SubmitOutcome` contract
  so the route and legacy runner agree on return shape.
- `src/orchestrator/supervisor_runtime.py` creates the DB run, writes the
  supervisor request, spawns the subprocess, and registers a synthetic
  `job_kind=orchestrator-supervisor` IPC job.
- `src/atlas_orchestrator_supervisor_ipc.py` is the subprocess entry point. It
  configures `ATLAS_PROJECT_ROOT`, `ATLAS_SOURCE_ROOT`,
  `ATLAS_WORKER_TRANSPORT=ipc`, builds `OrchestratorContext`, and runs the
  React bridge loop.
- `src/orchestrator/supervisor_wake.py` is the file-backed wake channel.
- `src/orchestrator/supervisor_watch.py` waits for the subprocess, reads the
  response JSON, updates the visible job row, unregisters the process, and
  closes the orchestrator DB run.

Supervisor control files live under the request project root:

```text
.session/orchestrators-ipc/<run_id>/request.json
.session/orchestrators-ipc/<run_id>/response.json
.session/orchestrators-ipc/<run_id>/wake.jsonl
.session/orchestrators-ipc/<run_id>/cancel.json
.session/orchestrators-ipc/<run_id>/supervisor.log
```

The route registers the supervisor with the same in-memory job/process tables
used by IPC workflow workers, so admin/runtime snapshots can see the
orchestrator supervisor as a live process. Appending a second chat message to
an active run writes a DB `user_reply` step and a `user_message` wake event
instead of spawning another supervisor. When stage jobs finish,
`_advance_pipeline_from` appends a `job_complete` wake event for the owning
`orchestrator_run_id`.

The route must keep using the request-scoped project root:

```text
pr = _request_project_root(request, ip, body)
db = _atlas_job_db_path(pr)
```

Passing the global `project_root()` here would put supervisor control files,
`atlas.db`, chat history, and worker artifacts in the wrong user's workspace.

Verification recorded with the commit:

- targeted supervisor/runtime tests: `11 passed`
- legacy route and runner regression tests: `19 passed`
- Python compile for the new supervisor modules: pass
- manual supervisor runtime smoke: subprocess spawned, wrote response/log, and
  cleaned up through the watcher
- Computer Use QA: live ATLAS surface showed orchestrator state through the
  product UI
- `ruff` was attempted but unavailable in the active Python environment

In worker mode:

```text
sim-debug classifies rtl-gen owner
  -> orchestrator dispatches handoff to rtl-gen worker immediately
  -> rtl-gen worker repairs RTL using mismatch evidence
  -> orchestrator validates RTL evidence
  -> downstream lint/tb/sim/coverage rerun
```

The handoff still has a JSON payload, but it is transported live instead of
waiting in a pending folder.

Minimum worker dispatch payload:

```json
{
  "schema": "workflow_handoff.v1",
  "mode": "worker",
  "scope": {
    "user_id": "user_a",
    "session_id": "S1",
    "pipeline_id": "P1",
    "workspace_id": "workspace_1",
    "ip_id": "simple_gpio_lite",
    "workflow": "rtl-gen",
    "lease_id": "lease_123"
  },
  "handoff_id": "simple_gpio_lite__sim-debug__rtl-gen__EQ_READBACK",
  "ip": "simple_gpio_lite",
  "from_workflow": "sim-debug",
  "to_workflow": "rtl-gen",
  "reason": "FL-vs-RTL mismatch",
  "owner_confidence": "high",
  "evidence": {
    "classification": "sim/mismatch_classification.json",
    "compare": "sim/fl_rtl_compare.json",
    "scoreboard": "sim/scoreboard_events.jsonl",
    "goals": "verify/equivalence_goals.json"
  },
  "expected": {"prdata": "FL expected value"},
  "observed": {"prdata": "RTL observed value"},
  "required_output": [
    "rtl/*.sv",
    "rtl/rtl_authoring_provenance.json",
    "rtl/rtl_todo_tracker.json"
  ],
  "downstream_stale": ["lint", "tb-gen", "sim", "coverage", "sim-debug", "goal-audit"],
  "retry_budget": 2
}
```

`workflow_handoff.v1` is the intended schema name. The schema file is TBD until
the handoff queue module is implemented.

The orchestrator must verify the worker's disk artifacts before moving the
handoff to `done`.

## JSON Fallback Mode

If no live worker is available, the orchestrator must persist the handoff as
JSON. This is the durable, multi-workspace path.

Recommended layout:

```text
<ip>/handoff/pending/<handoff_id>.json
<ip>/handoff/claimed/<handoff_id>.json
<ip>/handoff/done/<handoff_id>.json
<ip>/handoff/review/<handoff_id>.json
```

State transitions:

```text
pending -> claimed -> running -> done
pending -> review_decision_needed
claimed/running -> pending   # if claim expires or worker dies
```

Target behavior: a workspace operator can run a `take` command to claim the
next compatible handoff. This command is not shipped yet.

```text
/take <ip> --workflow rtl-gen
```

Proposed CLI shape:

```text
python3 src/headless_workflow.py --root <root> --ip <ip> --stages take --workflow rtl-gen
```

The exact CLI can evolve during implementation, but the contract is stable: `take` claims one
pending JSON handoff for the requested workflow, executes the owner workflow,
and writes a result record.

## Why Not Only Realtime?

Realtime worker dispatch is faster, but JSON fallback is required because:

- the UI may be closed while backend work continues
- a user may reopen a different workspace/session
- workers may be unavailable or capacity-limited
- slow models may finish after the original chat context is gone
- audit/debug needs a durable record of why a workflow was rerun

The JSON handoff is the audit trail. Worker mode is an acceleration path, not
the source of truth.

## Review Decision Needed

Repeated repair failure does not immediately escalate. The orchestrator retries
within budget and writes Review Decision Needed when the same mismatch
signature is still unresolved after the retry budget is exhausted:

```text
<ip>/review/decision_needed_pipeline_repeated_<owner>_mismatch.json
```

`<owner>` is the failing workflow name (e.g. `rtl-gen`, `tb-gen`, `sim-debug`).

Use Review Decision Needed when automation cannot safely decide whether the
problem is:

- missing SSOT/product semantics
- wrong owner classification
- a false evidence gate
- insufficient workflow/tool capability

Review Decision Needed is not Q&A history. It is a signoff blocker with
evidence, owner, and next-action options.

## Relationship To Scheduling

The scheduler answers "what can run now?"

The orchestrator answers "who owns the next repair and how is it delivered?"

```text
one live worker      -> serial dispatch
multiple live workers -> DAG dispatch
no live worker       -> write pending handoff JSON
```

This keeps the system usable in both modes:

- Web/worker mode: live agents keep receiving work in real time.
- Workspace mode: user can run one stage, then explicitly take pending work.

## UI Contract

The UI should connect to the orchestrator through the existing Pipeline screen,
not through a separate chat-only path.

Existing surface:

- `frontend/atlas/pipeline.jsx` owns the Pipeline screen.
- `frontend/atlas/pipeline.jsx` polls `/api/pipeline/state?ip=<ip>` every 2 s.
- `frontend/atlas/pipeline.jsx` dispatches stage runs through
  `/api/pipeline/dispatch`.
- `src/atlas_api_jobs.py` already owns `/api/pipeline/state` and
  `/api/pipeline/dispatch`.

Proposed target addition to `/api/pipeline/state`:

```json
{
  "orchestrator": {
    "enabled": true,
    "mode": "worker|json|mixed",
    "pending_handoffs": 2,
    "claimed_handoffs": 1,
    "review_decisions": 0,
    "decisions_needed": 0,
    "workers": {
      "rtl-gen": {
        "state": "running",
        "worker_id": "worker-rtl-gen-0",
        "url": "http://localhost:8000/api/workers/rtl-gen",
        "workflow": "rtl-gen",
        "ip": "simple_gpio_lite",
        "job_id": "job_123",
        "current_task": "repair EQ_GPIO_READBACK",
        "last_heartbeat_at": "2026-05-16T12:34:56Z",
        "elapsed_s": 84
      },
      "tb-gen": {
        "state": "idle",
        "worker_id": "worker-tb-gen-0",
        "url": "http://localhost:8000/api/workers/tb-gen",
        "workflow": "tb-gen",
        "last_heartbeat_at": "2026-05-16T12:35:02Z"
      },
      "lint": {"state": "offline", "workflow": "lint"}
    }
  },
  "handoffs_by_workflow": {
    "rtl-gen": {
      "pending": 1,
      "claimed": 0,
      "done": 3,
      "review": 0,
      "latest": {
        "handoff_id": "simple_gpio_lite__sim-debug__rtl-gen__abc123",
        "from_workflow": "sim-debug",
        "reason": "FL-vs-RTL mismatch",
        "goal_ids": ["EQ_GPIO_READBACK"]
      }
    }
  }
}
```

Offline workers omit `last_heartbeat_at`; the gateway treats absence as offline.

Pipeline screen behavior:

- Top run bar shows `orchestrator: worker`, `orchestrator: json`, or
  `orchestrator: mixed`.
- Top run bar shows whether `ATLAS_ORCHESTRATOR_MODE` is on.
- Top run bar shows `handoffs N pending` and `review M`.
- Top run bar shows `decisions K needed` when orchestrator-level user input is
  required, once the proposed API field is implemented.
- Top run bar or worker strip shows which workers are `running`, `idle`,
  `blocked`, `stale`, `offline`, or `done`.
- Each worker indicator should show workflow, IP, current task, elapsed time,
  and last heartbeat when available.
- User answers entered from the Pipeline screen are saved as durable decisions
  and routed to the owning workflow; they are not appended only to chat/Q&A
  history.
- Clicking an SSOT-related decision or the SSOT-GEN stage should deep-link into
  Workspace `ssot-gen` and focus the Q&A Session / requirement card.
- Clicking any other workflow issue should deep-link into the matching
  Workspace workflow detail surface.
- A failed StageCard with owner classification shows:

```text
blame -> rtl-gen [ dispatch ] [ save handoff ] [ view evidence ]
```

- A StageCard for a workflow with pending handoffs shows:

```text
handoff: 1 pending [ take ]
```

- `[ dispatch ]` asks the orchestrator to send the handoff to a live worker.
- `[ save handoff ]` forces JSON fallback even if worker mode exists.
- `[ take ]` claims one pending JSON handoff for the current workflow/session.
- `[ view evidence ]` opens the classification/scoreboard/equivalence evidence.

Worker status meanings:

```text
running -> worker is actively executing a job or handoff
idle    -> worker is online and has no current job
blocked -> worker is waiting for Review Decision / missing authority / tool blocker
stale   -> worker output exists but upstream artifact version changed
offline -> no live heartbeat or endpoint
done    -> latest assigned job finished and evidence was recorded
```

Workspace behavior:

- Workspace keeps single-stage execution.
- In Orchestrator Mode, changing workflow tabs does not stop running workers;
  it only changes the selected detail view.
- In non-orchestrator mode, keep the existing safety prompt before switching
  away from a locally running workflow.
- When `/take <ip> --workflow rtl-gen` is implemented, Workspace claims one
  JSON handoff and runs the owner workflow.
- If there is no pending handoff, `/take` prints a short "none available"
  result instead of starting unrelated work.

UI must not be the source of truth. It renders orchestrator state and sends
commands. The durable state remains the handoff JSON, run DB rows, and
artifact evidence.

## Related

- [[full-flow-pipeline]]
- [[workflow-feedback-and-scheduling]]
- [[workflow-ownership-and-boundaries]]
- [[rtl-version-run-history]]
- [[human-review-and-escalation]]
- [[orchestrator-worker-handoff-review]] — spec-vs-shipped audit (2026-05-16); use it to tell which sections of this page describe target behavior versus what is actually in `src/` today.
