# RTL Authoring Packet: module__arbiter_rr__integration

- Kind: module
- Owner module: arbiter_rr
- Owner file: rtl/arbiter_rr.sv
- Task count: 27
- Required tasks: 27

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 3/9 section=integration task_limit=48
- Slice rule: Owner module arbiter_rr is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=3
- SSOT connection contracts:
  - arbiter_rr_regs.PCLK <= PCLK (integration.connections[0])
  - arbiter_rr_regs.PRESETn <= PRESETn (integration.connections[1])
  - arbiter_rr_regs.PADDR <= PADDR (integration.connections[2])
  - arbiter_rr_regs.PSEL <= PSEL (integration.connections[3])
  - arbiter_rr_regs.PENABLE <= PENABLE (integration.connections[4])
  - arbiter_rr_regs.PWRITE <= PWRITE (integration.connections[5])
  - arbiter_rr_regs.PWDATA <= PWDATA (integration.connections[6])
  - arbiter_rr_regs.PRDATA <= PRDATA (integration.connections[7])
  - arbiter_rr_regs.PREADY <= PREADY (integration.connections[8])
  - arbiter_rr_regs.PSLVERR <= PSLVERR (integration.connections[9])
  - arbiter_rr_regs.enable_o <= arb_enable (integration.connections[10])
  - arbiter_rr_regs.mask_o <= req_mask (integration.connections[11])
- SSOT top IO contracts: 14

## Tasks

### RTL-0124: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/arbiter_rr.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0125: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: name=external_clocks; value=["PCLK"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/arbiter_rr.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0126: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: name=external_resets; value=["PRESETn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/arbiter_rr.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0127: Implement integration item PCLK

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PCLK; signal=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PCLK is the implementation/observation point for PCLK
- SSOT refs: integration.connections.PCLK

### RTL-0128: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PRESETn; signal=PRESETn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PRESETn is the implementation/observation point for PRESETn
- SSOT refs: integration.connections.PRESETn

### RTL-0129: Implement integration item PADDR

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PADDR
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PADDR.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PADDR; signal=PADDR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PADDR
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PADDR is the implementation/observation point for PADDR
- SSOT refs: integration.connections.PADDR

### RTL-0130: Implement integration item PSEL

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PSEL
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PSEL.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PSEL; signal=PSEL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PSEL
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PSEL is the implementation/observation point for PSEL
- SSOT refs: integration.connections.PSEL

### RTL-0131: Implement integration item PENABLE

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PENABLE
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PENABLE.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PENABLE; signal=PENABLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PENABLE
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PENABLE is the implementation/observation point for PENABLE
- SSOT refs: integration.connections.PENABLE

### RTL-0132: Implement integration item PWRITE

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PWRITE
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PWRITE.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PWRITE; signal=PWRITE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PWRITE
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PWRITE is the implementation/observation point for PWRITE
- SSOT refs: integration.connections.PWRITE

### RTL-0133: Implement integration item PWDATA

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PWDATA
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PWDATA.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PWDATA; signal=PWDATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PWDATA
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PWDATA is the implementation/observation point for PWDATA
- SSOT refs: integration.connections.PWDATA

### RTL-0134: Implement integration item PRDATA

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PRDATA
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRDATA.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PRDATA; signal=PRDATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRDATA
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PRDATA is the implementation/observation point for PRDATA
- SSOT refs: integration.connections.PRDATA

### RTL-0135: Implement integration item PREADY

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PREADY
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PREADY.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PREADY; signal=PREADY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PREADY
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PREADY is the implementation/observation point for PREADY
- SSOT refs: integration.connections.PREADY

### RTL-0136: Implement integration item PSLVERR

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PSLVERR
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PSLVERR.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=PSLVERR; signal=PSLVERR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PSLVERR
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port PSLVERR is the implementation/observation point for PSLVERR
- SSOT refs: integration.connections.PSLVERR

### RTL-0137: Implement integration item arb_enable

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.arb_enable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.arb_enable.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=enable_o; signal=arb_enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.arb_enable
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port enable_o is the implementation/observation point for enable_o
- SSOT refs: integration.connections.arb_enable

### RTL-0138: Implement integration item req_mask

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.req_mask
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.req_mask.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=mask_o; signal=req_mask.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.req_mask
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port mask_o is the implementation/observation point for mask_o
- SSOT refs: integration.connections.req_mask

### RTL-0139: Implement integration item PCLK

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=clk_i; signal=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.PCLK

### RTL-0140: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=rst_ni; signal=PRESETn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.PRESETn

### RTL-0141: Implement integration item req_i

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.req_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.req_i.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=req_i; signal=req_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.req_i
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port req_i is the implementation/observation point for req_i
- SSOT refs: integration.connections.req_i

### RTL-0142: Implement integration item req_mask

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.req_mask
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.req_mask.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=mask_i; signal=req_mask.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.req_mask
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port mask_i is the implementation/observation point for mask_i
- SSOT refs: integration.connections.req_mask

### RTL-0143: Implement integration item arb_enable

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.arb_enable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.arb_enable.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=enable_i; signal=arb_enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.arb_enable
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port enable_i is the implementation/observation point for enable_i
- SSOT refs: integration.connections.arb_enable

### RTL-0144: Implement integration item gnt_o

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.gnt_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.gnt_o.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=gnt_o; signal=gnt_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.gnt_o
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port gnt_o is the implementation/observation point for gnt_o
- SSOT refs: integration.connections.gnt_o

### RTL-0145: Implement integration item gnt_valid_o

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.gnt_valid_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.gnt_valid_o.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=gnt_valid_o; signal=gnt_valid_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.gnt_valid_o
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port gnt_valid_o is the implementation/observation point for gnt_valid_o
- SSOT refs: integration.connections.gnt_valid_o

### RTL-0146: Implement integration item gnt_idx_o

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.gnt_idx_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.gnt_idx_o.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=gnt_idx_o; signal=gnt_idx_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.gnt_idx_o
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port gnt_idx_o is the implementation/observation point for gnt_idx_o
- SSOT refs: integration.connections.gnt_idx_o

### RTL-0147: Implement integration item status_winner

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.status_winner
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.status_winner.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=winner_oh_o; signal=status_winner.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.status_winner
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port winner_oh_o is the implementation/observation point for winner_oh_o
- SSOT refs: integration.connections.status_winner

### RTL-0148: Implement integration item status_active_req

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.status_active_req
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.status_active_req.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=active_req_o; signal=status_active_req.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.status_active_req
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port active_req_o is the implementation/observation point for active_req_o
- SSOT refs: integration.connections.status_active_req

### RTL-0149: Implement integration item status_winner

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.status_winner
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.status_winner.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=winner_oh_i; signal=status_winner.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.status_winner
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port winner_oh_i is the implementation/observation point for winner_oh_i
- SSOT refs: integration.connections.status_winner

### RTL-0150: Implement integration item status_active_req

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.status_active_req
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.status_active_req.
Owner: arbiter_rr in rtl/arbiter_rr.sv via integration.
SSOT item context: port=active_req_i; signal=status_active_req.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.status_active_req
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - DUT port active_req_i is the implementation/observation point for active_req_i
- SSOT refs: integration.connections.status_active_req
