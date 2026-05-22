Repair the SSOT YAML artifact for gray_counter. This is repair attempt 2.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "gray_counter/yaml/gray_counter.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}
  ]
}

Repair rules:
- Do not use a fixed IP template or hardcoded workaround.
- Preserve product semantics from the requirement and current SSOT wherever they are valid.
- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.
- Fix the concrete parse/validator failures below, and also check for sibling contract defects.
- The repaired YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh gray_counter`.
- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.

Failure summary:
human_gate: SSOT disk validator failed: [check_ssot_disk] FAIL: gray_counter/yaml/gray_counter.ssot.yaml failed YAML/model validation

Blocker artifact:


Validator log:
cmd: bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh gray_counter
cwd: /Users/brian/Desktop/Project/brian_hw/common_ai_agent/_runspaces/test_pipeline_gpt53
returncode: 1
stdout:
[check_ssot_disk] FAIL: gray_counter/yaml/gray_counter.ssot.yaml failed YAML/model validation
  function_model.transactions[] must include at least one executable output_rules entry with name/expr/width/port


Requirements:
# gray_counter IP Requirements

## Intent

Build a small synchronous Gray-code counter as a smoke fixture for the
common_ai_agent SSOT pipeline. The block is intentionally narrow: no bus,
no memory, no interrupt. It must still exercise SSOT, function-model,
cycle-model, equivalence goals, RTL, lint, TB, sim, coverage, and audit.

## Functional Behavior

- `clk` is the only clock.
- `rst_n` is an active-low asynchronous reset; on assertion the counter
  returns to `gray_value = 0` and `done` deasserts.
- `clear` synchronously forces `gray_value` to 0 and clears `done`.
- `enable` advances the counter by one Gray step on every rising clock
  edge while high.
- `gray_value[WIDTH-1:0]` is the registered Gray-coded output.
- `bin_value[WIDTH-1:0]` is the combinational binary equivalent of
  `gray_value` provided for observers and coverage.
- `done` pulses for exactly one cycle when the counter wraps from the
  maximum Gray code back to zero.

## Non-Goals

- No APB/AXI/CSR bus or register file.
- No clock-domain crossing, asynchronous interface, or reset-domain
  crossing.
- No memory, FIFO, or interrupt generation.
- The counter width is parameterized through SSOT; the default is 4 bits
  for the smoke fixture.

## Verification Hints

- Stimulus uses `enable` pulses with periodic `clear` and `rst_n`
  injection.
- Expected `bin_value` follows the standard `bin = gray ^ (gray >> 1)`
  identity.
- `done` must align with the wrap cycle, not with intermediate counts.
- Coverage should hit reset, clear-after-run, full wrap, hold (enable
  low), and a randomized walk.


Current SSOT YAML:
top_module:
  name: gray_counter
  file: rtl/gray_counter.sv
  version: '1.0'
  type: peripheral
  description: Synchronous parameterized Gray-code counter smoke-fixture IP with wrap pulse output.
  reference_spec: gray_counter/req/gray_counter_requirements.md
  target:
    technology: generic
    clock_freq_mhz: 200
    area_um2: null
    power_mw: null
sub_modules:
- name: gray_counter_core
  file: rtl/gray_counter_core.sv
  ownership: manifest
  ssot_gen: false
  source_sections:
  - function_model
  - cycle_model
  - fsm
  - error_handling
  - features
  - dataflow
  - decomposition
  - test_requirements
  implements:
  - function_model.transactions.GC_TXN_ADVANCE
  - function_model.transactions.GC_TXN_CLEAR
  - function_model.transactions.GC_TXN_RESET
  - function_model.transactions.GC_TXN_HOLD
  - cycle_model.pipeline
  - fsm.control
  - error_handling
  function_model_refs:
  - function_model.transactions.GC_TXN_ADVANCE
  - function_model.transactions.GC_TXN_CLEAR
  - function_model.transactions.GC_TXN_RESET
  - function_model.transactions.GC_TXN_HOLD
  - function_model.state_variables
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.ordering
  - cycle_model
  fsm_refs:
  - fsm.control
  - fsm
  connections:
  - module: gray_counter_core
    port: clk
    signal: clk
  - module: gray_counter_core
    port: rst_n
    signal: rst_n
  - module: gray_counter_core
    port: enable
    signal: enable
  - module: gray_counter_core
    port: clear
    signal: clear
  - module: gray_counter_core
    port: gray_value
    signal: gray_value
  - module: gray_counter_core
    port: bin_value
    signal: bin_value
  - module: gray_counter_core
    port: done
    signal: done
  description: Owns sequential counter state, Gray increment behavior, wrap detect, and one-cycle done pulse.
  feature_refs:
  - features
  dataflow_refs:
  - dataflow
  decomposition_refs:
  - decomposition
  test_refs:
  - test_requirements
- name: gray_counter_top
  file: rtl/gray_counter.sv
  ownership: manifest
  ssot_gen: true
  wiring_only: true
  source_sections: &id001
  - io_list
  - integration
  implements:
  - io_list.interfaces.control
  - io_list.interfaces.status
  - integration.connections
  ssot_refs:
  - io_list.interfaces
  - integration.connections
  connections:
  - module: gray_counter
    port: clk
    signal: clk
  - module: gray_counter
    port: rst_n
    signal: rst_n
  - module: gray_counter
    port: enable
    signal: enable
  - module: gray_counter
    port: clear
    signal: clear
  - module: gray_counter
    port: gray_value
    signal: gray_value
  - module: gray_counter
    port: bin_value
    signal: bin_value
  - module: gray_counter
    port: done
    signal: done
  description: Top-level wiring shell exposing canonical ports and instantiating gray_counter_core.
- name: gray_counter
  file: rtl/gray_counter.sv
  ownership: manifest
  ssot_gen: true
  description: Top-level integration module matching SSOT top_module
decomposition:
  units:
  - id: state_update
    kind: sequential_control
    source_refs:
    - function_model.transactions
    - cycle_model.pipeline
    rtl_candidates:
    - gray_counter_core
    verification_impact:
    - test_requirements.scenarios
  - id: gray_to_binary_obs
    kind: combinational_datapath
    source_refs:
    - function_model.transactions.GC_TXN_ADVANCE.outputs
    rtl_candidates:
    - gray_counter_core
    verification_impact:
    - test_requirements.coverage_goals.function
  strategy: manifest_owned_leaf_decomposition
  owners:
  - module: gray_counter_core
    file: rtl/gray_counter_core.sv
    responsibility: Owns sequential counter state, Gray increment behavior, wrap detect, and one-cycle done pulse.
    source_sections:
    - function_model
    - cycle_model
    - fsm
    - error_handling
  - module: gray_counter_top
    file: rtl/gray_counter.sv
    responsibility: Top-level wiring shell exposing canonical ports and instantiating gray_counter_core.
    source_sections: *id001
  - module: gray_counter
    file: rtl/gray_counter.sv
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
- name: WIDTH
  default: 4
  type: int
  description: Counter width in bits; number of Gray states is 2^WIDTH.
  constraints: WIDTH >= 2
  drives:
  - rtl/gray_counter.sv
  - rtl/gray_counter_core.sv
  - sim/tb_top.sv
- name: CLOCK_FREQ_MHZ
  default: 200
  type: int
  description: Nominal target frequency for timing assumptions.
  drives:
  - timing
  - synthesis
io_list:
  clock_domains:
  - name: clk
    frequency_mhz: 200
    description: Single synchronous clock domain.
    ports:
    - name: clk
      width: 1
      direction: input
      description: Primary clock.
  resets:
  - name: rst_n
    polarity: active_low
    sync_async: async_assert_sync_deassert
    description: Asynchronous active-low reset.
    ports:
    - name: rst_n
      width: 1
      direction: input
      description: Reset input.
  interfaces:
  - name: control
    type: custom
    role: input
    description: Single-cycle sampled control inputs.
    ports:
    - name: enable
      width: 1
      direction: input
      description: Advance one Gray step when high on rising edge.
    - name: clear
      width: 1
      direction: input
      description: Synchronous clear to zero and done=0.
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: status
    type: custom
    role: output
    description: Observable counter outputs.
    ports:
    - name: gray_value
      width: WIDTH
      direction: output
      description: Registered Gray-coded value.
    - name: bin_value
      width: WIDTH
      direction: output
      description: Combinational binary equivalent of gray_value.
    - name: done
      width: 1
      direction: output
      description: One-cycle pulse on wrap from max to zero.
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
features:
- name: Gray increment progression
  trigger: enable sampled high at rising edge and clear low
  datapath: gray_value decoded to binary, incremented modulo 2^WIDTH, re-encoded to Gray
  control: RUN state update path
  output: gray_value advances one legal Gray step
- name: Wrap pulse generation
  trigger: increment event when previous binary value is 2^WIDTH-1
  datapath: wrap detect comparator drives done pulse
  control: RUN transition to WRAP_PULSE microstate for one cycle
  output: done asserted for exactly one cycle
- name: Deterministic clear/reset
  trigger: rst_n low (async) or clear high on sampled edge
  datapath: state forced to zero
  control: RESET/CLEAR transitions
  output: gray_value=0, bin_value=0, done=0
dataflow:
  control_path:
    source: enable, clear, rst_n
    sequence: sample inputs -> select reset/clear/advance/hold transaction -> commit state
  state_path:
    source: gray_value_reg
    transform: gray_to_bin -> +1 mod 2^WIDTH -> bin_to_gray
    destination: gray_value_reg
  observability_path:
    source: gray_value_reg
    transform: gray_to_bin combinational XOR fold
    destination: bin_value output
  pulse_path:
    source: prev_bin_is_max and advance_event
    destination: done output pulse register
function_model:
  purpose: Cycle-independent architectural contract for Gray counting, clear/reset semantics, and wrap pulse behavior.
  state_variables:
  - name: gray_state
    source: io_list.interfaces.status.gray_value
    reset: 0
    description: Architectural Gray counter register.
  - name: bin_state
    source: derived(gray_state)
    reset: 0
    description: Decoded binary state derived from gray_state.
  - name: done_state
    source: io_list.interfaces.status.done
    reset: 0
    description: One-cycle completion pulse state.
  transactions:
  - id: GC_TXN_RESET
    name: asynchronous_reset_assert
    preconditions:
    - rst_n == 0
    inputs:
    - rst_n
    outputs:
    - gray_value == 0
    - bin_value == 0
    - done == 0
    side_effects:
    - gray_state set to 0 immediately on reset assertion
    - done_state cleared
    output_rules: []
  - id: GC_TXN_CLEAR
    name: synchronous_clear
    preconditions:
    - rst_n == 1
    - clear sampled high on rising clock edge
    inputs:
    - clear
    outputs:
    - gray_value == 0 after edge
    - bin_value == 0 after edge
    - done == 0 after edge
    side_effects:
    - gray_state overwritten with 0
    - done_state cleared
    output_rules: []
  - id: GC_TXN_ADVANCE
    name: advance_one_gray_step
    preconditions:
    - rst_n == 1
    - clear == 0 on sampled edge
    - enable == 1 on sampled edge
    inputs:
    - enable
    - current gray_state
    outputs:
    - next binary state equals (current bin_state + 1) mod 2^WIDTH
    - next gray_value equals bin_to_gray(next binary state)
    - bin_value equals gray_to_bin(gray_value) at all observable times
    side_effects:
    - gray_state updates to next_gray
    - done_state set to 1 iff current bin_state is max value; else 0
    error_cases:
    - condition: WIDTH < 2
      result: Configuration error; synthesis/test should fail parameter constraint checks
    output_rules: []
  - id: GC_TXN_HOLD
    name: hold_state
    preconditions:
    - rst_n == 1
    - clear == 0 on sampled edge
    - enable == 0 on sampled edge
    inputs:
    - enable
    outputs:
    - gray_value remains unchanged
    - bin_value remains decode(gray_value)
    - done == 0
    side_effects:
    - done_state forced low in non-wrap hold cycles
    output_rules: []
  invariants:
  - gray_value is always a legal WIDTH-bit Gray encoding of bin_state.
  - bin_value always equals gray_to_bin(gray_value) combinationally.
  - done is asserted for at most one consecutive cycle per wrap event.
  - clear has priority over enable on sampled clock edges.
  - reset dominates all synchronous controls when asserted.
  reference_model_hint: Scoreboard model should maintain binary golden state, derive Gray by g=b^(b>>1), decode DUT gray_value each cycle, and
    check done pulse only on max->0 wrap.
cycle_model:
  purpose: Cycle-accurate control/latency contract for sampled inputs and registered outputs.
  executable: python
  clock: clk
  reset:
    assertion: rst_n low asynchronously clears gray_value and done.
    deassertion: first functional sample occurs on first rising edge after rst_n returns high.
  latency:
    control_to_state_update:
      min_cycles: 1
      max_cycles: 1
      description: enable/clear sampled on edge, new gray_value visible after that edge.
    gray_to_bin_observation:
      min_cycles: 0
      max_cycles: 0
      description: bin_value is combinational decode of current gray_value.
    done_pulse_width:
      min_cycles: 1
      max_cycles: 1
      description: done pulse is exactly one cycle on wrap event.
  handshake_rules:
  - signal: enable
    rule: Sampled only on rising clock edge; no combinational feedback obligations.
  - signal: clear
    rule: If high on rising edge, clear transaction executes and masks enable advance for that edge.
  - signal: rst_n
    rule: Asynchronous assertion immediately clears state; synchronous behavior resumes after deassertion and next rising edge.
  pipeline:
  - stage: S0_SAMPLE
    cycle: N
    action: Sample rst_n/clear/enable and current gray_state.
  - stage: S1_COMPUTE
    cycle: N
    action: Compute next binary/Gray and wrap flag combinationally.
  - stage: S2_COMMIT
    cycle: N->N+1 boundary
    action: Commit gray register and done pulse register at rising edge according to priority reset>clear>enable>hold.
  - stage: S3_OBSERVE
    cycle: N+1
    action: Observe updated gray_value and combinational bin_value decode.
  ordering:
  - Asynchronous reset effect precedes any synchronous clear/enable action while rst_n is low.
  - Within a rising-edge sample, clear decision is evaluated before enable advance.
  - done update is ordered with gray register commit from the same sampled edge.
  backpressure:
  - No ready/valid interface; design is always able to sample control each clock.
  observability:
  - Every function_model transaction maps to S0..S3 progression with deterministic one-cycle state commit.
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
    description: Single synchronous domain.
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
    register_width: 0
    addr_width: 0
    byte_addressable: false
  register_list: []
  note: No CSR/register file by requirement; control is direct pin-level.
  no_registers: true
  policy: No firmware-visible registers are declared; add register_list before CSR behavior is implemented.
memory:
  instances: []
  note: No SRAM/FIFO/memory macros; only internal flip-flop state.
interrupts:
  sources: []
  output:
    signal: none
    polarity: n/a
    type: none
  note: No interrupt generation by requirement.
fsm:
  control:
    states:
    - IDLE
    - RUN
    - WRAP_PULSE
    - CLEARED
    - RESET
    transitions:
    - from: RESET
      to: IDLE
      condition: rst_n deasserted and first rising edge observed
    - from: IDLE
      to: CLEARED
      condition: clear sampled high
    - from: IDLE
      to: RUN
      condition: enable sampled high and clear low
    - from: RUN
      to: WRAP_PULSE
      condition: advance event causes max->0 wrap
    - from: RUN
      to: IDLE
      condition: enable sampled low and clear low
    - from: WRAP_PULSE
      to: RUN
      condition: enable remains high after one pulse cycle
    - from: WRAP_PULSE
      to: IDLE
      condition: enable low after pulse
    - from: CLEARED
      to: IDLE
      condition: clear low on next edge
  note: FSM is abstract control model for verification traceability; RTL may implement equivalent compact logic.
timing:
  target_clocks:
  - domain: clk
    target_mhz: 200
    duty_cycle: 50
  latency_budget:
  - path: enable/clear sampled edge to gray_value update
    min_cycles: 1
    max_cycles: 1
  - path: gray_value to bin_value
    min_cycles: 0
    max_cycles: 0
  - path: wrap detect to done
    min_cycles: 1
    max_cycles: 1
  sta_expectations:
  - Meet setup/hold at target frequency with WIDTH default=4 and scalable WIDTH parameter.
power:
  domains:
  - name: PD_MAIN
    supply: VDD
    description: Always-on logic domain for smoke fixture.
  power_states:
  - name: 'ON'
    description: Clock active; normal operation.
  - name: RESET_ACTIVE
    description: rst_n asserted, state held cleared.
  clock_gating:
    used: false
    rationale: Tiny fixture; no dedicated gating required.
  upf_required: false
security:
  classification: non_security_critical_test_ip
  assets:
  - Correct state transition semantics
  - Deterministic reset/clear behavior
  - Accurate done pulse used for downstream checks
  threat_model:
  - Malformed stimulus toggling reset/clear near clock edges
  - Parameter misuse (illegal WIDTH) causing undefined behavior
  - X-propagation from uninitialized logic in simulation
  mitigations:
  - Explicit reset behavior and priority ordering
  - WIDTH constraint and lint/assertion checks
  - Deterministic combinational decode and default assignments
  privilege_model: System-level access control is owned by the integrating bus/firewall unless explicitly declared here.
error_handling:
  error_sources:
  - id: ERR_PARAM_WIDTH
    condition: WIDTH < 2
    architectural_effect: Status/error reporting follows the SSOT error policy
  - id: ERR_PROTOCOL_RESET_GLITCH
    condition: rst_n unknown or glitching
    architectural_effect: Status/error reporting follows the SSOT error policy
  propagation:
  - Parameter errors propagate to synthesis/sim gate as hard failures.
  - Reset protocol issues propagate to DV assertion failures.
  recovery:
  - For runtime control behavior, asserting rst_n low recovers architectural state to zero.
  - Parameter misconfiguration requires rebuild with legal WIDTH.
debug_observability:
  waveform_must_probe:
  - clk
  - rst_n
  - enable
  - clear
  - gray_value
  - bin_value
  - done
  - internal_bin_next
  - wrap_detect
  trace_events:
  - id: EV_RESET
    trigger: rst_n asserted
    payload: gray_value=0,done=0
  - id: EV_CLEAR
    trigger: clear sampled high
    payload: gray_value->0
  - id: EV_ADVANCE
    trigger: enable sampled high and clear low
    payload: prev_gray,next_gray,prev_bin,next_bin
  - id: EV_WRAP_DONE
    trigger: wrap event
    payload: done pulse asserted for one cycle
  status_outputs:
  - status/debug signals declared in io_list or registers
integration:
  bus_attachment:
    type: none
    description: Standalone pin-level block; no APB/AXI/CSR interface.
  dependencies:
  - Single clean synchronous clock source
  - Asynchronous active-low reset source meeting timing assumptions
  - Upstream stimulus driver for enable/clear
  connections:
  - module: gray_counter
    port: clk
    signal: soc_clk_or_tb_clk
  - module: gray_counter
    port: rst_n
    signal: soc_rst_n_or_tb_rst_n
  - module: gray_counter
    port: enable
    signal: control_enable
  - module: gray_counter
    port: clear
    signal: control_clear
  connection_contract_status: missing machine-readable module wiring; child RTL drafts may proceed from owner packets, but top integration/signoff
    must stay blocked until SSOT authors integration.connections or sub_modules[].connections with module/port/signal records
  integration_notes:
  - Integrator must connect every declared io_list port and honor timing/reset assumptions.
dft:
  scan_required: false
  controllability:
  - All control inputs (rst_n, clear, enable) directly controllable from testbench/ATE wrapper.
  observability:
  - All architectural outputs (gray_value, bin_value, done) directly observable at top ports.
  mbist_required: false
  atpg_notes:
  - Small sequential depth; stuck-at coverage expected without dedicated test points.
synthesis:
  dialect: systemverilog_2012
  constraints:
  - Primary clock constraint from timing.target_clocks
  - Asynchronous reset path treated per library reset semantics
  - Honor WIDTH parameterization without hardcoded constants
  required_outputs:
  - synthesis netlist
  - area report
  - timing report
  - unconstrained path report
  top_module: gray_counter
pnr:
  utilization_pct: 10
  aspect_ratio: 1.0
  core_space_um: 10.0
  global_density: 0.5
  io_layers:
    horizontal: met3
    vertical: met2
  cts:
    buf_list:
    - generic_clkbuf_small
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
  parameter_header: rtl/gray_counter_param.vh
  conventions:
  - Use nonblocking assignments in sequential logic.
  - Use blocking assignments in combinational logic.
  - No inferred latches.
  - Asynchronous active-low reset in sequential blocks.
  - Clear priority over enable in next-state logic.
  - Parameterize width-dependent constants with WIDTH.
  lint_waivers: []
reuse_modules: []
custom:
  assumptions:
  - Gray sequence generation uses binary increment then Gray re-encode; equivalent Gray-adjacent sequence is acceptable if function_model invariants
    hold.
  note: Smoke-fixture IP intentionally minimal to validate pipeline contracts.
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
  - rtl/gray_counter_param.vh
  rtl:
  - rtl/gray_counter.sv
  - rtl/gray_counter_core.sv
  sim:
  - sim/tb_top.sv
  - sim/tb_program.sv
  - sim/gray_counter_ref_model.py
  firmware: []
  docs:
  - doc/gray_counter_mas.md
  - docs/README.md
  tb:
  - tb/cocotb/test_gray_counter.py
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
    name: function_model transaction GC_TXN_RESET
    stimulus: Drive preconditions for function_model transaction `GC_TXN_RESET`.
    expected: Outputs and side effects match `GC_TXN_RESET` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.GC_TXN_RESET
  - id: SC07
    name: function_model transaction GC_TXN_CLEAR
    stimulus: Drive preconditions for function_model transaction `GC_TXN_CLEAR`.
    expected: Outputs and side effects match `GC_TXN_CLEAR` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.GC_TXN_CLEAR
  - id: SC08
    name: function_model transaction GC_TXN_ADVANCE
    stimulus: Drive preconditions for function_model transaction `GC_TXN_ADVANCE`.
    expected: Outputs and side effects match `GC_TXN_ADVANCE` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.GC_TXN_ADVANCE
  - id: SC09
    name: function_model transaction GC_TXN_HOLD
    stimulus: Drive preconditions for function_model transaction `GC_TXN_HOLD`.
    expected: Outputs and side effects match `GC_TXN_HOLD` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.GC_TXN_HOLD
  scoreboard_checks: 12
  coverage_goals:
    function:
      target_pct: 100
      model: function_model
      description: Cover each declared transaction and invariant outcome.
      bins:
      - id: FCOV_TXN_RESET
        source_ref: function_model.transactions.GC_TXN_RESET
        class: transaction
        description: Reset transaction observed
      - id: FCOV_TXN_CLEAR
        source_ref: function_model.transactions.GC_TXN_CLEAR
        class: transaction
        description: Clear transaction observed
      - id: FCOV_TXN_ADVANCE
        source_ref: function_model.transactions.GC_TXN_ADVANCE
        class: transaction
        description: Advance transaction observed
      - id: FCOV_TXN_HOLD
        source_ref: function_model.transactions.GC_TXN_HOLD
        class: transaction
        description: Hold transaction observed
    cycle:
      target_pct: 100
      model: cycle_model
      description: Cover input sampling, commit, and done pulse timing/order rules.
      bins:
      - id: CCOV_PIPE_SAMPLE
        source_ref: cycle_model.pipeline
        class: pipeline_stage
        description: Sample stage hit
      - id: CCOV_PIPE_COMMIT
        source_ref: cycle_model.pipeline
        class: pipeline_stage
        description: Commit stage hit
      - id: CCOV_ORDER_CLEAR_PRIORITY
        source_ref: cycle_model.ordering
        class: ordering
        description: Clear priority observed
      - id: CCOV_DONE_ONE_CYCLE
        source_ref: cycle_model.latency.done_pulse_width
        class: latency
        description: Done pulse width constrained to one cycle
    functional: 'Legacy alias: function + cycle'
    code: line >= 95%, branch >= 90%
    scenario: All SSOT scenarios pass with executable cocotb/pyuvm checkers and FL-vs-RTL scoreboard evidence
quality_gates:
  ssot:
    pass: All required SSOT sections complete; checker validates structure and semantic minimums with no repair.
    evidence:
    - gray_counter/yaml/gray_counter.ssot.yaml
    - workflow/ssot-gen/scripts/check_ssot_disk.sh output
  rtl:
    pass: RTL compiles, reset/clear/enable behavior matches function_model and cycle_model, and lint clean or waived.
    evidence:
    - compile.log
    - lint/lint_report.txt
    - sim/equivalence_audit.json
  rtl_gen:
    profile: standard
    pass: Manifest module ownership refs resolve and rtl-gen TODO ledger items are implementable from SSOT without semantic gaps.
    evidence:
    - rtl/rtl_todo_plan.json
    - rtl/rtl_authoring_provenance.json
  dv:
    pass: All required test scenarios execute with scoreboard pass and no unresolved mismatches.
    evidence:
    - sim/test_results.xml
    - sim/scoreboard_report.json
  coverage:
    pass: Function and cycle coverage goals reach target or have approved waiver.
    evidence:
    - cov/coverage.json
    - sim/coverage_report.md
  eda:
    pass: Synthesis/STA/PnR complete and timing target met for default WIDTH or waived.
    evidence:
    - syn/report_timing.rpt
    - sta/sta_summary.rpt
    - pnr/pnr_summary.rpt
  signoff:
    pass: SSOT-RTL-DV traceability closed; all required gates green or waived by owner.
    evidence:
    - traceability/signoff_matrix.json
    - release/signoff.md
traceability:
  yaml_to_output:
  - yaml: top_module
    output: rtl/gray_counter.sv
  - yaml: parameters
    output: rtl/gray_counter_param.vh and module parameterization
  - yaml: io_list.interfaces
    output: Top-level port declarations and TB drivers/monitors
  - yaml: function_model
    output: Reference model and scoreboard expected-state calculations
  - yaml: cycle_model
    output: RTL sequential update timing and temporal assertions
  - yaml: fsm
    output: Control-state intent checks and waveform debug labels
  - yaml: error_handling
    output: Assertions and config checks
  - yaml: test_requirements.scenarios
    output: cocotb/pyuvm test sequences
  - yaml: quality_gates
    output: CI gate criteria and signoff artifacts
  - yaml: function_model/cycle_model/test_requirements
    output: verify/equivalence_goals.json and FL-vs-RTL scoreboard contracts
  - yaml: timing
    output: STA constraints and latency pass/fail criteria
  - yaml: security
    output: Threat mitigations and negative tests
  - yaml: debug_observability
    output: VCD probes and sim_debug inspection
workflow_todos:
  fl-model-gen:
  - id: FL_TODO_GRAY_REF
    content: Create executable Python functional model for Gray counter.
    detail: Implement reset/clear/advance/hold semantics and done pulse wrap condition exactly as function_model transactions.
    criteria:
    - Model exposes step() API with inputs rst_n/clear/enable
    - Model outputs expected gray_value/b
... <truncated 5620 chars>