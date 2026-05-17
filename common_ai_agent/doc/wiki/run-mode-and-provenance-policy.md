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
- In `Starter`, `ssot_to_rtl.py` can emit deterministic RTL preview from
  direct `function_model.output_rules` without requiring LLM-authored RTL
  evidence first.
- Starter RTL preview writes `rtl/rtl_preview_gates.json`, keeping hard gates
  separate from soft/deferred gates. Missing `cycle_model` is warning/deferred
  for same-cycle combinational previews, not a blocking gate.
- Starter preview artifacts are marked as preview evidence only; deferred gates
  must still close before Engineering or Signoff approval.
- `workflow/sim/scripts/starter_preview_sim.py` extends the same Starter lane
  from RTL preview to simulation smoke. It emits `tb/tb_<ip>.sv`, runs
  `iverilog` + `vvp`, and writes `sim/starter_preview_sim.json`,
  `sim/results.xml`, and `sim/sim_report.txt`.
- Starter sim uses direct output-rule checks only. It is fast feedback that the
  generated RTL matches the preview contract; it is not a substitute for
  Engineering/Signoff cocotb, scoreboard, coverage, or equivalence evidence.
- Starter RTL preview now treats readability as a gate for simple one-bit
  boolean rules. A rule such as `a_i and b_i` must emit reviewable RTL such as
  `assign y_o = a_i & b_i;`, not nested defensive `!= 0` casts.

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
needs a different Starter generator shape from the direct combinational
`output_rules` preview.

Recommended split:

- Direct expression preview: minimal combinational behavior from
  `function_model.output_rules`.
- Template-backed peripheral preview: deterministic seed RTL for known
  peripheral shapes such as APB timer, UART-lite, GPIO, and simple interrupt
  controllers.

For an APB timer, Starter should require only the compact behavioral contract:

- `top_module`
- APB port/interface declaration
- clock/reset
- register map fields such as control, reload/compare/value, interrupt status
- timer behavior: enable, tick source/prescale, reload or one-shot policy,
  compare/terminal-count interrupt policy

Starter should then generate:

- APB read/write shell
- counter state
- interrupt/status logic
- small smoke simulation: reset, APB write, readback, count/tick, interrupt
  assertion/clear

Deferred gates stay explicit:

- CDC, DFT, PNR, timing IO delays, security review, full coverage, formal/equiv,
  and signoff-quality scoreboard remain Engineering/Signoff evidence.

Current implementation status: direct expression Starter RTL-to-sim is
implemented. APB timer Starter requires adding the template-backed peripheral
preview lane; without it, current Starter correctly blocks stateful behavior via
`STARTER_SEQUENTIAL_CONTRACT` rather than emitting misleading combinational RTL.

Current caveat: resolved-SSOT diff views are not yet exposed in the UI. The
sidecar already has nested paths, but the user-facing view currently summarizes
counts and examples rather than showing a field-by-field review table.
