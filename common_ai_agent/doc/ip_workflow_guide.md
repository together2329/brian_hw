# IP Workflow Guide

This guide records the intended `common_ai_agent` flow for generating and
validating IP artifacts from a canonical SSOT. The `todo_counter_pipe` cold run
is the reference example, but the flow is meant to apply to any IP.

## Core Rule

The parent operator/Codex should not directly implement downstream artifacts.

- Parent/operator owns requirement seed, SSOT review, workflow prompt/rule
  repair, and monitoring.
- `ssot-gen` owns the canonical SSOT only.
- `rtl-gen` owns RTL, filelist, compile, lint, and RTL TODO closure.
- `tb-gen`, `sim`, `sim_debug`, `coverage`, `syn`, `sta`, `pnr`, and
  `sta-post` own their own downstream artifacts.

If downstream generation fails because the SSOT is incomplete, the correct
repair is to update the SSOT through `ssot-gen` or a human-approved SSOT edit,
then rerun the downstream workflow. Do not make RTL pass by adding dummy wires,
comment-only evidence, heartbeat-only logic, or pass-shaped identifiers.

## Repository Root

Run commands from the `common_ai_agent` home:

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
```

Use isolated session names so model/workflow runs do not overwrite each other:

```text
<campaign>/<ip>/<workflow>[-<model-or-purpose>]
```

Examples:

```text
todo_pipeline/todo_counter_pipe/ssot-gen
todo_pipeline/todo_counter_pipe/rtl-gen-clean3
dma_bench/dma_axi/rtl-gen-gpt53
dma_bench/dma_axi/rtl-gen-deepseek
```

## Mode Selection

Use pipeline mode for exploratory end-to-end flow:

```text
/mode pipeline
```

Pipeline mode should keep moving, avoid `ask_user`, and record conservative
assumptions in the SSOT when a gap is not blocking.

Use CI mode for strict regression:

```text
/mode ci
```

CI mode should stop on missing required truth. It is better for automated
quality gates after the happy path is stable.

## SSOT Authoring Flow

Launch `ssot-gen`:

```bash
python3 src/main.py -s todo_pipeline/todo_counter_pipe/ssot-gen -w ssot-gen --model gpt-5.3-codex --effort medium
```

Inside the agent:

```text
/mode pipeline
/new-ip todo_counter_pipe counter
```

Then provide a requirement seed. The seed is not the YAML body; it is the input
for `ssot-gen` to create the canonical SSOT through its workflow rules.

Reference seed:

```text
Use the loaded /new-ip todo list and create only the canonical SSOT for IP todo_counter_pipe.
IP intent: parameterized synchronous up/down event counter with APB-lite style CSR interface,
separate bus_clk 150MHz and core_clk 300MHz, internal reset synchronizers, 2:1 core:bus clock
relationship, configurable WIDTH default 32, saturating and wrap modes, enable/clear/load
controls, terminal-count interrupt, sticky overflow/underflow status, debug observability
counters, clean function_model and cycle_model, and workflow_todos for rtl-gen/tb-gen/lint/
coverage/syn/sta/pnr.
Pipeline mode: do not block on ask_user; make conservative assumptions and record them in
custom.assumptions. Do not generate RTL/TB/sim/lint/syn artifacts in ssot-gen.
```

Expected SSOT output:

```text
<ip>/yaml/<ip>.ssot.yaml
```

For the reference run:

```text
todo_counter_pipe/yaml/todo_counter_pipe.ssot.yaml
```

## `/new-ip` Contract

`/new-ip <ip> <kind>` should load the SSOT new-IP TODO template and drive the
SSOT phases. The phase tracker should move with evidence:

```text
pending -> in_progress -> completed -> approved
```

The expected phases are:

1. Build requirements ledger and leaf boundary.
2. Scaffold only the leaf SSOT directory.
3. Write canonical behavior-rich SSOT.
4. Validate SSOT on disk.
5. Emit downstream handoff contract.

`/new-ip` is needed for a fresh IP because it creates the expected directory
shape and loads the SSOT authoring checklist. For an existing IP with a valid
SSOT, start from the downstream workflow command instead.

## Required SSOT Depth

The SSOT must contain enough structured truth for downstream workflows to
generate artifacts without re-asking basic architecture questions.

Minimum sections expected for a production-like IP:

- `top_module`: name, file, version, type, target.
- `sub_modules`: manifest blocks, ownership, file intent, source sections.
- `parameters`: defaults, constraints, and what each parameter controls.
- `io_list`: every port, direction, width, clock/reset domain, protocol role.
- `features`: trigger, datapath, control, output, and edge behavior.
- `dataflow`: concrete operational sequences.
- `function_model`: state variables, transactions, preconditions, outputs,
  side effects, error cases, invariants, and reference-model guidance.
- `cycle_model`: clocks, reset timing, latency, handshakes, pipeline stages,
  ordering, backpressure, CDC latency, and observability.
- `clock_reset_domains`: clocks, resets, frequencies, polarity, sync rules.
- `cdc_requirements` and `rdc_requirements`.
- `registers`: CSR map, offsets, fields, access type, reset value, side effects.
- `memory`: memory instances or explicit no-memory note.
- `interrupts`: sources, masks, pending bits, clear policy, output behavior.
- `fsm`: states, transitions, guards, outputs, illegal-state behavior.
- `timing_performance`: frequency, throughput, latency, outstanding/depth rules.
- `power_intent`, `security_safety`, `error_handling`, `debug_observability`.
- `integration_contract`, `dft_dfd`, `synthesis_ppa`, `coding_rules`.
- `test_requirements`: scenarios, stimulus, expected results, checker, coverage.
- `coverage_goals`: function coverage and cycle/performance coverage.
- `workflow_todos`: downstream TODOs with `content`, `detail`, `criteria`,
  `source_refs`, and owner file/module when inferable.
- `quality_gates`: pass criteria and evidence requirements.
- `generation_flow`: downstream handoff commands.
- `custom.assumptions`: assumptions made in pipeline mode.

## SSOT Validation

Run the canonical SSOT validator:

```bash
bash workflow/ssot-gen/scripts/check_ssot_disk.sh todo_counter_pipe
```

Reference result:

```text
[check_ssot_disk] PASS: todo_counter_pipe/yaml/todo_counter_pipe.ssot.yaml = 68776B, 36 sections, 0 TBDs
```

Run an independent summary check:

```bash
python3 - <<'PY'
import pathlib
import yaml

p = pathlib.Path("todo_counter_pipe/yaml/todo_counter_pipe.ssot.yaml")
data = yaml.safe_load(p.read_text())

print("file_bytes", p.stat().st_size)
print("top_keys", len(data))
print("top_module", data.get("top_module", {}).get("name"), data.get("top_module", {}).get("type"))
print("sub_modules", len(data.get("sub_modules", [])))
print("registers", len(data.get("registers", {}).get("register_list", [])))
print("fm_state_variables", len(data.get("function_model", {}).get("state_variables", [])))
print("fm_transactions", len(data.get("function_model", {}).get("transactions", [])))
print("cycle_stages", len(data.get("cycle_model", {}).get("pipeline", [])))
print("rtl_todos", len(data.get("workflow_todos", {}).get("rtl-gen", [])))
print("assumptions", len(data.get("custom", {}).get("assumptions", [])))
print("decomposition_type", type(data.get("decomposition")).__name__)
PY
```

Literal placeholder scan:

```bash
rg -n 'TBD|<TBD>' todo_counter_pipe/yaml/todo_counter_pipe.ssot.yaml
```

If the policy is literal zero `TBD` strings, tighten the validator to reject
prose occurrences too.

## RTL Handoff

After SSOT validation, switch to `rtl-gen` and run `/ssot-rtl`.

Launch:

```bash
python3 src/main.py -s todo_pipeline/todo_counter_pipe/rtl-gen-clean -w rtl-gen --model gpt-5.3-codex --effort medium
```

Inside the agent:

```text
/mode pipeline
/ssot-rtl todo_counter_pipe
```

## `/ssot-rtl` Internal Contract

`/ssot-rtl <ip>` is a common_ai_agent workflow command. It is not a shell
command and not a plain prompt.

Internal order:

1. `workflow/rtl-gen/commands/ssot-rtl.json` maps `/ssot-rtl` to
   `handler: stage:ssot-rtl`.
2. `src/workflow_stage_engine.py` runs the `ssot-rtl` stage.
3. The stage runs:

```bash
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py <ip> --root <project-root>
```

4. The derive script writes or refreshes:

```text
<ip>/rtl/rtl_todo_plan.json
<ip>/rtl/rtl_todo_tracker.json
<ip>/todo/rtl_todo_tracker.json
```

5. `workflow/loader.py` loads the dynamic tracker into the existing TodoTracker.
6. `rtl-gen` implements and repairs RTL from the loaded flat TODO ledger.
7. After RTL edits, the stage runs compile, DUT-only lint, and audit:

```bash
python3 workflow/rtl-gen/scripts/rtl_compile_report.py <ip> --project-root .
python3 workflow/lint/scripts/dut_lint_report.py <ip>
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py <ip> --root . --audit-rtl
```

The fixed seed file `workflow/rtl-gen/todo_templates/ssot-rtl.json` is only a
bootstrap surface. The authoritative work breakdown is the derived dynamic
tracker. Fresh dynamic tracker tasks start as `pending`; current audit status
is preserved in task detail/criteria, not pre-approved.

For shell validation, do not type `/ssot-rtl`. Use the script form:

```bash
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py todo_counter_pipe --root . --audit-rtl
```

## RTL TODO Driving

TODO derivation is deterministic script work:

```text
SSOT -> derive_rtl_todos.py -> rtl_todo_plan.json -> rtl_todo_tracker.json
```

TODO execution is agent/runtime work:

```text
dynamic TodoTracker -> rtl-gen LLM edits RTL -> compile/lint/audit -> close TODOs
```

The agent should close TODOs one at a time or in a small coherent batch, but the
closure evidence must come from real RTL and fresh reports. Static evidence is
not valid when it appears only in comments or dummy aliases.

## Downstream Workflow Ownership

Each downstream stage must use its own workflow command and evidence files.

- `rtl-gen`: `/ssot-rtl <ip>` for RTL, filelist, compile, lint, RTL TODO audit.
- `tb-gen`: `/ssot-tb <ip>` or `/ssot-tb-cocotb <ip>` for TB and scoreboard.
- `sim`: `/sim <ip>` for simulation execution and result artifacts.
- `sim_debug`: debug UI from sim artifacts, waveform, source, hierarchy.
- `coverage`: coverage report against SSOT function and cycle goals.
- `syn`: synthesis report.
- `sta`: pre-route STA report.
- `pnr`: place and route report.
- `sta-post`: post-route STA report.

Do not let one workflow claim another workflow's artifact is complete unless it
has run the owning workflow or produced the exact owning evidence.

## Monitoring Checklist

During a run, watch these files:

```text
.session/<session>/conversation.json
.session/<session>/todo.json
<ip>/yaml/<ip>.ssot.yaml
<ip>/rtl/rtl_todo_plan.json
<ip>/rtl/rtl_todo_tracker.json
<ip>/todo/rtl_todo_tracker.json
<ip>/rtl/rtl_compile.json
<ip>/lint/dut_lint.json
<ip>/logs/stage_engine/ssot-rtl.json
```

Useful status command:

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path("todo_counter_pipe/rtl/rtl_todo_plan.json")
obj = json.loads(p.read_text())
gate = obj.get("gate", {})
print("tasks", len(obj.get("tasks", [])))
print("gate", gate.get("status"))
print("open_required", gate.get("open_required_todos"))
print("static_missing", gate.get("static_missing"))
for t in obj.get("tasks", []):
    tc = t.get("todo_completion") or {}
    if t.get("required") and tc.get("status") != "pass":
        print(t.get("id"), t.get("category"), t.get("source_ref"), "-", tc.get("reason"))
PY
```

## Reference `todo_counter_pipe` Status

Verified behavior:

- `/ssot-rtl todo_counter_pipe` runs `derive_rtl_todos.py`.
- Dynamic TODO tracker is generated and loaded.
- Current reference ledger size: `279` RTL TODOs.
- Fresh dynamic tasks start `pending`.

Recent open gates observed during the reference run:

- RTL authoring provenance stale or incomplete.
- Static RTL evidence missing for CDC/FSM terms.
- Manifest signal-flow issue for `status_core_to_bus`.
- DUT-only lint not clean.
- Dynamic TODO closure not complete.

This means the flow is working as a gate, but the IP is not production-pass
until those gates close with real RTL and fresh evidence.

## Common Failure Modes

- Running `/ssot-rtl` in the shell. It must be typed inside common_ai_agent; use
  `derive_rtl_todos.py --audit-rtl` for shell checks.
- Reusing the same session name for different models or workflows. Use separate
  session names to avoid `.session` confusion.
- Marking TODOs approved before evidence exists. Fresh dynamic tracker tasks
  should start pending.
- Adding identifiers only to satisfy evidence matching. Evidence must be live
  synthesizable behavior.
- Treating `ssot-gen` scaffold RTL as implementation. It is only a placeholder
  unless `rtl-gen` authored and proved it.
- Letting sim, lint, coverage, synthesis, STA, or PnR be claimed by the wrong
  workflow.

## Minimal New-IP Template

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
python3 src/main.py -s <campaign>/<ip>/ssot-gen -w ssot-gen --model gpt-5.3-codex --effort medium
```

Inside the agent:

```text
/mode pipeline
/new-ip <ip> <kind>
```

Seed:

```text
Use the loaded /new-ip todo list and create only the canonical SSOT for IP <ip>.
IP intent: <purpose, clocks, resets, interfaces, parameters, registers, interrupts,
function behavior, cycle behavior, coverage goals, and downstream workflow todos>.
Pipeline mode: do not block on ask_user; make conservative assumptions and record
them in custom.assumptions. Do not generate RTL/TB/sim/lint/syn artifacts in ssot-gen.
```

Validate:

```bash
bash workflow/ssot-gen/scripts/check_ssot_disk.sh <ip>
```

Then hand off to RTL:

```bash
python3 src/main.py -s <campaign>/<ip>/rtl-gen -w rtl-gen --model gpt-5.3-codex --effort medium
```

Inside the `rtl-gen` agent:

```text
/mode pipeline
/ssot-rtl <ip>
```

Stop condition for RTL:

```text
derive_rtl_todos.py --audit-rtl reports gate=pass
rtl_compile.json reports errors=0
dut_lint.json reports errors=0 warnings=0 or approved waivers
all required rtl_todo_plan items have todo_completion.status=pass
```
