Repair the SSOT YAML artifact for caa_timer. This is repair attempt 1.

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
human_gate: while parsing a flow mapping
  in "<unicode string>", line 376, column 7:
        - { name: ON, condition: presetn i ... 
          ^
expected ',' or '}', but got '['
  in "<unicode string>", line 376, column 41:
     ... name: ON, condition: presetn in [0,1], behavior: full functional ... 
                                         ^

Blocker artifact:


Validator log:
cmd: bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh caa_timer --mode engineering
cwd: /Users/brian/Desktop/Project/brian_hw/common_ai_agent
returncode: 1
stdout:
[check_ssot_disk] FAIL: caa_timer/yaml/caa_timer.ssot.yaml failed YAML/model validation
  sub_modules[4].name='caa_timer' duplicates the IP name; rename, drop, or mark wiring_only:true so rtl-gen can tell it from the top wrapper


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
  version: "1.0"
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
    source_sections: [io_list, registers, error_handling]
    implements:
      - io_list.interfaces.apb_slave
      - registers.register_list
      - error_handling.error_sources.ILLEGAL_ADDR
    register_refs: [registers.register_list]
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
    source_sections: [function_model, cycle_model, interrupts, fsm]
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
    cycle_model_refs: [cycle_model.pipeline, cycle_model.handshake_rules]
    fsm_refs: [fsm.timer_control]
    description: Counter, compare detect, irq latch/clear, architectural state updates

parameters:
  - name: ADDR_WIDTH
    default: 8
    type: int
    description: APB address width
    drives: [rtl/caa_timer.sv, rtl/caa_timer_apb.sv]
  - name: DATA_WIDTH
    default: 32
    type: int
    description: APB data width
    drives: [rtl/caa_timer.sv, rtl/caa_timer_apb.sv]
  - name: COUNTER_WIDTH
    default: 8
    type: int
    description: Timer counter and compare register width
    drives: [rtl/caa_timer_core.sv]

io_list:
  clock_domains:
    - name: pclk
      frequency_mhz: 200
      description: APB peripheral clock
      ports:
        - { name: pclk, width: 1, direction: input, description: peripheral clock }
  resets:
    - name: presetn
      polarity: active_low
      sync_async: async_assert_sync_deassert
      description: asynchronous assert, synchronous deassert reset
      ports:
        - { name: presetn, width: 1, direction: input, description: active-low reset }
  interfaces:
    - name: apb_slave
      type: APB3
      role: slave
      description: APB register interface
      ports:
        - { name: paddr, width: 8, direction: input, description: byte address }
        - { name: psel, width: 1, direction: input, description: peripheral select }
        - { name: penable, width: 1, direction: input, description: access phase indicator }
        - { name: pwrite, width: 1, direction: input, description: write direction }
        - { name: pwdata, width: 32, direction: input, description: write data }
        - { name: prdata, width: 32, direction: output, description: read data }
        - { name: pready, width: 1, direction: output, description: transfer ready }
        - { name: pslverr, width: 1, direction: output, description: slave error }
    - name: irq_out
      type: custom
      role: output
      description: timer interrupt output
      ports:
        - { name: irq, width: 1, direction: output, description: interrupt pending level }

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
    - { name: enable, source: registers.register_list.CONTROL.fields.enable, reset: 0, width: 1, description: counting enable }
    - { name: compare, source: registers.register_list.COMPARE.fields.compare, reset: 3, width: 8, description: compare threshold }
    - { name: counter, source: registers.register_list.VALUE.fields.value, reset: 0, width: 8, description: current timer value }
    - { name: irq_pending, source: registers.register_list.IRQ_STATUS.fields.pending, reset: 0, width: 1, description: latched interrupt status }
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
      state_updates:
        - { name: enable_next, expr: "(pwdata & 1) if (addr == 0) else enable", width: 1 }
        - { name: compare_next, expr: "(pwdata & 0xFF) if (addr == 4) else compare", width: 8 }
      side_effects:
        - CONTROL bit0 updates enable when addr==0
        - COMPARE bits7:0 update compare when addr==4
    - id: TR_COUNT_TICK
      name: increment_counter_when_enabled
      preconditions:
        - tick_edge == 1
      inputs:
        - enable
        - counter
      outputs:
        - value_read_data == counter
      state_updates:
        - { name: counter_next, expr: "((counter + 1) & 0xFF) if (enable == 1) else counter", width: 8 }
      side_effects:
        - counter increments by one each clock only while enable is set
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
      state_updates:
        - { name: irq_pending_next_set, expr: "1", width: 1 }
      side_effects:
        - irq_pending is set and remains set until explicitly cleared
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
      state_updates:
        - { name: irq_pending_next_clear, expr: "0 if ((pwdata & 1) == 1) else irq_pending", width: 1 }
      side_effects:
        - writing 1 to IRQ_STATUS bit0 clears pending interrupt
      error_cases:
        - { condition: "(pwdata & 1) == 0", result: irq_pending remains unchanged }
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
  invariants:
    - irq_pending in [0, 1]
    - "(enable == 0) implies (counter_next_if_no_apb == counter)"
    - illegal APB access never modifies enable, compare, counter, or irq_pending
    - writes to VALUE address 0x08 are ignored and do not assert pslverr

cycle_model:
  purpose: Cycle-accurate handshake and update timing for APB timer.
  executable: pymtl3
  clock: pclk
  reset:
    assertion: presetn low asynchronously clears enable/counter/irq_pending and sets compare to 3
    deassertion: state usable on first rising edge after synchronized deassertion
  latency:
    apb_legal_access: { min_cycles: 1, max_cycles: 1, description: one APB access phase completion with pready=1 }
    apb_illegal_access: { min_cycles: 1, max_cycles: 1, description: one APB access phase completion with pslverr=1 }
    irq_set_after_match: { min_cycles: 0, max_cycles: 1, description: irq asserted on compare-match clock edge }
    irq_clear_w1c: { min_cycles: 0, max_cycles: 1, description: irq clears on write-1 clear acceptance edge }
  handshake_rules:
    - { signal: pready, rule: "When psel == 1 and penable == 1, pready shall be 1 in that cycle." }
    - { signal: pslverr, rule: "pslverr shall be 1 iff psel == 1 and penable == 1 and paddr not in [0,4,8,12]." }
    - { signal: prdata, rule: "For illegal reads, prdata shall be 0; for legal reads, prdata reflects addressed register in same access phase." }
    - { signal: irq, rule: "irq equals irq_pending combinationally or registered with zero extra protocol latency." }
  pipeline:
    - { stage: S0_IDLE_OR_COUNT, cycle: "t", action: "counter may increment if enable==1" }
    - { stage: S1_APB_DECODE, cycle: "t", action: "decode paddr when psel&&penable" }
    - { stage: S2_APB_RESPOND, cycle: "t", action: "drive pready/prdata/pslverr and apply legal write side effects" }
    - { stage: S3_IRQ_UPDATE, cycle: "t", action: "set irq_pending on compare hit or clear on IRQ_STATUS W1C" }
  ordering:
    - compare-hit set of irq_pending has priority over hold and occurs on the same active clock edge as counter evaluation
    - IRQ_STATUS W1C clear applies only for legal address 0x0C write accesses
    - illegal access response is side-effect-free and does not reorder with counter tick behavior
  backpressure:
    - APB slave does not backpressure legal/illegal accesses in access phase because pready is always 1 when selected
  observability:
    - every function_model transaction maps to one or more pipeline stages and directed tests

clock_reset_domains:
  domains:
    - { name: pclk, frequency_mhz: 200, description: timer and APB clock domain }
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
      offset: 0x00
      width: 32
      access: rw
      reset: 0x00000000
      description: Control register
      fields:
        - { name: enable, bits: [0, 0], access: rw, reset: 0x0, description: enable counting when set }
    - name: COMPARE
      offset: 0x04
      width: 32
      access: rw
      reset: 0x00000003
      description: Compare threshold register
      fields:
        - { name: compare, bits: [7, 0], access: rw, reset: 0x03, description: compare value for interrupt set }
    - name: VALUE
      offset: 0x08
      width: 32
      access: ro
      reset: 0x00000000
      description: Current counter value
      fields:
        - { name: value, bits: [7, 0], access: ro, reset: 0x00, description: live 8-bit timer count }
      write_behavior: ignored
    - name: IRQ_STATUS
      offset: 0x0C
      width: 32
      access: rw
      reset: 0x00000000
      description: Interrupt pending status
      fields:
        - { name: pending, bits: [0, 0], access: rw1c, reset: 0x0, description: pending interrupt flag, write 1 clears }

memory:
  instances:
    - { name: counter_ff, type: register, depth: 1, width: 8, read_ports: 1, write_ports: 1, latency: 0, description: timer counter storage }
    - { name: compare_ff, type: register, depth: 1, width: 8, read_ports: 1, write_ports: 1, latency: 0, description: compare value storage }
  note: No SRAM/FIFO structures required.

interrupts:
  sources:
    - { name: TIMER_COMPARE, bit: 0, type: level, enable_reg: null, status_reg: IRQ_STATUS, clear: W1C, description: asserted when counter equals compare while enabled }
  output:
    signal: irq
    polarity: active_high
    type: level

fsm:
  timer_control:
    states: [DISABLED, RUNNING]
    transitions:
      - { from: DISABLED, to: RUNNING, condition: enable==1 }
      - { from: RUNNING, to: DISABLED, condition: enable==0 }
    note: two-state control with orthogonal irq_pending latch

timing:
  target_clocks:
    - { domain: pclk, target_freq_mhz: 200, duty_cycle_pct: 50 }
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
    - { name: PD_MAIN, supply: VDD, elements: [caa_timer_apb, caa_timer_core], always_on: true }
  power_states:
    - { name: ON, condition: presetn in [0,1], behavior: full functionality when reset released }
    - { name: RESET, condition: presetn==0, behavior: counter/irq cleared, compare reset to 3 }
  clock_gating:
    supported: false
    rationale: small timer, always-clocked design for deterministic behavior

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

error_handling:
  error_sources:
    - { name: ILLEGAL_ADDR, trigger: "psel&&penable&&(paddr not in [0x00,0x04,0x08,0x0C])", effect: pslverr=1 and prdata=0 }
    - { name: WRITE_TO_VALUE, trigger: "psel&&penable&&pwrite&&(paddr==0x08)", effect: ignored write with pslverr=0 }
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
    - { name: EV_CFG_WRITE, trigger: "psel&&penable&&pwrite&&(paddr in [0,4])", payload: "paddr,pwdata" }
    - { name: EV_COUNT_TICK, trigger: "enable==1", payload: "counter" }
    - { name: EV_IRQ_SET, trigger: "enable==1&&counter==compare", payload: "counter,compare" }
    - { name: EV_IRQ_CLEAR, trigger: "psel&&penable&&pwrite&&(paddr==12)&&((pwdata&1)==1)", payload: "pwdata" }

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
    - { from_module: caa_timer, from_port: irq, to_signal: irq }
    - { from_module: caa_timer, from_port: paddr, to_signal: paddr }

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

dft:
  scan_required: true
  controllability:
    - CONTROL.enable and COMPARE.compare shall be controllable via APB scan stimulus equivalent
    - reset controllability through presetn pin
  observability:
    - VALUE and IRQ_STATUS readable via APB
    - irq pin observable at top level

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
    - no prescaler, no auto-reload, no interrupt mask register beyond specified requirements

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
  sim:
    - sim/tb_top.sv
    - sim/tb_apb_agent.sv
    - sim/tb_scoreboard.py
  docs:
    - doc/caa_timer_mas.md

rtl_contract:
  top: caa_timer
  ownership_model:
    - caa_timer_apb owns APB decode, legal/illegal response signaling, register read/write mux
    - caa_timer_core owns timer state, compare logic, irq latch/clear behavior
  must_implement:
    - legal APB accesses complete with pready=1 in one access phase
    - illegal addresses assert pslverr=1 and prdata=0 without state mutation
    - VALUE writes ignored without error
    - counter increments once per cycle while enabled
    - irq sets on counter==compare while enabled and remains asserted until W1C clear
  mismatch_ownership:
    - protocol mismatch: caa_timer_apb
    - state-transition mismatch: caa_timer_core
    - irq behavior mismatch: caa_timer_core

test_requirements:
  scenarios:
    - id: SCN_APB_RESET_DEFAULTS
      name: reset_defaults
      stimulus: assert reset then release; read CONTROL/COMPARE/VALUE/IRQ_STATUS
      expected: CONTROL=0 COMPARE=3 VALUE=0 IRQ_STATUS=0
      checker: APB read checker against function_model reset state
      coverage: [function_model.state_variables, cycle_model.reset]
    - id: SCN_ENABLE_AND_COUNT
      name: enable_counter_increments
      stimulus: write CONTROL.enable=1 then observe VALUE over 6 clocks
      expected: VALUE increments by one each cycle modulo 256
      checker: cycle-accurate counter progression checker
      coverage: [function_model.transactions.TR_COUNT_TICK, cycle_model.pipeline]
    - id: SCN_COMPARE_IRQ_SET
      name: compare_sets_irq
      stimulus: set COMPARE=5, enable counter, run until VALUE reaches 5
      expected: irq and IRQ_STATUS.pending assert and remain high
      checker: scoreboard checks sticky irq_pending after match
      coverage: [function_model.transactions.TR_COMPARE_HIT, interrupts.sources]
    - id: SCN_IRQ_W1C_CLEAR
      name: irq_clear_w1c
      stimulus: cause irq pending then write IRQ_STATUS bit0=1
      expected: irq deasserts and IRQ_STATUS.pending clears
      checker: APB write/readback plus irq pin checker
      coverage: [function_model.transactions.TR_IRQ_CLEAR, cycle_model.latency]
    - id: SCN_VALUE_WRITE_IGNORED
      name: value_write_ignored
      stimulus: write random data to VALUE address 0x08
      expected: counter state unchanged, no pslverr
      checker: pre/post VALUE compare and pslverr assertion checker
      coverage: [error_handling.error_sources.WRITE_TO_VALUE]
    - id: SCN_ILLEGAL_ADDR
      name: illegal_address_behavior
      stimulus: read and write address 0x10
      expected: pslverr=1 prdata=0 and architectural state unchanged
      checker: protocol and state-stability assertion
      coverage: [function_model.transactions.TR_ILLEGAL_ACCESS, error_handling.error_sources.ILLEGAL_ADDR]
  scoreboard_checks: 14
  coverage_goals:
    function:
      target_pct: 100
      model: function_model
      bins:
        - { id: FCOV_CFG_WRITE, source_ref: function_model.transactions.TR_CFG_WRITE, class: transaction, description: control/compare writes }
        - { id: FCOV_TICK, source_ref: function_model.transactions.TR_COUNT_TICK, class: transaction, description: enabled increment }
        - { id: FCOV_IRQ_SET, source_ref: function_model.transactions.TR_COMPARE_HIT, class: transaction, description: compare-triggered set }
        - { id: FCOV_IRQ_CLEAR, source_ref: function_model.transactions.TR_IRQ_CLEAR, class: transaction, description: w1c clear }
        - { id: FCOV_ILLEGAL, source_ref: function_model.transactions.TR_ILLEGAL_ACCESS, class: transaction, description: illegal response }
    cycle:
      target_pct: 100
      model: cycle_model
      bins:
        - { id: CCOV_APB_ONE_CYCLE, source_ref: cycle_model.latency.apb_legal_access, class: latency, description: one-cycle legal completion }
        - { id: CCOV_PSLVERR_RULE, source_ref: cycle_model.handshake_rules, class: handshake, description: illegal access error timing }
        - { id: CCOV_PIPELINE_STAGE, source_ref: cycle_model.pipeline, class: pipeline_stage, description: all stages observed }
    code: line >= 95%, branch >= 90%

quality_gates:
  rtl_gen:
    profile: standard
    pass: RTL generated by common_ai_agent rtl-gen using SSOT ownership and workflow_todos
    evidence: [rtl/rtl_authoring_provenance.json, rtl/rtl_todo_plan.json]
  ssot:
    pass: check_ssot_disk.sh passes in engineering mode with no unresolved behavior TBDs
    evidence: [yaml/caa_timer.ssot.yaml, req/caa_timer_requirements.md]
  rtl:
    pass: compiles cleanly and matches function_model/cycle_model intent
    evidence: [rtl/compile.log, lint/lint_report.txt]
  dv:
    pass: directed tests and scoreboard checks pass for all declared scenarios
    evidence: [sim/regression_summary.json, sim/scoreboard_report.json]
  coverage:
    pass: functional and cycle coverage goals meet 100 percent bins; code coverage target met
    evidence: [sim/coverage_report.json, cov/coverage.json]
  eda:
    pass: synthesis and STA meet target clock or documented waiver
    evidence: [syn/syn_report.rpt, sta/sta_setup_hold.rpt]
  signoff:
    pass: rtl/dv/coverage/eda gates satisfied and traceability complete
    evidence: [signoff/signoff_checklist.md]

traceability:
  yaml_to_output:
    - { yaml: top_module.name, output: rtl/caa_timer.sv }
    - { yaml: io_list.interfaces.apb_slave, output: rtl/caa_timer_apb.sv }
    - { yaml: registers.register_list, output: rtl/caa_timer_apb.sv }
    - { yaml: function_model.transactions, output: rtl/caa_timer_core.sv }
    - { yaml: cycle_model, output: rtl/caa_timer_core.sv }
    - { yaml: interrupts, output: rtl/caa_timer_core.sv }
    - { yaml: test_requirements.scenarios, output: sim/tb_top.sv and sim/tb_scoreboard.py }

workflow_todos:
  fl-model-gen: []
  rtl-gen:
    - id: RTL_TODO_APB_DECODE
      content: Implement APB3 address decode and legal/illegal response behavior
      detail: Create decode for 0x00/0x04/0x08/0x0C; drive pready high in access phase; assert pslverr only for illegal addresses; force illegal read prdata=0 and block state writes.
      criteria:
        - all legal accesses complete with pready=1 in one access phase
        - illegal accesses return prdata=0 and leave state unchanged
        - VALUE writes are ignored and pslverr remains 0
      source_refs: [io_list.interfaces.apb_slave, registers.register_list, function_model.transactions.TR_ILLEGAL_ACCESS, error_handling]
      owner_module: caa_timer_apb
      owner_file: rtl/caa_timer_apb.sv
      priority: high
      required: true
    - id: RTL_TODO_COUNTER_IRQ
      content: Implement enable-controlled 8-bit counter and compare-triggered sticky irq
      detail: Counter increments once per rising edge while enable=1, compare match sets irq_pending, and IRQ_STATUS W1C clears irq_pending.
      criteria:
        - counter increments exactly one step per clock when enabled
        - irq_pending sets when counter equals compare while enabled
        - irq_pending clears only on IRQ_STATUS write with bit0=1 or reset
      source_refs: [function_model.transactions.TR_COUNT_TICK, function_model.transactions.TR_COMPARE_HIT, function_model.transactions.TR_IRQ_CLEAR, interrupts]
      owner_module: caa_timer_core
      owner_file: rtl/caa_timer_core.sv
      priority: high
      required: true
    - id: RTL_TODO_TOP_INTEGRATION
      content: Integrate APB and core submodules in top-level caa_timer
      detail: Wire APB decoded strobes/data to core state update ports and route irq_pending to top irq output with consistent reset/clock hookups.
      criteria:
        - top module ports match io_list exactly
        - no duplicated state ownership between submodules
        - simulation shows coherent register readback and irq behavior
      source_refs: [top_module, sub_modules, integration.connections, rtl_contract]
      owner_module: caa_timer
      owner_file: rtl/caa_timer.sv
      priority: high
      required: true
  tb-gen: []
  sim_debug: []
  coverage: []
  syn: []
  pnr: []
  sta: []
  sta-post: []

generation_flow:
  steps:
    - { name: validate_ssot, command: "bash workflow/ssot-gen/scripts/check_ssot_disk.sh caa_timer --mode engineering", description: validate SSOT completeness and engineering gates }
    - { name: handoff_rtl, command: "/ssot-rtl caa_timer", description: generate RTL via common_ai_agent rtl-gen with LLM provenance }
    - { name: handoff_tb, command: "/ssot-tb caa_timer", description: generate TB/scoreboard from SSOT models }
    - { name: run_sim, command: "/wf sim_debug", description: execute regression and debug mismatches }
    - { name: run_coverage, command: "/coverage caa_timer", description: collect functional/cycle/code coverage against SSOT goals }
    - { name: run_eda, command: "/syn caa_timer && /sta caa_timer", description: produce synthesis and timing evidence for engineering closure }
