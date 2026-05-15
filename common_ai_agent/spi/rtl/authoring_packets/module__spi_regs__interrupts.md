# RTL Authoring Packet: module__spi_regs__interrupts

- Kind: module
- Owner module: spi_regs
- Owner file: rtl/spi_regs.sv
- Task count: 8
- Required tasks: 8

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: error_handling, error_handling.error_sources.access_policy_violation, error_handling.error_sources.illegal_apb_address, error_handling.error_sources.unsupported_write_strobe, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.config, registers.register_list, registers.register_list.CS_IDLE, registers.register_list.CTRL, registers.register_list.DEBUG, registers.register_list.PRESCALE, registers.register_list.RXDATA, registers.register_list.STATUS
- Module slice: 3/5 section=interrupts task_limit=48
- Slice rule: Owner module spi_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25

## Tasks

### RTL-0195: Implement interrupt item DONE

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.DONE
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.DONE.
Owner: spi_regs in rtl/spi_regs.sv via interrupts.
SSOT item context: name=DONE; clear=INT_CLEAR.W1C[0].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.DONE
  - Primary implementation evidence is in rtl/spi_regs.sv
  - DONE clear behavior matches SSOT clear policy INT_CLEAR.W1C[0]
- SSOT refs: interrupts.sources.DONE

### RTL-0196: Implement interrupt item TX_OVERRUN

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.TX_OVERRUN
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.TX_OVERRUN.
Owner: spi_regs in rtl/spi_regs.sv via interrupts.
SSOT item context: name=TX_OVERRUN; clear=INT_CLEAR.W1C[1].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.TX_OVERRUN
  - Primary implementation evidence is in rtl/spi_regs.sv
  - TX_OVERRUN clear behavior matches SSOT clear policy INT_CLEAR.W1C[1]
- SSOT refs: interrupts.sources.TX_OVERRUN

### RTL-0197: Implement interrupt item RX_OVERRUN

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.RX_OVERRUN
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.RX_OVERRUN.
Owner: spi_regs in rtl/spi_regs.sv via interrupts.
SSOT item context: name=RX_OVERRUN; clear=INT_CLEAR.W1C[2].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.RX_OVERRUN
  - Primary implementation evidence is in rtl/spi_regs.sv
  - RX_OVERRUN clear behavior matches SSOT clear policy INT_CLEAR.W1C[2]
- SSOT refs: interrupts.sources.RX_OVERRUN

### RTL-0198: Implement interrupt item RX_UNDERRUN

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.RX_UNDERRUN
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.RX_UNDERRUN.
Owner: spi_regs in rtl/spi_regs.sv via interrupts.
SSOT item context: name=RX_UNDERRUN; clear=INT_CLEAR.W1C[3].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.RX_UNDERRUN
  - Primary implementation evidence is in rtl/spi_regs.sv
  - RX_UNDERRUN clear behavior matches SSOT clear policy INT_CLEAR.W1C[3]
- SSOT refs: interrupts.sources.RX_UNDERRUN

### RTL-0199: Implement interrupt item MODE_FAULT

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.MODE_FAULT
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.MODE_FAULT.
Owner: spi_regs in rtl/spi_regs.sv via interrupts.
SSOT item context: name=MODE_FAULT; clear=INT_CLEAR.W1C[4].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.MODE_FAULT
  - Primary implementation evidence is in rtl/spi_regs.sv
  - MODE_FAULT clear behavior matches SSOT clear policy INT_CLEAR.W1C[4]
- SSOT refs: interrupts.sources.MODE_FAULT

### RTL-0200: Implement interrupt item ILLEGAL_ACCESS

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.ILLEGAL_ACCESS
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.ILLEGAL_ACCESS.
Owner: spi_regs in rtl/spi_regs.sv via interrupts.
SSOT item context: name=ILLEGAL_ACCESS; clear=INT_CLEAR.W1C[5].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.ILLEGAL_ACCESS
  - Primary implementation evidence is in rtl/spi_regs.sv
  - ILLEGAL_ACCESS clear behavior matches SSOT clear policy INT_CLEAR.W1C[5]
- SSOT refs: interrupts.sources.ILLEGAL_ACCESS

### RTL-0201: Implement interrupt item TX_EMPTY

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.TX_EMPTY
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.TX_EMPTY.
Owner: spi_regs in rtl/spi_regs.sv via interrupts.
SSOT item context: name=TX_EMPTY; clear=not_w1c.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.TX_EMPTY
  - Primary implementation evidence is in rtl/spi_regs.sv
  - TX_EMPTY clear behavior matches SSOT clear policy not_w1c
- SSOT refs: interrupts.sources.TX_EMPTY

### RTL-0202: Implement interrupt item RX_FULL

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.RX_FULL
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.RX_FULL.
Owner: spi_regs in rtl/spi_regs.sv via interrupts.
SSOT item context: name=RX_FULL; clear=not_w1c.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.RX_FULL
  - Primary implementation evidence is in rtl/spi_regs.sv
  - RX_FULL clear behavior matches SSOT clear policy not_w1c
- SSOT refs: interrupts.sources.RX_FULL
