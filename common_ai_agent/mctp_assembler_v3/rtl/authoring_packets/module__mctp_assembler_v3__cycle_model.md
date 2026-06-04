# RTL Authoring Packet: module__mctp_assembler_v3__cycle_model

- Kind: module
- Owner module: mctp_assembler_v3
- Owner file: rtl/mctp_assembler_v3.sv
- Task count: 5
- Required tasks: 5

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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, decomposition, function_model, function_model.transactions, integration, integration.connections, io_list, io_list.interfaces, top_module
- Module slice: 5/9 section=cycle_model task_limit=48
- Slice rule: Owner module mctp_assembler_v3 is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_modules=9, min_source_files=10
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])
  - mctp_assembler_v3_sram_packer.sram_wr_valid_o <= sram_wr_valid (integration.connections[5])
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])
  - mctp_assembler_v3_cdc_sync.evt_fatal_internal_error_a <= 1'b0 (integration.connections[7])
- SSOT top IO contracts: 51

## Tasks

### RTL-0308: Implement pipeline stage: S0_INGEST

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_INGEST
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_INGEST.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via cycle_model.pipeline.
SSOT item context: stage=S0_INGEST; action=Reconstruct TLP bytes from AXI W beats; legality check; cycle=0..B.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_INGEST
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - cycle_model.pipeline.S0_INGEST timing uses SSOT cycle/latency 0..B
  - cycle_model.pipeline.S0_INGEST appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_INGEST

### RTL-0309: Implement pipeline stage: S1_VDM_DECODE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_VDM_DECODE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_VDM_DECODE.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via cycle_model.pipeline.
SSOT item context: stage=S1_VDM_DECODE; action=Decode/validate 16B PCIe VDM header; strip header/pad/digest; cycle=B+1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_VDM_DECODE
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - cycle_model.pipeline.S1_VDM_DECODE timing uses SSOT cycle/latency B+1
  - cycle_model.pipeline.S1_VDM_DECODE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_VDM_DECODE

### RTL-0311: Implement pipeline stage: S3_CONTEXT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S3_CONTEXT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S3_CONTEXT.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via cycle_model.pipeline.
SSOT item context: stage=S3_CONTEXT; action=Allocate/append context by key; sequence/timeout checks; cycle=B+3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S3_CONTEXT
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - cycle_model.pipeline.S3_CONTEXT timing uses SSOT cycle/latency B+3
  - cycle_model.pipeline.S3_CONTEXT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S3_CONTEXT

### RTL-0312: Implement pipeline stage: S4_PACK

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S4_PACK
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S4_PACK.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via cycle_model.pipeline.
SSOT item context: stage=S4_PACK; action=Pack payload bytes into 256-bit SRAM words; per-context partial word; cycle=B+4..P.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S4_PACK
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - cycle_model.pipeline.S4_PACK timing uses SSOT cycle/latency B+4..P
  - cycle_model.pipeline.S4_PACK appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S4_PACK

### RTL-0313: Implement pipeline stage: S5_DESCRIPTOR

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S5_DESCRIPTOR
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S5_DESCRIPTOR.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via cycle_model.pipeline.
SSOT item context: stage=S5_DESCRIPTOR; action=On EOM push descriptor + first/last headers; raise descriptor_ready; cycle=P+1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S5_DESCRIPTOR
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - cycle_model.pipeline.S5_DESCRIPTOR timing uses SSOT cycle/latency P+1
  - cycle_model.pipeline.S5_DESCRIPTOR appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S5_DESCRIPTOR
