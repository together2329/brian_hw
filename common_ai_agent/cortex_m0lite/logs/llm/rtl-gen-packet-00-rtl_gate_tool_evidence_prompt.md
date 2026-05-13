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

Current packet: rtl_gate_tool_evidence
kind: gate
work queue: 1/1 active packets (19 closed packets skipped from 20 total)
batch limit: 1; deferred active packets after this batch: 0
owner_module: cortex_m0lite
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
    "blocked_by_llm_work": [],
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "dut_lint",
        "owner_module": "timer_core",
        "reason": "DUT lint artifact is not clean.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "timer_core",
        "reason": "1 required non-closure TODO(s) remain open.",
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
    "open_required_todos": 2,
    "pass_allowed": false,
    "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
    "stop_conditions": [
      "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
      "Do not claim rtl-gen PASS while pass_allowed is false.",
      "Do not sign off top integration while required connection contracts are missing."
    ],
    "tool_evidence_plan": [
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
        "reason": "DUT lint artifact is not clean.",
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
        "reason": "1 required non-closure TODO(s) remain open.",
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
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 2,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 2,
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__coverage.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__coverage",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__cycle_model",
      "required_count": 12,
      "status_counts": {
        "pass": 12
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__dataflow.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__dataflow",
      "required_count": 7,
      "status_counts": {
        "pass": 7
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__error_handling",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__features.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__features",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__fsm",
      "required_count": 8,
      "status_counts": {
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__function_model.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__function_model",
      "required_count": 23,
      "status_counts": {
        "pass": 23
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__integration.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__integration",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__io_list",
      "required_count": 9,
      "status_counts": {
        "pass": 9
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__parameters",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__registers.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__registers",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__rtl_flow.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__rtl_flow",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__security.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__security",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__synthesis.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__synthesis",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__test_requirements",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__workflow_todo",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 9,
      "status_counts": {
        "pass": 9
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
    "llm_actionable_packets": 0,
    "llm_actionable_tasks": 0,
    "max_packet_required_tasks": 23,
    "module_packets": 17,
    "next_llm_packets": [],
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
    "tool_evidence_tasks": 2,
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

    // Explicit FSM encoding from SSOT fsm.control.states.
    localparam [1:0] IDLE       = 2'd0;
    localparam [1:0] RUN        = 2'd1;
    localparam [1:0] DONE_PULSE = 2'd2;

    // timer_core architectural state from function_model/state_updates.
    logic [XLEN-1:0] pc_q;
    logic            busy_q;
    logic            retire_q;

    // FSM state tracks IDLE/RUN/DONE_PULSE observability and transition intent.
    logic [1:0]      state_q;
    logic [1:0]      state_next;

    // S0_CONTROL_SAMPLE acceptance qualifier from rtl_contract.sample_condition.
    logic            accept_txn;
    logic            s0_control_sample_fire;

    // S1_STATE_VISIBLE marker: with latency=1, new state is VISIBLE right after
    // the same accepting clock edge that updates pc_q/busy_q/retire_q.
    logic            s1_state_visible_fire;

    // Next-state wires implement SSOT output_rules/state_updates exactly.
    logic [XLEN-1:0] pc_next;
    logic            busy_next;
    logic            retire_next;

    // sample_condition from rtl_contract: fetch_en or flush or step_en or retire_q.
    assign accept_txn             = fetch_en | flush | step_en | retire_q;
    assign s0_control_sample_fire = accept_txn;

    // S1_STATE_VISIBLE occurs one cycle after S0 sampling for latency=1 observable behavior.
    assign s1_state_visible_fire  = s0_control_sample_fire;

    // ordering_rule_0 + flush_priority: flush has highest priority over all tick behavior.
    // ordering_rule_1 + fetch_en_load: fetch_en load is applied before step_en tick behavior.
    // step_en decrement occurs only while busy and pc_q > 0 (prevents underflow).
    assign pc_next = flush ? {XLEN{1'b0}} :
                     (fetch_en ? instr_data :
                     ((step_en && busy_q && (pc_q > {XLEN{1'b0}})) ?
                     (pc_q - {{(XLEN-1){1'b0}}, 1'b1}) : pc_q));

    // busy drops on terminal step tick when current pc_q <= 1.
    assign busy_next = flush ? 1'b0 :
                       (fetch_en ? (instr_data > {XLEN{1'b0}}) :
                       ((step_en && busy_q && (pc_q <= {{(XLEN-1){1'b0}}, 1'b1})) ? 1'b0 : busy_q));

    // retire is visible on the terminal decrement cycle (pc_q == 1 with step_en && busy_q).
    assign retire_next = flush ? 1'b0 :
                         (fetch_en ? 1'b0 :
                         ((step_en && busy_q && (pc_q == {{(XLEN-1){1'b0}}, 1'b1})) ? 1'b1 : 1'b0));

    // fsm.control.transitions implementation:
    // transition_0: IDLE -> RUN when fetch_en && instr_data != 0
    // transition_1: RUN -> RUN when step_en && pc > 1
    // transition_2: RUN -> DONE_PULSE when step_en && pc == 1
    // transition_3: DONE_PULSE -> IDLE on next control cycle without fetch_en
    // transition_4: RUN -> IDLE when flush
    always @(*) begin
        state_next = state_q;
        case (state_q)
            IDLE: begin
                if (flush) begin
                    state_next = IDLE;
                end else if (fetch_en && (instr_data != {XLEN{1'b0}})) begin
                    state_next = RUN;
                end else begin
                    state_next = IDLE;
                end
            end

            RUN: begin
                if (flush) begin
                    state_next = IDLE;
                end else if (step_en && busy_q && (pc_q == {{(XLEN-1){1'b0}}, 1'b1})) begin
                    state_next = DONE_PULSE;
                end else begin
                    state_next = RUN;
                end
            end

            DONE_PULSE: begin
                // A fresh fetch_en starts the next interval immediately.
                if (flush) begin
                    state_next = IDLE;
                end else if (fetch_en && (instr_data != {XLEN{1'b0}})) begin
                    state_next = RUN;
                end else begin
                    state_next = IDLE;
                end
            end

            default: begin
                state_next = IDLE;
            end
        endcase
    end

    // cycle_model.clock=clk, cycle_model.reset=rst_n(active low), cycle_model.latency=1.
    // S0_CONTROL_SAMPLE (cycle 0): controls are sampled when s0_control_sample_fire is high.
    // S1_STATE_VISIBLE (cycle 1): updated pc/busy/retire become VISIBLE after this same edge.
    // No extra input staging is used, so this remains latency=1 rather than latency=2.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_q     <= {XLEN{1'b0}};
            busy_q   <= 1'b0;
            retire_q <= 1'b0;
            state_q  <= IDLE;
        end else if (s0_control_sample_fire) begin
            pc_q     <= pc_next;
            busy_q   <= busy_next;
            retire_q <= retire_next;
            state_q  <= state_next;
        end
    end

    // S1_STATE_VISIBLE: outputs are the visible architectural state after latency-1 update.
    // s1_state_visible_fire is an explicit marker for cycle-model stage traceability.
    assign pc     = pc_q;
    assign busy   = busy_q;
    assign retire = retire_q;

endmodule

Current tool evidence artifacts referenced by this packet:
### cortex_m0lite/lint/dut_lint.json
{
  "schema_version": 1,
  "type": "dut_lint",
  "scope": "dut",
  "dut_only": true,
  "tool": "pyslang+verilator",
  "command": "pyslang rtl/cortex_m0lite.sv && verilator --lint-only -Wall -Irtl -f list/cortex_m0lite.f --top-module cortex_m0lite",
  "cwd": "cortex_m0lite",
  "top": "cortex_m0lite",
  "filelist": "cortex_m0lite/list/cortex_m0lite.f",
  "rtl_files": [
    "rtl/cortex_m0lite.sv"
  ],
  "timestamp": "2026-05-13T15:59:28.446636+00:00",
  "returncode": 1,
  "errors": 0,
  "warnings": 2,
  "waived_warnings": 0,
  "tool_results": [
    {
      "tool": "pyslang",
      "available": true,
      "command": "pyslang rtl/cortex_m0lite.sv",
      "returncode": 0,
      "errors": 0,
      "warnings": 0,
      "diagnostics": [],
      "passed": true
    },
    {
      "tool": "verilator",
      "available": true,
      "command": "verilator --lint-only -Wall -Irtl -f list/cortex_m0lite.f --top-module cortex_m0lite",
      "returncode": 1,
      "errors": 0,
      "warnings": 2,
      "diagnostics": [
        {
          "severity": "warning",
          "rule": "EOFNEWLINE",
          "file": "rtl/cortex_m0lite.sv",
          "line": 137,
          "column": 10,
          "message": "Missing newline at end of file (POSIX 3.206).",
          "source": "endmodule"
        },
        {
          "severity": "warning",
          "rule": "UNUSEDSIGNAL",
          "file": "rtl/cortex_m0lite.sv",
          "line": 35,
          "column": 22,
          "message": "Signal is not used: 's1_state_visible_fire'",
          "source": "    logic            s1_state_visible_fire;"
        }
      ],
      "passed": false
    }
  ],
  "suppression_violation_count": 0,
  "suppression_violations": [],
  "style_violation_count": 0,
  "style_violations": [],
  "policy": "DUT RTL must be lint-clean without ad-hoc verilator lint_off/lint_on or -Wno suppressions, and generated RTL must keep .sv filenames while using the project SystemVerilog subset: input logic/output logic ports and internal logic are allowed; package/import/interface/modport/function/task/for/while/typedef/enum/always_ff/always_comb remain forbidden.",
  "passed": false
}


### cortex_m0lite/rtl/rtl_todo_plan.json
{
  "blockers": [],
  "connection_contract_suggestions": {
    "rows": [],
    "rule": "Suggestions are emitted only when production connection contracts are missing.",
    "schema_version": 1,
    "summary": {
      "applied_to_ssot": false,
      "pending_review": 0,
      "status": "not_required",
      "suggested_rows": 0
    },
    "type": "rtl_connection_contract_suggestions"
  },
  "gate": {
    "all_required_todos_pass": false,
    "audit_rtl": true,
    "blocking_questions": 0,
    "criteria": [
      "Gate: SSOT function_model and cycle_model are present before RTL generation",
      "Gate: SSOT-authored rtl-gen workflow TODOs are well formed",
      "Gate: every SSOT-derived RTL behavior has an owner module",
      "Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits",
      "Gate: required SSOT behavior has static DUT RTL evidence after audit",
      "Gate: behavior-owner RTL modules contain real implementation structure",
      "Gate: RTL sources contain no placeholder markers or disallowed generated-RTL constructs",
      "Gate: SSOT top IO contracts match the RTL top module",
      "Gate: SSOT top outputs are driven by real RTL logic",
      "Gate: SSOT top inputs are consumed by RTL logic or child inputs",
      "Gate: manifest-owned RTL modules are integrated into the top hierarchy",
      "Gate: manifest-owned child instances have machine-checkable port connections",
      "Gate: manifest child port connections carry live RTL signal flow",
      "Gate: SSOT connection contracts match RTL child port maps",
      "Gate: DUT-only RTL compile report passes after the final RTL edit",
      "Gate: DUT-only lint report passes after the final RTL edit",
      "Gate: every required rtl_todo_plan item is closed before rtl-gen PASS"
    ],
    "open_required_todos": 2,
    "orphan_tasks": 0,
    "static_missing": 0,
    "status": "fail"
  },
  "generated_at": "2026-05-13T16:00:04Z",
  "ip": "cortex_m0lite",
  "manifest_hierarchy_evidence": {
    "connection_contract_count": 0,
    "connection_contract_issues": [],
    "connection_contract_status": "pass",
    "declared_modules": [
      "cortex_m0lite"
    ],
    "graph": {
      "cortex_m0lite": []
    },
    "issues": [],
    "port_connection_issues": [],
    "port_connection_status": "pass",
    "reachable_modules": [
      "cortex_m0lite"
    ],
    "roots": [
      "cortex_m0lite"
    ],
    "sources": [
      "rtl/cortex_m0lite.sv"
    ],
    "status": "pass"
  },
  "manifest_signal_flow_evidence": {
    "checked_inputs": 0,
    "checked_outputs": 0,
    "issues": [],
    "reachable_modules": [
      "cortex_m0lite"
    ],
    "roots": [
      "cortex_m0lite"
    ],
    "status": "pass"
  },
  "orphans": [],
  "owner_logic_evidence": {
    "checked": 1,
    "issues": [],
    "status": "pass"
  },
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
  "reference_profile": null,
  "reference_scale_gap": {},
  "rtl_implementation_depth_evidence": {
    "aggregate": {
      "behavior_owner_logic_modules": 1,
      "control_flow": 9,
      "depth_score": 54,
      "instances": 0,
      "lines": 137,
      "logic_modules": 1,
      "modules": 1,
      "nonconstant_assigns": 9,
      "procedural_blocks": 2,
      "source_files": 1,
      "state_updates": 9,
      "storage_decls": 12
    },
    "issues": [],
    "modules": [
      {
        "depth_score": 54,
        "file": "rtl/cortex_m0lite.sv",
        "metrics": {
          "control_flow": 9,
          "instances": 0,
          "nonconstant_assigns": 9,
          "placeholder_tokens": false,
          "procedural_blocks": 2,
          "state_updates": 9,
          "storage_decls": 12
        },
        "module": "cortex_m0lite"
      }
    ],
    "profile": "standard",
    "reference_comparison": null,
    "status": "pass",
    "target_scale": {},
    "thresholds": {
      "behavior_owners": 1,
      "behavior_tasks": 59,
      "machine_connection_contracts": 0,
      "manifest_rtl_files": 1,
      "min_depth_score": 24,
      "min_logic_modules": 1
    }
  },
  "rtl_placeholder_free_evidence": {
    "checked": 1,
    "issues": [],
    "status": "pass"
  },
  "schema_version": 1,
  "source": "cortex_m0lite/yaml/cortex_m0lite.ssot.yaml",
  "ssot_connection_contracts": [],
  "ssot_top_io_contracts": [
    {
      "aliases": [
        "clk"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "input",
      "name": "clk",
      "source_ref": "io_list.clock_domains[0].ports[0]",
      "width": "1"
    },
    {
      "aliases": [
        "rst_n"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "input",
      "name": "rst_n",
      "source_ref": "io_list.resets[0].ports[0]",
      "width": "1"
    },
    {
      "aliases": [
        "fetch_en",
        "timer_ctrl_fetch_en"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "input",
      "name": "fetch_en",
      "source_ref": "io_list.interfaces[0].ports[0]",
      "width": "1"
    },
    {
      "aliases": [
        "step_en",
        "timer_ctrl_step_en"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "input",
      "name": "step_en",
      "source_ref": "io_list.interfaces[0].ports[1]",
      "width": "1"
    },
    {
      "aliases": [
        "flush",
        "timer_ctrl_flush"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "input",
      "name": "flush",
      "source_ref": "io_list.interfaces[0].ports[2]",
      "width": "1"
    },
    {
      "aliases": [
        "instr_data",
        "timer_ctrl_instr_data"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "input",
      "name": "instr_data",
      "source_ref": "io_list.interfaces[0].ports[3]",
      "width": "XLEN"
    },
    {
      "aliases": [
        "pc",
        "timer_ctrl_pc"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "output",
      "name": "pc",
      "source_ref": "io_list.interfaces[0].ports[4]",
      "width": "XLEN"
    },
    {
      "aliases": [
        "busy",
        "timer_ctrl_busy"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "output",
      "name": "busy",
      "source_ref": "io_list.interfaces[0].ports[5]",
      "width": "1"
    },
    {
      "aliases": [
        "retire",
        "timer_ctrl_retire"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "output",
      "name": "retire",
      "source_ref": "io_list.interfaces[0].ports[6]",
      "width": "1"
    }
  ],
  "static_rtl_evidence": {
    "checked": 28,
    "missing": 0,
    "missing_tasks": [],
    "passed": 28,
    "sources": [
      "rtl/cortex_m0lite.sv"
    ]
  },
  "summary": {
    "blocking_questions": 0,
    "by_category": {
      "coverage.functional_bin": 3,
      "cycle_model.backpressure": 1,
      "cycle_model.clock": 1,
      "cycle_model.handshake_rules": 3,
      "cycle_model.latency": 1,
      "cycle_model.ordering": 3,
      "cycle_model.pipeline": 2,
      "cycle_model.reset": 1,
      "dataflow.ordering": 3,
      "dataflow.sequence": 4,
      "equivalence.module": 1,
      "error_handling.recovery": 2,
      "features.item": 3,
      "fsm.state": 3,
      "fsm.transition": 5,
      "function_model.error_case": 1,
      "function_model.invariant": 4,
      "function_model.output": 3,
      "function_model.output_rule": 3,
      "function_model.precondition": 2,
      "function_model.side_effect": 3,
      "function_model.state_update": 3,
      "function_model.state_variable": 3,
      "function_model.transaction": 1,
      "integration.dependencies": 3,
      "io_list.port": 9,
      "parameters.item": 1,
      "registers.architectural_state": 3,
      "rtl_flow.seed": 1,
      "rtl_flow.top": 1,
      "rtl_gate.rtl_gen": 17,
      "security.assets": 1,
      "synthesis.constraints": 3,
      "test_requirements.scenario": 3,
      "workflow_todo.rtl_gen": 3
    },
    "by_section": {
      "coverage": 3,
      "cycle_model": 12,
      "dataflow": 7,
      "equivalence": 1,
      "error_handling": 2,
      "features": 3,
      "fsm": 8,
      "function_model": 23,
      "integration": 3,
      "io_list": 9,
      "parameters": 1,
      "registers": 3,
      "rtl_flow": 2,
      "rtl_gate": 17,
      "security": 1,
      "synthesis": 3,
      "test_requirements": 3,
      "workflow_todo": 3
    },
    "orphan_tasks": 0,
    "owner_modules": [
      {
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
      }
    ],
    "reference_profile_present": false,
    "required_tasks": 104,
    "rtl_gate_todos": 17,
    "rtl_quality_profile": "standard",
    "ssot_workflow_todos": 3,
    "target_scale_present": false,
    "target_scale_waived": false,
    "total_tasks": 104
  },
  "target_scale": {},
  "target_scale_waiver": {},
  "tasks": [
    {
      "category": "rtl_flow.seed",
      "content": "Read SSOT and build dynamic RTL implementation ledger",
      "criteria": [
        "rtl_todo_plan.json was regenerated from the current SSOT",
        "Every required task in the plan is either implemented, evidenced, or escalated",
        "No IP-specific fixed template is used as the source of truth",
        "Traceability keeps source_ref top_module",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.\nSSOT ref: top_module.\nOwner: timer_core in rtl/cortex_m0lite.sv via single_owner.",
      "evidence_terms": [],
      "id": "RTL-0001",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_match": "single_owner",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "requires_static_rtl_evidence": false,
      "source_ref": "top_module",
      "ssot_context": {},
      "ssot_refs": [
        "top_module"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_flow.top",
      "content": "Implement top-level ports, reset, and filelist integration",
      "criteria": [
        "Top module name matches SSOT top_module",
        "Every SSOT top-level port appears with matching direction and width",
        "Filelist contains all LLM-authored RTL sources and no stale sources",
        "Traceability keeps source_ref io_list",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.\nSSOT ref: io_list.\nOwner: timer_core in rtl/cortex_m0lite.sv via single_owner.\nSSOT item context: value=cortex_m0lite.",
      "evidence_terms": [
        "cortex",
        "cortex_m0lite",
        "m0lite"
      ],
      "id": "RTL-0002",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_match": "single_owner",
      "owner_module": "timer_core",
      "priority": "high",
      "required": true,
      "requires_static_rtl_evidence": false,
      "source_ref": "io_list",
      "ssot_context": {
        "value": "cortex_m0lite"
      },
      "ssot_refs": [
        "io_list"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT function_model and cycle_model are present before RTL generation",
      "criteria": [
        "function_model is present and non-empty in the SSOT",
        "cycle_model is present and non-empty in the SSOT",
        "Missing authority artifacts open a human/ssot-gen gate instead of being bypassed in RTL",
        "Traceability keeps source_ref quality_gates.rtl_gen.ssot_required_sections",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "rtl-gen cannot implement production RTL until the SSOT contains both the functional golden behavior and the cycle/handshake contract.\nSSOT ref: quality_gates.rtl_gen.ssot_required_sections.\nOwner: timer_core in rtl/cortex_m0lite.sv via single_owner.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "yaml/<ip>.ssot.yaml",
        "kind": "ssot_required_sections",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0003",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_match": "single_owner",
      "owner_module": "timer_core",
      "priority": "critical",
      "required": true,
      "requires_static_rtl_evidence": false,
      "source_ref": "quality_gates.rtl_gen.ssot_required_sections",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.ssot_required_sec
... <truncated 224167 chars>

### cortex_m0lite/rtl/rtl_authoring_status.md
# RTL Authoring Status: cortex_m0lite

## Status

- Top: cortex_m0lite
- Packets: 20
- LLM-actionable tasks: 0
- Human-locked tasks: 0
- Tool-evidence tasks: 2
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=2, next_tool=lint, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.


Current packet JSON (rtl/authoring_packets/rtl_gate_tool_evidence.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "owner": {
      "file": "rtl/cortex_m0lite.sv",
      "name": "cortex_m0lite",
      "refs": [],
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
    "ssot_top_io_contracts": [
      {
        "aliases": [
          "clk"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "clk",
        "source_ref": "io_list.clock_domains[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "rst_n"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "rst_n",
        "source_ref": "io_list.resets[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "fetch_en",
          "timer_ctrl_fetch_en"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "fetch_en",
        "source_ref": "io_list.interfaces[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "step_en",
          "timer_ctrl_step_en"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "step_en",
        "source_ref": "io_list.interfaces[0].ports[1]",
        "width": "1"
      },
      {
        "aliases": [
          "flush",
          "timer_ctrl_flush"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "flush",
        "source_ref": "io_list.interfaces[0].ports[2]",
        "width": "1"
      },
      {
        "aliases": [
          "instr_data",
          "timer_ctrl_instr_data"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "instr_data",
        "source_ref": "io_list.interfaces[0].ports[3]",
        "width": "XLEN"
      },
      {
        "aliases": [
          "pc",
          "timer_ctrl_pc"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "pc",
        "source_ref": "io_list.interfaces[0].ports[4]",
        "width": "XLEN"
      },
      {
        "aliases": [
          "busy",
          "timer_ctrl_busy"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "busy",
        "source_ref": "io_list.interfaces[0].ports[5]",
        "width": "1"
      },
      {
        "aliases": [
          "retire",
          "timer_ctrl_retire"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "retire",
        "source_ref": "io_list.interfaces[0].ports[6]",
        "width": "1"
      }
    ],
    "target_scale": null
  },
  "execution_policy": {
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "dut_lint",
        "owner_module": "timer_core",
        "reason": "DUT lint artifact is not clean.",
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "timer_core",
        "reason": "1 required non-closure TODO(s) remain open.",
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "contract_blocked_open_count": 0,
    "deferred_human_qa_allowed": true,
    "draft_allowed": false,
    "evidence_closure_allowed": true,
    "human_locked_open_count": 0,
    "integration_signoff_allowed": true,
    "llm_actionable": false,
    "llm_actionable_open_count": 0,
    "open_required_count": 2,
    "pass_allowed": false,
    "stop_conditions": [
      "Close this packet only after every required task in the packet has pass status.",
      "Return human_gate/change-request JSON when locked truth is missing instead of inventing semantics.",
      "Never use a fixed RTL template as the implementation."
    ],
    "tool_evidence_open_count": 2,
    "tool_evidence_plan": [
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
        "reason": "DUT lint artifact is not clean.",
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
        "reason": "1 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "work_allowed": true
  },
  "ip": "cortex_m0lite",
  "kind": "gate",
  "owner_file": "rtl/cortex_m0lite.sv",
  "owner_module": "cortex_m0lite",
  "packet_id": "rtl_gate_tool_evidence",
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
      "rtl_gate.rtl_gen": 4
    },
    "module_slice": {},
    "open_required_count": 2,
    "required_count": 4,
    "source_refs": [
      "quality_gates.rtl_gen.common_ai_agent_authoring",
      "quality_gates.rtl_gen.dut_compile",
      "quality_gates.rtl_gen.dut_lint",
      "quality_gates.rtl_gen.dynamic_todo_closure"
    ],
    "status_counts": {
      "open": 2,
      "pass": 2
    },
    "task_count": 4
  },
  "tasks": [
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits",
      "criteria": [
        "rtl/rtl_authoring_provenance.json exists",
        "provenance agent is common_ai_agent",
        "provenance workflow is rtl-gen",
        "provenance surface is atlas_ui, textual_ui, or headless_common_engine",
        "provenance todo_plan_sha256 matches the current rtl_todo_plan.json",
        "provenance rtl_files lists every SSOT manifest RTL file",
        "provenance rtl_files covers the current DUT filelist sources",
        "Traceability keeps source_ref quality_gates.rtl_gen.common_ai_agent_authoring",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.\nSSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.\nOwner: timer_core in rtl/cortex_m0lite.sv via single_owner.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_authoring_provenance.json",
        "kind": "common_ai_agent_authoring",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0006",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.common_ai_agent_authoring"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_authoring_provenance.json"
        ],
        "reason": "RTL authoring provenance proves common_ai_agent rtl-gen ownership.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: DUT-only RTL compile report passes after the final RTL edit",
      "criteria": [
        "rtl/rtl_compile.json exists",
        "rtl_compile.json reports dut_only=true",
        "rtl_compile.json passed=true with zero errors, diagnostics, and style violations",
        "rtl_compile.json is newer than or equal to every listed DUT RTL source",
        "rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources",
        "Traceability keeps source_ref quality_gates.rtl_gen.dut_compile",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.\nSSOT ref: quality_gates.rtl_gen.dut_compile.\nOwner: timer_core in rtl/cortex_m0lite.sv via single_owner.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_compile.json",
        "kind": "dut_compile",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0017",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.dut_compile",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.dut_compile"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_compile.json"
        ],
        "reason": "DUT-only compile artifact passed with zero errors, diagnostics, and style violations.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: DUT-only lint report passes after the final RTL edit",
      "criteria": [
        "lint/dut_lint.json exists",
        "dut_lint.json reports dut_only=true",
        "dut_lint.json passed=true with zero errors and zero warnings",
        "dut_lint.json is newer than or equal to every listed DUT RTL source",
        "dut_lint.json rtl_files covers the current DUT filelist RTL/header sources",
        "No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver",
        "Traceability keeps source_ref quality_gates.rtl_gen.dut_lint",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.\nSSOT ref: quality_gates.rtl_gen.dut_lint.\nOwner: timer_core in rtl/cortex_m0lite.sv via single_owner.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "lint/dut_lint.json",
        "kind": "dut_lint",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0018",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.dut_lint",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.dut_lint"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "lint/dut_lint.json"
        ],
        "reason": "DUT lint artifact is not clean.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: every required rtl_todo_plan item is closed before rtl-gen PASS",
      "criteria": [
        "Every required non-closure task has todo_completion.status=pass",
        "open_required_todos is zero",
        "all_required_todos_pass is true",
        "Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure",
        "Primary implementation evidence is in rtl/cortex_m0lite.sv"
      ],
      "detail": "rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.\nSSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.\nOwner: timer_core in rtl/cortex_m0lite.sv via single_owner.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "dynamic_todo_closure",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0019",
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "timer_core",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.dynamic_todo_closure"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "1 required non-closure TODO(s) remain open.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "2c8b63440d960beba0c10f8b1f5686e14fe23432d04cff8c3991c1a1f1fbe10f",
  "top": "cortex_m0lite",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/rtl_gate_tool_evidence.md):
# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: cortex_m0lite
- Owner file: rtl/cortex_m0lite.sv
- Task count: 4
- Required tasks: 4

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Tool-evidence blockers:
  - dut_lint: DUT lint artifact is not clean.
  - dynamic_todo_closure: 1 required non-closure TODO(s) remain open.
- Tool-evidence runbook:
  - dut_lint: stages=lint, dut_lint; artifact=cortex_m0lite/lint/dut_lint.json
  - dynamic_todo_closure: stages=audit-rtl; artifact=cortex_m0lite/rtl/rtl_todo_plan.json
- SSOT top IO contracts: 9

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: timer_core in rtl/cortex_m0lite.sv via single_owner.
- Current reason: RTL authoring provenance proves common_ai_agent rtl-gen ownership.
- Criteria:
  - rtl/rtl_authoring_provenance.json exists
  - provenance agent is common_ai_agent
  - provenance workflow is rtl-gen
  - provenance surface is atlas_ui, textual_ui, or headless_common_engine
  - provenance todo_plan_sha256 matches the current rtl_todo_plan.json
  - provenance rtl_files lists every SSOT manifest RTL file
  - provenance rtl_files covers the current DUT filelist sources
  - Traceability keeps source_ref quality_gates.rtl_gen.common_ai_agent_authoring
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0017: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: timer_core in rtl/cortex_m0lite.sv via single_owner.
- Current reason: DUT-only compile artifact passed with zero errors, diagnostics, and style violations.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0018: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: timer_core in rtl/cortex_m0lite.sv via single_owner.
- Current reason: DUT lint artifact is not clean.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0019: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: timer_core in rtl/cortex_m0lite.sv via single_owner.
- Current reason: 1 required non-closure TODO(s) remain open.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure
