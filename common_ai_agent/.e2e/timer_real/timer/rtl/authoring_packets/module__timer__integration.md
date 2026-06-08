# RTL Authoring Packet: module__timer__integration

- Kind: module
- Owner module: timer
- Owner file: rtl/timer.sv
- Task count: 22
- Required tasks: 22

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 4/8 section=integration task_limit=48
- Slice rule: Owner module timer is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_regs.pclk <= pclk (integration.connections[0])
  - timer_regs.presetn <= presetn (integration.connections[1])
  - timer_regs.paddr <= paddr (integration.connections[2])
  - timer_regs.psel <= psel (integration.connections[3])
  - timer_regs.penable <= penable (integration.connections[4])
  - timer_regs.pwrite <= pwrite (integration.connections[5])
  - timer_regs.pwdata <= pwdata (integration.connections[6])
  - timer_regs.prdata <= prdata (integration.connections[7])
  - timer_regs.pready <= pready (integration.connections[8])
  - timer_regs.pslverr <= pslverr (integration.connections[9])
  - timer_regs.load_q <= load_q (integration.connections[10])
  - timer_regs.enable_q <= enable_q (integration.connections[11])
- SSOT top IO contracts: 11

## Tasks

### RTL-0184: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: value=Parent must provide pclk and presetn..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0185: Implement integration item dependencie_1

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_1
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_1.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: value=Parent APB master must follow setup/access phase semantics..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_1
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: integration.dependencies.dependencie_1

### RTL-0186: Implement integration item dependencie_2

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_2
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_2.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: value=Parent address map must reserve at least 0x10 bytes for timer registers..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_2
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: integration.dependencies.dependencie_2

### RTL-0187: Implement integration item pclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pclk.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=pclk; signal=pclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pclk
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port pclk is the implementation/observation point for pclk
- SSOT refs: integration.connections.pclk

### RTL-0188: Implement integration item presetn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.presetn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.presetn.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=presetn; signal=presetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.presetn
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port presetn is the implementation/observation point for presetn
- SSOT refs: integration.connections.presetn

### RTL-0189: Implement integration item paddr

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.paddr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.paddr.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=paddr; signal=paddr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.paddr
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port paddr is the implementation/observation point for paddr
- SSOT refs: integration.connections.paddr

### RTL-0190: Implement integration item psel

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.psel
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.psel.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=psel; signal=psel.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.psel
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port psel is the implementation/observation point for psel
- SSOT refs: integration.connections.psel

### RTL-0191: Implement integration item penable

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.penable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.penable.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=penable; signal=penable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.penable
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port penable is the implementation/observation point for penable
- SSOT refs: integration.connections.penable

### RTL-0192: Implement integration item pwrite

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pwrite
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pwrite.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=pwrite; signal=pwrite.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pwrite
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port pwrite is the implementation/observation point for pwrite
- SSOT refs: integration.connections.pwrite

### RTL-0193: Implement integration item pwdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pwdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pwdata.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=pwdata; signal=pwdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pwdata
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port pwdata is the implementation/observation point for pwdata
- SSOT refs: integration.connections.pwdata

### RTL-0194: Implement integration item prdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.prdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.prdata.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=prdata; signal=prdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.prdata
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port prdata is the implementation/observation point for prdata
- SSOT refs: integration.connections.prdata

### RTL-0195: Implement integration item pready

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pready
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pready.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=pready; signal=pready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pready
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port pready is the implementation/observation point for pready
- SSOT refs: integration.connections.pready

### RTL-0196: Implement integration item pslverr

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pslverr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pslverr.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=pslverr; signal=pslverr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pslverr
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port pslverr is the implementation/observation point for pslverr
- SSOT refs: integration.connections.pslverr

### RTL-0197: Implement integration item load_q

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.load_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.load_q.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=load_q; signal=load_q.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.load_q
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port load_q is the implementation/observation point for load_q
- SSOT refs: integration.connections.load_q

### RTL-0198: Implement integration item enable_q

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.enable_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.enable_q.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=enable_q; signal=enable_q.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.enable_q
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port enable_q is the implementation/observation point for enable_q
- SSOT refs: integration.connections.enable_q

### RTL-0199: Implement integration item count_q

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.count_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.count_q.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=count_q; signal=count_q.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.count_q
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port count_q is the implementation/observation point for count_q
- SSOT refs: integration.connections.count_q

### RTL-0200: Implement integration item pclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pclk.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=pclk; signal=pclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pclk
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port pclk is the implementation/observation point for pclk
- SSOT refs: integration.connections.pclk

### RTL-0201: Implement integration item presetn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.presetn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.presetn.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=presetn; signal=presetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.presetn
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port presetn is the implementation/observation point for presetn
- SSOT refs: integration.connections.presetn

### RTL-0202: Implement integration item load_q

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.load_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.load_q.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=load_q; signal=load_q.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.load_q
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port load_q is the implementation/observation point for load_q
- SSOT refs: integration.connections.load_q

### RTL-0203: Implement integration item enable_q

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.enable_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.enable_q.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=enable_q; signal=enable_q.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.enable_q
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port enable_q is the implementation/observation point for enable_q
- SSOT refs: integration.connections.enable_q

### RTL-0204: Implement integration item count_q

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.count_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.count_q.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=count_q; signal=count_q.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.count_q
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port count_q is the implementation/observation point for count_q
- SSOT refs: integration.connections.count_q

### RTL-0205: Implement integration item irq

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.irq
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.irq.
Owner: timer in rtl/timer.sv via integration.
SSOT item context: port=irq; signal=irq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.irq
  - Primary implementation evidence is in rtl/timer.sv
  - DUT port irq is the implementation/observation point for irq
- SSOT refs: integration.connections.irq
