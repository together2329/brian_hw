# RTL Authoring Packet: module__clkdiv

- Kind: module
- Owner module: clkdiv
- Owner file: rtl/clkdiv.sv
- Task count: 47
- Required tasks: 47

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
- LLM-actionable open tasks: 47
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- SSOT connection contracts:
  - clkdiv_regs.clk_i <= clk_i (sub_modules[0].connections[0])
  - clkdiv_regs.rst_ni <= rst_ni (sub_modules[0].connections[1])
  - clkdiv_regs.enable_o <= enable (sub_modules[0].connections[2])
  - clkdiv_regs.divisor_o <= active_divisor (sub_modules[0].connections[3])
  - clkdiv_regs.irq_pending_i <= irq_pending (sub_modules[0].connections[4])
  - clkdiv_core.clk_i <= clk_i (sub_modules[1].connections[0])
  - clkdiv_core.rst_ni <= rst_ni (sub_modules[1].connections[1])
  - clkdiv_core.enable_i <= enable (sub_modules[1].connections[2])
  - clkdiv_core.divisor_i <= active_divisor (sub_modules[1].connections[3])
  - clkdiv_core.clk_o <= clk_o (sub_modules[1].connections[4])
  - clkdiv_core.locked_o <= locked_o (sub_modules[1].connections[5])
  - clkdiv_core.terminal_event_o <= terminal_event (sub_modules[1].connections[6])
- SSOT top IO contracts: 14

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: planned
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: clkdiv in rtl/clkdiv.sv via top_module.
- Current reason: RTL audit has not run yet.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: planned
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: clkdiv in rtl/clkdiv.sv via top_module.
SSOT item context: value=clkdiv.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: io_list

### RTL-0027: Implement clkdiv top integration

- Priority: high
- Required: True
- Status: planned
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Create rtl/clkdiv.sv with declared IO ports and instantiate/wire clkdiv_regs and clkdiv_core according to integration.connections.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: clkdiv in rtl/clkdiv.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CLKDIV_TOP.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Top module ports match io_list exactly
  - Named port connections satisfy integration.connections
  - No wrapper-only top pattern; top file is rtl/clkdiv.sv
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/clkdiv.sv
  - Semantic source_refs covered: integration.connections, io_list, sub_modules, top_module
- SSOT refs: integration.connections, io_list, sub_modules, top_module, workflow_todos.rtl-gen[0]

### RTL-0119: Implement feature Programmable divide

- Priority: high
- Required: True
- Status: planned
- Category: features.item
- Source ref: features.Programmable_divide
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Programmable_divide.
Owner: clkdiv in rtl/clkdiv.sv via features.
SSOT item context: name=Programmable divide; output=clk_o toggles at a rate determined by DIVISOR..
- Current reason: RTL audit has not run yet.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Programmable_divide
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: features.Programmable_divide

### RTL-0120: Implement feature Glitchless divisor update

- Priority: high
- Required: True
- Status: planned
- Category: features.item
- Source ref: features.Glitchless_divisor_update
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Glitchless_divisor_update.
Owner: clkdiv in rtl/clkdiv.sv via features.
SSOT item context: name=Glitchless divisor update; output=No runt pulse or asynchronous clk_o edge occurs due to divisor write..
- Current reason: RTL audit has not run yet.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Glitchless_divisor_update
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: features.Glitchless_divisor_update

### RTL-0121: Implement feature Terminal event interrupt

- Priority: high
- Required: True
- Status: planned
- Category: features.item
- Source ref: features.Terminal_event_interrupt
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Terminal_event_interrupt.
Owner: clkdiv in rtl/clkdiv.sv via features.
SSOT item context: name=Terminal event interrupt; output=irq_o asserted while interrupt is enabled and pending..
- Current reason: RTL audit has not run yet.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Terminal_event_interrupt
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: features.Terminal_event_interrupt

### RTL-0124: Implement security item divider_configuration

- Priority: high
- Required: True
- Status: planned
- Category: security.assets
- Source ref: security.assets.divider_configuration
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.divider_configuration.
Owner: clkdiv in rtl/clkdiv.sv via security.
SSOT item context: name=divider_configuration.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.divider_configuration
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: security.assets.divider_configuration

### RTL-0125: Implement security item generated_clock_output

- Priority: high
- Required: True
- Status: planned
- Category: security.assets
- Source ref: security.assets.generated_clock_output
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.generated_clock_output.
Owner: clkdiv in rtl/clkdiv.sv via security.
SSOT item context: name=generated_clock_output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.generated_clock_output
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: security.assets.generated_clock_output

### RTL-0126: Implement integration item external_modules

- Priority: high
- Required: True
- Status: planned
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: name=external_modules.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0127: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: planned
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: name=external_clocks; value=["clk_i"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0128: Implement integration item external_resets

- Priority: high
- Required: True
- Status: planned
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: name=external_resets; value=["rst_ni"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0129: Implement integration item clk_i

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.clk_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.clk_i.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=clk_i; signal=clk_i.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.clk_i
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.clk_i

### RTL-0130: Implement integration item rst_ni

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.rst_ni
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rst_ni.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=rst_ni; signal=rst_ni.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rst_ni
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.rst_ni

### RTL-0131: Implement integration item paddr

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.paddr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.paddr.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=paddr; signal=paddr.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.paddr
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port paddr is the implementation/observation point for paddr
- SSOT refs: integration.connections.paddr

### RTL-0132: Implement integration item psel

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.psel
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.psel.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=psel; signal=psel.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.psel
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port psel is the implementation/observation point for psel
- SSOT refs: integration.connections.psel

### RTL-0133: Implement integration item penable

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.penable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.penable.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=penable; signal=penable.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.penable
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port penable is the implementation/observation point for penable
- SSOT refs: integration.connections.penable

### RTL-0134: Implement integration item pwrite

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.pwrite
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pwrite.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=pwrite; signal=pwrite.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pwrite
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port pwrite is the implementation/observation point for pwrite
- SSOT refs: integration.connections.pwrite

### RTL-0135: Implement integration item pwdata

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.pwdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pwdata.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=pwdata; signal=pwdata.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pwdata
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port pwdata is the implementation/observation point for pwdata
- SSOT refs: integration.connections.pwdata

### RTL-0136: Implement integration item pstrb

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.pstrb
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pstrb.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=pstrb; signal=pstrb.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pstrb
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port pstrb is the implementation/observation point for pstrb
- SSOT refs: integration.connections.pstrb

### RTL-0137: Implement integration item prdata

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.prdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.prdata.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=prdata; signal=prdata.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.prdata
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port prdata is the implementation/observation point for prdata
- SSOT refs: integration.connections.prdata

### RTL-0138: Implement integration item pready

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.pready
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pready.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=pready; signal=pready.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pready
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port pready is the implementation/observation point for pready
- SSOT refs: integration.connections.pready

### RTL-0139: Implement integration item pslverr

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.pslverr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pslverr.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=pslverr; signal=pslverr.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pslverr
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port pslverr is the implementation/observation point for pslverr
- SSOT refs: integration.connections.pslverr

### RTL-0140: Implement integration item clk_i

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.clk_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.clk_i.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=clk_i; signal=clk_i.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.clk_i
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.clk_i

### RTL-0141: Implement integration item rst_ni

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.rst_ni
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rst_ni.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=rst_ni; signal=rst_ni.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rst_ni
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.rst_ni

### RTL-0142: Implement integration item enable

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.enable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.enable.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=enable_i; signal=enable.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.enable
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port enable_i is the implementation/observation point for enable_i
- SSOT refs: integration.connections.enable

### RTL-0143: Implement integration item active_divisor

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.active_divisor
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.active_divisor.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=divisor_i; signal=active_divisor.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.active_divisor
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port divisor_i is the implementation/observation point for divisor_i
- SSOT refs: integration.connections.active_divisor

### RTL-0144: Implement integration item clk_o

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.clk_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.clk_o.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=clk_o; signal=clk_o.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.clk_o
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port clk_o is the implementation/observation point for clk_o
- SSOT refs: integration.connections.clk_o

### RTL-0145: Implement integration item locked_o

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.locked_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.locked_o.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=locked_o; signal=locked_o.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.locked_o
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port locked_o is the implementation/observation point for locked_o
- SSOT refs: integration.connections.locked_o

### RTL-0146: Implement integration item terminal_event

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.terminal_event
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.terminal_event.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=terminal_event_o; signal=terminal_event.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.terminal_event
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port terminal_event_o is the implementation/observation point for terminal_event_o
- SSOT refs: integration.connections.terminal_event

### RTL-0147: Implement integration item terminal_event

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.terminal_event
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.terminal_event.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=terminal_event_i; signal=terminal_event.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.terminal_event
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port terminal_event_i is the implementation/observation point for terminal_event_i
- SSOT refs: integration.connections.terminal_event

### RTL-0148: Implement integration item irq_o

- Priority: high
- Required: True
- Status: planned
- Category: integration.connections
- Source ref: integration.connections.irq_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.irq_o.
Owner: clkdiv in rtl/clkdiv.sv via integration.
SSOT item context: port=irq_o; signal=irq_o.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.irq_o
  - Primary implementation evidence is in rtl/clkdiv.sv
  - DUT port irq_o is the implementation/observation point for irq_o
- SSOT refs: integration.connections.irq_o

### RTL-0149: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: clkdiv in rtl/clkdiv.sv via synthesis.
SSOT item context: value=No inferred latches.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0150: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: clkdiv in rtl/clkdiv.sv via synthesis.
SSOT item context: value=All architectural flops reset according to clock_reset_domains.reset_scheme.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0151: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: clkdiv in rtl/clkdiv.sv via synthesis.
SSOT item context: value=No package/interface/modport/function/task/for/while constructs in generated RTL.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0152: Implement synthesis item constraint_3

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_3
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_3.
Owner: clkdiv in rtl/clkdiv.sv via synthesis.
SSOT item context: value=clk_o must be driven by sequential logic only; no combinational clock gating for clk_o.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_3
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: synthesis.constraints.constraint_3

### RTL-0153: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: clkdiv in rtl/clkdiv.sv via synthesis.
SSOT item context: name=area_um2_max.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0154: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: clkdiv in rtl/clkdiv.sv via synthesis.
SSOT item context: name=power_mw_max.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0155: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: clkdiv in rtl/clkdiv.sv via synthesis.
SSOT item context: name=frequency_mhz_min; value=100.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0158: Prove module clkdiv is functionally equivalent to FL

- Priority: high
- Required: True
- Status: planned
- Category: equivalence.module
- Source ref: sub_modules.clkdiv.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.clkdiv.module_equivalence.
Owner: clkdiv in rtl/clkdiv.sv via module_equivalence.
- Current reason: RTL audit has not run yet.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.clkdiv.module_equivalence
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: sub_modules.clkdiv.module_equivalence

### RTL-0030: Implement parameter DIV_WIDTH

- Priority: normal
- Required: True
- Status: planned
- Category: parameters.item
- Source ref: parameters.DIV_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DIV_WIDTH.
Owner: clkdiv in rtl/clkdiv.sv via parameters.
SSOT item context: name=DIV_WIDTH.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DIV_WIDTH
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: parameters.DIV_WIDTH

### RTL-0031: Implement parameter RESET_POLARITY

- Priority: normal
- Required: True
- Status: planned
- Category: parameters.item
- Source ref: parameters.RESET_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_POLARITY.
Owner: clkdiv in rtl/clkdiv.sv via parameters.
SSOT item context: name=RESET_POLARITY.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_POLARITY
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: parameters.RESET_POLARITY

### RTL-0032: Implement parameter CLOCK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: planned
- Category: parameters.item
- Source ref: parameters.CLOCK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CLOCK_FREQ_MHZ.
Owner: clkdiv in rtl/clkdiv.sv via parameters.
SSOT item context: name=CLOCK_FREQ_MHZ.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CLOCK_FREQ_MHZ
  - Primary implementation evidence is in rtl/clkdiv.sv
- SSOT refs: parameters.CLOCK_FREQ_MHZ

### RTL-0159: Keep RTL observable for scenario SC_APB

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_APB
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_APB.
Owner: clkdiv in rtl/clkdiv.sv via test_requirements.
SSOT item context: id=SC_APB; name=APB register access; expected=Register readback, reserved zero behavior, pslverr, and side effects match registers and error_handling..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_APB
  - Primary implementation evidence is in rtl/clkdiv.sv
  - Downstream checker compares RTL-observed behavior against expected result: Register readback, reserved zero behavior, pslverr, and side effects match registers and error_handling.
- SSOT refs: test_requirements.scenarios.SC_APB

### RTL-0160: Keep RTL observable for scenario SC_DIV2

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_DIV2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_DIV2.
Owner: clkdiv in rtl/clkdiv.sv via test_requirements.
SSOT item context: id=SC_DIV2; name=Divide by two baseline; expected=clk_o toggles every 2 clk_i rising edges and locked_o asserts after first reload..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_DIV2
  - Primary implementation evidence is in rtl/clkdiv.sv
  - Downstream checker compares RTL-observed behavior against expected result: clk_o toggles every 2 clk_i rising edges and locked_o asserts after first reload.
- SSOT refs: test_requirements.scenarios.SC_DIV2

### RTL-0161: Keep RTL observable for scenario SC_DIV_UPDATE

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_DIV_UPDATE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_DIV_UPDATE.
Owner: clkdiv in rtl/clkdiv.sv via test_requirements.
SSOT item context: id=SC_DIV_UPDATE; name=Glitchless divisor update; expected=active_divisor changes only at terminal boundary; no runt/asynchronous output pulse..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_DIV_UPDATE
  - Primary implementation evidence is in rtl/clkdiv.sv
  - Downstream checker compares RTL-observed behavior against expected result: active_divisor changes only at terminal boundary; no runt/asynchronous output pulse.
- SSOT refs: test_requirements.scenarios.SC_DIV_UPDATE

### RTL-0162: Keep RTL observable for scenario SC_IRQ

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_IRQ
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_IRQ.
Owner: clkdiv in rtl/clkdiv.sv via test_requirements.
SSOT item context: id=SC_IRQ; name=Terminal interrupt set and clear; expected=irq_pending and irq_o assert on terminal event and deassert after W1C clear..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_IRQ
  - Primary implementation evidence is in rtl/clkdiv.sv
  - Downstream checker compares RTL-observed behavior against expected result: irq_pending and irq_o assert on terminal event and deassert after W1C clear.
- SSOT refs: test_requirements.scenarios.SC_IRQ

### RTL-0163: Keep RTL observable for scenario SC_DIV_ZERO

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_DIV_ZERO
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_DIV_ZERO.
Owner: clkdiv in rtl/clkdiv.sv via test_requirements.
SSOT item context: id=SC_DIV_ZERO; name=DIVISOR zero write policy; expected=pending_divisor coerces to 1 without pslverr and output follows divide-by-one half-period contract..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_DIV_ZERO
  - Primary implementation evidence is in rtl/clkdiv.sv
  - Downstream checker compares RTL-observed behavior against expected result: pending_divisor coerces to 1 without pslverr and output follows divide-by-one half-period contract.
- SSOT refs: test_requirements.scenarios.SC_DIV_ZERO
