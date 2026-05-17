RTL-GEN PACKET MODE for simple_pwm. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "simple_pwm/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "simple_pwm/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "simple_pwm/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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
- Gate/tool-evidence packets may edit any declared RTL file implicated by the audit digest, compile diagnostics, lint diagnostics, or static-evidence gaps; current owner_file is the gate coordinator, not an edit restriction.
- Keep generated RTL lint-clean: eliminate Verilator warnings, unused evidence-only helper signals, unused parameters, and the no_parameterized_part_select_in_procedural_block style violation by adding real helper wires or real signal consumption.
- Treat lint.repair_hints as mandatory repair guidance. For UNUSED* diagnostics, prefer narrowing/removing helper declarations or real functional connections; do not add marker-only reductions, lint suppressions, or evidence-only consumes.
- If lint.repair_hints names a signal, the emitted RTL must make that exact reported diagnostic disappear; renaming or copying the signal while leaving the same unused upper-bit pattern open is a failed repair.
- For narrower GPIO/output consumers, connect from the full producer slice, such as producer[GPIO_WIDTH-1:0], or use a GPIO_WIDTH helper; do not create another DATA_WIDTH masked/full helper whose upper bits remain unused.
- Static evidence terms are search/audit hints, not required signal names. Do not declare a wire/reg whose only purpose is to spell a TODO term; implement the behavior with real protocol/datapath/control logic and remove marker signals that lint reports unused.
- For rtl_gate_contract_blocked, return human_gate only; missing SSOT connection contracts block correct top integration semantics.
- For rtl_gate_human_closure, return human_gate only; do not invent or edit human-locked authority.
- The headless runner will refresh filelist/provenance from LLM-authored artifacts after each packet.

Current packet: module__simple_pwm__function_model
kind: module
work queue: 1/4 active packets (2 closed packets skipped from 17 total)
batch limit: 4; deferred active packets after this batch: 11
owner_module: simple_pwm
owner_file: rtl/simple_pwm.sv

SSOT observable latency contract:
{
  "cycle_model.latency": {
    "counter_update": {
      "description": "Counter increments or wraps every clock edge when enabled",
      "max_cycles": 1,
      "min_cycles": 1
    },
    "pwm_output": {
      "description": "pwm_out reflects counter vs duty_cycle comparison on same edge",
      "max_cycles": 1,
      "min_cycles": 1
    }
  },
  "cycle_model.pipeline": [
    {
      "action": "Increment counter or wrap to 0 when enable=1; hold at 0 when enable=0",
      "cycle": 1,
      "stage": "S0_COUNTER_UPDATE"
    },
    {
      "action": "Compare counter with duty_cycle; drive pwm_out accordingly",
      "cycle": 1,
      "stage": "S1_COMPARE_OUTPUT"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": "enable == 1",
  "timing.latency_budget": {
    "pwm_update_cycles": {
      "max": 1,
      "measured_from": "rising edge",
      "measured_to": "pwm_out stable",
      "min": 1
    }
  }
}

SSOT bus/byte-lane policy:
{
  "guidance": "condition=none means upper byte lanes are not an APB error for legal offsets; consume otherwise-unused pwdata/pstrb upper bits through explicit legal ignore, byte-strobe masking, reserved-zero readback, or coverage/trace behavior while keeping pslverr deasserted for legal writes.",
  "illegal_byte_access_pattern_condition": "<not declared>",
  "upper_byte_lane_error_allowed": false
}

Locked SSOT YAML excerpt (simple_pwm/yaml/simple_pwm.ssot.yaml):
# =============================================================================
# simple_pwm SSOT — Single Source of Truth
# =============================================================================
# Type: peripheral (PWM generator)
# Scale: educational-tiny, single module, no bus, no registers
# =============================================================================

top_module:
  name: "simple_pwm"
  file: "rtl/simple_pwm.sv"
  version: "1.0"
  type: "peripheral"
  description: "Configurable PWM output generator with duty-cycle and period inputs"
  reference_spec: "user-defined"
  target:
    technology: "generic"
    clock_freq_mhz: 100
    area_um2: null
    power_mw: null

sub_modules: []

decomposition:
  units:
    - { id: "counter", kind: "datapath", source_refs: ["function_model.transactions"], rtl_candidates: ["simple_pwm"], verification_impact: ["test_requirements.scenarios"] }

parameters:
  - name: "COUNTER_WIDTH"
    default: 8
    type: int
    description: "Counter width in bits (1-16)"
    drives: ["rtl/simple_pwm.sv"]

io_list:
  clock_domains:
    - name: "clk"
      frequency_mhz: 100
      description: "System clock"
      ports:
        - { name: "clk", width: 1, direction: "input", description: "System clock, rising-edge active" }

  resets:
    - name: "rst_n"
      polarity: "active_low"
      sync_async: "async_assert_sync_deassert"
      description: "Active-low asynchronous reset"
      ports:
        - { name: "rst_n", width: 1, direction: "input", description: "Active-low async reset" }

  interfaces:
    - name: "pwm_control"
      type: "custom"
      clock_domain: "clk"
      reset_domain: "rst_n"
      description: "PWM control and data interface"
      protocol:
        sampling: "Inputs sampled on rising clk edge when rst_n is high."
        timing: "enable, duty_cycle, and period are combinational inputs, no handshake required."
      ports:
        - { name: "enable",     width: 1,              direction: "input",  description: "PWM enable (1=running, 0=stopped)" }
        - { name: "duty_cycle", width: "COUNTER_WIDTH", direction: "input",  description: "Duty cycle threshold value" }
        - { name: "period",     width: "COUNTER_WIDTH", direction: "input",  description: "Counter period (rollover value)" }

    - name: "pwm_output"
      type: "custom"
      clock_domain: "clk"
      reset_domain: "rst_n"
      description: "PWM output signal"
      protocol:
        assertion: "pwm_out reflects the comparison of counter vs duty_cycle each clock cycle."
        deassertion: "pwm_out clears to 0 on reset or when enable=0."
        reset_value: 0
      ports:
        - { name: "pwm_out", width: 1, direction: "output", description: "PWM output signal" }

features:
  - name: "PWM generation"
    trigger: "enable asserted high"
    datapath: "Free-running counter 0 to (period-1); pwm_out=1 when counter < duty_cycle, else 0"
    control: "IDLE when enable=0, RUNNING when enable=1"
    output: "pwm_out toggles at duty_cycle/period ratio"

  - name: "Dynamic reconfiguration"
    trigger: "duty_cycle or period input changes at any time"
    datapath: "New values sampled on next clock edge"
    control: "No special sequence required"
    output: "PWM output adjusts within one period"

dataflow:
  counter_path:
    source: "counter register (COUNTER_WIDTH bits)"
    sequence: "counter -> compare with duty_cycle -> pwm_out; compare with period -> rollover"

function_model:
  purpose: "Executable behavioral contract for rtl-gen and tb-gen"
  state_variables:
    - { name: "counter", source: "internal", reset: 0, description: "Free-running counter, wraps at period" }
  transactions:
    - id: "FM1"
      name: "pwm_active_high"
      preconditions:
        - "enable == 1"
        - "counter < duty_cycle"
      inputs:
        - "duty_cycle"
        - "period"
      outputs:
        - name: "pwm_out"
          value: 1
      output_rules:
        - { name: "pwm_out_high", expr: "1", width: 1, port: "pwm_out" }
      state_updates:
        - { name: "counter_next", expr: "counter + 1 if (counter + 1) < period else 0", width: "COUNTER_WIDTH" }
      side_effects:
        - "counter increments by 1"
      error_cases: []

    - id: "FM2"
      name: "pwm_active_low"
      preconditions:
        - "enable == 1"
        - "counter >= duty_cycle"
      inputs:
        - "duty_cycle"
        - "period"
      outputs:
        - name: "pwm_out"
          value: 0
      output_rules:
        - { name: "pwm_out_low", expr: "0", width: 1, port: "pwm_out" }
      state_updates:
        - { name: "counter_next", expr: "counter + 1 if (counter + 1) < period else 0", width: "COUNTER_WIDTH" }
      side_effects:
        - "counter increments by 1"
      error_cases: []

    - id: "FM3"
      name: "pwm_idle"
      preconditions:
        - "enable == 0"
      inputs: []
      outputs:
        - name: "pwm_out"
          value: 0
      output_rules:
        - { name: "pwm_out_off", expr: "0", width: 1, port: "pwm_out" }
      state_updates:
        - { name: "counter_next", expr: "0", width: "COUNTER_WIDTH" }
      side_effects:
        - "counter resets to 0"
      error_cases: []

  invariants:
    - "pwm_out is 0 whenever enable is 0"
    - "counter resets to 0 when it reaches period"
    - "counter is 0 whenever enable is 0"

cycle_model:
  purpose: "Cycle-accurate contract for rtl-gen"
  executable: "python"
  clock: "clk"
  reset:
    assertion: "rst_n low asynchronously clears counter to 0 and pwm_out to 0"
    deassertion: "state is usable on the first rising edge after synchronized deassertion"
  latency:
    counter_update: { min_cycles: 1, max_cycles: 1, description: "Counter increments or wraps every clock edge when enabled" }
    pwm_output: { min_cycles: 1, max_cycles: 1, description: "pwm_out reflects counter vs duty_cycle comparison on same edge" }
  handshake_rules:
    - { signal: "pwm_out", rule: "Combinational output derived from counter vs duty_cycle comparison; no valid/ready handshake" }
  pipeline:
    - { stage: "S0_COUNTER_UPDATE", cycle: 1, action: "Increment counter or wrap to 0 when enable=1; hold at 0 when enable=0" }
    - { stage: "S1_COMPARE_OUTPUT", cycle: 1, action: "Compare counter with duty_cycle; drive pwm_out accordingly" }
  ordering:
    - "Counter update and output comparison occur in the same clock cycle."
  backpressure: []
  performance:
    frequency_mhz: 100
    throughput: { sustained_operations_per_cycle: 1, condition: "enable asserted and period > 0" }
    outstanding: { max: 1, description: "Single-cycle counter operation" }
    depth: { pipeline_stages: 1, description: "Single-stage counter and compare" }
  observability:
    - "counter value is observable via internal state"
    - "pwm_out is the primary observable output"

clock_reset_domains:
  domains:
    - { name: "clk", frequency_mhz: 100, description: "System clock" }
  reset_scheme:
    signal: "rst_n"
    polarity: "active_low"
    type: "async_assert_sync_deassert"

cdc_requirements:
  crossings: []
  synchronizers: []
  note: "Single clock domain — no CDC required"

rdc_requirements:
  crossings: []
  synchronizers: []
  note: "No reset domain crossings"

registers:
  config:
    register_width: 0
    addr_width: 0
    byte_addressable: false
    note: "No register map — all inputs are direct ports"
  no_registers: true
  reason: "Educational PWM IP uses direct input ports instead of a register map; no bus interface required"
  register_list: []

memory:
  instances: []
  note: "No internal memory — counter is a simple register"

interrupts:
  sources: []
  output: null
  note: "No interrupts"

fsm:
  pwm_fsm:
    states:
      - "IDLE"
      - "RUNNING"
    transitions:
      - { from: "IDLE",    to: "RUNNING", condition: "enable == 1" }
      - { from: "RUNNING", to: "IDLE",    condition: "enable == 0" }
    description: "Simple enable-gated FSM"

rtl_contract:
  transaction: "FM1, FM2, FM3"
  sample_condition: "enable == 1"
  input_map:
    enable: "enable"
    duty_cycle: "duty_cycle"
    period: "period"
  output_map:
    pwm_out: "pwm_out"
  state_updates:
    - { name: "counter", reset: 0, expr: "(counter + 1) % period when enable else 0" }

timing:
  target_clocks:
    - { name: "clk", frequency_mhz: 100, duty_cycle: 0.5, uncertainty_ns: 0.1 }
  latency_budget:
    pwm_update_cycles: { min: 1, max: 1, measured_from: "rising edge", measured_to: "pwm_out stable" }
  throughput:
    sustained_operations_per_cycle: 1
    conditions: "Enable asserted, valid period > 0"
  timing_exceptions: []
  io_delays:
    inputs:
      - { ports: "all_inputs_except_clocks_resets", clock: "clk", delay_ns: 0.2, source: "system-level timing budget" }
    outputs:
      - { ports: "all_outputs", clock: "clk", delay_ns: 0.2, source: "system-level timing budget" }
  false_paths: []
  multicycle_paths: []
  sta_expectations:
    setup_wns_ns_min: 0.0
    hold_wns_ns_min: 0.0
    required_reports: []

power:
  domains:
    - { name: "PD_CORE", voltage: "nominal", clock_domains: ["clk"], isolation: "not_required_single_domain" }
  clock_gating:
    required: false
    rationale: "Educational tiny IP — no power management"
  reset_retention:
    retention_required: false
  power_states:
    - { name: "ON", entry: "rst_n deasserted", exit: "rst_n asserted", guarantees: ["All behavior active"] }
  upf_required: false

security:
  classification: "non_secure_control_ip"
  assets:
    - { name: "pwm_out", protection: "Output is not protected; direct port drive" }
  threat_model:
    - { threat: "glitch on pwm_out", mitigation: "No protection; downstream system must handle glitching if critical" }
  privilege_model: "No privilege levels"
  safety_goals:
    - "No silent output corruption on input change"

error_handling:
  error_sources:
    - { id: "ERR_NONE", condition: "No error sources in this minimal IP", architectural_effect: "N/A" }
  propagation:
    - "No error propagation in this educational IP."
  recovery:
    - { action: "reset", clears: ["counter", "pwm_out"], preserves: [] }

debug_observability:
  waveform_must_probe:
    - "counter"
    - "pwm_out"
    - "enable"
  status_outputs: []
  trace_events:
    - { name: "pwm_enable", trigger: "enable rising edge" }
    - { name: "pwm_disable", trigger: "enable falling edge" }
    - { name: "counter_rollover", trigger: "counter wraps to 0" }
  debug_registers: []

integration:
  bus_attachment: "none"
  connections: []
  address_map_requirements: { note: "No bus interface" }
  dependencies:
    external_modules: []
    external_clocks: ["clk"]
    external_resets: ["rst_n"]
  integration_notes:
    - "Standalone IP, no bus integration required."

dft:
  scan_required: false
  scan_ports: []
  test_mode_ports: []
  controllability:
    reset: "rst_n controllable"
    clocks: ["clk"]
  observability:
    required_internal_points: ["counter", "pwm_out"]
  mbist_required: false
  notes: "Educational IP, no DFT"

synthesis:
  dialect: "systemverilog_2012"
  top_module: "simple_pwm"
  technology:
    pdk: "generic"
    standard_cell_library: "generic"
  constraints:
    - "No inferred latches"
    - "All flops reset via rst_n"
    - "No package/interface/modport/function/task/for/while constructs"
  ppa_targets:
    area_um2_max: null
    power_mw_max: null
    frequency_mhz_min: 100
  required_outputs:
    - "rtl/simple_pwm.sv"

pnr:
  utilization_pct: 60
  aspect_ratio: 1.0
  core_space_um: 2.0
  global_density: 0.65
  io_layers: { horizontal: "met3", vertical: "met2" }
  routing: { signal_layers: { min: "met1", max: "met5" }, drc_waivers: [] }
  required_outputs: []
  note: "Educational IP, no physical implementation required"

coding_rules:
  verilog_style: "systemverilog_2012"
  file_extension: ".sv"
  conventions:
    - "nonblocking (<=) in sequential always @(posedge clk or negedge rst_n)"
    - "blocking (=) in combinational always @(*)"
    - "No latches: every combinational branch assigns all outputs"
    - "Active-low async reset with if (!rst_n)"
    - "Parameterize widths with COUNTER_WIDTH"
    - "ALLOW: input logic / output logic ANSI ports"
    - "BANNED: typedef / enum / always_ff / always_comb / always_latch / package / interface / modport / function / task / for / while / *_pkg.sv"
  lint_waivers: []

reuse_modules: []

custom:
  note: "Educational tiny PWM controller — minimal configuration"

dir_structure:
  output_dirs:
    rtl: "rtl/"
    sim: "sim/"
  yaml_dir: "yaml/"

filelist:
  headers: []
  rtl:
    - "rtl/simple_pwm.sv"

test_requirements:
  scenarios:
    - id: "SC1"
      name: "Basic PWM generation"
      stimulus: "Set period=10, duty_cycle=3, enable=1 for 30 clock cycles"
      expected: "3 clocks of pwm_out=1, 7 clocks of pwm_out=0, repeating 3 times"
      checker: "Scoreboard counts pwm_out=1 and pwm_out=0 per period and verifies ratio"
      coverage: ["FM1", "FM2"]

    - id: "SC2"
      name: "Duty cycle variation"
      stimulus: "Start with duty_cycle=3, period=10; change duty_cycle to 7 after first period"
      expected: "First period: 3 high / 7 low; second period: 7 high / 3 low"
      checker: "Scoreboard verifies duty ratio changes in the period following the input change"
      coverage: ["FM1", "FM2"]

    - id: "SC3"
      name: "Period rollover"
      stimulus: "Set period=5, duty_cycle=2, enable=1 for 15 clock cycles"
      expected: "Counter: 0,1,2,3,4,0,1,2,3,4,0,1,2,3,4; pwm_out: 1,1,0,0,0 repeating"
      checker: "Scoreboard verifies counter wraps at period and pwm pattern repeats"
      coverage: ["FM1", "FM2"]

    - id: "SC4"
      name: "Disable behavior"
      stimulus: "Enable PWM with period=10, duty_cycle=3; disable after 5 clocks; re-enable after 5 more clocks"
      expected: "When enable=0: pwm_out=0, counter=0. When re-enabled: starts from counter=0"
      checker: "Scoreboard verifies pwm_out=0 and counter=0 during idle, restart from 0 on re-enable"
      coverage: ["FM3"]

  scoreboard_checks: 4
  coverage_goals:
    function:
      target_pct: 100
      model: "function_model"
      description: "Cycle-independent behavioral intent coverage"
      bins:
        - { id: "FCOV_PWM_HIGH", source_ref: "function_model.transactions.FM1", class: "transaction", description: "FM1 pwm_active_high observed: pwm_out=1 when counter < duty_cycle" }
        - { id: "FCOV_PWM_LOW", source_ref: "function_model.transactions.FM2", class: "transaction", description: "FM2 pwm_active_low observed: pwm_out=0 when counter >= duty_cycle" }
        - { id: "FCOV_PWM_IDLE", source_ref: "function_model.transactions.FM3", class: "transaction", description: "FM3 pwm_idle observed: pwm_out=0 and counter=0 when enable=0" }
    cycle:
      target_pct: 100
      model: "cycle_model"
      description: "Cycle/handshake coverage"
      bins:
        - { id: "CCOV_COUNTER_INCREMENT", source_ref: "cycle_model.pipeline.S0_COUNTER_UPDATE", class: "pipeline_stage", description: "Counter increments when enabled" }
        - { id: "CCOV_COUNTER_ROLLOVER", source_ref: "cycle_model.pipeline.S0_COUNTER_UPDATE", class: "pipeline_stage", description: "Counter wraps to 0 when reaching period" }
        - { id: "CCOV_COMPARE_HIGH", source_ref: "cycle_model.pipeline.S1_COMPARE_OUTPUT", class: "pipeline_stage", description: "Comparison produces pwm_out=1" }
        - { id: "CCOV_COMPARE_LOW", source_ref: "cycle_model.pipeline.S1_COMPARE_OUTPUT", class: "pipeline_stage", description: "Comparison produces pwm_out=0" }
        - { id: "CCOV_FSM_IDLE_TO_RUNNING", source_ref: "fsm.pwm_fsm.transitions", class: "state_transition", description: "IDLE to RUNNING transition observed" }
        - { id: "CCOV_FSM_RUNNING_TO_IDLE", source_ref: "fsm.pwm_fsm.transitions", class: "state_transition", description: "RUNNING to IDLE transition observed" }
    functional: "Legacy alias: function + cycle coverage must both close"
    code: "line >= 90%, branch >= 85%"

quality_gates:
  ssot:
    pass: "All canonical sections present, no TBD placeholders, internally consistent"
    evidence: ["check_ssot_disk.sh PASS"]
  rtl_gen:
    profile: "standard"
    pass: "RTL compiles and lints clean; implements counter + duty comparison + period rollover"
    evidence: ["rtl/rtl_compile.json", "lint/dut_lint.json"]
  rtl:
    pass: "RTL matches function_model behavior"
    evidence: ["rtl compile report", "dut lint report", "FL-vs-RTL scoreboard"]
  dv:
    pass: "All test scenarios pass; FL-vs-RTL equivalence 100%"
    evidence: ["sim/results.xml", "sim/scoreboard_events.jsonl"]
  coverage:
    pass: "All declared function and cycle bins hit"
    evidence: ["cov/coverage.json"]
  eda:
    pass: "Not applicable for educational-tiny IP; synthesis not required"
    evidence: ["N/A — educational IP skips EDA stages"]
  signoff:
    pass: "All required stages have approved evidence"
    evidence: ["rtl/rtl_compile.json", "lint/dut_lint.json", "sim/results.xml", "cov/coverage.json"]

traceability:
  yaml_to_output:
    - { yaml: "top_module.name", output: "simple_pwm.sv (module name)" }
    - { yaml: "parameters", output: "COUNTER_WIDTH parameter in simple_pwm.sv" }
    - { yaml: "io_list.interfaces", output: "simple_pwm.sv (port list)" }
    - { yaml: "function_model", output: "simple_pwm.sv counter + compare logic + tb/cocotb scoreboard" }
    - { yaml: "cycle_model", output: "simple_pwm.sv single-cycle update logic" }
    - { yaml: "fsm", output: "simple_pwm.sv enable-gated FSM" }
    - { yaml: "test_requirements.scenarios", output: "tb/cocotb test scenarios" }

workflow_todos:
  fl-model-gen: []
  rtl-gen:
    - id: "RTL_001"
      content: "Implement PWM counter with period rollover"
      detail: "Implement a free-running counter that increments each clock cycle when enable=1 and wraps to 0 when it reaches the period input value. When enable=0, counter stays at 0."
      criteria:
        - "Counter increments when enable=1"
        - "Counter wraps to 0 when counter+1 == period"
        - "Counter stays at 0 when enable=0"
        - "Counter width is COUNTER_WIDTH parameter"
      source_refs: ["function_model.transactions.FM1", "function_model.transactions.FM2", "function_model.transactions.FM3"]
      owner_module: "simple_pwm"
      owner_file: "rtl/simple_pwm.sv"
      priority: "high"
      required: true
    - id: "RTL_002"
      content: "Implement duty-cycle comparison and pwm_out output"
      detail: "Compare counter value with duty_cycle input each clock cycle. Drive pwm_out=1 when counter < duty_cycle, pwm_out=0 when counter >= duty_cycle. When enable=0, force pwm_out=0."
      criteria:
        - "pwm_out=1 when enable=1 and counter < duty_cycle"
        - "pwm_out=0 when enable=1 and counter >= duty_cycle"
        - "pwm_out=0 when enable=0"
        - "Comparison is combinational (same-cycle)"
      source_refs: ["function_model.transactions.FM1", "function_model.transactions.FM2", "function_model.transactions.FM3"]
      owner_module: "simple_pwm"
      owner_file: "rtl/simple_pwm.sv"
      priority: "high"
      required: true
  tb-gen: []
  sim_debug: []
  coverage: []

generation_flow:
  steps:
    - { name: "validate_ssot", command: "bash workflow/ssot-gen/scripts/check_ssot_disk.sh simple_pwm", description: "Validate SSOT structure" }
    - { name: "handoff_fl_model", command: "/ssot-fl-model simple_pwm", description: "Generate functional model" }
    - { name: "handoff_rtl", command: "/ssot-rtl simple_pwm", description: "Generate RTL" }
    - { name: "handoff_tb", command: "/ssot-tb simple_pwm", description: "Generate testbench" }
    - { name: "handoff_sim", command: "/sim simple_pwm", description: "Run simulation" }
    - { name: "handoff_coverage", command: "/coverage simple_pwm", description: "Measure coverage" }


Base rtl-gen contract:
Prepare rtl-gen for simple_pwm using only simple_pwm/yaml/simple_pwm.ssot.yaml and simple_pwm/rtl/rtl_todo_plan.json, simple_pwm/rtl/rtl_authoring_plan.json, and packets under simple_pwm/rtl/authoring_packets. Return exactly one JSON object and nothing else. Success schema: {"files":[{"path":"simple_pwm/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"},{"path":"simple_pwm/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"},{"path":"simple_pwm/list/simple_pwm.f","kind":"filelist","content":"<filelist>"}]}. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=97147a83467339f3d8bdf10370e6366a4b8a3eeca0cb4ad8bac3bf660a00d118. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "simple_pwm",
        "reason": "31 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "simple_pwm",
        "reason": "1 owner logic structure issue(s) remain. simple_pwm: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "rtl_placeholder_free_evidence",
        "owner_module": "simple_pwm",
        "reason": "1 RTL placeholder/policy issue(s) remain. None:None: None (No listed RTL source files were readable, so placeholder-free evidence cannot be checked)",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "status": "open",
        "task_id": "RTL-0009"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "simple_pwm",
        "reason": "1 top IO contract issue(s) remain. simple_pwm: SSOT top module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "top_output_drive_evidence",
        "owner_module": "simple_pwm",
        "reason": "1 top output drive issue(s) remain. simple_pwm: SSOT top module is not declared, so output drive evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
        "status": "open",
        "task_id": "RTL-0011"
      },
      {
        "gate_kind": "top_input_consumption_evidence",
        "owner_module": "simple_pwm",
        "reason": "1 top input consumption issue(s) remain. simple_pwm: SSOT top module is not declared, so input consumption evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
        "status": "open",
        "task_id": "RTL-0012"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "simple_pwm",
        "reason": "1 manifest hierarchy integration issue(s) remain. simple_pwm: SSOT top module is not declared in listed RTL sources",
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
        "owner_module": "simple_pwm",
        "reason": "Missing common_ai_agent RTL authoring provenance.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "simple_pwm",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "simple_pwm",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "simple_pwm",
        "reason": "79 required non-closure TODO(s) remain open.",
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
    "open_required_todos": 80,
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
          "simple_pwm/rtl/rtl_authoring_provenance.json",
          "simple_pwm/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip simple_pwm --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py simple_pwm --root . --audit-rtl"
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
          "simple_pwm/rtl/rtl_compile.json",
          "simple_pwm/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py simple_pwm --top simple_pwm --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py simple_pwm --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "simple_pwm/list/simple_pwm.f covers the current DUT RTL sources."
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
          "simple_pwm/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py simple_pwm --top simple_pwm",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py simple_pwm --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "simple_pwm/list/simple_pwm.f covers the current DUT RTL/header sources."
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
          "simple_pwm/rtl/rtl_todo_plan.json",
          "simple_pwm/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py simple_pwm --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "79 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ]
  },
  "ip": "simple_pwm",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__function_model.json",
      "kind": "module",
      "llm_actionable_open_count": 28,
      "open_required_count": 28,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__function_model",
      "required_count": 28,
      "status_counts": {
        "open": 28
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 9,
      "open_required_count": 9,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__cycle_model",
      "required_count": 9,
      "status_counts": {
        "open": 9
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 6,
      "open_required_count": 6,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__io_list",
      "required_count": 6,
      "status_counts": {
        "open": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__synthesis.json",
      "kind": "module",
      "llm_actionable_open_count": 6,
      "open_required_count": 6,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__synthesis",
      "required_count": 6,
      "status_counts": {
        "open": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__fsm",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__test_requirements",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__integration.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__integration",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__features.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__features",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__workflow_todo",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__equivalence",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__error_handling",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__parameters",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__rtl_flow.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__rtl_flow",
      "required_count": 2,
      "status_counts": {
        "open": 1,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__simple_pwm__security.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "module__simple_pwm__security",
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
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
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
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
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
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 4,
      "status_counts": {
        "pass": 4
      }
    }
  ],
  "policy": {
    "dynamic_task_rule": "Use every required task in this file as the authoritative RTL implementation/evidence ledger. Expose Atlas/UI TodoTracker items as a flat one-to-one projection of this ledger so the existing flat TodoTracker executes one SSOT-derived RTL task at a time.",
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
  "sim_debug_repair_evidence": {
    "items": 0,
    "owner_workflow": "rtl-gen",
    "source": "simple_pwm/sim/mismatch_classification.json"
  },
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 0,
    "human_locked_tasks": 0,
    "llm_actionable_packets": 15,
    "llm_actionable_tasks": 76,
    "max_packet_required_tasks": 28,
    "module_packets": 14,
    "next_llm_packets": [
      "module__simple_pwm__function_model",
      "module__simple_pwm__cycle_model",
      "module__simple_pwm__io_list",
      "module__simple_pwm__synthesis",
      "module__simple_pwm__fsm",
      "module__simple_pwm__test_requirements",
      "module__simple_pwm__integration",
      "module__simple_pwm__features"
    ],
    "packet_task_limit": 48,
    "packets": 17,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 87,
    "sliced_module_packets": 14,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 4,
    "total_tasks": 87,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "97147a83467339f3d8bdf10370e6366a4b8a3eeca0cb4ad8bac3bf660a00d118",
  "top": "simple_pwm",
  "type": "rtl_authoring_plan"
}

Current sim-debug owner repair evidence:
{
  "items": [],
  "owner_workflow": "rtl-gen",
  "source": "simple_pwm/sim/mismatch_classification.json",
  "status": "none"
}

Current owner RTL file (rtl/simple_pwm.sv):
<missing or not authored yet>

Current RTL module interface digest (all manifest RTL files):
### rtl/simple_pwm.sv
<missing>

Current mandatory lint repair directives:
<none>

Current RTL gate audit digest:
{
  "compile": {
    "diagnostics": null,
    "errors": null,
    "passed": null,
    "present": false,
    "returncode": null,
    "source": "simple_pwm/rtl/rtl_compile.json",
    "style_violation_details": [],
    "style_violations": null
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
    "open_required_todos": 80,
    "orphan_tasks": 0,
    "static_missing": 31,
    "status": "fail"
  },
  "lint": {
    "diagnostics": [],
    "errors": null,
    "passed": null,
    "present": false,
    "repair_hints": [],
    "returncode": null,
    "source": "simple_pwm/lint/dut_lint.json",
    "style_violation_count": null,
    "suppression_violation_count": null,
    "warnings": null
  },
  "manifest_hierarchy_issues": [
    {
      "file": "rtl/simple_pwm.sv",
      "issue": "SSOT top module is not declared in listed RTL sources",
      "module": "simple_pwm"
    }
  ],
  "manifest_signal_flow_issues": [],
  "open_required_tasks": [
    {
      "category": "rtl_flow.top",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "io_list",
      "task_id": "RTL-0002"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "Missing common_ai_agent RTL authoring provenance.",
      "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
      "task_id": "RTL-0006"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "31 static-evidence-required task(s) still lack DUT RTL evidence.",
      "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
      "task_id": "RTL-0007"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 owner logic structure issue(s) remain. simple_pwm: Behavior-owner module is not declared in its owner file",
      "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
      "task_id": "RTL-0008"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 RTL placeholder/policy issue(s) remain. None:None: None (No listed RTL source files were readable, so placeholder-free evidence cannot be checked)",
      "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
      "task_id": "RTL-0009"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 top IO contract issue(s) remain. simple_pwm: SSOT top module is not declared in listed RTL sources",
      "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
      "task_id": "RTL-0010"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 top output drive issue(s) remain. simple_pwm: SSOT top module is not declared, so output drive evidence cannot be checked",
      "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
      "task_id": "RTL-0011"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 top input consumption issue(s) remain. simple_pwm: SSOT top module is not declared, so input consumption evidence cannot be checked",
      "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
      "task_id": "RTL-0012"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 manifest hierarchy integration issue(s) remain. simple_pwm: SSOT top module is not declared in listed RTL sources",
      "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "task_id": "RTL-0013"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
      "source_ref": "quality_gates.rtl_gen.dut_compile",
      "task_id": "RTL-0017"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
      "source_ref": "quality_gates.rtl_gen.dut_lint",
      "task_id": "RTL-0018"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "79 required non-closure TODO(s) remain open.",
      "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
      "task_id": "RTL-0019"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "workflow_todos.rtl-gen[0]",
      "task_id": "RTL-0020"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "workflow_todos.rtl-gen[1]",
      "task_id": "RTL-0021"
    },
    {
      "category": "parameters.item",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "parameters.COUNTER_WIDTH",
      "task_id": "RTL-0022"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "io_list.clock_domains.clk.ports.clk",
      "task_id": "RTL-0023"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "io_list.resets.rst_n.ports.rst_n",
      "task_id": "RTL-0024"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "io_list.interfaces.pwm_control.ports.enable",
      "task_id": "RTL-0025"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "io_list.interfaces.pwm_control.ports.duty_cycle",
      "task_id": "RTL-0026"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "io_list.interfaces.pwm_control.ports.period",
      "task_id": "RTL-0027"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "io_list.interfaces.pwm_output.ports.pwm_out",
      "task_id": "RTL-0028"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.state_variables.counter",
      "task_id": "RTL-0029"
    },
    {
      "category": "function_model.transaction",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1",
      "task_id": "RTL-0030"
    },
    {
      "category": "function_model.precondition",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1.preconditions.precondition_0",
      "task_id": "RTL-0031"
    },
    {
      "category": "function_model.precondition",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1.preconditions.precondition_1",
      "task_id": "RTL-0032"
    },
    {
      "category": "function_model.input",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1.inputs.input_0",
      "task_id": "RTL-0033"
    },
    {
      "category": "function_model.input",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1.inputs.input_1",
      "task_id": "RTL-0034"
    },
    {
      "category": "function_model.output",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1.outputs.pwm_out",
      "task_id": "RTL-0035"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1.output_rules.pwm_out_high",
      "task_id": "RTL-0036"
    },
    {
      "category": "function_model.state_update",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1.state_updates.counter_next",
      "task_id": "RTL-0037"
    },
    {
      "category": "function_model.side_effect",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM1.side_effects.side_effect_0",
      "task_id": "RTL-0038"
    },
    {
      "category": "function_model.transaction",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2",
      "task_id": "RTL-0039"
    },
    {
      "category": "function_model.precondition",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2.preconditions.precondition_0",
      "task_id": "RTL-0040"
    },
    {
      "category": "function_model.precondition",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2.preconditions.precondition_1",
      "task_id": "RTL-0041"
    },
    {
      "category": "function_model.input",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2.inputs.input_0",
      "task_id": "RTL-0042"
    },
    {
      "category": "function_model.input",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2.inputs.input_1",
      "task_id": "RTL-0043"
    },
    {
      "category": "function_model.output",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2.outputs.pwm_out",
      "task_id": "RTL-0044"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2.output_rules.pwm_out_low",
      "task_id": "RTL-0045"
    },
    {
      "category": "function_model.state_update",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2.state_updates.counter_next",
      "task_id": "RTL-0046"
    },
    {
      "category": "function_model.side_effect",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM2.side_effects.side_effect_0",
      "task_id": "RTL-0047"
    },
    {
      "category": "function_model.transaction",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM3",
      "task_id": "RTL-0048"
    },
    {
      "category": "function_model.precondition",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM3.preconditions.precondition_0",
      "task_id": "RTL-0049"
    },
    {
      "category": "function_model.output",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM3.outputs.pwm_out",
      "task_id": "RTL-0050"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM3.output_rules.pwm_out_off",
      "task_id": "RTL-0051"
    },
    {
      "category": "function_model.state_update",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM3.state_updates.counter_next",
      "task_id": "RTL-0052"
    },
    {
      "category": "function_model.side_effect",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.transactions.FM3.side_effects.side_effect_0",
      "task_id": "RTL-0053"
    },
    {
      "category": "function_model.invariant",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.invariants.invariant_0",
      "task_id": "RTL-0054"
    },
    {
      "category": "function_model.invariant",
      "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
      "source_ref": "function_model.invariants.invariant_1",
      "task_id": "RTL-0055"
    }
  ],
  "source": "simple_pwm/rtl/rtl_todo_plan.json",
  "static_missing_tasks": [
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 3,
      "required_terms": [
        "001",
        "RTL_001",
        "pwm",
        "simple",
        "simple_pwm"
      ],
      "source_ref": "workflow_todos.rtl-gen[0]",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0020"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 3,
      "required_terms": [
        "002",
        "RTL_002",
        "pwm",
        "simple",
        "simple_pwm"
      ],
      "source_ref": "workflow_todos.rtl-gen[1]",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0021"
    },
    {
      "category": "function_model.precondition",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "duty",
        "duty_cycle"
      ],
      "source_ref": "function_model.transactions.FM1.preconditions.precondition_1",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0032"
    },
    {
      "category": "function_model.input",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "duty",
        "duty_cycle",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM1.inputs.input_0",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0033"
    },
    {
      "category": "function_model.input",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next",
        "out",
        "period",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM1.inputs.input_1",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0034"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM1.outputs.pwm_out",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0035"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "high",
        "out",
        "pwm",
        "pwm_out",
        "pwm_out_high"
      ],
      "source_ref": "function_model.transactions.FM1.output_rules.pwm_out_high",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0036"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next"
      ],
      "source_ref": "function_model.transactions.FM1.state_updates.counter_next",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0037"
    },
    {
      "category": "function_model.side_effect",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM1.side_effects.side_effect_0",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0038"
    },
    {
      "category": "function_model.precondition",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "duty",
        "duty_cycle"
      ],
      "source_ref": "function_model.transactions.FM2.preconditions.precondition_1",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0041"
    },
    {
      "category": "function_model.input",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "duty",
        "duty_cycle",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM2.inputs.input_0",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0042"
    },
    {
      "category": "function_model.input",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next",
        "out",
        "period",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM2.inputs.input_1",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0043"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM2.outputs.pwm_out",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0044"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "low",
        "out",
        "pwm",
        "pwm_out",
        "pwm_out_low"
      ],
      "source_ref": "function_model.transactions.FM2.output_rules.pwm_out_low",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0045"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next"
      ],
      "source_ref": "function_model.transactions.FM2.state_updates.counter_next",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0046"
    },
    {
      "category": "function_model.side_effect",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM2.side_effects.side_effect_0",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0047"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM3.outputs.pwm_out",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0050"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "off",
        "out",
        "pwm",
        "pwm_out",
        "pwm_out_off"
      ],
      "source_ref": "function_model.transactions.FM3.output_rules.pwm_out_off",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0051"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next"
      ],
      "source_ref": "function_model.transactions.FM3.state_updates.counter_next",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0052"
    },
    {
      "category": "function_model.side_effect",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.transactions.FM3.side_effects.side_effect_0",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0053"
    },
    {
      "category": "function_model.invariant",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.invariants.invariant_0",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0054"
    },
    {
      "category": "function_model.invariant",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.invariants.invariant_1",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0055"
    },
    {
      "category": "function_model.invariant",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "function_model.invariants.invariant_2",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0056"
    },
    {
      "category": "cycle_model.handshake_rules",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "cycle_model.handshake_rules.pwm_out",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0060"
    },
    {
      "category": "cycle_model.pipeline",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "duty",
        "duty_cycle",
        "out",
        "pwm",
        "pwm_out"
      ],
      "source_ref": "cycle_model.pipeline.S1_COMPARE_OUTPUT",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0062"
    },
    {
      "category": "fsm.state",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 1,
      "required_terms": [
        "IDLE"
      ],
      "source_ref": "fsm.pwm_fsm.states.state_0",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0066"
    },
    {
      "category": "fsm.state",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 1,
      "required_terms": [
        "RUNNING"
      ],
      "source_ref": "fsm.pwm_fsm.states.state_1",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0067"
    },
    {
      "category": "fsm.transition",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "IDLE",
        "RUNNING"
      ],
      "source_ref": "fsm.pwm_fsm.transitions.transition_0",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0068"
    },
    {
      "category": "fsm.transition",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 2,
      "required_terms": [
        "IDLE",
        "RUNNING"
      ],
      "source_ref": "fsm.pwm_fsm.transitions.transition_1",
      "source_scope": "rtl/simple_pwm.sv",
      "task_id": "RTL-0069"
    },
    {
      "category": "features.item",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/simple_pwm.sv",
      "required_match_count": 1,
      "required_terms": [
        "duty",
        "duty_cycle
... <truncated 540 chars>

Current RTL file snapshots for gate/tool-evidence repair:
<included only for gate/tool-evidence packets>

Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__simple_pwm__function_model.json):
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
      "count": 14,
      "enabled": true,
      "index": 5,
      "key": "function_model",
      "module_task_count": 70,
      "rule": "Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "function_model",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/simple_pwm.sv",
      "name": "simple_pwm",
      "refs": [
        "top_module",
        "function_model",
        "cycle_model"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/simple_pwm.sv",
        "name": "simple_pwm",
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
          "enable",
          "pwm_control_enable"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "enable",
        "source_ref": "io_list.interfaces[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "duty_cycle",
          "pwm_control_duty_cycle"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "duty_cycle",
        "source_ref": "io_list.interfaces[0].ports[1]",
        "width": "COUNTER_WIDTH"
      },
      {
        "aliases": [
          "period",
          "pwm_control_period"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "period",
        "source_ref": "io_list.interfaces[0].ports[2]",
        "width": "COUNTER_WIDTH"
      },
      {
        "aliases": [
          "pwm_out",
          "pwm_output_pwm_out"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "pwm_out",
        "source_ref": "io_list.interfaces[1].ports[0]",
        "width": "1"
      }
    ],
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
    "llm_actionable_open_count": 28,
    "open_required_count": 28,
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
  "ip": "simple_pwm",
  "kind": "module",
  "owner_file": "rtl/simple_pwm.sv",
  "owner_module": "simple_pwm",
  "packet_id": "module__simple_pwm__function_model",
  "rules": [
    "No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.",
    "Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.",
    "Every task must satisfy content, detail, and criteria before the packet is closed.",
    "For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.",
    "Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.",
    "Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.",
    "Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json."
  ],
  "schema_version": 1,
  "source_plan": "rtl/rtl_todo_plan.json",
  "summary": {
    "categories": {
      "function_model.input": 4,
      "function_model.invariant": 3,
      "function_model.output": 3,
      "function_model.output_rule": 3,
      "function_model.precondition": 5,
      "function_model.side_effect": 3,
      "function_model.state_update": 3,
      "function_model.state_variable": 1,
      "function_model.transaction": 3
    },
    "module_slice": {
      "count": 14,
      "enabled": true,
      "index": 5,
      "key": "function_model",
      "module_task_count": 70,
      "rule": "Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "function_model",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 28,
    "required_count": 28,
    "source_refs": [
      "function_model.state_variables.counter",
      "function_model.transactions.FM1",
      "function_model.transactions.FM1.preconditions.precondition_0",
      "function_model.transactions.FM1.preconditions.precondition_1",
      "function_model.transactions.FM1.inputs.input_0",
      "function_model.transactions.FM1.inputs.input_1",
      "function_model.transactions.FM1.outputs.pwm_out",
      "function_model.transactions.FM1.output_rules.pwm_out_high",
      "function_model.transactions.FM1.state_updates.counter_next",
      "function_model.transactions.FM1.side_effects.side_effect_0",
      "function_model.transactions.FM2",
      "function_model.transactions.FM2.preconditions.precondition_0",
      "function_model.transactions.FM2.preconditions.precondition_1",
      "function_model.transactions.FM2.inputs.input_0",
      "function_model.transactions.FM2.inputs.input_1",
      "function_model.transactions.FM2.outputs.pwm_out",
      "function_model.transactions.FM2.output_rules.pwm_out_low",
      "function_model.transactions.FM2.state_updates.counter_next",
      "function_model.transactions.FM2.side_effects.side_effect_0",
      "function_model.transactions.FM3",
      "function_model.transactions.FM3.preconditions.precondition_0",
      "function_model.transactions.FM3.outputs.pwm_out",
      "function_model.transactions.FM3.output_rules.pwm_out_off",
      "function_model.transactions.FM3.state_updates.counter_next"
    ],
    "status_counts": {
      "open": 28
    },
    "task_count": 28
  },
  "tasks": [
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state counter",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.counter",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "counter reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.counter.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: name=counter; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0029",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.counter",
      "ssot_context": {
        "name": "counter",
        "reset": "0"
      },
      "ssot_refs": [
        "function_model.state_variables.counter"
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
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.transaction",
      "content": "Implement transaction FM1",
      "criteria": [
        "Acceptance/precondition logic is explicit in RTL",
        "All outputs and side effects occur exactly once per accepted transaction",
        "The transaction is covered by equivalence goals and scoreboard observations downstream",
        "Traceability keeps source_ref function_model.transactions.FM1",
        "Primary implementation evidence is in rtl/simple_pwm.sv"
      ],
      "detail": "Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.\nSSOT ref: function_model.transactions.FM1.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM1; name=pwm_active_high.",
      "evidence_terms": [],
      "id": "RTL-0030",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1",
      "ssot_context": {
        "id": "FM1",
        "name": "pwm_active_high"
      },
      "ssot_refs": [
        "function_model.transactions.FM1"
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
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.precondition",
      "content": "Implement precondition for FM1: precondition_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0",
        "Primary implementation evidence is in rtl/simple_pwm.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM1.preconditions.precondition_0.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: value=enable == 1.",
      "evidence_terms": [],
      "id": "RTL-0031",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1.preconditions.precondition_0",
      "ssot_context": {
        "value": "enable == 1"
      },
      "ssot_refs": [
        "function_model.transactions.FM1.preconditions.precondition_0"
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
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.precondition",
      "content": "Implement precondition for FM1: precondition_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_1",
        "Primary implementation evidence is in rtl/simple_pwm.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM1.preconditions.precondition_1.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: value=counter < duty_cycle.",
      "evidence_terms": [
        "duty",
        "duty_cycle"
      ],
      "id": "RTL-0032",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1.preconditions.precondition_1",
      "ssot_context": {
        "value": "counter < duty_cycle"
      },
      "ssot_refs": [
        "function_model.transactions.FM1.preconditions.precondition_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "duty",
          "duty_cycle"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.input",
      "content": "Implement input for FM1: input_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM1.inputs.input_0",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "DUT port [\"pwm_out\"] is the implementation/observation point for pwm_active_high"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM1.inputs.input_0.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM1; name=pwm_active_high; port=[\"pwm_out\"]; signal=[\"duty_cycle\"]; state=[\"counter_next\"].",
      "evidence_terms": [
        "counter_next",
        "duty",
        "duty_cycle",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "id": "RTL-0033",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1.inputs.input_0",
      "ssot_context": {
        "id": "FM1",
        "name": "pwm_active_high",
        "port": "[\"pwm_out\"]",
        "signal": "[\"duty_cycle\"]",
        "state": "[\"counter_next\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM1.inputs.input_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "duty",
          "duty_cycle",
          "next",
          "out",
          "pwm",
          "pwm_out"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.input",
      "content": "Implement input for FM1: input_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM1.inputs.input_1",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "DUT port [\"pwm_out\"] is the implementation/observation point for pwm_active_high"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM1.inputs.input_1.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM1; name=pwm_active_high; port=[\"pwm_out\"]; signal=[\"period\"]; state=[\"counter_next\"].",
      "evidence_terms": [
        "counter_next",
        "next",
        "out",
        "period",
        "pwm",
        "pwm_out"
      ],
      "id": "RTL-0034",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1.inputs.input_1",
      "ssot_context": {
        "id": "FM1",
        "name": "pwm_active_high",
        "port": "[\"pwm_out\"]",
        "signal": "[\"period\"]",
        "state": "[\"counter_next\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM1.inputs.input_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "next",
          "out",
          "period",
          "pwm",
          "pwm_out"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output",
      "content": "Implement output for FM1: pwm_out",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM1.outputs.pwm_out",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "DUT port [\"pwm_out\"] is the implementation/observation point for pwm_active_high"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM1.outputs.pwm_out.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM1; name=pwm_active_high; port=[\"pwm_out\"]; signal=[{\"name\": \"pwm_out\", \"value\": 1}]; state=[\"counter_next\"].",
      "evidence_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "id": "RTL-0035",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1.outputs.pwm_out",
      "ssot_context": {
        "id": "FM1",
        "name": "pwm_active_high",
        "port": "[\"pwm_out\"]",
        "signal": "[{\"name\": \"pwm_out\", \"value\": 1}]",
        "state": "[\"counter_next\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM1.outputs.pwm_out"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "next",
          "out",
          "pwm",
          "pwm_out"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output_rule",
      "content": "Implement output rule for FM1: pwm_out_high",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM1.output_rules.pwm_out_high",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "pwm_out_high width matches SSOT value 1",
        "pwm_out_high RTL expression implements SSOT expression 1",
        "DUT port pwm_out is the implementation/observation point for pwm_out_high",
        "pwm_out_high is not implemented only in FunctionalModel or scoreboard code"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM1.output_rules.pwm_out_high.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: name=pwm_out_high; port=pwm_out; expr=1; width=1.",
      "evidence_terms": [
        "high",
        "out",
        "pwm",
        "pwm_out",
        "pwm_out_high"
      ],
      "id": "RTL-0036",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1.output_rules.pwm_out_high",
      "ssot_context": {
        "expr": "1",
        "name": "pwm_out_high",
        "port": "pwm_out",
        "width": "1"
      },
      "ssot_refs": [
        "function_model.transactions.FM1.output_rules.pwm_out_high"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "high",
          "out",
          "pwm",
          "pwm_out",
          "pwm_out_high"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.state_update",
      "content": "Implement state update for FM1: counter_next",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM1.state_updates.counter_next",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "counter_next width matches SSOT value COUNTER_WIDTH",
        "counter_next RTL expression implements SSOT expression counter + 1 if (counter + 1) < period else 0",
        "counter_next updates exactly once at the SSOT-defined transaction acceptance point"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM1.state_updates.counter_next.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: name=counter_next; expr=counter + 1 if (counter + 1) < period else 0; width=COUNTER_WIDTH.",
      "evidence_terms": [
        "counter_next",
        "next"
      ],
      "id": "RTL-0037",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1.state_updates.counter_next",
      "ssot_context": {
        "expr": "counter + 1 if (counter + 1) < period else 0",
        "name": "counter_next",
        "width": "COUNTER_WIDTH"
      },
      "ssot_refs": [
        "function_model.transactions.FM1.state_updates.counter_next"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "next"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM1: side_effect_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "DUT port [\"pwm_out\"] is the implementation/observation point for pwm_active_high"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM1; name=pwm_active_high; port=[\"pwm_out\"]; signal=[\"counter increments by 1\"]; state=[\"counter_next\"].",
      "evidence_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "id": "RTL-0038",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM1.side_effects.side_effect_0",
      "ssot_context": {
        "id": "FM1",
        "name": "pwm_active_high",
        "port": "[\"pwm_out\"]",
        "signal": "[\"counter increments by 1\"]",
        "state": "[\"counter_next\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM1.side_effects.side_effect_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "next",
          "out",
          "pwm",
          "pwm_out"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.transaction",
      "content": "Implement transaction FM2",
      "criteria": [
        "Acceptance/precondition logic is explicit in RTL",
        "All outputs and side effects occur exactly once per accepted transaction",
        "The transaction is covered by equivalence goals and scoreboard observations downstream",
        "Traceability keeps source_ref function_model.transactions.FM2",
        "Primary implementation evidence is in rtl/simple_pwm.sv"
      ],
      "detail": "Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.\nSSOT ref: function_model.transactions.FM2.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM2; name=pwm_active_low.",
      "evidence_terms": [],
      "id": "RTL-0039",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2",
      "ssot_context": {
        "id": "FM2",
        "name": "pwm_active_low"
      },
      "ssot_refs": [
        "function_model.transactions.FM2"
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
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.precondition",
      "content": "Implement precondition for FM2: precondition_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0",
        "Primary implementation evidence is in rtl/simple_pwm.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM2.preconditions.precondition_0.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: value=enable == 1.",
      "evidence_terms": [],
      "id": "RTL-0040",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2.preconditions.precondition_0",
      "ssot_context": {
        "value": "enable == 1"
      },
      "ssot_refs": [
        "function_model.transactions.FM2.preconditions.precondition_0"
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
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.precondition",
      "content": "Implement precondition for FM2: precondition_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_1",
        "Primary implementation evidence is in rtl/simple_pwm.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM2.preconditions.precondition_1.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: value=counter >= duty_cycle.",
      "evidence_terms": [
        "duty",
        "duty_cycle"
      ],
      "id": "RTL-0041",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2.preconditions.precondition_1",
      "ssot_context": {
        "value": "counter >= duty_cycle"
      },
      "ssot_refs": [
        "function_model.transactions.FM2.preconditions.precondition_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "duty",
          "duty_cycle"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.input",
      "content": "Implement input for FM2: input_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM2.inputs.input_0",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "DUT port [\"pwm_out\"] is the implementation/observation point for pwm_active_low"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM2.inputs.input_0.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM2; name=pwm_active_low; port=[\"pwm_out\"]; signal=[\"duty_cycle\"]; state=[\"counter_next\"].",
      "evidence_terms": [
        "counter_next",
        "duty",
        "duty_cycle",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "id": "RTL-0042",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2.inputs.input_0",
      "ssot_context": {
        "id": "FM2",
        "name": "pwm_active_low",
        "port": "[\"pwm_out\"]",
        "signal": "[\"duty_cycle\"]",
        "state": "[\"counter_next\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM2.inputs.input_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "duty",
          "duty_cycle",
          "next",
          "out",
          "pwm",
          "pwm_out"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.input",
      "content": "Implement input for FM2: input_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM2.inputs.input_1",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "DUT port [\"pwm_out\"] is the implementation/observation point for pwm_active_low"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM2.inputs.input_1.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM2; name=pwm_active_low; port=[\"pwm_out\"]; signal=[\"period\"]; state=[\"counter_next\"].",
      "evidence_terms": [
        "counter_next",
        "next",
        "out",
        "period",
        "pwm",
        "pwm_out"
      ],
      "id": "RTL-0043",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2.inputs.input_1",
      "ssot_context": {
        "id": "FM2",
        "name": "pwm_active_low",
        "port": "[\"pwm_out\"]",
        "signal": "[\"period\"]",
        "state": "[\"counter_next\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM2.inputs.input_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "next",
          "out",
          "period",
          "pwm",
          "pwm_out"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output",
      "content": "Implement output for FM2: pwm_out",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM2.outputs.pwm_out",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "DUT port [\"pwm_out\"] is the implementation/observation point for pwm_active_low"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM2.outputs.pwm_out.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM2; name=pwm_active_low; port=[\"pwm_out\"]; signal=[{\"name\": \"pwm_out\", \"value\": 0}]; state=[\"counter_next\"].",
      "evidence_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "id": "RTL-0044",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2.outputs.pwm_out",
      "ssot_context": {
        "id": "FM2",
        "name": "pwm_active_low",
        "port": "[\"pwm_out\"]",
        "signal": "[{\"name\": \"pwm_out\", \"value\": 0}]",
        "state": "[\"counter_next\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM2.outputs.pwm_out"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "next",
          "out",
          "pwm",
          "pwm_out"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output_rule",
      "content": "Implement output rule for FM2: pwm_out_low",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM2.output_rules.pwm_out_low",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "pwm_out_low width matches SSOT value 1",
        "pwm_out_low RTL expression implements SSOT expression 0",
        "DUT port pwm_out is the implementation/observation point for pwm_out_low",
        "pwm_out_low is not implemented only in FunctionalModel or scoreboard code"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM2.output_rules.pwm_out_low.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: name=pwm_out_low; port=pwm_out; expr=0; width=1.",
      "evidence_terms": [
        "low",
        "out",
        "pwm",
        "pwm_out",
        "pwm_out_low"
      ],
      "id": "RTL-0045",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2.output_rules.pwm_out_low",
      "ssot_context": {
        "expr": "0",
        "name": "pwm_out_low",
        "port": "pwm_out",
        "width": "1"
      },
      "ssot_refs": [
        "function_model.transactions.FM2.output_rules.pwm_out_low"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "low",
          "out",
          "pwm",
          "pwm_out",
          "pwm_out_low"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.state_update",
      "content": "Implement state update for FM2: counter_next",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM2.state_updates.counter_next",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "counter_next width matches SSOT value COUNTER_WIDTH",
        "counter_next RTL expression implements SSOT expression counter + 1 if (counter + 1) < period else 0",
        "counter_next updates exactly once at the SSOT-defined transaction acceptance point"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM2.state_updates.counter_next.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: name=counter_next; expr=counter + 1 if (counter + 1) < period else 0; width=COUNTER_WIDTH.",
      "evidence_terms": [
        "counter_next",
        "next"
      ],
      "id": "RTL-0046",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2.state_updates.counter_next",
      "ssot_context": {
        "expr": "counter + 1 if (counter + 1) < period else 0",
        "name": "counter_next",
        "width": "COUNTER_WIDTH"
      },
      "ssot_refs": [
        "function_model.transactions.FM2.state_updates.counter_next"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "counter_next",
          "next"
        ],
        "source_scope": "rtl/simple_pwm.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/simple_pwm.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM2: side_effect_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_0",
        "Primary implementation evidence is in rtl/simple_pwm.sv",
        "DUT port [\"pwm_out\"] is the implementation/observation point for pwm_active_low"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM2.side_effects.side_effect_0.\nOwner: simple_pwm in rtl/simple_pwm.sv via function_model.\nSSOT item context: id=FM2; name=pwm_active_low; port=[\"pwm_out\"]; signal=[\"counter increments by 1\"]; state=[\"counter_next\"].",
      "evidence_terms": [
        "counter_next",
        "next",
        "out",
        "pwm",
        "pwm_out"
      ],
      "id": "RTL-0047",
      "owner_file": "rtl/simple_pwm.sv",
      "owner_module": "simple_pwm",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM2.side_effects.side_effect_0",
      "ssot_context": {
        "id": "FM2",
        "name": "pwm_active_low",
        "port": "[\"pwm_out\"]",
        "signal": "[\"counter increments by 1\"]",
        "state": "[\"counter_next\"]"
      },
      "ssot_refs": [
       
... <truncated 21714 chars>

Current packet Markdown (rtl/authoring_packets/module__simple_pwm__function_model.md):
# RTL Authoring Packet: module__simple_pwm__function_model

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
- Task count: 28
- Required tasks: 28

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
- LLM-actionable open tasks: 28
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 5/14 section=function_model task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0029: Implement RTL state owner for FL state counter

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.counter
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.counter.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=counter; reset=0.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.counter
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - counter reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.counter

### RTL-0030: Implement transaction FM1

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM1

### RTL-0031: Implement precondition for FM1: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=enable == 1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_0

### RTL-0032: Implement precondition for FM1: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=counter < duty_cycle.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_1

### RTL-0033: Implement input for FM1: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high; port=["pwm_out"]; signal=["duty_cycle"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_high
- SSOT refs: function_model.transactions.FM1.inputs.input_0

### RTL-0034: Implement input for FM1: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high; port=["pwm_out"]; signal=["period"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_high
- SSOT refs: function_model.transactions.FM1.inputs.input_1

### RTL-0035: Implement output for FM1: pwm_out

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.pwm_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.pwm_out.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high; port=["pwm_out"]; signal=[{"name": "pwm_out", "value": 1}]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.pwm_out
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_high
- SSOT refs: function_model.transactions.FM1.outputs.pwm_out

### RTL-0036: Implement output rule for FM1: pwm_out_high

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.pwm_out_high
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.pwm_out_high.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=pwm_out_high; port=pwm_out; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.pwm_out_high
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - pwm_out_high width matches SSOT value 1
  - pwm_out_high RTL expression implements SSOT expression 1
  - DUT port pwm_out is the implementation/observation point for pwm_out_high
  - pwm_out_high is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.pwm_out_high

### RTL-0037: Implement state update for FM1: counter_next

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM1.state_updates.counter_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.state_updates.counter_next.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=counter_next; expr=counter + 1 if (counter + 1) < period else 0; width=COUNTER_WIDTH.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.state_updates.counter_next
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - counter_next width matches SSOT value COUNTER_WIDTH
  - counter_next RTL expression implements SSOT expression counter + 1 if (counter + 1) < period else 0
  - counter_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM1.state_updates.counter_next

### RTL-0038: Implement side effect for FM1: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high; port=["pwm_out"]; signal=["counter increments by 1"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_high
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_0

### RTL-0039: Implement transaction FM2

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM2; name=pwm_active_low.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM2

### RTL-0040: Implement precondition for FM2: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=enable == 1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_0

### RTL-0041: Implement precondition for FM2: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=counter >= duty_cycle.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_1

### RTL-0042: Implement input for FM2: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_0.
Owner: simple_pwm in rtl/simple_pwm.s
... <truncated 16828 chars>