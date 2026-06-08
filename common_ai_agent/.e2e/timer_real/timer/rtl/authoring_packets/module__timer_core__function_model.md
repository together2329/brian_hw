# RTL Authoring Packet: module__timer_core__function_model

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer_core.sv
- Task count: 3
- Required tasks: 3

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, dataflow.count_path, dataflow.irq_path, decomposition, features, fsm, function_model, function_model.state_variables, function_model.state_variables.count_q, function_model.state_variables.enable_q, function_model.state_variables.load_q, function_model.transactions.FM_DISABLED_HOLD
- Module slice: 1/8 section=function_model task_limit=48
- Slice rule: Owner module timer_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_core.pclk <= pclk (integration.connections[13])
  - timer_core.presetn <= presetn (integration.connections[14])
  - timer_core.load_q <= load_q (integration.connections[15])
  - timer_core.enable_q <= enable_q (integration.connections[16])
  - timer_core.count_q <= count_q (integration.connections[17])
  - timer_core.irq <= irq (integration.connections[18])

## Tasks

### RTL-0039: Implement RTL state owner for FL state load_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.load_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.load_q.
Owner: timer_core in rtl/timer_core.sv via function_model.state_variables.load_q.
SSOT item context: name=load_q; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.load_q
  - Primary implementation evidence is in rtl/timer_core.sv
  - load_q width matches SSOT value 32
  - load_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.load_q

### RTL-0040: Implement RTL state owner for FL state enable_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.enable_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.enable_q.
Owner: timer_core in rtl/timer_core.sv via function_model.state_variables.enable_q.
SSOT item context: name=enable_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.enable_q
  - Primary implementation evidence is in rtl/timer_core.sv
  - enable_q width matches SSOT value 1
  - enable_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.enable_q

### RTL-0041: Implement RTL state owner for FL state count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.count_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.count_q.
Owner: timer_core in rtl/timer_core.sv via function_model.state_variables.count_q.
SSOT item context: name=count_q; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.count_q
  - Primary implementation evidence is in rtl/timer_core.sv
  - count_q width matches SSOT value 32
  - count_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.count_q
