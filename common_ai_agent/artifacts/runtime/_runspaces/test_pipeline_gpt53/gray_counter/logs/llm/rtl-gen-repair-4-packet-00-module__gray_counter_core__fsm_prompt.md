RTL-GEN PACKET MODE for gray_counter. Packet attempt 4.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "gray_counter/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "gray_counter/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "gray_counter/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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

Current packet: module__gray_counter_core__fsm
kind: module
work queue: 1/3 active packets (9 closed packets skipped from 13 total)
batch limit: 4; deferred active packets after this batch: 1
owner_module: gray_counter_core
owner_file: rtl/gray_counter_core.sv

SSOT observable latency contract:
{
  "cycle_model.latency": {
    "control_to_state_update": {
      "description": "enable/clear sampled on edge",
      "max_cycles": 1,
      "min_cycles": 1,
      "new gray_value visible after that edge.": null
    },
    "done_pulse_width": {
      "description": "done pulse is exactly one cycle on wrap event.",
      "max_cycles": 1,
      "min_cycles": 1
    },
    "gray_to_bin_observation": {
      "description": "bin_value is combinational decode of current gray_value.",
      "max_cycles": 0,
      "min_cycles": 0
    }
  },
  "cycle_model.pipeline": [
    {
      "action": "Sample rst_n/clear/enable and current gray_state.",
      "cycle": "N",
      "stage": "S0_SAMPLE"
    },
    {
      "action": "Compute next binary/Gray and wrap flag combinationally.",
      "cycle": "N",
      "stage": "S1_COMPUTE"
    },
    {
      "action": "Commit gray register and done pulse register at rising edge according to priority reset>clear>enable>hold.",
      "cycle": "N_to_Nplus1",
      "stage": "S2_COMMIT"
    },
    {
      "action": "Observe updated gray_value and combinational bin_value decode.",
      "cycle": "Nplus1",
      "stage": "S3_OBSERVE"
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
      "path": "enable_clear_to_gray_update"
    },
    {
      "max_cycles": 0,
      "min_cycles": 0,
      "path": "gray_to_bin_value"
    },
    {
      "max_cycles": 1,
      "min_cycles": 1,
      "path": "wrap_to_done"
    }
  ]
}

Locked SSOT YAML excerpt (gray_counter/yaml/gray_counter.ssot.yaml):
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
  - cycle_model.latency
  - cycle_model
  fsm_refs:
  - fsm.control
  - fsm
  feature_refs:
  - features
  dataflow_refs:
  - dataflow
  decomposition_refs:
  - decomposition
  test_refs:
  - test_requirements
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
    - function_model.transactions.GC_TXN_ADVANCE.output_rules
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
    - features
    - dataflow
    - decomposition
    - test_requirements
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
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Sampled on rising edge.
      stability: Inputs must meet setup/hold around rising edge.
      response: State updates follow cycle_model latencies.
    ports:
    - name: enable
      width: 1
      direction: input
      description: Advance one Gray step when high on rising edge.
    - name: clear
      width: 1
      direction: input
      description: Synchronous clear to zero and done=0.
  - name: status
    type: custom
    role: output
    description: Observable counter outputs.
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Continuously observable outputs.
      stability: gray_value/done are registered; bin_value is combinational decode.
      response: done pulse aligns with wrap commit cycle.
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
    output_rules:
    - name: gray_value_reset
      expr: '0'
      width: WIDTH
      port: gray_value
    - name: bin_value_reset
      expr: '0'
      width: WIDTH
      port: bin_value
    - name: done_reset
      expr: '0'
      width: 1
      port: done
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
    output_rules:
    - name: gray_value_clear
      expr: '0'
      width: WIDTH
      port: gray_value
    - name: bin_value_clear
      expr: '0'
      width: WIDTH
      port: bin_value
    - name: done_clear
      expr: '0'
      width: 1
      port: done
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
    output_rules:
    - name: gray_advance
      expr: ((bin_state + 1) ^ ((bin_state + 1) >> 1)) & ((1<<WIDTH)-1)
      width: WIDTH
      port: gray_value
    - name: bin_observe
      expr: gray_to_bin(gray_value)
      width: WIDTH
      port: bin_value
    - name: done_wrap
      expr: (1 if bin_state == ((1<<WIDTH)-1) else 0)
      width: 1
      port: done
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
    output_rules:
    - name: gray_hold
      expr: gray_state
      width: WIDTH
      port: gray_value
    - name: bin_hold
      expr: gray_to_bin(gray_state)
      width: WIDTH
      port: bin_value
    - name: done_hold
      expr: '0'
      width: 1
      port: done
  invariants:
  - gray_value is always a legal WIDTH-bit Gray encoding of bin_state.
  - bin_value always equals gray_to_bin(gray_value) combinationally.
  - done is asserted for at most one consecutive cycle per wrap event.
  - clear has priority over enable on sampled clock edges.
  - reset dominates all synchronous controls when asserted.
  reference_model_hint: Scoreboard model maintains binary golden state, derives gray as g=b^(b>>1), decodes DUT gray_value each cycle, and checks
    done pulse only on max->0 wrap.
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
      description: enable/clear sampled on edge
      new gray_value visible after that edge.: null
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
    rule: If high on rising edge
    clear transaction executes and masks enable advance for that edge.: null
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
    cycle: N_to_Nplus1
    action: Commit gray register and done pulse register at rising edge according to priority reset>clear>enable>hold.
  - stage: S3_OBSERVE
    cycle: Nplus1
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
timing:
  target_clocks:
  - domain: clk
    target_mhz: 200
    duty_cycle: 50
  latency_budget:
  - path: enable_clear_to_gray_update
    min_cycles: 1
    max_cycles: 1
  - path: gray_to_bin_value
    min_cycles: 0
    max_cycles: 0
  - path: wrap_to_done
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
  - name: true
    description: Clock active; normal operation.
  - name: RESET_ACTIVE
    description: rst_n asserted
    state held cleared.: null
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
    architectural_effect: Build-time configuration error
  - id: ERR_PROTOCOL_RESET_GLITCH
    condition: rst_n unknown or glitching
    architectural_effect: DV protocol assertion failure
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
    payload: gray_value=0_done=0
  - id: EV_CLEAR
    trigger: clear sampled high
    payload: gray_value_to_0
  - id: EV_ADVANCE
    trigger: enable sampled high and clear low
    payload: prev_gray_next_gray_prev_bin_next_bin
  - id: EV_WRAP_DONE
    trigger: wrap event
    payload: done_pulse_asserted_one_cycle
  status_outputs:
  - status/debug signals declared in io_list
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
  - module: gray_counter
    port: gray_value
    signal: observed_gray_value
  - module: gray_counter
    port: bin_value
    signal: observed_bin_value
  - module: gray_counter
    port: done
    signal: observed_done
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
  - Gray sequence generation uses binary increment then Gray re-encode.
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
      description: Cover sampling, commit, and done pulse timing/order rules.
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
        description: Done pulse constrained to one cycle
    functional: Legacy alias function+cycle
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
    pass: Every SSOT test_requirements scenario has an executable checker and FL-vs-RTL equivalence goal
    evidence:
    - verify/equivalence_goals.json
    - sim/scoreboard_events.jsonl
    - tb/cocotb tests
    - scenario implementation map
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
    pass: SSOT, FL/equivalence, RTL, lint, DV, sim, coverage, and EDA gates pass with fresh artifacts
    evidence:
    - ATLAS progress signoff PASS
traceability:
  yaml_to_output:
  - yaml: top_module
    output: rtl/gray_counter.sv
  - yaml: parameters
    output: rtl/gray_counter_param.vh and module parameterization
  - yaml: io_list.interfaces
    output: top-level port declarations and TB drivers/monitors
  - yaml: function_model
    output: reference model and scoreboard expected-state calculations
  - yaml: cycle_model
    output: RTL sequential update timing and temporal assertions
  - yaml: fsm
    output: control-state intent checks and waveform debug labels
  - yaml: test_requirements.scenarios
    output: cocotb/pyuvm test sequences
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
  fl-model-gen:
  - id: FL_TODO_GRAY_REF
    content: Create executable Python functional model for Gray counter.
    detail: Implement reset/clear/advance/hold semantics and done pulse wrap condition exactly as function_model transactions and output_rules.
    criteria:
    - Model exposes step(rst_n, clear, enable)
    - Model returns gray_value, bin_value, done per transaction output_rules
    source_refs:
    - function_model.transactions
    - function_model.invariants
    owner_module: gray_counter_core
    owner_file: rtl/gray_counter_core.sv
    priority: high
    required: true
  rtl-gen:
  - id: RTL_TODO_CORE_SEMANTICS
    content: Implement core sequential and combinational behavior.
    detail: RTL must implement priority reset>clear>enable>hold, gray/bin transforms, and one-cycle wrap done pulse.
    criteria:
    - All function_model transactions implemented with matching observable outputs
    - cycle_model latency/ordering rules hold in simulation
    source_refs:
    - function_model.transactions
    - cycle_model
    - fsm.control
    owner_module: gray_counter_core
    owner_file: rtl/gray_counter_core.sv
    priority: high
    required: true
  tb-gen:
  - id: TB_TODO_SCENARIOS
    content: Implement scenario tests and scoreboard.
    detail: Build cocotb/pyuvm tests for SC01..SC05 with reference-model checks each cycle.
    criteria:
    - All scenarios pass
    - Coverage bins mapped to scenario evidence
    source_refs:
    - test_requirements.scenarios
    - test_requirements.coverage_goals
    owner_module: gray_counter
    owner_file: sim/tb_top.sv
    priority: high
    required: true
  sim_debug: []
  coverage: []
  syn: []
  pnr: []
  sta: []
  sta-post: []
generation_flow:
  steps:
  - name: validate_ssot
    command: bash workflow/ssot-gen/scripts/check_ssot_disk.sh gray_counter
    description: Validate production SSOT structure and quality gates
  - name: handoff_fl_model
    command: /ssot-fl-model gray_counter
    description: Generate FunctionalModel, decomposition, and FCOV plan from SSOT
  - name: handoff_equivalence_goals
    command: /ssot-equiv-goals gray_counter
    description: Derive FL-vs-RTL equivalence goals before TB generation
  - name: handoff_rtl
    command: /ssot-rtl gray_counter
    description: Generate RTL from validated SSOT
  - name: handoff_tb
    command: /ssot-tb-cocotb gray_counter
    description: Generate cocotb/pyuvm verification from validated SSOT
  - name: handoff_sim_debug
    command: /wf sim_debug
    description: Run simulation, waveform, and coverage inspection
rtl_contract:
  top: gray_counter
  owner_policy: SSOT is authoritative for function_model, cycle_model, decomposition, and DV contracts.
  reset_policy:
    signal: rst_n
    polarity: active_low
    style: async_assert_sync_deassert
  implementation_notes:
  - clear has synchronous priority over enable when rst_n is high.
  - done is a one-cycle pulse only on modulo wrap from max binary count to zero.
  owner: ssot-gen
  type: ssot_derived_rule_contract
  transaction: GC_TXN_RESET
  clock: clk
  reset: rst_n
  reset_active: low
  sample_condition: enable
  input_map:
    enable: enable
    clear: clear
  output_map:
    gray_value: gray_value
    bin_value: bin_value
    done: done
  contract_invariants:
  - RTL-visible behavior implements the referenced function_model transaction.
  - Input sampling and output observation follow cycle_model handshake and latency rules.
  output_rules:
  - name: gray_value_reset
    port: gray_value
    expr: '0'
    width: WIDTH
    description: FunctionalModel output observable mapped to DUT output port.
  - name: bin_value_reset
    port: bin_value
    expr: '0'
    width: WIDTH
    description: FunctionalModel output observable mapped to DUT output port.
  - name: done_reset
    port: done
    expr: '0'
    width: 1
    description: FunctionalModel output observable mapped to DUT output port.


Base rtl-gen contract:
Prepare rtl-gen for gray_counter using only gray_counter/yaml/gray_counter.ssot.yaml and gray_counter/rtl/rtl_todo_plan.json, gray_counter/rtl/rtl_authoring_plan.json, and packets under gray_counter/rtl/authoring_packets. Return exactly one JSON object and nothing else. Success schema: {"files":[{"path":"gray_counter/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"},{"path":"gray_counter/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"},{"path":"gray_counter/list/gray_counter.f","kind":"filelist","content":"<filelist>"}]}. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=d473b2610c40c79069346972679ffe8377525380178163598257ddce80b959b1. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "gray_counter_top",
        "reason": "13 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      }
    ],
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "dut_lint",
        "owner_module": "gray_counter_top",
        "reason": "DUT lint artifact is not clean.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "gray_counter_top",
        "reason": "15 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 21,
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
    "open_required_todos": 16,
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
          "gray_counter/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py gray_counter --top gray_counter",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py gray_counter --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "gray_counter/list/gray_counter.f covers the current DUT RTL/header sources."
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
          "gray_counter/rtl/rtl_todo_plan.json",
          "gray_counter/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py gray_counter --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "15 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ]
  },
  "ip": "gray_counter",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 12,
      "open_required_count": 12,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__fsm",
      "required_count": 13,
      "status_counts": {
        "open": 12,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__function_model_01.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__function_model_01",
      "required_count": 48,
      "status_counts": {
        "open": 1,
        "pass": 47
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/gray_counter.sv",
      "owner_module": "gray_counter",
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
      "open_required_count": 2,
      "owner_file": "rtl/gray_counter.sv",
      "owner_module": "gray_counter",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 2,
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__cycle_model",
      "required_count": 15,
      "status_counts": {
        "pass": 15
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__error_handling",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__features.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__features",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__function_model_02",
      "required_count": 10,
      "status_counts": {
        "pass": 10
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__test_requirements",
      "required_count": 9,
      "status_counts": {
        "pass": 9
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_core__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "packet_id": "module__gray_counter_core__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__gray_counter_top.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter.sv",
      "owner_module": "gray_counter_top",
      "packet_id": "module__gray_counter_top",
      "required_count": 27,
      "status_counts": {
        "pass": 27
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/gray_counter.sv",
      "owner_module": "gray_counter",
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
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 0,
    "human_locked_tasks": 0,
    "llm_actionable_packets": 3,
    "llm_actionable_tasks": 14,
    "max_packet_required_tasks": 48,
    "module_packets": 10,
    "next_llm_packets": [
      "module__gray_counter_core__fsm",
      "module__gray_counter_core__function_model_01",
      "rtl_gate_evidence_closure"
    ],
    "packet_task_limit": 48,
    "packets": 13,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 146,
    "sliced_module_packets": 9,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 2,
    "total_tasks": 146,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "d473b2610c40c79069346972679ffe8377525380178163598257ddce80b959b1",
  "top": "gray_counter",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/gray_counter_core.sv):
module gray_counter_core #(
    parameter integer WIDTH = 4
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             enable,
    input  logic             clear,
    output logic [WIDTH-1:0] gray_value,
    output logic [WIDTH-1:0] bin_value,
    output logic             done
);

    localparam [WIDTH-1:0] MAX_BIN = {WIDTH{1'b1}};

    // WIDTH legality marker participates in live logic to avoid unused-signal lint.
    logic width_ok;
    assign width_ok = (WIDTH >= 2);

    // Architectural state: registered Gray output and one-cycle done pulse.
    logic [WIDTH-1:0] gray_state;
    logic             done_state;

    // Decode current Gray to binary combinationally (no loops/functions).
    // Prefix-XOR expansion using log-depth shift/XOR chain.
    logic [WIDTH-1:0] gray_to_bin_s1;
    logic [WIDTH-1:0] gray_to_bin_s2;
    logic [WIDTH-1:0] gray_to_bin_s3;
    logic [WIDTH-1:0] gray_to_bin_s4;
    logic [WIDTH-1:0] gray_to_bin_s5;
    logic [WIDTH-1:0] curr_bin;

    assign gray_to_bin_s1 = gray_state ^ (gray_state >> 1);
    assign gray_to_bin_s2 = gray_to_bin_s1 ^ (gray_to_bin_s1 >> 2);
    assign gray_to_bin_s3 = gray_to_bin_s2 ^ (gray_to_bin_s2 >> 4);
    assign gray_to_bin_s4 = gray_to_bin_s3 ^ (gray_to_bin_s3 >> 8);
    assign gray_to_bin_s5 = gray_to_bin_s4 ^ (gray_to_bin_s4 >> 16);
    assign curr_bin       = gray_to_bin_s5;

    // Advance path from current sampled state.
    logic [WIDTH-1:0] next_bin;
    logic [WIDTH-1:0] next_gray;
    logic             wrap_detect;

    assign next_bin    = curr_bin + {{(WIDTH-1){1'b0}}, 1'b1};
    assign next_gray   = next_bin ^ (next_bin >> 1);
    assign wrap_detect = (curr_bin == MAX_BIN);

    // Observable outputs: gray/done are registered; bin is combinational decode of gray.
    assign gray_value = gray_state;
    assign done       = done_state;
    assign bin_value  = curr_bin;

    // Commit ordering reset > clear > enable > hold.
    // latency=1 rule: accepted enable updates gray/done in this same edge commit.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gray_state <= {WIDTH{1'b0}};
            done_state <= 1'b0;
        end else if (!width_ok) begin
            // Deterministic safe state if illegal parameterization is forced.
            gray_state <= {WIDTH{1'b0}};
            done_state <= 1'b0;
        end else if (clear) begin
            gray_state <= {WIDTH{1'b0}};
            done_state <= 1'b0;
        end else if (enable) begin
            gray_state <= next_gray;
            done_state <= wrap_detect;
        end else begin
            gray_state <= gray_state;
            done_state <= 1'b0;
        end
    end

endmodule


Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__gray_counter_core__fsm.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 21,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 4,
      "key": "fsm",
      "module_task_count": 102,
      "rule": "Owner module gray_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "fsm",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/gray_counter_core.sv",
      "name": "gray_counter_core",
      "refs": [
        "cycle_model",
        "cycle_model.latency",
        "cycle_model.ordering",
        "cycle_model.pipeline",
        "dataflow",
        "decomposition",
        "error_handling",
        "features",
        "fsm",
        "fsm.control",
        "function_model",
        "function_model.state_variables",
        "function_model.transactions.GC_TXN_ADVANCE",
        "function_model.transactions.GC_TXN_CLEAR",
        "function_model.transactions.GC_TXN_HOLD",
        "function_model.transactions.GC_TXN_RESET",
        "test_requirements"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/gray_counter_core.sv",
        "name": "gray_counter_core",
        "wiring_only": false
      },
      {
        "file": "rtl/gray_counter.sv",
        "name": "gray_counter_top",
        "wiring_only": true
      },
      {
        "file": "rtl/gray_counter.sv",
        "name": "gray_counter",
        "wiring_only": false
      }
    ],
    "quality_profile": "standard",
    "reference_profile": null,
    "ssot_connection_contracts": [
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter_core",
        "port": "clk",
        "signal": "clk",
        "signal_terms": [
          "clk"
        ],
        "source_ref": "sub_modules[0].connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter_core",
        "port": "rst_n",
        "signal": "rst_n",
        "signal_terms": [
          "rst_n"
        ],
        "source_ref": "sub_modules[0].connections[1]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter_core",
        "port": "enable",
        "signal": "enable",
        "signal_terms": [
          "enable"
        ],
        "source_ref": "sub_modules[0].connections[2]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter_core",
        "port": "clear",
        "signal": "clear",
        "signal_terms": [],
        "source_ref": "sub_modules[0].connections[3]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter_core",
        "port": "gray_value",
        "signal": "gray_value",
        "signal_terms": [
          "gray_value"
        ],
        "source_ref": "sub_modules[0].connections[4]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter_core",
        "port": "bin_value",
        "signal": "bin_value",
        "signal_terms": [
          "bin_value"
        ],
        "source_ref": "sub_modules[0].connections[5]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter_core",
        "port": "done",
        "signal": "done",
        "signal_terms": [
          "done"
        ],
        "source_ref": "sub_modules[0].connections[6]"
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
    "llm_actionable_open_count": 12,
    "open_required_count": 12,
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
  "ip": "gray_counter",
  "kind": "module",
  "owner_file": "rtl/gray_counter_core.sv",
  "owner_module": "gray_counter_core",
  "packet_id": "module__gray_counter_core__fsm",
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
      "fsm.state": 5,
      "fsm.transition": 8
    },
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 4,
      "key": "fsm",
      "module_task_count": 102,
      "rule": "Owner module gray_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "fsm",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 12,
    "required_count": 13,
    "source_refs": [
      "fsm.control.states.state_0",
      "fsm.control.states.state_1",
      "fsm.control.states.state_2",
      "fsm.control.states.state_3",
      "fsm.control.states.state_4",
      "fsm.control.transitions.transition_0",
      "fsm.control.transitions.transition_1",
      "fsm.control.transitions.transition_2",
      "fsm.control.transitions.transition_3",
      "fsm.control.transitions.transition_4",
      "fsm.control.transitions.transition_5",
      "fsm.control.transitions.transition_6",
      "fsm.control.transitions.transition_7"
    ],
    "status_counts": {
      "open": 12,
      "pass": 1
    },
    "task_count": 13
  },
  "tasks": [
    {
      "category": "fsm.state",
      "content": "Implement FSM state control.state_0",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.control.states.state_0",
        "Primary implementation evidence is in rtl/gray_counter_core.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.states.state_0.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: value=IDLE.",
      "evidence_terms": [
        "IDLE"
      ],
      "id": "RTL-0103",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.states.state_0",
      "ssot_context": {
        "value": "IDLE"
      },
      "ssot_refs": [
        "fsm.control.states.state_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "IDLE"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.state",
      "content": "Implement FSM state control.state_1",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.control.states.state_1",
        "Primary implementation evidence is in rtl/gray_counter_core.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.states.state_1.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: value=RUN.",
      "evidence_terms": [
        "RUN"
      ],
      "id": "RTL-0104",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.states.state_1",
      "ssot_context": {
        "value": "RUN"
      },
      "ssot_refs": [
        "fsm.control.states.state_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "RUN"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.state",
      "content": "Implement FSM state control.state_2",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.control.states.state_2",
        "Primary implementation evidence is in rtl/gray_counter_core.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.states.state_2.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: value=WRAP_PULSE.",
      "evidence_terms": [
        "WRAP_PULSE"
      ],
      "id": "RTL-0105",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.states.state_2",
      "ssot_context": {
        "value": "WRAP_PULSE"
      },
      "ssot_refs": [
        "fsm.control.states.state_2"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "WRAP_PULSE"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.state",
      "content": "Implement FSM state control.state_3",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.control.states.state_3",
        "Primary implementation evidence is in rtl/gray_counter_core.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.states.state_3.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: value=CLEARED.",
      "evidence_terms": [
        "CLEARED"
      ],
      "id": "RTL-0106",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.states.state_3",
      "ssot_context": {
        "value": "CLEARED"
      },
      "ssot_refs": [
        "fsm.control.states.state_3"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "CLEARED"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.state",
      "content": "Implement FSM state control.state_4",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.control.states.state_4",
        "Primary implementation evidence is in rtl/gray_counter_core.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.states.state_4.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: value=RESET.",
      "evidence_terms": [
        "RESET"
      ],
      "id": "RTL-0107",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.states.state_4",
      "ssot_context": {
        "value": "RESET"
      },
      "ssot_refs": [
        "fsm.control.states.state_4"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "RESET"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
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
        "Primary implementation evidence is in rtl/gray_counter_core.sv",
        "fsm.control.transitions.transition_0 condition is implemented as RTL control logic: rst_n deasserted and first rising edge observed",
        "fsm.control.transitions.transition_0 transition path RESET -> IDLE is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_0.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: from=RESET; to=IDLE; condition=rst_n deasserted and first rising edge observed.",
      "evidence_terms": [
        "IDLE",
        "RESET",
        "rst",
        "rst_n"
      ],
      "id": "RTL-0108",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_0",
      "ssot_context": {
        "condition": "rst_n deasserted and first rising edge observed",
        "from": "RESET",
        "to": "IDLE"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_0"
      ],
      "static_evidence": {
        "matched_count": 2,
        "matched_terms": [
          "rst",
          "rst_n"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "IDLE",
          "RESET",
          "rst",
          "rst_n"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 7,
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
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_1",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_1",
        "Primary implementation evidence is in rtl/gray_counter_core.sv",
        "fsm.control.transitions.transition_1 condition is implemented as RTL control logic: clear sampled high",
        "fsm.control.transitions.transition_1 transition path IDLE -> CLEARED is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_1.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: from=IDLE; to=CLEARED; condition=clear sampled high.",
      "evidence_terms": [
        "CLEARED",
        "IDLE"
      ],
      "id": "RTL-0109",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_1",
      "ssot_context": {
        "condition": "clear sampled high",
        "from": "IDLE",
        "to": "CLEARED"
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
          "CLEARED",
          "IDLE"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
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
        "Primary implementation evidence is in rtl/gray_counter_core.sv",
        "fsm.control.transitions.transition_2 condition is implemented as RTL control logic: enable sampled high and clear low",
        "fsm.control.transitions.transition_2 transition path IDLE -> RUN is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_2.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: from=IDLE; to=RUN; condition=enable sampled high and clear low.",
      "evidence_terms": [
        "IDLE",
        "RUN"
      ],
      "id": "RTL-0110",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_2",
      "ssot_context": {
        "condition": "enable sampled high and clear low",
        "from": "IDLE",
        "to": "RUN"
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
          "IDLE",
          "RUN"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
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
        "Primary implementation evidence is in rtl/gray_counter_core.sv",
        "fsm.control.transitions.transition_3 condition is implemented as RTL control logic: advance event causes max->0 wrap",
        "fsm.control.transitions.transition_3 transition path RUN -> WRAP_PULSE is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_3.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: from=RUN; to=WRAP_PULSE; condition=advance event causes max->0 wrap.",
      "evidence_terms": [
        "RUN",
        "WRAP_PULSE"
      ],
      "id": "RTL-0111",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_3",
      "ssot_context": {
        "condition": "advance event causes max->0 wrap",
        "from": "RUN",
        "to": "WRAP_PULSE"
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
          "RUN",
          "WRAP_PULSE"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
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
        "Primary implementation evidence is in rtl/gray_counter_core.sv",
        "fsm.control.transitions.transition_4 condition is implemented as RTL control logic: enable sampled low and clear low",
        "fsm.control.transitions.transition_4 transition path RUN -> IDLE is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_4.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: from=RUN; to=IDLE; condition=enable sampled low and clear low.",
      "evidence_terms": [
        "IDLE",
        "RUN"
      ],
      "id": "RTL-0112",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_4",
      "ssot_context": {
        "condition": "enable sampled low and clear low",
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
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_5",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_5",
        "Primary implementation evidence is in rtl/gray_counter_core.sv",
        "fsm.control.transitions.transition_5 condition is implemented as RTL control logic: enable remains high after one pulse cycle",
        "fsm.control.transitions.transition_5 transition path WRAP_PULSE -> RUN is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_5.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: from=WRAP_PULSE; to=RUN; condition=enable remains high after one pulse cycle.",
      "evidence_terms": [
        "RUN",
        "WRAP_PULSE"
      ],
      "id": "RTL-0113",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_5",
      "ssot_context": {
        "condition": "enable remains high after one pulse cycle",
        "from": "WRAP_PULSE",
        "to": "RUN"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_5"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "RUN",
          "WRAP_PULSE"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_6",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_6",
        "Primary implementation evidence is in rtl/gray_counter_core.sv",
        "fsm.control.transitions.transition_6 condition is implemented as RTL control logic: enable low after pulse",
        "fsm.control.transitions.transition_6 transition path WRAP_PULSE -> IDLE is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_6.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: from=WRAP_PULSE; to=IDLE; condition=enable low after pulse.",
      "evidence_terms": [
        "IDLE",
        "WRAP_PULSE"
      ],
      "id": "RTL-0114",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_6",
      "ssot_context": {
        "condition": "enable low after pulse",
        "from": "WRAP_PULSE",
        "to": "IDLE"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_6"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "IDLE",
          "WRAP_PULSE"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition control.transition_7",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.control.transitions.transition_7",
        "Primary implementation evidence is in rtl/gray_counter_core.sv",
        "fsm.control.transitions.transition_7 condition is implemented as RTL control logic: clear low on next edge",
        "fsm.control.transitions.transition_7 transition path CLEARED -> IDLE is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.\nSSOT ref: fsm.control.transitions.transition_7.\nOwner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.\nSSOT item context: from=CLEARED; to=IDLE; condition=clear low on next edge.",
      "evidence_terms": [
        "CLEARED",
        "IDLE"
      ],
      "id": "RTL-0115",
      "owner_file": "rtl/gray_counter_core.sv",
      "owner_module": "gray_counter_core",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.control.transitions.transition_7",
      "ssot_context": {
        "condition": "clear low on next edge",
        "from": "CLEARED",
        "to": "IDLE"
      },
      "ssot_refs": [
        "fsm.control.transitions.transition_7"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "CLEARED",
          "IDLE"
        ],
        "source_scope": "rtl/gray_counter_core.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "d473b2610c40c79069346972679ffe8377525380178163598257ddce80b959b1",
  "top": "gray_counter",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__gray_counter_core__fsm.md):
# RTL Authoring Packet: module__gray_counter_core__fsm

- Kind: module
- Owner module: gray_counter_core
- Owner file: rtl/gray_counter_core.sv
- Task count: 13
- Required tasks: 13

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
- LLM-actionable open tasks: 12
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, error_handling, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions.GC_TXN_ADVANCE, function_model.transactions.GC_TXN_CLEAR, function_model.transactions.GC_TXN_HOLD, function_model.transactions.GC_TXN_RESET
- Module slice: 4/9 section=fsm task_limit=48
- Slice rule: Owner module gray_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_counter_core.clk <= clk (sub_modules[0].connections[0])
  - gray_counter_core.rst_n <= rst_n (sub_modules[0].connections[1])
  - gray_counter_core.enable <= enable (sub_modules[0].connections[2])
  - gray_counter_core.clear <= clear (sub_modules[0].connections[3])
  - gray_counter_core.gray_value <= gray_value (sub_modules[0].connections[4])
  - gray_counter_core.bin_value <= bin_value (sub_modules[0].connections[5])
  - gray_counter_core.done <= done (sub_modules[0].connections[6])

## Tasks

### RTL-0103: Implement FSM state control.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=IDLE.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_0

### RTL-0104: Implement FSM state control.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=RUN.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_1

### RTL-0105: Implement FSM state control.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=WRAP_PULSE.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_2

### RTL-0106: Implement FSM state control.state_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_3.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=CLEARED.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_3
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_3

### RTL-0107: Implement FSM state control.state_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_4.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=RESET.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_4
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_4

### RTL-0108: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=RESET; to=IDLE; condition=rst_n deasserted and first rising edge observed.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_0 condition is implemented as RTL control logic: rst_n deasserted and first rising edge observed
  - fsm.control.transitions.transition_0 transition path RESET -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0109: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=IDLE; to=CLEARED; condition=clear sampled high.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_1 condition is implemented as RTL control logic: clear sampled high
  - fsm.control.transitions.transition_1 transition path IDLE -> CLEARED is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0110: Implement FSM transition control.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=IDLE; to=RUN; condition=enable sampled high and clear low.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_2 condition is implemented as RTL control logic: enable sampled high and clear low
  - fsm.control.transitions.transition_2 transition path IDLE -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_2

### RTL-0111: Implement FSM transition control.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_3.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=RUN; to=WRAP_PULSE; condition=advance event causes max->0 wrap.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_3
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_3 condition is implemented as RTL control logic: advance event causes max->0 wrap
  - fsm.control.transitions.transition_3 transition path RUN -> WRAP_PULSE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_3

### RTL-0112: Implement FSM transition control.transition_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_4.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=RUN; to=IDLE; condition=enable sampled low and clear low.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_4
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_4 condition is implemented as RTL control logic: enable sampled low and clear low
  - fsm.control.transitions.transition_4 transition path RUN -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_4

### RTL-0113: Implement FSM transition control.transition_5

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_5.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=WRAP_PULSE; to=RUN; condition=enable remains high after one pulse cycle.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_5
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_5 condition is implemented as RTL control logic: enable remains high after one pulse cycle
  - fsm.control.transitions.transition_5 transition path WRAP_PULSE -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_5

### RTL-0114: Implement FSM transition control.transition_6

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_6.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=WRAP_PULSE; to=IDLE; condition=enable lo
... <truncated 1920 chars>