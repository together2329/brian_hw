RTL-GEN PACKET MODE for cortex_m0lite. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "cortex_m0lite/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "cortex_m0lite/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "cortex_m0lite/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
  ]
}

If this packet exposes a missing locked-truth decision, return a human_gate object instead of inventing SSOT, FL, coverage, interface, or performance semantics.

Packet execution rules:
- Author only RTL-owned artifacts for the current packet, plus local notes/contract metadata when useful.
- Do not edit SSOT YAML, FunctionalModel, coverage goals, protocol assertions, performance targets, or requirements.
- You cannot read files from the repo during this turn. The required locked SSOT facts are embedded below; do not return requires/missing-file JSON for those paths.
- Do not emit placeholder, heartbeat-only, alive-only, or tie-off-only RTL to satisfy a manifest.
- For production-profile packets, add real SSOT-scaled implementation depth: state/control/data movement, nonconstant logic, and child wiring must be proportional to the packet tasks.
- For a module packet, focus on owner_file and every task content/detail/criteria/source_ref in the packet.
- If current owner_file content is provided, preserve prior slice logic and merge the new behavior; do not replace the file with a partial slice-only module.
- For mixed packets with locked-truth blockers, keep authoring LLM-actionable RTL/test/evidence work and leave the locked-truth tasks open.
- Return human_gate only when no LLM-actionable open work remains or the missing locked-truth decision blocks correct RTL authoring.
- For rtl_gate_evidence_closure, repair only LLM-actionable evidence gaps revealed by compile/lint/audit output; do not claim PASS.
- If rtl_gate_evidence_closure includes pending connection_contract_suggestions, you may use them as draft RTL wiring candidates to instantiate child modules and close hierarchy/signal-flow evidence, but they remain pending QA and must not be treated as SSOT authority.
- For rtl_gate_tool_evidence, do not fabricate compile/lint/sim/coverage artifacts. If compile/lint evidence already exists and is not clean, repair the owner RTL that caused the diagnostics; the runner will rerun tools afterward.
- For rtl_gate_contract_blocked, return human_gate only; missing SSOT connection contracts block correct top integration semantics.
- For rtl_gate_human_closure, return human_gate only; do not invent or edit human-locked authority.
- The headless runner will refresh filelist/provenance from LLM-authored artifacts after each packet.

Current packet: module__timer_core__fsm
kind: module
work queue: 4/4 active packets (2 closed packets skipped from 20 total)
batch limit: 4; deferred active packets after this batch: 14
owner_module: timer_core
owner_file: rtl/cortex_m0lite.sv

SSOT observable latency contract:
{
  "cycle_model.latency": 1,
  "cycle_model.pipeline": [
    {
      "action": "Sample fetch_en, step_en, flush, instr_data, pc, and busy.",
      "cycle": 0,
      "stage": "S0_CONTROL_SAMPLE"
    },
    {
      "action": "Present updated pc, busy, and retire.",
      "cycle": 1,
      "stage": "S1_STATE_VISIBLE"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": "fetch_en or flush or step_en or retire_q",
  "timing.latency_budget": {
    "fetch_en_to_pc_visible": {
      "max": 1,
      "min": 1,
      "unit": "cycles"
    },
    "terminal_tick_to_retire": {
      "max": 1,
      "min": 1,
      "unit": "cycles"
    }
  }
}

Locked SSOT YAML excerpt (cortex_m0lite/yaml/cortex_m0lite.ssot.yaml):
top_module:
  name: cortex_m0lite
  description: Small parameterized pcdown cortex_m0lite used as an ATLAS SSOT pipeline smoke fixture.
  owner: ssot-gen
  quality_profile: standard

sub_modules:
  - name: timer_core
    file: rtl/cortex_m0lite.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - function_model.transactions.FM_TICK
      - cycle_model
      - rtl_contract
    source_sections:
      - io_list
      - parameters
      - function_model
      - cycle_model
      - fsm
      - rtl_contract
    description: Single-leaf RTL block for pcdown state, retire pulse, and observable debug outputs.

decomposition:
  modules:
    - name: timer_core
      role: pcdown datapath and control
      owns:
        - pc
        - busy
        - retire
  ownership:
    function_model: timer_core
    cycle_model: timer_core
    rtl_contract: timer_core
  internal_state:
    - name: pc_q
      drives_output: pc
    - name: busy_q
      drives_output: busy
    - name: retire_q
      drives_output: retire

rtl_contract:
  clock: clk
  reset: rst_n
  reset_active: low
  transaction: FM_TICK
  sample_condition: "fetch_en or flush or step_en or retire_q"
  input_map:
    load: instr_data
  output_map:
    pc_next: pc
    busy_next: busy
    retire_pulse: retire
  output_rules:
    - name: pc_next
      port: pc
      width: 16
      expr: "0 if flush else (load if fetch_en else ((pc_q - 1) if (step_en and busy_q and (pc_q > 0)) else pc_q))"
    - name: busy_next
      port: busy
      width: 1
      expr: "0 if flush else ((load > 0) if fetch_en else (0 if (step_en and busy_q and (pc_q <= 1)) else busy_q))"
    - name: retire_pulse
      port: retire
      width: 1
      expr: "0 if flush else (0 if fetch_en else (1 if (step_en and busy_q and (pc_q == 1)) else 0))"
  state_updates:
    - name: pc_q
      width: 16
      reset: 0
      expr: "0 if flush else (load if fetch_en else ((pc_q - 1) if (step_en and busy_q and (pc_q > 0)) else pc_q))"
    - name: busy_q
      width: 1
      reset: 0
      expr: "0 if flush else ((load > 0) if fetch_en else (0 if (step_en and busy_q and (pc_q <= 1)) else busy_q))"
    - name: retire_q
      width: 1
      reset: 0
      expr: "0 if flush else (0 if fetch_en else (1 if (step_en and busy_q and (pc_q == 1)) else 0))"

parameters:
  - name: XLEN
    type: int
    default: 16
    description: Width of instr_data and pc.
    user_editable: true

io_list:
  clock_domains:
    - name: main
      ports:
        - name: clk
          direction: input
          width: 1
  resets:
    - name: rst_n
      active: low
      ports:
        - name: rst_n
          direction: input
          width: 1
  interfaces:
    - name: timer_ctrl
      type: custom_control
      ports:
        - name: fetch_en
          direction: input
          width: 1
          description: Load instr_data and fetch_en the pcdown.
        - name: step_en
          direction: input
          width: 1
          description: Advance the pcdown while busy.
        - name: flush
          direction: input
          width: 1
          description: Clear and stop the cortex_m0lite.
        - name: instr_data
          direction: input
          width: XLEN
          parameter_ref: XLEN
          description: Initial pc value loaded on fetch_en.
        - name: pc
          direction: output
          width: XLEN
          parameter_ref: XLEN
          description: Current pcdown value.
        - name: busy
          direction: output
          width: 1
          description: High while the cortex_m0lite is active.
        - name: retire
          direction: output
          width: 1
          description: One-cycle pulse when the pcdown reaches zero.

features:
  - name: parameterized_pcdown
    description: Countdown width is controlled by XLEN so users can resize the cortex_m0lite without changing control logic.
    requirement_trace: req/requirements.md#functional-behavior
  - name: retire_pulse
    description: retire pulses when the cortex_m0lite consumes pc value 1 and then flushs on the next observable control cycle.
    requirement_trace: req/requirements.md#functional-behavior
  - name: flush_priority
    description: flush has priority over pcdown tick behavior and flushs observable state.
    requirement_trace: req/requirements.md#functional-behavior

dataflow:
  sequence:
    - Reset flushs pc, busy, and retire.
    - fetch_en samples instr_data into pc and asserts busy when instr_data is non-zero.
    - step_en advances the pcdown by one while busy is high.
    - flush overrides cortex_m0lite progress and returns observable state to idle.
  ordering:
    - flush is evaluated before pcdown decrement.
    - fetch_en creates a new cortex_m0lite interval before step_en tick side effects are considered.
    - retire is derived from the cycle where pc is one and step_en is asserted.
  state_flow:
    - instr_data -> pc_q -> pc
    - pc_q/busy_q/step_en -> pc_next/busy_next/retire_pulse

function_model:
  purpose: Cycle-independent cortex_m0lite reference model for scoreboard and RTL equivalence checks.
  state_variables:
    - name: pc_q
      width: 16
      reset: 0
      description: Internal current pcdown value that drives pc.
    - name: busy_q
      width: 1
      reset: 0
      description: Internal cortex_m0lite active state that drives busy.
    - name: retire_q
      width: 1
      reset: 0
      description: Internal completion pulse state that drives retire.
  transactions:
    - id: FM_TICK
      name: timer_control_tick
      required_fields:
        - fetch_en
        - step_en
        - flush
        - load
      preconditions:
        - rst_n is deasserted
        - load is in the range 0 to 2**XLEN-1
      outputs:
        - pc
        - busy
        - retire
      output_rules:
        - name: pc_next
          port: pc
          width: 16
          expr: "0 if flush else (load if fetch_en else ((pc_q - 1) if (step_en and busy_q and (pc_q > 0)) else pc_q))"
        - name: busy_next
          port: busy
          width: 1
          expr: "0 if flush else ((load > 0) if fetch_en else (0 if (step_en and busy_q and (pc_q <= 1)) else busy_q))"
        - name: retire_pulse
          port: retire
          width: 1
          expr: "0 if flush else (0 if fetch_en else (1 if (step_en and busy_q and (pc_q == 1)) else 0))"
      state_updates:
        - name: pc_q
          width: 16
          reset: 0
          expr: "0 if flush else (load if fetch_en else ((pc_q - 1) if (step_en and busy_q and (pc_q > 0)) else pc_q))"
        - name: busy_q
          width: 1
          reset: 0
          expr: "0 if flush else ((load > 0) if fetch_en else (0 if (step_en and busy_q and (pc_q <= 1)) else busy_q))"
        - name: retire_q
          width: 1
          reset: 0
          expr: "0 if flush else (0 if fetch_en else (1 if (step_en and busy_q and (pc_q == 1)) else 0))"
      side_effects:
        - pc updates according to fetch_en, flush, and step_en priority.
        - busy drops when the pcdown consumes the final pc.
        - retire pulses for the terminal pcdown tick.
      error_cases:
        - No protocol error is generated; out-of-range load values are impossible after port truncation.
  invariants:
    - Reset or flush leaves pc=0, busy=0, and retire=0.
    - retire is asserted only on a terminal step_end pcdown tick.
    - pc never underflows below zero because the decrement rule is gated by pc > 0.
    - When step_en is low and no fetch_en or flush is asserted, pc and busy hold their previous values.
  reference_model_hint: FunctionalModel.apply(fetch_en, step_en, flush, load) returns pc, busy, and retire after one control tick.

cycle_model:
  executable: pymtl3
  backend_policy: Use PyMTL3 for the cycle model shell and keep the FunctionalModel as the behavioral oracle.
  clock: clk
  reset: rst_n
  latency: 1
  handshake_rules:
    - name: fetch_en_load
      description: fetch_en samples instr_data on the active clock edge and makes the loaded pc visible after that edge.
    - name: step_end_tick
      description: step_en advances pc only while busy is high.
    - name: flush_priority
      description: flush returns the cortex_m0lite to idle regardless of step_en or busy.
  pipeline:
    - stage: S0_CONTROL_SAMPLE
      cycle: 0
      action: Sample fetch_en, step_en, flush, instr_data, pc, and busy.
    - stage: S1_STATE_VISIBLE
      cycle: 1
      action: Present updated pc, busy, and retire.
  ordering:
    - flush has highest priority.
    - fetch_en load is applied before step_end pcdown behavior for a new interval.
    - retire is observed on the same state-visible cycle as the terminal decrement.
  backpressure:
    - There is no ready/valid backpressure; step_en controls cortex_m0lite progress.
  performance:
    frequency_mhz: 100
    throughput:
      sustained_ticks_per_cycle: 1
      condition: step_en asserted while busy
    outstanding:
      max: 1
      description: One active pcdown interval at a time.
    depth:
      pipeline_stages: 1
      queue_depth: 0
      description: Registered state update with no internal queue.
    pipelining:
      style: single_stage_registered_control
      overlap: none

clock_reset_domains:
  domains:
    - name: main
      clock: clk
      reset: rst_n
      reset_active: low

cdc_requirements:
  crossings: []
  rationale: Single clock domain.

rdc_requirements:
  crossings: []
  rationale: Single reset domain.

registers:
  register_list: []
  architectural_state:
    - name: pc_q
      reset: 0
      source: function_model.state_variables.pc_q
      drives_output: pc
    - name: busy_q
      reset: 0
      source: function_model.state_variables.busy_q
      drives_output: busy
    - name: retire_q
      reset: 0
      source: function_model.state_variables.retire_q
      drives_output: retire

memory:
  instances: []
  rationale: No memory is needed for this small pcdown cortex_m0lite.

interrupts:
  sources: []
  outputs: []
  rationale: The smoke fixture exposes retire as a pulse output instead of an interrupt line.

fsm:
  control:
    diagram_kind: state_transition
    reset_state: IDLE
    states:
      - name: IDLE
        description: CortexM0Lite is not busy and pc is zero or waiting for fetch_en.
      - name: RUN
        description: CortexM0Lite is pcing down while busy is high.
      - name: DONE_PULSE
        description: One-cycle observable completion pulse.
    transitions:
      - from: IDLE
        to: RUN
        condition: fetch_en and instr_data != 0
        action: Load pc and assert busy.
      - from: RUN
        to: RUN
        condition: step_en and pc > 1
        action: Decrement pc.
      - from: RUN
        to: DONE_PULSE
        condition: step_en and pc == 1
        action: Drive retire and stop busy.
      - from: DONE_PULSE
        to: IDLE
        condition: next control cycle without fetch_en
        action: Clear retire.
      - from: RUN
        to: IDLE
        condition: flush
        action: Clear state.

timing:
  target_clocks:
    - name: clk
      frequency_mhz: 100
      period_ns: 10.0
  latency_budget:
    fetch_en_to_pc_visible:
      min: 1
      max: 1
      unit: cycles
    terminal_tick_to_retire:
      min: 1
      max: 1
      unit: cycles

power:
  domains:
    - name: PD_MAIN
      clock_domains:
        - main
      isolation: not_required
  power_states:
    - name: ON
      entry: rst_n deasserted
      exit: rst_n asserted or integration power down
      guarantees:
        - CortexM0Lite state follows function_model.

security:
  classification: non_secure_leaf_ip
  assets:
    - name: timer_state_integrity
      protection: pc, busy, and retire must match the function_model.
  threat_model:
    - threat: silent cortex_m0lite completion corruption
      mitigation: FL-vs-RTL scoreboard and retire_pulse coverage bins.

error_handling:
  error_sources:
    - id: ERR_NONE
      condition: No malformed transaction class exists for this leaf IP.
      architectural_effect: No error output is asserted.
  propagation:
    - Error propagation is not applicable.
  recovery:
    - action: flush
      flushs:
        - pc
        - busy
        - retire
    - action: reset
      flushs:
        - pc
        - busy
        - retire

debug_observability:
  waveform_must_probe:
    - clk
    - rst_n
    - fetch_en
    - step_en
    - flush
    - instr_data
    - pc
    - busy
    - retire
  trace_events:
    - name: timer_fetch_en
      trigger: fetch_en
    - name: timer_tick
      trigger: step_en and busy
    - name: timer_retire
      trigger: retire

integration:
  bus_attachment:
    type: native_control
    interfaces:
      - timer_ctrl
  dependencies:
    external_modules: []
    external_clocks:
      - clk
    external_resets:
      - rst_n
  connections: []

dft:
  scan_required: false
  controllability:
    reset: rst_n
    clock: clk
    inputs:
      - fetch_en
      - step_en
      - flush
      - instr_data
  observability:
    outputs:
      - pc
      - busy
      - retire

synthesis:
  dialect: systemverilog_2012
  constraints:
    - No inferred latches.
    - No unresolved black boxes.
    - XLEN must remain a positive integer.
  required_outputs:
    - rtl/cortex_m0lite.sv
    - list/cortex_m0lite.f
    - reports/syn/syn_report.json
  pdk_policy:
    default_family: sky130
    library_root: pdk/
    fallback: report actionable missing-lib message rather than silently using fake timing.

pnr:
  floorplan:
    utilization_target_pct: 65
    aspect_ratio: 1.0
  clocking:
    primary_clock: clk
    target_skew_ps: 100
  route:
    max_routing_layer: M5
    congestion_target_pct: 75
  required_outputs:
    - reports/pnr/pnr_report.json
    - reports/pnr/def/final.def

coding_rules:
  verilog_style: systemverilog_2012
  port_declaration_default: input logic and output logic
  arithmetic_policy:
    multiply: prefer shifts when the operation is a power-of-two scale.
    divide: prefer shifts when the divisor is a power of two.
    timer_note: This cortex_m0lite uses subtract-by-one only; no multiply or divide is required.
  conventions:
    - Use parameterized widths for instr_data and pc.
    - Comment reset, flush, fetch_en, tick, and retire-pulse behavior flushly.
    - Keep combinational expressions machine-checkable against function_model output_rules.
  lint_waivers: []

reuse_modules: []

custom:
  assumptions:
    - This smoke fixture intentionally avoids bus integration to keep the pipeline test fast.
    - instr_data zero fetch_ens an empty interval and immediately leaves busy low after the next state update.
  optional_behavior_policy:
    resolution: No optional cortex_m0lite modes are step_end by default.
    downstream_rule: rtl-gen and tb-gen must implement only the explicit function_model and cycle_model rules.

dir_structure:
  yaml_dir: yaml/
  req_dir: req/
  rtl_dir: rtl/
  list_dir: list/
  tb_dir: tb/
  sim_dir: sim/
  cov_dir: cov/
  lint_dir: lint/
  doc_dir: doc/
  reports_dir: reports/

filelist:
  rtl:
    - rtl/cortex_m0lite.sv
  tb:
    - tb/cocotb/test_timer.py
  coverage:
    - cov/coverage.json
    - cov/fcov_plan.json

test_requirements:
  scenarios:
    - id: SC_RESET_CLEAR
      name: reset and flush force idle
      stimulus: Assert reset, then fetch_en the cortex_m0lite, then assert flush.
      expected: pc=0, busy=0, retire=0 after reset or flush.
      checker: Scoreboard compares outputs against FunctionalModel reset and flush state.
      coverage:
        - fcov_flush_priority
        - ccov_reset_recovery
    - id: SC_COUNTDOWN_DONE
      name: pcdown reaches retire
      stimulus: fetch_en with instr_data=3 and keep step_en asserted.
      expected: pc decrements 3 to 2 to 1 to 0, busy drops, and retire pulses once.
      checker: Scoreboard compares every cycle against FunctionalModel.apply.
      coverage:
        - fcov_retire_pulse
        - ccov_terminal_tick
    - id: SC_ENABLE_HOLD
      name: step_en low holds state
      stimulus: fetch_en with instr_data=4, deassert step_en for two cycles, then resume step_en.
      expected: pc and busy hold while step_en is low.
      checker: Cycle checker verifies no decrement occurs when step_en is low.
      coverage:
        - fcov_step_en_hold
        - ccov_hold_cycle
  scoreboard_checks:
    - reset_state
    - flush_priority
    - pcdown_sequence
    - retire_pulse_width
    - step_en_hold
  coverage_goals:
    function:
      target_pct: 100
      model: function_model
      description: Functional coverage for fetch_en, flush, step_end pcdown, hold, and retire pulse behavior.
      bins:
        - id: fcov_fetch_en_load
          source_ref: function_model.transactions.FM_TICK
          class: transaction
          description: fetch_en loads instr_data into pc.
        - id: fcov_flush_priority
          source_ref: function_model.invariants.flush
          class: state
          description: flush returns all observable state to idle.
        - id: fcov_retire_pulse
          source_ref: function_model.transactions.FM_TICK.output_rules.retire_pulse
          class: event
          description: terminal step_end tick asserts retire for one pulse.
        - id: fcov_step_en_hold
          source_ref: function_model.invariants.step_en_hold
          class: state
          description: step_en low prevents pcdown progress.
    cycle:
      target_pct: 100
      model: cycle_model
      description: Cycle coverage for reset, fetch_en-load latency, step_end tick latency, hold cycles, and terminal retire timing.
      bins:
        - id: ccov_fetch_en_visible_next_cycle
          source_ref: cycle_model.pipeline.S1_STATE_VISIBLE
          class: latency
          description: fetch_en result is visible on the next clock edge.
        - id: ccov_terminal_tick
          source_ref: cycle_model.handshake_rules.step_end_tick
          class: timing
          description: terminal pcdown tick drives retire timing.
        - id: ccov_hold_cycle
          source_ref: cycle_model.backpressure
          class: control
          description: step_en low hold is observed.
    planned_bins:
      - id: fcov_fetch_en_load
        class: transaction
        coverage_domain: function
        source_ref: function_model.transactions.FM_TICK
        description: fetch_en loads instr_data.
      - id: fcov_retire_pulse
        class: event
        coverage_domain: function
        source_ref: function_model.transactions.FM_TICK.output_rules.retire_pulse
        description: retire pulse observed.
      - id: ccov_terminal_tick
        class: timing
        coverage_domain: cycle
        source_ref: cycle_model.handshake_rules.step_end_tick
        description: terminal tick timing observed.

quality_gates:
  ssot:
    pass: check_ssot_disk.sh exits 0 for cortex_m0lite/yaml/cortex_m0lite.ssot.yaml.
    evidence:
      - workflow/ssot-gen/scripts/check_ssot_disk.sh PASS
  rtl:
    pass: RTL implements function_model and cycle_model with DUT-only compile and lint evidence.
    evidence:
      - cortex_m0lite/rtl/cortex_m0lite.sv
      - cortex_m0lite/list/cortex_m0lite.f
      - cortex_m0lite/rtl_compile.json
      - cortex_m0lite/lint/dut_lint.json
  dv:
    pass: Cocotb scenarios pass against FunctionalModel scoreboard.
    evidence:
      - cortex_m0lite/sim/results.xml
      - cortex_m0lite/sim/scoreboard_events.jsonl
  coverage:
    pass: Function and cycle coverage plans include fetch_en, hold, terminal tick, and retire pulse bins.
    evidence:
      - cortex_m0lite/cov/fl_fcov_plan.json
      - cortex_m0lite/cov/cl_fcov_plan.json
      - cortex_m0lite/cov/fcov_plan.json
  eda:
    pass: Lint, synthesis, STA, and PNR report actionable pass/fail evidence or missing-tool blockers.
    evidence:
      - cortex_m0lite/lint/lint_report.json
      - cortex_m0lite/reports/syn/syn_report.json
      - cortex_m0lite/reports/sta/sta_report.json
      - cortex_m0lite/reports/pnr/pnr_report.json
  signoff:
    pass: Goal audit shows SSOT, model, RTL, lint, simulation, coverage, and EDA gates have evidence.
    evidence:
      - cortex_m0lite/reports/goal_audit.json

traceability:
  requirements:
    - cortex_m0lite/req/requirements.md
  llm_stage: ssot-gen
  yaml_to_output:
    - yaml: io_list
      output: rtl/cortex_m0lite.sv port list and cocotb driver
    - yaml: function_model
      output: model/functional_model.py and scoreboard expected values
    - yaml: cycle_model
      output: model/cycle_model.py and cycle coverage plan
    - yaml: fsm
      output: SSOT design review FSM transition diagram
    - yaml: test_requirements
      output: tb/cocotb/test_timer.py and coverage bins

workflow_todos:
  rtl-gen:
    - id: RTL_TIMER_CONTROL
      content: Implement cortex_m0lite control priority from the SSOT.
      detail: flush must override pcdown progress, fetch_en must load instr_data, step_en must decrement only while busy, and retire must pulse on the terminal tick.
      criteria:
        - flush returns pc, busy, and retire to zero.
        - fetch_en loads instr_data through the XLEN parameterized datapath.
        - step_en decrements pc only while busy is true.
        - retire pulses on pc==1 with step_en and busy asserted.
      source_refs:
        - function_model.transactions.FM_TICK
        - cycle_model.handshake_rules.step_end_tick
        - fsm.control.transitions
      owner_module: timer_core
      owner_file: rtl/cortex_m0lite.sv
      priority: high
      required: true
    - id: RTL_TIMER_OBSERVABILITY
      content: Preserve waveform-observable cortex_m0lite state.
      detail: Expose pc, busy, and retire exactly as declared in debug_observability so sim_debug can correlate source, hierarchy, waveform, and scoreboard events.
      criteria:
        - pc is driven from the cortex_m0lite state register.
        - busy is driven from the cortex_m0lite state register.
        - retire is a visible pulse output.
        - waveform probes include every debug_observability.waveform_must_probe signal.
      source_refs:
        - debug_observability.waveform_must_probe
        - io_list.interfaces.timer_ctrl
        - test_requirements.scenarios.SC_COUNTDOWN_DONE
      owner_module: timer_core
      owner_file: rtl/cortex_m0lite.sv
      priority: medium
      required: true
    - id: RTL_TIMER_PARAMETERIZATION
      content: Keep cortex_m0lite input and output widths user-editable.
      detail: Use XLEN for instr_data and pc so the cortex_m0lite can be resized by changing the SSOT parameter.
      criteria:
        - XLEN parameter controls instr_data width.
        - XLEN parameter controls pc width.
        - No hard-coded pc datapath width is used outside the parameter declaration.
      source_refs:
        - parameters.XLEN
        - io_list.interfaces.timer_ctrl.ports.instr_data
        - coding_rules.port_declaration_default
      owner_module: timer_core
      owner_file: rtl/cortex_m0lite.sv
      priority: medium
      required: true
  tb-gen:
    - id: TB_TIMER_SCENARIOS
      content: Generate reset, flush, pcdown, and hold tests.
      detail: The cocotb test list must mirror test_requirements.scenarios.
      criteria:
        - SC_RESET_CLEAR is implemented.
        - SC_COUNTDOWN_DONE is implemented.
        - SC_ENABLE_HOLD is implemented.
      source_refs:
        - test_requirements.scenarios
  sim_debug:
    - id: DEBUG_TIMER_WAVES
      content: Correlate cortex_m0lite waveform, source, and scoreboard events.
      detail: Sim debug should show pc, busy, retire, fetch_en, step_en, flush, and instr_data in the first debug view.
      criteria:
        - waveform includes all debug_observability.waveform_must_probe entries.
        - source view opens rtl/cortex_m0lite.sv.
        - hierarchy contains cortex_m0lite.
      source_refs:
        - debug_observability

generation_flow:
  steps:
    - name: validate_ssot
      command: bash workflow/ssot-gen/scripts/check_ssot_disk.sh cortex_m0lite
      description: Validate the cortex_m0lite SSOT structure on disk.
    - name: generate_fl_model
      command: /ssot-fl-model cortex_m0lite
      description: Generate FunctionalModel and coverage seeds from the SSOT.
    - name: generate_cycle_model
      command: /ssot-cycle-model cortex_m0lite
      description: Generate the PyMTL cycle model shell and cycle checker evidence.
    - name: generate_coverage
      command: /ssot-dual-fcov cortex_m0lite
      description: Split function and cycle coverage plans.
    - name: generate_equivalence
      command: /ssot-equiv-goals cortex_m0lite
      description: Create FL/RTL equivalence goals.
    - name: generate_rtl
      command: /ssot-rtl cortex_m0lite
      description: Generate or validate RTL from SSOT-derived RTL TODOs.
    - name: run_lint
      command: /lint cortex_m0lite
      description: Produce lint report evidence.


Base rtl-gen contract:
Prepare rtl-gen for cortex_m0lite using only cortex_m0lite/yaml/cortex_m0lite.ssot.yaml and cortex_m0lite/rtl/rtl_todo_plan.json, cortex_m0lite/rtl/rtl_authoring_plan.json, and packets under cortex_m0lite/rtl/authoring_packets. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=2c8b63440d960beba0c10f8b1f5686e14fe23432d04cff8c3991c1a1f1fbe10f. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

Authoring plan overview:
{
  "execution_policy": {
    "allowed_draft_work": [
      "Author module RTL from SSOT-derived TODO packets.",
      "Add tests, vectors, assertions, reports, and repair RTL under LLM-editable surfaces.",
      "Leave unresolved locked-truth decisions as human_gate/change-request records instead of changing SSOT authority."
    ],
    "blocked_by_llm_work": [
      {
        "gate_kind": "static_rtl_evidence",
        "owner_module": "timer_core",
        "reason": "28 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "timer_core",
        "reason": "1 owner logic structure issue(s) remain. timer_core: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "rtl_placeholder_free_evidence",
        "owner_module": "timer_core",
        "reason": "1 RTL placeholder/policy issue(s) remain. None:None: None (No listed RTL source files were readable, so placeholder-free evidence cannot be checked)",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "status": "open",
        "task_id": "RTL-0009"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "timer_core",
        "reason": "1 top IO contract issue(s) remain. cortex_m0lite: SSOT top module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "top_output_drive_evidence",
        "owner_module": "timer_core",
        "reason": "1 top output drive issue(s) remain. cortex_m0lite: SSOT top module is not declared, so output drive evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
        "status": "open",
        "task_id": "RTL-0011"
      },
      {
        "gate_kind": "top_input_consumption_evidence",
        "owner_module": "timer_core",
        "reason": "1 top input consumption issue(s) remain. cortex_m0lite: SSOT top module is not declared, so input consumption evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
        "status": "open",
        "task_id": "RTL-0012"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "timer_core",
        "reason": "1 manifest hierarchy integration issue(s) remain. cortex_m0lite: SSOT top module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      }
    ],
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "timer_core",
        "reason": "Missing common_ai_agent RTL authoring provenance.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "timer_core",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "timer_core",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "timer_core",
        "reason": "96 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {
      "path": "rtl/connection_contract_suggestions.json",
      "rule": "Suggestions are emitted only when production connection contracts are missing.",
      "sample_rows": [],
      "summary": {
        "applied_to_ssot": false,
        "pending_review": 0,
        "status": "not_required",
        "suggested_rows": 0
      }
    },
    "deferred_human_qa_allowed": true,
    "draft_allowed": true,
    "gate_status": "fail",
    "hard_blockers": [],
    "open_required_todos": 97,
    "pass_allowed": false,
    "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
    "stop_conditions": [
      "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
      "Do not claim rtl-gen PASS while pass_allowed is false.",
      "Do not sign off top integration while required connection contracts are missing."
    ],
    "tool_evidence_plan": [
      {
        "artifact": "rtl/rtl_authoring_provenance.json",
        "artifacts": [
          "cortex_m0lite/rtl/rtl_authoring_provenance.json",
          "cortex_m0lite/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip cortex_m0lite --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "common_ai_agent_authoring",
        "prerequisites": [
          "An LLM authoring pass emitted or repaired DUT RTL files."
        ],
        "reason": "Missing common_ai_agent RTL authoring provenance.",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "stage_sequence": [
          "ssot-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "artifact": "rtl/rtl_compile.json",
        "artifacts": [
          "cortex_m0lite/rtl/rtl_compile.json",
          "cortex_m0lite/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py cortex_m0lite --top cortex_m0lite --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "cortex_m0lite/list/cortex_m0lite.f covers the current DUT RTL sources."
        ],
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "stage_sequence": [
          "ssot-rtl",
          "dut_compile"
        ],
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "artifact": "lint/dut_lint.json",
        "artifacts": [
          "cortex_m0lite/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py cortex_m0lite --top cortex_m0lite",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "cortex_m0lite/list/cortex_m0lite.f covers the current DUT RTL/header sources."
        ],
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "stage_sequence": [
          "lint",
          "dut_lint"
        ],
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "artifact": "rtl/rtl_todo_plan.json",
        "artifacts": [
          "cortex_m0lite/rtl/rtl_todo_plan.json",
          "cortex_m0lite/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "96 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ]
  },
  "ip": "cortex_m0lite",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__function_model.json",
      "kind": "module",
      "llm_actionable_open_count": 23,
      "open_required_count": 23,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__function_model",
      "required_count": 23,
      "status_counts": {
        "open": 23
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 12,
      "open_required_count": 12,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__cycle_model",
      "required_count": 12,
      "status_counts": {
        "open": 12
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 9,
      "open_required_count": 9,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__io_list",
      "required_count": 9,
      "status_counts": {
        "open": 9
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 8,
      "open_required_count": 8,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__fsm",
      "required_count": 8,
      "status_counts": {
        "open": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__dataflow.json",
      "kind": "module",
      "llm_actionable_open_count": 7,
      "open_required_count": 7,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__dataflow",
      "required_count": 7,
      "status_counts": {
        "open": 7
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__coverage.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__coverage",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__features.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__features",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__integration.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__integration",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__registers.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__registers",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__synthesis.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__synthesis",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__test_requirements",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__workflow_todo",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__error_handling",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__equivalence",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__parameters",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__rtl_flow.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__rtl_flow",
      "required_count": 2,
      "status_counts": {
        "open": 1,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__security.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__security",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 7,
      "open_required_count": 7,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 9,
      "status_counts": {
        "open": 7,
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 4,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 4,
      "status_counts": {
        "pass": 4
      }
    }
  ],
  "policy": {
    "dynamic_task_rule": "Use every required task in this file as the authoritative RTL implementation/evidence ledger. Expose Atlas/UI TodoTracker items as grouped section/work-type tasks, targeting roughly 20-30 active TODOs for complex IPs, with the detailed ledger items preserved as criteria instead of one UI TODO per ledger row.",
    "fixed_template_role": "seed_only",
    "no_orphan_function_level": true,
    "reference_profile_rule": "Optional rtl_reference_profile artifacts are calibration-only scale reports; they must not be copied, transformed, or used as fixed RTL templates.",
    "rtl_gate_todo_rule": "RTL-gen quality gates are first-class rtl_gate.rtl_gen TODOs; compile/lint/static/ownership/owner-logic/placeholder-free/implementation-depth/top-io/top-output-drive/top-input-consumption/hierarchy/port-connection/signal-flow/connection-contract gates must close as TODOs before PASS.",
    "rtl_quality_profile": "standard",
    "rtl_target_scale": {},
    "rtl_target_scale_waiver": {},
    "single_source_of_truth": "SSOT YAML is the only authority for function_model, cycle_model, RTL ownership, DV plan, and coverage.",
    "ssot_workflow_todo_rule": "workflow_todos.rtl-gen[] entries are first-class downstream tasks; content/detail/criteria must be preserved and satisfied by RTL evidence.",
    "target_scale_rule": "Optional quality_gates.rtl_gen.target_scale is SSOT-locked human policy. It can be calibrated from a reference profile, but it is enforced as generic structural depth evidence, not as copied reference RTL."
  },
  "reference_profile": {},
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 0,
    "human_locked_tasks": 0,
    "llm_actionable_packets": 18,
    "llm_actionable_tasks": 93,
    "max_packet_required_tasks": 23,
    "module_packets": 17,
    "next_llm_packets": [
      "module__timer_core__function_model",
      "module__timer_core__cycle_model",
      "module__timer_core__io_list",
      "module__timer_core__fsm",
      "module__timer_core__dataflow",
      "module__timer_core__coverage",
      "module__timer_core__features",
      "module__timer_core__integration"
    ],
    "packet_task_limit": 48,
    "packets": 20,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 104,
    "sliced_module_packets": 17,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 4,
    "total_tasks": 104,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "2c8b63440d960beba0c10f8b1f5686e14fe23432d04cff8c3991c1a1f1fbe10f",
  "top": "cortex_m0lite",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/cortex_m0lite.sv):
module cortex_m0lite #(
    parameter integer XLEN = 16
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             fetch_en,
    input  logic             step_en,
    input  logic             flush,
    input  logic [XLEN-1:0]  instr_data,
    output logic [XLEN-1:0]  pc,
    output logic             busy,
    output logic             retire
);

    // timer_core architectural state from function_model/state_updates.
    logic [XLEN-1:0] pc_q;
    logic            busy_q;
    logic            retire_q;

    // S0_CONTROL_SAMPLE: accept a control sample when any contract trigger is high.
    // No ready/valid backpressure is used; step_en controls progress directly.
    logic            accept_txn;

    // Next-state wires implement the SSOT output_rules/state_updates exactly.
    logic [XLEN-1:0] pc_next;
    logic            busy_next;
    logic            retire_next;

    // sample_condition from rtl_contract: fetch_en or flush or step_en or retire_q.
    assign accept_txn = fetch_en | flush | step_en | retire_q;

    // ordering_rule_0 + flush_priority: flush has highest priority over all tick behavior.
    // ordering_rule_1 + fetch_en_load: fetch_en load is applied before step_end_tick behavior.
    // step_end_tick decrement only occurs while busy and pc_q > 0.
    assign pc_next = flush ? {XLEN{1'b0}} :
                     (fetch_en ? instr_data :
                     ((step_en && busy_q && (pc_q > {XLEN{1'b0}})) ?
                     (pc_q - {{(XLEN-1){1'b0}}, 1'b1}) : pc_q));

    // busy drops on terminal step_end_tick when current pc_q <= 1.
    assign busy_next = flush ? 1'b0 :
                       (fetch_en ? (instr_data > {XLEN{1'b0}}) :
                       ((step_en && busy_q && (pc_q <= {{(XLEN-1){1'b0}}, 1'b1})) ? 1'b0 : busy_q));

    // ordering_rule_2: retire is observed on the same S1_STATE_VISIBLE cycle
    // as the terminal decrement (pc_q == 1 with step_en && busy_q).
    assign retire_next = flush ? 1'b0 :
                         (fetch_en ? 1'b0 :
                         ((step_en && busy_q && (pc_q == {{(XLEN-1){1'b0}}, 1'b1})) ? 1'b1 : 1'b0));

    // cycle_model.clock=clk, cycle_model.reset=rst_n(active low), cycle_model.latency=1:
    // update state in this accepting edge so outputs are visible after one edge.
    // This is S1_STATE_VISIBLE for the sampled S0_CONTROL_SAMPLE transaction.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_q     <= {XLEN{1'b0}};
            busy_q   <= 1'b0;
            retire_q <= 1'b0;
        end else if (accept_txn) begin
            pc_q     <= pc_next;
            busy_q   <= busy_next;
            retire_q <= retire_next;
        end
    end

    // Observable outputs are direct architectural-state views for waveform/debug checks.
    assign pc     = pc_q;
    assign busy   = busy_q;
    assign retire = retire_q;

endmodule


Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__timer_core__fsm.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 17,
      "enabled": true,
      "index": 7,
      "key": "fsm",
      "module_task_count": 87,
      "rule": "Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "fsm",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/cortex_m0lite.sv",
      "name": "timer_core",
      "refs": [
        "cycle_model",
        "fsm",
        "function_model",
        "function_model.transactions.FM_TICK",
        "io_list",
        "parameters",
        "rtl_contract"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/cortex_m0lite.sv",
        "name": "timer_core",
        "wiring_only": false
      }
    ],
    "quality_profile": "standard",
    "reference_profile": null,
    "ssot_connection_contracts": [],
    "ssot_top_io_contracts": [],
    "target_scale": null
  },
  "execution_policy": {
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [],
    "contract_blocked_open_count": 0,
    "deferred_human_qa_allowed": true,
    "draft_allowed": true,
    "evidence_closure_allowed": false,
    "human_locked_open_count": 0,
    "integration_signoff_allowed": true,
    "llm_actionable": true,
    "llm_actionable_open_count": 8,
    "open_required_count": 8,
    "pass_allowed": false,
    "stop_conditions": [
      "Close this packet only after every required task in the packet has pass status.",
      "Return human_gate/change-request JSON when locked truth is missing instead of inventing semantics.",
      "Never use a fixed RTL template as the implementation."
    ],
    "tool_evidence_open_count": 0,
    "tool_evidence_plan": [],
    "work_allowed": true
  },
  "ip": "cortex_m0lite",
  "kind": "module",
  "owner_file": "rtl/cortex_m0lite.sv",
  "owner_module": "timer_core",
  "packet_id": "module__timer_core__fsm",
  "rules": [
    "No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.",
    "Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.",
    "Every task must satisfy content, detail, and criteria before the packet is closed.",
    "For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.",
    "Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json."
  ],
  "schema_version": 1,
  "source_plan": "rtl/rtl_todo_plan.json",
  "summary": {
    "categories": {
      "fsm.state": 3,
      "fsm.transition": 5
    },
    "module_slice": {
      "count": 17,
      "enabled": true,
      "index": 7,
      "key": "fsm",
      "module_task_count": 87,
      "rule": "Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "fsm",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 8,
    "required_count": 8,
    "source_refs": [
      "fsm.control.states.IDLE",
      "fsm.control.states.RUN",
      "fsm.control.states.DONE_PULSE",
      "fsm.control.transitions.transition_0",
      "fsm.control.transitions.transition_1",
      "fsm.control.transitions.transition_2",
      "fsm.control.transitions.transition_3",
      "fsm.control.transitions.transition_4"
    ],
    "status_counts": {
      "open": 8
    },
    "task_count": 8
  },
  "tasks": [
    {
      "category": "fsm.state",
      "content": "Implement FSM state control.IDLE",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.control.states.IDLE",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.states.IDLE.\nOwner: timer_core in rtl/cortex_m0lite.sv via fsm.\nSSOT item context: name=IDLE.",
      "evidence_terms": [],
      "id": "RTL-0071",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.states.IDLE",
      "ssot_context": {
        "name": "IDLE"
      },
      "ssot_refs": [
        "fsm.control.states.IDLE"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.state",
      "content": "Implement FSM state control.RUN",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.control.states.RUN",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.states.RUN.\nOwner: timer_core in rtl/cortex_m0lite.sv via fsm.\nSSOT item context: name=RUN.",
      "evidence_terms": [],
      "id": "RTL-0072",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.states.RUN",
      "ssot_context": {
        "name": "RUN"
      },
      "ssot_refs": [
        "fsm.control.states.RUN"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.state",
      "content": "Implement FSM state control.DONE_PULSE",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.control.states.DONE_PULSE",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.states.DONE_PULSE.\nOwner: timer_core in rtl/cortex_m0lite.sv via fsm.\nSSOT item context: name=DONE_PULSE.",
      "evidence_terms": [],
      "id": "RTL-0073",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.states.DONE_PULSE",
      "ssot_context": {
        "name": "DONE_PULSE"
      },
      "ssot_refs": [
        "fsm.control.states.DONE_PULSE"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_0",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_0",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv",
        "fsm.control.transitions.transition_0 condition is implemented as RTL control logic: fetch_en and instr_data != 0",
        "fsm.control.transitions.transition_0 transition path IDLE -> RUN is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_0.\nOwner: timer_core in rtl/cortex_m0lite.sv via fsm.\nSSOT item context: from=IDLE; to=RUN; condition=fetch_en and instr_data != 0.",
      "evidence_terms": [
        "IDLE",
        "RUN",
        "data",
        "en",
        "fetch",
        "fetch_en",
        "instr",
        "instr_data"
      ],
      "id": "RTL-0074",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_0",
      "ssot_context": {
        "condition": "fetch_en and instr_data != 0",
        "from": "IDLE",
        "to": "RUN"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "IDLE",
          "RUN",
          "data",
          "en",
          "fetch",
          "fetch_en",
          "instr",
          "instr_data"
        ],
        "source_scope": "rtl/cortex_m0lite.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_1",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_1",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv",
        "fsm.control.transitions.transition_1 condition is implemented as RTL control logic: step_en and pc > 1",
        "fsm.control.transitions.transition_1 transition path RUN -> RUN is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_1.\nOwner: timer_core in rtl/cortex_m0lite.sv via fsm.\nSSOT item context: from=RUN; to=RUN; condition=step_en and pc > 1.",
      "evidence_terms": [
        "RUN",
        "en",
        "step",
        "step_en"
      ],
      "id": "RTL-0075",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_1",
      "ssot_context": {
        "condition": "step_en and pc > 1",
        "from": "RUN",
        "to": "RUN"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "RUN",
          "en",
          "step",
          "step_en"
        ],
        "source_scope": "rtl/cortex_m0lite.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_2",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_2",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv",
        "fsm.control.transitions.transition_2 condition is implemented as RTL control logic: step_en and pc == 1",
        "fsm.control.transitions.transition_2 transition path RUN -> DONE_PULSE is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_2.\nOwner: timer_core in rtl/cortex_m0lite.sv via fsm.\nSSOT item context: from=RUN; to=DONE_PULSE; condition=step_en and pc == 1.",
      "evidence_terms": [
        "DONE_PULSE",
        "RUN",
        "en",
        "step",
        "step_en"
      ],
      "id": "RTL-0076",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_2",
      "ssot_context": {
        "condition": "step_en and pc == 1",
        "from": "RUN",
        "to": "DONE_PULSE"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_2"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "DONE_PULSE",
          "RUN",
          "en",
          "step",
          "step_en"
        ],
        "source_scope": "rtl/cortex_m0lite.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_3",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_3",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv",
        "fsm.control.transitions.transition_3 condition is implemented as RTL control logic: next control cycle without fetch_en",
        "fsm.control.transitions.transition_3 transition path DONE_PULSE -> IDLE is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_3.\nOwner: timer_core in rtl/cortex_m0lite.sv via fsm.\nSSOT item context: from=DONE_PULSE; to=IDLE; condition=next control cycle without fetch_en.",
      "evidence_terms": [
        "DONE_PULSE",
        "IDLE",
        "en",
        "fetch",
        "fetch_en"
      ],
      "id": "RTL-0077",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_3",
      "ssot_context": {
        "condition": "next control cycle without fetch_en",
        "from": "DONE_PULSE",
        "to": "IDLE"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_3"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "DONE_PULSE",
          "IDLE",
          "en",
          "fetch",
          "fetch_en"
        ],
        "source_scope": "rtl/cortex_m0lite.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_4",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_4",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv",
        "fsm.control.transitions.transition_4 condition is implemented as RTL control logic: flush",
        "fsm.control.transitions.transition_4 transition path RUN -> IDLE is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_4.\nOwner: timer_core in rtl/cortex_m0lite.sv via fsm.\nSSOT item context: from=RUN; to=IDLE; condition=flush.",
      "evidence_terms": [
        "IDLE",
        "RUN"
      ],
      "id": "RTL-0078",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_4",
      "ssot_context": {
        "condition": "flush",
        "from": "RUN",
        "to": "IDLE"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_4"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "IDLE",
          "RUN"
        ],
        "source_scope": "rtl/cortex_m0lite.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite.sv.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "2c8b63440d960beba0c10f8b1f5686e14fe23432d04cff8c3991c1a1f1fbe10f",
  "top": "cortex_m0lite",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__timer_core__fsm.md):
# RTL Authoring Packet: module__timer_core__fsm

- Kind: module
- Owner module: timer_core
- Owner file: rtl/cortex_m0lite.sv
- Task count: 8
- Required tasks: 8

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 8
- Human-locked open tasks: 0
- Owner refs: cycle_model, fsm, function_model, function_model.transactions.FM_TICK, io_list, parameters, rtl_contract
- Module slice: 7/17 section=fsm task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0071: Implement FSM state control.IDLE

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.IDLE
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.IDLE.
Owner: timer_core in rtl/cortex_m0lite.sv via fsm.
SSOT item context: name=IDLE.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.IDLE
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: fsm.control.states.IDLE

### RTL-0072: Implement FSM state control.RUN

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.RUN
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.RUN.
Owner: timer_core in rtl/cortex_m0lite.sv via fsm.
SSOT item context: name=RUN.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.RUN
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: fsm.control.states.RUN

### RTL-0073: Implement FSM state control.DONE_PULSE

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.DONE_PULSE
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.DONE_PULSE.
Owner: timer_core in rtl/cortex_m0lite.sv via fsm.
SSOT item context: name=DONE_PULSE.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.DONE_PULSE
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: fsm.control.states.DONE_PULSE

### RTL-0074: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: timer_core in rtl/cortex_m0lite.sv via fsm.
SSOT item context: from=IDLE; to=RUN; condition=fetch_en and instr_data != 0.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - fsm.control.transitions.transition_0 condition is implemented as RTL control logic: fetch_en and instr_data != 0
  - fsm.control.transitions.transition_0 transition path IDLE -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0075: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: timer_core in rtl/cortex_m0lite.sv via fsm.
SSOT item context: from=RUN; to=RUN; condition=step_en and pc > 1.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - fsm.control.transitions.transition_1 condition is implemented as RTL control logic: step_en and pc > 1
  - fsm.control.transitions.transition_1 transition path RUN -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0076: Implement FSM transition control.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_2.
Owner: timer_core in rtl/cortex_m0lite.sv via fsm.
SSOT item context: from=RUN; to=DONE_PULSE; condition=step_en and pc == 1.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_2
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - fsm.control.transitions.transition_2 condition is implemented as RTL control logic: step_en and pc == 1
  - fsm.control.transitions.transition_2 transition path RUN -> DONE_PULSE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_2

### RTL-0077: Implement FSM transition control.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_3.
Owner: timer_core in rtl/cortex_m0lite.sv via fsm.
SSOT item context: from=DONE_PULSE; to=IDLE; condition=next control cycle without fetch_en.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_3
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - fsm.control.transitions.transition_3 condition is implemented as RTL control logic: next control cycle without fetch_en
  - fsm.control.transitions.transition_3 transition path DONE_PULSE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_3

### RTL-0078: Implement FSM transition control.transition_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_4.
Owner: timer_core in rtl/cortex_m0lite.sv via fsm.
SSOT item context: from=RUN; to=IDLE; condition=flush.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_4
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
  - fsm.control.transitions.transition_4 condition is implemented as RTL control logic: flush
  - fsm.control.transitions.transition_4 transition path RUN -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_4
