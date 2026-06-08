RTL-GEN PACKET MODE for timer. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "timer/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "timer/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "timer/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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

Current packet: rtl_gate_evidence_closure
kind: gate
work queue: 1/1 active packets (2 closed packets skipped from 5 total)
batch limit: 1; deferred active packets after this batch: 2
owner_module: timer
owner_file: rtl/timer.sv

SSOT observable latency contract:
{
  "cycle_model.latency": 1,
  "cycle_model.pipeline": [
    {
      "action": "Sample data_in when valid is high.",
      "cycle": 0,
      "stage": "S0_SAMPLE"
    },
    {
      "action": "Drive result and result_valid for the sampled value.",
      "cycle": 1,
      "stage": "S1_RESULT"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": "result_valid",
  "rtl_contract.sample_condition": "valid && ready",
  "timing.latency_budget": {
    "accepted_to_result_valid": {
      "max": 1,
      "min": 1,
      "unit": "cycles"
    }
  }
}

SSOT bus/byte-lane policy:
{
  "guidance": "condition=none means upper byte lanes are not an APB error for legal offsets; consume otherwise-unused pwdata/pstrb upper bits through explicit legal ignore, byte-strobe masking, reserved-zero readback, or coverage/trace behavior while keeping pslverr deasserted for legal writes.",
  "illegal_byte_access_pattern_condition": "<not declared>",
  "upper_byte_lane_error_allowed": false
}

Locked SSOT YAML excerpt (timer/yaml/timer.ssot.yaml):
top_module:
  name: timer
  file: rtl/timer.sv
  description: timer top-level wrapper for the sampled transaction rule.
  type: peripheral
  version: '1.0'
  reference_spec: user-defined
  target:
    technology: generic
    clock_freq_mhz: 100
    area_um2: null
    power_mw: null
sub_modules:
- name: timer
  file: rtl/timer.sv
  ownership: manifest
  wiring_only: true
  implements:
  - io_list
  - integration
  - top_module
  source_sections: &id001
  - io_list
  - integration
  - top_module
  - decomposition
  description: Top wrapper that connects external ports to the SSOT-owned core.
  ssot_gen: true
  decomposition_refs:
  - decomposition
  dataflow_refs:
  - dataflow
- name: timer_core
  file: rtl/timer_core.sv
  ownership: manifest
  implements:
  - function_model.transactions
  - cycle_model
  - rtl_contract
  source_sections:
  - function_model
  - cycle_model
  - rtl_contract
  - fsm
  - dataflow
  - registers
  - features
  - decomposition
  - test_requirements
  function_model_refs:
  - function_model.transactions.FM_PRIMARY
  - function_model.state_variables
  - function_model.invariants
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model
  dataflow_refs:
  - dataflow.sequence
  - dataflow.ordering
  - dataflow
  register_refs:
  - registers.architectural_state.accepted_count
  fsm_refs:
  - fsm.control
  - fsm
  description: Core RTL block implementing the sampled transaction rule.
  feature_refs:
  - features
  decomposition_refs:
  - decomposition
  test_refs:
  - test_requirements
decomposition:
  strategy: manifest_owned_leaf_decomposition
  owners:
  - module: timer
    file: rtl/timer.sv
    responsibility: Top wrapper that connects external ports to the SSOT-owned core.
    source_sections: *id001
  - module: timer_core
    file: rtl/timer_core.sv
    responsibility: Core RTL block implementing the sampled transaction rule.
    source_sections:
    - function_model
    - cycle_model
    - rtl_contract
    - fsm
    - dataflow
    - registers
  integration_policy: Top-level wiring must be backed by integration.connections or sub_modules[].connections before signoff.
  source_refs:
  - sub_modules
  - function_model
  - cycle_model
  - integration
rtl_contract:
  clock: clk
  reset: rst_n
  reset_active: low
  transaction: FM_PRIMARY
  sample_condition: valid && ready
  input_map:
    value: data_in
    data_in: data_in
  output_map:
    result: result
    valid: result_valid
    ready: ready
    result_valid: result_valid
  ready_output: ready
  output_valid: result_valid
  owner: ssot-gen
  type: ssot_derived_rule_contract
  contract_invariants:
  - RTL-visible behavior implements the referenced function_model transaction.
  - Input sampling and output observation follow cycle_model handshake and latency rules.
  output_rules:
  - name: result
    port: result
    expr: value * 2
    width: 9
    description: FunctionalModel output observable mapped to DUT output port.
parameters:
- name: DATA_WIDTH
  default: 8
  type: int
  description: Input data width.
- name: RESULT_WIDTH
  default: 9
  type: int
  description: Output result width.
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
  - name: rule_io
    type: custom
    role: target
    clock_domain: main
    reset_domain: rst_n
    protocol:
      acceptance: A request is accepted when valid && ready is true on clk.
      response: result and result_valid are driven one cycle after the accepted request.
      stability: data_in is sampled only at acceptance; result remains traceable to that sampled value.
    ports:
    - name: valid
      direction: input
      width: 1
      description: Recovered from io_list.interfaces.rule_io.signals
    - name: data_in
      direction: input
      width: 8
      description: Recovered from io_list.interfaces.rule_io.signals
    - name: result
      direction: output
      width: 9
      description: Recovered from io_list.interfaces.rule_io.signals
    - name: ready
      direction: output
      width: 1
      description: Recovered from io_list.interfaces.rule_io.signals
      allow_constant: true
      tieoff: 1'b1
      constant_value: 1'b1
    - name: result_valid
      direction: output
      width: 1
      description: Recovered from io_list.interfaces.rule_io.signals
features:
- name: double_value
  description: Sample data_in when valid is high and produce result=data_in*2 one cycle later.
  requirement_trace: '# Headless Requirement timer is a small ready/valid stream transform IP used to validate the headless workflow. After reset deassertion, it samples data_in only when valid is asserted. The ready output remains high after reset. One cycle af'
dataflow:
  sequence:
  - Sample data_in when valid is asserted after reset release.
  - Compute result as sampled value multiplied by two.
  - Present result and result_valid on the next observable cycle.
  ordering:
  - accepted request precedes result observation
function_model:
  state_variables:
  - name: accepted_count
    width: 8
    reset: 0
  transactions:
  - id: FM_PRIMARY
    name: primary_behavior
    required_fields:
    - value
    preconditions:
    - rst_n is deasserted
    - valid is high
    outputs:
    - result
    - state: accepted_count
      expr: accepted_count + 1
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: result
      port: result
      expr: value * 2
      width: 9
    side_effects:
    - accepted_count increments on each sampled transaction
    state_updates:
    - name: accepted_count
      expr: accepted_count + 1
      width: 8
  invariants:
  - No result is produced before reset is released.
  - Each accepted valid transaction produces exactly one result_valid observation.
  - The result value is derived only from the sampled input transaction.
  reference_model_hint: FunctionalModel.apply(value) returns result=value*2 and increments accepted_count.
cycle_model:
  executable: python
  backend_policy: Use the repo-owned pure-Python deterministic stepper; FunctionalModel remains the behavioral oracle.
  clock: clk
  reset: rst_n
  latency: 1
  handshake_rules:
  - name: valid_sample
    description: data_in is sampled only when valid is high; ready remains high after reset.
  pipeline:
  - stage: S0_SAMPLE
    cycle: 0
    action: Sample data_in when valid is high.
  - stage: S1_RESULT
    cycle: 1
    action: Drive result and result_valid for the sampled value.
  ordering:
  - Transactions are observed in the same order they are sampled.
  - Reset clears pending valid output before any new transaction is accepted.
  backpressure:
  - ready remains asserted in this one-deep sample rule IP.
  performance:
    frequency_mhz: 100
    throughput:
      sustained_beats_per_cycle: 1
      condition: ready remains asserted
    outstanding:
      max: 1
      description: One sampled transaction at a time
    depth:
      pipeline_stages: 2
      queue_depth: 1
      description: Sample/result default cycle depth
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
  no_registers: true
  policy: No firmware-visible CSR/register map is required for this native valid/ready rule IP.
  register_list: []
  architectural_state:
  - name: accepted_count
    reset: 0
    source: function_model.state_variables
memory:
  instances: []
  rationale: No memory required for the one-cycle datapath rule.
interrupts:
  sources: []
  outputs: []
  rationale: No interrupt behavior required for this rule IP.
fsm:
  control:
    states:
    - S0_SAMPLE
    - S1_RESULT
    reset_state: S0_SAMPLE
    transitions:
    - from: S0_SAMPLE
      to: S1_RESULT
      condition: valid
      action: Latch input value.
    - from: S1_RESULT
      to: S0_SAMPLE
      condition: next cycle
      action: Emit result_valid.
timing:
  target_clocks:
  - name: clk
    frequency_mhz: 100
    period_ns: 10.0
  latency_budget:
    accepted_to_result_valid:
      min: 1
      max: 1
      unit: cycles
  sta_expectations:
    setup_wns_ns_min: 0.0
    hold_wns_ns_min: 0.0
    required_reports:
    - sta/out/timing.rpt
    - sta/out/wns.json
power:
  domains:
  - name: PD_MAIN
    clock_domains:
    - main
    isolation: not_required
  power_states:
  - name: 'ON'
    entry: reset deasserted
    exit: reset asserted
  clock_gating:
    required: false
    rationale: No explicit integrated clock-gating requirement in approved SSOT
  upf_required: false
security:
  classification: non_secure_leaf_ip
  assets:
  - name: result_integrity
    protection: result must match function_model output rule
  threat_model:
  - threat: silent datapath corruption
    mitigation: FL-vs-RTL scoreboard checks every result
  privilege_model: System-level access control is owned by the integrating bus/firewall unless explicitly declared here.
error_handling:
  error_sources:
  - id: ERR_NONE
    condition: No protocol error input exists
    architectural_effect: No error output is asserted
  propagation:
  - No error response interface exists for this simple rule IP.
  recovery:
  - action: reset
    clears:
    - accepted_count
    - result_valid
debug_observability:
  waveform_must_probe:
  - clk
  - rst_n
  - valid
  - data_in
  - ready
  - result
  - result_valid
  - accepted_count
  trace_events:
  - name: sample
    trigger: valid && ready
  - name: result
    trigger: result_valid
  status_outputs:
  - status/debug signals declared in io_list or registers
integration:
  bus_attachment:
    type: native_valid_ready_rule_io
    interfaces:
    - rule_io
  dependencies:
    external_modules: []
    external_clocks:
    - clk
    external_resets:
    - rst_n
  connections:
  - module: timer_core
    port: clk
    signal: clk
  - module: timer_core
    port: rst_n
    signal: rst_n
  - module: timer_core
    port: valid
    signal: valid
  - module: timer_core
    port: data_in
    signal: data_in
  - module: timer_core
    port: ready
    signal: ready
  - module: timer_core
    port: result
    signal: result
  - module: timer_core
    port: result_valid
    signal: result_valid
  connection_contract_status: missing machine-readable module wiring; child RTL drafts may proceed from owner packets, but top integration/signoff must stay blocked until SSOT authors integration.connections or sub_modules[].connections with module/port/signal records
  integration_notes:
  - Integrator must connect every declared io_list port and honor timing/reset assumptions.
dft:
  scan_required: false
  controllability:
    reset: rst_n
    clock: clk
    inputs:
    - valid
    - data_in
  observability:
    outputs:
    - ready
    - result
    - result_valid
  mbist_required: false
synthesis:
  dialect: systemverilog_2012
  constraints:
  - No inferred latches
  - No unresolved black boxes
  required_outputs:
  - rtl compile log
  - dut lint report
  - syn/out/synth.v
  top_module: timer
  tool_flow: yosys
  target_technology: sky130_fd_sc_hd
  target_library: sky130_fd_sc_hd
  liberty_env_var: SKY130_LIB
  corner:
    name: sky130_fd_sc_hd__ss_100C_1v40
    process: ss
    temperature_c: 100
    voltage_v: 1.4
  library_policy: Use the SKY130_LIB environment variable to locate the SS corner Liberty file for the declared sky130_fd_sc_hd target library; synthesis and STA must stop if the file is unreadable or does not match the declared corner.
  ppa_targets:
    area_um2_max: null
    power_mw_max: null
    frequency_mhz_min: 100
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
  conventions:
  - Use sequential flops for registered outputs
  - Use combinational defaults on all paths
  lint_waivers: []
reuse_modules: []
custom:
  assumptions:
  - This fixture intentionally models a tiny generic transaction rule IP.
dir_structure:
  yaml_dir: yaml/
  rtl_dir: rtl/
  tb_dir: tb/
  sim_dir: sim/
  cov_dir: cov/
  lint_dir: lint/
filelist:
  rtl:
  - rtl/timer.sv
  - rtl/timer_core.sv
  tb:
  - tb/cocotb/test_timer.py
  coverage:
  - cov/coverage.json
  headers:
  - rtl/timer_param.vh
  sim:
  - sim/results.xml
  - sim/waves.fst
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
    name: function_model transaction FM_PRIMARY
    stimulus: Drive preconditions for function_model transaction `FM_PRIMARY`.
    expected: Outputs and side effects match `FM_PRIMARY` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_PRIMARY
  scoreboard_checks: 6
  coverage_goals:
    function:
      target_pct: 100
      model: function_model
      description: Behavioral coverage for function_model transaction results and state updates.
      bins:
      - id: FCOV_RULE_DOUBLE
        source_ref: function_model.transactions.RULE_DOUBLE
        class: transaction
        description: sampled data_in doubling rule observed
    cycle:
      target_pct: 100
      model: cycle_model
      description: Cycle coverage for sample/result pipeline stages and valid/ready timing.
      bins:
      - id: CCOV_SAMPLE_RESULT_PIPELINE
        source_ref: cycle_model.pipeline
        class: pipeline_stage
        description: sample-to-result cycle path observed
    planned_bins:
    - id: FCOV_RULE_DOUBLE
      class: datapath
      coverage_domain: function
      source_ref: function_model.transactions.RULE_DOUBLE
      description: sampled data_in doubling rule observed
    functional: 'Legacy alias: coverage_goals.function and coverage_goals.cycle must both close.'
    scenario: All SSOT scenarios pass with executable cocotb/pyuvm checkers and FL-vs-RTL scoreboard evidence
quality_gates:
  ssot:
    pass: check_ssot_disk.sh exits 0
    evidence:
    - check_ssot_disk.sh PASS
  rtl:
    pass: RTL compiles and maps every declared port
    evidence:
    - rtl_compile.json
    - dut_lint.json
  rtl_gen:
    profile: standard
    pass: rtl-gen execution_policy.pass_allowed is true, every required SSOT-derived RTL TODO is closed, and provenance proves common_ai_agent rtl-gen authored the RTL without fixed-template fallback behavior
    evidence:
    - rtl/rtl_authoring_plan.json
    - logs/rtl-gen/rtl_todo_plan.json
    - rtl/provenance.json
    - rtl_compile.json
    - lint/dut_lint.json
  dv:
    pass: All scenarios pass with scoreboard evidence
    evidence:
    - results.xml
    - scoreboard_events.jsonl
  coverage:
    pass: All planned functional bins are hit
    evidence:
    - coverage.json
  eda:
    pass: EDA checks are clean or explicitly waived
    evidence:
    - lint report
  signoff:
    pass: SSOT, RTL, lint, sim, and coverage gates pass
    evidence:
    - goal audit
traceability:
  requirements:
  - timer/req/timer_requirements.md
  llm_stage: ssot-gen
  yaml_to_output:
  - yaml: io_list
    output: RTL ports and cocotb driver
  - yaml: function_model
    output: FunctionalModel and scoreboard expected values
  - yaml: cycle_model
    output: RTL latency and waveform checks
  - yaml: test_requirements
    output: cocotb scenarios and coverage bins
  - yaml: function_model/cycle_model/test_requirements
    output: verify/equivalence_goals.json and FL-vs-RTL scoreboard contracts
  - yaml: timing
    output: STA constraints and latency pass/fail criteria
  - yaml: security
    output: Threat mitigations and negative tests
  - yaml: error_handling
    output: Fault RTL paths and DV error scenarios
  - yaml: debug_observability
    output: VCD probes and sim_debug inspection
  - yaml: quality_gates
    output: ATLAS progress/signoff criteria
workflow_todos:
  rtl-gen:
  - id: RTL_RULE_DOUBLE
    content: Implement rule_double from the SSOT function and cycle model
    detail: Capture accepted data_in, produce result=data_in*2 at the declared cycle latency, and expose enough DUT evidence for FL-vs-RTL comparison.
    criteria:
    - RTL updates only on the declared valid/ready acceptance event
    - RTL observed result equals FunctionalModel.apply for RULE_DOUBLE
    - DUT-only compile/lint and rtl_todo_plan audit pass after the final edit
    source_refs:
    - function_model.transactions.RULE_DOUBLE
    - cycle_model.pipeline
    owner_module: timer_core
    owner_file: rtl/timer_core.sv
    priority: high
    required: true
  tb-gen: []
  sim_debug: []
generation_flow:
  steps:
  - name: verify_ssot
    command: python3 "$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py" timer --root "$ATLAS_PROJECT_ROOT" --mode ${ATLAS_RUN_MODE:-signoff}
    description: Validate SSOT structure, Preview fields, and quality gates at the selected Run Mode
  - name: handoff_fl_model
    command: /ssot-fl-model timer
    description: Generate FunctionalModel, decomposition, and FCOV plan from SSOT
  - name: handoff_equivalence_goals
    command: /ssot-equiv-goals timer
    description: Derive FL-vs-RTL equivalence goals before TB generation
  - name: handoff_rtl
    command: /ssot-rtl timer
    description: Generate RTL from validated SSOT
  - name: handoff_tb
    command: /ssot-tb-cocotb timer
    description: Generate cocotb/pyuvm verification from validated SSOT
  - name: handoff_sim_debug
    command: /wf sim_debug
    description: Run simulation, waveform, and coverage inspection


Base rtl-gen contract:
Prepare rtl-gen for timer using only timer/yaml/timer.ssot.yaml and timer/rtl/rtl_todo_plan.json, timer/rtl/rtl_authoring_plan.json, and packets under timer/rtl/authoring_packets. Return exactly one JSON object and nothing else. Success schema: {"files":[{"path":"timer/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"},{"path":"timer/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"},{"path":"timer/list/timer.f","kind":"filelist","content":"<filelist>"}]}. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=38320f1cc94e3b700c9fed82c121eadb81b94bb552b665f8059bf80fe1066eca. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "timer",
        "reason": "18 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "timer",
        "reason": "1 owner logic structure issue(s) remain. timer_core: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "rtl_placeholder_free_evidence",
        "owner_module": "timer",
        "reason": "1 RTL placeholder/policy issue(s) remain. None:None: None (No listed RTL source files were readable, so placeholder-free evidence cannot be checked)",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "status": "open",
        "task_id": "RTL-0009"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "timer",
        "reason": "1 top IO contract issue(s) remain. timer: SSOT top module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "top_output_drive_evidence",
        "owner_module": "timer",
        "reason": "1 top output drive issue(s) remain. timer: SSOT top module is not declared, so output drive evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
        "status": "open",
        "task_id": "RTL-0011"
      },
      {
        "gate_kind": "top_input_consumption_evidence",
        "owner_module": "timer",
        "reason": "1 top input consumption issue(s) remain. timer: SSOT top module is not declared, so input consumption evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
        "status": "open",
        "task_id": "RTL-0012"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "timer",
        "reason": "2 manifest hierarchy integration issue(s) remain. timer: SSOT top module is not declared in listed RTL sources; timer_core: SSOT manifest child module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "timer",
        "reason": "1 manifest signal-flow issue(s) remain. timer: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "status": "open",
        "task_id": "RTL-0015"
      }
    ],
    "blocked_by_locked_truth": [
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "owner_module": "timer",
        "reason": "7 SSOT connection contract issue(s) remain. timer_core: SSOT connection contract targets a module not declared in RTL; timer_core: SSOT connection contract targets a module not declared in RTL; timer_core: SSOT connection contract targets a module not declared in RTL",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      }
    ],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "timer",
        "reason": "Missing common_ai_agent RTL authoring provenance.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "timer",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "timer",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "timer",
        "reason": "80 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 7,
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
    "open_required_todos": 81,
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
          "timer/rtl/rtl_authoring_provenance.json",
          "timer/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip timer --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py timer --root . --audit-rtl"
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
          "timer/rtl/rtl_compile.json",
          "timer/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py timer --top timer --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py timer --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "timer/list/timer.f covers the current DUT RTL sources."
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
          "timer/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py timer --top timer",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py timer --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "timer/list/timer.f covers the current DUT RTL/header sources."
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
          "timer/rtl/rtl_todo_plan.json",
          "timer/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py timer --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "80 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ]
  },
  "ip": "timer",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer.json",
      "kind": "module",
      "llm_actionable_open_count": 28,
      "open_required_count": 28,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer",
      "required_count": 29,
      "status_counts": {
        "open": 28,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core.json",
      "kind": "module",
      "llm_actionable_open_count": 40,
      "open_required_count": 40,
      "owner_file": "rtl/timer_core.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core",
      "required_count": 40,
      "status_counts": {
        "open": 40
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 8,
      "open_required_count": 8,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 9,
      "status_counts": {
        "open": 8,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 1,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 1,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 4,
      "status_counts": {
        "open": 1,
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 4,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    }
  ],
  "policy": {
    "dynamic_task_rule": "Use every required task in this file as the authoritative RTL implementation/evidence ledger. Expose Atlas/UI TodoTracker as one visible gen-rtl implementation/gate loop while keeping every per-contract ledger row in rtl_todo_plan.json for audit, repair routing, and evidence closure.",
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
    "source": "timer/sim/mismatch_classification.json"
  },
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 1,
    "human_locked_tasks": 1,
    "llm_actionable_packets": 3,
    "llm_actionable_tasks": 76,
    "max_packet_required_tasks": 40,
    "module_packets": 2,
    "next_llm_packets": [
      "module__timer",
      "module__timer_core",
      "rtl_gate_evidence_closure"
    ],
    "packet_task_limit": 48,
    "packets": 5,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 86,
    "sliced_module_packets": 0,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 4,
    "total_tasks": 86,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "38320f1cc94e3b700c9fed82c121eadb81b94bb552b665f8059bf80fe1066eca",
  "top": "timer",
  "type": "rtl_authoring_plan"
}

Current sim-debug owner repair evidence:
{
  "items": [],
  "owner_workflow": "rtl-gen",
  "source": "timer/sim/mismatch_classification.json",
  "status": "none"
}

Current owner RTL file (rtl/timer.sv):
<missing or not authored yet>

Current RTL module interface digest (all manifest RTL files):
### rtl/timer.sv
<missing>

### rtl/timer_core.sv
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
    "source": "timer/rtl/rtl_compile.json",
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
    "open_required_todos": 81,
    "orphan_tasks": 0,
    "static_missing": 18,
    "status": "fail"
  },
  "lint": {
    "diagnostics": [],
    "errors": null,
    "passed": null,
    "present": false,
    "repair_hints": [],
    "returncode": null,
    "source": "timer/lint/dut_lint.json",
    "style_violation_count": null,
    "suppression_violation_count": null,
    "warnings": null
  },
  "manifest_hierarchy_issues": [
    {
      "file": "rtl/timer.sv",
      "issue": "SSOT top module is not declared in listed RTL sources",
      "module": "timer"
    },
    {
      "file": "rtl/timer_core.sv",
      "issue": "SSOT manifest child module is not declared in listed RTL sources",
      "module": "timer_core"
    }
  ],
  "manifest_signal_flow_issues": [
    {
      "issue": "SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
      "module": "timer"
    }
  ],
  "open_required_tasks": [
    {
      "category": "rtl_flow.top",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
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
      "reason": "18 static-evidence-required task(s) still lack DUT RTL evidence.",
      "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
      "task_id": "RTL-0007"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 owner logic structure issue(s) remain. timer_core: Behavior-owner module is not declared in its owner file",
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
      "reason": "1 top IO contract issue(s) remain. timer: SSOT top module is not declared in listed RTL sources",
      "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
      "task_id": "RTL-0010"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 top output drive issue(s) remain. timer: SSOT top module is not declared, so output drive evidence cannot be checked",
      "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
      "task_id": "RTL-0011"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 top input consumption issue(s) remain. timer: SSOT top module is not declared, so input consumption evidence cannot be checked",
      "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
      "task_id": "RTL-0012"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "2 manifest hierarchy integration issue(s) remain. timer: SSOT top module is not declared in listed RTL sources; timer_core: SSOT manifest child module is not declared in listed RTL sources",
      "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "task_id": "RTL-0013"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 manifest signal-flow issue(s) remain. timer: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
      "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
      "task_id": "RTL-0015"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "7 SSOT connection contract issue(s) remain. timer_core: SSOT connection contract targets a module not declared in RTL; timer_core: SSOT connection contract targets a module not declared in RTL; timer_core: SSOT connection contract targets a module not declared in RTL",
      "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
      "task_id": "RTL-0016"
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
      "reason": "80 required non-closure TODO(s) remain open.",
      "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
      "task_id": "RTL-0019"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "workflow_todos.rtl-gen[0]",
      "task_id": "RTL-0020"
    },
    {
      "category": "parameters.item",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "parameters.DATA_WIDTH",
      "task_id": "RTL-0021"
    },
    {
      "category": "parameters.item",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "parameters.RESULT_WIDTH",
      "task_id": "RTL-0022"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "io_list.clock_domains.main.ports.clk",
      "task_id": "RTL-0023"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "io_list.resets.rst_n.ports.rst_n",
      "task_id": "RTL-0024"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "io_list.interfaces.rule_io.ports.valid",
      "task_id": "RTL-0025"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "io_list.interfaces.rule_io.ports.data_in",
      "task_id": "RTL-0026"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "io_list.interfaces.rule_io.ports.result",
      "task_id": "RTL-0027"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "io_list.interfaces.rule_io.ports.ready",
      "task_id": "RTL-0028"
    },
    {
      "category": "io_list.port",
      "reason": "Owner RTL file is missing: rtl/timer.sv.",
      "source_ref": "io_list.interfaces.rule_io.ports.result_valid",
      "task_id": "RTL-0029"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.state_variables.accepted_count",
      "task_id": "RTL-0030"
    },
    {
      "category": "function_model.transaction",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.transactions.FM_PRIMARY",
      "task_id": "RTL-0031"
    },
    {
      "category": "function_model.precondition",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.transactions.FM_PRIMARY.preconditions.precondition_0",
      "task_id": "RTL-0032"
    },
    {
      "category": "function_model.precondition",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.transactions.FM_PRIMARY.preconditions.precondition_1",
      "task_id": "RTL-0033"
    },
    {
      "category": "function_model.output",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.transactions.FM_PRIMARY.outputs.output_0",
      "task_id": "RTL-0034"
    },
    {
      "category": "function_model.output",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.transactions.FM_PRIMARY.outputs.accepted_count",
      "task_id": "RTL-0035"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.transactions.FM_PRIMARY.output_rules.result",
      "task_id": "RTL-0036"
    },
    {
      "category": "function_model.state_update",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.transactions.FM_PRIMARY.state_updates.accepted_count",
      "task_id": "RTL-0037"
    },
    {
      "category": "function_model.side_effect",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.transactions.FM_PRIMARY.side_effects.side_effect_0",
      "task_id": "RTL-0038"
    },
    {
      "category": "function_model.invariant",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.invariants.invariant_0",
      "task_id": "RTL-0039"
    },
    {
      "category": "function_model.invariant",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.invariants.invariant_1",
      "task_id": "RTL-0040"
    },
    {
      "category": "function_model.invariant",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "function_model.invariants.invariant_2",
      "task_id": "RTL-0041"
    },
    {
      "category": "cycle_model.clock",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.clock",
      "task_id": "RTL-0042"
    },
    {
      "category": "cycle_model.reset",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.reset",
      "task_id": "RTL-0043"
    },
    {
      "category": "cycle_model.latency",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.latency",
      "task_id": "RTL-0044"
    },
    {
      "category": "cycle_model.handshake_rules",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.handshake_rules.valid_sample",
      "task_id": "RTL-0045"
    },
    {
      "category": "cycle_model.pipeline",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.pipeline.S0_SAMPLE",
      "task_id": "RTL-0046"
    },
    {
      "category": "cycle_model.pipeline",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.pipeline.S1_RESULT",
      "task_id": "RTL-0047"
    },
    {
      "category": "cycle_model.ordering",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.ordering.ordering_rule_0",
      "task_id": "RTL-0048"
    },
    {
      "category": "cycle_model.ordering",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.ordering.ordering_rule_1",
      "task_id": "RTL-0049"
    },
    {
      "category": "cycle_model.backpressure",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "cycle_model.backpressure.backpressure_rule_0",
      "task_id": "RTL-0050"
    },
    {
      "category": "registers.architectural_state",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "registers.architectural_state.accepted_count",
      "task_id": "RTL-0051"
    },
    {
      "category": "fsm.state",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "fsm.control.states.state_0",
      "task_id": "RTL-0052"
    },
    {
      "category": "fsm.state",
      "reason": "Owner RTL file is missing: rtl/timer_core.sv.",
      "source_ref": "fsm.control.states.state_1",
      "task_id": "RTL-0053"
    }
  ],
  "source": "timer/rtl/rtl_todo_plan.json",
  "static_missing_tasks": [
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 3,
      "required_terms": [
        "core",
        "timer",
        "timer_core"
      ],
      "source_ref": "workflow_todos.rtl-gen[0]",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0020"
    },
    {
      "category": "function_model.state_variable",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "accepted",
        "accepted_count",
        "count"
      ],
      "source_ref": "function_model.state_variables.accepted_count",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0030"
    },
    {
      "category": "function_model.precondition",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "rst",
        "rst_n"
      ],
      "source_ref": "function_model.transactions.FM_PRIMARY.preconditions.precondition_0",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0032"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "accepted",
        "accepted_count",
        "count"
      ],
      "source_ref": "function_model.transactions.FM_PRIMARY.outputs.accepted_count",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0035"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "result"
      ],
      "source_ref": "function_model.transactions.FM_PRIMARY.output_rules.result",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0036"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "accepted",
        "accepted_count",
        "count"
      ],
      "source_ref": "function_model.transactions.FM_PRIMARY.state_updates.accepted_count",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0037"
    },
    {
      "category": "function_model.side_effect",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "accepted",
        "accepted_count",
        "count",
        "result",
        "value"
      ],
      "source_ref": "function_model.transactions.FM_PRIMARY.side_effects.side_effect_0",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0038"
    },
    {
      "category": "cycle_model.reset",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "rst",
        "rst_n"
      ],
      "source_ref": "cycle_model.reset",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0043"
    },
    {
      "category": "cycle_model.handshake_rules",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "sample",
        "valid",
        "valid_sample"
      ],
      "source_ref": "cycle_model.handshake_rules.valid_sample",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0045"
    },
    {
      "category": "cycle_model.pipeline",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "data",
        "data_in",
        "in"
      ],
      "source_ref": "cycle_model.pipeline.S0_SAMPLE",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0046"
    },
    {
      "category": "cycle_model.pipeline",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "result",
        "result_valid",
        "valid"
      ],
      "source_ref": "cycle_model.pipeline.S1_RESULT",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0047"
    },
    {
      "category": "registers.architectural_state",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "accepted",
        "accepted_count",
        "count"
      ],
      "source_ref": "registers.architectural_state.accepted_count",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0051"
    },
    {
      "category": "fsm.state",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "S0_SAMPLE"
      ],
      "source_ref": "fsm.control.states.state_0",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0052"
    },
    {
      "category": "fsm.state",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 1,
      "required_terms": [
        "S1_RESULT"
      ],
      "source_ref": "fsm.control.states.state_1",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0053"
    },
    {
      "category": "fsm.transition",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "RESULT",
        "S0",
        "S0_SAMPLE",
        "S1",
        "S1_RESULT",
        "SAMPLE"
      ],
      "source_ref": "fsm.control.transitions.transition_0",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0054"
    },
    {
      "category": "fsm.transition",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "RESULT",
        "S0",
        "S0_SAMPLE",
        "S1",
        "S1_RESULT",
        "SAMPLE"
      ],
      "source_ref": "fsm.control.transitions.transition_1",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0055"
    },
    {
      "category": "dataflow.sequence",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "data",
        "data_in",
        "in"
      ],
      "source_ref": "dataflow.sequence.sequence_0",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0057"
    },
    {
      "category": "dataflow.sequence",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "result",
        "result_valid",
        "valid"
      ],
      "source_ref": "dataflow.sequence.sequence_2",
      "source_scope": "rtl/timer_core.sv",
      "task_id": "RTL-0059"
    }
  ]
}

Current RTL file snapshots for gate/tool-evidence repair:
### rtl/timer.sv
<missing>

### rtl/timer_core.sv
<missing>

Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/rtl_gate_evidence_closure.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 7,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "owner": {
      "file": "rtl/timer.sv",
      "name": "timer",
      "refs": [
        "dataflow",
        "decomposition",
        "integration",
        "io_list",
        "top_module"
      ],
      "wiring_only": true
    },
    "peer_modules": [
      {
        "file": "rtl/timer.sv",
        "name": "timer",
        "wiring_only": true
      },
      {
        "file": "rtl/timer_core.sv",
        "name": "timer_core",
        "wiring_only": false
      }
    ],
    "quality_profile": "standard",
    "reference_profile": null,
    "ssot_connection_contracts": [
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_core",
        "port": "clk",
        "signal": "clk",
        "signal_terms": [
          "clk"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_core",
        "port": "rst_n",
        "signal": "rst_n",
        "signal_terms": [
          "rst_n"
        ],
        "source_ref": "integration.connections[1]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_core",
        "port": "valid",
        "signal": "valid",
        "signal_terms": [
          "valid"
        ],
        "source_ref": "integration.connections[2]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_core",
        "port": "data_in",
        "signal": "data_in",
        "signal_terms": [
          "data_in"
        ],
        "source_ref": "integration.connections[3]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_core",
        "port": "ready",
        "signal": "ready",
        "signal_terms": [
          "ready"
        ],
        "source_ref": "integration.connections[4]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_core",
        "port": "result",
        "signal": "result",
        "signal_terms": [
          "result"
        ],
        "source_ref": "integration.connections[5]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_core",
        "port": "result_valid",
        "signal": "result_valid",
        "signal_terms": [
          "result_valid"
        ],
        "source_ref": "integration.connections[6]"
      }
    ],
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
          "rule_io_valid",
          "valid"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "valid",
        "source_ref": "io_list.interfaces[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "data_in",
          "rule_io_data_in"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "data_in",
        "source_ref": "io_list.interfaces[0].ports[1]",
        "width": "8"
      },
      {
        "aliases": [
          "result",
          "rule_io_result"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "result",
        "source_ref": "io_list.interfaces[0].ports[2]",
        "width": "9"
      },
      {
        "aliases": [
          "ready",
          "rule_io_ready"
        ],
        "allow_constant": true,
        "allow_unused": false,
        "direction": "output",
        "name": "ready",
        "source_ref": "io_list.interfaces[0].ports[3]",
        "width": "1"
      },
      {
        "aliases": [
          "result_valid",
          "rule_io_result_valid"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "result_valid",
        "source_ref": "io_list.interfaces[0].ports[4]",
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
    "draft_allowed": false,
    "evidence_closure_allowed": true,
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
  "ip": "timer",
  "kind": "gate",
  "owner_file": "rtl/timer.sv",
  "owner_module": "timer",
  "packet_id": "rtl_gate_evidence_closure",
  "rules": [
    "No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.",
    "Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.",
    "Every task must satisfy content, detail, and criteria before the packet is closed.",
    "For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.",
    "Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.",
    "Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.",
    "Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.",
    "Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json."
  ],
  "schema_version": 1,
  "source_plan": "rtl/rtl_todo_plan.json",
  "summary": {
    "categories": {
      "rtl_gate.rtl_gen": 9
    },
    "module_slice": {},
    "open_required_count": 8,
    "required_count": 9,
    "source_refs": [
      "quality_gates.rtl_gen.static_rtl_evidence",
      "quality_gates.rtl_gen.owner_logic_structure_evidence",
      "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
      "quality_gates.rtl_gen.top_io_contract_evidence",
      "quality_gates.rtl_gen.top_output_drive_evidence",
      "quality_gates.rtl_gen.top_input_consumption_evidence",
      "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "quality_gates.rtl_gen.manifest_port_connection_evidence",
      "quality_gates.rtl_gen.manifest_signal_flow_evidence"
    ],
    "status_counts": {
      "open": 8,
      "pass": 1
    },
    "task_count": 9
  },
  "tasks": [
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: required SSOT behavior has static DUT RTL evidence after audit",
      "criteria": [
        "derive_rtl_todos.py --audit-rtl ran after the final RTL edit",
        "rtl_todo_plan.json static_rtl_evidence.missing is zero",
        "Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token",
        "No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code",
        "Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.\nSSOT ref: quality_gates.rtl_gen.static_rtl_evidence.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "static_rtl_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0007",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.static_rtl_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "18 static-evidence-required task(s) still lack DUT RTL evidence.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: behavior-owner RTL modules contain real implementation structure",
      "criteria": [
        "Every active behavior-owner module is declared in its owner file",
        "Behavior-owner modules contain non-placeholder assign/procedural implementation logic",
        "State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions",
        "Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.\nSSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "owner_logic_structure_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0008",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.owner_logic_structure_evidence"
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
        "reason": "1 owner logic structure issue(s) remain. timer_core: Behavior-owner module is not declared in its owner file",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: RTL sources contain no placeholder markers or disallowed generated-RTL constructs",
      "criteria": [
        "Listed RTL source files contain no TODO/TBD/FIXME/HACK markers",
        "Listed RTL source files contain no audit-banned incomplete/fake implementation text",
        "Listed RTL source files and rtl/<ip>_param.vh contain no banned package/function/task/loop constructs",
        "Default generated RTL uses input/output logic ports and portable always @ syntax",
        "FSMs use the conventional explicit style by default, unless SSOT/user specifies another synthesizable style",
        "Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments",
        "Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "Production RTL cannot carry audit-banned incomplete/fake implementation markers in source code or comments. Generated RTL uses the project SystemVerilog subset: ANSI ports default to input/output logic, with no package/import/interface/modport, no function/task, no for/while, and no typedef/enum/always_ff/always_comb. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.\nSSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "rtl_placeholder_free_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0009",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.rtl_placeholder_free_evidence"
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
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "1 RTL placeholder/policy issue(s) remain. None:None: None (No listed RTL source files were readable, so placeholder-free evidence cannot be checked)",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top IO contracts match the RTL top module",
      "criteria": [
        "SSOT clock/reset names are declared on the RTL top module",
        "Explicit io_list ports/signals are declared on the RTL top module",
        "Known SSOT directions and simple widths match RTL declarations",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.\nSSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_io_contract_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0010",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_io_contract_evidence"
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
        "reason": "1 top IO contract issue(s) remain. timer: SSOT top module is not declared in listed RTL sources",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top outputs are driven by real RTL logic",
      "criteria": [
        "Every SSOT output/inout top contract has drive evidence in the RTL top",
        "Non-waived output constants are rejected as placeholder tieoffs",
        "Child-instance drive evidence uses a declared child output/inout port, not an unknown direction",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.\nSSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_output_drive_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0011",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_output_drive_evidence"
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
        "reason": "1 top output drive issue(s) remain. timer: SSOT top module is not declared, so output drive evidence cannot be checked",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top inputs are consumed by RTL logic or child inputs",
      "criteria": [
        "Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top",
        "Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction",
        "Unused or reserved inputs are accepted only when explicitly waived by SSOT",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.\nSSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_input_consumption_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0012",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_input_consumption_evidence"
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
        "reason": "1 top input consumption issue(s) remain. timer: SSOT top module is not declared, so input consumption evidence cannot be checked",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest-owned RTL modules are integrated into the top hierarchy",
      "criteria": [
        "Every manifest-owned non-top submodule is declared in listed DUT RTL sources",
        "Each child module is reachable from the SSOT top module through SystemVerilog instantiation",
        "A disconnected child file or flattened top cannot close the manifest hierarchy gate",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.\nSSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_hierarchy_integration",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0013",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_hierarchy_integration"
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
        "reason": "2 manifest hierarchy integration issue(s) remain. timer: SSOT top module is not declared in listed RTL sources; timer_core: SSOT manifest child module is not declared in listed RTL sources",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest-owned child instances have machine-checkable port connections",
      "criteria": [
        "Each reachable manifest child instance uses named port mapping",
        "Every declared child port is connected by name on at least one reachable instance",
        "No child port connection is empty unless represented by an explicit SSOT waiver",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.\nSSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_port_connection_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0014",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_port_connection_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_port_connection_evidence"
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
        "reason": "Every reachable manifest child instance has named, non-empty port connections.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest child port connections carry live RTL signal flow",
      "criteria": [
        "Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance",
        "Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts",
        "Named port-map entries reference ports declared by the child module",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "Primary implementation evidence is in rtl/timer.sv"
      ],
      "detail": "Named port maps prove that ports are connected, but not that the connected signals are useful. Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and child outputs must feed a top output, parent logic, or another declared child input/inout.\nSSOT ref: quality_gates.rtl_gen.manifest_signal_flow_evidence.\nOwner: timer in rtl/timer.sv via top_module.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_signal_flow_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0015",
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_signal_flow_evidence"
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
        "reason": "1 manifest signal-flow issue(s) remain. timer: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "38320f1cc94e3b700c9fed82c121eadb81b94bb552b665f8059bf80fe1066eca",
  "top": "timer",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/rtl_gate_evidence_closure.md):
# RTL Authoring Packet: rtl_gate_evidence_closure

- Kind: gate
- Owner module: timer
- Owner file: rtl/timer.sv
- Task count: 9
- Required tasks: 9

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
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 8
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- SSOT connection contracts:
  - timer_core.clk <= clk (integration.connections[0])
  - timer_core.rst_n <= rst_n (integration.connections[1])
  - timer_core.valid <= valid (integration.connections[2])
  - timer_core.data_in <= data_in (integration.connections[3])
  - timer_core.ready <= ready (integration.connections[4])
  - timer_core.result <= result (integration.connections[5])
  - timer_core.result_valid <= result_valid (integration.connections[6])
- SSOT top IO contracts: 7

## Tasks

### RTL-0007: Gate: required SSOT behavior has static DUT RTL evidence after audit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.static_rtl_evidence
- Detail: After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.
SSOT ref: quality_gates.rtl_gen.static_rtl_evidence.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: 18 static-evidence-required task(s) still lack DUT RTL evidence.
- Criteria:
  - derive_rtl_todos.py --audit-rtl ran after the final RTL edit
  - rtl_todo_plan.json static_rtl_evidence.missing is zero
  - Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token
  - No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code
  - Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.static_rtl_evidence

### RTL-0008: Gate: behavior-owner RTL modules contain real implementation structure

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_logic_structure_evidence
- Detail: Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.
SSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: 1 owner logic structure issue(s) remain. timer_core: Behavior-owner module is not declared in its owner file
- Criteria:
  - Every active behavior-owner module is declared in its owner file
  - Behavior-owner modules contain non-placeholder assign/procedural implementation logic
  - State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_logic_structure_evidence

### RTL-0009: Gate: RTL sources contain no placeholder markers or disallowed generated-RTL constructs

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence
- Detail: Production RTL cannot carry audit-banned incomplete/fake implementation markers in source code or comments. Generated RTL uses the project SystemVerilog subset: ANSI ports default to input/output logic, with no package/import/interface/modport, no function/task, no for/while, and no typedef/enum/always_ff/always_comb. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.
SSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: 1 RTL placeholder/policy issue(s) remain. None:None: None (No listed RTL source files were readable, so placeholder-free evidence cannot be checked)
- Criteria:
  - Listed RTL source files contain no TODO/TBD/FIXME/HACK markers
  - Listed RTL source files contain no audit-banned incomplete/fake implementation text
  - Listed RTL source files and rtl/<ip>_param.vh contain no banned package/function/task/loop constructs
  - Default generated RTL uses input/output logic ports and portable always @ syntax
  - FSMs use the conventional explicit style by default, unless SSOT/user specifies another synthesizable style
  - Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments
  - Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.rtl_placeholder_free_evidence

### RTL-0010: Gate: SSOT top IO contracts match the RTL top module

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_io_contract_evidence
- Detail: The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.
SSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: 1 top IO contract issue(s) remain. timer: SSOT top module is not declared in listed RTL sources
- Criteria:
  - SSOT clock/reset names are declared on the RTL top module
  - Explicit io_list ports/signals are declared on the RTL top module
  - Known SSOT directions and simple widths match RTL declarations
  - Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_io_contract_evidence

### RTL-0011: Gate: SSOT top outputs are driven by real RTL logic

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_output_drive_evidence
- Detail: Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.
SSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: 1 top output drive issue(s) remain. timer: SSOT top module is not declared, so output drive evidence cannot be checked
- Criteria:
  - Every SSOT output/inout top contract has drive evidence in the RTL top
  - Non-waived output constants are rejected as placeholder tieoffs
  - Child-instance drive evidence uses a declared child output/inout port, not an unknown direction
  - Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_output_drive_evidence

### RTL-0012: Gate: SSOT top inputs are consumed by RTL logic or child inputs

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_input_consumption_evidence
- Detail: Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.
SSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: 1 top input consumption issue(s) remain. timer: SSOT top module is not declared, so input consumption evidence cannot be checked
- Criteria:
  - Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top
  - Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction
  - Unused or reserved inputs are accepted only when explicitly waived by SSOT
  - Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_input_consumption_evidence

### RTL-0013: Gate: manifest-owned RTL modules are integrated into the top hierarchy

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_hierarchy_integration
- Detail: File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.
SSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: 2 manifest hierarchy integration issue(s) remain. timer: SSOT top module is not declared in listed RTL sources; timer_core: SSOT manifest child module is not declared in listed RTL sources
- Criteria:
  - Every manifest-owned non-top submodule is declared in listed DUT RTL sources
  - Each child module is reachable from the SSOT top module through SystemVerilog instantiation
  - A disconnected child file or flattened top cannot close the manifest hierarchy gate
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_hierarchy_integration

### RTL-0014: Gate: manifest-owned child instances have machine-checkable port connections

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_port_connection_evidence
- Detail: Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.
SSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: Every reachable manifest child instance has named, non-empty port connections.
- Criteria:
  - Each reachable manifest child instance uses named port mapping
  - Every declared child port is connected by name on at least one reachable instance
  - No child port connection is empty unless represented by an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_port_connection_evidence

### RTL-0015: Gate: manifest child port connections carry live RTL signal flow

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_signal_flow_evidence
- Detail: Named port maps prove that ports are connected, but not that the connected signals are useful. Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and child outputs must feed a top output, parent logic, or another declared child input/inout.
SSOT ref: quality_gates.rtl_gen.manifest_signal_flow_evidence.
Owner: timer in rtl/timer.sv via top_module.
- Current reason: 1 manifest signal-flow issue(s) remain. timer: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked
- Criteria:
  - Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance
  - Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts
  - Named port-map entries reference ports declared by the child module
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_signal_flow_evidence
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_signal_flow_evidence
