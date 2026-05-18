---
title: ATCDMAC100 Document Flow UI Honesty 2026-05-18
type: run
tags: [atcdmac100, atlas-ui, orchestrator, pdf-import, dma, signoff, evidence, honesty]
updated: 2026-05-18
related: [atlas-browser-control-runbook, pipeline-progress-debugging, orchestrator-worker-handoff, full-flow-pipeline, pl330-real-orchestrator-ui-lessons-20260517, atlas-pipeline-screen]
---

# ATCDMAC100 Document Flow UI Honesty 2026-05-18

Corrective run record for the Andes ATCDMAC100 DMA controller flow started from
`AndeShape_ATCDMAC100_DS079_V1.2.pdf`. This page intentionally records both the
technical artifact state and the process mistake: the visible ATLAS UI was open,
but most work was executed through backend workflow scripts instead of by typing
into the right-side Orchestrator chat and letting the UI dispatch workers.

Related: [[atlas-browser-control-runbook]], [[pipeline-progress-debugging]],
[[orchestrator-worker-handoff]], [[full-flow-pipeline]],
[[pl330-real-orchestrator-ui-lessons-20260517]], [[atlas-pipeline-screen]].

## Snapshot

| Item | Value |
|---|---|
| IP | `atcdmac100` |
| Source document | `/Users/brian/Desktop/andes/platform/AE210P_20161118/DOCS/AndeShape_ATCDMAC100_DS079_V1.2.pdf` |
| Visible ATLAS URL | `http://127.0.0.1:62196/?backend=live&session=codexadmin%2Fatcdmac100%2Forchestrator&ip=atcdmac100&workflow=orchestrator&session_id=codexadmin` |
| Document authority copied into IP | `atcdmac100/req/source/ATCDMAC100_DS079_V1_2_extracted.md` |
| PDF SHA256 | `009859054f1992b6c64ec7e4e09402aad1b2ee21558c6c3cce48d91a4b231ac9` |
| Extracted MD SHA256 | `da27defb17f2d88b340be4fa4a12af3d7cd25499daef199cef118a02280524c1` |
| Requirements SHA256 | `828df834b0bdb8790fb07a1995ea72931729f06045c7862b8bc023448ad8f27c` |
| Product-flow authority | **Not proven**. UI was visible, but backend scripts performed the flow. |

## What Actually Happened

The operator opened the ATLAS browser on the `atcdmac100` orchestrator session
and then used backend workflow/script execution to force the IP through the
common engine. This produced real artifacts, but it did not prove that the
right-side Orchestrator chat can drive the same document-based flow end to end.

Process truth:

- Real artifact generation happened.
- Real compile/lint/sim/coverage/syn/sta evidence was produced.
- The browser was not the primary execution surface for those stages.
- The Orchestrator chat did not own the PDF ingestion, stage decisions, worker
  dispatch, or repair loop for this run.
- PnR was started through the backend flow and was manually stopped after the
  user challenged the UI/process mismatch.

Therefore this run is useful as a backend/common-engine evidence run, not as a
valid ATLAS UI Orchestrator product-flow proof.

## Artifact State

### Requirements And SSOT

Artifacts:

- `atcdmac100/req/atcdmac100_requirements.md`
- `atcdmac100/req/approval_manifest.json`
- `atcdmac100/req/source/ATCDMAC100_DS079_V1_2_extracted.md`
- `atcdmac100/yaml/atcdmac100.ssot.yaml`
- `atcdmac100/yaml/atcdmac100.ssot.provenance.json`

The SSOT models ATCDMAC100 as an AHB slave register block plus an AHB master DMA
engine with eight channels and sixteen DMA request/ack lines. Key visible
interfaces include `hclk/hresetn`, `dma_int/dma_req/dma_ack`, AHB slave signals
such as `haddr/htrans/hwrite/hsize/hburst/hwdata/hsel/hreadyin/hrdata/hresp`,
and AHB master signals such as
`haddr_mst/htrans_mst/hwrite_mst/hsize_mst/hprot_mst/hlock_mst/hburst_mst/hwdata_mst/hrdata_mst/hresp_mst/hready_mst/hbusreq_mst/hgrant_mst`.

Key register groups captured from the document include `IdRev`, `DMACfg`,
`DMACtrl`, `IntStatus`, `ChEN`, `ChAbort`, `ChnCtrl`, `ChnSrcAddr`,
`ChnDstAddr`, `ChnTranSize`, and `ChnLLPointer`.

### Models, RTL, Lint

Artifacts:

- `atcdmac100/model/functional_model.py`
- `atcdmac100/model/cycle_model.py`
- `atcdmac100/verify/equivalence_goals.json`
- `atcdmac100/rtl/atcdmac100_core.sv`
- `atcdmac100/rtl/atcdmac100.sv`
- `atcdmac100/list/atcdmac100.f`
- `atcdmac100/rtl/rtl_compile.json`
- `atcdmac100/lint/dut_lint.json`

Backend evidence:

- RTL compile: `returncode=0`, `errors=0`, `passed=true`
- Lint: `returncode=0`, `errors=0`, `warnings=0`, `passed=true`
- Lint toolchain target: pyslang + verilator

Important local RTL/TB repair that happened during backend execution:

- Added `HTRANS_SEQ = 2'b11` and used it for the AHB master write data beat so
  the RTL matched the FL write-beat expectation.
- Kept terminal `dma_ack_q` observable in handshake mode so terminal interrupt
  and ACK could be seen together.
- Extended the cocotb TB to resolve internal `u_core` signals for source and
  waveform tracking without treating the VCD dump wrapper as the design top.

### TB, Sim, Coverage, Debug, Audit

Artifacts:

- `atcdmac100/tb/cocotb/test_atcdmac100.py`
- `atcdmac100/sim/results.xml`
- `atcdmac100/sim/scoreboard_events.jsonl`
- `atcdmac100/sim/atcdmac100.vcd`
- `atcdmac100/sim/fl_rtl_compare.json`
- `atcdmac100/sim/mismatch_classification.json`
- `atcdmac100/cov/coverage.json`
- `atcdmac100/sim/fl_rtl_goal_audit.json`

Backend evidence:

```text
Simulation: TESTS=1 PASS=1 FAIL=0, 0 errors, 0 warnings
FL-vs-RTL: status=pass, goals_checked=62, goals_passed=62, goals_failed=0
Coverage: status=pass, functional=60/60, pct=100.0
Goal audit: status=pass, total_checks=16, passed_checks=16, failed_checks=0
```

### EDA Signoff

Artifacts:

- `atcdmac100/syn/out/synth.v`
- `atcdmac100/syn/out/syn.report.md`
- `atcdmac100/syn/out/area.json`
- `atcdmac100/sta/out/atcdmac100.sdc`
- `atcdmac100/sta/out/sta.report.md`
- `atcdmac100/sta/out/wns.json`
- `atcdmac100/pnr/out/floorplan.def`
- `atcdmac100/pnr/out/placed.def`
- `atcdmac100/pnr/out/cts.def`
- `atcdmac100/pnr/out/cts.v`

Synthesis result:

```text
top=atcdmac100
corner=sky130_fd_sc_hd__ss_100C_1v40.lib
cells=8622
sequential=1524
combinational=7098
area=69900.0 um2
warnings=none in syn.report.md
```

STA result:

```text
result=SETUP FAIL
clock=hclk
period=10.0 ns
setup WNS=-22.560 ns
setup TNS=-112.300 ns
setup violations=5
hold WNS=1.170 ns
hold violations=0
```

PnR state:

- Floorplan completed.
- Placement completed.
- CTS completed.
- Route started and reached detailed router pin-access processing.
- Route was stopped after the user challenged the fact that the flow was being
  driven by backend scripts rather than ATLAS UI Orchestrator chat.

Do not mark `pnr` or `sta-post` green from this run.

## Could Orchestrator Have Done This?

Short answer: **partly yes with the current implementation, but not the full
document-requirement flow exactly as the user intended without tightening the
UI path.**

What exists today:

- `src/atlas_api_jobs.py` exposes `/api/pipeline/orchestrator/chat`.
- That route parses phrases like `run to green`, `pipeline`, `만들`, and `생성`
  into the full pipeline stage list.
- It creates jobs with `pipeline_run_id`, `session`, `user_id`, `ip`, workflow,
  stage id, dependency order, run mode, and exec mode.
- It records `chat_message`, `chat_response`, and `workflow_dispatch` events in
  the DB.
- It uses worker model defaults such as:
  - orchestrator: `gpt-5.5`
  - ssot-gen: `gpt-5.5`
  - rtl-gen: `gpt-5.3-codex`
  - tb-gen: `deepseek`
  - sim_debug: `kimi`
  - lint: `deepseek`
  - syn/sta/pnr/sta-post: `gpt-5.3-codex`
- Regression tests prove the route can dispatch all stages and preserve
  `user/ip/pipeline_run_id` identity, but those tests use mock workers.

What is not enough yet:

- The `/api/pipeline/orchestrator/chat` route is mostly deterministic
  stage-selection and job creation. It is not itself a long-running LLM
  Orchestrator reasoning loop over the PDF.
- The chat route does not automatically read the PDF path, extract the manual,
  and pass document provenance to `ssot-gen` unless that is already implemented
  by the worker prompt/payload or preloaded IP context.
- A product-flow proof must show the right-side chat input causing worker
  dispatch in the visible UI, then stage evidence appearing through
  `/api/pipeline/state` and the Pipeline graph.
- If a worker URL is missing, the correct behavior is durable handoff/review,
  not shell execution by the operator.
- EDA stages can legitimately fail; this run's pre-route STA has real setup
  failure and must route back to RTL/SSOT/timing-constraint ownership.

So for this exact request, the honest answer is:

```text
Current ATLAS can dispatch an ATCDMAC100 full pipeline through Orchestrator chat
if live workers are registered and the document requirement has been made
available to the SSOT worker.

It was not proven in this run, because the operator bypassed that path with
backend scripts.
```

## Correct Protocol For The Next UI Proof

Use this protocol when the user says "ATLAS UI로 해줘" or "나도 보게":

1. Open the visible ATLAS URL in the in-app Browser.
2. Select or create a fresh IP, for example `atcdmac100_ui_real`.
3. In the right-side Orchestrator chat, type the real goal, including the PDF
   path:

   ```text
   Create ATCDMAC100 from /Users/brian/Desktop/andes/platform/AE210P_20161118/DOCS/AndeShape_ATCDMAC100_DS079_V1.2.pdf and run the engineering full pipeline through workers. Do not pass a stage without evidence.
   ```

4. Verify the chat route returns `action=dispatch` and a `pipeline_run_id`.
5. Watch the Pipeline screen and `/api/pipeline/state?ip=<ip>` for real stage
   transitions.
6. Click worker cards to inspect their workspaces. Do not chat with workers
   directly unless the Orchestrator explicitly routes there.
7. Do not run workflow scripts manually to advance the flow. Shell is allowed
   only for read-only diagnostics, cleanup of already-started processes, or
   source-code fixes requested by the user.
8. If a worker cannot proceed, record the handoff or QA card and stop at the
   visible blocker.
9. A stage is green only when the Pipeline state and artifact evidence agree.

## Lessons

- A visible browser tab is not enough. The execution path must be the same
  Orchestrator chat and worker dispatch path the user sees.
- Backend/common-engine runs are valuable for debugging, but they are not UI
  product-flow proof.
- "All flow with document requirement" must bind the source document to the
  SSOT worker as provenance, not silently let the operator extract and patch
  requirements by hand.
- PnR/STA results must be reported honestly. Artifact existence is not pass:
  `sta.report.md` says setup fail at `hclk@10ns`, and route/post-route STA were
  not completed in this run.
- Future agents should cite this page before claiming that ATLAS UI
  Orchestrator can complete a PDF-to-signoff DMA flow.
