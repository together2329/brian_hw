# RTL Authoring Packet: module__todo_counter_pipe_cdc

- Kind: module
- Owner module: todo_counter_pipe_cdc
- Owner file: rtl/todo_counter_pipe_cdc.sv
- Task count: 23
- Required tasks: 23

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
- Owner refs: cdc_requirements, cdc_requirements.crossings.control_bus_to_core, cdc_requirements.crossings.status_core_to_bus, cdc_requirements.synchronizers.sync_ctrl, cdc_requirements.synchronizers.sync_pulse_clear, cdc_requirements.synchronizers.sync_status, clock_reset_domains, clock_reset_domains.domains.bus_clk, clock_reset_domains.domains.core_clk, clock_reset_domains.reset_scheme, clock_reset_domains.reset_scheme.bus_domain, clock_reset_domains.reset_scheme.core_domain, cycle_model, cycle_model.clock, cycle_model.latency.control_cdc_bus_to_core, cycle_model.latency.status_cdc_core_to_bus
- SSOT connection contracts:
  - todo_counter_pipe_cdc.bus_clk <= integration.connections.todo_counter_pipe_cdc.bus_clk (sub_modules[2].connections)
  - todo_counter_pipe_cdc.core_clk <= integration.connections.todo_counter_pipe_cdc.core_clk (sub_modules[2].connections)
  - todo_counter_pipe_cdc.bus_rst_n <= integration.connections.todo_counter_pipe_cdc.bus_rst_n (sub_modules[2].connections)
  - todo_counter_pipe_cdc.core_rst_n <= integration.connections.todo_counter_pipe_cdc.core_rst_n (sub_modules[2].connections)
  - todo_counter_pipe_cdc.control_bus_to_core <= cdc_requirements.crossings.control_bus_to_core.signals (sub_modules[2].connections)
  - todo_counter_pipe_cdc.status_core_to_bus <= cdc_requirements.crossings.status_core_to_bus.signals (sub_modules[2].connections)
  - todo_counter_pipe_cdc.bus_clk <= bus_clk (integration.connections[6])
  - todo_counter_pipe_cdc.core_clk <= core_clk (integration.connections[7])
  - todo_counter_pipe_cdc.bus_rst_n <= bus_rst_n (integration.connections[8])
  - todo_counter_pipe_cdc.core_rst_n <= core_rst_n (integration.connections[9])

## Tasks

### RTL-0022: Implement CDC synchronizers for bus↔core crossings

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Implement 2-stage FF synchronizers for all control (bus→core) and status (core→bus) crossings per cdc_requirements. Use toggle synchronizer for clear/load single-cycle pulses.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CDC_SYNC.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Control CDC: enable, up_down, mode, load_value use 2-stage FF sync
  - Pulse CDC: clear_pulse, load_pulse use toggle synchronizer with edge detect
  - Status CDC: cnt_value, overflow, underflow, tc_pending, ovf_pending, unf_pending, dbg_cycle_count use 2-stage FF sync
  - Synchronizer FFs have ASYNC_REG attribute and set_dont_touch for synthesis
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - Semantic source_refs covered: cdc_requirements.crossings, cdc_requirements.synchronizers
- SSOT refs: cdc_requirements.crossings, cdc_requirements.synchronizers, workflow_todos.rtl-gen[2]

### RTL-0162: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via cycle_model.latency.control_cdc_bus_to_core.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0168: Implement pipeline stage: S1_CDC_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_CDC_CTRL
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_CDC_CTRL.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via cycle_model.pipeline.S1_CDC_CTRL.
SSOT item context: stage=S1_CDC_CTRL; action=2-stage synchronizer: CTRL fields (enable, up_down, mode, clear pulse, load pulse), LOAD value cross bus→core; cycle=0..4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_CDC_CTRL
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - cycle_model.pipeline.S1_CDC_CTRL timing uses SSOT cycle/latency 0..4
  - cycle_model.pipeline.S1_CDC_CTRL appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_CDC_CTRL

### RTL-0170: Implement pipeline stage: S3_CDC_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S3_CDC_STATUS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S3_CDC_STATUS.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via cycle_model.pipeline.S3_CDC_STATUS.
SSOT item context: stage=S3_CDC_STATUS; action=2-stage synchronizer: cnt_value, overflow, underflow, tc_pending, ovf_pending, unf_pending, dbg_cycle_count cross cor...; cycle=0..5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S3_CDC_STATUS
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - cycle_model.pipeline.S3_CDC_STATUS timing uses SSOT cycle/latency 0..5
  - cycle_model.pipeline.S3_CDC_STATUS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S3_CDC_STATUS

### RTL-0238: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0239: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.
SSOT item context: name=external_clocks; value=["bus_clk", "core_clk"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0240: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.
SSOT item context: name=external_resets; value=["bus_rst_n", "core_rst_n"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0241: Implement integration item bus_clk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.bus_clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.bus_clk.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=bus_clk; signal=bus_clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.bus_clk
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port bus_clk is the implementation/observation point for bus_clk
- SSOT refs: integration.connections.bus_clk

### RTL-0242: Implement integration item bus_rst_n

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.bus_rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.bus_rst_n.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=bus_rst_n; signal=bus_rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.bus_rst_n
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port bus_rst_n is the implementation/observation point for bus_rst_n
- SSOT refs: integration.connections.bus_rst_n

### RTL-0243: Implement integration item counter_irq

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.counter_irq
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.counter_irq.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=irq_o; signal=counter_irq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.counter_irq
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port irq_o is the implementation/observation point for irq_o
- SSOT refs: integration.connections.counter_irq

### RTL-0244: Implement integration item core_clk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.core_clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.core_clk.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=core_clk; signal=core_clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.core_clk
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port core_clk is the implementation/observation point for core_clk
- SSOT refs: integration.connections.core_clk

### RTL-0245: Implement integration item core_rst_n

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.core_rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.core_rst_n.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=core_rst_n; signal=core_rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.core_rst_n
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port core_rst_n is the implementation/observation point for core_rst_n
- SSOT refs: integration.connections.core_rst_n

### RTL-0246: Implement integration item event_i

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.event_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.event_i.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=event_i; signal=event_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.event_i
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port event_i is the implementation/observation point for event_i
- SSOT refs: integration.connections.event_i

### RTL-0247: Implement integration item bus_clk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.bus_clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.bus_clk.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=bus_clk; signal=bus_clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.bus_clk
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port bus_clk is the implementation/observation point for bus_clk
- SSOT refs: integration.connections.bus_clk

### RTL-0248: Implement integration item core_clk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.core_clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.core_clk.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=core_clk; signal=core_clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.core_clk
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port core_clk is the implementation/observation point for core_clk
- SSOT refs: integration.connections.core_clk

### RTL-0249: Implement integration item bus_rst_n

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.bus_rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.bus_rst_n.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=bus_rst_n; signal=bus_rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.bus_rst_n
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port bus_rst_n is the implementation/observation point for bus_rst_n
- SSOT refs: integration.connections.bus_rst_n

### RTL-0250: Implement integration item core_rst_n

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.core_rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.core_rst_n.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via integration.connections.
SSOT item context: port=core_rst_n; signal=core_rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.core_rst_n
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
  - DUT port core_rst_n is the implementation/observation point for core_rst_n
- SSOT refs: integration.connections.core_rst_n

### RTL-0261: Prove module todo_counter_pipe_cdc is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.todo_counter_pipe_cdc.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.todo_counter_pipe_cdc.module_equivalence.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.todo_counter_pipe_cdc.module_equivalence
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: sub_modules.todo_counter_pipe_cdc.module_equivalence

### RTL-0024: Implement parameter WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.WIDTH.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via parameters.
SSOT item context: name=WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.WIDTH
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: parameters.WIDTH

### RTL-0025: Implement parameter BUS_CLK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.BUS_CLK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.BUS_CLK_FREQ_MHZ.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via parameters.
SSOT item context: name=BUS_CLK_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.BUS_CLK_FREQ_MHZ
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: parameters.BUS_CLK_FREQ_MHZ

### RTL-0026: Implement parameter CORE_CLK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.CORE_CLK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CORE_CLK_FREQ_MHZ.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via parameters.
SSOT item context: name=CORE_CLK_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CORE_CLK_FREQ_MHZ
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: parameters.CORE_CLK_FREQ_MHZ

### RTL-0027: Implement parameter CDC_SYNC_STAGES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.CDC_SYNC_STAGES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CDC_SYNC_STAGES.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via parameters.
SSOT item context: name=CDC_SYNC_STAGES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CDC_SYNC_STAGES
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: parameters.CDC_SYNC_STAGES

### RTL-0028: Implement parameter RESET_POLARITY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESET_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_POLARITY.
Owner: todo_counter_pipe_cdc in rtl/todo_counter_pipe_cdc.sv via parameters.
SSOT item context: name=RESET_POLARITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_POLARITY
  - Primary implementation evidence is in rtl/todo_counter_pipe_cdc.sv
- SSOT refs: parameters.RESET_POLARITY
