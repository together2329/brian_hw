---
title: PL330 Real Orchestrator UI Lessons 2026-05-17
type: run
tags: [atlas-ui, orchestrator, pl330, rtl-gen, multi-worker, debugging, real-llm]
updated: 2026-05-17
related: [orchestrator-workflow-bring-up-20260517, orchestrator-worker-handoff, pipeline-progress-debugging, multi-user-worker-isolation, multi-user-worker-conflicts, full-flow-pipeline, rtl-gen-ssot-contract, atlas-pipeline-screen, atlas-pipeline-worker-workspace-jump, atlas-pipeline-db-state, round2-retry-budget-cross-workflow-routing-20260517]
---

# PL330 Real Orchestrator UI Lessons 2026-05-17

Real-use debugging record for the `pl330realverify` ATLAS UI run. This page
captures the mistakes that only became visible when the user watched the UI and
insisted on real Orchestrator + worker execution rather than headless shortcuts
or mock progress.

Related: [[orchestrator-workflow-bring-up-20260517]],
[[orchestrator-worker-handoff]], [[pipeline-progress-debugging]],
[[multi-user-worker-isolation]], [[multi-user-worker-conflicts]],
[[full-flow-pipeline]], [[rtl-gen-ssot-contract]],
[[atlas-pipeline-screen]], [[atlas-pipeline-worker-workspace-jump]],
[[atlas-pipeline-db-state]],
[[round2-retry-budget-cross-workflow-routing-20260517]]

## Run Snapshot

| Item | Value |
|---|---|
| IP | `pl330realverify` |
| Visible UI | `http://127.0.0.1:62196/?backend=live&session=codexadmin%2Fpl330realverify%2Forchestrator&ip=pl330realverify&workflow=orchestrator&session_id=codexadmin` |
| Product authority | ATLAS UI/API/worker path, not manual file creation |
| Orchestrator | `gpt-5.5`, `xhigh` |
| Main RTL worker | `rtl-gen` on `http://127.0.0.1:5623`, `gpt-5.3-codex` |
| Lint worker | `lint` on `http://127.0.0.1:5624`, `deepseek-v4-pro` |
| Other live workers | `ssot-gen:5621`, `fl-model-gen:5622`, `tb-gen:5625`, `sim:5626`, `coverage:5627`, `sim_debug:5628`, `syn:5629`, `sta:5630`, `pnr:5631`, `sta-post:5632` |
| UI status after RTL/LINT | `SSOT / FL / CL / EQUIV / RTL / LINT` passed; `SIM/COV/DBG` locked |
| Contaminated status | `TB` showed failed because a human/operator status probe accidentally dispatched `tb-gen` and the run was immediately cancelled |

Evidence paths:

- `pl330realverify/yaml/pl330realverify.ssot.yaml`
- `pl330realverify/model/functional_model.py`
- `pl330realverify/model/cycle_model.py`
- `pl330realverify/verify/equivalence_goals.json`
- `pl330realverify/rtl/*.sv`
- `pl330realverify/list/pl330realverify.f`
- `pl330realverify/rtl/rtl_compile.json`
- `pl330realverify/lint/dut_lint.json`
- `pl330realverify/rtl/rtl_authoring_provenance.json`
- `pl330realverify/orchestrator/trace.jsonl`

## What Went Wrong

### 1. "Are you really using the browser?"

The user could not see shell-only or headless actions and correctly challenged
whether the UI was actually being used. For explicit Browser/plugin requests,
use the in-app Browser skill and inspect the live tab. Do not substitute macOS
`open`, generic web search, or a headless-only run. Product-flow claims need
the same visible UI/API/worker path described in [[pipeline-progress-debugging]].

Practical rule:

```text
If the user says "ATLAS UI / web browser / I want to see it":
  open the actual localhost URL in the in-app browser,
  verify DOM/API state,
  and cite the visible URL plus backend evidence.
```

### 2. "This looks like a fake mock"

The UI can look credible while only showing staged state or synthetic progress.
The real proof is the worker contract:

- `/api/pipeline/state?ip=<ip>` shows stage evidence.
- Worker `/health` shows real workflow/model binding and active runs.
- `orchestrator/trace.jsonl` shows dispatches and completions.
- Canonical artifact JSONs prove outputs: compile, lint, provenance, coverage,
  sim, or debug reports.

For this run, RTL was real because `rtl-gen` produced SystemVerilog files,
`rtl_compile.json` returned `returncode=0`, and `dut_lint.json` returned
`pyslang` and `verilator` pass results. It was not full signoff, because the
RTL TODO audit still had open required items.

### 3. User Should Talk To Orchestrator, Not Workers

The desired product shape is:

```text
User -> right-side Orchestrator chat
Orchestrator -> worker dispatches
Workers -> artifacts + evidence + trace
UI -> stage cards, graph, evidence, handoff status
```

Direct `curl` or shell commands are allowed for operator debugging, but they are
not the user-facing product path. When validating UX, drive the Orchestrator
chat and then use API/worker state only as evidence.

### 4. RTL Should Receive `/ssot-rtl`, Not A Giant TODO Payload

The biggest product lesson from the loading discussion: `rtl-gen` should not
receive a large preloaded `ssot-rtl` TODO template over HTTP. RTL owns a dynamic
ledger that can contain hundreds of SSOT-derived tasks. The right handoff is a
small command:

```text
Orchestrator -> rtl-gen: /ssot-rtl <ip>
rtl-gen -> disk: read SSOT, FL/CL/equiv, rtl_todo_plan, authoring packets
rtl-gen -> output: RTL files, filelist, compile/lint reports, provenance
```

This avoids confusing two different TODO concepts:

- Workflow TODO ledger: durable SSOT-derived RTL IDs such as `RTL-XXXX`.
- Agent session TODOs: transient working memory inside one LLM loop.

The UI can still show the RTL ledger, but the network handoff should be the
command and scoped IP, not a copy of the ledger.

Code change tied to this lesson:

- `src/atlas_api_jobs.py` now returns no default TODO template for
  `workflow == "rtl-gen"` or `stage_id == "rtl"`.
- `src/workflow_stage_surface.py` now emits `/ssot-rtl <ip>` before the RTL
  instruction block.

### 5. Loading Was Also A Duplicate Dispatch Risk

The Orchestrator chat and pipeline buttons could create duplicate jobs for the
same `user/ip/stage/workflow` while an earlier job was still
`pending`, `queued`, or `running`. In the UI this looks like loading or like
the wrong worker is still active. In a multi-user system it can also mix status
across IPs if the job scope is not explicit.

Fix pattern:

```text
Before dispatch:
  refresh tracked jobs,
  find active jobs scoped by user_id/db_user_id + ip + stage/workflow,
  return {deduped: true, status: "already_running", existing_jobs: [...]}
  instead of launching a new worker run.
```

Code paths now covered by the dedupe guard:

- `/api/job/dispatch`
- `/api/jobs/dispatch_many`
- `/api/pipeline/dispatch`
- `/api/pipeline/orchestrator/chat`
- `dispatch_workflow` tool bridge

Regression test:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_orchestrator_chat_dedupes_active_ip_stage -q
```

Expected: `1 passed`.

### 6. "Completed" Must Mean Produced Evidence

Earlier worker runs could report success even when a model only talked and did
not write files. The same family appeared in
[[round2-retry-budget-cross-workflow-routing-20260517]]. For this run we also
hardened file-write accounting so textual ReAct actions and tool observations
like `wrote <path>` count toward production evidence.

Code change:

- `core/agent_server.py` now records files from native tool calls, textual
  `Action: write_file(...)` / `replace_file(...)`, and tool output text.

### 7. KPI Readers Must Match Report Schema

The UI RTL compile dot looked wrong because the report writer used
`returncode`, while the KPI reader looked for `rc` / `return_code`.

Code change:

- `src/workflow_stage_surface.py` now reads `returncode` too.

### 8. Artifact Recovery Should Repair Missing Filelist/Provenance

RTL stage cards should not stay half-alive just because a worker wrote RTL but
missed the filelist or provenance sidecar. Artifact recovery now refreshes
`list/<ip>.f` and `rtl/rtl_authoring_provenance.json` once for RTL jobs when
they are missing.

Code change:

- `src/atlas_api_jobs.py` adds RTL provenance/filelist recovery through
  `HeadlessWorkflowRunner._refresh_rtl_filelist_and_provenance(ip)`.

### 9. Accidental Operator Dispatch Can Pollute The UI

While checking Orchestrator status, a plain `status?` message was interpreted
as a next-stage request and dispatched `tb-gen`. The run was cancelled
immediately, but the UI still showed `TB failed`.

Do not read that status as "TB proved bad." It means "operator misfire was
cancelled and the stage card retained a failed/cancelled trace." The UI should
eventually distinguish:

- worker failed by evidence,
- operator cancelled,
- duplicate dispatch suppressed,
- stage not yet attempted.

## Verification From This Run

RTL compile:

```bash
python3 workflow/rtl-gen/scripts/rtl_compile_report.py \
  pl330realverify --top pl330realverify --project-root .
```

Observed:

```text
[rtl_compile_report] iverilog: errors=0 diagnostics=0 style_violations=0 returncode=0
```

Lint:

```bash
python3 workflow/lint/scripts/dut_lint_report.py \
  pl330realverify --top pl330realverify
```

Observed:

```text
[dut_lint_report] pyslang+verilator: errors=0 warnings=0 suppression_violations=0 style_violations=0 returncode=0
pyslang errors=0 warnings=0 returncode=0
verilator errors=0 warnings=0 returncode=0
```

RTL audit:

```bash
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py \
  pl330realverify --root . --audit-rtl
```

Observed: `gate=fail` with open required TODOs. This is the important
distinction: compile/lint/provenance were good enough for the RTL UI card to
show progress, but production RTL signoff was not complete.

Targeted test for the dispatch race:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_orchestrator_chat_dedupes_active_ip_stage -q
```

Observed: `1 passed`.

Known unrelated test environment issue:

- Running pytest without `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` can fail because an
  old `pytest_pymtl3` plugin registers the removed `pytest_cmdline_preparse`
  hook.
- A broader orchestrator integration test still fails because its mock SSOT is
  too small for the current strict `check_ssot_disk.sh` evidence contract.

## Operational Runbook For The Next Session

1. Open the live ATLAS URL in the in-app browser when the user wants to see the
   run.
2. Confirm the URL contains the intended `session_id`, `ip`, and `workflow`.
3. Check worker health for the bound model and no stale active runs.
4. Drive the right-side Orchestrator chat, not direct worker chat.
5. For RTL handoff, tell Orchestrator to dispatch `/ssot-rtl <ip>` to
   `rtl-gen`; do not preload a TODO template.
6. If the UI says loading, check active scoped jobs first. If a job exists,
   surface the existing job instead of dispatching another.
7. After RTL, verify compile, lint, filelist, provenance, and TODO audit
   separately. Do not equate compile/lint pass with full RTL signoff.
8. If a stage card unexpectedly shows failed, inspect whether it is a true
   evidence failure, cancelled operator action, duplicate suppression, or stale
   DB state.

## Follow-Up Improvements

- Keep worker detail clicks audit-oriented: `ssot-gen`, `rtl-gen`, and
  `tb-gen` should open the real workflow workspace/history/artifacts, not switch
  normal user chat away from Orchestrator. The implemented pattern and
  validation checklist are in [[atlas-pipeline-worker-workspace-jump]].
- Surface `deduped: true` as a clear UI state: "already running" with the
  existing job ID and worker model.
- Preserve cancelled operator runs as `cancelled`, not generic `failed`, so
  stage cards do not look like real evidence failures.
- Show worker command handoff in the Orchestrator trace, especially
  `/ssot-rtl <ip>`.
- Add an Orchestrator chat guard for ambiguous status messages so `status?`
  does not dispatch the next stage.
- Add a compact real-evidence drawer per stage: worker model, run ID,
  artifact paths, report timestamps, and pass/fail reason.
- Keep DB scope visible everywhere: `user_id`, `session_id`, `ip_id`,
  `workflow`, `pipeline_run_id`.
