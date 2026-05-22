# RTL Authoring Packet: module__dma_real_apb_cfg__io_list

- Kind: module
- Owner module: dma_real_apb_cfg
- Owner file: rtl/dma_real_apb_cfg.sv
- Task count: 17
- Required tasks: 17

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
- Owner refs: dataflow.ordering.ordering_0, dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, function_model.state_variables, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 1/8 section=io_list task_limit=48
- Slice rule: Owner module dma_real_apb_cfg is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0035: Implement and connect port pclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk_domain.ports.pclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk_domain.ports.pclk.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=pclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk_domain.ports.pclk
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - pclk width matches SSOT value 1
  - pclk port direction remains input
- SSOT refs: io_list.clock_domains.pclk_domain.ports.pclk

### RTL-0036: Implement and connect port hclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.hclk_domain.ports.hclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.hclk_domain.ports.hclk.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=hclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.hclk_domain.ports.hclk
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - hclk width matches SSOT value 1
  - hclk port direction remains input
- SSOT refs: io_list.clock_domains.hclk_domain.ports.hclk

### RTL-0037: Implement and connect port presetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.presetn_domain.ports.presetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn_domain.ports.presetn.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=presetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.presetn_domain.ports.presetn
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - presetn width matches SSOT value 1
  - presetn port direction remains input
- SSOT refs: io_list.resets.presetn_domain.ports.presetn

### RTL-0038: Implement and connect port hresetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.hresetn_domain.ports.hresetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.hresetn_domain.ports.hresetn.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=hresetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.hresetn_domain.ports.hresetn
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - hresetn width matches SSOT value 1
  - hresetn port direction remains input
- SSOT refs: io_list.resets.hresetn_domain.ports.hresetn

### RTL-0039: Implement and connect port psel

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.psel.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.psel
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.psel

### RTL-0040: Implement and connect port penable

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.penable.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.penable
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.penable

### RTL-0041: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwrite.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwrite
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwrite

### RTL-0042: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.paddr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
SSOT item context: name=paddr; width=12; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.paddr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - paddr width matches SSOT value 12
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.paddr

### RTL-0043: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwdata.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pwdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwdata
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - pwdata width matches SSOT value 32
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwdata

### RTL-0044: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.prdata.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
SSOT item context: name=prdata; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.prdata
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - prdata width matches SSOT value 32
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.prdata

### RTL-0045: Implement and connect port pready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pready.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pready
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - pready width matches SSOT value 1
  - pready port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pready

### RTL-0046: Implement and connect port pslverr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pslverr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pslverr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pslverr; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pslverr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - pslverr width matches SSOT value 1
  - pslverr port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pslverr

### RTL-0063: Implement and connect port ch_busy

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.dma_status.ports.ch_busy
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_status.ports.ch_busy.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=ch_busy; width=N_CHANNELS; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_status.ports.ch_busy
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_busy width matches SSOT value N_CHANNELS
  - ch_busy port direction remains output
- SSOT refs: io_list.interfaces.dma_status.ports.ch_busy

### RTL-0064: Implement and connect port ch_done

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.dma_status.ports.ch_done
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_status.ports.ch_done.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=ch_done; width=N_CHANNELS; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_status.ports.ch_done
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_done width matches SSOT value N_CHANNELS
  - ch_done port direction remains output
- SSOT refs: io_list.interfaces.dma_status.ports.ch_done

### RTL-0065: Implement and connect port ch_error

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.dma_status.ports.ch_error
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_status.ports.ch_error.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=ch_error; width=N_CHANNELS; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_status.ports.ch_error
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_error width matches SSOT value N_CHANNELS
  - ch_error port direction remains output
- SSOT refs: io_list.interfaces.dma_status.ports.ch_error

### RTL-0066: Implement and connect port ch_err_code

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.dma_status.ports.ch_err_code
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_status.ports.ch_err_code.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=ch_err_code; width=8; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_status.ports.ch_err_code
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_err_code width matches SSOT value 8
  - ch_err_code port direction remains output
- SSOT refs: io_list.interfaces.dma_status.ports.ch_err_code

### RTL-0067: Implement and connect port arb_grant

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.dma_status.ports.arb_grant
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_status.ports.arb_grant.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.
SSOT item context: name=arb_grant; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_status.ports.arb_grant
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - arb_grant width matches SSOT value 3
  - arb_grant port direction remains output
- SSOT refs: io_list.interfaces.dma_status.ports.arb_grant
