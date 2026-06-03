# RTL Authoring Packet: module__mctp_assembler_scratch_v5_axi_write_ingress__dataflow

- Kind: module
- Owner module: mctp_assembler_scratch_v5_axi_write_ingress
- Owner file: rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- Task count: 7
- Required tasks: 7

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
- Owner refs: cycle_model, cycle_model.handshake_rules.axi_write_channels, dataflow, function_model, function_model.transactions.FM_ACCEPT_AXI_TLP, io_list, io_list.interfaces.axi_write_slave, test_requirements
- Module slice: 7/7 section=dataflow task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_v5_axi_write_ingress is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_v5_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_v5_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])

## Tasks

### RTL-0389: Implement dataflow sequence: sequence_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_0.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via dataflow.
SSOT item context: value=axi_write_ingress.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: dataflow.sequence.sequence_0

### RTL-0390: Implement dataflow sequence: sequence_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_1.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via dataflow.
SSOT item context: value=pcie_vdm_parse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: dataflow.sequence.sequence_1

### RTL-0391: Implement dataflow sequence: sequence_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_2.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via dataflow.
SSOT item context: value=mctp_parse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: dataflow.sequence.sequence_2

### RTL-0392: Implement dataflow sequence: sequence_3

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_3
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_3.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via dataflow.
SSOT item context: value=context_assembly.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_3
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: dataflow.sequence.sequence_3

### RTL-0393: Implement dataflow sequence: sequence_4

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_4
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_4.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via dataflow.
SSOT item context: value=sram_pack.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_4
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: dataflow.sequence.sequence_4

### RTL-0394: Implement dataflow sequence: sequence_5

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_5
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_5.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via dataflow.
SSOT item context: value=descriptor_publish.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_5
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: dataflow.sequence.sequence_5

### RTL-0395: Implement dataflow sequence: sequence_6

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_6
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_6.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via dataflow.
SSOT item context: value=axi_readback.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_6
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: dataflow.sequence.sequence_6
