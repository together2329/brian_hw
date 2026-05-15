RTL-GEN PACKET MODE for gpio. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "gpio/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "gpio/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "gpio/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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

Current packet: module__gpio_regs__test_requirements
kind: module
work queue: 3/4 active packets (2 closed packets skipped from 15 total)
batch limit: 4; deferred active packets after this batch: 9
owner_module: gpio_regs
owner_file: rtl/gpio_regs.sv

SSOT observable latency contract:
{
  "cycle_model.latency": {
    "control_to_state": {
      "description": "dir_in/dout_in sampled on next rising edge",
      "max_cycles": 1,
      "min_cycles": 1
    },
    "pad_to_din": {
      "description": "input bits sample pad_in on rising edge",
      "max_cycles": 1,
      "min_cycles": 1
    },
    "state_to_outputs": {
      "description": "oe_o and pad_o combinational from state",
      "max_cycles": 0,
      "min_cycles": 0
    }
  },
  "cycle_model.pipeline": [
    {
      "action": "Clear dir_q/dout_q/din_q when rst_n=0",
      "cycle": "async",
      "stage": "S0_RESET"
    },
    {
      "action": "Latch dir_in->dir_q and dout_in->dout_q at rising edge",
      "cycle": "N",
      "stage": "S1_LATCH_CONTROL"
    },
    {
      "action": "Sample pad_in into din_q only for dir_q=0 bits",
      "cycle": "N",
      "stage": "S2_SAMPLE_INPUTS"
    },
    {
      "action": "Drive oe_o/pad_o from registered state",
      "cycle": "N+comb",
      "stage": "S3_DRIVE_OUTPUTS"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": "legal transaction accepted under cycle_model.handshake_rules",
  "timing.latency_budget": [
    {
      "cycles": 1,
      "path": "dir_in->dir_q",
      "requirement": "fixed"
    },
    {
      "cycles": 1,
      "path": "dout_in->dout_q",
      "requirement": "fixed"
    },
    {
      "cycles": 0,
      "path": "dir_q->oe_o",
      "requirement": "combinational"
    },
    {
      "cycles": 0,
      "dout_q->pad_o": null,
      "path": "dir_q",
      "requirement": "combinational"
    },
    {
      "cycles": 1,
      "path": "pad_in->din_q",
      "requirement": "fixed_for_input_bits"
    }
  ]
}

Locked SSOT YAML excerpt (gpio/yaml/gpio.ssot.yaml):
top_module:
  name: gpio
  file: rtl/gpio.sv
  version: '1.0'
  type: peripheral
  description: Parameterizable bidirectional GPIO smoke-fixture peripheral with direct register-style control ports
  reference_spec: gpio/req/gpio_requirements.md
  target:
    technology: generic
    clock_freq_mhz: 200
    area_um2: null
    power_mw: null
sub_modules:
- name: gpio_regs
  file: rtl/gpio_regs.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - function_model.transactions.FM1_LATCH_CONTROL
  - function_model.transactions.FM4_ASYNC_RESET
  - registers.register_list.DIR_Q
  - registers.register_list.DOUT_Q
  - cycle_model.pipeline.S1_LATCH_CONTROL
  source_sections:
  - function_model
  - registers
  - cycle_model
  - features
  - dataflow
  - fsm
  - decomposition
  - test_requirements
  function_model_refs:
  - function_model.transactions.FM1_LATCH_CONTROL
  - function_model.transactions.FM4_ASYNC_RESET
  - function_model.state_variables
  - function_model.transactions.FM2_SAMPLE_INPUTS
  - function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
  register_refs:
  - registers.register_list.DIR_Q
  - registers.register_list.DOUT_Q
  - registers.register_list
  cycle_model_refs:
  - cycle_model.pipeline.S1_LATCH_CONTROL
  - cycle_model
  description: Sequential register block for direction/output state
  feature_refs:
  - features
  dataflow_refs:
  - dataflow
  fsm_refs:
  - fsm
  decomposition_refs:
  - decomposition
  test_refs:
  - test_requirements
- name: gpio_input_sampler
  file: rtl/gpio_input_sampler.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - function_model.transactions.FM2_SAMPLE_INPUTS
  - registers.register_list.DIN_Q
  - cycle_model.pipeline.S2_SAMPLE_INPUTS
  source_sections: &id001
  - function_model
  - registers
  - cycle_model
  function_model_refs:
  - function_model.transactions.FM2_SAMPLE_INPUTS
  register_refs:
  - registers.register_list.DIN_Q
  cycle_model_refs:
  - cycle_model.pipeline.S2_SAMPLE_INPUTS
  description: Sequential input sampler with direction mask
- name: gpio_pad_logic
  file: rtl/gpio_pad_logic.sv
  ownership: manifest
  ssot_gen: true
  wiring_only: false
  implements:
  - function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
  - cycle_model.handshake_rules.HR_COMB_OUTPUTS
  - io_list.interfaces.gpio_pad
  source_sections: &id002
  - function_model
  - cycle_model
  - io_list
  function_model_refs:
  - function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
  cycle_model_refs:
  - cycle_model.handshake_rules.HR_COMB_OUTPUTS
  ssot_refs:
  - io_list.interfaces.gpio_pad
  description: Combinational output-enable/output-data generation
- name: gpio
  file: rtl/gpio.sv
  ownership: manifest
  ssot_gen: false
  implements:
  - integration.connections
  - rtl_contract
  source_sections: &id003
  - integration
  - rtl_contract
  description: Top-level integration and wiring
decomposition:
  strategy: manifest_owned_leaf_decomposition
  units:
  - id: regs
    kind: control_state
    source_refs:
    - function_model.transactions.FM1_LATCH_CONTROL
    - function_model.transactions.FM4_ASYNC_RESET
    rtl_candidates:
    - gpio_regs
    verification_impact:
    - test_requirements.scenarios.SC06
    - test_requirements.scenarios.SC09
  - id: sample
    kind: input_capture
    source_refs:
    - function_model.transactions.FM2_SAMPLE_INPUTS
    rtl_candidates:
    - gpio_input_sampler
    verification_impact:
    - test_requirements.scenarios.SC07
  - id: drive
    kind: combinational_output
    source_refs:
    - function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
    rtl_candidates:
    - gpio_pad_logic
    verification_impact:
    - test_requirements.scenarios.SC08
  owners:
  - module: gpio_regs
    file: rtl/gpio_regs.sv
    responsibility: Sequential register block for direction/output state
    source_sections:
    - function_model
    - registers
    - cycle_model
  - module: gpio_input_sampler
    file: rtl/gpio_input_sampler.sv
    responsibility: Sequential input sampler with direction mask
    source_sections: *id001
  - module: gpio_pad_logic
    file: rtl/gpio_pad_logic.sv
    responsibility: Combinational output-enable/output-data generation
    source_sections: *id002
  - module: gpio
    file: rtl/gpio.sv
    responsibility: Top-level integration and wiring
    source_sections: *id003
  integration_policy: Top-level wiring must be backed by integration.connections or sub_modules[].connections before signoff.
  source_refs:
  - sub_modules
  - function_model
  - cycle_model
  - integration
parameters:
- name: WIDTH
  default: 8
  type: int
  description: Number of GPIO pins
  drives:
  - rtl/gpio.sv
  - rtl/gpio_regs.sv
  - rtl/gpio_input_sampler.sv
  - rtl/gpio_pad_logic.sv
  - sim/tb_top.sv
io_list:
  clock_domains:
  - name: clk
    frequency_mhz: 200
    description: Single functional clock
    ports:
    - name: clk
      width: 1
      direction: input
      description: Primary rising-edge clock
  resets:
  - name: rst_n
    polarity: active_low
    sync_async: async_assert_sync_deassert
    description: Asynchronous assert reset
    ports:
    - name: rst_n
      width: 1
      direction: input
      description: Active-low reset
  interfaces:
  - name: gpio_ctrl
    type: custom
    role: slave
    description: Direct control inputs
    ports:
    - name: dir_in
      width: WIDTH
      direction: input
      description: 0=input 1=output
    - name: dout_in
      width: WIDTH
      direction: input
      description: Output data input
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: gpio_pad
    type: custom
    role: master
    description: Pad ring signals
    ports:
    - name: pad_in
      width: WIDTH
      direction: input
      description: Sampled pad value
    - name: oe_o
      width: WIDTH
      direction: output
      description: Output-enable
    - name: pad_o
      width: WIDTH
      direction: output
      description: Output drive data
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: gpio_state
    type: custom
    role: status
    description: Registered internal state outputs
    ports:
    - name: dir_q
      width: WIDTH
      direction: output
      description: Registered direction state
    - name: dout_q
      width: WIDTH
      direction: output
      description: Registered output data state
    - name: din_q
      width: WIDTH
      direction: output
      description: Registered input sample state
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
features:
- name: Per-bit direction control
  trigger: dir_in sampled on rising clk
  datapath: dir_in -> dir_q -> oe_o and pad_o mask
  control: single-cycle latch
  output: oe_o[i]=1 when dir_q[i]=1
- name: Registered output data
  trigger: dout_in sampled on rising clk
  datapath: dout_in -> dout_q -> pad_o when output mode
  control: single-cycle latch
  output: pad_o follows dout_q only for dir_q=1 bits
- name: Direction-masked input sampling
  trigger: rising clk
  datapath: pad_in sampled into din_q when dir_q=0
  control: per-bit conditional update
  output: output-mode bits hold prior din_q
dataflow:
  control_path:
    source: dir_in,dout_in
    sequence: rising clk samples controls into dir_q,dout_q
  output_path:
    source: dir_q,dout_q
    sequence: combinational derive oe_o,pad_o
  input_path:
    source: pad_in
    sequence: at each rising clk sample into din_q only for bits where dir_q=0
function_model:
  purpose: Behavioral contract for GPIO state update, input sampling, and pad outputs
  state_variables:
  - name: dir_state
    source: io_list.interfaces.gpio_state.ports.dir_q
    reset: 0
    description: Registered direction vector
  - name: dout_state
    source: io_list.interfaces.gpio_state.ports.dout_q
    reset: 0
    description: Registered output data vector
  - name: din_state
    source: io_list.interfaces.gpio_state.ports.din_q
    reset: 0
    description: Registered sampled input vector
  transactions:
  - id: FM1_LATCH_CONTROL
    name: latch_direction_and_output_data
    preconditions:
    - rst_n is deasserted
    - rising edge of clk
    inputs:
    - dir_in
    - dout_in
    outputs:
    - dir_state equals dir_in after sampling edge
    - dout_state equals dout_in after sampling edge
    side_effects:
    - dir_q and dout_q update atomically each cycle
    output_rules:
    - name: dir_q_next
      expr: dir_in
      width: WIDTH
      port: dir_q
    - name: dout_q_next
      expr: dout_in
      width: WIDTH
      port: dout_q
  - id: FM2_SAMPLE_INPUTS
    name: sample_pad_inputs_for_input_bits_only
    preconditions:
    - rst_n is deasserted
    - rising edge of clk
    inputs:
    - pad_in
    - dir_state
    - din_state
    outputs:
    - din_state bits with dir_state=0 sample pad_in
    - din_state bits with dir_state=1 hold previous value
    side_effects:
    - din_q updates only on input-configured bits
    output_rules:
    - name: din_q_masked_next
      expr: (din_q & dir_q) | (pad_in & ~dir_q)
      width: WIDTH
      port: din_q
  - id: FM3_DRIVE_PAD_OUTPUTS
    name: derive_output_enable_and_pad_drive
    preconditions:
    - dir_state and dout_state are defined
    inputs:
    - dir_state
    - dout_state
    outputs:
    - oe_o equals dir_state
    - pad_o equals dout_state where dir_state is 1 else 0
    side_effects:
    - no sequential state change
    output_rules:
    - name: oe_comb
      expr: dir_q
      width: WIDTH
      port: oe_o
    - name: pad_comb
      expr: dout_q & dir_q
      width: WIDTH
      port: pad_o
  - id: FM4_ASYNC_RESET
    name: asynchronous_reset_clears_state
    preconditions:
    - rst_n asserted low
    outputs:
    - dir_state zero
    - dout_state zero
    - din_state zero
    - oe_o zero
    - pad_o zero
    side_effects:
    - all architectural state cleared independent of clk
    output_rules:
    - name: dir_reset
      expr: '0'
      width: WIDTH
      port: dir_q
    - name: dout_reset
      expr: '0'
      width: WIDTH
      port: dout_q
    - name: din_reset
      expr: '0'
      width: WIDTH
      port: din_q
  invariants:
  - oe_o equals dir_q at all times after combinational settle
  - pad_o equals (dout_q & dir_q) bitwise
  - din_q output-configured bits hold unless reset
  - no hidden state beyond dir_q, dout_q, din_q
cycle_model:
  purpose: Cycle-accurate timing and ordering for GPIO behavior
  executable: pymtl3
  backend_policy: Use PyMTL3 for cycle shell and direct Python oracle checks
  clock: clk
  reset:
    assertion: rst_n low asynchronously clears state
    deassertion: state usable on first rising edge after deassertion
  latency:
    control_to_state:
      min_cycles: 1
      max_cycles: 1
      description: dir_in/dout_in sampled on next rising edge
    state_to_outputs:
      min_cycles: 0
      max_cycles: 0
      description: oe_o and pad_o combinational from state
    pad_to_din:
      min_cycles: 1
      max_cycles: 1
      description: input bits sample pad_in on rising edge
  handshake_rules:
  - id: HR_SYNC_SAMPLE
    signal: clk
    rule: Inputs sampled only on rising edge
  - id: HR_INPUT_MASK_SAMPLE
    signal: din_q
    rule: din_q bit updates only when corresponding dir_q bit is 0
  - id: HR_COMB_OUTPUTS
    signal: oe_o/pad_o
    rule: Outputs are pure combinational functions of registered state
  pipeline:
  - stage: S0_RESET
    cycle: async
    action: Clear dir_q/dout_q/din_q when rst_n=0
  - stage: S1_LATCH_CONTROL
    cycle: N
    action: Latch dir_in->dir_q and dout_in->dout_q at rising edge
  - stage: S2_SAMPLE_INPUTS
    cycle: N
    action: Sample pad_in into din_q only for dir_q=0 bits
  - stage: S3_DRIVE_OUTPUTS
    cycle: N+comb
    action: Drive oe_o/pad_o from registered state
  ordering:
  - sequential updates occur at edge, combinational outputs settle after edge
  - reset dominates non-reset behavior
  backpressure:
  - no ready/valid protocol in this GPIO fixture
  observability:
  - each function_model transaction maps to cycle stages and test scenarios
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
  - name: clk
    frequency_mhz: 200
    description: Single GPIO domain
  reset_scheme:
    signal: rst_n
    polarity: active_low
    type: async_assert_sync_deassert
cdc_requirements:
  crossings: []
  synchronizers: []
  note: Single clock domain
rdc_requirements:
  crossings: []
  synchronizers: []
  note: Single reset domain
registers:
  config:
    register_width: 32
    addr_width: 4
    byte_addressable: true
    note: Logical architectural registers only; no external bus interface
  register_list:
  - name: DIR_Q
    offset: 0
    width: 32
    access: rw
    reset: 0
    category: state
    description: Registered direction state sampled from dir_in[WIDTH-1:0]
    fields:
    - name: dir
      bits:
      - 7
      - 0
      access: rw
      reset: 0
      description: 0=input 1=output
      write_effect: Updated by sampled dir_in each rising edge
  - name: DOUT_Q
    offset: 4
    width: 32
    access: rw
    reset: 0
    category: state
    description: Registered output data sampled from dout_in[WIDTH-1:0]
    fields:
    - name: dout
      bits:
      - 7
      - 0
      access: rw
      reset: 0
      description: Output data state
      write_effect: Updated by sampled dout_in each rising edge
  - name: DIN_Q
    offset: 8
    width: 32
    access: ro
    reset: 0
    category: state
    description: Registered sampled input data
    fields:
    - name: din
      bits:
      - 7
      - 0
      access: ro
      reset: 0
      description: Sampled from pad_in when dir_q indicates input
memory:
  instances:
  - name: dir_q_ff
    type: register
    depth: 1
    width: WIDTH
    read_ports: 1
    write_ports: 1
    latency: 0
    description: Direction flops
  - name: dout_q_ff
    type: register
    depth: 1
    width: WIDTH
    read_ports: 1
    write_ports: 1
    latency: 0
    description: Output-data flops
  - name: din_q_ff
    type: register
    depth: 1
    width: WIDTH
    read_ports: 1
    write_ports: 1
    latency: 0
    description: Input-sample flops
  note: No SRAM/FIFO structures
interrupts:
  sources: []
  output:
    signal: null
    polarity: null
    type: none
  note: No interrupt support by requirement
fsm:
  control:
    states:
    - ACTIVE
    transitions:
    - from: ACTIVE
      to: ACTIVE
      condition: normal operation each cycle
    note: Stateless transfer behavior with single architectural mode
timing:
  target_clocks:
  - domain: clk
    target_mhz: 200
    duty_cycle_pct: 50
  latency_budget:
  - path: dir_in->dir_q
    cycles: 1
    requirement: fixed
  - path: dout_in->dout_q
    cycles: 1
    requirement: fixed
  - path: dir_q->oe_o
    cycles: 0
    requirement: combinational
  - path: dir_q
    dout_q->pad_o: null
    cycles: 0
    requirement: combinational
  - path: pad_in->din_q
    cycles: 1
    requirement: fixed_for_input_bits
  sta_expectations:
  - Meet single-clock setup/hold at target frequency
  - Check reset recovery/removal for rst_n
power:
  domains:
  - name: VDD_GPIO
    voltage: nominal
    elements:
    - all_gpio_logic
  power_states:
  - name: true
    description: Normal operation
  - name: RESET
    description: rst_n asserted and state cleared
  clock_gating: none
  retention: not required
  upf_required: false
security:
  classification: non-sensitive peripheral control
  assets:
  - Correct direction gating to avoid unintended output drive
  - Integrity of sampled input state din_q
  threat_model:
  - Accidental misconfiguration of direction
  - Glitchy pad input sampled at clock edge
  assumptions:
  - System-level privilege and access control are out of scope
  privilege_model: controlled by SoC integration policy
error_handling:
  error_sources:
  - id: x_propagation_from_pad
    condition: pad_in contains unknown in simulation
    architectural_effect: unknown may propagate into din_q for sampled input bits
  propagation:
  - No interrupt or fault output in this fixture
  recovery:
  - Assert rst_n low to restore deterministic zero state
debug_observability:
  waveform_must_probe:
  - clk
  - rst_n
  - dir_in
  - dout_in
  - pad_in
  - dir_q
  - dout_q
  - din_q
  - oe_o
  - pad_o
  trace_events:
  - name: EV_CONTROL_LATCH
    trigger: rising_clk
    payload:
    - dir_in
    - dout_in
    - dir_q
    - dout_q
  - name: EV_INPUT_SAMPLE
    trigger: rising_clk
    payload:
    - pad_in
    - dir_q
    - din_q
  - name: EV_RESET
    trigger: rst_n_falling
    payload:
    - dir_q
    - dout_q
    - din_q
  status_outputs:
  - dir_q
  - dout_q
  - din_q
integration:
  bus_attachment:
    type: none
    description: No APB/AXI/CSR bus; direct ports only
  dependencies:
  - pad_ring interface for pad_in/oe_o/pad_o
  - clock/reset distribution for clk/rst_n
  connections:
  - module: gpio_regs
    port: clk
    signal: clk
  - module: gpio_regs
    port: rst_n
    signal: rst_n
  - module: gpio_regs
    port: dir_in
    signal: dir_in
  - module: gpio_regs
    port: dout_in
    signal: dout_in
  - module: gpio_regs
    port: dir_q
    signal: dir_q
  - module: gpio_regs
    port: dout_q
    signal: dout_q
  - module: gpio_input_sampler
    port: clk
    signal: clk
  - module: gpio_input_sampler
    port: rst_n
    signal: rst_n
  - module: gpio_input_sampler
    port: pad_in
    signal: pad_in
  - module: gpio_input_sampler
    port: dir_q
    signal: dir_q
  - module: gpio_input_sampler
    port: din_q
    signal: din_q
  - module: gpio_pad_logic
    port: dir_q
    signal: dir_q
  - module: gpio_pad_logic
    port: dout_q
    signal: dout_q
  - module: gpio_pad_logic
    port: oe_o
    signal: oe_o
  - module: gpio_pad_logic
    port: pad_o
    signal: pad_o
  integration_notes:
  - Integrator must connect all io_list ports and preserve reset/clock assumptions
  connection_contract_status: missing machine-readable module wiring; child RTL drafts may proceed from owner packets, but top integration/signoff
    must stay blocked until SSOT authors integration.connections or sub_modules[].connections with module/port/signal records
dft:
  scan_required: true
  controllability:
  - dir_q, dout_q, din_q flops scannable
  - primary inputs controllable in test mode
  observability:
  - dir_q, dout_q, din_q visible at outputs
  - oe_o and pad_o observable combinationally
  mbist: not applicable
  mbist_required: false
synthesis:
  dialect: systemverilog_2012
  constraints:
  - Single clock constraint on clk
  - Reset recovery/removal constraints for rst_n
  - WIDTH >= 1
  required_outputs:
  - gate_level_netlist
  - area_report
  - timing_report
  - unconstrained_path_report
  top_module: gpio
pnr:
  utilization_pct: 20
  aspect_ratio: 1.0
  core_space_um: 1.0
  global_density: 0.5
  io_layers:
    horizontal: met3
    vertical: met2
  cts:
    buf_list:
    - sky130_fd_sc_hd__clkbuf_4
    - sky130_fd_sc_hd__clkbuf_8
  routing:
    signal_layers:
      min: met1
      max: met4
    drc_waivers: []
  cts_buf_list:
  - sky130_fd_sc_hd__clkbuf_4
  - sky130_fd_sc_hd__clkbuf_8
coding_rules:
  verilog_style: systemverilog_2012
  file_extension: .sv
  parameter_header: rtl/gpio_param.vh
  conventions:
  - nonblocking in sequential always blocks
  - blocking in combinational always blocks
  - no inferred latches
  - active-low async reset semantics
  - parameterized width usage
  lint_waivers:
  - none_expected
reuse_modules: []
custom:
  assumptions:
  - no metastability hardening; pad_in sampled directly
  note: minimal smoke-fixture IP
dir_structure:
  template_dirs:
    rtl: templates/rtl/
    sim: templates/sim/
  output_dirs:
    rtl: rtl/
    sim: sim/
    firmware: firmware/
    docs: docs/
  yaml_dir: yaml/
  generators_dir: generators/
filelist:
  headers:
  - rtl/gpio_param.vh
  rtl:
  - rtl/gpio_regs.sv
  - rtl/gpio_input_sampler.sv
  - rtl/gpio_pad_logic.sv
  - rtl/gpio.sv
  sim:
  - sim/tb_top.sv
  - sim/tb_gpio_scoreboard.py
  firmware: []
  docs:
  - doc/gpio_mas.md
  tb:
  - tb/cocotb/test_gpio.py
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
    name: function_model transaction FM1_LATCH_CONTROL
    stimulus: Drive preconditions for function_model transaction `FM1_LATCH_CONTROL`.
    expected: Outputs and side effects match `FM1_LATCH_CONTROL` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM1_LATCH_CONTROL
  - id: SC07
    name: function_model transaction FM2_SAMPLE_INPUTS
    stimulus: Drive preconditions for function_model transaction `FM2_SAMPLE_INPUTS`.
    expected: Outputs and side effects match `FM2_SAMPLE_INPUTS` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM2_SAMPLE_INPUTS
  - id: SC08
    name: function_model transaction FM3_DRIVE_PAD_OUTPUTS
    stimulus: Drive preconditions for function_model transaction `FM3_DRIVE_PAD_OUTPUTS`.
    expected: Outputs and side effects match `FM3_DRIVE_PAD_OUTPUTS` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
  - id: SC09
    name: function_model transaction FM4_ASYNC_RESET
    stimulus: Drive preconditions for function_model transaction `FM4_ASYNC_RESET`.
    expected: Outputs and side effects match `FM4_ASYNC_RESET` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM4_ASYNC_RESET
  scoreboard_checks: 12
  coverage_goals:
    function:
      target_pct: 100
      model: function_model
      description: all transactions and invariants covered
      bins:
      - id: FCOV_FM1
        source_ref: function_model.transactions.FM1_LATCH_CONTROL
        class: transaction
        description: latch transaction observed
      - id: FCOV_FM2
        source_ref: function_model.transactions.FM2_SAMPLE_INPUTS
        class: transaction
        description: sample transaction observed
      - id: FCOV_FM3
        source_ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
        class: transaction
        description: drive transaction observed
      - id: FCOV_FM4
        source_ref: function_model.transactions.FM4_ASYNC_RESET
        class: transaction
        description: reset transaction observed
    cycle:
      target_pct: 100
      model: cycle_model
      description: stage and rule coverage
      bins:
      - id: CCOV_S1
        source_ref: cycle_model.pipeline.S1_LATCH_CONTROL
        class: pipeline_stage
        description: latch stage hit
      - id: CCOV_S2
        source_ref: cycle_model.pipeline.S2_SAMPLE_INPUTS
        class: pipeline_stage
        description: sample stage hit
      - id: CCOV_S3
        source_ref: cycle_model.pipeline.S3_DRIVE_OUTPUTS
        class: pipeline_stage
        description: drive stage hit
      - id: CCOV_RULE_MASK
        source_ref: cycle_model.handshake_rules.HR_INPUT_MASK_SAMPLE
        class: handshake
        description: mask rule exercised
    functional: function_plus_cycle
    code: line >= 90%, branch >= 85%
    scenario: All SSOT scenarios pass with executable cocotb/pyuvm checkers and FL-vs-RTL scoreboard evidence
quality_gates:
  ssot:
    pass: SSOT parses and passes check_ssot_disk.sh
    evidence:
    - gpio/yaml/gpio.ssot.yaml
    - workflow/ssot-gen/scripts/check_ssot_disk.sh_log
  rtl:
    pass: RTL compiles/lints and matches function_model/cycle_model
    evidence:
    - rtl_compile_report
    - dut_lint_report
    - fl_vs_rtl_scoreboard
  rtl_gen:
    profile: standard
    pass: workflow_todos.rtl-gen items implemented with ownership traceability
    evidence:
    - rtl/rtl_todo_plan.json
    - rtl/rtl_authoring_provenance.json
  dv:
    pass: Every SSOT test_requirements scenario has an executable checker and FL-vs-RTL equivalence goal
    evidence:
    - verify/equivalence_goals.json
    - sim/scoreboard_events.jsonl
    - tb/cocotb tests
    - scenario implementation map
  coverage:
    pass: function and cycle coverage goals met or waived
    evidence:
    - cov/coverage.json
    - sim/coverage_report.md
  eda:
    pass: synthesis/STA/PnR meet targets or approved waiver
    evidence:
    - syn_report
    - sta_report
    - pnr_report
  signoff:
    pass: SSOT, FL/equivalence, RTL, lint, DV, sim, coverage, and EDA gates pass with fresh artifacts
    evidence:
    - ATLAS progress signoff PASS
traceability:
  yaml_to_output:
  - yaml: top_module.name
    output: rtl/gpio.sv
  - yaml: parameters
    output: rtl/gpio_param.vh
  - yaml: io_list.interfaces
    output: rtl/gpio.sv port list
  - yaml: function_model
    output: scoreboard/reference model
  - yaml: cycle_model
    output: protocol/cycle checkers
  - yaml: registers.register_list
    output: state docs and signal naming
  - yaml: rtl_contract
    output: module ownership implementation rules
  - yaml: test_requirements.scenarios
    output: sim tests
  - yaml: quality_gates
    output: CI signoff criteria
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
  - id: FL_GPIO_ORACLE
    content: Implement Python functional oracle for GPIO
    detail: Encode FM1-FM4 output_rules and invariants for scoreboard comparisons
    criteria:
    - oracle computes dir_q/dout_q/din_q/oe_o/pad_o per transaction output_rules
    - oracle used by tests SC01-SC05
    source_refs:
    - function_model.transactions
    - function_model.invariants
    owner_module: gpio
    owner_file: sim/tb_gpio_scoreboard.py
    priority: high
    required: true
  rtl-gen:
  - id: RTL_GPIO_REGS
    content: Implement sequential state registers
    detail: Create async-reset sequential logic for dir_q and dout_q sampled each rising edge
    criteria:
    - reset clears registers to zero
    - one-cycle sampling of dir_in/dout_in is preserved
    source_refs:
    - function_model.transactions.FM1_LATCH_CONTROL
    - function_model.transactions.FM4_ASYNC_RESET
    - cycle_model.pipeline.S1_LATCH_CONTROL
    owner_module: gpio_regs
    owner_file: rtl/gpio_regs.sv
    priority: high
    required: true
  - id: RTL_GPIO_SAMPLER
    content: Implement direction-masked input sampling
    detail: Update din_q only on input-configured bits at rising edge
    criteria:
    - din_q[i] samples pad_in[i] when dir_q[i]==0
    - din_q[i] holds when dir_q[i]==1
    source_refs:
    - function_model.transactions.FM2_SAMPLE_INPUTS
    - cycle_model.pipeline.S2_SAMPLE_INPUTS
    owner_module: gpio_input_sampler
    owner_file: rtl/gpio_input_sampler.sv
    priority: high
    required: true
  - id: RTL_GPIO_PAD
    content: Implement combinational pad drive logic
    detail: Derive oe_o and pad_o directly from dir_q and dout_q
    criteria:
    - oe_o equals dir_q bitwise
    - pad_o equals dout_q & dir_q
    source_refs:
    - function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
    - cycle_model.handshake_rules.HR_COMB_OUTPUTS
    owner_module: gpio_pad_logic
    owner_file: rtl/gpio_pad_logic.sv
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
  - name: validate_ssot
    command: bash workflow/ssot-gen/scripts/check_ssot_disk.sh gpio
    description: Validate production SSOT structure and quality gates
  - name: handoff_fl_model
    command: /ssot-fl-model gpio
    description: Generate FunctionalModel, decomposition, and FCOV plan from SSOT
  - name: handoff_equivalence_goals
    command: /ssot-equiv-goals gpio
    description: Derive FL-vs-RTL equivalence goals before TB generation
  - name: handoff_rtl
    command: /ssot-rtl gpio
    description: Generate RTL from validated SSOT
  - name: handoff_tb
    command: /ssot-tb-cocotb gpio
    description: Generate cocotb/pyuvm verification from validated SSOT
  - name: handoff_sim_debug
    command: /wf sim_debug
    description: Run simulation, waveform, and coverage inspection
rtl_contract:
  reset_contract:
    reset_signal: rst_n
    polarity: active_low
    behavior: async_assert_sync_deassert
    reset_state:
      dir_q: 0
      dout_q: 0
      din_q: 0
      oe_o: 0
      pad_o: 0
  sequential_contract:
  - name: latch_control
    rule: On each rising clk edge with rst_n=1, dir_q <= dir_in and dout_q <= dout_in.
  - name: sample_inputs
    rule: On each rising clk edge with rst_n=1, din_q[i] <= pad_in[i] only when dir_q[i]==0; else din_q[i] holds.
  combinational_contract:
  - name: drive_oe
    rule: oe_o equals dir_q bitwise.
  - name: drive_pad
    rule: pad_o[i] equals dout_q[i] when dir_q[i]==1 else 0.
  ownership:
    owner_top: gpio
    owner_modules:
    - gpio_regs
    - gpio_input_sampler
    - gpio_pad_logic
  owner: ssot-gen
  type: ssot_derived_rule_contract
  transaction: FM1_LATCH_CONTROL
  clock: clk
  reset: rst_n
  reset_active: low
  sample_condition: legal transaction accepted under cycle_model.handshake_rules
  input_map:
    dir_in: dir_in
    dout_in: dout_in
    pad_in: pad_in
  output_map:
    oe_o: oe_o
    pad_o: pad_o
    dir_q: dir_q
    dout_q: dout_q
    din_q: din_q
  contract_invariants:
  - RTL-visible behavior implements the referenced function_model transaction.
  - Input sampling and output observation follow cycle_model handshake and latency rules.
  output_rules:
  - name: dir_q_next
    port: dir_q
    expr: dir_in
    width: WIDTH
    description: FunctionalModel output observable mapped to DUT output port.
  - name: dout_q_next
    port: dout_q
    expr: dout_in
    width: WIDTH
    description: FunctionalModel output observable mapped to DUT output port.
  - name: din_q_masked_next
    port: din_q
    expr: (din_q & dir_q) | (pad_in & ~dir_q)
    width: WIDTH
    description: FunctionalModel output observable mapped to DUT output port.
  - name: oe_comb
    port: oe_o
    expr: dir_q
    width: WIDTH
    description: FunctionalModel output observable mapped to DUT output port.
  - name: pad_comb
    port: pad_o
    expr: dout_q & dir_q
    width: WIDTH
    description: FunctionalModel output observable mapped to DUT output port.


Base rtl-gen contract:
Prepare rtl-gen for gpio using only gpio/yaml/gpio.ssot.yaml and gpio/rtl/rtl_todo_plan.json, gpio/rtl/rtl_authoring_plan.json, and packets under gpio/rtl/authoring_packets. Return exactly one JSON object and nothing else. Success schema: {"files":[{"path":"gpio/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"},{"path":"gpio/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"},{"path":"gpio/list/gpio.f","kind":"filelist","content":"<filelist>"}]}. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=123947ae1f7d9f96f7ef25a8af2118a8e5c5ac198b54689b9c8f4223188b5dce. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "gpio",
        "reason": "53 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "gpio",
        "reason": "3 owner logic structure issue(s) remain. gpio_regs: Behavior-owner module is not declared in its owner file; gpio_input_sampler: Behavior-owner module is not declared in its owner file; gpio_pad_logic: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "rtl_placeholder_free_evidence",
        "owner_module": "gpio",
        "reason": "1 RTL placeholder/policy issue(s) remain. None:None: None (No listed RTL source files were readable, so placeholder-free evidence cannot be checked)",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "status": "open",
        "task_id": "RTL-0009"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "gpio",
        "reason": "1 top IO contract issue(s) remain. gpio: SSOT top module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "top_output_drive_evidence",
        "owner_module": "gpio",
        "reason": "1 top output drive issue(s) remain. gpio: SSOT top module is not declared, so output drive evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
        "status": "open",
        "task_id": "RTL-0011"
      },
      {
        "gate_kind": "top_input_consumption_evidence",
        "owner_module": "gpio",
        "reason": "1 top input consumption issue(s) remain. gpio: SSOT top module is not declared, so input consumption evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
        "status": "open",
        "task_id": "RTL-0012"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "gpio",
        "reason": "4 manifest hierarchy integration issue(s) remain. gpio: SSOT top module is not declared in listed RTL sources; gpio_regs: SSOT manifest child module is not declared in listed RTL sources; gpio_input_sampler: SSOT manifest child module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "gpio",
        "reason": "1 manifest signal-flow issue(s) remain. gpio: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "status": "open",
        "task_id": "RTL-0015"
      }
    ],
    "blocked_by_locked_truth": [
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "owner_module": "gpio",
        "reason": "15 SSOT connection contract issue(s) remain. gpio_regs: SSOT connection contract targets a module not declared in RTL; gpio_regs: SSOT connection contract targets a module not declared in RTL; gpio_regs: SSOT connection contract targets a module not declared in RTL",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      }
    ],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "gpio",
        "reason": "Missing common_ai_agent RTL authoring provenance.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "gpio",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "gpio",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "gpio",
        "reason": "137 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 15,
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
    "open_required_todos": 138,
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
          "gpio/rtl/rtl_authoring_provenance.json",
          "gpio/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip gpio --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py gpio --root . --audit-rtl"
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
          "gpio/rtl/rtl_compile.json",
          "gpio/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py gpio --top gpio --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py gpio --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "gpio/list/gpio.f covers the current DUT RTL sources."
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
          "gpio/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py gpio --top gpio",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py gpio --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "gpio/list/gpio.f covers the current DUT RTL/header sources."
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
          "gpio/rtl/rtl_todo_plan.json",
          "gpio/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py gpio --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "137 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ]
  },
  "ip": "gpio",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_regs__function_model.json",
      "kind": "module",
      "llm_actionable_open_count": 38,
      "open_required_count": 38,
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "packet_id": "module__gpio_regs__function_model",
      "required_count": 38,
      "status_counts": {
        "open": 38
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_regs__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 12,
      "open_required_count": 12,
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "packet_id": "module__gpio_regs__cycle_model",
      "required_count": 12,
      "status_counts": {
        "open": 12
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_regs__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 9,
      "open_required_count": 9,
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "packet_id": "module__gpio_regs__test_requirements",
      "required_count": 9,
      "status_counts": {
        "open": 9
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_regs__registers.json",
      "kind": "module",
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "packet_id": "module__gpio_regs__registers",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_regs__features.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "packet_id": "module__gpio_regs__features",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_regs__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "packet_id": "module__gpio_regs__fsm",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_regs__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "packet_id": "module__gpio_regs__equivalence",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_regs__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "packet_id": "module__gpio_regs__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_input_sampler.json",
      "kind": "module",
      "llm_actionable_open_count": 5,
      "open_required_count": 5,
      "owner_file": "rtl/gpio_input_sampler.sv",
      "owner_module": "gpio_input_sampler",
      "packet_id": "module__gpio_input_sampler",
      "required_count": 5,
      "status_counts": {
        "open": 5
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio_pad_logic.json",
      "kind": "module",
      "llm_actionable_open_count": 22,
      "open_required_count": 22,
      "owner_file": "rtl/gpio_pad_logic.sv",
      "owner_module": "gpio_pad_logic",
      "packet_id": "module__gpio_pad_logic",
      "required_count": 22,
      "status_counts": {
        "open": 22
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gpio.json",
      "kind": "module",
      "llm_actionable_open_count": 25,
      "open_required_count": 25,
      "owner_file": "rtl/gpio.sv",
      "owner_module": "gpio",
      "packet_id": "module__gpio",
      "required_count": 26,
      "status_counts": {
        "open": 25,
        "pass": 1
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
      "llm_actionable_open_count": 8,
      "open_required_count": 8,
      "owner_file": "rtl/gpio.sv",
      "owner_module": "gpio",
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
      "owner_file": "rtl/gpio.sv",
      "owner_module": "gpio",
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
      "owner_file": "rtl/gpio.sv",
      "owner_module": "gpio",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 4
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
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 1,
    "human_locked_tasks": 1,
    "llm_actionable_packets": 13,
    "llm_actionable_tasks": 133,
    "max_packet_required_tasks": 38,
    "module_packets": 11,
    "next_llm_packets": [
      "module__gpio_regs__function_model",
      "module__gpio_regs__cycle_model",
      "module__gpio_regs__test_requirements",
      "module__gpio_regs__registers",
      "module__gpio_regs__features",
      "module__gpio_regs__fsm",
      "module__gpio_regs__equivalence",
      "module__gpio_regs__workflow_todo"
    ],
    "packet_task_limit": 48,
    "packets": 15,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 143,
    "sliced_module_packets": 8,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 4,
    "total_tasks": 143,
    "unowned_packets": 1
  },
  "target_scale": {},
  "todo_plan_sha256": "123947ae1f7d9f96f7ef25a8af2118a8e5c5ac198b54689b9c8f4223188b5dce",
  "top": "gpio",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/gpio_regs.sv):
module gpio_regs #(
    parameter integer WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic [WIDTH-1:0] dir_in,
    input  logic [WIDTH-1:0] dout_in,
    input  logic [WIDTH-1:0] pad_in,
    output logic [WIDTH-1:0] dir_q,
    output logic [WIDTH-1:0] dout_q,
    output logic [WIDTH-1:0] din_q
);

    // HR_INPUT_MASK_SAMPLE / S2_SAMPLE_INPUTS:
    // Use registered direction state to decide which din_q bits sample pad_in
    // and which bits hold previous state.
    logic [WIDTH-1:0] din_q_masked_next;

    // S3_DRIVE_OUTPUTS observability in this owner file:
    // gpio_regs owns registered state; top-level pad outputs are driven from this
    // state in gpio_pad_logic with oe_o=dir_q and pad_o=(dout_q & dir_q).
    // Keeping these stage wires local preserves cycle-model traceability while
    // leaving architectural ownership unchanged.
    logic [WIDTH-1:0] oe_o_s3;
    logic [WIDTH-1:0] pad_o_s3;

    assign din_q_masked_next = (din_q & dir_q) | (pad_in & (~dir_q));
    assign oe_o_s3           = dir_q;
    assign pad_o_s3          = dout_q & dir_q;

    // FM1 + FM2 + FM4 owner behavior with SSOT cycle semantics:
    // - HR_SYNC_SAMPLE: all sampling happens only on posedge clk
    // - S0_RESET: async assert reset clears architectural state
    // - S1_LATCH_CONTROL: latch dir_in/dout_in at cycle N
    // - S2_SAMPLE_INPUTS: update din_q using registered direction mask
    // Ordering rule: reset dominates non-reset logic.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dir_q  <= {WIDTH{1'b0}};
            dout_q <= {WIDTH{1'b0}};
            din_q  <= {WIDTH{1'b0}};
        end else begin
            // S1_LATCH_CONTROL (latency=1 from control inputs to state outputs)
            dir_q  <= dir_in;
            dout_q <= dout_in;

            // HR_INPUT_MASK_SAMPLE / S2_SAMPLE_INPUTS (latency=1 pad_in->din_q)
            din_q  <= din_q_masked_next;
        end
    end

endmodule


Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__gpio_regs__test_requirements.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 15,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 8,
      "enabled": true,
      "index": 6,
      "key": "test_requirements",
      "module_task_count": 70,
      "rule": "Owner module gpio_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "test_requirements",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/gpio_regs.sv",
      "name": "gpio_regs",
      "refs": [
        "cycle_model",
        "cycle_model.pipeline.S1_LATCH_CONTROL",
        "dataflow",
        "decomposition",
        "features",
        "fsm",
        "function_model",
        "function_model.state_variables",
        "function_model.transactions.FM1_LATCH_CONTROL",
        "function_model.transactions.FM2_SAMPLE_INPUTS",
        "function_model.transactions.FM3_DRIVE_PAD_OUTPUTS",
        "function_model.transactions.FM4_ASYNC_RESET",
        "registers",
        "registers.register_list",
        "registers.register_list.DIR_Q",
        "registers.register_list.DOUT_Q",
        "test_requirements"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/gpio_regs.sv",
        "name": "gpio_regs",
        "wiring_only": false
      },
      {
        "file": "rtl/gpio_input_sampler.sv",
        "name": "gpio_input_sampler",
        "wiring_only": false
      },
      {
        "file": "rtl/gpio_pad_logic.sv",
        "name": "gpio_pad_logic",
        "wiring_only": false
      },
      {
        "file": "rtl/gpio.sv",
        "name": "gpio",
        "wiring_only": false
      }
    ],
    "quality_profile": "standard",
    "reference_profile": null,
    "ssot_connection_contracts": [
      {
        "instance": "",
        "machine_readable": true,
        "module": "gpio_regs",
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
        "module": "gpio_regs",
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
        "module": "gpio_regs",
        "port": "dir_in",
        "signal": "dir_in",
        "signal_terms": [
          "dir_in"
        ],
        "source_ref": "integration.connections[2]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gpio_regs",
        "port": "dout_in",
        "signal": "dout_in",
        "signal_terms": [
          "dout_in"
        ],
        "source_ref": "integration.connections[3]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gpio_regs",
        "port": "dir_q",
        "signal": "dir_q",
        "signal_terms": [
          "dir_q"
        ],
        "source_ref": "integration.connections[4]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gpio_regs",
        "port": "dout_q",
        "signal": "dout_q",
        "signal_terms": [
          "dout_q"
        ],
        "source_ref": "integration.connections[5]"
      }
    ],
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
    "llm_actionable_open_count": 9,
    "open_required_count": 9,
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
  "ip": "gpio",
  "kind": "module",
  "owner_file": "rtl/gpio_regs.sv",
  "owner_module": "gpio_regs",
  "packet_id": "module__gpio_regs__test_requirements",
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
      "test_requirements.scenario": 9
    },
    "module_slice": {
      "count": 8,
      "enabled": true,
      "index": 6,
      "key": "test_requirements",
      "module_task_count": 70,
      "rule": "Owner module gpio_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "test_requirements",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 9,
    "required_count": 9,
    "source_refs": [
      "test_requirements.scenarios.SC01",
      "test_requirements.scenarios.SC02",
      "test_requirements.scenarios.SC03",
      "test_requirements.scenarios.SC04",
      "test_requirements.scenarios.SC05",
      "test_requirements.scenarios.SC06",
      "test_requirements.scenarios.SC07",
      "test_requirements.scenarios.SC08",
      "test_requirements.scenarios.SC09"
    ],
    "status_counts": {
      "open": 9
    },
    "task_count": 9
  },
  "tasks": [
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC01",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC01",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Architectural state, status, outputs, and debug observability match function_model reset outputs."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC01.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC01; name=reset contract; expected=Architectural state, status, outputs, and debug observability match function_model reset outputs..",
      "evidence_terms": [],
      "id": "RTL-0135",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC01",
      "ssot_context": {
        "expected": "Architectural state, status, outputs, and debug observability match function_model reset outputs.",
        "id": "SC01",
        "name": "reset contract"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC01"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC02",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC02",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Externally observable result/status/side effects match the function_model primary transaction."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC02.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC02; name=primary approved behavior; expected=Externally observable result/status/side effects match the function_model primary transaction..",
      "evidence_terms": [],
      "id": "RTL-0136",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC02",
      "ssot_context": {
        "expected": "Externally observable result/status/side effects match the function_model primary transaction.",
        "id": "SC02",
        "name": "primary approved behavior"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC02"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC03",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC03",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC03.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC03; name=cycle handshake and backpressure; expected=Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules..",
      "evidence_terms": [],
      "id": "RTL-0137",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC03",
      "ssot_context": {
        "expected": "Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules.",
        "id": "SC03",
        "name": "cycle handshake and backpressure"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC03"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC04",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC04",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC04.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC04; name=error and recovery policy; expected=Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state..",
      "evidence_terms": [],
      "id": "RTL-0138",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC04",
      "ssot_context": {
        "expected": "Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state.",
        "id": "SC04",
        "name": "error and recovery policy"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC04"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC05",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC05",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC05.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC05; name=debug and trace observability; expected=Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior..",
      "evidence_terms": [],
      "id": "RTL-0139",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC05",
      "ssot_context": {
        "expected": "Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior.",
        "id": "SC05",
        "name": "debug and trace observability"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC05"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC06",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC06",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM1_LATCH_CONTROL` exactly."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC06.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC06; name=function_model transaction FM1_LATCH_CONTROL; expected=Outputs and side effects match `FM1_LATCH_CONTROL` exactly..",
      "evidence_terms": [],
      "id": "RTL-0140",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC06",
      "ssot_context": {
        "expected": "Outputs and side effects match `FM1_LATCH_CONTROL` exactly.",
        "id": "SC06",
        "name": "function_model transaction FM1_LATCH_CONTROL"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC06"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC07",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC07",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM2_SAMPLE_INPUTS` exactly."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC07.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC07; name=function_model transaction FM2_SAMPLE_INPUTS; expected=Outputs and side effects match `FM2_SAMPLE_INPUTS` exactly..",
      "evidence_terms": [],
      "id": "RTL-0141",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC07",
      "ssot_context": {
        "expected": "Outputs and side effects match `FM2_SAMPLE_INPUTS` exactly.",
        "id": "SC07",
        "name": "function_model transaction FM2_SAMPLE_INPUTS"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC07"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC08",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC08",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM3_DRIVE_PAD_OUTPUTS` exactly."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC08.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC08; name=function_model transaction FM3_DRIVE_PAD_OUTPUTS; expected=Outputs and side effects match `FM3_DRIVE_PAD_OUTPUTS` exactly..",
      "evidence_terms": [],
      "id": "RTL-0142",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC08",
      "ssot_context": {
        "expected": "Outputs and side effects match `FM3_DRIVE_PAD_OUTPUTS` exactly.",
        "id": "SC08",
        "name": "function_model transaction FM3_DRIVE_PAD_OUTPUTS"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC08"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC09",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC09",
        "Primary implementation evidence is in rtl/gpio_regs.sv",
        "Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM4_ASYNC_RESET` exactly."
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC09.\nOwner: gpio_regs in rtl/gpio_regs.sv via test_requirements.\nSSOT item context: id=SC09; name=function_model transaction FM4_ASYNC_RESET; expected=Outputs and side effects match `FM4_ASYNC_RESET` exactly..",
      "evidence_terms": [],
      "id": "RTL-0143",
      "owner_file": "rtl/gpio_regs.sv",
      "owner_module": "gpio_regs",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC09",
      "ssot_context": {
        "expected": "Outputs and side effects match `FM4_ASYNC_RESET` exactly.",
        "id": "SC09",
        "name": "function_model transaction FM4_ASYNC_RESET"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC09"
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
        "reason": "Owner RTL file is missing: rtl/gpio_regs.sv.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "123947ae1f7d9f96f7ef25a8af2118a8e5c5ac198b54689b9c8f4223188b5dce",
  "top": "gpio",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__gpio_regs__test_requirements.md):
# RTL Authoring Packet: module__gpio_regs__test_requirements

- Kind: module
- Owner module: gpio_regs
- Owner file: rtl/gpio_regs.sv
- Task count: 9
- Required tasks: 9

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
- LLM-actionable open tasks: 9
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline.S1_LATCH_CONTROL, dataflow, decomposition, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM1_LATCH_CONTROL, function_model.transactions.FM2_SAMPLE_INPUTS, function_model.transactions.FM3_DRIVE_PAD_OUTPUTS, function_model.transactions.FM4_ASYNC_RESET, registers, registers.register_list, registers.register_list.DIR_Q, registers.register_list.DOUT_Q
- Module slice: 6/8 section=test_requirements task_limit=48
- Slice rule: Owner module gpio_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gpio_regs.clk <= clk (integration.connections[0])
  - gpio_regs.rst_n <= rst_n (integration.connections[1])
  - gpio_regs.dir_in <= dir_in (integration.connections[2])
  - gpio_regs.dout_in <= dout_in (integration.connections[3])
  - gpio_regs.dir_q <= dir_q (integration.connections[4])
  - gpio_regs.dout_q <= dout_q (integration.connections[5])

## Tasks

### RTL-0135: Keep RTL observable for scenario SC01

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC01
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC01.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC01; name=reset contract; expected=Architectural state, status, outputs, and debug observability match function_model reset outputs..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC01
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Architectural state, status, outputs, and debug observability match function_model reset outputs.
- SSOT refs: test_requirements.scenarios.SC01

### RTL-0136: Keep RTL observable for scenario SC02

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC02
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC02.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC02; name=primary approved behavior; expected=Externally observable result/status/side effects match the function_model primary transaction..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC02
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Externally observable result/status/side effects match the function_model primary transaction.
- SSOT refs: test_requirements.scenarios.SC02

### RTL-0137: Keep RTL observable for scenario SC03

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC03
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC03.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC03; name=cycle handshake and backpressure; expected=Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC03
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules.
- SSOT refs: test_requirements.scenarios.SC03

### RTL-0138: Keep RTL observable for scenario SC04

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC04
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC04.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC04; name=error and recovery policy; expected=Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC04
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state.
- SSOT refs: test_requirements.scenarios.SC04

### RTL-0139: Keep RTL observable for scenario SC05

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC05
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC05.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC05; name=debug and trace observability; expected=Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC05
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior.
- SSOT refs: test_requirements.scenarios.SC05

### RTL-0140: Keep RTL observable for scenario SC06

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC06
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC06.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC06; name=function_model transaction FM1_LATCH_CONTROL; expected=Outputs and side effects match `FM1_LATCH_CONTROL` exactly..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC06
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM1_LATCH_CONTROL` exactly.
- SSOT refs: test_requirements.scenarios.SC06

### RTL-0141: Keep RTL observable for scenario SC07

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC07
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC07.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC07; name=function_model transaction FM2_SAMPLE_INPUTS; expected=Outputs and side effects match `FM2_SAMPLE_INPUTS` exactly..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC07
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM2_SAMPLE_INPUTS` exactly.
- SSOT refs: test_requirements.scenarios.SC07

### RTL-0142: Keep RTL observable for scenario SC08

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC08
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC08.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC08; name=function_model transaction FM3_DRIVE_PAD_OUTPUTS; expected=Outputs and side effects match `FM3_DRIVE_PAD_OUTPUTS` exactly..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC08
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM3_DRIVE_PAD_OUTPUTS` exactly.
- SSOT refs: test_requirements.scenarios.SC08

### RTL-0143: Keep RTL observable for scenario SC09

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC09
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC09.
Owner: gpio_regs in rtl/gpio_regs.sv via test_requirements.
SSOT item context: id=SC09; name=function_model transaction FM4_ASYNC_RESET; expected=Outputs and side effects match `FM4_ASYNC_RESET` exactly..
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC09
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM4_ASYNC_RESET` exactly.
- SSOT refs: test_requirements.scenarios.SC09
