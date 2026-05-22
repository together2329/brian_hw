RTL-GEN PACKET MODE for model_compare_counter. Packet attempt 2.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "model_compare_counter/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "model_compare_counter/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "model_compare_counter/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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

Current packet: module__model_compare_counter_core__function_model_02
kind: module
work queue: 2/4 active packets (10 closed packets skipped from 14 total)
batch limit: 4; deferred active packets after this batch: 0
owner_module: model_compare_counter_core
owner_file: rtl/model_compare_counter_core.sv

SSOT observable latency contract:
{
  "cycle_model.latency": {
    "update_latency": {
      "description": "Input sampled at edge N",
      "max_cycles": 1,
      "min_cycles": 1,
      "updated outputs visible after edge N": null
    }
  },
  "cycle_model.pipeline": [
    {
      "action": "Sample clear, enable, step, and current count state",
      "cycle": 0,
      "output_rules": [
        {
          "expr": "0",
          "name": "sample_enable",
          "port": "valid",
          "width": 1
        }
      ],
      "stage": "SAMPLE"
    },
    {
      "action": "Commit clear/update/idle state and pulse outputs",
      "cycle": 1,
      "output_rules": [
        {
          "expr": "0 if clear == 1 else (((count_q + step) & 0xFF) if enable == 1 else count_q)",
          "name": "count_commit",
          "port": "count",
          "width": 8
        },
        {
          "expr": "0 if clear == 1 else ((1 if ((count_q + step) > 255) else 0) if enable == 1 else 0)",
          "name": "wrapped_commit",
          "port": "wrapped",
          "width": 1
        },
        {
          "expr": "0 if clear == 1 else (1 if enable == 1 else 0)",
          "name": "valid_commit",
          "port": "valid",
          "width": 1
        }
      ],
      "stage": "COMMIT"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": "enable",
  "timing.latency_budget": [
    {
      "max_cycles": 1,
      "min_cycles": 1,
      "path": "enable/clear/step -> count/wrapped/valid",
      "requirement": "single-cycle accept/update/observe"
    }
  ]
}

SSOT bus/byte-lane policy:
{
  "guidance": "condition=none means upper byte lanes are not an APB error for legal offsets; consume otherwise-unused pwdata/pstrb upper bits through explicit legal ignore, byte-strobe masking, reserved-zero readback, or coverage/trace behavior while keeping pslverr deasserted for legal writes.",
  "illegal_byte_access_pattern_condition": "<not declared>",
  "upper_byte_lane_error_allowed": false
}

Locked SSOT YAML excerpt (model_compare_counter/yaml/model_compare_counter.ssot.yaml):
top_module:
  name: model_compare_counter
  file: rtl/model_compare_counter.sv
  version: '1.0'
  type: peripheral
  description: 8-bit enabled up-counter with clear priority, overflow pulse, and valid pulse.
  reference_spec: model_compare_counter/req/model_compare_counter_requirements.md
  target:
    technology: generic
    clock_freq_mhz: 100
    area_um2: null
    power_mw: null
sub_modules:
- name: model_compare_counter_core
  file: rtl/model_compare_counter_core.sv
  ownership: manifest
  ssot_gen: false
  implements:
  - function_model.transactions
  - function_model.state_variables
  - cycle_model.pipeline
  - cycle_model.ordering
  - io_list.interfaces
  - io_list.clock_domains
  - io_list.resets
  - fsm.control
  source_sections:
  - function_model
  - cycle_model
  - io_list
  - fsm
  - features
  - dataflow
  - decomposition
  - test_requirements
  function_model_refs:
  - function_model.transactions
  - function_model.state_variables
  - function_model.transactions.FM_CLEAR
  - function_model.transactions.FM_UPDATE
  - function_model.transactions.FM_IDLE
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.ordering
  - cycle_model.handshake_rules
  - cycle_model
  fsm_refs:
  - fsm.control
  - fsm
  description: Sequential state update and output pulse generation logic.
  feature_refs:
  - features
  dataflow_refs:
  - dataflow
  decomposition_refs:
  - decomposition
  test_refs:
  - test_requirements
- name: model_compare_counter
  file: rtl/model_compare_counter.sv
  ownership: manifest
  ssot_gen: true
  wiring_only: true
  description: Top-level integration module matching SSOT top_module
  implements:
  - top_module
  - integration
  source_sections: &id001
  - top_module
  - io_list
  - decomposition
  - integration
  decomposition_refs:
  - decomposition
  dataflow_refs:
  - dataflow
decomposition:
  strategy: manifest_owned_leaf_decomposition
  owners:
  - module: model_compare_counter_core
    file: rtl/model_compare_counter_core.sv
    responsibility: Sequential state update and output pulse generation logic.
    source_sections:
    - function_model
    - cycle_model
    - io_list
    - fsm
  - module: model_compare_counter
    file: rtl/model_compare_counter.sv
    responsibility: Top-level integration module matching SSOT top_module
    source_sections: *id001
  integration_policy: Top-level wiring must be backed by integration.connections or sub_modules[].connections before signoff.
  source_refs:
  - sub_modules
  - function_model
  - cycle_model
  - integration
rtl_contract:
  top_name: model_compare_counter
  reset_behavior:
    asynchronous_assertion: true
    synchronous_release: true
    reset_values:
      count: 0
      wrapped: 0
      valid: 0
  protocols:
  - No external bus protocol; direct sampled control inputs.
  implementation_rules:
  - clear must have higher priority than enable in sequential next-state logic.
  - count update is modulo 256 (truncate to COUNT_WIDTH).
  - wrapped and valid are one-cycle pulses and deassert in idle cycles.
  owner: ssot-gen
  type: ssot_derived_rule_contract
  transaction: FM_CLEAR
  clock: clk
  reset: rst_n
  reset_active: low
  sample_condition: enable
  input_map:
    enable: enable
    clear: clear
    step: step
  output_map:
    count: count
    wrapped: wrapped
    valid: valid
  contract_invariants:
  - RTL-visible behavior implements the referenced function_model transaction.
  - Input sampling and output observation follow cycle_model handshake and latency rules.
  output_rules:
  - name: out_count
    port: count
    expr: '0'
    width: 8
    description: FunctionalModel output observable mapped to DUT output port.
  - name: out_wrapped
    port: wrapped
    expr: '0'
    width: 1
    description: FunctionalModel output observable mapped to DUT output port.
  - name: out_valid
    port: valid
    expr: '0'
    width: 1
    description: FunctionalModel output observable mapped to DUT output port.
parameters:
- name: COUNT_WIDTH
  default: 8
  type: int
  description: Width of count output register.
  drives:
  - rtl/model_compare_counter.sv
  - rtl/model_compare_counter_core.sv
- name: STEP_WIDTH
  default: 4
  type: int
  description: Width of step input.
  drives:
  - rtl/model_compare_counter.sv
  - rtl/model_compare_counter_core.sv
io_list:
  clock_domains:
  - name: clk
    frequency_mhz: 100
    description: Main synchronous clock.
    ports:
    - name: clk
      width: 1
      direction: input
      description: Rising-edge sampling clock
  resets:
  - name: rst_n
    polarity: active_low
    sync_async: async_assert_sync_deassert
    description: Active-low reset for all architectural state.
    ports:
    - name: rst_n
      width: 1
      direction: input
      description: Active-low reset
  interfaces:
  - name: ctrl_inputs
    type: custom
    role: sink
    description: Control and increment inputs.
    ports:
    - name: enable
      width: 1
      direction: input
      description: Accept update when high and clear low
    - name: clear
      width: 1
      direction: input
      description: Synchronous clear request with priority over enable
    - name: step
      width: 4
      direction: input
      description: Increment magnitude for enabled update
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: status_outputs
    type: custom
    role: source
    description: Counter state and pulse outputs.
    ports:
    - name: count
      width: 8
      direction: output
      description: Registered modulo-256 counter value
    - name: wrapped
      width: 1
      direction: output
      description: One-cycle pulse on overflow of enabled addition
    - name: valid
      width: 1
      direction: output
      description: One-cycle pulse when enabled update is accepted
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
features:
- name: Clear-priority synchronous control
  trigger: clear sampled high at rising edge
  datapath: Force counter and pulse outputs to zero
  control: Clear branch precedes enable branch
  output: count=0, wrapped=0, valid=0
- name: Enabled modulo increment
  trigger: enable high while clear low
  datapath: Add zero-extended step to 8-bit count and truncate to 8 bits
  control: Update branch after clear check
  output: count updates modulo 256, valid pulse asserted
- name: Overflow notification pulse
  trigger: enabled increment where count + step >= 256
  datapath: Carry-out detect from 9-bit addition
  control: Only in enabled update branch
  output: wrapped pulse for one cycle
dataflow:
  read_path:
    source: Inputs enable/clear/step sampled at clk edge
    burst: single sample per cycle
    buffer: n/a
    sequence: sample inputs -> evaluate priority -> compute next state
  write_path:
    source: next_count and next pulse flags
    burst: single register update per cycle
    destination: count/wrapped/valid output registers
    sequence: compute next values -> commit on rising edge
  loop_control:
    counter: count register
    decrement: n/a
    auto_increment: count increments by step when enabled and not cleared
function_model:
  purpose: Behavioral oracle for counter updates, overflow pulse semantics, and idle hold behavior.
  state_variables:
  - name: count_q
    reset: 0
    width: 8
    description: Architectural counter state
  - name: wrapped_q
    reset: 0
    width: 1
    description: One-cycle overflow indication output register
  - name: valid_q
    reset: 0
    width: 1
    description: One-cycle accepted-update indication output register
  transactions:
  - id: FM_CLEAR
    name: clear_priority_reset
    preconditions:
    - clear == 1
    inputs:
    - clear
    - enable
    - step
    - count_q
    outputs:
    - count == 0
    - wrapped == 0
    - valid == 0
    - name: out_count
      port: count
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: out_wrapped
      port: wrapped
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: out_valid
      port: valid
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: count_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: wrapped_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: valid_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: out_count
      port: count
      width: 8
      expr: '0'
    - name: out_wrapped
      port: wrapped
      width: 1
      expr: '0'
    - name: out_valid
      port: valid
      width: 1
      expr: '0'
    state_updates:
    - name: count_q
      width: 8
      expr: '0'
    - name: wrapped_q
      width: 1
      expr: '0'
    - name: valid_q
      width: 1
      expr: '0'
    side_effects:
    - Clear overrides enable and forces all outputs/state low on next observed state.
    error_cases: []
  - id: FM_UPDATE
    name: enabled_increment
    preconditions:
    - clear == 0
    - enable == 1
    inputs:
    - clear
    - enable
    - step
    - count_q
    outputs:
    - count == ((count_q + step) & 0xFF)
    - wrapped == 1 when (count_q + step) > 255 else 0
    - valid == 1
    - name: out_count
      port: count
      expr: (count_q + step) & 0xFF
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: out_wrapped
      port: wrapped
      expr: 1 if ((count_q + step) > 255) else 0
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: out_valid
      port: valid
      expr: '1'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: count_q
      expr: (count_q + step) & 0xFF
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: wrapped_q
      expr: 1 if ((count_q + step) > 255) else 0
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: valid_q
      expr: '1'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: out_count
      port: count
      width: 8
      expr: (count_q + step) & 0xFF
    - name: out_wrapped
      port: wrapped
      width: 1
      expr: 1 if ((count_q + step) > 255) else 0
    - name: out_valid
      port: valid
      width: 1
      expr: '1'
    state_updates:
    - name: count_q
      width: 8
      expr: (count_q + step) & 0xFF
    - name: wrapped_q
      width: 1
      expr: 1 if ((count_q + step) > 255) else 0
    - name: valid_q
      width: 1
      expr: '1'
    side_effects:
    - Accepted enabled update advances count modulo 256 and emits valid pulse.
    - wrapped pulse is asserted only for overflowing additions.
    error_cases: []
  - id: FM_IDLE
    name: idle_hold
    preconditions:
    - transaction is accepted under cycle_model rules
    inputs:
    - clear
    - enable
    - step
    - count_q
    outputs:
    - count == count_q
    - wrapped == 0
    - valid == 0
    - name: out_count
      port: count
      expr: count_q
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: out_wrapped
      port: wrapped
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: out_valid
      port: valid
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: count_q
      expr: count_q
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: wrapped_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: valid_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: out_count
      port: count
      width: 8
      expr: count_q
    - name: out_wrapped
      port: wrapped
      width: 1
      expr: '0'
    - name: out_valid
      port: valid
      width: 1
      expr: '0'
    state_updates:
    - name: count_q
      width: 8
      expr: count_q
    - name: wrapped_q
      width: 1
      expr: '0'
    - name: valid_q
      width: 1
      expr: '0'
    side_effects:
    - Counter holds during idle cycles while pulse outputs deassert.
    error_cases: []
  invariants:
  - clear==1 implies next count_q, wrapped_q, valid_q are all zero regardless of enable.
  - valid_q may only be 1 in cycles where clear==0 and enable==1.
  - wrapped_q may only be 1 in cycles where clear==0 and enable==1 and (count_prev + step) > 255.
cycle_model:
  purpose: Single-cycle sampled-input to post-edge-state visibility contract.
  executable: pymtl3
  backend_policy: Use FunctionalModel transaction stepping for expected behavior and lockstep cycle comparison.
  cosim: true
  state_accumulating: true
  use_per_cycle_expected: true
  clock: clk
  reset:
    assertion: rst_n low asynchronously clears count/wrapped/valid state to zero
    deassertion: state is valid on first rising edge after rst_n is high
  latency:
    update_latency:
      min_cycles: 1
      max_cycles: 1
      description: Input sampled at edge N
      updated outputs visible after edge N: null
  handshake_rules:
  - signal: clk
    rule: Inputs enable/clear/step are sampled only on rising edge of clk.
  - signal: clear_enable_priority
    rule: If clear and enable are both high at a sampled edge, clear branch wins and no increment occurs.
  - signal: backpressure
    rule: No ready/valid backpressure; every cycle can accept control inputs.
  pipeline:
  - stage: SAMPLE
    cycle: 0
    action: Sample clear, enable, step, and current count state
    output_rules:
    - name: sample_enable
      port: valid
      width: 1
      expr: '0'
  - stage: COMMIT
    cycle: 1
    action: Commit clear/update/idle state and pulse outputs
    output_rules:
    - name: count_commit
      port: count
      width: 8
      expr: 0 if clear == 1 else (((count_q + step) & 0xFF) if enable == 1 else count_q)
    - name: wrapped_commit
      port: wrapped
      width: 1
      expr: 0 if clear == 1 else ((1 if ((count_q + step) > 255) else 0) if enable == 1 else 0)
    - name: valid_commit
      port: valid
      width: 1
      expr: 0 if clear == 1 else (1 if enable == 1 else 0)
  ordering:
  - 'Reset dominance: active reset forces zeros before functional branch evaluation.'
  - Within functional operation, clear branch is evaluated before enable branch each sampled cycle.
  - Pulse outputs wrapped/valid correspond to same update cycle as count commit.
  backpressure:
  - Not applicable; no downstream handshake channels to stall updates.
  observability:
  - Each function_model transaction maps to COMMIT stage output expectations.
  performance:
    frequency_mhz: 100
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
  - name: clk
    frequency_mhz: 100
    description: Sole synchronous domain
  reset_scheme:
    signal: rst_n
    polarity: active_low
    type: async_assert_sync_deassert
cdc_requirements:
  crossings: []
  synchronizers: []
  note: Single clock domain; no CDC paths.
rdc_requirements:
  crossings: []
  synchronizers: []
  note: Single reset domain; no RDC paths.
registers:
  config:
    register_width: 32
    addr_width: 0
    byte_addressable: false
  no_registers_policy:
    reason: This IP is direct-wire controlled and does not expose CSR/register programming interface.
    software_visible: false
  register_list: []
  no_registers: true
  policy: No firmware-visible registers are declared; add register_list before CSR behavior is implemented.
memory:
  instances:
  - name: count_state_ff
    type: register
    depth: 1
    width: 8
    read_ports: 1
    write_ports: 1
    latency: 0
    description: Counter state storage
  - name: wrapped_state_ff
    type: register
    depth: 1
    width: 1
    read_ports: 1
    write_ports: 1
    latency: 0
    description: Wrapped pulse storage
  - name: valid_state_ff
    type: register
    depth: 1
    width: 1
    read_ports: 1
    write_ports: 1
    latency: 0
    description: Valid pulse storage
interrupts:
  sources: []
  output:
    signal: none
    polarity: active_high
    type: none
fsm:
  control:
    states:
    - RESET
    - CLEAR
    - UPDATE
    - IDLE
    transitions:
    - from: RESET
      to: IDLE
      condition: rst_n == 1
    - from: IDLE
      to: CLEAR
      condition: clear == 1
    - from: IDLE
      to: UPDATE
      condition: clear == 0 and enable == 1
    - from: IDLE
      to: IDLE
      condition: clear == 0 and enable == 0
    - from: UPDATE
      to: IDLE
      condition: next cycle
    - from: CLEAR
      to: IDLE
      condition: next cycle
timing:
  target_clocks:
  - name: clk
    period_ns: 10.0
    uncertainty_ns: 0.2
  latency_budget:
  - path: enable/clear/step -> count/wrapped/valid
    min_cycles: 1
    max_cycles: 1
    requirement: single-cycle accept/update/observe
  throughput:
  - item: updates
    value: 1 update per cycle when enable=1 and clear=0
  sta_expectations:
    setup_wns_ns_min: 0.0
    hold_wns_ns_min: 0.0
    required_reports:
    - sta/out/timing.rpt
    - sta/out/wns.json
power:
  domains:
  - name: PD_MAIN
    description: Always-on logic domain for this simple block
  power_states:
  - name: true
    domain: PD_MAIN
    condition: clk toggling and rst_n may be asserted/deasserted
    retention: false
  clock_gating:
  - Optional inferred enable-based data gating allowed; no explicit clock gate required.
  upf_required: false
security:
  classification: non-cryptographic control primitive
  assets:
  - count output integrity
  - clear priority correctness
  - overflow pulse correctness
  threat_model:
  - threat: control input glitching near clock edge
    mitigation: synchronous sampling contract and setup/hold assumptions
  - threat: state corruption via reset misuse
    mitigation: defined reset behavior and verification of reset recovery
  assumptions:
  - Inputs are driven from trusted logic within same clock domain.
  privilege_model: System-level access control is owned by the integrating bus/firewall unless explicitly declared here.
error_handling:
  error_sources:
  - id: illegal_xz_inputs
    condition: Simulation-only X/Z on control inputs
    architectural_effect: Status/error reporting follows the SSOT error policy
  propagation:
  - No dedicated error output; errors are detected in verification checks and lint/formal assertions.
  recovery:
  - Apply rst_n low then high to return outputs/state to known zero baseline.
debug_observability:
  waveform_must_probe:
  - clk
  - rst_n
  - clear
  - enable
  - step
  - count
  - wrapped
  - valid
  trace_events:
  - name: EVT_CLEAR
    trigger: clear==1 sampled
    observables:
    - count
    - wrapped
    - valid
  - name: EVT_UPDATE
    trigger: clear==0 and enable==1 sampled
    observables:
    - count
    - wrapped
    - valid
    - step
  - name: EVT_IDLE
    trigger: clear==0 and enable==0 sampled
    observables:
    - count
    - wrapped
    - valid
  status_outputs:
  - status/debug signals declared in io_list or registers
integration:
  bus_attachment:
    type: none
    description: Direct signal-level integration; no APB/AXI wrapper required.
  dependencies:
  - Single synchronous clock domain source
  - Active-low reset distribution
  connections:
  - module: model_compare_counter
    port: clk
    signal: clk
  - module: model_compare_counter
    port: rst_n
    signal: rst_n
  - module: model_compare_counter
    port: enable
    signal: enable
  - module: model_compare_counter
    port: clear
    signal: clear
  - module: model_compare_counter
    port: step
    signal: step
  connection_contract_status: missing machine-readable module wiring; child RTL drafts may proceed from owner packets, but top integration/signoff must stay blocked until SSOT authors integration.connections or sub_modules[].connections with module/port/signal records
  integration_notes:
  - Integrator must connect every declared io_list port and honor timing/reset assumptions.
dft:
  scan_required: false
  controllability:
  - All state is controllable via rst_n, enable, clear, step under clocked operation.
  observability:
  - All state is directly observable via count, wrapped, valid outputs.
  mbist_required: true
synthesis:
  dialect: systemverilog_2012
  constraints:
  - Constrain clk to 100 MHz target
  - Constrain rst_n as asynchronous reset input
  required_outputs:
  - netlist
  - area_report
  - timing_report
  - lint_report
  top_module: model_compare_counter
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
  file_extension: .sv
  conventions:
  - Use nonblocking assignments in sequential always blocks.
  - No inferred latches.
  - Single always_ff-style sequential process for state updates.
  - Clear branch must be coded ahead of enable branch in priority chain.
  lint_waivers: []
reuse_modules: []
custom:
  assumptions:
  - step is interpreted as unsigned 4-bit value in range 0..15.
  notes:
  - No protocol backpressure or multicycle command tracking is required.
  optional_behavior_policy:
    resolution: non_required_optional_items_disabled_unless_ssot_marks_required_or_parameterized
    owner: ssot-gen deterministic repair
    rule: Rows marked required:false or prose-only optional verification aids do not add RTL behavior. Any optional functional behavior must be converted by ssot-gen into required behavior or an explicit parameter/register policy before rtl-gen signoff.
dir_structure:
  yaml_dir: yaml/
  output_dirs:
    rtl: rtl/
    tb: tb/
    tc: tc/
    sim: sim/
    lint: lint/
    list: list/
filelist:
  headers: []
  rtl:
  - rtl/model_compare_counter.sv
  - rtl/model_compare_counter_core.sv
  sim:
  - sim/tb_model_compare_counter.py
  firmware: []
  docs:
  - doc/model_compare_counter_mas.md
  tb:
  - tb/cocotb/test_model_compare_counter.py
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
    name: function_model transaction FM_CLEAR
    stimulus: Drive preconditions for function_model transaction `FM_CLEAR`.
    expected: Outputs and side effects match `FM_CLEAR` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_CLEAR
  - id: SC07
    name: function_model transaction FM_UPDATE
    stimulus: Drive preconditions for function_model transaction `FM_UPDATE`.
    expected: Outputs and side effects match `FM_UPDATE` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_UPDATE
  - id: SC08
    name: function_model transaction FM_IDLE
    stimulus: Drive preconditions for function_model transaction `FM_IDLE`.
    expected: Outputs and side effects match `FM_IDLE` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_IDLE
  scoreboard_checks: 12
  coverage_goals:
    function:
      target_pct: 100
      model: function_model
      bins:
      - id: FCOV_CLEAR_PRIORITY
        source_ref: function_model.transactions.FM_CLEAR
        class: transaction
        description: Clear transaction taken when clear=1
      - id: FCOV_UPDATE_NO_OVERFLOW
        source_ref: function_model.transactions.FM_UPDATE
        class: arithmetic
        description: Enabled increment with no overflow
      - id: FCOV_UPDATE_OVERFLOW
        source_ref: function_model.transactions.FM_UPDATE
        class: arithmetic
        description: Enabled increment with overflow wrap
      - id: FCOV_IDLE_HOLD
        source_ref: function_model.transactions.FM_IDLE
        class: transaction
        description: Idle hold transaction executed
      description: Behavioral coverage from function_model.
    cycle:
      target_pct: 100
      model: cycle_model
      bins:
      - id: CCOV_CLEAR_WINS
        source_ref: cycle_model.handshake_rules.clear_enable_priority
        class: ordering
        description: Clear branch selected over enable
      - id: CCOV_WRAP_PULSE
        source_ref: cycle_model.pipeline.COMMIT
        class: pulse
        description: Wrapped pulse asserted on overflow cycle
      - id: CCOV_IDLE_DEASSERT
        source_ref: cycle_model.pipeline.COMMIT
        class: pulse
        description: wrapped/valid deasserted during idle
      - id: CCOV_CONSECUTIVE_UPDATES
        source_ref: cycle_model.pipeline.COMMIT
        class: sequence
        description: Multi-cycle consecutive updates
      description: Cycle/performance coverage from cycle_model.
    code: line >= 95%, branch >= 95%
    scenario: All SSOT scenarios pass with executable cocotb/pyuvm checkers and FL-vs-RTL scoreboard evidence
quality_gates:
  ssot:
    pass: SSOT passes engineering schema and disk checks with mandatory function/cycle/test sections populated.
    evidence:
    - req/ssot_validation.json
    - req/ssot_downstream_blockers.json
  rtl:
    pass: RTL compiles and lints clean with no warnings; behavior matches SSOT function/cycle contracts.
    evidence:
    - lint/lint_report.txt
    - sim/fl_rtl_goal_audit.json
  rtl_gen:
    profile: standard
    pass: RTL TODO ledger implemented with provenance for model_compare_counter_core behavior.
    evidence:
    - rtl/rtl_todo_plan.json
    - rtl/rtl_authoring_provenance.json
  dv:
    pass: cocotb/pyuvm scenarios execute and scoreboard passes all required checks.
    evidence:
    - sim/sim_results.xml
    - sim/scoreboard_report.json
  coverage:
    pass: Function and cycle coverage bins for all required scenarios reach target or approved waiver.
    evidence:
    - cov/coverage.json
    - sim/coverage_report.md
  eda:
    pass: Synthesis meets 100MHz target and emits required reports.
    evidence:
    - syn/syn_report.txt
    - syn/timing_report.txt
    - syn/area_report.txt
  signoff:
    pass: Final goal audit shows all required SSOT->RTL->TB->SIM goals closed.
    evidence:
    - sim/final_goal_audit.json
traceability:
  yaml_to_output:
  - yaml: top_module
    output: rtl/model_compare_counter.sv
  - yaml: io_list.interfaces
    output: rtl/model_compare_counter.sv port list
  - yaml: function_model.transactions
    output: sim scoreboard expected model and rtl sequential logic
  - yaml: cycle_model.pipeline
    output: cycle-accurate checks in cocotb/pyuvm
  - yaml: test_requirements.scenarios
    output: sim test sequences
  - yaml: quality_gates
    output: lint/sim/coverage/syn signoff evidence collection
  - yaml: function_model
    output: RTL behavior and TB reference model
  - yaml: cycle_model
    output: RTL handshake/pipeline timing and waveform checks
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
workflow_todos:
  fl-model-gen:
  - id: FL_TODO_MODEL_COUNTER_STEP
    content: Implement executable FL model for clear/enable/idle transactions.
    detail: Build Python FunctionalModel state step() honoring transaction order FM_CLEAR -> FM_UPDATE -> FM_IDLE and invariants.
    criteria:
    - FL model reproduces modulo-256 count update behavior
    - FL model emits wrapped/valid pulses exactly per SSOT
    source_refs:
    - function_model.transactions
    - function_model.invariants
    priority: high
    required: true
  rtl-gen:
  - id: RTL_TODO_PRIORITY_SEQ
    content: Implement clear-priority sequential next-state logic.
    detail: In rtl/model_compare_counter_core.sv code reset, clear, enable, idle branches with clear overriding enable in same sampled cycle.
    criteria:
    - If clear=1 and enable=1 at edge, resulting count/wrapped/valid are zero
    - Branch order and behavior match FM_CLEAR/FM_UPDATE/FM_IDLE
    source_refs:
    - function_model.transactions.FM_CLEAR
    - function_model.transactions.FM_UPDATE
    - cycle_model.ordering
    owner_module: model_compare_counter_core
    owner_file: rtl/model_compare_counter_core.sv
    priority: high
    required: true
  - id: RTL_TODO_OVERFLOW_PULSE
    content: Generate wrapped pulse from overflow carry-out only on enabled updates.
    detail: Compute 9-bit sum for count+step and drive wrapped for one cycle when carry-out is set, while idle/clear force wrapped low.
    criteria:
    - wrapped asserted exactly on overflowing FM_UPDATE cycles
    - wrapped deasserted on clear and idle cycles
    source_refs:
    - function_model.transactions.FM_UPDATE
    - function_model.invariants
    - cycle_model.pipeline
    owner_module: model_compare_counter_core
    owner_file: rtl/model_compare_counter_core.sv
    priority: high
    required: true
  - id: RTL_TODO_VALID_PULSE
    content: Implement valid one-cycle pulse for accepted enabled updates.
    detail: Drive valid high only in enable && !clear branch and low otherwise, including reset and clear cycles.
    criteria:
    - valid=1 for each accepted update cycle
    - valid=0 during reset, clear, and idle cycles
    source_refs:
    - function_model.transactions.FM_UPDATE
    - function_model.transactions.FM_CLEAR
    - function_model.transactions.FM_IDLE
    owner_module: model_compare_counter_core
    owner_file: rtl/model_compare_counter_core.sv
    priority: high
    required: true
  tb-gen:
  - id: TB_TODO_SCENARIOS
    content: Implement cocotb/pyuvm tests for six required scenarios.
    detail: Create directed and sequence-based tests for reset, clear priority, no-overflow, overflow, idle hold, and multi-update accumulation.
    criteria:
    - All scenario IDs SC_RESET..SC_MULTI_SEQ executed
    - Scoreboard checks pass for all transactions
    source_refs:
    - test_requirements.scenarios
    - function_model
    - cycle_model
    priority: high
    required: true
  sim_debug:
  - id: DBG_TODO_WAVES
    content: Capture debug waveforms for must-probe signals in failing tests.
    detail: Ensure waveform dump includes all debug_observability.waveform_must_probe signals and annotate transaction boundaries.
    criteria:
    - Waveform includes clk,rst_n,clear,enable,step,count,wrapped,valid
    source_refs:
    - debug_observability.waveform_must_probe
    priority: medium
    required: true
  coverage:
  - id: COV_TODO_BINS
    content: Close function and cycle coverage bins tied to required scenarios.
    detail: Add collectors/crosses to prove overflow and clear-priority ordering bins and consecutive update sequence bins.
    criteria:
    - All function and cycle bins hit >= target_pct
    source_refs:
    - test_requirements.coverage_goals
    priority: high
    required: true
  syn: []
  pnr: []
  sta: []
  sta-post: []
generation_flow:
  steps:
  - name: verify_ssot
    command: python3 workflow/ssot-gen/scripts/verify_ssot.py model_compare_counter --mode ${ATLAS_RUN_MODE:-signoff}
    description: Validate SSOT structure, Preview fields, and quality gates at the selected Run Mode
  - name: handoff_fl_model
    command: /ssot-fl-model model_compare_counter
    description: Generate FunctionalModel, decomposition, and FCOV plan from SSOT
  - name: handoff_equivalence_goals
    command: /ssot-equiv-goals model_compare_counter
    description: Derive FL-vs-RTL equivalence goals before TB generation
  - name: handoff_rtl
    command: /ssot-rtl model_compare_counter
    description: Generate RTL from validated SSOT
  - name: handoff_tb
    command: /ssot-tb-cocotb model_compare_counter
    description: Generate cocotb/pyuvm verification from validated SSOT
  - name: handoff_sim_debug
    command: /wf sim_debug
    description: Run simulation, waveform, and coverage inspection


Base rtl-gen contract:
Prepare rtl-gen for model_compare_counter using only model_compare_counter/yaml/model_compare_counter.ssot.yaml and model_compare_counter/rtl/rtl_todo_plan.json, model_compare_counter/rtl/rtl_authoring_plan.json, and packets under model_compare_counter/rtl/authoring_packets. Return exactly one JSON object and nothing else. Success schema: {"files":[{"path":"model_compare_counter/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"},{"path":"model_compare_counter/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"},{"path":"model_compare_counter/list/model_compare_counter.f","kind":"filelist","content":"<filelist>"}]}. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=5946d1d82f02eaa33296490d5185f21234edb676b9e0ba19728ae9a9733bb672. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "model_compare_counter",
        "reason": "6 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      }
    ],
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "dut_compile",
        "owner_module": "model_compare_counter",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "model_compare_counter",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "model_compare_counter",
        "reason": "12 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 5,
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
    "open_required_todos": 13,
    "pass_allowed": false,
    "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
    "stop_conditions": [
      "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
      "Do not claim rtl-gen PASS while pass_allowed is false.",
      "Do not sign off top integration while required connection contracts are missing."
    ],
    "tool_evidence_plan": [
      {
        "artifact": "rtl/rtl_compile.json",
        "artifacts": [
          "model_compare_counter/rtl/rtl_compile.json",
          "model_compare_counter/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py model_compare_counter --top model_compare_counter --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py model_compare_counter --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "model_compare_counter/list/model_compare_counter.f covers the current DUT RTL sources."
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
          "model_compare_counter/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py model_compare_counter --top model_compare_counter",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py model_compare_counter --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "model_compare_counter/list/model_compare_counter.f covers the current DUT RTL/header sources."
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
          "model_compare_counter/rtl/rtl_todo_plan.json",
          "model_compare_counter/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py model_compare_counter --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "12 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ]
  },
  "ip": "model_compare_counter",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__function_model_01.json",
      "kind": "module",
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__function_model_01",
      "required_count": 48,
      "status_counts": {
        "open": 4,
        "pass": 44
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__function_model_02",
      "required_count": 26,
      "status_counts": {
        "open": 2,
        "pass": 24
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/unowned_tasks.json",
      "kind": "unowned",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "",
      "owner_module": "",
      "packet_id": "unowned_tasks",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/model_compare_counter.sv",
      "owner_module": "model_compare_counter",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 9,
      "status_counts": {
        "open": 1,
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 3,
      "owner_file": "rtl/model_compare_counter.sv",
      "owner_module": "model_compare_counter",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 3,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__cycle_model",
      "required_count": 13,
      "status_counts": {
        "pass": 13
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__features.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__features",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__fsm",
      "required_count": 10,
      "status_counts": {
        "pass": 10
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__io_list",
      "required_count": 8,
      "status_counts": {
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__test_requirements",
      "required_count": 8,
      "status_counts": {
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter_core__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "packet_id": "module__model_compare_counter_core__workflow_todo",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__model_compare_counter.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter.sv",
      "owner_module": "model_compare_counter",
      "packet_id": "module__model_compare_counter",
      "required_count": 21,
      "status_counts": {
        "pass": 21
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/model_compare_counter.sv",
      "owner_module": "model_compare_counter",
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
    "source": "model_compare_counter/sim/mismatch_classification.json"
  },
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 0,
    "human_locked_tasks": 0,
    "llm_actionable_packets": 4,
    "llm_actionable_tasks": 10,
    "max_packet_required_tasks": 48,
    "module_packets": 10,
    "next_llm_packets": [
      "module__model_compare_counter_core__function_model_01",
      "module__model_compare_counter_core__function_model_02",
      "unowned_tasks",
      "rtl_gate_evidence_closure"
    ],
    "packet_task_limit": 48,
    "packets": 14,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 161,
    "sliced_module_packets": 9,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 3,
    "total_tasks": 161,
    "unowned_packets": 1
  },
  "target_scale": {},
  "todo_plan_sha256": "5946d1d82f02eaa33296490d5185f21234edb676b9e0ba19728ae9a9733bb672",
  "top": "model_compare_counter",
  "type": "rtl_authoring_plan"
}

Current sim-debug owner repair evidence:
{
  "items": [],
  "owner_workflow": "rtl-gen",
  "source": "model_compare_counter/sim/mismatch_classification.json",
  "status": "none"
}

Current owner RTL file (rtl/model_compare_counter_core.sv):
module model_compare_counter_core #(
    parameter integer COUNT_WIDTH = 8,
    parameter integer STEP_WIDTH  = 4
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    enable,
    input  logic                    clear,
    input  logic [STEP_WIDTH-1:0]   step,
    output logic [COUNT_WIDTH-1:0]  count,
    output logic                    wrapped,
    output logic                    valid
);

    // SSOT fsm.control states: RESET, CLEAR, UPDATE, IDLE
    localparam [1:0] RESET  = 2'd0,
                     CLEAR  = 2'd1,
                     UPDATE = 2'd2,
                     IDLE   = 2'd3;

    logic [1:0] state;
    logic [1:0] next_state;

    // Functional-model aligned architectural state aliases.
    logic [COUNT_WIDTH-1:0] count_q;
    logic                   wrapped_q;
    logic                   valid_q;

    localparam integer SUM_W = COUNT_WIDTH + 1;
    logic [SUM_W-1:0] add_full;

    // Explicit handshake term for cycle_model.handshake_rules.clear_enable_priority.
    logic clear_enable_priority;
    logic priority_clear_wins;

    // 9-bit style carry detect generalized to COUNT_WIDTH+1.
    assign add_full = {1'b0, count_q} + {{(SUM_W-STEP_WIDTH){1'b0}}, step};

    // When clear and enable are both high, clear has priority.
    assign clear_enable_priority = clear & enable;
    assign priority_clear_wins   = clear | clear_enable_priority;

    // Conventional next-state decode for SSOT transitions.
    always @(*) begin
        next_state = state;
        case (state)
            RESET: begin
                if (rst_n == 1'b1) begin
                    next_state = IDLE;
                end else begin
                    next_state = RESET;
                end
            end

            IDLE: begin
                if (priority_clear_wins == 1'b1) begin
                    next_state = CLEAR;
                end else if (enable == 1'b1) begin
                    next_state = UPDATE;
                end else begin
                    next_state = IDLE;
                end
            end

            UPDATE: begin
                // SSOT transition: UPDATE -> IDLE on next cycle.
                next_state = IDLE;
            end

            CLEAR: begin
                // SSOT transition: CLEAR -> IDLE on next cycle.
                next_state = IDLE;
            end

            default: begin
                next_state = RESET;
            end
        endcase
    end

    // Single-cycle accept/update/observe behavior (latency=1):
    // evaluate clear/enable from current edge and commit outputs/state in same edge.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= RESET;
            count_q   <= {COUNT_WIDTH{1'b0}};
            wrapped_q <= 1'b0;
            valid_q   <= 1'b0;
        end else begin
            state <= next_state;

            // FM_CLEAR has priority over FM_UPDATE in same sampled cycle.
            if (priority_clear_wins == 1'b1) begin
                count_q   <= {COUNT_WIDTH{1'b0}};
                wrapped_q <= 1'b0;
                valid_q   <= 1'b0;
            end else if (enable == 1'b1) begin
                // FM_UPDATE: modulo update + overflow pulse.
                count_q   <= add_full[COUNT_WIDTH-1:0];
                wrapped_q <= add_full[COUNT_WIDTH];
                valid_q   <= 1'b1;
            end else begin
                // FM_IDLE: hold count, deassert one-cycle pulses.
                count_q   <= count_q;
                wrapped_q <= 1'b0;
                valid_q   <= 1'b0;
            end
        end
    end

    assign count   = count_q;
    assign wrapped = wrapped_q;
    assign valid   = valid_q;

endmodule


Current RTL module interface digest (all manifest RTL files):
### rtl/model_compare_counter_core.sv
module model_compare_counter_core #(
    parameter integer COUNT_WIDTH = 8,
    parameter integer STEP_WIDTH  = 4
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    enable,
    input  logic                    clear,
    input  logic [STEP_WIDTH-1:0]   step,
    output logic [COUNT_WIDTH-1:0]  count,
    output logic                    wrapped,
    output logic                    valid
);

### rtl/model_compare_counter.sv
module model_compare_counter #(
    parameter integer COUNT_WIDTH = 8,
    parameter integer STEP_WIDTH  = 4
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    enable,
    input  logic                    clear,
    input  logic [STEP_WIDTH-1:0]   step,
    output logic [COUNT_WIDTH-1:0]  count,
    output logic                    wrapped,
    output logic                    valid
);

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
    "source": "model_compare_counter/rtl/rtl_compile.json",
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
    "open_required_todos": 13,
    "orphan_tasks": 0,
    "static_missing": 6,
    "status": "fail"
  },
  "lint": {
    "diagnostics": [],
    "errors": null,
    "passed": null,
    "present": false,
    "repair_hints": [],
    "returncode": null,
    "source": "model_compare_counter/lint/dut_lint.json",
    "style_violation_count": null,
    "suppression_violation_count": null,
    "warnings": null
  },
  "manifest_hierarchy_issues": [],
  "manifest_signal_flow_issues": [],
  "open_required_tasks": [
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "6 static-evidence-required task(s) still lack DUT RTL evidence.",
      "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
      "task_id": "RTL-0007"
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
      "reason": "12 required non-closure TODO(s) remain open.",
      "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
      "task_id": "RTL-0019"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_CLEAR.output_rules.out_count",
      "task_id": "RTL-0051"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_CLEAR.output_rules.out_wrapped",
      "task_id": "RTL-0052"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_CLEAR.output_rules.out_valid",
      "task_id": "RTL-0053"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_UPDATE.output_rules.out_valid",
      "task_id": "RTL-0076"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_IDLE.output_rules.out_wrapped",
      "task_id": "RTL-0098"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_IDLE.output_rules.out_valid",
      "task_id": "RTL-0099"
    },
    {
      "category": "memory.instances",
      "reason": "Task has no RTL owner file.",
      "source_ref": "memory.instances.count_state_ff",
      "task_id": "RTL-0120"
    },
    {
      "category": "memory.instances",
      "reason": "Task has no RTL owner file.",
      "source_ref": "memory.instances.wrapped_state_ff",
      "task_id": "RTL-0121"
    },
    {
      "category": "memory.instances",
      "reason": "Task has no RTL owner file.",
      "source_ref": "memory.instances.valid_state_ff",
      "task_id": "RTL-0122"
    }
  ],
  "source": "model_compare_counter/rtl/rtl_todo_plan.json",
  "static_missing_tasks": [
    {
      "category": "function_model.output_rule",
      "matched_count": 1,
      "matched_terms": [
        "count"
      ],
      "owner_file": "rtl/model_compare_counter_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "count",
        "out",
        "out_count"
      ],
      "source_ref": "function_model.transactions.FM_CLEAR.output_rules.out_count",
      "source_scope": "rtl/model_compare_counter_core.sv",
      "task_id": "RTL-0051"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 1,
      "matched_terms": [
        "wrapped"
      ],
      "owner_file": "rtl/model_compare_counter_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "out_wrapped",
        "wrapped"
      ],
      "source_ref": "function_model.transactions.FM_CLEAR.output_rules.out_wrapped",
      "source_scope": "rtl/model_compare_counter_core.sv",
      "task_id": "RTL-0052"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 1,
      "matched_terms": [
        "valid"
      ],
      "owner_file": "rtl/model_compare_counter_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "out_valid",
        "valid"
      ],
      "source_ref": "function_model.transactions.FM_CLEAR.output_rules.out_valid",
      "source_scope": "rtl/model_compare_counter_core.sv",
      "task_id": "RTL-0053"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 1,
      "matched_terms": [
        "valid"
      ],
      "owner_file": "rtl/model_compare_counter_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "out_valid",
        "valid"
      ],
      "source_ref": "function_model.transactions.FM_UPDATE.output_rules.out_valid",
      "source_scope": "rtl/model_compare_counter_core.sv",
      "task_id": "RTL-0076"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 1,
      "matched_terms": [
        "wrapped"
      ],
      "owner_file": "rtl/model_compare_counter_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "out_wrapped",
        "wrapped"
      ],
      "source_ref": "function_model.transactions.FM_IDLE.output_rules.out_wrapped",
      "source_scope": "rtl/model_compare_counter_core.sv",
      "task_id": "RTL-0098"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 1,
      "matched_terms": [
        "valid"
      ],
      "owner_file": "rtl/model_compare_counter_core.sv",
      "required_match_count": 2,
      "required_terms": [
        "out",
        "out_valid",
        "valid"
      ],
      "source_ref": "function_model.transactions.FM_IDLE.output_rules.out_valid",
      "source_scope": "rtl/model_compare_counter_core.sv",
      "task_id": "RTL-0099"
    }
  ]
}

Current RTL file snapshots for gate/tool-evidence repair:
<included only for gate/tool-evidence packets>

Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__model_compare_counter_core__function_model_02.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 5,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 3,
      "key": "function_model_02",
      "module_task_count": 120,
      "rule": "Owner module model_compare_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "function_model",
      "section_chunk_count": 2,
      "section_chunk_index": 2,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/model_compare_counter_core.sv",
      "name": "model_compare_counter_core",
      "refs": [
        "cycle_model",
        "cycle_model.handshake_rules",
        "cycle_model.ordering",
        "cycle_model.pipeline",
        "dataflow",
        "decomposition",
        "features",
        "fsm",
        "fsm.control",
        "function_model",
        "function_model.state_variables",
        "function_model.transactions",
        "function_model.transactions.FM_CLEAR",
        "function_model.transactions.FM_IDLE",
        "function_model.transactions.FM_UPDATE",
        "io_list",
        "io_list.clock_domains",
        "io_list.interfaces",
        "io_list.resets",
        "test_requirements"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/model_compare_counter_core.sv",
        "name": "model_compare_counter_core",
        "wiring_only": false
      },
      {
        "file": "rtl/model_compare_counter.sv",
        "name": "model_compare_counter",
        "wiring_only": true
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
    "llm_actionable_open_count": 2,
    "open_required_count": 2,
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
  "ip": "model_compare_counter",
  "kind": "module",
  "owner_file": "rtl/model_compare_counter_core.sv",
  "owner_module": "model_compare_counter_core",
  "packet_id": "module__model_compare_counter_core__function_model_02",
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
      "function_model.output": 9,
      "function_model.output_rule": 3,
      "function_model.precondition": 1,
      "function_model.side_effect": 2,
      "function_model.state_update": 3,
      "function_model.transaction": 1
    },
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 3,
      "key": "function_model_02",
      "module_task_count": 120,
      "rule": "Owner module model_compare_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "function_model",
      "section_chunk_count": 2,
      "section_chunk_index": 2,
      "task_limit": 48
    },
    "open_required_count": 2,
    "required_count": 26,
    "source_refs": [
      "function_model.transactions.FM_UPDATE.side_effects.side_effect_1",
      "function_model.transactions.FM_IDLE",
      "function_model.transactions.FM_IDLE.preconditions.precondition_0",
      "function_model.transactions.FM_IDLE.inputs.input_0",
      "function_model.transactions.FM_IDLE.inputs.input_1",
      "function_model.transactions.FM_IDLE.inputs.input_2",
      "function_model.transactions.FM_IDLE.inputs.input_3",
      "function_model.transactions.FM_IDLE.outputs.output_0",
      "function_model.transactions.FM_IDLE.outputs.output_1",
      "function_model.transactions.FM_IDLE.outputs.output_2",
      "function_model.transactions.FM_IDLE.outputs.out_count",
      "function_model.transactions.FM_IDLE.outputs.out_wrapped",
      "function_model.transactions.FM_IDLE.outputs.out_valid",
      "function_model.transactions.FM_IDLE.outputs.count_q",
      "function_model.transactions.FM_IDLE.outputs.wrapped_q",
      "function_model.transactions.FM_IDLE.outputs.valid_q",
      "function_model.transactions.FM_IDLE.output_rules.out_count",
      "function_model.transactions.FM_IDLE.output_rules.out_wrapped",
      "function_model.transactions.FM_IDLE.output_rules.out_valid",
      "function_model.transactions.FM_IDLE.state_updates.count_q",
      "function_model.transactions.FM_IDLE.state_updates.wrapped_q",
      "function_model.transactions.FM_IDLE.state_updates.valid_q",
      "function_model.transactions.FM_IDLE.side_effects.side_effect_0",
      "function_model.invariants.invariant_0"
    ],
    "status_counts": {
      "open": 2,
      "pass": 24
    },
    "task_count": 26
  },
  "tasks": [
    {
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM_UPDATE: side_effect_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_UPDATE.side_effects.side_effect_1",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for enabled_increment"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_UPDATE.side_effects.side_effect_1.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.\nSSOT item context: id=FM_UPDATE; name=enabled_increment; port=[\"count\", \"wrapped\", \"valid\"]; signal=[\"wrapped pulse is asserted only for overflowing additions.\"]; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "count",
        "count_q",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0081",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_UPDATE.side_effects.side_effect_1",
      "ssot_context": {
        "id": "FM_UPDATE",
        "name": "enabled_increment",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[\"wrapped pulse is asserted only for overflowing additions.\"]",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_UPDATE.side_effects.side_effect_1"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.transaction",
      "content": "Implement transaction FM_IDLE",
      "criteria": [
        "Acceptance/precondition logic is explicit in RTL",
        "All outputs and side effects occur exactly once per accepted transaction",
        "The transaction is covered by equivalence goals and scoreboard observations downstream",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv"
      ],
      "detail": "Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.\nSSOT ref: function_model.transactions.FM_IDLE.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold.",
      "evidence_terms": [],
      "id": "RTL-0082",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE"
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
      "category": "function_model.precondition",
      "content": "Implement precondition for FM_IDLE: precondition_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.preconditions.precondition_0",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.preconditions.precondition_0.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: value=transaction is accepted under cycle_model rules.",
      "evidence_terms": [],
      "id": "RTL-0083",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.preconditions.precondition_0",
      "ssot_context": {
        "value": "transaction is accepted under cycle_model rules"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.preconditions.precondition_0"
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
      "category": "function_model.input",
      "content": "Implement input for FM_IDLE: input_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_0",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.inputs.input_0.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[\"clear\"]; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "count",
        "count_q",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0084",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.inputs.input_0",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[\"clear\"]",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.inputs.input_0"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.input",
      "content": "Implement input for FM_IDLE: input_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_1",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.inputs.input_1.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[\"enable\"]; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "count",
        "count_q",
        "enable",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0085",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.inputs.input_1",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[\"enable\"]",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.inputs.input_1"
      ],
      "static_evidence": {
        "matched_count": 7,
        "matched_terms": [
          "count",
          "count_q",
          "enable",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "count_q",
          "enable",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.input",
      "content": "Implement input for FM_IDLE: input_2",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_2",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.inputs.input_2.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[\"step\"]; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "count",
        "count_q",
        "step",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0086",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.inputs.input_2",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[\"step\"]",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.inputs.input_2"
      ],
      "static_evidence": {
        "matched_count": 7,
        "matched_terms": [
          "count",
          "count_q",
          "step",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "count_q",
          "step",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.input",
      "content": "Implement input for FM_IDLE: input_3",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_3",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.inputs.input_3.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[\"count_q\"]; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "count",
        "count_q",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0087",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.inputs.input_3",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[\"count_q\"]",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.inputs.input_3"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.output",
      "content": "Implement output for FM_IDLE: output_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_0",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.outputs.output_0.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[\"count == count_q\"]; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "count",
        "count_q",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0088",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.outputs.output_0",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[\"count == count_q\"]",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.outputs.output_0"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.output",
      "content": "Implement output for FM_IDLE: output_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_1",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.outputs.output_1.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[\"wrapped == 0\"]; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "count",
        "count_q",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0089",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.outputs.output_1",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[\"wrapped == 0\"]",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.outputs.output_1"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.output",
      "content": "Implement output for FM_IDLE: output_2",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_2",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.outputs.output_2.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[\"valid == 0\"]; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "count",
        "count_q",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0090",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.outputs.output_2",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[\"valid == 0\"]",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.outputs.output_2"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.output",
      "content": "Implement output for FM_IDLE: out_count",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.out_count",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.outputs.out_count.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[{\"description\": \"Mirrored from executable output_rules for SSOT validator completeness.\", \"expr\": \"count_q\", \"name\":...; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "Mirrored",
        "SSOT",
        "count",
        "count_q",
        "out",
        "out_count",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0091",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.outputs.out_count",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[{\"description\": \"Mirrored from executable output_rules for SSOT validator completeness.\", \"expr\": \"count_q\", \"name\":...",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.outputs.out_count"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "Mirrored",
          "SSOT",
          "count",
          "count_q",
          "out",
          "out_count",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.output",
      "content": "Implement output for FM_IDLE: out_wrapped",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.out_wrapped",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.outputs.out_wrapped.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[{\"description\": \"Mirrored from executable output_rules for SSOT validator completeness.\", \"expr\": \"0\", \"name\": \"out_...; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "Mirrored",
        "SSOT",
        "count",
        "count_q",
        "out",
        "out_wrapped",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0092",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.outputs.out_wrapped",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[{\"description\": \"Mirrored from executable output_rules for SSOT validator completeness.\", \"expr\": \"0\", \"name\": \"out_...",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.outputs.out_wrapped"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "Mirrored",
          "SSOT",
          "count",
          "count_q",
          "out",
          "out_wrapped",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.output",
      "content": "Implement output for FM_IDLE: out_valid",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.out_valid",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.outputs.out_valid.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[{\"description\": \"Mirrored from executable output_rules for SSOT validator completeness.\", \"expr\": \"0\", \"name\": \"out_...; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "Mirrored",
        "SSOT",
        "count",
        "count_q",
        "out",
        "out_valid",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0093",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.outputs.out_valid",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[{\"description\": \"Mirrored from executable output_rules for SSOT validator completeness.\", \"expr\": \"0\", \"name\": \"out_...",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.outputs.out_valid"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "Mirrored",
          "SSOT",
          "count",
          "count_q",
          "out",
          "out_valid",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.output",
      "content": "Implement output for FM_IDLE: count_q",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.count_q",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.outputs.count_q.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[{\"description\": \"Mirrored from executable state_updates for SSOT validator completeness.\", \"expr\": \"count_q\", \"state...; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "Mirrored",
        "SSOT",
        "count",
        "count_q",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0094",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.outputs.count_q",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[{\"description\": \"Mirrored from executable state_updates for SSOT validator completeness.\", \"expr\": \"count_q\", \"state...",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.outputs.count_q"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "Mirrored",
          "SSOT",
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
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
      "category": "function_model.output",
      "content": "Implement output for FM_IDLE: wrapped_q",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.wrapped_q",
        "Primary implementation evidence is in rtl/model_compare_counter_core.sv",
        "DUT port [\"count\", \"wrapped\", \"valid\"] is the implementation/observation point for idle_hold"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_IDLE.outputs.wrapped_q.\nOwner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.\nSSOT item context: id=FM_IDLE; name=idle_hold; port=[\"count\", \"wrapped\", \"valid\"]; signal=[{\"description\": \"Mirrored from executable state_updates for SSOT validator completeness.\", \"expr\": \"0\", \"state\": \"wr...; state=[\"count_q\", \"wrapped_q\", \"valid_q\"].",
      "evidence_terms": [
        "Mirrored",
        "SSOT",
        "count",
        "count_q",
        "valid",
        "valid_q",
        "wrapped",
        "wrapped_q"
      ],
      "id": "RTL-0095",
      "owner_file": "rtl/model_compare_counter_core.sv",
      "owner_module": "model_compare_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_IDLE.outputs.wrapped_q",
      "ssot_context": {
        "id": "FM_IDLE",
        "name": "idle_hold",
        "port": "[\"count\", \"wrapped\", \"valid\"]",
        "signal": "[{\"description\": \"Mirrored from executable state_updates for SSOT validator completeness.\", \"expr\": \"0\", \"state\": \"wr...",
        "state": "[\"count_q\", \"wrapped_q\", \"valid_q\"]"
      },
      "ssot_refs": [
        "function_model.transactions.FM_IDLE.outputs.wrapped_q"
      ],
      "static_evidence": {
        "matched_count": 6,
        "matched_terms": [
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "Mirrored",
          "SSOT",
          "count",
          "count_q",
          "valid",
          "valid_q",
          "wrapped",
          "wrapped_q"
        ],
        "source_scope": "rtl/model_compare_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
   
... <truncated 31831 chars>

Current packet Markdown (rtl/authoring_packets/module__model_compare_counter_core__function_model_02.md):
# RTL Authoring Packet: module__model_compare_counter_core__function_model_02

- Kind: module
- Owner module: model_compare_counter_core
- Owner file: rtl/model_compare_counter_core.sv
- Task count: 26
- Required tasks: 26

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
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_CLEAR, function_model.transactions.FM_IDLE, function_model.transactions.FM_UPDATE, io_list
- Module slice: 3/9 section=function_model task_limit=48
- Slice rule: Owner module model_compare_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0081: Implement side effect for FM_UPDATE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_UPDATE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.side_effects.side_effect_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["wrapped pulse is asserted only for overflowing additions."]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.side_effects.side_effect_1

### RTL-0082: Implement transaction FM_IDLE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_IDLE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_IDLE.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_IDLE
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_IDLE

### RTL-0083: Implement precondition for FM_IDLE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_IDLE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.preconditions.precondition_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: value=transaction is accepted under cycle_model rules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_IDLE.preconditions.precondition_0

### RTL-0084: Implement input for FM_IDLE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_IDLE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.inputs.input_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["clear"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.inputs.input_0

### RTL-0085: Implement input for FM_IDLE: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_IDLE.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.inputs.input_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["enable"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.inputs.input_1

### RTL-0086: Implement input for FM_IDLE: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_IDLE.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.inputs.input_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["step"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.inputs.input_2

### RTL-0087: Implement input for FM_IDLE: input_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_IDLE.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.inputs.input_3.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["count_q"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_3
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.inputs.input_3

### RTL-0088: Implement output for FM_IDLE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.output_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["count == count_q"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.output_0

### RTL-0089: Implement output for FM_IDLE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.output_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["wrapped == 0"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.output_1

### RTL-0090: Implement output for FM_IDLE: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.output_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["valid == 0"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.output_2

### RTL-0091: Implement output for FM_IDLE: out_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.out_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.out_count.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "count_q", "name":...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.out_count
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.out_count

### RTL-0092: Implement output for FM_IDLE: out_wrapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_
... <truncated 20475 chars>