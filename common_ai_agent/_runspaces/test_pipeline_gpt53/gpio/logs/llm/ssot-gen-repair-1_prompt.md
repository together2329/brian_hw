Repair the SSOT YAML artifact for gpio. This is repair attempt 1.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "gpio/yaml/gpio.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}
  ]
}

Repair rules:
- Do not use a fixed IP template or hardcoded workaround.
- Preserve product semantics from the requirement and current SSOT wherever they are valid.
- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.
- Fix the concrete parse/validator failures below, and also check for sibling contract defects.
- The repaired YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh gpio`.
- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.

Failure summary:
human_gate: SSOT disk validator failed: [check_ssot_disk] FAIL: gpio/yaml/gpio.ssot.yaml failed YAML/model validation

Blocker artifact:


Validator log:
cmd: bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh gpio
cwd: /Users/brian/Desktop/Project/brian_hw/common_ai_agent/_runspaces/test_pipeline_gpt53
returncode: 1
stdout:
[check_ssot_disk] FAIL: gpio/yaml/gpio.ssot.yaml failed YAML/model validation
  function_model.transactions[] must include at least one executable output_rules entry with name/expr/width/port


Requirements:
# gpio IP Requirements

## Intent

Build a small parameterizable bidirectional GPIO peripheral as a smoke
fixture for the common_ai_agent SSOT pipeline. The block is intentionally
narrow: no bus and no interrupt, just direct register-style ports that
exercise SSOT, function-model, cycle-model, equivalence goals, RTL,
lint, TB, sim, coverage, and audit.

## Functional Behavior

- `clk` is the only clock.
- `rst_n` is an active-low asynchronous reset; on assertion all output
  state returns to zero.
- `dir_in[WIDTH-1:0]` is a synchronous control that selects per-pin
  direction. `0` makes the pin an input, `1` makes the pin an output.
- `dout_in[WIDTH-1:0]` is the output data value to drive when the pin
  is configured as output.
- `pad_in[WIDTH-1:0]` is the observed pad value when the pin is an
  input.
- `dir_q[WIDTH-1:0]` is the registered direction state.
- `dout_q[WIDTH-1:0]` is the registered output-data state.
- `oe_o[WIDTH-1:0]` is the combinational output-enable to the pad
  ring; bit `i` is high iff `dir_q[i]` is `1`.
- `pad_o[WIDTH-1:0]` is the combinational output-data to the pad ring;
  bit `i` equals `dout_q[i]` when `dir_q[i]` is `1`, otherwise `0`.
- `din_q[WIDTH-1:0]` is the registered input sample of `pad_in` on the
  rising clock edge for every bit whose `dir_q` is `0`. Bits whose
  `dir_q` is `1` hold their previous `din_q` value.

## Non-Goals

- No APB, AXI, or CSR bus.
- No interrupt or edge-detect logic.
- No clock-domain crossing or asynchronous IO ring metastability
  modeling beyond the simple input sample.
- `WIDTH` is parameterized via SSOT; the smoke fixture default is 8
  bits.

## Verification Hints

- Reset clears `dir_q`, `dout_q`, `din_q`, `oe_o`, and `pad_o`.
- Toggling `dir_in` from 0 to 1 should make `oe_o` follow on the next
  cycle.
- When `dir_q[i]` is 0, `pad_o[i]` must stay at 0 regardless of
  `dout_q[i]`.
- When `dir_q[i]` is 1, `pad_o[i]` must equal `dout_q[i]` and `oe_o[i]`
  must be 1.
- `din_q[i]` only samples `pad_in[i]` for input bits; output bits keep
  their last sampled value.
- Coverage should hit: all-input, all-output, mixed direction, write
  while output, read while input, and a randomized walk that flips
  direction.


Current SSOT YAML:
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
  - function_model.transactions.FM2_SAMPLE_INPUTS
  - function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
  - function_model.transactions.FM4_ASYNC_RESET
  - function_model.state_variables
  register_refs:
  - registers.register_list.DIR_Q
  - registers.register_list.DOUT_Q
  - registers.register_list
  cycle_model_refs:
  - cycle_model.pipeline.S1_LATCH_CONTROL
  - cycle_model
  description: Sequential control-state register block for direction and output data
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
  description: Sequential input capture block with per-bit direction masking
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
  description: Combinational pad output-enable and output-data generation
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
  description: Top-level integration and module wiring
decomposition:
  strategy: manifest_owned_leaf_decomposition
  owners:
  - module: gpio_regs
    file: rtl/gpio_regs.sv
    responsibility: Sequential control-state register block for direction and output data
    source_sections:
    - function_model
    - registers
    - cycle_model
  - module: gpio_input_sampler
    file: rtl/gpio_input_sampler.sv
    responsibility: Sequential input capture block with per-bit direction masking
    source_sections: *id001
  - module: gpio_pad_logic
    file: rtl/gpio_pad_logic.sv
    responsibility: Combinational pad output-enable and output-data generation
    source_sections: *id002
  - module: gpio
    file: rtl/gpio.sv
    responsibility: Top-level integration and module wiring
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
- name: RESET_VALUE
  default: 0
  type: int
  description: Reset value for dir_q/dout_q/din_q
  drives:
  - rtl/gpio_regs.sv
  - rtl/gpio_input_sampler.sv
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
    description: Direct register-style control inputs
    ports:
    - name: dir_in
      width: WIDTH
      direction: input
      description: Per-pin direction control; 0=input, 1=output
    - name: dout_in
      width: WIDTH
      direction: input
      description: Per-pin output data control
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: gpio_pad
    type: custom
    role: master
    description: Pad ring driving/sampling signals
    ports:
    - name: pad_in
      width: WIDTH
      direction: input
      description: Observed external pad levels
    - name: oe_o
      width: WIDTH
      direction: output
      description: Output-enable to pad ring
    - name: pad_o
      width: WIDTH
      direction: output
      description: Output data to pad ring
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: gpio_state
    type: custom
    role: status
    description: Registered architectural GPIO state outputs
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
      description: Registered sampled input state
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
features:
- name: Per-bit direction control
  trigger: dir_in update sampled on rising clk
  datapath: dir_in -> dir_q -> oe_o gating and pad_o mask
  control: Single-cycle register latch
  output: oe_o[i]=1 when dir_q[i]=1
- name: Registered output data
  trigger: dout_in update sampled on rising clk
  datapath: dout_in -> dout_q -> pad_o when dir_q=1
  control: Single-cycle register latch
  output: pad_o follows dout_q only for output-configured bits
- name: Direction-masked input sampling
  trigger: rising clk
  datapath: pad_in sampled into din_q for bits where dir_q=0
  control: Per-bit conditional register update
  output: din_q holds previous value for output-configured bits
dataflow:
  control_path:
    source: dir_in, dout_in
    sequence: sample at clk edge -> update dir_q,dout_q
    note: No bus decode; controls are direct ports
  output_path:
    source: dir_q,dout_q
    sequence: combinational derive oe_o and pad_o
    rules:
    - oe_o[i] = dir_q[i]
    - pad_o[i] = dout_q[i] when dir_q[i]=1 else 0
  input_path:
    source: pad_in
    sequence: at each clk edge, if dir_q[i]=0 then din_q[i] := pad_in[i] else hold
function_model:
  purpose: Cycle-independent behavioral contract for GPIO register-state and pad behavior
  state_variables:
  - name: dir_state
    source: dir_q
    reset: 0
    description: Registered direction vector
  - name: dout_state
    source: dout_q
    reset: 0
    description: Registered output data vector
  - name: din_state
    source: din_q
    reset: 0
    description: Registered sampled input vector
  transactions:
  - id: FM1_LATCH_CONTROL
    name: latch_direction_and_output_data
    preconditions:
    - rst_n is deasserted
    - rising edge of clk
    inputs:
    - dir_in[WIDTH-1:0]
    - dout_in[WIDTH-1:0]
    outputs:
    - dir_state equals dir_in after sampling edge
    - dout_state equals dout_in after sampling edge
    side_effects:
    - Architectural registers dir_q and dout_q are updated atomically each cycle
    output_rules: []
  - id: FM2_SAMPLE_INPUTS
    name: sample_pad_inputs_for_input_bits_only
    preconditions:
    - rst_n is deasserted
    - rising edge of clk
    inputs:
    - pad_in[WIDTH-1:0]
    - dir_state from previous or same-edge architectural interpretation
    outputs:
    - 'For each bit i: if dir_state[i]=0 then din_state[i]=pad_in[i]'
    - 'For each bit i: if dir_state[i]=1 then din_state[i] retains previous value'
    side_effects:
    - din_q updates only on bits configured as input
    output_rules: []
  - id: FM3_DRIVE_PAD_OUTPUTS
    name: derive_output_enable_and_pad_drive
    preconditions:
    - dir_state and dout_state are defined
    inputs:
    - dir_state
    - dout_state
    outputs:
    - oe_o[i] is 1 iff dir_state[i]=1
    - pad_o[i] equals dout_state[i] when dir_state[i]=1
    - pad_o[i] equals 0 when dir_state[i]=0
    side_effects:
    - No sequential state change; combinational observable outputs reflect registered state
    output_rules: []
  - id: FM4_ASYNC_RESET
    name: asynchronous_reset_clears_state
    preconditions:
    - rst_n asserted low
    outputs:
    - dir_state becomes 0
    - dout_state becomes 0
    - din_state becomes 0
    - oe_o becomes 0
    - pad_o becomes 0
    side_effects:
    - All architectural state cleared independent of clk
    output_rules: []
  invariants:
  - For all bits i, oe_o[i] == dir_q[i] at all times after combinational settle.
  - For all bits i with dir_q[i]==0, pad_o[i] must be 0 regardless of dout_q[i].
  - For all bits i with dir_q[i]==1, din_q[i] cannot change unless reset is asserted.
  - No hidden state exists beyond dir_q, dout_q, din_q.
cycle_model:
  purpose: Cycle-accurate timing and ordering contract for GPIO control/sample/drive behavior
  executable: python
  clock: clk
  reset:
    assertion: rst_n low asynchronously clears sequential state immediately
    deassertion: state is usable from first rising edge after rst_n returns high
  latency:
    control_to_dir_q:
      min_cycles: 1
      max_cycles: 1
      description: dir_in sampled to dir_q on next rising edge
    control_to_dout_q:
      min_cycles: 1
      max_cycles: 1
      description: dout_in sampled to dout_q on next rising edge
    dir_q_to_oe_o:
      min_cycles: 0
      max_cycles: 0
      description: oe_o is combinational from dir_q
    dir_q_dout_q_to_pad_o:
      min_cycles: 0
      max_cycles: 0
      description: pad_o combinational from dir_q and dout_q
    pad_in_to_din_q_when_input:
      min_cycles: 1
      max_cycles: 1
      description: pad_in sampled into din_q on rising edge for input bits
  handshake_rules:
  - id: HR_SYNC_SAMPLE
    signal: clk
    rule: dir_in and dout_in are sampled only on rising clk edge.
  - id: HR_INPUT_MASK_SAMPLE
    signal: din_q
    rule: din_q bit updates on rising edge only if corresponding dir_q bit indicates input mode.
  - id: HR_COMB_OUTPUTS
    signal: oe_o/pad_o
    rule: oe_o and pad_o are pure combinational functions of registered states with no extra cycle latency.
  pipeline:
  - stage: S0_RESET
    cycle: async
    action: On rst_n low, clear dir_q/dout_q/din_q to zero
  - stage: S1_LATCH_CONTROL
    cycle: N
    action: At rising edge N, latch dir_in into dir_q and dout_in into dout_q
  - stage: S2_SAMPLE_INPUTS
    cycle: N
    action: At rising edge N, sample pad_in into din_q only for bits with input direction
  - stage: S3_DRIVE_OUTPUTS
    cycle: N+combinational
    action: Drive oe_o and pad_o from new registered state after edge
  ordering:
  - Within a cycle, sequential updates occur at edge; combinational outputs reflect updated state after propagation.
  - Reset dominates all non-reset transitions.
  - Input-sample hold behavior for output bits is preserved across cycles unless reset occurs.
  backpressure:
  - No ready/valid backpressure protocol; behavior is fully synchronous to clk.
  observability:
  - Each function_model transaction maps to a pipeline stage and directed test scenario.
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
  - name: clk
    frequency_mhz: 200
    description: Single GPIO functional domain
  reset_scheme:
    signal: rst_n
    polarity: active_low
    type: async_assert_sync_deassert
cdc_requirements:
  crossings: []
  synchronizers: []
  note: Single internal clock domain; no CDC paths in this fixture
rdc_requirements:
  crossings: []
  synchronizers: []
  note: Single reset domain; no RDC crossings
registers:
  config:
    register_width: WIDTH
    addr_width: 0
    byte_addressable: false
    note: Architectural state exposed directly via ports; no memory-mapped bus
  register_list:
  - name: DIR_Q
    offset: null
    width: WIDTH
    access: rw_via_port
    reset: 0
    category: state
    description: Registered direction state sampled from dir_in
    fields:
    - name: dir
      bits:
      - WIDTH-1
      - 0
      access: rw_via_port
      reset: 0
      description: 0=input, 1=output
      write_effect: APB write data updates this field value according to its bit mask.
  - name: DOUT_Q
    offset: null
    width: WIDTH
    access: rw_via_port
    reset: 0
    category: state
    description: Registered output data sampled from dout_in
    fields:
    - name: dout
      bits:
      - WIDTH-1
      - 0
      access: rw_via_port
      reset: 0
      description: Output drive value when direction is output
      write_effect: APB write data updates this field value according to its bit mask.
  - name: DIN_Q
    offset: null
    width: WIDTH
    access: ro
    reset: 0
    category: state
    description: Registered sampled input data
    fields:
    - name: din
      bits:
      - WIDTH-1
      - 0
      access: ro
      reset: 0
      description: Sampled pad_in value for input-configured bits
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
    note: Stateless datapath-style peripheral; behavior encoded in register transfer rules rather than multi-state FSM
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
  - path: dir_q,dout_q->pad_o
    cycles: 0
    requirement: combinational
  - path: pad_in->din_q (input bits)
    cycles: 1
    requirement: fixed
  sta_expectations:
  - Meet single-clock setup/hold at target frequency
  - Reset recovery/removal checks for rst_n
power:
  domains:
  - name: VDD_GPIO
    voltage: nominal
    elements:
    - all gpio logic
  power_states:
  - name: 'ON'
    description: Normal operation
  - name: RESET
    description: rst_n asserted; state cleared
  clock_gating: none
  retention: not required
  upf_required: false
security:
  classification: non-sensitive peripheral control
  assets:
  - Correct direction gating to avoid unintended output driving
  - Integrity of sampled input state din_q
  threat_model:
  - Accidental misconfiguration of direction bits
  - Glitchy external pad inputs sampled at clock edge
  assumptions:
  - System-level access control for driving dir_in/dout_in is out of scope
  privilege_model: System-level access control is owned by the integrating bus/firewall unless explicitly declared here.
error_handling:
  error_sources:
  - id: illegal_state
    condition: none expected
    architectural_effect: Status/error reporting follows the SSOT error policy
  - id: x_propagation_from_pad
    condition: pad_in unknown in simulation
    architectural_effect: Status/error reporting follows the SSOT error policy
  propagation:
  - No internal fault interrupt/path; unknown pad values may reflect into din_q when sampled as input
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
    trigger: rising edge
    payload:
    - dir_in
    - dout_in
    - dir_q
    - dout_q
  - name: EV_INPUT_SAMPLE
    trigger: rising edge
    payload:
    - pad_in
    - dir_q
    - din_q
  - name: EV_RESET
    trigger: rst_n falling
    payload:
    - dir_q
    - dout_q
    - din_q
  status_outputs:
  - status/debug signals declared in io_list or registers
integration:
  bus_attachment:
    type: none
    description: Direct pin-level control, no APB/AXI/CSR bus
  dependencies:
  - Pad ring provides pad_in and consumes oe_o/pad_o
  - System clock/reset distribution provides clk/rst_n
  connections:
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
  connection_contract_status: missing machine-readable module wiring; child RTL drafts may proceed from owner packets, but top integration/signoff
    must stay blocked until SSOT authors integration.connections or sub_modules[].connections with module/port/signal records
  integration_notes:
  - Integrator must connect every declared io_list port and honor timing/reset assumptions.
dft:
  scan_required: true
  controllability:
  - dir_q, dout_q, din_q flops must be scannable
  - Primary inputs dir_in/dout_in/pad_in are controllable in testbench/ATE context
  observability:
  - dir_q, dout_q, din_q observable via module outputs
  - oe_o and pad_o observable as combinational outputs
  mbist: not applicable
  mbist_required: true
synthesis:
  dialect: systemverilog_2012
  constraints:
  - Single clock constraint on clk
  - Asynchronous reset false-path/setup-hold handling per flow policy
  - WIDTH must be >=1
  required_outputs:
  - Gate-level netlist
  - Area/timing reports
  - Unconstrained-path report
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
    - generic_clkbuf
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
  - nonblocking assignments in sequential always blocks
  - blocking assignments in combinational always blocks
  - no inferred latches
  - active-low asynchronous reset semantics
  - parameterized width usage
  lint_waivers:
  - none expected
reuse_modules: []
custom:
  assumptions:
  - No metastability hardening included; pad_in is sampled directly as specified
  note: Smoke-fixture IP intentionally minimal
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
      description: All declared transactions and invariants exercised
      bins:
      - id: FCOV_FM1
        source_ref: function_model.transactions.FM1_LATCH_CONTROL
        class: transaction
        description: Control latch observed
      - id: FCOV_FM2
        source_ref: function_model.transactions.FM2_SAMPLE_INPUTS
        class: transaction
        description: Input sampling observed
      - id: FCOV_FM3
        source_ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
        class: transaction
        description: Pad drive derivation observed
      - id: FCOV_FM4
        source_ref: function_model.transactions.FM4_ASYNC_RESET
        class: transaction
        description: Reset behavior observed
    cycle:
      target_pct: 100
      model: cycle_model
      description: Latency, ordering, and stage transitions covered
      bins:
      - id: CCOV_PIPE_S1
        source_ref: cycle_model.pipeline.S1_LATCH_CONTROL
        class: pipeline_stage
        description: Control latch stage hit
      - id: CCOV_PIPE_S2
        source_ref: cycle_model.pipeline.S2_SAMPLE_INPUTS
        class: pipeline_stage
        description: Input sample stage hit
      - id: CCOV_PIPE_S3
        source_ref: cycle_model.pipeline.S3_DRIVE_OUTPUTS
        class: pipeline_stage
        description: Combinational drive stage hit
      - id: CCOV_RULE_MASK
        source_ref: cycle_model.handshake_rules.HR_INPUT_MASK_SAMPLE
        class: rule
        description: Direction mask sample rule checked
    functional: Legacy alias for function+cycle closure
    code: line >= 90%, branch >= 85%
    scenario: All SSOT scenarios pass with executable cocotb/pyuvm checkers and FL-vs-RTL scoreboard evidence
quality_gates:
  ssot:
    pass: SSOT parses, includes all required canonical sections, and passes check_ssot_disk.sh
    evidence:
    - gpio/yaml/gpio.ssot.yaml
    - workflow/ssot-gen/scripts/check_ssot_disk.sh log
  rtl:
    pass: RTL matches function_model and cycle_model behavior and compiles/lints clean
    evidence:
    - rtl compile report
    - lint report
    - FL-vs-RTL comparison log
  rtl_gen:
    profile: standard
    pass: All workflow_todos.rtl-gen items implemented with traceable ownership and compile-clean RTL
    evidence:
    - rtl/rtl_todo_plan.json
    - rtl/rtl_authoring_provenance.json
  dv:
    pass: Directed and randomized scenarios pass with scoreboard and assertions
    evidence:
    - sim regression summary
    - scoreboard mismatch report (empty)
  coverage:
    pass: Function and cycle coverage goals reach declared targets or have approved waiver
    evidence:
    - cov/coverage.json
    - coverage report
  eda:
    pass: Synthesis/STA/PnR reports meet target or accepted waiver exists
    evidence:
    - syn report
    - sta report
    - pnr report
  signoff:
    pass: All gates ssot/rtl/dv/coverage/eda are green
    evidence:
    - signoff checklist
    - artifact manifest
traceability:
  yaml_to_output:
  - yaml: top_module
    output: rtl/gpio.sv
  - yaml: parameters
    output: rtl/gpio_param.vh and module parameter declarations
  - yaml: io_list.interfaces
    output: top-level port list and tb pin drivers
  - yaml: function_model
    output: scoreboard reference model and RTL behavioral checks
  - yaml: cycle_model
    output: temporal assertions and cycle-accurate checkers
  - yaml: registers.register_list
    output: architectural state signal naming and docs
  - yaml: rtl_contract
    output: owner-module RTL implementation rules
  - yaml: test_requirements.scenarios
    output: sim test sequences
  - yaml: quality_gates
    output: CI pass/fail criteria
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
  fl-model-ge
... <truncated 5045 chars>