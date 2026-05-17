# RTL Authoring Packet: module__pl330realverify_datapath

- Kind: module
- Owner module: pl330realverify_datapath
- Owner file: rtl/pl330realverify_datapath.sv
- Task count: 19
- Required tasks: 19

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: dataflow, dataflow.loop_control, dataflow.read_path, dataflow.write_path, decomposition.units.datapath, function_model, function_model.state_variables, function_model.transactions.FM_TRANSFER, function_model.transactions.FM_TRANSFER.state_updates, memory, memory.instances.rd_buf
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_datapath.clk_i <= dmaclk (sub_modules[4].connections[0])
  - pl330realverify_datapath.rst_ni <= dmacresetn (sub_modules[4].connections[1])
  - pl330realverify_datapath.src_addr_o <= araddr (sub_modules[4].connections[2])
  - pl330realverify_datapath.dst_addr_o <= awaddr (sub_modules[4].connections[3])
  - pl330realverify_datapath.rd_data_i <= rdata (sub_modules[4].connections[4])
  - pl330realverify_datapath.wr_data_o <= wdata (sub_modules[4].connections[5])
  - pl330realverify_datapath.rd_data_i <= rdata (integration.connections[19])
  - pl330realverify_datapath.wr_data_o <= wdata (integration.connections[20])

## Tasks

### RTL-0088: Implement RTL state owner for FL state sar

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.sar
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.sar.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=sar; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.sar
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - sar width matches SSOT value 32
  - sar reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.sar

### RTL-0089: Implement RTL state owner for FL state dar

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.dar
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.dar.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=dar; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.dar
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - dar width matches SSOT value 32
  - dar reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.dar

### RTL-0090: Implement RTL state owner for FL state loop_remaining

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.loop_remaining
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.loop_remaining.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=loop_remaining; width=8; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.loop_remaining
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - loop_remaining width matches SSOT value 8
  - loop_remaining reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.loop_remaining

### RTL-0091: Implement RTL state owner for FL state status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.status
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.status.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=status; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.status
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - status width matches SSOT value 4
  - status reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.status

### RTL-0092: Implement RTL state owner for FL state error_code

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.error_code
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.error_code.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=error_code; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.error_code
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - error_code width matches SSOT value 4
  - error_code reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.error_code

### RTL-0093: Implement RTL state owner for FL state rd_buf

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rd_buf
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rd_buf.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=rd_buf; width=64; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rd_buf
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - rd_buf width matches SSOT value 64
  - rd_buf reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.rd_buf

### RTL-0094: Implement RTL state owner for FL state intstatus

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.intstatus
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.intstatus.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=intstatus; width=32; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.intstatus
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - intstatus width matches SSOT value 32
  - intstatus reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.intstatus

### RTL-0095: Implement RTL state owner for FL state inten

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.inten
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.inten.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=inten; width=32; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.inten
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - inten width matches SSOT value 32
  - inten reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.inten

### RTL-0096: Implement RTL state owner for FL state pc

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.pc
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.pc.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.state_variables.
SSOT item context: name=pc; width=32; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.pc
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - pc width matches SSOT value 32
  - pc reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.pc

### RTL-0153: Implement state update for FM_TRANSFER: rd_buf

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TRANSFER.state_updates.rd_buf
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.state_updates.rd_buf.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.transactions.FM_TRANSFER.state_updates.
SSOT item context: name=rd_buf; expr=rdata if (rvalid == 1 and rready == 1 and rresp == 0) else rd_buf; width=64.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.state_updates.rd_buf
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - rd_buf width matches SSOT value 64
  - rd_buf RTL expression implements SSOT expression rdata if (rvalid == 1 and rready == 1 and rresp == 0) else rd_buf
  - rd_buf updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TRANSFER.state_updates.rd_buf

### RTL-0154: Implement state update for FM_TRANSFER: sar

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TRANSFER.state_updates.sar
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.state_updates.sar.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.transactions.FM_TRANSFER.state_updates.
SSOT item context: name=sar; expr=sar + (DATA_WIDTH // 8); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.state_updates.sar
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - sar width matches SSOT value 32
  - sar RTL expression implements SSOT expression sar + (DATA_WIDTH // 8)
  - sar updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TRANSFER.state_updates.sar

### RTL-0155: Implement state update for FM_TRANSFER: dar

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TRANSFER.state_updates.dar
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.state_updates.dar.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.transactions.FM_TRANSFER.state_updates.
SSOT item context: name=dar; expr=dar + (DATA_WIDTH // 8); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.state_updates.dar
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - dar width matches SSOT value 32
  - dar RTL expression implements SSOT expression dar + (DATA_WIDTH // 8)
  - dar updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TRANSFER.state_updates.dar

### RTL-0156: Implement state update for FM_TRANSFER: loop_remaining

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TRANSFER.state_updates.loop_remaining
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.state_updates.loop_remaining.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.transactions.FM_TRANSFER.state_updates.
SSOT item context: name=loop_remaining; expr=max(loop_remaining - 1, 0); width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.state_updates.loop_remaining
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - loop_remaining width matches SSOT value 8
  - loop_remaining RTL expression implements SSOT expression max(loop_remaining - 1, 0)
  - loop_remaining updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TRANSFER.state_updates.loop_remaining

### RTL-0157: Implement state update for FM_TRANSFER: status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TRANSFER.state_updates.status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.state_updates.status.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.transactions.FM_TRANSFER.state_updates.
SSOT item context: name=status; expr=6 if loop_remaining <= 1 else 1; width=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.state_updates.status
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - status width matches SSOT value 4
  - status RTL expression implements SSOT expression 6 if loop_remaining <= 1 else 1
  - status updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TRANSFER.state_updates.status

### RTL-0158: Implement state update for FM_TRANSFER: error_code

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TRANSFER.state_updates.error_code
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.state_updates.error_code.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.transactions.FM_TRANSFER.state_updates.
SSOT item context: name=error_code; expr=0; width=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.state_updates.error_code
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - error_code width matches SSOT value 4
  - error_code RTL expression implements SSOT expression 0
  - error_code updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TRANSFER.state_updates.error_code

### RTL-0159: Implement state update for FM_TRANSFER: intstatus

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TRANSFER.state_updates.intstatus
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.state_updates.intstatus.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via function_model.transactions.FM_TRANSFER.state_updates.
SSOT item context: name=intstatus; expr=intstatus | complete_irq_mask if loop_remaining <= 1 else intstatus; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.state_updates.intstatus
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - intstatus width matches SSOT value 32
  - intstatus RTL expression implements SSOT expression intstatus | complete_irq_mask if loop_remaining <= 1 else intstatus
  - intstatus updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TRANSFER.state_updates.intstatus

### RTL-0273: Implement memory item rd_buf

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.rd_buf
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.rd_buf.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via memory.instances.rd_buf.
SSOT item context: name=rd_buf; width=64; depth=1; reset=0; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.rd_buf
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - rd_buf width matches SSOT value 64
  - rd_buf reset behavior matches SSOT value 0
  - rd_buf timing uses SSOT cycle/latency 0
  - rd_buf storage depth matches SSOT value 1
- SSOT refs: memory.instances.rd_buf

### RTL-0274: Implement memory item channel_state_bank

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.channel_state_bank
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.channel_state_bank.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via memory.
SSOT item context: name=channel_state_bank; width=96; depth=8; reset=0; latency=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.channel_state_bank
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
  - channel_state_bank width matches SSOT value 96
  - channel_state_bank reset behavior matches SSOT value 0
  - channel_state_bank timing uses SSOT cycle/latency 0
  - channel_state_bank storage depth matches SSOT value 8
- SSOT refs: memory.instances.channel_state_bank

### RTL-0379: Prove module pl330realverify_datapath is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.pl330realverify_datapath.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330realverify_datapath.module_equivalence.
Owner: pl330realverify_datapath in rtl/pl330realverify_datapath.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330realverify_datapath.module_equivalence
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv
- SSOT refs: sub_modules.pl330realverify_datapath.module_equivalence
