---
title: ATLAS Pipeline Worker Workspace Jump
type: runbook
tags: [atlas-ui, pipeline, workspace, workflow, orchestrator, worker]
updated: 2026-05-18
related: [atlas-pipeline-screen, pl330-real-orchestrator-ui-lessons-20260517, orchestrator-worker-handoff, pipeline-progress-debugging, multi-user-worker-isolation, atlas-pipeline-db-state]
---

# ATLAS Pipeline Worker Workspace Jump

Pipeline worker details must be inspectable from the visible UI. When the user
clicks `ssot-gen`, `rtl-gen`, or `tb-gen` in the Pipeline worker row, ATLAS
should open that worker's real workspace so the user can see the chat history,
files, artifacts, and recent evidence created by that workflow.

Related: [[atlas-pipeline-screen]],
[[pl330-real-orchestrator-ui-lessons-20260517]],
[[orchestrator-worker-handoff]], [[pipeline-progress-debugging]],
[[multi-user-worker-isolation]], [[atlas-pipeline-db-state]]

## Product Rule

The right rail is still the Orchestrator chat. Users should not normally chat
directly with workers. Worker detail clicks are for inspection:

```text
Pipeline screen
  click ssot-gen / rtl-gen / tb-gen worker detail
    -> switch namespace to session_id/ip/workflow
    -> open Workspace screen
    -> show worker conversation.json / full_conversation.json
    -> open a representative artifact preview
```

This keeps the normal product path clean:

- user asks Orchestrator to make or repair an IP,
- Orchestrator dispatches worker commands,
- workers write artifacts and evidence,
- Pipeline shows status,
- worker detail click opens the worker workspace for audit/debug.

Do not treat this drilldown as permission to bypass Orchestrator for normal
work. It is an evidence and history viewer.

## User Flow

Starting from a live Pipeline URL such as:

```text
http://127.0.0.1:<port>/?backend=live&session=<user>%2F<ip>%2Forchestrator&ip=<ip>&workflow=orchestrator&session_id=<user>
```

1. Open `◫ Pipeline`.
2. Wait for `/api/pipeline/state?ip=<ip>` to populate the worker orchestra row.
3. Click one of the worker detail buttons:
   - `ssot-gen`
   - `rtl-gen`
   - `tb-gen`
4. ATLAS opens `⌂ Workspace` with the workflow combobox set to the clicked
   worker.
5. The active namespace must be:

```text
.session/<session_id>/<ip>/<workflow>
```

6. The Workspace file tree and preview should show that workflow's artifacts
   and conversation history.

Expected URL shape:

```text
...?session=<session_id>%2F<ip>%2Fssot-gen&ip=<ip>&workflow=ssot-gen&session_id=<session_id>
...?session=<session_id>%2F<ip>%2Frtl-gen&ip=<ip>&workflow=rtl-gen&session_id=<session_id>
...?session=<session_id>%2F<ip>%2Ftb-gen&ip=<ip>&workflow=tb-gen&session_id=<session_id>
```

## Representative Files

The click should open a useful first file instead of dropping the user into an
empty workspace:

| Workflow | Default preview |
|---|---|
| `ssot-gen` | `<ip>/yaml/<ip>.ssot.yaml` |
| `rtl-gen` | `<ip>/rtl/rtl_authoring_status.md` |
| `tb-gen` | `<ip>/tb/cocotb/test_<ip>.py` |

Stage cards may override this with their first evidence path when it is more
specific. The worker-row click uses the workflow default because it does not
always have stage evidence paths in hand.

## Frontend Wiring

Load-bearing code:

- `frontend/atlas/pipeline.jsx`
- `frontend/atlas/app.jsx`

Pipeline owns the workflow/stage mapping:

```text
PIPELINE_STAGE_WORKFLOW
  ssot -> ssot-gen
  rtl  -> rtl-gen
  tb   -> tb-gen

PIPELINE_WORKSPACE_WORKFLOWS
  ssot-gen, rtl-gen, tb-gen

PIPELINE_WORKFLOW_PRIMARY_STAGE
  ssot-gen -> ssot
  rtl-gen  -> rtl
  tb-gen   -> tb
```

Pipeline helpers:

- `pipelineWorkflowForStage(stageId)` maps stage IDs to workflow names.
- `pipelineDefaultWorkspacePath(ip, workflow, stageId, evidencePaths)` chooses
  the initial file preview.
- `openPipelineWorkflowWorkspace({ip, workflow, stageId, path})` dispatches
  `atlas:open_workflow_workspace`.

`WorkerOrchestraBar` behavior:

- for `ssot-gen`, `rtl-gen`, `tb-gen`, click opens the workflow workspace;
- for other workflows, existing target-selection behavior is preserved;
- the button tooltip should say it opens workspace/history, not just chat
  target selection.

`StageCard` behavior:

- `ssot`, `rtl`, and `tb` stage cards expose a `⌂ workspace` button;
- the button opens the same workflow workspace event;
- if `evidence_paths[]` exists, the preview path can come from evidence.

## App-Level Event Handling

`frontend/atlas/app.jsx` handles:

```text
atlas:open_workflow_workspace
```

Required behavior:

1. Normalize `workflow`.
2. If the current agent is running, call the same workflow-switch guard used by
   the workflow selector.
3. Resolve owner/session and IP from, in order:
   - event detail,
   - active namespace,
   - active session/IP state,
   - browser/user defaults.
4. Call:

```text
activateNamespace(owner, ip, workflow, true)
setScreen('workspace')
```

5. If a preview path is present:
   - store `localStorage.atlasPreviewPath`,
   - dispatch `atlas-chip-open` with the path.

Important bug fix: leaving `pipeline` normally may reset the workflow to
`default`. A deliberate worker workspace jump must set a guard flag so the
pipeline/architect screen-exit effect does not overwrite the target workflow.
Without this guard, clicking `ssot-gen` can momentarily route correctly and
then land in `workflow=default`.

## Verification Runbook

Use the visible in-app browser for this check. Product-flow claims should match
the path users see, per [[pipeline-progress-debugging]].

1. Open the live Pipeline URL for a real IP.
2. Confirm worker cards exist. If the page initially shows `Full IP pipeline
   0/11`, wait for the live poll to refresh before clicking.
3. Click `ssot-gen`.
4. Verify:
   - URL has `workflow=ssot-gen`;
   - active namespace is `.session/<user>/<ip>/ssot-gen`;
   - workflow combobox selected `ssot-gen`;
   - Workspace shows `conversation.json` / full history controls;
   - full view opens `<ip>/yaml/<ip>.ssot.yaml`.
5. Return to Pipeline and repeat for `rtl-gen`.
6. Verify full view opens `<ip>/rtl/rtl_authoring_status.md`.
7. Return to Pipeline and repeat for `tb-gen`.
8. Verify full view opens `<ip>/tb/cocotb/test_<ip>.py`.

Observed good PL330 validation on 2026-05-18:

```text
ssot-gen -> .session/codexadmin/pl330realverify/ssot-gen
           Full view: pl330realverify/yaml/pl330realverify.ssot.yaml

rtl-gen  -> .session/codexadmin/pl330realverify/rtl-gen
           Full view: pl330realverify/rtl/rtl_authoring_status.md

tb-gen   -> .session/codexadmin/pl330realverify/tb-gen
           Full view: pl330realverify/tb/cocotb/test_pl330realverify.py
```

Code-level checks:

```bash
node - <<'NODE'
const fs = require('fs');
const acorn = require('acorn');
const jsx = require('acorn-jsx');
const Parser = acorn.Parser.extend(jsx());
for (const file of ['frontend/atlas/pipeline.jsx', 'frontend/atlas/app.jsx']) {
  Parser.parse(fs.readFileSync(file, 'utf8'), {
    ecmaVersion: 'latest',
    sourceType: 'script',
    allowReturnOutsideFunction: true,
  });
  console.log(`${file}: parse ok`);
}
NODE

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_api_pipeline_state.py::test_pipeline_state_summarizes_nested_junit_testsuites \
  tests/test_pipeline_orchestrator_worker_integration.py::test_orchestrator_worker_status_exposes_default_model_bindings \
  -q
```

Expected:

```text
frontend/atlas/pipeline.jsx: parse ok
frontend/atlas/app.jsx: parse ok
2 passed
```

## Failure Modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Click lands in `workflow=default` | pipeline/architect exit fallback reset the workflow | keep the explicit workspace-jump guard in `app.jsx` |
| Worker cards missing after opening Pipeline | live state poll has not populated yet | wait for worker row or inspect `/api/pipeline/state?ip=<ip>` |
| Preview opens old file | `atlasPreviewPath` is stale or `atlas-chip-open` did not fire | send preview path in `atlas:open_workflow_workspace` and dispatch `atlas-chip-open` after screen switch |
| `tb-gen` click fails during refresh | DOM re-mounted while pipeline state updated | re-snapshot and click the fresh worker button |
| User starts chatting in worker workspace | product path is unclear | keep right rail Orchestrator-first; document worker workspace as inspect/debug only |

## Design Boundary

This feature intentionally covers only `ssot-gen`, `rtl-gen`, and `tb-gen`
because those are the highest-value authoring workspaces with rich conversation
and artifact history. Extending the same pattern to `sim_debug`, `lint`, or
`coverage` is possible, but should choose workflow-specific preview files first
so users land on reports rather than arbitrary directories.
