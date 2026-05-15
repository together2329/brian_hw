# AI-Driven IP Development Guide

This guide explains how common_ai_agent turns an IP idea into verified
artifacts through workflow-owned automation.

Audience:

- RTL designers who want the tool to drive implementation.
- DV engineers who want traceable FL/CL/TB/coverage evidence.
- Workflow developers who need to know where each responsibility lives.
- New users who need to run the flow without knowing internal scripts.

Design intent:

```text
One SSOT.
One workflow path.
Many LLM providers.
Evidence-based approval.
Human review only for real product/spec decisions.
```

## Mental Model

Think of the system like this:

```text
SSOT = contract
Workflow = factory line
LLM = worker
TodoTracker = work state machine
Validator/Audit = judge
Human review = spec authority
```

The LLM writes artifacts. It does not get final authority just because it says
"done". A todo becomes approved when the configured evidence passes, or when a
human explicitly approves a human-owned decision.

## End-To-End Flow

The target IP pipeline is:

```text
requirement
  -> ssot-gen
  -> fl-model-gen
  -> cl-model-gen
  -> rtl-gen
  -> tb-gen
  -> sim
  -> sim-debug
  -> lint
  -> coverage
  -> syn
  -> sta
  -> pnr
  -> post-sta
```

Not every project must run every stage on day one. The long-term goal is that
each stage consumes the previous approved evidence and emits its own approved
evidence.

## What Each Workflow Owns

| Workflow | Owns | Must not silently change |
| --- | --- | --- |
| `ssot-gen` | Canonical YAML SSOT, assumptions, workflow todos, human gates | RTL/TB/sim artifacts |
| `fl-model-gen` | FunctionalModel from `function_model`, FCOV plan, equivalence goals | SSOT semantics |
| `cl-model-gen` | Cycle model from `cycle_model`, latency/handshake/performance model | Function semantics |
| `rtl-gen` | RTL, filelist, RTL todo ledger, compile/lint/audit evidence | SSOT/FL/CL truth |
| `tb-gen` | TB, drivers, monitors, scoreboard, assertions, test manifest | SSOT coverage goals |
| `sim` | Running tests, pass/fail, scoreboard rows, waveform outputs | RTL/SSOT semantics |
| `sim-debug` | Failure triage, wave/source/hierarchy views, mismatch classification | Product intent |
| `lint` | DUT lint report, style/suppression checks | RTL function |
| `coverage` | Function coverage, cycle coverage, static trace coverage | Coverage goals without review |
| `syn` | Synthesis run/report | RTL behavior |
| `sta` | Pre-route timing analysis | Constraints without review |
| `pnr` | Place and route outputs | RTL behavior |
| `sta-post` | Post-route timing analysis | Constraints without review |

Hard rule:

```text
If downstream evidence fails, repair the owning downstream artifact or open a
human review item. Do not edit SSOT/FL/CL/coverage goals just to make a stage pass.
```

## Golden Todo Strategy

Every stage should have a golden todo ledger.

Current reference:

```text
<ip>/rtl/rtl_todo_plan.json
```

Future stage ledgers:

```text
<ip>/model/fl_todo_plan.json
<ip>/model/cl_todo_plan.json
<ip>/tb/tb_todo_plan.json
<ip>/sim/sim_todo_plan.json
<ip>/lint/lint_todo_plan.json
<ip>/cov/coverage_todo_plan.json
```

Todo ledger rule:

```text
The todo list is not a prompt checklist.
It is a contract between SSOT, generated artifacts, and evidence.
```

Each todo should know:

- `id`
- `content`
- `detail`
- `criteria`
- `source_refs`
- `owner_workflow`
- `owner_module` / `owner_file` when applicable
- `approval_policy`
- `required_evidence`
- `fallback_if_no_evidence`
- current `todo_completion`

Example:

```json
{
  "id": "RTL-0021",
  "content": "Implement result_valid one-cycle pulse",
  "source_refs": [
    "function_model.transactions.FM_ACCEPT",
    "cycle_model.latency.result_valid"
  ],
  "owner_workflow": "rtl-gen",
  "owner_file": "rtl/timer.sv",
  "approval_policy": "evidence_required",
  "required_evidence": [
    "rtl_compile",
    "dut_lint",
    "rtl_static_audit",
    "cycle_latency_check"
  ],
  "fallback_if_no_evidence": "human_review_needed"
}
```

## Approval Model

Default approval policy:

```text
evidence_required
```

Status flow:

```text
pending
  -> in_progress
  -> completed
  -> approval_requested
  -> approved | rejected | human_review_needed | blocked
```

Meaning:

- `completed`: the LLM produced the artifact or edit.
- `approval_requested`: the LLM claims criteria are met and explains why.
- `approved`: validator/audit or human authority accepted it.
- `rejected`: evidence says it is wrong or incomplete.
- `human_review_needed`: a human decision is needed; this is not failure.
- `blocked`: required upstream input or artifact is missing.

LLM reason is useful:

```text
"I implemented result_valid as a registered pulse after valid && ready."
```

Evidence is stronger:

```text
rtl_compile.json pass
dut_lint.json pass
rtl_todo_plan.json RTL-0021 pass
sim assertion accept_to_result_valid_1cycle pass
```

Rule:

```text
LLM reason explains the work.
Evidence approves the work.
Human review decides product/spec truth.
```

## Human Review Queue

Human review should be collected separately from rejected work.

Use `human_review_needed` for:

- undefined protocol choices;
- architecture tradeoffs;
- target frequency/area/power tradeoffs;
- security or safety policy;
- waiver requests;
- unreachable coverage bins;
- any proposal to change SSOT/FL/CL authority to make downstream pass.

Example review item:

```json
{
  "status": "human_review_needed",
  "decision_needed": "Choose DMA descriptor width",
  "source_refs": ["function_model.transactions.FM_DESCRIPTOR_FETCH"],
  "options": [
    {
      "label": "32-bit descriptor",
      "effect": "smaller RTL, limited address range"
    },
    {
      "label": "64-bit descriptor",
      "effect": "larger address range, wider datapath"
    }
  ],
  "recommended_default": {
    "label": "64-bit descriptor",
    "why": "More reusable for DMA-class IP"
  }
}
```

## FL, CL, And Coverage

FL and CL are not just model files. They define what coverage must prove.

```text
function_model -> function coverage
cycle_model    -> cycle coverage
RTL source     -> static implementation coverage
simulation     -> dynamic RTL-observed coverage
```

Function coverage answers:

```text
Did each function_model transaction happen in simulation, and did the
scoreboard compare expected vs actual?
```

Cycle coverage answers:

```text
Did each cycle_model latency, handshake, ordering, backpressure, depth,
outstanding, pipelining, frequency, and throughput target happen and pass?
```

Static coverage answers:

```text
Does RTL contain real implementation evidence for the SSOT ref?
```

Static coverage is not enough for signoff. It proves presence. Dynamic
coverage and checkers prove behavior.

Suggested coverage artifacts:

```text
cov/static_coverage.json
cov/function_coverage.json
cov/cycle_coverage.json
cov/coverage_traceability.json
```

## Provider Normalization

LLM providers are interchangeable only after normalization.

Provider adapters may differ:

```text
gpt/deepseek/glm/kimi API -> response text/json
cursor-cli                -> cursor-agent output/events
claude-cli                -> Claude result JSON plus possible hook noise
```

But workflow input should be normalized:

```json
{
  "schema_version": "workflow_artifact.v1",
  "workflow": "rtl-gen",
  "ip": "timer",
  "todo_id": "RTL-0021",
  "result": "completed",
  "files": [
    {
      "path": "timer/rtl/timer.sv",
      "kind": "rtl",
      "content": "..."
    }
  ],
  "claims": [
    "Implements function_model.transactions.FM_ACCEPT"
  ],
  "human_gate": null,
  "notes": []
}
```

Provider-specific code should stop at:

```text
raw provider output -> normalized artifact envelope
```

It should not decide whether a todo is approved.

## Multi-Agent Collaboration Model

The system should be able to run multiple specialized agents against the same IP
without losing authority, duplicating truth, or corrupting session state.

Collaboration rule:

```text
Agents share the SSOT and stage ledgers.
Agents do not share uncontrolled assumptions.
Agents hand off through artifacts, evidence, and review items.
```

### Agent Roles

| Agent | Primary job | Writes | Reads |
| --- | --- | --- | --- |
| Requirement/architect agent | Clarify intent, boundaries, tradeoffs | `req/`, review cards, SSOT decisions | prior docs, Q&A, user input |
| `ssot-gen` agent | Produce canonical SSOT | `yaml/<ip>.ssot.yaml` | requirements, approved review cards |
| FL agent | Emit functional model and FCOV plan | `model/functional_model.py`, `cov/fcov_plan.json` | SSOT `function_model` |
| CL agent | Emit cycle model and cycle coverage intent | `model/cycle_model.py`, `model/cl_model_check.json` | SSOT `cycle_model` |
| RTL agent | Implement RTL from SSOT/FL/CL todo ledger | `rtl/`, `list/`, RTL reports | SSOT, FL/CL outputs, RTL todo ledger |
| TB agent | Implement testbench and scoreboard | `tb/`, `tc/`, TB reports | SSOT, FL model, coverage goals |
| Sim agent | Run tests and collect observations | `sim/`, waveform/log artifacts | RTL, TB, scenarios |
| Sim-debug agent | Classify mismatch ownership | debug reports, source/wave links | sim logs, waveforms, hierarchy |
| Lint agent | Close lint/style gates | `lint/`, RTL style fixes when allowed | RTL, coding rules |
| Coverage agent | Close function/cycle coverage | `cov/` reports, coverage-directed tests | SSOT coverage goals, sim evidence |
| EDA agents | Run syn/sta/pnr/post-sta | `syn/`, `sta/`, `pnr/` reports | RTL, constraints, PDK setup |
| Review agent | Verify evidence and human review queue | review summaries | all ledgers and reports |

### Collaboration Contract

Every agent must answer three questions before writing:

```text
1. Which workflow owns this artifact?
2. Which SSOT refs or upstream evidence authorize this edit?
3. Which validator will approve or reject the result?
```

If an agent cannot answer them, it should create a `human_review_needed` or
`blocked` item instead of inventing behavior.

### Handoff Format

Agents hand off through JSON/markdown artifacts, not hidden chat memory.

Minimum handoff:

```json
{
  "handoff_schema": "stage_handoff.v1",
  "ip": "dma",
  "from_workflow": "rtl-gen",
  "to_workflow": "tb-gen",
  "source_refs": [
    "function_model.transactions.FM_DESCRIPTOR_FETCH",
    "cycle_model.pipeline.DESCRIPTOR_FETCH"
  ],
  "artifacts": [
    "rtl/dma_core.sv",
    "rtl/rtl_todo_plan.json",
    "rtl/rtl_compile.json",
    "lint/dut_lint.json"
  ],
  "evidence_summary": {
    "status": "approved",
    "required_todos": 95,
    "open_required_todos": 0
  },
  "human_review_needed": []
}
```

### Conflict Rules

- SSOT, FL model, CL model, coverage goals, and constraints are upstream truth.
  Downstream agents must not mutate them to make their stage pass.
- RTL agent may edit RTL-owned files only.
- TB/coverage agents may add tests and coverage-directed stimulus, but must not
  weaken expected behavior.
- EDA agents may add constraints only when they trace to SSOT timing/power/PDK
  requirements or an approved review item.
- If two agents want the same file, the owner workflow wins. Others file a
  repair request or review item.

### Parallel Work

Parallelism is allowed when write scopes are disjoint:

```text
FL model agent and CL model agent can run after SSOT approval.
RTL and TB can draft in parallel only when TB consumes locked SSOT/FL APIs.
Lint can run after RTL snapshots.
Coverage can start with SSOT goals, but closure requires sim evidence.
EDA can start after RTL compile/lint is stable.
```

Parallel agents must write separate logs and session paths:

```text
<campaign>/<ip>/<workflow>-<model-or-purpose>
```

Examples:

```text
dma_bench/dma_axi/rtl-gen-cursor
dma_bench/dma_axi/tb-gen-gpt53
dma_bench/dma_axi/coverage-deepseek
```

### System Completion Definition

The IP is not complete when one agent says "done". It is complete when the
cross-stage goal ledger says all required stages have approved evidence.

Completion requires:

```text
SSOT approved
FL model approved
CL model approved when cycle_model requires it
RTL compile/lint/audit approved
TB scoreboard approved
sim pass with fresh logs
sim-debug has no unresolved owner-classified mismatch
function coverage approved
cycle coverage approved
lint approved
required EDA reports approved or explicitly waived
human_review_needed queue empty or accepted as known open decisions
```

Recommended final artifact:

```text
<ip>/signoff/goal_ledger.json
```

Example:

```json
{
  "ip": "dma",
  "status": "approved",
  "stages": {
    "ssot-gen": {"status": "approved"},
    "fl-model-gen": {"status": "approved"},
    "cl-model-gen": {"status": "approved"},
    "rtl-gen": {"status": "approved"},
    "tb-gen": {"status": "approved"},
    "sim": {"status": "approved"},
    "sim-debug": {"status": "approved"},
    "lint": {"status": "approved"},
    "coverage": {"status": "approved"}
  },
  "human_review_needed": [],
  "known_waivers": []
}
```

## Running The Flow

Start from the common_ai_agent root:

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
```

Create or repair SSOT:

```bash
python3 src/main.py -s <campaign>/<ip>/ssot-gen -w ssot-gen --model gpt-5.3-codex --effort medium
```

Inside common_ai_agent:

```text
/mode pipeline
/new-ip <ip> <kind>
```

Validate SSOT:

```bash
bash workflow/ssot-gen/scripts/check_ssot_disk.sh <ip>
```

Run downstream stages through their workflow commands:

```text
/ssot-fl-model <ip>
/ssot-equiv-goals <ip>
/ssot-rtl <ip>
/ssot-tb <ip>
/sim <ip>
/sim-debug <ip>
/ssot-coverage <ip>
```

For headless TDD:

```bash
ATLAS_RUN_REAL_LLM_TDD=1 \
PYTHONPATH=src:. \
python3 src/headless_workflow.py \
  --root /tmp/<run-root> \
  --ip <ip> \
  --req <requirements.md> \
  --model cursor-cli \
  --stages ssot-gen,fl-model-gen,equiv-goals,rtl-gen \
  --provider real
```

## How To Read A Run

Primary run logs:

```text
<ip>/logs/run_progress.jsonl
<ip>/logs/headless_run.json
<ip>/logs/llm_call_trace.jsonl
```

SSOT:

```text
<ip>/yaml/<ip>.ssot.yaml
```

RTL:

```text
<ip>/rtl/rtl_todo_plan.json
<ip>/rtl/rtl_todo_tracker.json
<ip>/rtl/rtl_compile.json
<ip>/lint/dut_lint.json
```

Coverage:

```text
<ip>/cov/coverage.json
<ip>/cov/function_coverage.json
<ip>/cov/cycle_coverage.json
```

Pass should mean:

```text
All required stage todos are approved by evidence or explicit human review.
No downstream stage changed upstream truth to pass.
Fresh logs prove the current artifacts.
```

## Relationship To Other Docs

- `workflow/COMMON_ENGINE_FLOW.md`
  - Engine boundary and canonical stage order.

- `doc/golden_todo_evidence_flow.md`
  - Approval policy, golden todo ledger design, human review queue, and
    coverage trace model.

- `doc/ip_workflow_guide.md`
  - Practical command guide for running IP generation.

- `workflow/rtl-gen/RTL_GEN_FLOW.md`
  - RTL-specific implementation of the golden todo pattern.

- `workflow/fl-model-gen/flow_guide.md`
  - FL model generation details.

- `workflow/coverage/system_prompt.md`
  - Coverage workflow behavior; should consume function/cycle/static coverage
    targets from this guide.

- `doc/workflow_long_term_improvements.md`
  - Backlog for staged implementation of the full strategy.

## Development Roadmap

1. Keep RTL golden todo as the reference implementation.
2. Add explicit `approval_policy` and `required_evidence` to RTL todo rows.
3. Sync audit-approved rows into TodoTracker/UI state where mode policy allows.
4. Add FL and CL ledgers from SSOT `function_model` and `cycle_model`.
5. Add TB/sim/lint/coverage ledgers.
6. Add cross-stage traceability from each SSOT ref to final RTL-observed
   coverage evidence.
7. Add a unified human review queue.
8. Add dashboard views for per-IP, per-workflow, per-model LLM calls, tokens,
   cost, repair count, rejection count, human interventions, and evidence age.
9. Add a cross-agent handoff/goal ledger so all workflow agents collaborate
   through shared evidence instead of hidden chat state.
