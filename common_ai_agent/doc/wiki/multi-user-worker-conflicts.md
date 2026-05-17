# Multi-User Worker Conflicts

Status: operational risk note, 2026-05-17. This page captures the structural
conflict surface for the current worker fleet and what is already happening on
this machine right now. It complements [[orchestrator-worker-handoff]] and
[[orchestrator-worker-handoff-review]] which describe the *target* multi-user
isolation design that is not shipped yet.

Related: [[orchestrator-worker-handoff]] · [[orchestrator-worker-handoff-review]] ·
[[workflow-ownership-and-boundaries]] · [[parallel-todo-sub-agent-workers]]

## TL;DR

The current worker dispatch path resolves a `WORKER_URL_<workflow>` env var to
one fixed HTTP endpoint and posts `/run` to it. There is no `user_id`,
`session_id`, `pipeline_run_id`, or `lease_id` in the request, and the worker
does not validate that the incoming workflow matches its startup binding.

That makes the worker pool shared at process granularity. Today this means:

- Two different IPs that share the same `WORKER_URL_*` value will share the
  worker's `_runs` dict, its `.session/worker_registry.json`, its
  `.session/agent_runs.json`, and its `<startup_root>/.session/<session>/`
  files.
- If a `/run` payload omits `project_root`, the worker falls back to its own
  startup `_project_root`. Any artifacts written by the agent during that run
  land under the *worker's* startup root, not the caller's IP root.
- Two real LLM `ssot-gen` runs against different scratch roots compete for the
  same provider quota and the same Codex `unified exec` handle budget.

Conclusion: **the conflict is structural, not just hypothetical**. The fact
that we have not seen artifact corruption yet is mostly because Atlas dispatch
explicitly sets `project_root` and unique `session_name` per job. As soon as
something else (a manual `curl /run`, a future tool, a forked dispatcher,
parallel `--take` runners) bypasses that discipline, mixing is possible.

## Evidence In Source

- `src/atlas_api_jobs.py:581-588` — `WORKER_URL_<WF>` resolves to a single
  fixed URL; default fallback is `http://localhost:8001`. No tenant key.
- `core/agent_server.py:35` — `_project_root` is captured at server startup
  and is process-global.
- `core/agent_server.py:103,117` — `_REGISTRY_FILE` and `_PERSISTENCE_FILE`
  are `<_project_root>/.session/worker_registry.json` and
  `<_project_root>/.session/agent_runs.json`. Both are single-file,
  single-process state, shared across every `/run` the worker accepts.
- `core/agent_server.py:664` — the per-run `ATLAS_PROJECT_ROOT` chain is
  `project_root` arg → `os.environ['ATLAS_PROJECT_ROOT']` → `_project_root`.
  An omitted or empty `project_root` silently falls back to the worker's
  startup root.
- `core/agent_server.py:703` — `session_dir = Path(_project_root) / ".session"
  / active_session`. Session subdir lives under the worker's startup root, so
  a `/run` from IP A and another from IP B with different `session_name`
  values still end up siblings inside the same worker's `_project_root`.
- `core/agent_server.py /run handler` — no permission check that the request
  `workflow` matches the `--workflow` value the worker was started with. A
  `/run` for `tb-gen` posted to the `rtl-gen` worker is accepted.

## Failure Modes

### F1. Wrong-root artifact writes

If a caller posts `/run` without `project_root`, the worker writes files into
its own startup `_project_root`. On this machine that root is
`/Users/brian/Desktop/Project/brian_hw/common_ai_agent`, not the IP scratch
root the caller is iterating in.

Trigger: any code path that calls `WORKER_URL_*` directly (curl, script,
forked dispatcher) without populating `project_root` from the IP root.

Blast radius: artifacts polluted into common_ai_agent source tree. Hard to
detect because `git status` may not pick it up immediately.

### F2. Mixed worker session/registry state

Two different IPs sending `/run` to the same port both write into
`<worker_startup_root>/.session/worker_registry.json` and
`<worker_startup_root>/.session/agent_runs.json`. There is one in-memory
`_runs` dict for the whole worker process.

Concrete effect: "what was this worker doing?" answer is interleaved across
unrelated IPs. Recovering after a worker crash is ambiguous because the
persistence files are not partitioned by `user/session/ip`.

### F3. Wrong-workflow acceptance

A worker started with `--workflow rtl-gen` will still happily process a
`/run` whose request body says `workflow: "tb-gen"`. The startup binding is
advisory: it sets default todo template paths and prompt context, but it
does not gate which work the worker accepts.

Concrete effect: if a caller's `WORKER_URL_TB_GEN` is misconfigured and
points at the rtl-gen port (e.g. ports `5521` and `5522` swapped), the call
succeeds and produces wrong-context output.

### F4. Provider/credential contention

Even when artifacts and sessions stay clean, multiple real LLM jobs against
the same Codex/Claude CLI process share one OAuth/credential context and one
`unified exec` budget. Long parallel `ssot-gen` runs can race for the
provider and trigger:

`maximum number of unified exec processes you can keep open is 60`.

Recorded in [[gpio-orchestrator-multiworker-run]] BUG-028. This is not file
corruption, but it does halt unrelated runs.

## Current Live State (2026-05-17)

Observed on this machine while writing this page:

- `:5521` worker — `workflow=rtl-gen`, `worker-name=author`,
  `session=quad_spi_author`. Bound to QUAD SPI by current convention.
- `:5522` worker — `workflow=tb-gen`, `worker-name=verify`,
  `session=quad_spi_verify`. Same convention.
- Multiple real-LLM `ssot-gen` jobs running concurrently against different
  scratch roots:
  - `quad_spi_ctrl` ssot-gen, `gpt-5.3-codex`.
  - `atcuart100` ssot-gen/repair, `gpt-5.3-codex`.
  - `atcuart100` draft ssot-gen, `glm-5.1`.
- Mini CPU `_001` / `_002` / `_003` scratch trees stalled at the first
  ssot-gen LLM call. They never reached `rtl-gen`, so no live shared worker
  use happened on those — but if Mini CPU is restarted now and re-uses the
  current `WORKER_URL_RTL_GEN=http://localhost:5521`, F1/F2/F3 apply.

Per-IP scratch root collision: none today. Each run root is distinct so
artifact overwrites do not happen at the artifact path level.

Worker port collision: structurally possible right now. `5521` and `5522`
are claimed by `quad_spi_*` workers; another IP that re-uses those URLs will
hit F1/F2/F3 unless every call passes `project_root` and a unique
`session_name`.

## Mitigations Available Today

These are interim guardrails that work with the current shipped code, not the
target design.

1. **Never reuse worker ports across IPs in one machine session.**
   Run Mini CPU as its own pair, e.g. `5621/5622`, set
   `WORKER_URL_RTL_GEN=http://localhost:5621` and
   `WORKER_URL_TB_GEN=http://localhost:5622` for that run, and start the
   worker pair against the Mini CPU scratch root.
2. **Always pass `project_root` and a unique `session_name` in every
   `/run`.** Atlas dispatch already does this; manual `curl` calls and
   ad-hoc scripts must too. Empty `project_root` silently bleeds artifacts
   into the worker startup tree (F1).
3. **Per-IP worker startup root.** Launch each worker with `cd <ip-scratch>`
   and `ATLAS_PROJECT_ROOT=<ip-scratch>` so the worker's `_project_root` is
   the IP scratch, not `common_ai_agent`. This bounds the F1 fallback.
4. **Pre-flight `WORKER_URL_*` sanity check.** Before a long pipeline,
   `curl http://localhost:<port>/health` and confirm the `worker_name`
   matches the workflow you expect. The worker does not enforce F3, so the
   caller must.
5. **Do not run two real-LLM `ssot-gen` jobs on the same provider account
   in parallel.** F4 is purely operational — serialize, or split across
   `gpt-5.3-codex` / `claude-cli` / `cursor-cli` / `glm-5.1` so the unified
   exec budget is not exhausted.
6. **Pin scratch ports per IP in run docs.** Each reference-run wiki page
   (e.g. [[gpio-orchestrator-multiworker-run]],
   [[mini-cpu-rerun-20260517]]) should record the exact ports/sessions the
   run used. Cross-IP reuse becomes visible at write time.

## Why It Cannot Be Fully Prevented Yet

The target design in [[orchestrator-worker-handoff]] requires:

- per-user orchestrator
- `pipeline_run_id` as a durable DB key
- per-worker `capacity_group` and `lease_id`
- gateway/router in front of multi-worker fleet
- per-lease scope on every write (artifact, log, decision, handoff)

None of those are shipped. The audit in
[[orchestrator-worker-handoff-review]] records `pipeline_run_id`, leases,
and per-user orchestrator as TODO. Until they ship, the **discipline lives in
the caller**, not in the worker. F1 can be reduced but not closed.

## Recommended Tracker Items

Treat these as the gating fixes that turn the operational discipline into
structural prevention:

- worker `/run` should reject requests whose `workflow` does not match the
  worker's startup binding (closes F3).
- worker `/run` should refuse requests with empty `project_root` and require
  the caller to pass an absolute root (closes F1).
- `worker_registry.json` and `agent_runs.json` should be partitioned by
  `pipeline_run_id` or at minimum by `(session_name, project_root)` so
  per-IP history is recoverable after a worker restart (reduces F2).
- `WORKER_URL_*` resolution should be augmented with a capability handshake
  so the dispatcher can verify the binding before posting `/run` (defense
  in depth for F3).
- Provider quota guardrail: a process-level lock on real-LLM `ssot-gen` so
  two jobs against the same credential do not race the unified exec budget
  (closes F4 for the common case).

Until those land, treat shared worker ports the same way you treat shared
databases: assume that any unscoped write is a potential cross-tenant
contamination.
