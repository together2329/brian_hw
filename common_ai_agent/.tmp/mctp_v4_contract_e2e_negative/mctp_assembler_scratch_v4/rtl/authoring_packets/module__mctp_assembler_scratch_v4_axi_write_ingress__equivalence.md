# RTL Authoring Packet: module__mctp_assembler_scratch_v4_axi_write_ingress__equivalence

- Kind: module
- Owner module: mctp_assembler_scratch_v4_axi_write_ingress
- Owner file: rtl/mctp_assembler_scratch_v4_axi_write_ingress.sv
- Task count: 1
- Required tasks: 1

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
- Module slice: 5/7 section=equivalence task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_v4_axi_write_ingress is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_v4_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_v4_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])

## Tasks

### RTL-0421: Prove module mctp_assembler_scratch_v4_axi_write_ingress is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_v4_axi_write_ingress.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_v4_axi_write_ingress.module_equivalence.
Owner: mctp_assembler_scratch_v4_axi_write_ingress in rtl/mctp_assembler_scratch_v4_axi_write_ingress.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_v4_axi_write_ingress.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_axi_write_ingress.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_v4_axi_write_ingress.module_equivalence
