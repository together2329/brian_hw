Repair the SSOT YAML artifact for caa_timer. This is repair attempt 2.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "caa_timer/yaml/caa_timer.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}
  ]
}

Repair rules:
- Do not use a fixed IP template or hardcoded workaround.
- Preserve product semantics from the requirement and current SSOT wherever they are valid.
- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.
- Fix the concrete parse/validator failures below, and also check for sibling contract defects.
- The repaired YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh caa_timer --mode engineering`.
- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.

Failure summary:
human_gate: SSOT disk validator failed: [check_ssot_disk] FAIL: caa_timer/yaml/caa_timer.ssot.yaml failed YAML/model validation

Blocker artifact:


Validator log:
cmd: bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh caa_timer --mode engineering
cwd: /Users/brian/Desktop/Project/brian_hw/common_ai_agent
returncode: 1
stdout:
[check_ssot_disk] FAIL: caa_timer/yaml/caa_timer.ssot.yaml failed YAML/model validation
  function_model.transactions[4] must include executable output_rules or state_updates; prose outputs/side_effects are not scoreboard-comparable


Requirements:
# caa_timer Engineering Requirement

Create a small APB timer IP named `caa_timer`.

The IP has one clock and one active-low asynchronous reset. It exposes an APB3-style slave interface with `paddr[7:0]`, `psel`, `penable`, `pwrite`, `pwdata[31:0]`, `prdata[31:0]`, `pready`, and `pslverr`.

Registers:
- `0x00 CONTROL`: bit 0 enables counting. Reset value is 0.
- `0x04 COMPARE`: bits 7:0 hold the compare value. Reset value is 3.
- `0x08 VALUE`: read-only current counter value, bits 7:0.
- `0x0c IRQ_STATUS`: bit 0 is the pending interrupt. Writing 1 clears it.

Behavior:
- While enabled, the 8-bit counter increments once per clock.
- When the counter equals COMPARE while enabled, `irq` becomes 1 and remains set until IRQ_STATUS bit 0 is written with 1.
- APB legal accesses complete in one access phase with `pready=1`.
- Illegal addresses assert `pslverr=1`, return read data 0, and do not change state.
- Writes to VALUE are ignored and do not raise an error.

Engineering run requirements:
- Use Engineering mode.
- The SSOT must lock all behavior above, with no optional behavior.
- `top_module.name` must be `caa_timer`, but `sub_modules[]` must not contain another module named exactly `caa_timer`.
- If a top wrapper is listed in `sub_modules[]`, name it `caa_timer_top` and mark `wiring_only: true`.
- RTL must be authored by the common_ai_agent `rtl-gen` workflow using real LLM calls, not deterministic fixed-template fallback.
- Produce RTL, filelist, lint evidence, testbench/simulation evidence, and enough model/equivalence/coverage artifacts for wiki graph closure.


Current SSOT YAML:
top_module:
  name: caa_timer
  file: rtl/caa_timer.sv
  version: '1.0'
  type: peripheral
  description: APB3 programmable 8-bit timer with compare-triggered level interrupt
  reference_spec: caa_timer/req/caa_timer_requirements.md
  target:
    technology: generic
    clock_freq_mhz: 200
    area_um2: null
    power_mw: null
sub_modules:
- name: caa_timer_apb
  file: rtl/caa_timer_apb.sv
  ownership: manifest
  ssot_gen: true
  source_sections:
  - io_list
  - registers
  - error_handling
  implements:
  - io_list.interfaces.apb_slave
  - registers.register_list
  - error_handling.error_sources.ILLEGAL_ADDR
  register_refs:
  - registers.register_list
  description: APB access decode, read/write data muxing, legal/illegal address handling
  connections:
  - module: caa_timer_apb
    port: paddr
    signal: paddr
  - module: caa_timer_apb
    port: psel
    signal: psel
  - module: caa_timer_apb
    port: penable
    signal: penable
  - module: caa_timer_apb
    port: pwrite
    signal: pwrite
  - module: caa_timer_apb
    port: pwdata
    signal: pwdata
  - module: caa_timer_apb
    port: prdata
    signal: prdata
  - module: caa_timer_apb
    port: pready
    signal: pready
  - module: caa_timer_apb
    port: pslverr
    signal: pslverr
- name: caa_timer_core
  file: rtl/caa_timer_core.sv
  ownership: manifest
  ssot_gen: false
  source_sections:
  - function_model
  - cycle_model
  - interrupts
  - fsm
  - features
  - dataflow
  - decomposition
  - test_requirements
  implements:
  - function_model.transactions.TR_CFG_WRITE
  - function_model.transactions.TR_COUNT_TICK
  - function_model.transactions.TR_COMPARE_HIT
  - function_model.transactions.TR_IRQ_CLEAR
  - cycle_model.pipeline
  - interrupts.sources
  - fsm.timer_control
  function_model_refs:
  - function_model.transactions.TR_CFG_WRITE
  - function_model.transactions.TR_COUNT_TICK
  - function_model.transactions.TR_COMPARE_HIT
  - function_model.transactions.TR_IRQ_CLEAR
  - function_model.transactions.TR_ILLEGAL_ACCESS
  - function_model.state_variables
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.handshake_rules
  - cycle_model
  fsm_refs:
  - fsm.timer_control
  - fsm
  description: Counter, compare detect, irq latch/clear, architectural state updates
  feature_refs:
  - features
  dataflow_refs:
  - dataflow
  decomposition_refs:
  - decomposition
  test_refs:
  - test_requirements
- name: caa_timer_top
  file: rtl/caa_timer_top.sv
  ownership: manifest
  ssot_gen: true
  wiring_only: true
  source_sections: &id001
  - io_list
  - integration
  implements:
  - integration.connections
  - io_list.interfaces
  - io_list.clock_domains
  - io_list.resets
  description: Optional wiring wrapper name reserved to avoid top-name collision in sub_modules list
- name: caa_timer
  file: rtl/caa_timer.sv
  ownership: manifest
  ssot_gen: true
  description: Top-level integration module matching SSOT top_module
decomposition:
  units:
  - id: apb_frontend
    kind: control
    source_refs:
    - io_list.interfaces.apb_slave
    - registers.register_list
    - error_handling.error_sources
    rtl_candidates:
    - caa_timer_apb
    verification_impact:
    - test_requirements.scenarios
  - id: timer_engine
    kind: datapath/control
    source_refs:
    - function_model.transactions
    - cycle_model.pipeline
    - interrupts.sources
    rtl_candidates:
    - caa_timer_core
    verification_impact:
    - test_requirements.coverage_goals.function
    - test_requirements.coverage_goals.cycle
  strategy: manifest_owned_leaf_decomposition
  owners:
  - module: caa_timer_apb
    file: rtl/caa_timer_apb.sv
    responsibility: APB access decode, read/write data muxing, legal/illegal address handling
    source_sections:
    - io_list
    - registers
    - error_handling
  - module: caa_timer_core
    file: rtl/caa_timer_core.sv
    responsibility: Counter, compare detect, irq latch/clear, architectural state updates
    source_sections:
    - function_model
    - cycle_model
    - interrupts
    - fsm
  - module: caa_timer_top
    file: rtl/caa_timer_top.sv
    responsibility: Optional wiring wrapper name reserved to avoid top-name collision in sub_modules list
    source_sections: *id001
  - module: caa_timer
    file: rtl/caa_timer.sv
    responsibility: Top-level integration module matching SSOT top_module
    source_sections:
    - function_model
    - cycle_model
    - io_list
  integration_policy: Top-level wiring must be backed by integration.connections or sub_modules[].connections before signoff.
  source_refs:
  - sub_modules
  - function_model
  - cycle_model
  - integration
parameters:
- name: ADDR_WIDTH
  default: 8
  type: int
  description: APB address width
  drives:
  - rtl/caa_timer.sv
  - rtl/caa_timer_apb.sv
- name: DATA_WIDTH
  default: 32
  type: int
  description: APB data width
  drives:
  - rtl/caa_timer.sv
  - rtl/caa_timer_apb.sv
- name: COUNTER_WIDTH
  default: 8
  type: int
  description: Timer counter and compare register width
  drives:
  - rtl/caa_timer_core.sv
io_list:
  clock_domains:
  - name: pclk
    frequency_mhz: 200
    description: APB peripheral clock
    ports:
    - name: pclk
      width: 1
      direction: input
      description: peripheral clock
  resets:
  - name: presetn
    polarity: active_low
    sync_async: async_assert_sync_deassert
    description: asynchronous assert, synchronous deassert reset
    ports:
    - name: presetn
      width: 1
      direction: input
      description: active-low reset
  interfaces:
  - name: apb_slave
    type: APB3
    role: slave
    description: APB register interface
    ports:
    - name: paddr
      width: 8
      direction: input
      description: byte address
    - name: psel
      width: 1
      direction: input
      description: peripheral select
    - name: penable
      width: 1
      direction: input
      description: access phase indicator
    - name: pwrite
      width: 1
      direction: input
      description: write direction
    - name: pwdata
      width: 32
      direction: input
      description: write data
    - name: prdata
      width: 32
      direction: output
      description: read data
    - name: pready
      width: 1
      direction: output
      description: transfer ready
    - name: pslverr
      width: 1
      direction: output
      description: slave error
    clock_domain: pclk
    reset_domain: presetn
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: irq_out
    type: custom
    role: output
    description: timer interrupt output
    ports:
    - name: irq
      width: 1
      direction: output
      description: interrupt pending level
    clock_domain: pclk
    reset_domain: presetn
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
features:
- name: enable_controlled_counter
  trigger: CONTROL.enable set to 1
  datapath: counter increments every rising clock edge while enabled
  control: governed by enable bit and reset
  output: VALUE register exposes current counter
- name: compare_interrupt_latch
  trigger: enabled counter equals COMPARE value
  datapath: comparator drives irq_pending latch set
  control: irq remains set until IRQ_STATUS W1C clear
  output: irq pin asserted high while irq_pending is 1
- name: deterministic_apb_response
  trigger: legal APB access phase
  datapath: decode fixed addresses 0x00,0x04,0x08,0x0C
  control: legal accesses complete in one access phase
  output: pready=1 for legal accesses, pslverr only for illegal addresses
dataflow:
  register_write_path:
    source: apb_slave.pwdata
    destination: CONTROL.enable and COMPARE.compare
    sequence: APB decode -> write strobe -> state update on next rising edge
  counter_path:
    source: internal enable state
    destination: VALUE.current_count
    sequence: if enable==1 then counter_next=(counter+1)&0xFF else hold
  irq_path:
    source: compare_match and W1C clear
    destination: IRQ_STATUS.pending and irq output
    sequence: set on compare match, clear on IRQ_STATUS write bit0=1
function_model:
  purpose: Architectural behavioral contract for APB timer independent of implementation partitioning.
  state_variables:
  - name: enable
    source: registers.register_list.CONTROL.fields.enable
    reset: 0
    width: 1
    description: counting enable
  - name: compare
    source: registers.register_list.COMPARE.fields.compare
    reset: 3
    width: 8
    description: compare threshold
  - name: counter
    source: registers.register_list.VALUE.fields.value
    reset: 0
    width: 8
    description: current timer value
  - name: irq_pending
    source: registers.register_list.IRQ_STATUS.fields.pending
    reset: 0
    width: 1
    description: latched interrupt status
  transactions:
  - id: TR_CFG_WRITE
    name: write_control_or_compare
    preconditions:
    - apb_sel == 1
    - apb_enable_phase == 1
    - apb_write == 1
    - addr in [0, 4]
    inputs:
    - addr
    - pwdata
    outputs:
    - pready_out == 1
    - pslverr_out == 0
    - state: enable_next
      expr: (pwdata & 1) if (addr == 0) else enable
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: compare_next
      expr: (pwdata & 0xFF) if (addr == 4) else compare
      description: Mirrored from executable state_updates for SSOT validator completeness.
    state_updates:
    - name: enable_next
      expr: (pwdata & 1) if (addr == 0) else enable
      width: 1
    - name: compare_next
      expr: (pwdata & 0xFF) if (addr == 4) else compare
      width: 8
    side_effects:
    - CONTROL bit0 updates enable when addr==0
    - COMPARE bits7:0 update compare when addr==4
    output_rules: []
  - id: TR_COUNT_TICK
    name: increment_counter_when_enabled
    preconditions:
    - tick_edge == 1
    inputs:
    - enable
    - counter
    outputs:
    - value_read_data == counter
    - state: counter_next
      expr: ((counter + 1) & 0xFF) if (enable == 1) else counter
      description: Mirrored from executable state_updates for SSOT validator completeness.
    state_updates:
    - name: counter_next
      expr: ((counter + 1) & 0xFF) if (enable == 1) else counter
      width: 8
    side_effects:
    - counter increments by one each clock only while enable is set
    output_rules: []
  - id: TR_COMPARE_HIT
    name: set_irq_on_compare
    preconditions:
    - tick_edge == 1
    - enable == 1
    - counter == compare
    inputs:
    - counter
    - compare
    outputs:
    - irq_out == 1
    - state: irq_pending_next_set
      expr: '1'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    state_updates:
    - name: irq_pending_next_set
      expr: '1'
      width: 1
    side_effects:
    - irq_pending is set and remains set until explicitly cleared
    output_rules: []
  - id: TR_IRQ_CLEAR
    name: clear_irq_status_w1c
    preconditions:
    - apb_sel == 1
    - apb_enable_phase == 1
    - apb_write == 1
    - addr == 12
    inputs:
    - pwdata
    outputs:
    - pready_out == 1
    - pslverr_out == 0
    - state: irq_pending_next_clear
      expr: 0 if ((pwdata & 1) == 1) else irq_pending
      description: Mirrored from executable state_updates for SSOT validator completeness.
    state_updates:
    - name: irq_pending_next_clear
      expr: 0 if ((pwdata & 1) == 1) else irq_pending
      width: 1
    side_effects:
    - writing 1 to IRQ_STATUS bit0 clears pending interrupt
    error_cases:
    - condition: (pwdata & 1) == 0
      result: irq_pending remains unchanged
    output_rules: []
  - id: TR_ILLEGAL_ACCESS
    name: illegal_address_response
    preconditions:
    - apb_sel == 1
    - apb_enable_phase == 1
    - addr not in [0, 4, 8, 12]
    inputs:
    - addr
    outputs:
    - pready_out == 1
    - pslverr_out == 1
    - prdata_out == 0
    side_effects:
    - no architectural state change
    output_rules: []
  invariants:
  - irq_pending in [0, 1]
  - (enable == 0) implies (counter_next_if_no_apb == counter)
  - illegal APB access never modifies enable, compare, counter, or irq_pending
  - writes to VALUE address 0x08 are ignored and do not assert pslverr
  derived_signals:
  - name: apb_access
    expr: psel and penable
    width: 1
    description: APB access phase helper derived from psel and penable.
    source: repair_ssot_schema.apb_helper
  - name: apb_valid_write
    expr: psel and penable and pwrite
    width: 1
    description: APB write access helper derived from psel, penable, and pwrite.
    source: repair_ssot_schema.apb_helper
  - name: apb_valid_read
    expr: psel and penable and not pwrite
    width: 1
    description: APB read access helper derived from psel, penable, and pwrite.
    source: repair_ssot_schema.apb_helper
  - name: addr
    expr: paddr
    width: 8
    description: Register address helper derived from the APB paddr input.
    source: repair_ssot_schema.apb_helper
  - name: legal_addr
    expr: (addr == 0) or (addr == 4) or (addr == 8) or (addr == 12)
    width: 1
    description: APB legal address decode derived from registers.register_list offsets.
    source: repair_ssot_schema.apb_helper
  - name: wr_control
    expr: apb_valid_write and (addr == 0)
    width: 1
    description: APB write decode helper for register CONTROL.
    source: repair_ssot_schema.apb_helper
  - name: rd_control
    expr: apb_valid_read and (addr == 0)
    width: 1
    description: APB read decode helper for register CONTROL.
    source: repair_ssot_schema.apb_helper
  - name: wr_compare
    expr: apb_valid_write and (addr == 4)
    width: 1
    description: APB write decode helper for register COMPARE.
    source: repair_ssot_schema.apb_helper
  - name: rd_compare
    expr: apb_valid_read and (addr == 4)
    width: 1
    description: APB read decode helper for register COMPARE.
    source: repair_ssot_schema.apb_helper
  - name: wr_value
    expr: apb_valid_write and (addr == 8)
    width: 1
    description: APB write decode helper for register VALUE.
    source: repair_ssot_schema.apb_helper
  - name: rd_value
    expr: apb_valid_read and (addr == 8)
    width: 1
    description: APB read decode helper for register VALUE.
    source: repair_ssot_schema.apb_helper
  - name: wr_irq_status
    expr: apb_valid_write and (addr == 12)
    width: 1
    description: APB write decode helper for register IRQ_STATUS.
    source: repair_ssot_schema.apb_helper
  - name: rd_irq_status
    expr: apb_valid_read and (addr == 12)
    width: 1
    description: APB read decode helper for register IRQ_STATUS.
    source: repair_ssot_schema.apb_helper
  - name: irq_status_w1c
    expr: ((pwdata & gpio_mask) if wr_irq_status else 0)
    width: 32
    description: W1C write mask helper for register IRQ_STATUS.
    source: repair_ssot_schema.apb_helper
  - name: read_mux
    expr: (0 if addr == 0 else (compare if addr == 4 else (0 if addr == 8 else (0 if addr == 12 else 0))))
    width: 32
    description: APB read data mux derived from registers.register_list offsets and function_model state variables.
    source: repair_ssot_schema.apb_helper
cycle_model:
  purpose: Cycle-accurate handshake and update timing for APB timer.
  executable: pymtl3
  clock: pclk
  reset:
    assertion: presetn low asynchronously clears enable/counter/irq_pending and sets compare to 3
    deassertion: state usable on first rising edge after synchronized deassertion
  latency:
    apb_legal_access:
      min_cycles: 1
      max_cycles: 1
      description: one APB access phase completion with pready=1
    apb_illegal_access:
      min_cycles: 1
      max_cycles: 1
      description: one APB access phase completion with pslverr=1
    irq_set_after_match:
      min_cycles: 0
      max_cycles: 1
      description: irq asserted on compare-match clock edge
    irq_clear_w1c:
      min_cycles: 0
      max_cycles: 1
      description: irq clears on write-1 clear acceptance edge
  handshake_rules:
  - signal: pready
    rule: When psel == 1 and penable == 1, pready shall be 1 in that cycle.
  - signal: pslverr
    rule: pslverr shall be 1 iff psel == 1 and penable == 1 and paddr not in [0,4,8,12].
  - signal: prdata
    rule: For illegal reads, prdata shall be 0; for legal reads, prdata reflects addressed register in same access phase.
  - signal: irq
    rule: irq equals irq_pending combinationally or registered with zero extra protocol latency.
  pipeline:
  - stage: S0_IDLE_OR_COUNT
    cycle: t
    action: counter may increment if enable==1
  - stage: S1_APB_DECODE
    cycle: t
    action: decode paddr when psel&&penable
  - stage: S2_APB_RESPOND
    cycle: t
    action: drive pready/prdata/pslverr and apply legal write side effects
  - stage: S3_IRQ_UPDATE
    cycle: t
    action: set irq_pending on compare hit or clear on IRQ_STATUS W1C
  ordering:
  - compare-hit set of irq_pending has priority over hold and occurs on the same active clock edge as counter evaluation
  - IRQ_STATUS W1C clear applies only for legal address 0x0C write accesses
  - illegal access response is side-effect-free and does not reorder with counter tick behavior
  backpressure:
  - APB slave does not backpressure legal/illegal accesses in access phase because pready is always 1 when selected
  observability:
  - every function_model transaction maps to one or more pipeline stages and directed tests
  backend_policy: Use PyMTL3 for the clocked cycle model shell; FunctionalModel remains the behavioral oracle.
  performance:
    frequency_mhz: 200
    throughput:
      sustained_beats_per_cycle: 1
      condition: No backpressure on the active interface
    outstanding:
      max: 1
      description: Default one accepted operation until the SSOT declares deeper buffering
    depth:
      pipeline_stages: 3
      queue_depth: 1
      description: Default accept/evaluate/observe cycle model depth
clock_reset_domains:
  domains:
  - name: pclk
    frequency_mhz: 200
    description: timer and APB clock domain
  reset_scheme:
    signal: presetn
    polarity: active_low
    type: async_assert_sync_deassert
cdc_requirements:
  crossings: []
  synchronizers: []
  note: Single clock design, no CDC paths.
rdc_requirements:
  crossings: []
  synchronizers: []
  note: Single reset domain, no RDC paths.
registers:
  config:
    register_width: 32
    addr_width: 8
    byte_addressable: true
  register_list:
  - name: CONTROL
    offset: 0
    width: 32
    access: rw
    reset: 0
    description: Control register
    fields:
    - name: enable
      bits:
      - 0
      - 0
      access: rw
      reset: 0
      description: enable counting when set
      write_effect: APB write data updates this field value according to its bit mask.
  - name: COMPARE
    offset: 4
    width: 32
    access: rw
    reset: 3
    description: Compare threshold register
    fields:
    - name: compare
      bits:
      - 7
      - 0
      access: rw
      reset: 3
      description: compare value for interrupt set
      write_effect: APB write data updates this field value according to its bit mask.
  - name: VALUE
    offset: 8
    width: 32
    access: ro
    reset: 0
    description: Current counter value
    fields:
    - name: value
      bits:
      - 7
      - 0
      access: ro
      reset: 0
      description: live 8-bit timer count
    write_behavior: ignored
  - name: IRQ_STATUS
    offset: 12
    width: 32
    access: rw
    reset: 0
    description: Interrupt pending status
    fields:
    - name: pending
      bits:
      - 0
      - 0
      access: rw1c
      reset: 0
      description: pending interrupt flag
      write 1 clears: null
      write_effect: Writing 1 clears the corresponding status bit; writing 0 leaves it unchanged.
memory:
  instances:
  - name: counter_ff
    type: register
    depth: 1
    width: 8
    read_ports: 1
    write_ports: 1
    latency: 0
    description: timer counter storage
  - name: compare_ff
    type: register
    depth: 1
    width: 8
    read_ports: 1
    write_ports: 1
    latency: 0
    description: compare value storage
  note: No SRAM/FIFO structures required.
interrupts:
  sources:
  - name: TIMER_COMPARE
    bit: 0
    type: level
    enable_reg: null
    status_reg: IRQ_STATUS
    clear: W1C
    description: asserted when counter equals compare while enabled
  output:
    signal: irq
    polarity: active_high
    type: level
fsm:
  timer_control:
    states:
    - DISABLED
    - RUNNING
    transitions:
    - from: DISABLED
      to: RUNNING
      condition: enable==1
    - from: RUNNING
      to: DISABLED
      condition: enable==0
    note: two-state control with orthogonal irq_pending latch
timing:
  target_clocks:
  - domain: pclk
    target_freq_mhz: 200
    duty_cycle_pct: 50
  latency_budget:
    apb_access_cycles: 1
    irq_assert_cycles_from_match: 1
    irq_clear_cycles_from_w1c: 1
  throughput:
    counter_increment_per_cycle: 1
  sta_expectations:
  - setup and hold clean at target clock for all register-to-register paths
power:
  domains:
  - name: PD_MAIN
    supply: VDD
    elements:
    - caa_timer_apb
    - caa_timer_core
    always_on: true
  power_states:
  - name: true
    condition: presetn in [0,1]
    behavior: full functionality when reset released
  - name: RESET
    condition: presetn==0
    behavior: counter/irq cleared, compare reset to 3
  clock_gating:
    supported: false
    rationale: small timer, always-clocked design for deterministic behavior
  upf_required: false
security:
  classification: non_secure_peripheral
  assets:
  - timer configuration integrity
  - interrupt signaling correctness
  - APB register access correctness
  threat_model:
  - invalid APB address probes must not corrupt state
  - malformed writes to read-only VALUE must not alter state
  - reset glitch exposure limited to asynchronous clear semantics
  assumptions:
  - APB master is trusted for privilege domain; no internal access control required
  privilege_model: System-level access control is owned by the integrating bus/firewall unless explicitly declared here.
error_handling:
  error_sources:
  - id: ILLEGAL_ADDR
    condition: Declared error condition is observed
    architectural_effect: Status/error reporting follows the SSOT error policy
  - id: WRITE_TO_VALUE
    condition: Declared error condition is observed
    architectural_effect: Status/error reporting follows the SSOT error policy
  propagation:
  - illegal address error is local protocol response only, no interrupt escalation
  recovery:
  - master retries with legal address; internal state remains unchanged
debug_observability:
  waveform_must_probe:
  - paddr
  - psel
  - penable
  - pwrite
  - pwdata
  - prdata
  - pready
  - pslverr
  - enable
  - compare
  - counter
  - irq_pending
  - irq
  trace_events:
  - name: EV_CFG_WRITE
    trigger: psel&&penable&&pwrite&&(paddr in [0,4])
    payload: paddr,pwdata
  - name: EV_COUNT_TICK
    trigger: enable==1
    payload: counter
  - name: EV_IRQ_SET
    trigger: enable==1&&counter==compare
    payload: counter,compare
  - name: EV_IRQ_CLEAR
    trigger: psel&&penable&&pwrite&&(paddr==12)&&((pwdata&1)==1)
    payload: pwdata
  status_outputs:
  - status/debug signals declared in io_list or registers
integration:
  bus_attachment:
    bus_type: APB3
    role: slave
    base_address_requirement: 0x00-0x0F internal offset map
    access_policy: single-cycle access phase response for legal and illegal accesses
  dependencies:
  - APB master drives valid setup/access timing
  - system interrupt controller samples level irq
  connections:
  - from_module: caa_timer
    from_port: irq
    to_signal: irq
  - from_module: caa_timer
    from_port: paddr
    to_signal: paddr
  connection_contract_status: missing machine-readable module wiring; child RTL drafts may proceed from owner packets, but top integration/signoff must stay blocked until SSOT authors integration.connections or sub_modules[].connections with module/port/signal records
  integration_notes:
  - Integrator must connect every declared io_list port and honor timing/reset assumptions.
dft:
  scan_required: true
  controllability:
  - CONTROL.enable and COMPARE.compare shall be controllable via APB scan stimulus equivalent
  - reset controllability through presetn pin
  observability:
  - VALUE and IRQ_STATUS readable via APB
  - irq pin observable at top level
  mbist_required: true
synthesis:
  dialect: systemverilog_2012
  constraints:
  - sdc/caa_timer.sdc defines pclk and reset exceptions
  - no multicycle path assumptions
  required_outputs:
  - gate_level_netlist
  - timing_report_setup_hold
  - area_report
  - power_report
  top_module: caa_timer
pnr:
  utilization_pct: 60
  aspect_ratio: 1.0
  core_space_um: 2.0
  global_density: 0.65
  io_layers:
    horizontal: met3
    vertical: met2
  cts_buf_list:
  - sky130_fd_sc_hd__clkbuf_4
  - sky130_fd_sc_hd__clkbuf_8
  routing:
    signal_layers:
      min: met1
      max: met5
    drc_waivers: []
coding_rules:
  verilog_style: systemverilog_2012
  file_extension: .sv
  conventions:
  - nonblocking assignments in sequential logic
  - blocking assignments in combinational logic
  - no inferred latches
  - explicit default assignments in combinational decode
  - active-low async reset style consistent across all sequential blocks
  lint_waivers: []
reuse_modules: []
custom:
  assumptions:
  - no prescaler
  - no auto-reload
  - no interrupt mask register beyond specified requirements
  optional_behavior_policy:
    resolution: non_required_optional_items_disabled_unless_ssot_marks_required_or_parameterized
    owner: ssot-gen deterministic repair
    rule: Rows marked required:false or prose-only optional verification aids do not add RTL behavior. Any optional functional behavior must be converted by ssot-gen into required behavior or an explicit parameter/register policy before rtl-gen signoff.
dir_structure:
  yaml_dir: yaml/
  output_dirs:
    rtl: rtl/
    list: list/
    tb: tb/
    tc: tc/
    sim: sim/
    lint: lint/
    doc: doc/
filelist:
  headers: []
  rtl:
  - rtl/caa_timer.sv
  - rtl/caa_timer_apb.sv
  - rtl/caa_timer_core.sv
  - rtl/caa_timer_top.sv
  sim:
  - sim/tb_top.sv
  - sim/tb_apb_agent.sv
  - sim/tb_scoreboard.py
  docs:
  - doc/caa_timer_mas.md
  tb:
  - tb/cocotb/test_caa_timer.py
  - tb/cocotb/test_runner.py
  - tb/cocotb/scoreboard.py
  coverage:
  - cov/coverage.json
test_requirements:
  scenarios:
  - id: SC01
    name: reset contract
    stimulus: Assert and release the declared reset while all external interfaces remain idle.
    expected: Architectural state, status, outputs, and debug observability match function_model reset outputs.
    checker: Reset checker compares all declared reset-visible state against function_model and cycle_model reset rules.
    coverage:
    - function_model.reset
    - cycle_model.reset
  - id: SC02
    name: primary approved behavior
    stimulus: Drive a legal request, transaction, command, packet, or CSR operation from function_model primary preconditions.
    expected: Externally observable result/status/side effects match the function_model primary transaction.
    checker: FL-vs-RTL scoreboard compares observable outputs and state updates from the locked function_model.
    coverage:
    - function_model.primary
    - features
    - dataflow
  - id: SC03
    name: cycle handshake and backpressure
    stimulus: Apply legal stalls or delayed handshakes on every declared cycle_model interface phase.
    expected: Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules.
    checker: Protocol monitor and scoreboard check cycle_model.handshake_rules, ordering, and latency budget.
    coverage:
    - cycle_model.handshake_rules
    - cycle_model.ordering
    - backpressure
  - id: SC04
    name: error and recovery policy
    stimulus: Inject each declared error_handling.error_sources condition where the interface can represent it.
    expected: Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state.
    checker: Negative checker compares error result and recovery state against function_model error_cases.
    coverage:
    - error_handling.error_sources
    - function_model.error_cases
  - id: SC05
    name: debug and trace observability
    stimulus: Run nominal and error flows while sampling every debug_observability waveform/status/trace point.
    expected: Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior.
    checker: Waveform/trace checker validates debug_observability entries and traceability.yaml_to_output rows.
    coverage:
    - debug_observability
    - traceability
  - id: SC06
    name: function_model transaction TR_CFG_WRITE
    stimulus: Drive preconditions for function_model transaction `TR_CFG_WRITE`.
    expected: Outputs and side effects match `TR_CFG_WRITE` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.TR_CFG_WRITE
  - id: SC07
    name: function_model transaction TR_COUNT_TICK
    stimulus: Drive preconditions for function_model transaction `TR_COUNT_TICK`.
    expected: Outputs and side effects match `TR_COUNT_TICK` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.TR_COUNT_TICK
  - id: SC08
    name: function_model transaction TR_COMPARE_HIT
    stimulus: Drive preconditions
... <truncated 9399 chars>