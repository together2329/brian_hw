# Run Mode And SSOT Provenance Policy

Status: product/design decision, 2026-05-17.

This page records the decision from the UI/SSOT discussion around
`Starter`, `Engineering`, and `Signoff` modes. The important outcome is that
the modes describe **work maturity and evidence strictness**, not IP size.

Related: [[atlas-pipeline-screen]] · [[ssot-gen-pass-pipeline]] ·
[[full-flow-pipeline]] · [[golden-todo-evidence]] ·
[[orchestrator-worker-handoff]]

## Decision

Use two independent controls:

```text
Run Mode:  Starter | Engineering | Signoff
Exec Mode: Single Worker | Orchestrator
```

`Run Mode` answers: **how strict are the gates for this run?**

`Exec Mode` answers: **how is work executed?**

They must not be merged. A user can run a DMA in `Starter` mode to get a first
green path, and can run a tiny PWM in `Signoff` mode when they need audit-grade
evidence.

## Why Not IP-Size Modes

The rejected model was:

```text
tiny IP  -> light schema
large IP -> full schema
```

That fails because IP size is not the real product question. The real question
is whether the user is exploring, engineering, or signing off. The same IP can
move through all three modes over time.

The user feedback that shaped the decision:

- A PWM should not require DMA-class paperwork just to prove the flow works.
- A DMA may still need a "first green" mode before full signoff.
- Beginner UX should not expose the whole canonical SSOT boilerplate on day 1.
- Signoff must still be able to prove which values were user-authored,
  derived, defaulted, or unresolved.

## Run Mode Semantics

| Mode | Purpose | Defaults | Blocking behavior |
|---|---|---|---|
| `Starter` | Fast first green and onboarding | Generated defaults allowed and recorded | Blocks only on missing core intent or impossible downstream generation |
| `Engineering` | Normal IP development | Generated defaults allowed only with provenance and review visibility | Blocks on missing functional/cycle/coverage evidence required for development |
| `Signoff` | Audit-grade release evidence | Generated defaults are not allowed for signoff-critical fields | Blocks on unresolved review decisions, generated defaults in critical fields, stale evidence, or missing signoff gates |

Starter is not "toy mode." It is a maturity mode. It must still create honest
artifacts and must not claim signoff readiness.

## Provenance Decision

Do **not** put provenance metadata inline on every user-visible SSOT YAML field.
That would make the SSOT 2-3x larger and worsen the boilerplate problem.

Instead, keep the user SSOT clean and store provenance as sidecar evidence:

```text
<ip>/yaml/<ip>.ssot.yaml             # user-visible authored intent
<ip>/yaml/<ip>.ssot.resolved.yaml    # canonical resolved SSOT for downstream workflows
<ip>/yaml/<ip>.ssot.provenance.json  # field-origin ledger
<ip>/review/review_decisions.json    # user/human authority and unresolved decisions
```

The validator/schema policy defines which fields are critical in each mode.
The provenance ledger records origin for the resolved meaningful fields,
starting with mode-critical and validator-gated fields. The UI can summarize
counts without showing boilerplate in the main YAML editor.

Example ledger entry:

```json
{
  "/clocking/core_clk/frequency_mhz": {
    "authority": "generated_default",
    "source": "starter_policy",
    "value": 100,
    "mode_allowed": ["starter"],
    "review": "needed_for_engineering"
  },
  "/top_module/name": {
    "authority": "user",
    "source": "yaml/simple_pwm.ssot.yaml"
  }
}
```

Authority values:

```text
user
derived
generated_default
review_needed
tool_evidence
```

`generated_default` is allowed in Starter, visible in Engineering, and blocks
Signoff when the field is signoff-critical.

## Feedback Incorporated

The external/Claude-style feedback asked whether provenance should be attached
to every SSOT YAML field or only to required validator fields.

Accepted part:

- Inline provenance on every YAML field is too heavy.
- The user-facing SSOT should stay readable.
- Mode policy belongs in validator/schema logic, not as hand-written YAML
  boilerplate.

Refined decision:

- Not "YAML inline everywhere."
- Not "validator code only, no durable record."
- Use **schema policy + resolved SSOT + sidecar provenance ledger**.

This keeps the editing experience simple while preserving signoff auditability.

## UI Placement

Global ATLAS top control row:

```text
Workspace  Pipeline  Architect   Run Mode: [Engineering v]   Exec: [Orchestrator v]   running...
```

This belongs next to the existing screen controls because it is part of the
current IP/workflow execution context.

Do not put `Run Mode` inside the right-side Agent status panel. That panel's
existing "Mode" is agent/chat intent (`Normal` / `Plan`) and would confuse two
different concepts.

Pipeline screen:

```text
ip gpio   pipeline   Run Mode: Engineering   Exec: Orchestrator   defaults 7   review 2   signoff blocked
```

The Pipeline screen should show the same selected values with richer evidence:

- generated-default count
- review-needed count
- signoff-blocked reason
- active workers
- pending handoffs
- running stages

## Backend Contract

Dispatch payloads should carry both independent choices:

```json
{
  "ip": "gpio",
  "stages": ["ssot", "rtl", "lint"],
  "schedule": "auto",
  "run_mode": "engineering",
  "exec_mode": "orchestrator"
}
```

Pipeline state should echo the effective policy:

```json
{
  "run_mode": "engineering",
  "exec_mode": "orchestrator",
  "provenance_summary": {
    "generated_defaults": 7,
    "review_needed": 2,
    "signoff_blocked": true
  }
}
```

The UI renders this state; backend validators and workflow runners remain the
authority.

## Validator Behavior

Mode policy should live in deterministic schema/validator code:

- Starter: fill safe derived/default fields, record provenance, do not claim
  signoff.
- Engineering: require functional model, cycle model, coverage intent, core
  quality gates, and fresh evidence; generated defaults remain visible.
- Signoff: fail if signoff-critical fields are `generated_default` or
  `review_needed`; require syn/sta/pnr/security/dft/timing gates according to
  the IP's selected scope.

The validator should emit concise user-facing summaries:

```text
Engineering ready: 7 generated defaults recorded, 2 review decisions open.
Signoff blocked: /clocking/core_clk/frequency_mhz is generated_default.
```

## Hard Rules

- User-visible SSOT YAML stays clean.
- Resolved SSOT is the downstream contract.
- Provenance is durable sidecar evidence, not hidden runtime memory.
- Signoff cannot silently accept generated defaults for critical fields.
- Run Mode and Exec Mode are separate UI/backend concepts.
- Pipeline UI displays policy and evidence, but does not decide pass/fail.

## Implementation Status

Implemented on 2026-05-17:

- ATLAS top row exposes `run` and `exec` selectors.
- Pipeline dispatch payloads include `run_mode` and `exec_mode`.
- `/api/pipeline/run_policy` persists the effective policy for the process.
- `/api/pipeline/state` echoes policy plus `provenance_summary`.
- Pipeline screen displays Run Mode, Exec Mode, generated-default count,
  review-needed count, and signoff-blocked status.
- Pipeline review chip now opens the first human-facing decision artifact
  through the normal Workspace preview path when
  `orchestrator.decision_items[].evidence.human_facing_request` is present.
- `check_ssot_disk.sh` accepts `--mode starter|engineering|signoff`.
- `repair_ssot_schema.py` accepts `--mode` and writes
  `<ip>/yaml/<ip>.ssot.provenance.json`.
- Provenance sidecar records nested field paths as well as top-level sections,
  so `quality_gates.ssot.pass`, `security.assets[0].name`, and similar paths
  can be traced separately.
- `headless_workflow.py` passes Run Mode into SSOT validation and repair.
- `ssot_to_rtl.py` accepts `--mode starter|engineering|signoff`.
- In `Starter`, `ssot_to_rtl.py` writes an LLM authoring handoff instead of RTL.
  Starter gates are relaxed, but the RTL artifact is still real LLM-authored
  RTL.
- Starter handoff writes `rtl/rtl_preview_gates.json`, keeping hard gates
  separate from soft/deferred gates. Missing `cycle_model` is warning/deferred
  for same-cycle starter contracts, not a blocking gate.
- Starter artifacts are real authoring and verification artifacts. They are not
  signoff evidence; deferred gates must still close before Engineering or
  Signoff approval.
- `workflow/sim/scripts/starter_preview_sim.py` extends the same Starter lane
  from RTL preview to simulation smoke. It emits `tb/tb_<ip>.sv`, runs
  `iverilog` + `vvp`, and writes `sim/starter_preview_sim.json`,
  `sim/results.xml`, and `sim/sim_report.txt`.
- Starter sim uses direct output-rule checks only. It is fast feedback that the
  LLM-authored RTL matches the Starter contract; it is not a substitute for
  Engineering/Signoff cocotb, scoreboard, coverage, or equivalence evidence.
- Starter now stops at an LLM authoring handoff for all RTL, including tiny
  combinational examples. The contract may contain `output_rules`,
  `function_model.state_variables`, and `state_updates`, but default Starter
  must not compile those rules into RTL. The LLM/worker authors RTL, then
  compile/sim gates verify it.

Mode-specific validator behavior now starts with this contract:

| Field group | Starter | Engineering | Signoff |
|---|---|---|---|
| `top_module` | required | required | required |
| `io_list` | required | required | required |
| `function_model` | required | required | required |
| `cycle_model` | generated/default allowed | required | required |
| `test_requirements.coverage_goals` | generated/default allowed | required | required |
| `quality_gates` | generated/default allowed | required core gates | required full gates |
| `dft` | generated/default allowed | optional / generated | required |
| `pnr` | generated/default allowed | optional / generated | required |
| `security.assets` | generated/default allowed | required | required |
| `error_handling` | generated/default allowed | required | required |
| `timing.io_delays` | generated/default allowed | generated/default visible | required when signoff scope needs it |

## APB Timer in Starter

Starter is not an IP-size label. An APB timer can start in Starter mode, but it
must be LLM-authored RTL, not template RTL and not generic rule-to-RTL compiler
output. The rule contract guides authoring and verification; it is not a hidden
HDL.

Recommended split:

- Starter authoring contract: compact SSOT plus machine-checkable rules for
  LLM/worker guidance.
- Starter gates: relaxed compile/smoke evidence to move fast.
- Engineering/Signoff gates: stricter coverage, scoreboard, equivalence,
  timing, DFT, PNR, and review evidence.

For an APB timer, Starter should require only the compact behavioral contract:

- `top_module`
- APB port/interface declaration
- clock/reset
- executable state variables such as enable, compare/reload, count, interrupt
  state
- executable state updates for APB writes, tick/count behavior, interrupt set
  and clear
- executable output rules for ready/error/read-data/interrupt outputs

Starter should then produce handoff and verification artifacts:

- `rtl/rtl_contract.json` with type `starter_llm_rtl_authoring_contract`
- `rtl/starter_llm_rtl_handoff.json` for the worker
- no RTL file from `ssot_to_rtl.py` by default
- after the LLM writes RTL, compile and smoke simulation from the same contract

Deferred gates stay explicit:

- CDC, DFT, PNR, timing IO delays, security review, full coverage, formal/equiv,
  and signoff-quality scoreboard remain Engineering/Signoff evidence.

Correction from 2026-05-17: rule-driven RTL generation was tried and rejected
as the default because it turns Starter into a YAML-to-RTL generator DSL.
Default Starter now writes an LLM handoff for RTL. A fresh APB Timer smoke
(`starter_apb_timer`) confirmed the corrected flow: `ssot_to_rtl.py --mode
starter` stopped at LLM handoff, an LLM-authored RTL file was supplied, then
compile passed with `errors=0 diagnostics=0 style_violations=0` and sim passed
with `tests=64 pass=64 fail=0`.

Current caveat: resolved-SSOT diff views are not yet exposed in the UI. The
sidecar already has nested paths, but the user-facing view currently summarizes
counts and examples rather than showing a field-by-field review table.

## Engineering Mode RTL Policy

Engineering is the default serious implementation lane. It is not a larger-IP
mode and it is not a deterministic YAML-to-RTL generator. The difference from
Starter is gate depth:

- Starter: compact SSOT, relaxed/deferred gates, real LLM-authored RTL, fast
  compile/smoke feedback.
- Engineering: full SSOT contract, real LLM-authored RTL, provenance, compile,
  lint/smoke simulation, coverage plan, scoreboard scenarios, and concrete
  review evidence.
- Signoff: Engineering evidence plus signoff-only domains such as DFT, PNR,
  timing closure, and full coverage/equivalence closure.

Decision from 2026-05-17:

- `ssot_to_rtl.py --mode engineering` must not write RTL from rules by default,
  even when `req/requirements.md` is present.
- If RTL/list/provenance are absent or stale, Engineering must stop with
  `[RTL BLOCKED] LLM_RTL_IMPLEMENTATION_REQUIRED` or
  `COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED`.
- The existing rule-contract helpers remain useful for authoring context,
  scoreboard/TB generation, and validation. They are not authorization to emit
  default RTL.

Engineering APB Timer smoke result:

- Root: `/tmp/atlas_engineering_apb_timer_smoke_20260517`
- `check_ssot_disk.sh apb_timer --mode engineering`: PASS, 11.6 KB YAML,
  34 sections, 0 TBDs.
- `derive_rtl_todos.py`: PASS, `tasks=95 blockers=0 orphans=0 gate=planned`.
- Before RTL authoring, `ssot_to_rtl.py --mode engineering` stopped at
  `[RTL BLOCKED]` with `LLM_RTL_IMPLEMENTATION_REQUIRED`.
- After LLM-authored `rtl/apb_timer.sv`, `list/apb_timer.f`, and
  `rtl/rtl_authoring_provenance.json`, RTL preflight passed with
  `1 manifest file`.
- `rtl_compile_report.py`: PASS, `errors=0 diagnostics=0 style_violations=0`.
- Icarus/VVP smoke: `TESTS=9 PASS=9 FAIL=0`.
- `check_sim_disk.sh`: PASS, `tests=9 failures=0 errors=0`.
