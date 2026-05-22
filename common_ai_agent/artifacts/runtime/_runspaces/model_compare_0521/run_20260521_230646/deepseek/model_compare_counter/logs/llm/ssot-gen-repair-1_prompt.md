Repair the SSOT YAML artifact for model_compare_counter. This is repair attempt 1.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "model_compare_counter/yaml/model_compare_counter.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}
  ]
}

Repair rules:
- Do not use a fixed IP template or hardcoded workaround.
- Preserve product semantics from the requirement and current SSOT wherever they are valid.
- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.
- Fix the concrete parse/validator failures below, and also check for sibling contract defects.
- The repaired YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh model_compare_counter --mode engineering`.
- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.

Failure summary:
human_gate: while parsing a block mapping
  in "<unicode string>", line 120, column 7:
        - stage: "S0_UPDATE", cycle: 0, ac ... 
          ^
expected <block end>, but found ','
  in "<unicode string>", line 120, column 25:
        - stage: "S0_UPDATE", cycle: 0, action: "On rising e ... 
                            ^

Blocker artifact:


Validator log:


Requirements:
# model_compare_counter Requirements

Create a small synthesizable hardware IP named `model_compare_counter`.

The block has one clock `clk` and active-low reset `rst_n`. It exposes:

- `enable` input, 1 bit.
- `clear` input, 1 bit.
- `step` input, 4 bits.
- `count` output, 8 bits.
- `wrapped` output, 1 bit.
- `valid` output, 1 bit.

Behavior:

- On reset, `count`, `wrapped`, and `valid` are zero.
- `clear` has priority over `enable`.
- When `clear` is high, `count`, `wrapped`, and `valid` become zero on the next clock.
- When `enable` is high and `clear` is low, add `step` to `count` on the next clock.
- The addition wraps modulo 256.
- `wrapped` is asserted for one cycle when the addition overflows 8 bits.
- `valid` is asserted for one cycle when an enabled update is accepted.
- When neither clear nor enable is high, hold `count`; deassert `wrapped` and `valid`.

Cycle model:

- Single-cycle accept/update/observe behavior.
- Inputs are sampled on the rising edge.
- Outputs reflect the registered state after that edge.
- Clear priority must be visible in the cycle model.
- Backpressure is not required.

Verification scenarios:

- Reset state.
- Clear priority over enable.
- Increment without overflow.
- Increment with overflow.
- Hold when idle.
- Multiple sequential updates.

Quality requirements:

- Generate SSOT, functional model, cycle model, equivalence goals, RTL, lint evidence, cocotb/pyuvm testbench, simulation evidence, coverage, sim-debug evidence, and final goal audit.
- RTL must compile and lint clean with no warnings.
- Functional coverage and equivalence coverage must include the cycle model and the scenarios above.


Current SSOT YAML:
top_module:
  name: "model_compare_counter"
  file: "rtl/model_compare_counter.sv"
  version: "1.0"
  type: "datapath"
  description: "Synchronous 8-bit counter with enable, clear, step input, overflow detection, and valid output."
  reference_spec: null
  target:
    technology: "generic"
    clock_freq_mhz: 100
    area_um2: null
    power_mw: null

sub_modules: []

parameters: []

io_list:
  clock_domains:
    - name: "clk"
      frequency_mhz: 100
      description: "main clock"
      ports:
        - { name: "clk", width: 1, direction: "input", description: "Clock input" }
  resets:
    - name: "rst_n"
      polarity: "active_low"
      sync_async: "async_assert_sync_deassert"
      description: "Active-low reset"
      ports:
        - { name: "rst_n", width: 1, direction: "input", description: "Active-low reset" }
  interfaces:
    - name: "cnt_if"
      type: "custom"
      description: "Counter control and status interface"
      ports:
        - { name: "enable", width: 1, direction: "input", description: "Enable signal" }
        - { name: "clear", width: 1, direction: "input", description: "Clear signal (priority)" }
        - { name: "step", width: 4, direction: "input", description: "Increment amount" }
        - { name: "count", width: 8, direction: "output", description: "Current counter value" }
        - { name: "wrapped", width: 1, direction: "output", description: "Wrap occurred on last update" }
        - { name: "valid", width: 1, direction: "output", description: "Update accepted this cycle" }

features:
  - name: "Synchronous Increment"
    trigger: "enable asserted, clear low"
    datapath: "add step to count modulo 256, detect overflow, set valid and wrapped"
    control: "priority: clear overrides enable"
    output: "count updated, valid=1, wrapped=1 if overflow"
  - name: "Clear"
    trigger: "clear asserted"
    datapath: "set count=0, valid=0, wrapped=0"
    control: "Combinationally overrides enable"
    output: "count=0 next cycle"

dataflow:
  read_path:
    source: "step input"
    sequence: "step -> adder (with current count) -> count register"
  write_path:
    destination: "count output"
    sequence: "count register reflected on output"
  control_flow:
    priority: "clear > enable"
    idle: "no update, outputs=0 (valid, wrapped) unless count stable"

function_model:
  purpose: "Describe the counter's pure functional behavior independent of timing."
  state_variables:
    - { name: "count", reset: 0, description: "Counter value (8-bit, modulo 256)" }
  transactions:
    - id: "FM_CLEAR"
      name: "Clear"
      preconditions:
        - "clear == 1"
      outputs:
        - "count = 0"
        - "valid = 0"
        - "wrapped = 0"
      side_effects:
        - "count <= 0"
      error_cases: []
    - id: "FM_INCREMENT"
      name: "Increment"
      preconditions:
        - "enable == 1"
        - "clear == 0"
      outputs:
        - "count = (count + step) % 256"
        - "valid = 1"
        - "wrapped = 1 if (count + step) >= 256 else 0"
      side_effects:
        - "count <= (count + step) % 256"
      error_cases: []
    - id: "FM_IDLE"
      name: "Idle"
      preconditions: []
      outputs:
        - "count = count"
        - "valid = 0"
        - "wrapped = 0"
      side_effects: []
      error_cases: []
  invariants:
    - "Clear overrides enable: When clear=1, outputs reflect clear, not increment."
    - "Valid and wrapped are asserted for one cycle after an enabled update."
    - "Counter wraps modulo 256."

cycle_model:
  purpose: "Clock-cycle timing contract for RTL generation and verification."
  clock: "clk"
  reset:
    assertion: "rst_n low clears count to 0 and resets valid/wrapped to 0."
    deassertion: "state is usable on first rising edge after synchronized deassertion."
  latency:
    update: { min_cycles: 1, max_cycles: 1, description: "All outputs reflect the new state one cycle after input change." }
  handshake_rules:
    - "No handshake: inputs are accepted every clock cycle; outputs always valid after one cycle."
  pipeline:
    - stage: "S0_UPDATE", cycle: 0, action: "On rising edge, evaluate clear>enable priority, compute next count and outputs; present on next cycle."
  ordering:
    - "Clear is evaluated before enable."
  backpressure: "None; no ready/valid handshake."

clock_reset_domains:
  domains:
    - { name: "clk", frequency_mhz: 100, description: "Main clock" }
  reset_scheme:
    signal: "rst_n"
    polarity: "active_low"
    type: "async_assert_sync_deassert"

cdc_requirements:
  crossings: []
  synchronizers: []
  note: "Single clock domain; no CDC required."

rdc_requirements:
  crossings: []
  synchronizers: []
  note: "No reset domain crossings."

registers:
  config:
    register_width: null
    addr_width: null
    byte_addressable: false
  register_list: []
  note: "No programmable registers; control via input ports."

memory:
  instances: []
  note: "No internal memories."

interrupts:
  sources: []
  output:
    signal: null
    polarity: null
    type: null
  note: "No interrupts."

fsm: null

timing:
  target_clocks:
    - { name: "clk", period_ns: 10, uncertainty: 0.1 }
  latency_budget:
    input_to_output: { min_ns: 0, max_ns: 10 }
    note: "Simple sequential path; 10ns period assumed."

power:
  domains:
    - { name: "main", vdd: 1.2, description: "Core power domain" }
  clock_gating: []
  retention: []
  upf: null
  power_states:
    - { name: "active", power_mw: 0.1, description: "Normal operation" }
    - { name: "idle", power_mw: 0.01, description: "Clock stopped but state retained" }
  note: "Power estimates are placeholders."

security:
  classification: "low"
  assets:
    - { name: "counter_data", type: "data", confidentiality: "low", integrity: "medium", availability: "high" }
  threat_model:
    - { threat: "None", likelihood: "negligible", impact: "none", mitigation: "not applicable" }
  note: "No security requirements."

error_handling:
  error_sources: []
  propagation: "none"
  recovery: "none"
  note: "No error conditions defined."

debug_observability:
  waveform_must_probe:
    - "clk"
    - "rst_n"
    - "enable"
    - "clear"
    - "step"
    - "count"
    - "wrapped"
    - "valid"
  trace_events:
    - "count_update"
    - "clear"
    - "wrap"
  note: "All primary I/O should be probeable."

integration:
  bus_attachment: "none"
  dependencies: []
  connections: []
  note: "Standalone IP, no bus attachment required."

dft:
  scan_required: false
  controllability: "limited"
  observability: "all primary outputs are observable"
  note: "No scan chain insertion; functional test only."

synthesis:
  dialect: "systemverilog_2012"
  constraints:
    - "create_clock -period 10.0 [get_ports clk]"
    - "set_input_delay 2.0 -clock clk [all_inputs]"
    - "set_output_delay 2.0 -clock clk [all_outputs]"
  ppa_targets: { area_um2: 100, power_mw: 1.0 }
  required_outputs:
    - "mapped netlist"
    - "timing report"
    - "area report"
  note: "Standard synthesis assumptions."

coding_rules:
  verilog_style: "systemverilog_2012"
  file_extension: ".sv"
  parameter_header: null
  conventions:
    - "Use sequential always @(posedge clk or negedge rst_n)"
    - "Nonblocking assignments for registered outputs"
    - "Combinational next-state logic outside always block"
    - "No latches"
  lint_waivers: []

reuse_modules: []

custom:
  note: "No custom extensions."

dir_structure:
  template_dirs:
    rtl: "templates/rtl/"
    sim: "templates/sim/"
  output_dirs:
    rtl: "rtl/"
    sim: "sim/"
    firmware: "firmware/"
    docs: "docs/"
  yaml_dir: "yaml/"
  generators_dir: "generators/"

filelist:
  headers: []
  rtl:
    - "rtl/model_compare_counter.sv"
  sim:
    - "sim/tb_model_compare_counter.sv"
  firmware: []
  docs:
    - "docs/model_compare_counter.md"

rtl_contract:
  top_module: "model_compare_counter"
  file: "rtl/model_compare_counter.sv"
  description: "Simple synchronous counter with clear and enable."
  handshake: false
  pipeline: false
  note: "No internal submodules; single file."

test_requirements:
  scenarios:
    - id: "SC1"
      name: "Reset state"
      stimulus: "Apply reset (rst_n low) for several cycles, then release."
      expected: "count=0, wrapped=0, valid=0 after reset deassertion."
      checker: "Check outputs match expected state."
      coverage: ["reset"]
    - id: "SC2"
      name: "Clear priority over enable"
      stimulus: "Drive enable=1, clear=1 simultaneously."
      expected: "count=0, valid=0, wrapped=0 regardless of enable."
      checker: "Assert clear takes precedence."
      coverage: ["clear_priority"]
    - id: "SC3"
      name: "Increment without overflow"
      stimulus: "Set enable=1, clear=0, step=3, count initially 10. Drive for 2 cycles."
      expected: "count becomes 13 then 16; valid=1 each cycle; wrapped=0."
      checker: "Scoreboard checks sequence."
      coverage: ["increment"]
    - id: "SC4"
      name: "Increment with overflow"
      stimulus: "Set enable=1, clear=0, step=5, count=252. Drive 2 cycles: 252+5=257%256=1, wrapped=1; next count=6, wrapped=0."
      expected: "Sequence: count=252, enable, next count=1, wrapped=1; next count=6, wrapped=0."
      checker: "Assert wrapped asserted on overflow cycle only."
      coverage: ["overflow"]
    - id: "SC5"
      name: "Hold when idle"
      stimulus: "Set enable=0, clear=0 after some count=100."
      expected: "count stays 100, valid=0, wrapped=0."
      checker: "Check outputs remain stable."
      coverage: ["idle"]
    - id: "SC6"
      name: "Multiple sequential updates"
      stimulus: "Sequence: enable=1 step=10 for 5 cycles, then enable=0, then enable=1 step=7 for 3 cycles."
      expected: "count increments accordingly with wrap detection."
      checker: "Scoreboard tracks expected count through sequence."
      coverage: ["sequential"]
  scoreboard_checks: 6
  coverage_goals:
    function:
      target_pct: 100
      model: "function_model"
      description: "Functional coverage for counter operations."
      bins:
        - { id: "FCOV_CLEAR", source_ref: "function_model.transactions.FM_CLEAR", class: "transaction", description: "Clear operation observed." }
        - { id: "FCOV_INCREMENT", source_ref: "function_model.transactions.FM_INCREMENT", class: "transaction", description: "Increment operation observed." }
        - { id: "FCOV_IDLE", source_ref: "function_model.transactions.FM_IDLE", class: "transaction", description: "Idle operation observed." }
    cycle:
      target_pct: 100
      model: "cycle_model"
      description: "Cycle/handshake coverage."
      bins:
        - { id: "CCOV_UPDATE_STAGE", source_ref: "cycle_model.pipeline", class: "pipeline_stage", description: "Update stage observed." }
    functional: "Legacy alias"
    code: "line >= 90%, branch >= 85%"

quality_gates:
  ssot:
    pass: "SSOT validated by verify_ssot.py."
    evidence: ["req/ssot_validation.json"]
  rtl:
    pass: "RTL compiles and lints clean."
    evidence: ["rtl compile report", "lint report"]
  dv:
    pass: "All test scenarios pass with scoreboard checks."
    evidence: ["sim results", "coverage report"]
  coverage:
    pass: "Functional and code coverage targets met."
    evidence: ["coverage.json"]
  eda:
    pass: "Synthesis meets area/power targets (placeholder)."
    evidence: ["syn report"]
  signoff:
    pass: "All gates met."
    evidence: ["signoff checklist"]
  rtl_gen:
    profile: "standard"
    pass: "RTL generated from SSOT and passes compile/lint."
    evidence: ["rtl/rtl_gen_evidence.txt"]

traceability:
  yaml_to_output:
    - { yaml: "top_module.name", output: "ALL files (module name)" }
    - { yaml: "io_list.interfaces", output: "rtl/model_compare_counter.sv (port list)" }
    - { yaml: "function_model", output: "<ip>_core.sv + tb scoreboard/reference model" }
    - { yaml: "cycle_model", output: "<ip>_core.sv pipeline/handshake logic + waveform checks" }
    - { yaml: "test_requirements.scenarios", output: "sim/tb_model_compare_counter.sv" }

workflow_todos:
  fl-model-gen: []
  rtl-gen:
    - id: "RTL_TODO_COUNTER_TOP"
      content: "Implement the model_compare_counter top module with counter behavior."
      detail: "Use sequential always block with async reset (active low). Priority: if clear then count=0, valid=0, wrapped=0; else if enable then count <= (count + step) % 256, valid <= 1, wrapped <= (count + step >= 256); else count unchanged, valid=0, wrapped=0."
      criteria:
        - "RTL compiles and lints clean"
        - "Behavior matches function_model for all scenarios"
        - "Timing meets 10ns clock period"
      source_refs: ["function_model", "cycle_model", "io_list"]
      priority: "high"
      required: true
      owner_module: "model_compare_counter"
      owner_file: "rtl/model_compare_counter.sv"
  tb-gen: []
  sim_debug: []
  coverage: []
  syn: []
  pnr: []
  sta: []
  sta-post: []

generation_flow:
  steps:
    - { name: "verify_ssot", command: "python3 workflow/ssot-gen/scripts/verify_ssot.py model_compare_counter --mode engineering", description: "Validate production SSOT structure" }
    - { name: "handoff_rtl", command: "/ssot-rtl model_compare_counter", description: "Downstream RTL generation from validated SSOT" }
    - { name: "handoff_tb", command: "/ssot-tb model_compare_counter", description: "Downstream testbench generation" }
    - { name: "handoff_sim", command: "/wf sim", description: "Simulation" }
    - { name: "handoff_coverage", command: "/coverage model_compare_counter", description: "Coverage measurement" }