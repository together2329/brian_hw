# RTL Authoring Packet: module__pl330_target__io_list

- Kind: module
- Owner module: pl330_target
- Owner file: rtl/pl330_target.sv
- Task count: 9
- Required tasks: 9

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: False
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Module slice: 2/10 section=io_list task_limit=48
- Slice rule: Owner module pl330_target is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_engine.busy <= engine_busy (observed_named_port_map)
  - pl330_target_engine.channel_state <= engine_channel_state (observed_named_port_map)
  - pl330_target_engine.clk <= clk (observed_named_port_map)
  - pl330_target_engine.cmd_channel <= engine_cmd_channel (observed_named_port_map)
  - pl330_target_engine.cmd_dst_addr <= engine_cmd_dst_addr (observed_named_port_map)
  - pl330_target_engine.cmd_len <= engine_cmd_len (observed_named_port_map)
  - pl330_target_engine.cmd_opcode <= engine_cmd_opcode (observed_named_port_map)
  - pl330_target_engine.cmd_privileged <= engine_cmd_privileged (observed_named_port_map)
- SSOT top IO contracts: 11

## Tasks

### RTL-0102: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/pl330_target.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0103: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/pl330_target.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0104: Implement and connect port req_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control_data.ports.req_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control_data.ports.req_valid.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=req_valid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control_data.ports.req_valid
  - Primary implementation evidence is in rtl/pl330_target.sv
  - req_valid width matches SSOT value 1
  - req_valid port direction remains input
- SSOT refs: io_list.interfaces.control_data.ports.req_valid

### RTL-0105: Implement and connect port req_ready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control_data.ports.req_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control_data.ports.req_ready.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=req_ready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control_data.ports.req_ready
  - Primary implementation evidence is in rtl/pl330_target.sv
  - req_ready width matches SSOT value 1
  - req_ready port direction remains output
- SSOT refs: io_list.interfaces.control_data.ports.req_ready

### RTL-0106: Implement and connect port req_data

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control_data.ports.req_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control_data.ports.req_data.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=req_data; width=DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control_data.ports.req_data
  - Primary implementation evidence is in rtl/pl330_target.sv
  - req_data width matches SSOT value DATA_WIDTH
  - req_data port direction remains input
- SSOT refs: io_list.interfaces.control_data.ports.req_data

### RTL-0107: Implement and connect port rsp_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control_data.ports.rsp_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control_data.ports.rsp_valid.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=rsp_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control_data.ports.rsp_valid
  - Primary implementation evidence is in rtl/pl330_target.sv
  - rsp_valid width matches SSOT value 1
  - rsp_valid port direction remains output
- SSOT refs: io_list.interfaces.control_data.ports.rsp_valid

### RTL-0108: Implement and connect port rsp_ready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control_data.ports.rsp_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control_data.ports.rsp_ready.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=rsp_ready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control_data.ports.rsp_ready
  - Primary implementation evidence is in rtl/pl330_target.sv
  - rsp_ready width matches SSOT value 1
  - rsp_ready port direction remains input
- SSOT refs: io_list.interfaces.control_data.ports.rsp_ready

### RTL-0109: Implement and connect port rsp_data

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control_data.ports.rsp_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control_data.ports.rsp_data.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=rsp_data; width=DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control_data.ports.rsp_data
  - Primary implementation evidence is in rtl/pl330_target.sv
  - rsp_data width matches SSOT value DATA_WIDTH
  - rsp_data port direction remains output
- SSOT refs: io_list.interfaces.control_data.ports.rsp_data

### RTL-0110: Implement and connect port error

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control_data.ports.error
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control_data.ports.error.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=error; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control_data.ports.error
  - Primary implementation evidence is in rtl/pl330_target.sv
  - error width matches SSOT value 1
  - error port direction remains output
- SSOT refs: io_list.interfaces.control_data.ports.error
