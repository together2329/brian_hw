# RTL Authoring Packet: module__pl330realverify__features

- Kind: module
- Owner module: pl330realverify
- Owner file: rtl/pl330realverify.sv
- Task count: 6
- Required tasks: 6

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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 4/9 section=features task_limit=48
- Slice rule: Owner module pl330realverify is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_regs.clk_i <= dmaclk (sub_modules[0].connections[0])
  - pl330realverify_regs.rst_ni <= dmacresetn (sub_modules[0].connections[1])
  - pl330realverify_regs.paddr_i <= paddr (sub_modules[0].connections[2])
  - pl330realverify_regs.psel_i <= psel (sub_modules[0].connections[3])
  - pl330realverify_regs.penable_i <= penable (sub_modules[0].connections[4])
  - pl330realverify_regs.pwrite_i <= pwrite (sub_modules[0].connections[5])
  - pl330realverify_regs.pwdata_i <= pwdata (sub_modules[0].connections[6])
  - pl330realverify_regs.pstrb_i <= pstrb (sub_modules[0].connections[7])
  - pl330realverify_regs.prdata_o <= prdata (sub_modules[0].connections[8])
  - pl330realverify_regs.pready_o <= pready (sub_modules[0].connections[9])
  - pl330realverify_regs.pslverr_o <= pslverr (sub_modules[0].connections[10])
  - pl330realverify_regs.irq_o <= dmac_irq (sub_modules[0].connections[11])
- SSOT top IO contracts: 46

## Tasks

### RTL-0325: Implement feature APB programmable DMA channels

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.APB_programmable_DMA_channels
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.APB_programmable_DMA_channels.
Owner: pl330realverify in rtl/pl330realverify.sv via features.
SSOT item context: name=APB programmable DMA channels; output=APB read data, pslverr, channel status, and command pulses..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.APB_programmable_DMA_channels
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: features.APB_programmable_DMA_channels

### RTL-0326: Implement feature AXI memory-to-memory transfer

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.AXI_memory_to_memory_transfer
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.AXI_memory_to_memory_transfer.
Owner: pl330realverify in rtl/pl330realverify.sv via features.
SSOT item context: name=AXI memory-to-memory transfer; output=AXI read/write master transactions and completion status/interrupt..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.AXI_memory_to_memory_transfer
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: features.AXI_memory_to_memory_transfer

### RTL-0327: Implement feature Wait-for-peripheral event release

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Wait_for_peripheral_event_release
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Wait_for_peripheral_event_release.
Owner: pl330realverify in rtl/pl330realverify.sv via features.
SSOT item context: name=Wait-for-peripheral event release; output=No AXI traffic while waiting; normal transfer resumes after event..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Wait_for_peripheral_event_release
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: features.Wait_for_peripheral_event_release

### RTL-0328: Implement feature Interrupt pending/enable/W1C

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Interrupt_pending_enable_W1C
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Interrupt_pending_enable_W1C.
Owner: pl330realverify in rtl/pl330realverify.sv via features.
SSOT item context: name=Interrupt pending/enable/W1C; output=Active-high level dmac_irq and software-readable pending status..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Interrupt_pending_enable_W1C
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: features.Interrupt_pending_enable_W1C

### RTL-0329: Implement feature Debug command subset

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Debug_command_subset
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Debug_command_subset.
Owner: pl330realverify in rtl/pl330realverify.sv via features.
SSOT item context: name=Debug command subset; output=Debug pulse/status and parameterized debug-done interrupt controlled by INTEN.dbg_done_en..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Debug_command_subset
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: features.Debug_command_subset

### RTL-0330: Implement feature Fault classification and first-error-wins

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Fault_classification_and_first_error_wins
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Fault_classification_and_first_error_wins.
Owner: pl330realverify in rtl/pl330realverify.sv via features.
SSOT item context: name=Fault classification and first-error-wins; output=FAULTED status, CH_FAULT pending bit, and dmac_irq when enabled..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Fault_classification_and_first_error_wins
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: features.Fault_classification_and_first_error_wins
