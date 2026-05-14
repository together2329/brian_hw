# IP Workflow Guide

This guide records the verified authoring flow for creating an IP SSOT with
`common_ai_agent`, using the `todo_counter_pipe` cold run as the reference.

The key principle is:

- The human/operator provides an IP requirement seed.
- `common_ai_agent` runs the workflow.
- `ssot-gen` writes only the canonical SSOT.
- Downstream workflows own RTL, TB, simulation, lint, coverage, synthesis, STA,
  PnR, and post-route STA.

## Reference Run

Working directory:

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
```

Launch the agent with an isolated session, IP, and workflow path:

```bash
python3 src/main.py -s todo_pipeline/todo_counter_pipe/ssot-gen -w ssot-gen --model deepseek --effort medium
```

Inside the interactive agent:

```text
/mode pipeline
/new-ip todo_counter_pipe counter
```

Then provide the requirement seed prompt:

```text
Use the loaded /new-ip todo list and create only the canonical SSOT for IP todo_counter_pipe. IP intent: parameterized synchronous up/down event counter with APB-lite style CSR interface, separate bus_clk 150MHz and core_clk 300MHz, internal reset synchronizers, 2:1 core:bus clock relationship, configurable WIDTH default 32, saturating and wrap modes, enable/clear/load controls, terminal-count interrupt, sticky overflow/underflow status, debug observability counters, clean function_model and cycle_model, and workflow_todos for rtl-gen/tb-gen/lint/coverage/syn/sta/pnr. Pipeline mode: do not block on ask_user; make conservative assumptions and record them in custom.assumptions. Do not generate RTL/TB/sim/lint/syn artifacts in ssot-gen.
```

The prompt above is not the YAML body. It is only the requirement seed. The
actual SSOT authoring is done by `common_ai_agent` through the `ssot-gen`
workflow rules, template, tools, and TODO tracker.

## What Actually Writes The SSOT

The SSOT writing flow is:

1. `src/main.py` starts the selected workflow.
2. `-w ssot-gen` loads the SSOT generator workflow.
3. `/mode pipeline` selects non-blocking pipeline behavior for questions.
4. `/new-ip <ip_name> <kind>` loads the SSOT new-IP TODO template.
5. The operator gives a requirement seed prompt.
6. `ssot-gen` reads `workflow/ssot-gen/rules/ssot-template.yaml`.
7. `ssot-gen` calls `scaffold_ip` to create the standard IP layout.
8. `ssot-gen` writes the canonical file:

```text
<ip>/yaml/<ip>.ssot.yaml
```

9. `ssot-gen` validates the SSOT on disk.
10. `ssot-gen` emits `[SSOT HANDOFF] -> rtl-gen`.

For the reference run, the generated SSOT is:

```text
todo_counter_pipe/yaml/todo_counter_pipe.ssot.yaml
```

## `/new-ip` Phase Contract

`/new-ip` currently drives a 5-phase SSOT flow:

1. Build requirements ledger and leaf boundary.
2. Scaffold only the leaf SSOT directory.
3. Write canonical behavior-rich SSOT.
4. Validate SSOT on disk.
5. Emit downstream handoff contract.

Each phase must move through:

```text
pending -> in_progress -> completed -> approved
```

The tracker expects evidence between state transitions. A phase should be
started before the evidence command/tool is run, then completed and approved
after the evidence is available.

## What `ssot-gen` May Create

Allowed outputs in `ssot-gen`:

- Canonical SSOT YAML under `<ip>/yaml/<ip>.ssot.yaml`.
- Standard workflow directories needed by the scaffold.
- Placeholder scaffold stubs only when required by the existing scaffold
  contract.

Not allowed to claim in `ssot-gen`:

- RTL complete.
- TB complete.
- Simulation pass.
- Lint clean.
- Waveform correct.
- Coverage closed.
- Synthesis complete.
- STA signed off.
- PnR complete.
- DFT inserted.

In the reference run, `ssot-gen` created only a scaffold RTL stub:

```text
todo_counter_pipe/rtl/todo_counter_pipe.sv
```

That file was only a 216-byte placeholder containing a module skeleton and
`// TBD`. It was not production RTL.

## Required SSOT Depth

The canonical SSOT should contain enough structured information for downstream
workflows to implement the IP without re-asking basic architecture questions.

At minimum, the SSOT should define:

- `top_module`: name, file, version, type, target.
- `sub_modules`: manifest blocks, ownership, file intent, source sections.
- `parameters`: defaults, types, constraints, and what each parameter drives.
- `io_list`: every port, direction, width, clock/reset domain, protocol role.
- `features`: trigger, datapath behavior, control behavior, output behavior.
- `dataflow`: concrete operational sequences.
- `function_model`: state variables, transactions, preconditions, outputs,
  side effects, error cases, invariants, and reference-model guidance.
- `cycle_model`: clocks, reset timing, latency, handshakes, pipeline stages,
  ordering, CDC latency, and observability.
- `clock_reset_domains`: all clocks, resets, frequencies, polarity, sync rules.
- `cdc_requirements` and `rdc_requirements`.
- `registers`: CSR map, offsets, fields, access type, reset value, side effects.
- `memory`: memory instances or an explicit no-memory note.
- `interrupts`: sources, masks, pending bits, clear policy, output behavior.
- `fsm`: states, transitions, guards, outputs, illegal-state behavior.
- `timing_performance`: frequency, throughput, latency, outstanding/depth rules.
- `power_intent`: clock gating, idle behavior, retention assumptions.
- `security_safety`: access assumptions, error containment, safety behavior.
- `error_handling`: overflow, underflow, protocol errors, illegal config.
- `debug_observability`: counters, status, trace points.
- `integration_contract`: parent SoC expectations and ownership boundaries.
- `dft_dfd`: scan, CDC sync handling, test assumptions.
- `synthesis_ppa`: synthesis, STA, constraints, PPA targets.
- `coding_rules`: RTL style, reset style, arithmetic guidance.
- `custom.assumptions`: conservative assumptions made in pipeline mode.
- `test_requirements`: scenarios with stimulus, expected result, checker, and
  coverage intent.
- `coverage_goals`: function coverage and cycle/performance coverage.
- `workflow_todos`: downstream TODOs with `content`, `detail`, `criteria`,
  `source_refs`, and owner file/module when inferable.
- `quality_gates`: pass criteria and evidence requirements.
- `generation_flow`: the downstream handoff commands.

## Validation Commands

Run the canonical SSOT validator:

```bash
bash workflow/ssot-gen/scripts/check_ssot_disk.sh todo_counter_pipe
```

Reference result:

```text
[check_ssot_disk] PASS: todo_counter_pipe/yaml/todo_counter_pipe.ssot.yaml = 68776B, 36 sections, 0 TBDs
```

Run an independent parse and summary check:

```bash
python3 - <<'PY'
import yaml, pathlib

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

Reference result:

```text
file_bytes 68776
top_keys 36
top_module todo_counter_pipe peripheral
sub_modules 3
registers 9
fm_state_variables 12
fm_transactions 10
cycle_stages 5
rtl_todos 4
assumptions 6
decomposition_type dict
```

## Literal TBD Scan

The validator checks for live placeholders, but a literal text scan is still
useful:

```bash
rg -n 'TBD|<TBD>' todo_counter_pipe/yaml/todo_counter_pipe.ssot.yaml
```

In the reference run, the validator reported `0 TBDs`, but a literal scan still
found two descriptive uses of `TBD` inside normal prose:

- One DFT note mentioning a future scan mux policy.
- One quality-gate phrase saying no live TBD placeholders are allowed.

If the desired policy is literal zero `TBD` strings, the validator and SSOT
rules should be tightened to reject any occurrence, including prose.

## Downstream Handoff

After SSOT validation, the next workflow should be `rtl-gen`.

Expected next command inside the appropriate workflow/session:

```text
/ssot-rtl todo_counter_pipe
```

Downstream ownership should be kept separate:

- `rtl-gen`: RTL source files, parameter/header intent, filelist, compile, lint
  readiness.
- `tb-gen`: cocotb TB, scoreboard, scenarios, functional/cycle coverage
  collection hooks.
- `sim`: simulation execution and waveform output.
- `sim_debug`: VCD/waveform/source/hierarchy/coverage inspection after sim
  outputs exist.
- `coverage`: report coverage against SSOT-declared function and cycle goals.
- `syn`: synthesis report.
- `sta`: pre-route STA report.
- `pnr`: place and route report.
- `sta-post`: post-route STA report.

`ssot-gen` should hand off requirements and ownership. It should not claim that
any downstream artifact has passed.

## Pipeline Mode Versus CI Mode

Use `pipeline` mode when the goal is to keep moving with conservative
assumptions:

- Non-blocking question behavior.
- Record assumptions in `custom.assumptions`.
- Continue to downstream-ready SSOT when gaps are not blocking.

Use `ci` mode when the goal is strict failure-on-gap behavior:

- Stop on missing required inputs.
- Do not silently assume.
- Better for regression testing workflow correctness.

For cold-run pipeline validation, `pipeline` mode is useful first. For production
workflow regression, use `ci` mode after the happy path is stable.

## Known Issues Observed

The reference run found two important workflow issues:

1. The TODO tracker initially stayed on phase 1 `pending` even while SSOT work
   was already happening. The operator had to explicitly move phases through
   `in_progress`, `completed`, and `approved` after evidence existed.

2. Incremental YAML replacement briefly left a duplicate top-level key:

```yaml
decomposition: TBD
```

This was caused by replacing one adjacent section with a block that also
contained the next section. The agent caught it during self-review, removed the
duplicate line, and revalidated the SSOT.

Recommended hardening:

- Start the current `/new-ip` TODO before tool work begins.
- Add duplicate top-level YAML key detection.
- Add stricter literal placeholder policy if desired.
- Ensure `check_ssot_disk.sh` validates section type, not only section presence.

## Session Logs

The reference run saved history here:

```text
.session/todo_pipeline/todo_counter_pipe/ssot-gen/input_history.txt
.session/todo_pipeline/todo_counter_pipe/ssot-gen/conversation.json
.session/todo_pipeline/todo_counter_pipe/ssot-gen/full_conversation.json
.session/todo_pipeline/todo_counter_pipe/ssot-gen/todo.json
```

The input history proves the user/operator provided only:

1. `/mode pipeline`
2. `/new-ip todo_counter_pipe counter`
3. The IP requirement seed prompt

The SSOT body itself was authored by `common_ai_agent` through the workflow.

## Minimal Reproduction Template

For a new IP:

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
python3 src/main.py -s <session_group>/<ip_name>/ssot-gen -w ssot-gen --model gpt-5.3-codex --effort medium
```

Inside the agent:

```text
/mode pipeline
/new-ip <ip_name> <ip_kind>
```

Then provide a concise but specific seed:

```text
Use the loaded /new-ip todo list and create only the canonical SSOT for IP <ip_name>.
IP intent: <purpose, clocks, resets, interfaces, parameters, registers, interrupts,
function behavior, cycle behavior, coverage goals, and downstream workflow todos>.
Pipeline mode: do not block on ask_user; make conservative assumptions and record
them in custom.assumptions. Do not generate RTL/TB/sim/lint/syn artifacts in ssot-gen.
```

Validate:

```bash
bash workflow/ssot-gen/scripts/check_ssot_disk.sh <ip_name>
```

Then hand off:

```text
/ssot-rtl <ip_name>
```
