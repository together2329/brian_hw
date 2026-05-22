# RTL Authoring Packet: unowned_tasks

- Kind: unowned
- Owner module: <none>
- Owner file: <none>
- Task count: 2
- Required tasks: 2

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
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- SSOT connection contracts:
  - arm_m0_min_if.i_haddr <= i_haddr (integration.connections[0])
  - arm_m0_min_if.i_htrans <= i_htrans (integration.connections[1])
  - arm_m0_min_if.i_hready <= i_hready (integration.connections[2])
  - arm_m0_min_if.i_hrdata <= i_hrdata (integration.connections[3])
  - arm_m0_min_if.i_hresp <= i_hresp (integration.connections[4])
  - arm_m0_min_ex.d_haddr <= d_haddr (integration.connections[5])
  - arm_m0_min_ex.d_htrans <= d_htrans (integration.connections[6])
  - arm_m0_min_ex.d_hwrite <= d_hwrite (integration.connections[7])
  - arm_m0_min_ex.d_hwdata <= d_hwdata (integration.connections[8])
  - arm_m0_min_ex.d_hready <= d_hready (integration.connections[9])
  - arm_m0_min_ex.d_hrdata <= d_hrdata (integration.connections[10])
  - arm_m0_min_ex.d_hresp <= d_hresp (integration.connections[11])

## Tasks

### RTL-0102: Implement memory item if_id_instr

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.if_id_instr
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.if_id_instr.
SSOT item context: name=if_id_instr; width=32; depth=1; latency=0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.if_id_instr
  - if_id_instr width matches SSOT value 32
  - if_id_instr timing uses SSOT cycle/latency 0
  - if_id_instr storage depth matches SSOT value 1
- SSOT refs: memory.instances.if_id_instr

### RTL-0103: Implement memory item id_ex_ctrl

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.id_ex_ctrl
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.id_ex_ctrl.
SSOT item context: name=id_ex_ctrl; width=64; depth=1; latency=0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.id_ex_ctrl
  - id_ex_ctrl width matches SSOT value 64
  - id_ex_ctrl timing uses SSOT cycle/latency 0
  - id_ex_ctrl storage depth matches SSOT value 1
- SSOT refs: memory.instances.id_ex_ctrl
