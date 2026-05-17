# Multi-User Worker Isolation

Status: risk review captured on 2026-05-17 KST.

This page records whether Atlas/Common AI Agent workers can collide when
multiple users or IP runs are active at the same time.

## Current Answer

Yes, collision is possible in the shipped HTTP-worker path.

The durable handoff queue and Pipeline state API are mostly user-scoped, but
live HTTP worker dispatch is still URL-scoped, not lease-scoped. A worker URL
such as `http://localhost:5521` does not currently prove that the worker belongs
to the requesting user, IP, workflow, workspace, or pipeline run.

## Evidence From Code

Worker URL resolution:

- `src/atlas_api_jobs.py::_resolve_worker_url(workflow)` checks
  `WORKER_URL_<workflow>` and then falls back to `WORKER_URL_DEFAULT`, defaulting
  to `http://localhost:8001`.
- `core/delegate_runner.py::HTTPWorkerDelegate._resolve_worker_url()` uses the
  same precedence.
- There is no worker lease lookup in this path.

Worker launch command:

- `src/atlas_api_jobs.py::_worker_launch_command()` starts a worker with
  `ATLAS_PROJECT_ROOT=<project_root>`, `--workflow <workflow>`,
  `--worker-name <workflow>`, and `--session <session_name>`.
- The command embeds useful context, but this is an operator command, not an
  enforced dispatch guard.

Worker server:

- `core/agent_server.py` accepts `POST /run` with `workflow`, `session`, `ip`,
  and `project_root`.
- Per-run session override writes to `.session/<session>/conversation.json`,
  `.session/<session>/todo.json`, `.session/<session>/cost.json`, and related
  files.
- `/health` returns only `{status, runs}`. It does not expose bound user, IP,
  workflow, workspace, project root, or current lease.
- The in-memory run store is per worker process, and persistence is under
  `.session/agent_runs.json` in the common source tree.

Already-shipped safe areas:

- `doc/wiki/orchestrator-worker-handoff-review.md` records that
  `/api/pipeline/state`, handoff list/save/take, and `claim_next` are
  user-scoped for handoff JSON.
- These protections do not by themselves isolate a live HTTP worker once a
  request is sent to a shared `WORKER_URL_*`.

## Evidence From Current Runtime

Observed process state during the mini CPU rerun investigation:

- `:5521` was already serving a `quad_spi` `rtl-gen` worker:
  `--workflow rtl-gen --worker-name author --session quad_spi_author`.
- `:5522` was already serving a `quad_spi` `tb-gen` worker:
  `--workflow tb-gen --worker-name verify --session quad_spi_verify`.
- `8001`, `8002`, `8003`, and `8765` were not listening.
- Several unrelated real `ssot-gen` jobs were also running for `quad_spi_ctrl`
  and `atcuart100`.
- The mini CPU headless processes were stopped and no `mini_cpu_orch_rerun`
  process remained.

Interpretation:

- A file overwrite collision did not occur for the mini CPU run because it did
  not reach live worker dispatch, and its scratch roots were separate.
- A live worker collision was still a real operational risk: if mini CPU had
  resolved `WORKER_URL_RTL_GEN` to `http://localhost:5521` or
  `WORKER_URL_TB_GEN` to `http://localhost:5522`, it would have submitted work
  to workers launched for `quad_spi`.
- Provider contention did occur as a separate class: multiple real `ssot-gen`
  calls were active, and mini CPU stalled in the first `ssot-gen` call without
  producing artifacts.

## Collision Classes

| Class | Current risk | Why |
|---|---:|---|
| File/artifact overwrite | Medium | Safe when each run uses a unique root; unsafe if two users share the same IP directory or `project_root`. |
| Session history/todo/cost mix | Medium | Per-run `session` can isolate `.session/<session>`, but nothing prevents two jobs from reusing the same session name. |
| Live worker wrong-owner dispatch | High | `WORKER_URL_*` selects by URL only; no user/IP/workspace/run lease is checked before `/run`. |
| Worker capacity collision | High | A worker accepts concurrent runs up to `AGENT_SERVER_MAX_CONCURRENT`; this can interleave unrelated jobs unless the worker is dedicated or leased. |
| Pipeline UI state leakage | Lower | Handoff state has user-scoped tests, but live worker status is not fully lease-scoped. |
| LLM provider throttling/hang | High | Real provider calls are shared resources; concurrent long `ssot-gen` calls can starve or stall new runs. |
| Unified exec handle exhaustion | High in long sessions | Codex reports the 60-process-handle limit even when OS workflow processes are not leaked. |

## Can We Prevent It Now?

Partially, with operating discipline:

1. Do not use `WORKER_URL_DEFAULT` in multi-user runs.
2. Allocate unique worker ports per user/IP/workflow/run.
3. Launch workers with unique sessions such as
   `<user>/<ip>/<workflow>/<pipeline_run_id>`.
4. Set `ATLAS_PROJECT_ROOT` to the run scratch root when launching each worker.
5. Export `WORKER_URL_RTL_GEN`, `WORKER_URL_TB_GEN`, etc. to those unique worker
   URLs only for that run.
6. Before dispatch, check that the target port is not already bound to another
   IP/session.
7. Prefer JSON handoff plus `/take` when no verified worker is available.

This prevents most accidental collisions, but it is not a hard product-level
guarantee because the worker server does not enforce the lease.

## Required Product Fix

The robust fix is an orchestrator-managed worker lease model:

1. Add worker lease records keyed by
   `user_id + workspace_id + ip_id + workflow + pipeline_run_id`.
2. Add `/health` or `/capabilities` metadata from each worker:
   `worker_id`, `bound_user`, `bound_ip`, `bound_workflow`, `session`,
   `project_root`, `active_run_count`, `max_concurrency`, and `lease_id`.
3. Make dispatch fail closed when the resolved worker metadata does not match
   the job scope.
4. Remove or disable `WORKER_URL_DEFAULT` for multi-user mode.
5. Add a dynamic port allocator or a single gateway that routes by lease, not
   by manually configured fixed ports.
6. Persist worker leases in DB, with heartbeat and TTL cleanup.
7. Include `user_id` and `workspace_id` in session names and cost/trace records.
8. Make the Pipeline UI show whether a worker is dedicated, shared, busy,
   stale, or mismatched.

Until those fixes land, Atlas should label live worker mode as
`shared-worker-risk` unless every worker URL has been verified as dedicated to
the current run.

## Operational Rule

For multi-user or parallel IP development:

- Safe: unique scratch root + unique session + unique worker port/lease per
  user/IP/workflow/run.
- Risky: reusing `5521`, `5522`, or `8001` across unrelated IPs.
- Unsafe: relying on `WORKER_URL_DEFAULT` while another user or IP run has a
  live worker on that URL.

