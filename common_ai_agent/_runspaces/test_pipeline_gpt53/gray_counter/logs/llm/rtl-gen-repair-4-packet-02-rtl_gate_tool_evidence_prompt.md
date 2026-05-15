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

Current packet: rtl_gate_tool_evidence
kind: gate
work queue: 3/3 active packets (9 closed packets skipped from 13 total)
batch limit: 4; deferred active packets after this batch: 1
owner_module: gray_counter
owner_file: rtl/gray_counter.sv

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

Current owner RTL file (rtl/gray_counter.sv):
module gray_counter #(
    parameter integer WIDTH = 4,
    parameter integer CLOCK_FREQ_MHZ = 200
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             enable,
    input  logic             clear,
    output logic [WIDTH-1:0] gray_value,
    output logic [WIDTH-1:0] bin_value,
    output logic             done
);

    // CLOCK_FREQ_MHZ is an SSOT-owned top parameter (timing/synthesis contract).
    // Keep it semantically used without altering datapath behavior.
    logic clock_freq_param_used;
    assign clock_freq_param_used = (CLOCK_FREQ_MHZ >= 0);

    gray_counter_core #(
        .WIDTH(WIDTH)
    ) u_gray_counter_core (
        .clk       (clk),
        .rst_n     (rst_n),
        .enable    (enable),
        .clear     (clear),
        .gray_value(gray_value),
        .bin_value (bin_value),
        .done      (done)
    );

endmodule


Current tool evidence artifacts referenced by this packet:
### gray_counter/lint/dut_lint.json
{
  "schema_version": 1,
  "type": "dut_lint",
  "scope": "dut",
  "dut_only": true,
  "tool": "pyslang+verilator",
  "command": "pyslang rtl/gray_counter_core.sv rtl/gray_counter.sv && verilator --lint-only -Wall -Irtl -f list/gray_counter.f --top-module gray_counter",
  "cwd": "gray_counter",
  "top": "gray_counter",
  "filelist": "gray_counter/list/gray_counter.f",
  "rtl_files": [
    "rtl/gray_counter_core.sv",
    "rtl/gray_counter.sv"
  ],
  "timestamp": "2026-05-15T09:04:09.074060+00:00",
  "returncode": 1,
  "errors": 0,
  "warnings": 1,
  "waived_warnings": 0,
  "tool_results": [
    {
      "tool": "pyslang",
      "available": true,
      "command": "pyslang rtl/gray_counter_core.sv rtl/gray_counter.sv",
      "returncode": 0,
      "errors": 0,
      "warnings": 0,
      "diagnostics": [],
      "passed": true
    },
    {
      "tool": "verilator",
      "available": true,
      "command": "verilator --lint-only -Wall -Irtl -f list/gray_counter.f --top-module gray_counter",
      "returncode": 1,
      "errors": 0,
      "warnings": 1,
      "diagnostics": [
        {
          "severity": "warning",
          "rule": "UNUSEDSIGNAL",
          "file": "rtl/gray_counter.sv",
          "line": 16,
          "column": 11,
          "message": "Signal is not used: 'clock_freq_param_used'",
          "source": "    logic clock_freq_param_used;"
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


### gray_counter/rtl/rtl_todo_plan.json
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
    "open_required_todos": 16,
    "orphan_tasks": 0,
    "static_missing": 13,
    "status": "fail"
  },
  "generated_at": "2026-05-15T09:04:10Z",
  "ip": "gray_counter",
  "manifest_hierarchy_evidence": {
    "connection_contract_count": 21,
    "connection_contract_issues": [],
    "connection_contract_status": "pass",
    "declared_modules": [
      "gray_counter",
      "gray_counter_core"
    ],
    "graph": {
      "gray_counter": [
        "gray_counter_core"
      ],
      "gray_counter_core": []
    },
    "issues": [],
    "port_connection_issues": [],
    "port_connection_status": "pass",
    "reachable_modules": [
      "gray_counter",
      "gray_counter_core"
    ],
    "roots": [
      "gray_counter"
    ],
    "sources": [
      "rtl/gray_counter.sv",
      "rtl/gray_counter_core.sv"
    ],
    "status": "pass"
  },
  "manifest_signal_flow_evidence": {
    "checked_inputs": 4,
    "checked_outputs": 3,
    "issues": [],
    "reachable_modules": [
      "gray_counter",
      "gray_counter_core"
    ],
    "roots": [
      "gray_counter"
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
  "reference_profile": null,
  "reference_scale_gap": {},
  "rtl_implementation_depth_evidence": {
    "aggregate": {
      "behavior_owner_logic_modules": 1,
      "control_flow": 4,
      "depth_score": 58,
      "instances": 1,
      "lines": 106,
      "logic_modules": 2,
      "modules": 2,
      "nonconstant_assigns": 14,
      "procedural_blocks": 1,
      "source_files": 2,
      "state_updates": 10,
      "storage_decls": 15
    },
    "issues": [],
    "modules": [
      {
        "depth_score": 53,
        "file": "rtl/gray_counter_core.sv",
        "metrics": {
          "control_flow": 4,
          "instances": 0,
          "nonconstant_assigns": 13,
          "placeholder_tokens": false,
          "procedural_blocks": 1,
          "state_updates": 10,
          "storage_decls": 13
        },
        "module": "gray_counter_core"
      },
      {
        "depth_score": 5,
        "file": "rtl/gray_counter.sv",
        "metrics": {
          "control_flow": 0,
          "instances": 1,
          "nonconstant_assigns": 1,
          "placeholder_tokens": false,
          "procedural_blocks": 0,
          "state_updates": 0,
          "storage_decls": 2
        },
        "module": "gray_counter"
      }
    ],
    "profile": "standard",
    "reference_comparison": null,
    "status": "pass",
    "target_scale": {},
    "thresholds": {
      "behavior_owners": 1,
      "behavior_tasks": 94,
      "machine_connection_contracts": 21,
      "manifest_rtl_files": 2,
      "min_depth_score": 78,
      "min_logic_modules": 1
    }
  },
  "rtl_placeholder_free_evidence": {
    "checked": 2,
    "issues": [],
    "status": "pass"
  },
  "schema_version": 1,
  "source": "gray_counter/yaml/gray_counter.ssot.yaml",
  "ssot_connection_contracts": [
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter_core",
      "port": "clk",
      "raw": "{\"module\": \"gray_counter_core\", \"port\": \"clk\", \"signal\": \"clk\"}",
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
      "raw": "{\"module\": \"gray_counter_core\", \"port\": \"rst_n\", \"signal\": \"rst_n\"}",
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
      "raw": "{\"module\": \"gray_counter_core\", \"port\": \"enable\", \"signal\": \"enable\"}",
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
      "raw": "{\"module\": \"gray_counter_core\", \"port\": \"clear\", \"signal\": \"clear\"}",
      "signal": "clear",
      "signal_terms": [],
      "source_ref": "sub_modules[0].connections[3]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter_core",
      "port": "gray_value",
      "raw": "{\"module\": \"gray_counter_core\", \"port\": \"gray_value\", \"signal\": \"gray_value\"}",
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
      "raw": "{\"module\": \"gray_counter_core\", \"port\": \"bin_value\", \"signal\": \"bin_value\"}",
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
      "raw": "{\"module\": \"gray_counter_core\", \"port\": \"done\", \"signal\": \"done\"}",
      "signal": "done",
      "signal_terms": [
        "done"
      ],
      "source_ref": "sub_modules[0].connections[6]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "clk",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"clk\", \"signal\": \"clk\"}",
      "signal": "clk",
      "signal_terms": [
        "clk"
      ],
      "source_ref": "sub_modules[1].connections[0]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "rst_n",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"rst_n\", \"signal\": \"rst_n\"}",
      "signal": "rst_n",
      "signal_terms": [
        "rst_n"
      ],
      "source_ref": "sub_modules[1].connections[1]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "enable",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"enable\", \"signal\": \"enable\"}",
      "signal": "enable",
      "signal_terms": [
        "enable"
      ],
      "source_ref": "sub_modules[1].connections[2]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "clear",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"clear\", \"signal\": \"clear\"}",
      "signal": "clear",
      "signal_terms": [],
      "source_ref": "sub_modules[1].connections[3]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "gray_value",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"gray_value\", \"signal\": \"gray_value\"}",
      "signal": "gray_value",
      "signal_terms": [
        "gray_value"
      ],
      "source_ref": "sub_modules[1].connections[4]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "bin_value",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"bin_value\", \"signal\": \"bin_value\"}",
      "signal": "bin_value",
      "signal_terms": [
        "bin_value"
      ],
      "source_ref": "sub_modules[1].connections[5]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "done",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"done\", \"signal\": \"done\"}",
      "signal": "done",
      "signal_terms": [
        "done"
      ],
      "source_ref": "sub_modules[1].connections[6]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "clk",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"clk\", \"signal\": \"soc_clk_or_tb_clk\"}",
      "signal": "soc_clk_or_tb_clk",
      "signal_terms": [
        "soc_clk_or_tb_clk"
      ],
      "source_ref": "integration.connections[0]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "rst_n",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"rst_n\", \"signal\": \"soc_rst_n_or_tb_rst_n\"}",
      "signal": "soc_rst_n_or_tb_rst_n",
      "signal_terms": [
        "soc_rst_n_or_tb_rst_n"
      ],
      "source_ref": "integration.connections[1]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "enable",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"enable\", \"signal\": \"control_enable\"}",
      "signal": "control_enable",
      "signal_terms": [
        "control_enable"
      ],
      "source_ref": "integration.connections[2]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "clear",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"clear\", \"signal\": \"control_clear\"}",
      "signal": "control_clear",
      "signal_terms": [
        "control_clear"
      ],
      "source_ref": "integration.connections[3]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "gray_value",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"gray_value\", \"signal\": \"observed_gray_value\"}",
      "signal": "observed_gray_value",
      "signal_terms": [
        "observed_gray_value"
      ],
      "source_ref": "integration.connections[4]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "bin_value",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"bin_value\", \"signal\": \"observed_bin_value\"}",
      "signal": "observed_bin_value",
      "signal_terms": [
        "observed_bin_value"
      ],
      "source_ref": "integration.connections[5]"
    },
    {
      "instance": "",
      "machine_readable": true,
      "module": "gray_counter",
      "port": "done",
      "raw": "{\"module\": \"gray_counter\", \"port\": \"done\", \"signal\": \"observed_done\"}",
      "signal": "observed_done",
      "signal_terms": [
        "observed_done"
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
        "control_enable",
        "enable"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "input",
      "name": "enable",
      "source_ref": "io_list.interfaces[0].ports[0]",
      "width": "1"
    },
    {
      "aliases": [
        "clear",
        "control_clear"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "input",
      "name": "clear",
      "source_ref": "io_list.interfaces[0].ports[1]",
      "width": "1"
    },
    {
      "aliases": [
        "gray_value",
        "status_gray_value"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "output",
      "name": "gray_value",
      "source_ref": "io_list.interfaces[1].ports[0]",
      "width": "WIDTH"
    },
    {
      "aliases": [
        "bin_value",
        "status_bin_value"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "output",
      "name": "bin_value",
      "source_ref": "io_list.interfaces[1].ports[1]",
      "width": "WIDTH"
    },
    {
      "aliases": [
        "done",
        "status_done"
      ],
      "allow_constant": false,
      "allow_unused": false,
      "constant_value": "",
      "direction": "output",
      "name": "done",
      "source_ref": "io_list.interfaces[1].ports[2]",
      "width": "1"
    }
  ],
  "static_rtl_evidence": {
    "checked": 54,
    "missing": 13,
    "missing_tasks": [
      {
        "category": "function_model.output",
        "matched_count": 1,
   
... <truncated 339879 chars>

### gray_counter/rtl/rtl_authoring_status.md
# RTL Authoring Status: gray_counter

## Status

- Top: gray_counter
- Packets: 13
- LLM-actionable tasks: 14
- Human-locked tasks: 0
- Tool-evidence tasks: 2
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__gray_counter_core__fsm: rtl/authoring_packets/module__gray_counter_core__fsm.json (llm_open=12, human_locked=0)
- module__gray_counter_core__function_model_01: rtl/authoring_packets/module__gray_counter_core__function_model_01.json (llm_open=1, human_locked=0)
- rtl_gate_evidence_closure: rtl/authoring_packets/rtl_gate_evidence_closure.json (llm_open=1, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=2, next_tool=lint, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- Do not close static RTL evidence with comments: derive_rtl_todos.py strips comments before matching, so evidence_terms must be preserved in live lint-clean RTL identifiers/logic.
- Do not close static RTL evidence with evidence-only alias/dummy wires; the matched identifiers must participate in real RTL behavior.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.


Current packet JSON (rtl/authoring_packets/rtl_gate_tool_evidence.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 21,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "owner": {
      "file": "rtl/gray_counter.sv",
      "name": "gray_counter",
      "refs": [],
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
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "clk",
        "signal": "clk",
        "signal_terms": [
          "clk"
        ],
        "source_ref": "sub_modules[1].connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "rst_n",
        "signal": "rst_n",
        "signal_terms": [
          "rst_n"
        ],
        "source_ref": "sub_modules[1].connections[1]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "enable",
        "signal": "enable",
        "signal_terms": [
          "enable"
        ],
        "source_ref": "sub_modules[1].connections[2]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "clear",
        "signal": "clear",
        "signal_terms": [],
        "source_ref": "sub_modules[1].connections[3]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "gray_value",
        "signal": "gray_value",
        "signal_terms": [
          "gray_value"
        ],
        "source_ref": "sub_modules[1].connections[4]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "bin_value",
        "signal": "bin_value",
        "signal_terms": [
          "bin_value"
        ],
        "source_ref": "sub_modules[1].connections[5]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "done",
        "signal": "done",
        "signal_terms": [
          "done"
        ],
        "source_ref": "sub_modules[1].connections[6]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "clk",
        "signal": "soc_clk_or_tb_clk",
        "signal_terms": [
          "soc_clk_or_tb_clk"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "rst_n",
        "signal": "soc_rst_n_or_tb_rst_n",
        "signal_terms": [
          "soc_rst_n_or_tb_rst_n"
        ],
        "source_ref": "integration.connections[1]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "enable",
        "signal": "control_enable",
        "signal_terms": [
          "control_enable"
        ],
        "source_ref": "integration.connections[2]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "clear",
        "signal": "control_clear",
        "signal_terms": [
          "control_clear"
        ],
        "source_ref": "integration.connections[3]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "gray_value",
        "signal": "observed_gray_value",
        "signal_terms": [
          "observed_gray_value"
        ],
        "source_ref": "integration.connections[4]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "bin_value",
        "signal": "observed_bin_value",
        "signal_terms": [
          "observed_bin_value"
        ],
        "source_ref": "integration.connections[5]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "gray_counter",
        "port": "done",
        "signal": "observed_done",
        "signal_terms": [
          "observed_done"
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
          "control_enable",
          "enable"
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
          "clear",
          "control_clear"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "clear",
        "source_ref": "io_list.interfaces[0].ports[1]",
        "width": "1"
      },
      {
        "aliases": [
          "gray_value",
          "status_gray_value"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "gray_value",
        "source_ref": "io_list.interfaces[1].ports[0]",
        "width": "WIDTH"
      },
      {
        "aliases": [
          "bin_value",
          "status_bin_value"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "bin_value",
        "source_ref": "io_list.interfaces[1].ports[1]",
        "width": "WIDTH"
      },
      {
        "aliases": [
          "done",
          "status_done"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "done",
        "source_ref": "io_list.interfaces[1].ports[2]",
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
        "owner_module": "gray_counter_top",
        "reason": "DUT lint artifact is not clean.",
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "gray_counter_top",
        "reason": "15 required non-closure TODO(s) remain open.",
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
    ],
    "work_allowed": true
  },
  "ip": "gray_counter",
  "kind": "gate",
  "owner_file": "rtl/gray_counter.sv",
  "owner_module": "gray_counter",
  "packet_id": "rtl_gate_tool_evidence",
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
        "Primary implementation evidence is in rtl/gray_counter.sv"
      ],
      "detail": "RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.\nSSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.\nOwner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_authoring_provenance.json",
        "kind": "common_ai_agent_authoring",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0006",
      "owner_file": "rtl/gray_counter.sv",
      "owner_module": "gray_counter_top",
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
        "Primary implementation evidence is in rtl/gray_counter.sv"
      ],
      "detail": "Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.\nSSOT ref: quality_gates.rtl_gen.dut_compile.\nOwner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_compile.json",
        "kind": "dut_compile",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0017",
      "owner_file": "rtl/gray_counter.sv",
      "owner_module": "gray_counter_top",
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
        "Primary implementation evidence is in rtl/gray_counter.sv"
      ],
      "detail": "Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.\nSSOT ref: quality_gates.rtl_gen.dut_lint.\nOwner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "lint/dut_lint.json",
        "kind": "dut_lint",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0018",
      "owner_file": "rtl/gray_counter.sv",
      "owner_module": "gray_counter_top",
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
        "Primary implementation evidence is in rtl/gray_counter.sv"
      ],
      "detail": "rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.\nSSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.\nOwner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "dynamic_todo_closure",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0019",
      "owner_file": "rtl/gray_counter.sv",
      "owner_module": "gray_counter_top",
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
        "reason": "15 required non-closure TODO(s) remain open.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "d473b2610c40c79069346972679ffe8377525380178163598257ddce80b959b1",
  "top": "gray_counter",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/rtl_gate_tool_evidence.md):
# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: gray_counter
- Owner file: rtl/gray_counter.sv
- Task count: 4
- Required tasks: 4

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
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Tool-evidence blockers:
  - dut_lint: DUT lint artifact is not clean.
  - dynamic_todo_closure: 15 required non-closure TODO(s) remain open.
- Tool-evidence runbook:
  - dut_lint: stages=lint, dut_lint; artifact=gray_counter/lint/dut_lint.json
  - dynamic_todo_closure: stages=audit-rtl; artifact=gray_counter/rtl/rtl_todo_plan.json
- SSOT connection contracts:
  - gray_counter_core.clk <= clk (sub_modules[0].connections[0])
  - gray_counter_core.rst_n <= rst_n (sub_modules[0].connections[1])
  - gray_counter_core.enable <= enable (sub_modules[0].connections[2])
  - gray_counter_core.clear <= clear (sub_modules[0].connections[3])
  - gray_counter_core.gray_value <= gray_value (sub_modules[0].connections[4])
  - gray_counter_core.bin_value <= bin_value (sub_modules[0].connections[5])
  - gray_counter_core.done <= done (sub_modules[0].connections[6])
  - gray_counter.clk <= clk (sub_modules[1].connections[0])
  - gray_counter.rst_n <= rst_n (sub_modules[1].connections[1])
  - gray_counter.enable <= enable (sub_modules[1].connections[2])
  - gray_counter.clear <= clear (sub_modules[1].connections[3])
  - gray_counter.gray_value <= gray_value (sub_modules[1].connections[4])
- SSOT top IO contracts: 7

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.
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
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0017: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.
- Current reason: DUT-only compile artifact passed with zero errors, diagnostics, and style violations.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0018: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.
- Current reason: DUT lint artifact is not clean.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0019: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.
- Current reason: 15 required non-closure TODO(s) remain open.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure
