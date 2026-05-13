# RTL Authoring Packet: module__cortex_m0lite__io_list

- Kind: module
- Owner module: cortex_m0lite
- Owner file: rtl/cortex_m0lite.sv
- Task count: 27
- Required tasks: 27

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
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cdc_requirements, clock_reset_domains, integration, integration.connections, internal_interfaces, io_list, io_list.interfaces
- Module slice: 2/7 section=io_list task_limit=48
- Slice rule: Owner module cortex_m0lite is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])
  - if_stage.clk <= clk (integration.connections[1])
  - if_stage.rst_n <= core_rst_n_sync (integration.connections[1])
  - if_stage.if_id_valid <= if_id_valid (integration.connections[1])
- SSOT top IO contracts: 27

## Tasks

### RTL-0045: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.core_clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.core_clk.ports.clk.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.core_clk.ports.clk
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.core_clk.ports.clk

### RTL-0046: Implement and connect port hclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.bus_clk.ports.hclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.bus_clk.ports.hclk.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=hclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.bus_clk.ports.hclk
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - hclk width matches SSOT value 1
  - hclk port direction remains input
- SSOT refs: io_list.clock_domains.bus_clk.ports.hclk

### RTL-0047: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.core_rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.core_rst_n.ports.rst_n.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.core_rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.core_rst_n.ports.rst_n

### RTL-0048: Implement and connect port hresetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.bus_rst_n.ports.hresetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.bus_rst_n.ports.hresetn.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=hresetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.bus_rst_n.ports.hresetn
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - hresetn width matches SSOT value 1
  - hresetn port direction remains input
- SSOT refs: io_list.resets.bus_rst_n.ports.hresetn

### RTL-0049: Implement and connect port i_haddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_haddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_haddr.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_haddr; width=AHB_ADDR_W; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_haddr
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_haddr width matches SSOT value AHB_ADDR_W
  - i_haddr port direction remains output
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_haddr

### RTL-0050: Implement and connect port i_htrans

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_htrans
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_htrans.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_htrans; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_htrans
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_htrans width matches SSOT value 2
  - i_htrans port direction remains output
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_htrans

### RTL-0051: Implement and connect port i_hwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_hwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_hwrite.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_hwrite; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_hwrite
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_hwrite width matches SSOT value 1
  - i_hwrite port direction remains output
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_hwrite

### RTL-0052: Implement and connect port i_hsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_hsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_hsize.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_hsize; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_hsize
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_hsize width matches SSOT value 3
  - i_hsize port direction remains output
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_hsize

### RTL-0053: Implement and connect port i_hburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_hburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_hburst.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_hburst; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_hburst
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_hburst width matches SSOT value 3
  - i_hburst port direction remains output
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_hburst

### RTL-0054: Implement and connect port i_hwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_hwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_hwdata.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_hwdata; width=AHB_DATA_W; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_hwdata
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_hwdata width matches SSOT value AHB_DATA_W
  - i_hwdata port direction remains output
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_hwdata

### RTL-0055: Implement and connect port i_hrdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_hrdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_hrdata.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_hrdata; width=AHB_DATA_W; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_hrdata
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_hrdata width matches SSOT value AHB_DATA_W
  - i_hrdata port direction remains input
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_hrdata

### RTL-0056: Implement and connect port i_hready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_hready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_hready.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_hready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_hready
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_hready width matches SSOT value 1
  - i_hready port direction remains input
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_hready

### RTL-0057: Implement and connect port i_hresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_ahb_m.ports.i_hresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_ahb_m.ports.i_hresp.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=i_hresp; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_ahb_m.ports.i_hresp
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - i_hresp width matches SSOT value 1
  - i_hresp port direction remains input
- SSOT refs: io_list.interfaces.instr_ahb_m.ports.i_hresp

### RTL-0058: Implement and connect port d_haddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_haddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_haddr.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_haddr; width=AHB_ADDR_W; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_haddr
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_haddr width matches SSOT value AHB_ADDR_W
  - d_haddr port direction remains output
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_haddr

### RTL-0059: Implement and connect port d_htrans

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_htrans
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_htrans.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_htrans; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_htrans
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_htrans width matches SSOT value 2
  - d_htrans port direction remains output
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_htrans

### RTL-0060: Implement and connect port d_hwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_hwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_hwrite.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_hwrite; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_hwrite
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_hwrite width matches SSOT value 1
  - d_hwrite port direction remains output
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_hwrite

### RTL-0061: Implement and connect port d_hsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_hsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_hsize.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_hsize; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_hsize
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_hsize width matches SSOT value 3
  - d_hsize port direction remains output
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_hsize

### RTL-0062: Implement and connect port d_hburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_hburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_hburst.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_hburst; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_hburst
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_hburst width matches SSOT value 3
  - d_hburst port direction remains output
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_hburst

### RTL-0063: Implement and connect port d_hwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_hwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_hwdata.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_hwdata; width=AHB_DATA_W; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_hwdata
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_hwdata width matches SSOT value AHB_DATA_W
  - d_hwdata port direction remains output
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_hwdata

### RTL-0064: Implement and connect port d_hrdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_hrdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_hrdata.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_hrdata; width=AHB_DATA_W; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_hrdata
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_hrdata width matches SSOT value AHB_DATA_W
  - d_hrdata port direction remains input
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_hrdata

### RTL-0065: Implement and connect port d_hready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_hready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_hready.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_hready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_hready
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_hready width matches SSOT value 1
  - d_hready port direction remains input
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_hready

### RTL-0066: Implement and connect port d_hresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_ahb_m.ports.d_hresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_ahb_m.ports.d_hresp.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=d_hresp; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_ahb_m.ports.d_hresp
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - d_hresp width matches SSOT value 1
  - d_hresp port direction remains input
- SSOT refs: io_list.interfaces.data_ahb_m.ports.d_hresp

### RTL-0067: Implement and connect port irq

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.irq_if.ports.irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.irq_if.ports.irq.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=irq; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.irq_if.ports.irq
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - irq width matches SSOT value 1
  - irq port direction remains input
- SSOT refs: io_list.interfaces.irq_if.ports.irq

### RTL-0068: Implement and connect port pc_dbg

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.debug_status.ports.pc_dbg
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.debug_status.ports.pc_dbg.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=pc_dbg; width=XLEN; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.debug_status.ports.pc_dbg
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - pc_dbg width matches SSOT value XLEN
  - pc_dbg port direction remains output
- SSOT refs: io_list.interfaces.debug_status.ports.pc_dbg

### RTL-0069: Implement and connect port state_dbg

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.debug_status.ports.state_dbg
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.debug_status.ports.state_dbg.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=state_dbg; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.debug_status.ports.state_dbg
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - state_dbg width matches SSOT value 3
  - state_dbg port direction remains output
- SSOT refs: io_list.interfaces.debug_status.ports.state_dbg

### RTL-0070: Implement and connect port retire

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.debug_status.ports.retire
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.debug_status.ports.retire.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=retire; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.debug_status.ports.retire
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - retire width matches SSOT value 1
  - retire port direction remains output
- SSOT refs: io_list.interfaces.debug_status.ports.retire

### RTL-0071: Implement and connect port trap

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.debug_status.ports.trap
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.debug_status.ports.trap.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via io_list.
SSOT item context: name=trap; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.debug_status.ports.trap
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - trap width matches SSOT value 1
  - trap port direction remains output
- SSOT refs: io_list.interfaces.debug_status.ports.trap
