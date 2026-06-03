# Pipeline Progress Debugging

This page defines how ATLAS should debug progress for pipeline and worker
runs without guessing from scattered files.

Related: [[atlas-pipeline-screen]] · [[orchestrator-worker-handoff]] ·
[[multi-user-worker-isolation]] · [[ssot-gen-pass-pipeline]] ·
[[wiki-curation-policy]]

## Core Rule

Do not treat a headless-only pass as production flow evidence.

The real user environment is:

```text
ATLAS UI
  -> /api/pipeline/dispatch or /api/job/dispatch
  -> workflow worker /run
  -> worker /status/<run_id>
  -> worker /result/<run_id>
  -> artifacts + DB workflow_runs + pipeline state
  -> UI refresh
```

Headless runs are still valuable, but their role is narrower:

- fast isolated regression tests
- deterministic artifact contract tests
- reproduction of stuck LLM/provider calls
- validation of workflow scripts without browser/UI overhead

The final claim for a product-facing flow must use the same Atlas UI/API/worker
path the user uses.

## Current Debug Surface

The pipeline state endpoint should expose both live worker state and headless
file state:

```text
GET /api/pipeline/state?ip=<ip>
  -> progress_debug.worker
  -> progress_debug.headless
  -> progress_debug.diagnosis

GET /api/pipeline/progress-debug?ip=<ip>
  -> same compact diagnosis block, without the full stage payload
```

`progress_debug.worker` is authoritative when worker jobs exist in the current
ATLAS UI process. It summarizes job id, run id, worker URL, workflow, stage,
session namespace, elapsed time, polling age, iterations, result tail, and
error.

`progress_debug.headless` is a fallback and reproduction aid. It reads:

```text
<ip>/logs/heartbeat.json
<ip>/logs/run_progress.jsonl
<ip>/logs/llm_call_trace.jsonl
<ip>/logs/headless_run.json
well-known stage artifacts such as yaml/<ip>.ssot.yaml and lint/dut_lint.json
```

The same headless summary can be inspected from shell:

```bash
python3 -m src.progress_debug --root /path/to/workspace --ip <ip>
python3 -m src.progress_debug --root /path/to/workspace --ip <ip> --json
```

- Orchestrator `trace.jsonl` is append-only with no rotation (`core/orchestrator_trace.py:117`); harmless today (~204 KB total across all IPs) since each per-IP file is frozen when its run ends, but add rotation if sustained stress/CI loads push a single IP toward ~14k dispatches (~10 MB).

## What Good Progress Evidence Looks Like

For a live worker run, the UI should be able to answer these questions without
manual file hunting:

- Which workflow/stage is running?
- Which worker URL owns it?
- Which `session` and `scope_path` are bound to it?
- Which model is being used?
- How long has it been running?
- When was it last polled?
- Did it return a `run_id`?
- Is it blocked by a dependency or dispatch failure?
- Which artifact/version/run history will prove completion?

For a stuck LLM call, the UI should show:

- stage and log stage
- model
- elapsed seconds inside the open LLM call
- prompt/system prompt character counts when available
- whether an `llm_call_end` event or LLM log artifact exists
- which expected artifact is still missing

## Stop Conditions

Use these stop conditions when debugging a slow or stuck progress view:

1. If a worker job exists, debug the worker first.
2. If the worker has no `run_id`, debug dispatch and worker URL/lease binding.
3. If the worker has a `run_id` but polling is stale, debug `/status/<run_id>`.
4. If the worker completed but stage state did not update, debug `/result`,
   artifact recovery, and DB `workflow_runs`.
5. If no worker job exists and headless logs exist, debug the headless runner as
   a reproduction path, not as the product flow.
6. If neither worker nor headless state exists, the UI should say "no run
   registered" instead of forcing the user to inspect directories.

## Development Practice

Every debugging improvement that changes how we understand the pipeline should
update this wiki, or a more specific linked page, in the same development pass.

The wiki is part of the product control plane. It must capture:

- real-use validation results, not just unit-test success
- known differences between headless, worker, and UI behavior
- shipped-vs-target status for orchestrator and worker features
- failure modes that recur across IPs or users
- operator-facing commands and endpoint paths

Do not let the wiki trail behind the implementation. When a workflow or UI
debugging rule changes, update code, tests, and wiki together.

## Exec Session Warnings

Codex can warn that the unified exec process limit is near or above 60 even
when the product worker pool itself is not overloaded. Treat that warning as a
Codex-session resource signal first, not as proof that Atlas workers are still
running.

Triage order:

1. Check live Atlas/Common-AI-Agent worker processes before killing anything.
2. Do not kill Claude, Cursor, cmux, or MCP helper processes just because they
   match broad words like `worker`; they may belong to another user/session.
3. If no `textual_main`, `agent_server`, `headless_workflow`, or Atlas worker
   process is present, record that product workers are not the source of the
   warning.
4. Continue with short, bounded commands and avoid starting new long-running
   servers until the Codex exec pressure clears.

This matters for multi-user development: process cleanup must be scoped by
user, session, IP, workflow, and command owner. Broad `pkill` style cleanup is
unsafe until worker leases/gateway isolation are implemented.
