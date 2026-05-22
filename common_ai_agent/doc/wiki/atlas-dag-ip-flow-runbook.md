---
title: "ATLAS DAG IP Flow Runbook"
tags: ["atlas", "dag", "pipeline", "ip-flow", "cycle-model", "timeline"]
created: 2026-05-21T22:57:40+09:00
updated: 2026-05-21T22:57:40+09:00
sources: ["atlas_vr_smoke_0521"]
links: ["full-flow-pipeline.md", "workflow-ownership-and-boundaries.md"]
category: reference
confidence: high
schemaVersion: 1
---

# ATLAS DAG IP Flow Runbook

## DAG Meaning

DAG means **Directed Acyclic Graph**.

In the ATLAS workflow, it means the pipeline is not just a flat shell script.
Each stage declares what it depends on, and the orchestrator runs stages when
their prerequisites are ready. Independent stages can run in parallel; dependent
stages wait.

Example:

```text
ssot
  -> fl-model
  -> cl-model
  -> equivalence
  -> rtl
  -> lint
  -> tb
  -> sim
  -> coverage
  -> sim-debug
  -> syn
  -> sta
  -> pnr
  -> sta-post
  -> goal-audit
```

With `schedule: "dag"`, ATLAS decides the safe ordering from stage
dependencies. It is useful when a long flow has both strict ordering and
parallelizable work.

## Headless Backend Run

The successful smoke IP was `atlas_vr_smoke_0521`.

From the `common_ai_agent` project root, the backend API payload was:

```json
{
  "ip": "atlas_vr_smoke_0521",
  "stages": [
    "fl-model",
    "cl-model",
    "equivalence",
    "lint",
    "tb",
    "sim",
    "coverage",
    "sim-debug",
    "syn",
    "sta",
    "pnr",
    "sta-post",
    "goal-audit"
  ],
  "schedule": "dag",
  "run_mode": "engineering",
  "exec_mode": "orchestrator"
}
```

The same shape can be sent to:

```text
POST /api/pipeline/dispatch
```

Use `exec_mode: "orchestrator"` when the flow should let ATLAS coordinate the
workers. Use explicit `ip` until active-IP command fallback is proven for the
specific command surface.

## Worker Surfaces

The run maps approximately to these worker commands:

```text
/ssot-fl-model
/ssot-cl-model
/ssot-equiv-goals
/lint
/tb-gen
/ssot-sim
/ssot-coverage
/sim-debug
/syn-auto
/sta-auto
/pnr-auto
/sta-post
/goal-audit
```

## Local Verification Commands

Use these when debugging or confirming fresh evidence:

```bash
python3 workflow/rtl-gen/scripts/rtl_compile_report.py atlas_vr_smoke_0521 --top atlas_vr_smoke_0521 --project-root .
python3 workflow/lint/scripts/dut_lint_report.py atlas_vr_smoke_0521 --top atlas_vr_smoke_0521
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atlas_vr_smoke_0521 --root . --audit-rtl
python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py atlas_vr_smoke_0521 --root .
```

For rerunning only the final physical stages after a PnR fix:

```json
{
  "ip": "atlas_vr_smoke_0521",
  "stages": ["pnr", "sta-post", "goal-audit"],
  "schedule": "dag",
  "run_mode": "engineering",
  "exec_mode": "orchestrator"
}
```

## Evidence To Check

Minimum signoff evidence:

```text
rtl/rtl_compile.json
lint/dut_lint.json
model/fl_model_check.json
model/cl_model_check.json
verify/equivalence_goals.json
sim/fl_rtl_compare.json
cov/coverage_functional.json
sim/fl_rtl_goal_audit.json
syn/out/area.json
sta/out/wns.json
pnr/out/pnr.report.md
pnr/out/drc.json
sta-post/out/wns.json
```

For `atlas_vr_smoke_0521`, the final evidence was:

```text
lint: 0 errors, 0 warnings
FL/RTL compare: 38/38 goals passed
functional coverage: 44/44 bins hit, 100%
goal audit: 16/16 checks passed
STA: setup WNS +5.69 ns, hold WNS +1.22 ns, 0 violations
PnR DRC: 0
post-route STA: setup WNS +3.05 ns, hold WNS +1.27 ns, 0 violations
```

## Cycle Model And Timeline Scenario

Cycle model was generated and validated for the smoke IP:

```text
model/cycle_model.py
model/cl_model_check.json
```

The generated cycle coverage included:

```text
cycle_handshake_*
cycle_latency_*
cycle_pipeline_s0_accept
cycle_pipeline_s1_evaluate
cycle_pipeline_s2_observe
cycle_ordering_*
cycle_backpressure_0
```

Scenario execution was represented by `SC01` through `SC09`, with `SC03`
covering handshake/backpressure behavior.

Important gap: this proves cycle behavior through model/check/coverage artifacts,
but it is not yet a polished human-readable timeline spec. A stronger next step
is to add a first-class artifact such as:

```text
verify/timeline_scenarios.json
doc/timeline_scenarios.md
```

Example target shape:

```text
SC03_BACKPRESSURE
  cycle 0: reset released
  cycle 1: request valid and accepted
  cycle 2: response valid, response ready low, payload held
  cycle 3: response still held
  cycle 4: response ready high, completion observed
```

Then the TB should consume that artifact directly instead of inferring timeline
checks loosely from generic equivalence goals.

## Common Failure From This Run

OpenROAD/TritonRoute treated a hierarchical constant net such as
`u_vr_incr_core/one_` as a POWER signal and failed routing. The fix was to make
the PnR route script normalize hierarchical net names by checking the leaf name
as well as the full net name.

After that fix, rerunning only `pnr`, `sta-post`, and `goal-audit` was enough.

## Related

- [[full-flow-pipeline]]
- [[workflow-ownership-and-boundaries]]
