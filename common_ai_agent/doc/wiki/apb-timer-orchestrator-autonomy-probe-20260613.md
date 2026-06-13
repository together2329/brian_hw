# APB Timer Orchestrator Autonomy Probe (2026-06-13)

Goal: exercise the orchestrator as if a user asked for a moderately realistic
IP: APB slave timer with `pclk`/active-low reset, PWM output, and interrupt
pending/W1C behavior.

This probe did not reach RTL/FL/TB validation. The blocker is earlier: the
execution/observability layer failed before `ssot-gen` produced a real SSOT.

Related: [[orchestrator-campaign-10ip-20260610]], [[pipeline-progress-debugging]],
[[atlas-worker-workflow-ui-sync-20260610]].

## IP Under Test

Path:
`/Users/brian/Desktop/Project/NEW_WORKSPACE/admin/default/apb_timer_pwm_irq_v1`

Locked user intent:

- APB signals: `pclk`, `presetn`, `psel`, `penable`, `pwrite`, `paddr`,
  `pwdata`, `prdata`, `pready`, `pslverr`.
- Registers: `CTRL`, `PRESCALE`, `PERIOD`, `DUTY`, `COUNT`, `STATUS`.
- Timer wraps on `PERIOD-1`, sets `irq_pending`, and supports W1C clear.
- PWM is high when enabled and `COUNT < min(DUTY, PERIOD)`.
- Illegal APB accesses assert `pslverr`, ignore writes, and read zero.

Durable IP memory exists at:
`apb_timer_pwm_irq_v1/wiki/llm_memory.md`.

## Timeline And Evidence

### 1. Requirement Lock Succeeded

`scripts/orch_campaign_truth.py` produced the locked truth bundle under
`req/`. IP-local snapshot:

- `2a7a78a req: lock APB timer PWM IRQ truth`

This means the failure below is not caused by missing user requirements.

### 2. Standalone Orchestrator Probe Failed Before Dispatch

Run id:
`3f01f5e112ff4446b05820dc7984617e`

Model:
`gpt-5.5`, low effort.

Trace:

```text
status=tool_failed model=gpt-5.5 steps=2
000 read_pipeline_state [FAILED]
    error: parent read_pipeline_state bridge unavailable
001 dispatch_workflow ssot-gen [NO JOB] [FAILED]
    error: parent dispatch_workflow bridge unavailable
```

Diagnosis:

The standalone supervisor path can start a run, but its IPC bridge expects
parent callbacks for `read_pipeline_state` and `dispatch_workflow`. Those
callbacks are registered by the Atlas API/server path, not by this standalone
launcher. Therefore the orchestrator can reason, but it cannot inspect or
dispatch pipeline jobs in this context.

This is a launcher/bridge contract gap, not an APB timer IP gap.

Preferred fix:

- Do not duplicate dispatch logic.
- Reuse the existing `core.tools.dispatch_workflow()` and
  `core.tools.read_pipeline_state()` fallback paths when the IPC callback is
  absent, or register the same callbacks in the standalone supervisor launcher.
- Keep Atlas UI and CLI on the same trace/dispatch semantics.

### 3. Headless Fallback Entered A Stuck LLM Call

Because standalone orchestrator dispatch failed, `ssot-gen` was tried directly
through `src.headless_workflow`.

Attempts:

- `gpt-5.5`: reached `llm_call_start`; no `llm_call_end`.
- `gpt-5.4`: reached `llm_call_start`; no `llm_call_end`.

Observed progress:

```json
{"event":"llm_call_start","stage":"ssot-gen","model":"gpt-5.4",
 "prompt_chars":13577,"system_prompt_chars":69328}
```

Heartbeat:

```json
{"state":"running","phase":"llm_call","stage":"ssot-gen","model":"gpt-5.4"}
```

`src.progress_debug` correctly diagnoses this as:

```text
diagnosis: stuck_llm_call (warning)
ssot-gen is still inside LLM call; no llm_call_end event or LLM log artifact yet.
```

But that diagnosis is not yet promoted into the orchestrator/UI run state, so
an operator sees "running" and cannot tell whether to wait or intervene.

### 4. SSOT Artifact Is Only A Stub

The current SSOT file exists but is not a real result:

```text
yaml/apb_timer_pwm_irq_v1.ssot.yaml
line count: 1
content: ip: apb_timer_pwm_irq_v1
```

Quality check:

- ports: 0
- transactions: 0
- state variables: none
- features: 0

So no downstream RTL/FL/TB conclusion should be drawn from this probe.

## Problem Summary

The current failure is not "APB timer is too hard". It is:

1. **Standalone orchestrator bridge gap**: CLI-launched supervisor lacks the
   parent callbacks that Atlas server mode registers, so tools fail before any
   worker job is created.
2. **Headless long-call observability gap**: `headless_workflow` writes one
   heartbeat before `llm_provider.complete()` and then goes silent until the
   provider returns. A long or hung provider call looks like "running".
3. **Status fidelity gap**: a stub `ssot.yaml` can exist while the stage has
   not produced a meaningful SSOT. Status surfaces must distinguish "artifact
   file exists" from "artifact passes minimal content contract".

## Recommended Next Work

1. Fix standalone supervisor dispatch by wiring the bridge to existing
   `core.tools` fallback behavior or registering callbacks in the CLI launcher.
2. Surface `src.progress_debug.summarize_headless_progress()` in the shared
   trace/API/UI path so `stuck_llm_call` becomes visible where the operator is
   already watching.
3. Add a terminal policy for stale active LLM calls: after a configured
   threshold, mark the stage/job as blocked with model, prompt size, elapsed
   seconds, and missing `llm_call_end` evidence.
4. Make status panels show "stub/no semantic SSOT" separately from "SSOT exists".

## Operator Rule

If the trace says `parent ... bridge unavailable`, do not wait: no worker job
was dispatched.

If progress says `stuck_llm_call` and the SSOT is a one-line stub, do not claim
IP failure: classify it as a runtime/observability blocker and retry only after
the bridge/heartbeat path is fixed.
