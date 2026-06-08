# RTL Authoring Packet: module__timer_regs__function_model_02

- Kind: module
- Owner module: timer_regs
- Owner file: rtl/timer_regs.sv
- Task count: 48
- Required tasks: 48

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
- Owner refs: error_handling, function_model, function_model.invariants, function_model.state_variables, function_model.transactions.FM_APB_READ_STATUS, function_model.transactions.FM_APB_UNMAPPED_ACCESS, function_model.transactions.FM_APB_WRITE_CTRL, function_model.transactions.FM_APB_WRITE_LOAD, function_model.transactions.FM_DISABLED_HOLD, function_model.transactions.FM_TICK_DECREMENT, function_model.transactions.FM_TICK_RELOAD_IRQ, registers, registers.register_list, registers.register_list.CTRL, registers.register_list.LOAD, registers.register_list.STATUS
- Module slice: 2/7 section=function_model task_limit=48
- Slice rule: Owner module timer_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_regs.pclk <= pclk (integration.connections[0])
  - timer_regs.presetn <= presetn (integration.connections[1])
  - timer_regs.paddr <= paddr (integration.connections[2])
  - timer_regs.psel <= psel (integration.connections[3])
  - timer_regs.penable <= penable (integration.connections[4])
  - timer_regs.pwrite <= pwrite (integration.connections[5])
  - timer_regs.pwdata <= pwdata (integration.connections[6])
  - timer_regs.prdata <= prdata (integration.connections[7])
  - timer_regs.pready <= pready (integration.connections[8])
  - timer_regs.pslverr <= pslverr (integration.connections[9])
  - timer_regs.load_q <= load_q (integration.connections[10])
  - timer_regs.enable_q <= enable_q (integration.connections[11])

## Tasks

### RTL-0090: Implement precondition for FM_TICK_DECREMENT: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TICK_DECREMENT.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.preconditions.precondition_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: value=psel == 0 and enable_q == 1 and count_q > 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.preconditions.precondition_0

### RTL-0091: Implement output for FM_TICK_DECREMENT: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK_DECREMENT.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.outputs.output_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: value=irq == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.outputs.output_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.outputs.output_0

### RTL-0092: Implement output for FM_TICK_DECREMENT: irq_decrement

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK_DECREMENT.outputs.irq_decrement
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.outputs.irq_decrement.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: name=irq_decrement; port=irq; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.outputs.irq_decrement
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_decrement RTL expression implements SSOT expression 0
  - DUT port irq is the implementation/observation point for irq_decrement
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.outputs.irq_decrement

### RTL-0093: Implement output for FM_TICK_DECREMENT: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK_DECREMENT.outputs.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.outputs.count_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: state=count_q; expr=(count_q - 1) & 0xffffffff.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.outputs.count_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_TICK_DECREMENT.outputs.count_q RTL expression implements SSOT expression (count_q - 1) & 0xffffffff
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.outputs.count_q

### RTL-0094: Implement output for FM_TICK_DECREMENT: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK_DECREMENT.outputs.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.outputs.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: state=irq_q; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.outputs.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_TICK_DECREMENT.outputs.irq_q RTL expression implements SSOT expression 0
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.outputs.irq_q

### RTL-0095: Implement output rule for FM_TICK_DECREMENT: irq_decrement

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TICK_DECREMENT.output_rules.irq_decrement
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.output_rules.irq_decrement.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: name=irq_decrement; port=irq; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.output_rules.irq_decrement
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_decrement width matches SSOT value 1
  - irq_decrement RTL expression implements SSOT expression 0
  - DUT port irq is the implementation/observation point for irq_decrement
  - irq_decrement is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.output_rules.irq_decrement

### RTL-0096: Implement state update for FM_TICK_DECREMENT: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TICK_DECREMENT.state_updates.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.state_updates.count_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: name=count_q; expr=(count_q - 1) & 0xffffffff; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.state_updates.count_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - count_q width matches SSOT value 32
  - count_q RTL expression implements SSOT expression (count_q - 1) & 0xffffffff
  - count_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.state_updates.count_q

### RTL-0097: Implement state update for FM_TICK_DECREMENT: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TICK_DECREMENT.state_updates.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.state_updates.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: name=irq_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.state_updates.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_q width matches SSOT value 1
  - irq_q RTL expression implements SSOT expression 0
  - irq_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.state_updates.irq_q

### RTL-0098: Implement side effect for FM_TICK_DECREMENT: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TICK_DECREMENT.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.side_effects.side_effect_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: id=FM_TICK_DECREMENT; name=enabled_decrement_nonzero; port=["irq"]; signal=["count_q decrements by one modulo 32-bit range."]; state=["count_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["irq"] is the implementation/observation point for enabled_decrement_nonzero
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.side_effects.side_effect_0

### RTL-0099: Implement side effect for FM_TICK_DECREMENT: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TICK_DECREMENT.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.side_effects.side_effect_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: id=FM_TICK_DECREMENT; name=enabled_decrement_nonzero; port=["irq"]; signal=["irq_q remains 0."]; state=["count_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["irq"] is the implementation/observation point for enabled_decrement_nonzero
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT.side_effects.side_effect_1

### RTL-0100: Implement transaction FM_TICK_RELOAD_IRQ

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: id=FM_TICK_RELOAD_IRQ; name=enabled_zero_reload_and_irq_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ

### RTL-0101: Implement precondition for FM_TICK_RELOAD_IRQ: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.preconditions.precondition_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: value=psel == 0 and enable_q == 1 and count_q == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.preconditions.precondition_0

### RTL-0102: Implement output for FM_TICK_RELOAD_IRQ: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.output_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: value=irq == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.output_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.output_0

### RTL-0103: Implement output for FM_TICK_RELOAD_IRQ: irq_reload

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_reload
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_reload.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: name=irq_reload; port=irq; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_reload
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_reload RTL expression implements SSOT expression 1
  - DUT port irq is the implementation/observation point for irq_reload
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_reload

### RTL-0104: Implement output for FM_TICK_RELOAD_IRQ: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.count_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: state=count_q; expr=load_q & 0xffffffff.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.count_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.count_q RTL expression implements SSOT expression load_q & 0xffffffff
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.count_q

### RTL-0105: Implement output for FM_TICK_RELOAD_IRQ: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: state=irq_q; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_q RTL expression implements SSOT expression 1
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_q

### RTL-0106: Implement output rule for FM_TICK_RELOAD_IRQ: irq_reload

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.output_rules.irq_reload
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.output_rules.irq_reload.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: name=irq_reload; port=irq; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.output_rules.irq_reload
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_reload width matches SSOT value 1
  - irq_reload RTL expression implements SSOT expression 1
  - DUT port irq is the implementation/observation point for irq_reload
  - irq_reload is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.output_rules.irq_reload

### RTL-0107: Implement state update for FM_TICK_RELOAD_IRQ: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.count_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: name=count_q; expr=load_q & 0xffffffff; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.count_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - count_q width matches SSOT value 32
  - count_q RTL expression implements SSOT expression load_q & 0xffffffff
  - count_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.count_q

### RTL-0108: Implement state update for FM_TICK_RELOAD_IRQ: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: name=irq_q; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_q width matches SSOT value 1
  - irq_q RTL expression implements SSOT expression 1
  - irq_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.irq_q

### RTL-0109: Implement side effect for FM_TICK_RELOAD_IRQ: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: id=FM_TICK_RELOAD_IRQ; name=enabled_zero_reload_and_irq_pulse; port=["irq"]; signal=["irq_q asserts for this cycle."]; state=["count_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["irq"] is the implementation/observation point for enabled_zero_reload_and_irq_pulse
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_0

### RTL-0110: Implement side effect for FM_TICK_RELOAD_IRQ: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: id=FM_TICK_RELOAD_IRQ; name=enabled_zero_reload_and_irq_pulse; port=["irq"]; signal=["count_q reloads from load_q."]; state=["count_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["irq"] is the implementation/observation point for enabled_zero_reload_and_irq_pulse
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_1

### RTL-0111: Implement side effect for FM_TICK_RELOAD_IRQ: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_2.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_RELOAD_IRQ.
SSOT item context: id=FM_TICK_RELOAD_IRQ; name=enabled_zero_reload_and_irq_pulse; port=["irq"]; signal=["Timer continues enabled unless CTRL.ENABLE is later cleared."]; state=["count_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["irq"] is the implementation/observation point for enabled_zero_reload_and_irq_pulse
- SSOT refs: function_model.transactions.FM_TICK_RELOAD_IRQ.side_effects.side_effect_2

### RTL-0112: Implement transaction FM_DISABLED_HOLD

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DISABLED_HOLD
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: id=FM_DISABLED_HOLD; name=disabled_hold_count.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD

### RTL-0113: Implement precondition for FM_DISABLED_HOLD: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DISABLED_HOLD.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.preconditions.precondition_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: value=psel == 0 and enable_q == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.preconditions.precondition_0

### RTL-0114: Implement output for FM_DISABLED_HOLD: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DISABLED_HOLD.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.outputs.output_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: value=irq == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.outputs.output_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.outputs.output_0

### RTL-0115: Implement output for FM_DISABLED_HOLD: irq_disabled

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DISABLED_HOLD.outputs.irq_disabled
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.outputs.irq_disabled.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: name=irq_disabled; port=irq; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.outputs.irq_disabled
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_disabled RTL expression implements SSOT expression 0
  - DUT port irq is the implementation/observation point for irq_disabled
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.outputs.irq_disabled

### RTL-0116: Implement output for FM_DISABLED_HOLD: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DISABLED_HOLD.outputs.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.outputs.count_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: state=count_q; expr=count_q & 0xffffffff.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.outputs.count_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_DISABLED_HOLD.outputs.count_q RTL expression implements SSOT expression count_q & 0xffffffff
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.outputs.count_q

### RTL-0117: Implement output for FM_DISABLED_HOLD: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DISABLED_HOLD.outputs.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.outputs.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: state=irq_q; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.outputs.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_DISABLED_HOLD.outputs.irq_q RTL expression implements SSOT expression 0
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.outputs.irq_q

### RTL-0118: Implement output rule for FM_DISABLED_HOLD: irq_disabled

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DISABLED_HOLD.output_rules.irq_disabled
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.output_rules.irq_disabled.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: name=irq_disabled; port=irq; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.output_rules.irq_disabled
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_disabled width matches SSOT value 1
  - irq_disabled RTL expression implements SSOT expression 0
  - DUT port irq is the implementation/observation point for irq_disabled
  - irq_disabled is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.output_rules.irq_disabled

### RTL-0119: Implement state update for FM_DISABLED_HOLD: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DISABLED_HOLD.state_updates.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.state_updates.count_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: name=count_q; expr=count_q & 0xffffffff; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.state_updates.count_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - count_q width matches SSOT value 32
  - count_q RTL expression implements SSOT expression count_q & 0xffffffff
  - count_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.state_updates.count_q

### RTL-0120: Implement state update for FM_DISABLED_HOLD: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DISABLED_HOLD.state_updates.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.state_updates.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: name=irq_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.state_updates.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_q width matches SSOT value 1
  - irq_q RTL expression implements SSOT expression 0
  - irq_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.state_updates.irq_q

### RTL-0121: Implement side effect for FM_DISABLED_HOLD: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DISABLED_HOLD.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.side_effects.side_effect_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: id=FM_DISABLED_HOLD; name=disabled_hold_count; port=["irq"]; signal=["count_q holds its current value while disabled."]; state=["count_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["irq"] is the implementation/observation point for disabled_hold_count
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.side_effects.side_effect_0

### RTL-0122: Implement side effect for FM_DISABLED_HOLD: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DISABLED_HOLD.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DISABLED_HOLD.side_effects.side_effect_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_DISABLED_HOLD.
SSOT item context: id=FM_DISABLED_HOLD; name=disabled_hold_count; port=["irq"]; signal=["irq_q remains 0."]; state=["count_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DISABLED_HOLD.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["irq"] is the implementation/observation point for disabled_hold_count
- SSOT refs: function_model.transactions.FM_DISABLED_HOLD.side_effects.side_effect_1

### RTL-0123: Implement transaction FM_APB_UNMAPPED_ACCESS

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: id=FM_APB_UNMAPPED_ACCESS; name=unmapped_apb_access_error.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS

### RTL-0124: Implement precondition for FM_APB_UNMAPPED_ACCESS: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.preconditions.precondition_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: value=psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.preconditions.precondition_0

### RTL-0125: Implement input for FM_APB_UNMAPPED_ACCESS: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.inputs.input_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: id=FM_APB_UNMAPPED_ACCESS; name=unmapped_apb_access_error; port=["pready", "pslverr"]; signal=["paddr"]; state=["irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.inputs.input_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for unmapped_apb_access_error
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.inputs.input_0

### RTL-0126: Implement output for FM_APB_UNMAPPED_ACCESS: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.output_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: value=pready == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.output_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.output_0

### RTL-0127: Implement output for FM_APB_UNMAPPED_ACCESS: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.output_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: value=pslverr == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.output_1
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.output_1

### RTL-0128: Implement output for FM_APB_UNMAPPED_ACCESS: pready_unmapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.pready_unmapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.pready_unmapped.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: name=pready_unmapped; port=pready; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.pready_unmapped
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pready_unmapped RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for pready_unmapped
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.pready_unmapped

### RTL-0129: Implement output for FM_APB_UNMAPPED_ACCESS: pslverr_unmapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.pslverr_unmapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.pslverr_unmapped.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: name=pslverr_unmapped; port=pslverr; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.pslverr_unmapped
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pslverr_unmapped RTL expression implements SSOT expression 1
  - DUT port pslverr is the implementation/observation point for pslverr_unmapped
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.pslverr_unmapped

### RTL-0130: Implement output for FM_APB_UNMAPPED_ACCESS: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: state=irq_q; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.irq_q RTL expression implements SSOT expression 0
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.irq_q

### RTL-0131: Implement output rule for FM_APB_UNMAPPED_ACCESS: pready_unmapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.output_rules.pready_unmapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.output_rules.pready_unmapped.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: name=pready_unmapped; port=pready; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.output_rules.pready_unmapped
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pready_unmapped width matches SSOT value 1
  - pready_unmapped RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for pready_unmapped
  - pready_unmapped is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.output_rules.pready_unmapped

### RTL-0132: Implement output rule for FM_APB_UNMAPPED_ACCESS: pslverr_unmapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.output_rules.pslverr_unmapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.output_rules.pslverr_unmapped.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: name=pslverr_unmapped; port=pslverr; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.output_rules.pslverr_unmapped
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pslverr_unmapped width matches SSOT value 1
  - pslverr_unmapped RTL expression implements SSOT expression 1
  - DUT port pslverr is the implementation/observation point for pslverr_unmapped
  - pslverr_unmapped is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.output_rules.pslverr_unmapped

### RTL-0133: Implement state update for FM_APB_UNMAPPED_ACCESS: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.state_updates.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.state_updates.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: name=irq_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.state_updates.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_q width matches SSOT value 1
  - irq_q RTL expression implements SSOT expression 0
  - irq_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.state_updates.irq_q

### RTL-0134: Implement side effect for FM_APB_UNMAPPED_ACCESS: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.side_effects.side_effect_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: id=FM_APB_UNMAPPED_ACCESS; name=unmapped_apb_access_error; port=["pready", "pslverr"]; signal=["No architectural register or counter state changes on unmapped access."]; state=["irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for unmapped_apb_access_error
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.side_effects.side_effect_0

### RTL-0135: Implement error case for FM_APB_UNMAPPED_ACCESS: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_UNMAPPED_ACCESS.error_cases.error_case_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_UNMAPPED_ACCESS.
SSOT item context: id=FM_APB_UNMAPPED_ACCESS; name=unmapped_apb_access_error; port=["pready", "pslverr"]; signal=[{"condition": "paddr != 0 and paddr != 4 and paddr != 8", "result": "pslverr is asserted for the accepted transfer."}]; state=["irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_UNMAPPED_ACCESS.error_cases.error_case_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for unmapped_apb_access_error
- SSOT refs: function_model.transactions.FM_APB_UNMAPPED_ACCESS.error_cases.error_case_0

### RTL-0136: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.invariants.
SSOT item context: port=["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq"]; signal=count_q >= 0 and count_q <= 0xffffffff; state=["count_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq"] is the implementation/observation point for ["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0137: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.invariants.
SSOT item context: port=["pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq"]; signal=load_q >= 0 and load_q <= 0xffffffff; state=["load_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq"] is the implementation/observation point for ["pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq"]
- SSOT refs: function_model.invariants.invariant_1
