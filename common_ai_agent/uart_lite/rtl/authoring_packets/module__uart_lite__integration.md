# RTL Authoring Packet: module__uart_lite__integration

- Kind: module
- Owner module: uart_lite
- Owner file: rtl/uart_lite.sv
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
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 4/8 section=integration task_limit=48
- Slice rule: Owner module uart_lite is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])
  - uart_lite_regs.uart_irq_o <= uart_irq (integration.connections[2])
  - uart_lite_core.tx_o <= tx (integration.connections[3])
  - uart_lite_core.rx_i <= rx (integration.connections[4])
- SSOT top IO contracts: 14

## Tasks

### RTL-0247: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0248: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: name=external_clocks; value=["PCLK"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0249: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: name=external_resets; value=["PRESETn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0250: Implement integration item PCLK

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: port=PCLK; signal=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/uart_lite.sv
  - DUT port PCLK is the implementation/observation point for PCLK
- SSOT refs: integration.connections.PCLK

### RTL-0251: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: port=PRESETn; signal=PRESETn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/uart_lite.sv
  - DUT port PRESETn is the implementation/observation point for PRESETn
- SSOT refs: integration.connections.PRESETn

### RTL-0252: Implement integration item uart_irq

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.uart_irq
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.uart_irq.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: port=uart_irq_o; signal=uart_irq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.uart_irq
  - Primary implementation evidence is in rtl/uart_lite.sv
  - DUT port uart_irq_o is the implementation/observation point for uart_irq_o
- SSOT refs: integration.connections.uart_irq

### RTL-0253: Implement integration item tx

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.tx
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.tx.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: port=tx_o; signal=tx.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.tx
  - Primary implementation evidence is in rtl/uart_lite.sv
  - DUT port tx_o is the implementation/observation point for tx_o
- SSOT refs: integration.connections.tx

### RTL-0254: Implement integration item rx

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.rx
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rx.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: port=rx_i; signal=rx.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rx
  - Primary implementation evidence is in rtl/uart_lite.sv
  - DUT port rx_i is the implementation/observation point for rx_i
- SSOT refs: integration.connections.rx
