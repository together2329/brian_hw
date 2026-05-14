# RTL Authoring Packet: module__timer_core__coverage

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer.sv
- Task count: 3
- Required tasks: 3

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, fsm, function_model, function_model.transactions.FM_TICK, io_list, parameters, rtl_contract
- Module slice: 14/17 section=coverage task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0102: Provide RTL evidence for coverage bin fcov_start_load

- Priority: normal
- Required: True
- Status: pass
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.fcov_start_load
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.fcov_start_load.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: id=fcov_start_load.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.fcov_start_load
  - Primary implementation evidence is in rtl/timer.sv
  - fcov_start_load can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.fcov_start_load

### RTL-0103: Provide RTL evidence for coverage bin fcov_done_pulse

- Priority: normal
- Required: True
- Status: pass
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.fcov_done_pulse
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.fcov_done_pulse.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: id=fcov_done_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.fcov_done_pulse
  - Primary implementation evidence is in rtl/timer.sv
  - fcov_done_pulse can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.fcov_done_pulse

### RTL-0104: Provide RTL evidence for coverage bin ccov_terminal_tick

- Priority: normal
- Required: True
- Status: pass
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.ccov_terminal_tick
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.ccov_terminal_tick.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: id=ccov_terminal_tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.ccov_terminal_tick
  - Primary implementation evidence is in rtl/timer.sv
  - ccov_terminal_tick can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.ccov_terminal_tick
