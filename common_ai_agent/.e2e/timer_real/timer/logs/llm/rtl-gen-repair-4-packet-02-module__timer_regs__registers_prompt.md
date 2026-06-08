RTL-GEN PACKET MODE for timer. Packet attempt 4.

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

Current packet: module__timer_regs__registers
kind: module
work queue: 3/4 active packets (22 closed packets skipped from 26 total)
batch limit: 4; deferred active packets after this batch: 0
owner_module: timer_regs
owner_file: rtl/timer_regs.sv

SSOT observable latency contract:
{
  "cycle_model.latency": {
    "irq_pulse": {
      "description": "irq remains asserted for exactly one pclk cycle at zero reload event.",
      "max_cycles": 1,
      "min_cycles": 1
    },
    "register_read": {
      "description": "Read data and pready are produced during the APB access phase.",
      "max_cycles": 1,
      "min_cycles": 0
    },
    "register_write": {
      "description": "Writes update architectural register state on the accepted APB access edge.",
      "max_cycles": 1,
      "min_cycles": 0
    },
    "timer_tick": {
      "description": "While enabled, one decrement or reload decision occurs per pclk cycle not occupied by reset.",
      "max_cycles": 1,
      "min_cycles": 1
    }
  },
  "cycle_model.pipeline": [
    {
      "action": "After reset deassertion, hold count_q=0, enable_q=0, irq=0 until APB write or enable tick.",
      "cycle": 0,
      "output_rules": [
        {
          "expr": "0",
          "name": "irq_reset_idle",
          "port": "irq",
          "width": 1
        }
      ],
      "stage": "RESET_RELEASED_IDLE"
    },
    {
      "action": "Decode LOAD, CTRL, STATUS, or unmapped address during APB access phase.",
      "cycle": 0,
      "output_rules": [
        {
          "expr": "psel == 1 and penable == 1",
          "name": "pready_apb_access",
          "port": "pready",
          "width": 1
        },
        {
          "expr": "psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)",
          "name": "pslverr_apb_access",
          "port": "pslverr",
          "width": 1
        }
      ],
      "stage": "APB_ACCESS"
    },
    {
      "action": "If enabled and count_q is nonzero, decrement count_q by one and keep irq low.",
      "cycle": 1,
      "output_rules": [
        {
          "expr": "0",
          "name": "irq_tick_decrement",
          "port": "irq",
          "width": 1
        }
      ],
      "stage": "TICK_DECREMENT"
    },
    {
      "action": "If enabled and count_q is zero, assert irq for this cycle and reload count_q from LOAD.",
      "cycle": 1,
      "output_rules": [
        {
          "expr": "enable_q == 1 and count_q == 0",
          "name": "irq_tick_reload",
          "port": "irq",
          "width": 1
        }
      ],
      "stage": "TICK_RELOAD_IRQ"
    },
    {
      "action": "If disabled, hold count_q and deassert irq.",
      "cycle": 1,
      "output_rules": [
        {
          "expr": "0",
          "name": "irq_disabled_hold",
          "port": "irq",
          "width": 1
        }
      ],
      "stage": "DISABLED_HOLD"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": "1",
  "timing.latency_budget": {
    "apb_read_cycles": {
      "max": 1,
      "min": 0
    },
    "apb_write_cycles": {
      "max": 1,
      "min": 0
    },
    "decrement_period_cycles": {
      "max": 1,
      "min": 1
    },
    "irq_pulse_width_cycles": {
      "max": 1,
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

Locked SSOT YAML excerpt (timer/yaml/timer.ssot.yaml):
top_module:
  name: timer
  file: rtl/timer.sv
  version: '1.0'
  type: peripheral
  description: Small APB-style programmable down-counter timer with periodic single-cycle interrupt pulse.
  reference_spec: timer/req/timer_requirements.md
  target:
    technology: generic
    clock_freq_mhz: 100
    area_um2: null
    power_mw: null
sub_modules:
- name: timer_regs
  file: rtl/timer_regs.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - registers.register_list
  - function_model.transactions.FM_APB_WRITE_LOAD
  - function_model.transactions.FM_APB_WRITE_CTRL
  - function_model.transactions.FM_APB_READ_STATUS
  - error_handling
  source_sections:
  - registers
  - function_model
  - error_handling
  register_refs:
  - registers.register_list.LOAD
  - registers.register_list.CTRL
  - registers.register_list.STATUS
  - registers.register_list
  function_model_refs:
  - function_model.transactions.FM_APB_WRITE_LOAD
  - function_model.transactions.FM_APB_WRITE_CTRL
  - function_model.transactions.FM_APB_READ_STATUS
  - function_model.transactions.FM_TICK_DECREMENT
  - function_model.transactions.FM_TICK_RELOAD_IRQ
  - function_model.transactions.FM_DISABLED_HOLD
  - function_model.transactions.FM_APB_UNMAPPED_ACCESS
  - function_model.state_variables
  - function_model.invariants
  description: APB register decode, LOAD/CTRL storage, STATUS read mux, and APB response behavior.
- name: timer_core
  file: rtl/timer_core.sv
  ownership: manifest
  ssot_gen: false
  implements:
  - function_model.state_variables
  - function_model.transactions.FM_TICK_DECREMENT
  - function_model.transactions.FM_TICK_RELOAD_IRQ
  - function_model.transactions.FM_DISABLED_HOLD
  - cycle_model.pipeline
  - interrupts.sources.TIMER_ZERO
  source_sections:
  - function_model
  - cycle_model
  - interrupts
  - dataflow
  - features
  - fsm
  - decomposition
  - test_requirements
  function_model_refs:
  - function_model.state_variables.count_q
  - function_model.state_variables.enable_q
  - function_model.state_variables.load_q
  - function_model.transactions.FM_TICK_DECREMENT
  - function_model.transactions.FM_TICK_RELOAD_IRQ
  - function_model.transactions.FM_DISABLED_HOLD
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.ordering
  - cycle_model.handshake_rules
  - cycle_model
  dataflow_refs:
  - dataflow.count_path
  - dataflow.irq_path
  - dataflow
  description: Timer decrement/reload datapath and single-cycle interrupt pulse behavior.
  feature_refs:
  - features
  fsm_refs:
  - fsm
  decomposition_refs:
  - decomposition
  test_refs:
  - test_requirements
- name: timer
  file: rtl/timer.sv
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
  - module: timer_regs
    file: rtl/timer_regs.sv
    responsibility: APB register decode, LOAD/CTRL storage, STATUS read mux, and APB response behavior.
    source_sections:
    - registers
    - function_model
    - error_handling
  - module: timer_core
    file: rtl/timer_core.sv
    responsibility: Timer decrement/reload datapath and single-cycle interrupt pulse behavior.
    source_sections:
    - function_model
    - cycle_model
    - interrupts
    - dataflow
  - module: timer
    file: rtl/timer.sv
    responsibility: Top-level integration module matching SSOT top_module
    source_sections: *id001
  integration_policy: Top-level wiring must be backed by integration.connections or sub_modules[].connections before signoff.
  source_refs:
  - sub_modules
  - function_model
  - cycle_model
  - integration
rtl_contract:
  role: APB-style timer peripheral with register file and down-counter core.
  reset_behavior:
    presetn_asserted_low: load_q=0, enable_q=0, count_q=0, irq=0, prdata=0, pready=0, pslverr=0
    after_deassertion: counter remains disabled and holds zero until software enables it.
  implementation_rules:
  - LOAD and CTRL writes are accepted on APB transfer_accept.
  - STATUS read returns current count_q and has no read side effects.
  - irq is a pulse, not a sticky level; it is high for exactly one pclk cycle per zero event.
  - pslverr is asserted only for accepted APB transfers to unmapped addresses.
  owner: ssot-gen
  type: ssot_derived_rule_contract
  transaction: FM_APB_WRITE_LOAD
  clock: pclk
  reset: presetn
  reset_active: low
  sample_condition: '1'
  input_map:
    paddr: paddr
    psel: psel
    penable: penable
    pwrite: pwrite
    pwdata: pwdata
  output_map:
    prdata: prdata
    pready: pready
    pslverr: pslverr
    irq: irq
  contract_invariants:
  - RTL-visible behavior implements the referenced function_model transaction.
  - Input sampling and output observation follow cycle_model handshake and latency rules.
  output_rules:
  - name: pready_write_load
    port: pready
    expr: '1'
    width: 1
    description: FunctionalModel output observable mapped to DUT output port.
  - name: pslverr_write_load
    port: pslverr
    expr: '0'
    width: 1
    description: FunctionalModel output observable mapped to DUT output port.
  - name: prdata_status
    port: prdata
    expr: count_q & 0xffffffff
    width: 32
    description: FunctionalModel output observable mapped to DUT output port.
  - name: irq_decrement
    port: irq
    expr: '0'
    width: 1
    description: FunctionalModel output observable mapped to DUT output port.
parameters:
- name: DATA_WIDTH
  default: 32
  type: int
  description: Width of LOAD and STATUS counter value.
  drives:
  - rtl/timer_regs.sv
  - rtl/timer_core.sv
- name: ADDR_WIDTH
  default: 4
  type: int
  description: APB byte address width for three 32-bit registers.
  drives:
  - rtl/timer.sv
  - rtl/timer_regs.sv
- name: CLOCK_FREQ_MHZ
  default: 100
  type: int
  description: Nominal starter target clock frequency.
  drives:
  - timer/sdc/timer.sdc
- name: RESET_POLARITY
  default: active_low
  type: enum
  values:
  - active_low
  - active_high
  description: Timer reset polarity; active-low reset is selected for this SSOT.
  drives:
  - rtl/timer.sv
  - rtl/timer_core.sv
  - rtl/timer_regs.sv
io_list:
  clock_domains:
  - name: pclk
    frequency_mhz: 100
    description: APB and timer counter clock domain.
    ports:
    - name: pclk
      width: 1
      direction: input
      description: APB/timer clock.
  resets:
  - name: presetn
    polarity: active_low
    sync_async: async_assert_sync_deassert
    description: Active-low reset. After reset deassertion the timer count is zero and disabled.
    ports:
    - name: presetn
      width: 1
      direction: input
      description: Active-low reset input.
  interfaces:
  - name: apb_slave
    type: APB-style
    role: slave
    description: 32-bit APB-style software register interface.
    protocol:
      setup_phase: psel == 1 and penable == 0
      access_phase: psel == 1 and penable == 1
      transfer_accept: psel == 1 and penable == 1 and pready == 1
      read_data_valid: psel == 1 and penable == 1 and pwrite == 0 and pready == 1
    ports:
    - name: paddr
      width: 4
      direction: input
      description: Byte address for LOAD, CTRL, and STATUS registers.
    - name: psel
      width: 1
      direction: input
      description: APB select.
    - name: penable
      width: 1
      direction: input
      description: APB enable/access phase indicator.
    - name: pwrite
      width: 1
      direction: input
      description: APB write control.
    - name: pwdata
      width: 32
      direction: input
      description: APB write data.
    - name: prdata
      width: 32
      direction: output
      description: APB read data.
    - name: pready
      width: 1
      direction: output
      description: APB ready; timer responds in the access phase without wait states.
    - name: pslverr
      width: 1
      direction: output
      description: APB error for unmapped register accesses.
    clock_domain: pclk
    reset_domain: presetn
  - name: interrupt
    type: custom
    role: source
    description: Single-cycle timer expiration pulse.
    ports:
    - name: irq
      width: 1
      direction: output
      description: Asserted for one pclk cycle when enabled counter reaches zero and reloads LOAD.
    clock_domain: pclk
    reset_domain: presetn
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
features:
- name: Programmable load register
  trigger: Software writes LOAD over APB-style interface.
  datapath: pwdata is captured into load_q on accepted write to LOAD.
  control: APB access decode.
  output: Future reload value for count_q.
- name: Enable-controlled down counter
  trigger: Software writes CTRL.ENABLE to 1.
  datapath: count_q decrements by one each pclk cycle while enable_q is 1 and count_q is nonzero.
  control: timer_core enabled tick path.
  output: STATUS reflects current count_q.
- name: Periodic irq pulse and reload
  trigger: Enabled tick observes count_q == 0.
  datapath: irq is asserted for one cycle and count_q is loaded from load_q.
  control: timer_core reload/irq path.
  output: Single-cycle irq pulse and continued counting from LOAD.
- name: Disable hold
  trigger: Software writes CTRL.ENABLE to 0.
  datapath: enable_q clears and count_q holds its current value.
  control: timer_core disabled path.
  output: No decrement and irq remains deasserted.
dataflow:
  register_write_path:
    source: APB pwdata on accepted writes.
    destination: LOAD.value or CTRL.ENABLE.
    sequence: psel/penable/pwrite decode -> register update -> function_model state mirror.
  count_path:
    source: count_q and load_q.
    sequence: enabled tick -> decrement if count_q>0 else reload from load_q -> STATUS.count mirror.
  irq_path:
    source: zero-detect on enabled count_q.
    sequence: enable_q && count_q==0 -> irq pulse one cycle -> irq deassert.
  read_path:
    source: STATUS.count or readable control registers.
    sequence: APB read decode -> prdata mux -> scoreboard comparison.
function_model:
  purpose: Executable expected-behavior source for cocotb/pyuvm scoreboard and FL-vs-RTL comparison.
  state_variables:
  - name: load_q
    source: registers.LOAD.value
    width: 32
    reset: 0
    description: Programmed reload value written by software.
  - name: enable_q
    source: registers.CTRL.ENABLE
    width: 1
    reset: 0
    description: Timer enable bit written by software.
  - name: count_q
    source: registers.STATUS.count
    width: 32
    reset: 0
    description: Current counter value exposed by STATUS.
  - name: irq_q
    width: 1
    reset: 0
    description: One-cycle interrupt pulse value for current cycle.
  transactions:
  - id: FM_APB_WRITE_LOAD
    name: write_load_register
    preconditions:
    - psel == 1 and penable == 1 and pwrite == 1 and paddr == 0
    inputs:
    - pwdata
    outputs:
    - pready == 1
    - pslverr == 0
    - name: pready_write_load
      port: pready
      expr: '1'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: pslverr_write_load
      port: pslverr
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: load_q
      expr: pwdata & 0xffffffff
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: irq_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: pready_write_load
      port: pready
      width: 1
      expr: '1'
    - name: pslverr_write_load
      port: pslverr
      width: 1
      expr: '0'
    state_updates:
    - name: load_q
      width: 32
      expr: pwdata & 0xffffffff
    - name: irq_q
      width: 1
      expr: '0'
    side_effects:
    - load_q becomes pwdata[31:0].
    - irq_q is deasserted for this APB write transaction.
    error_cases: []
  - id: FM_APB_WRITE_CTRL
    name: write_ctrl_enable
    preconditions:
    - psel == 1 and penable == 1 and pwrite == 1 and paddr == 4
    inputs:
    - pwdata
    outputs:
    - pready == 1
    - pslverr == 0
    - name: pready_write_ctrl
      port: pready
      expr: '1'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: pslverr_write_ctrl
      port: pslverr
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: enable_q
      expr: pwdata & 1
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: irq_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: pready_write_ctrl
      port: pready
      width: 1
      expr: '1'
    - name: pslverr_write_ctrl
      port: pslverr
      width: 1
      expr: '0'
    state_updates:
    - name: enable_q
      width: 1
      expr: pwdata & 1
    - name: irq_q
      width: 1
      expr: '0'
    side_effects:
    - enable_q becomes pwdata[0].
    - If ENABLE is written 0, count_q holds its current value on subsequent timer ticks.
    - irq_q is deasserted for this APB write transaction.
    error_cases: []
  - id: FM_APB_READ_STATUS
    name: read_status_current_count
    preconditions:
    - psel == 1 and penable == 1 and pwrite == 0 and paddr == 8
    inputs: []
    outputs:
    - prdata == count_q
    - pready == 1
    - pslverr == 0
    - name: prdata_status
      port: prdata
      expr: count_q & 0xffffffff
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: pready_read_status
      port: pready
      expr: '1'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: pslverr_read_status
      port: pslverr
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: irq_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: prdata_status
      port: prdata
      width: 32
      expr: count_q & 0xffffffff
    - name: pready_read_status
      port: pready
      width: 1
      expr: '1'
    - name: pslverr_read_status
      port: pslverr
      width: 1
      expr: '0'
    state_updates:
    - name: irq_q
      width: 1
      expr: '0'
    side_effects:
    - STATUS read has no count_q side effect.
    - irq_q is deasserted for this APB read transaction.
    error_cases: []
  - id: FM_TICK_DECREMENT
    name: enabled_decrement_nonzero
    preconditions:
    - psel == 0 and enable_q == 1 and count_q > 0
    inputs: []
    outputs:
    - irq == 0
    - name: irq_decrement
      port: irq
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: count_q
      expr: (count_q - 1) & 0xffffffff
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: irq_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: irq_decrement
      port: irq
      width: 1
      expr: '0'
    state_updates:
    - name: count_q
      width: 32
      expr: (count_q - 1) & 0xffffffff
    - name: irq_q
      width: 1
      expr: '0'
    side_effects:
    - count_q decrements by one modulo 32-bit range.
    - irq_q remains 0.
    error_cases: []
  - id: FM_TICK_RELOAD_IRQ
    name: enabled_zero_reload_and_irq_pulse
    preconditions:
    - psel == 0 and enable_q == 1 and count_q == 0
    inputs: []
    outputs:
    - irq == 1
    - name: irq_reload
      port: irq
      expr: '1'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: count_q
      expr: load_q & 0xffffffff
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: irq_q
      expr: '1'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: irq_reload
      port: irq
      width: 1
      expr: '1'
    state_updates:
    - name: count_q
      width: 32
      expr: load_q & 0xffffffff
    - name: irq_q
      width: 1
      expr: '1'
    side_effects:
    - irq_q asserts for this cycle.
    - count_q reloads from load_q.
    - Timer continues enabled unless CTRL.ENABLE is later cleared.
    error_cases: []
  - id: FM_DISABLED_HOLD
    name: disabled_hold_count
    preconditions:
    - psel == 0 and enable_q == 0
    inputs: []
    outputs:
    - irq == 0
    - name: irq_disabled
      port: irq
      expr: '0'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: count_q
      expr: count_q & 0xffffffff
      description: Mirrored from executable state_updates for SSOT validator completeness.
    - state: irq_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: irq_disabled
      port: irq
      width: 1
      expr: '0'
    state_updates:
    - name: count_q
      width: 32
      expr: count_q & 0xffffffff
    - name: irq_q
      width: 1
      expr: '0'
    side_effects:
    - count_q holds its current value while disabled.
    - irq_q remains 0.
    error_cases: []
  - id: FM_APB_UNMAPPED_ACCESS
    name: unmapped_apb_access_error
    preconditions:
    - psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)
    inputs:
    - paddr
    outputs:
    - pready == 1
    - pslverr == 1
    - name: pready_unmapped
      port: pready
      expr: '1'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - name: pslverr_unmapped
      port: pslverr
      expr: '1'
      description: Mirrored from executable output_rules for SSOT validator completeness.
    - state: irq_q
      expr: '0'
      description: Mirrored from executable state_updates for SSOT validator completeness.
    output_rules:
    - name: pready_unmapped
      port: pready
      width: 1
      expr: '1'
    - name: pslverr_unmapped
      port: pslverr
      width: 1
      expr: '1'
    state_updates:
    - name: irq_q
      width: 1
      expr: '0'
    side_effects:
    - No architectural register or counter state changes on unmapped access.
    error_cases:
    - condition: paddr != 0 and paddr != 4 and paddr != 8
      result: pslverr is asserted for the accepted transfer.
  invariants:
  - count_q >= 0 and count_q <= 0xffffffff
  - load_q >= 0 and load_q <= 0xffffffff
  - enable_q == 0 or enable_q == 1
  - irq_q == 0 or irq_q == 1
  - enable_q == 0 and psel == 0 implies irq_q == 0
  reference_model_hint: Build scoreboard expected events from transaction output_rules and state_updates; STATUS reads compare prdata against count_q and irq compares against irq_q.
  derived_signals:
  - name: apb_access
    expr: psel and penable
    width: 1
    description: APB access phase helper derived from psel and penable.
    source: repair_ssot_schema.apb_helper
  - name: apb_valid_write
    expr: psel and penable and pwrite
    width: 1
    description: APB write access helper derived from psel, penable, and pwrite.
    source: repair_ssot_schema.apb_helper
  - name: apb_valid_read
    expr: psel and penable and not pwrite
    width: 1
    description: APB read access helper derived from psel, penable, and pwrite.
    source: repair_ssot_schema.apb_helper
  - name: addr
    expr: paddr
    width: 4
    description: Register address helper derived from the APB paddr input.
    source: repair_ssot_schema.apb_helper
  - name: legal_addr
    expr: (addr == 0) or (addr == 4) or (addr == 8)
    width: 1
    description: APB legal address decode derived from registers.register_list offsets.
    source: repair_ssot_schema.apb_helper
  - name: wr_load
    expr: apb_valid_write and (addr == 0)
    width: 1
    description: APB write decode helper for register LOAD.
    source: repair_ssot_schema.apb_helper
  - name: rd_load
    expr: apb_valid_read and (addr == 0)
    width: 1
    description: APB read decode helper for register LOAD.
    source: repair_ssot_schema.apb_helper
  - name: wr_ctrl
    expr: apb_valid_write and (addr == 4)
    width: 1
    description: APB write decode helper for register CTRL.
    source: repair_ssot_schema.apb_helper
  - name: rd_ctrl
    expr: apb_valid_read and (addr == 4)
    width: 1
    description: APB read decode helper for register CTRL.
    source: repair_ssot_schema.apb_helper
  - name: wr_status
    expr: apb_valid_write and (addr == 8)
    width: 1
    description: APB write decode helper for register STATUS.
    source: repair_ssot_schema.apb_helper
  - name: rd_status
    expr: apb_valid_read and (addr == 8)
    width: 1
    description: APB read decode helper for register STATUS.
    source: repair_ssot_schema.apb_helper
  - name: read_mux
    expr: (0 if addr == 0 else (0 if addr == 4 else (0 if addr == 8 else 0)))
    width: 32
    description: APB read data mux derived from registers.register_list offsets and function_model state variables.
    source: repair_ssot_schema.apb_helper
cycle_model:
  purpose: Cycle and handshake contract for APB access, decrement, reload, and irq pulse timing.
  executable: python
  backend_policy: Deterministic cycle stepper using function_model state_updates and APB transfer predicates.
  cosim: true
  state_accumulating: true
  clock: pclk
  reset:
    signal: presetn
    assertion: presetn low asynchronously clears load_q, enable_q, count_q, irq_q, prdata, pready, and pslverr to 0.
    deassertion: counter is usable on the first rising edge after synchronized reset deassertion and remains disabled at count zero.
  latency:
    register_read:
      min_cycles: 0
      max_cycles: 1
      description: Read data and pready are produced during the APB access phase.
    register_write:
      min_cycles: 0
      max_cycles: 1
      description: Writes update architectural register state on the accepted APB access edge.
    timer_tick:
      min_cycles: 1
      max_cycles: 1
      description: While enabled, one decrement or reload decision occurs per pclk cycle not occupied by reset.
    irq_pulse:
      min_cycles: 1
      max_cycles: 1
      description: irq remains asserted for exactly one pclk cycle at zero reload event.
  handshake_rules:
  - signal: pready
    rule: pready is asserted for an APB access when psel == 1 and penable == 1.
    expr: psel == 1 and penable == 1
  - signal: pslverr
    rule: pslverr is asserted only for accepted APB accesses with paddr not equal to LOAD, CTRL, or STATUS offsets.
    expr: psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)
  - signal: prdata
    rule: STATUS read returns current count_q during accepted read access.
    expr: psel == 1 and penable == 1 and pwrite == 0 and paddr == 8
  - signal: irq
    rule: irq is high for exactly the reload cycle when enable_q == 1 and count_q == 0.
    expr: enable_q == 1 and count_q == 0
  pipeline:
  - stage: RESET_RELEASED_IDLE
    cycle: 0
    action: After reset deassertion, hold count_q=0, enable_q=0, irq=0 until APB write or enable tick.
    output_rules:
    - name: irq_reset_idle
      port: irq
      width: 1
      expr: '0'
  - stage: APB_ACCESS
    cycle: 0
    action: Decode LOAD, CTRL, STATUS, or unmapped address during APB access phase.
    output_rules:
    - name: pready_apb_access
      port: pready
      width: 1
      expr: psel == 1 and penable == 1
    - name: pslverr_apb_access
      port: pslverr
      width: 1
      expr: psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)
  - stage: TICK_DECREMENT
    cycle: 1
    action: If enabled and count_q is nonzero, decrement count_q by one and keep irq low.
    output_rules:
    - name: irq_tick_decrement
      port: irq
      width: 1
      expr: '0'
  - stage: TICK_RELOAD_IRQ
    cycle: 1
    action: If enabled and count_q is zero, assert irq for this cycle and reload count_q from LOAD.
    output_rules:
    - name: irq_tick_reload
      port: irq
      width: 1
      expr: enable_q == 1 and count_q == 0
  - stage: DISABLED_HOLD
    cycle: 1
    action: If disabled, hold count_q and deassert irq.
    output_rules:
    - name: irq_disabled_hold
      port: irq
      width: 1
      expr: '0'
  ordering:
  - APB writes update LOAD or CTRL on the accepted access edge.
  - A CTRL write with ENABLE=0 prevents subsequent decrement/reload ticks and holds count_q.
  - STATUS read observes the current count_q value for the access cycle and has no read side effects.
  - irq assertion and count_q reload occur on the same timer tick when enable_q == 1 and count_q == 0.
  - irq deasserts on the cycle following a reload event unless another reload condition is again true.
  backpressure:
  - No APB wait states are introduced by the timer; pready follows accepted access phase.
  observability:
  - STATUS read, irq pulse, and internal count_q are the primary scoreboard observation points.
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
  - name: pclk
    frequency_mhz: 100
    description: Single clock domain for APB and timer core.
  reset_scheme:
    signal: presetn
    polarity: active_low
    type: async_assert_sync_deassert
cdc_requirements:
  crossings: []
  synchronizers: []
  note: Single pclk domain; no CDC required.
rdc_requirements:
  crossings: []
  synchronizers: []
  note: Single reset domain; no reset domain crossing required.
registers:
  config:
    register_width: 32
    addr_width: 4
    byte_addressable: true
    bus: APB-style
  register_list:
  - name: LOAD
    offset: 0
    width: 32
    access: rw
    reset: 0
    category: control
    description: Software-programmed reload value.
    fields:
    - name: value
      bits:
      - 31
      - 0
      access: rw
      reset: 0
      description: Value reloaded into STATUS/current count when timer expires.
      write_effect: &id002
        write: Updates load_q only; does not directly modify current count_q unless a simultaneous reload tick occurs per cycle_model ordering.
        read: Returns load_q.
    side_effects: *id002
  - name: CTRL
    offset: 4
    width: 32
    access: rw
    reset: 0
    category: control
    description: Timer enable control register.
    fields:
    - name: ENABLE
      bits:
      - 0
      - 0
      access: rw
      reset: 0
      description: 1 enables decrement/reload operation; 0 stops and holds the counter.
      write_effect: &id003
        write: Bit 0 updates enable_q; clearing ENABLE stops and holds count_q.
        read: Returns ENABLE in bit 0 and zeros in reserved bits.
    - name: RESERVED
      bits:
      - 31
      - 1
      access: ro
      reset: 0
      description: Reserved bits read as zero and ignore writes.
    side_effects: *id003
  - name: STATUS
    offset: 8
    width: 32
    access: ro
    reset: 0
    category: status
    description: Read-only current counter value.
    fields:
    - name: count
      bits:
      - 31
      - 0
      access: ro
      reset: 0
      description: Current down-counter value count_q.
    side_effects:
      write: Ignored for mapped STATUS address; no state change.
      read: Returns current count_q with no side effects.
memory:
  instances: []
  note: Timer uses registers only; no SRAM, FIFO, or RAM instances are required.
interrupts:
  sources:
  - name: TIMER_ZERO
    bit: 0
    type: pulse
    status_reg: none
    enable_reg: CTRL.ENABLE
    clear: self_clearing_next_cycle
    description: Single-cycle irq pulse when enabled counter reaches zero and reloads LOAD.
  output:
    signal: irq
    polarity: active_high
    type: pulse
fsm:
  timer_control:
    states:
    - DISABLED
    - ENABLED_COUNT
    - RELOAD_IRQ
    transitions:
    - from: DISABLED
      to: ENABLED_COUNT
      condition: enable_q == 1
    - from: ENABLED_COUNT
      to: RELOAD_IRQ
      condition: enable_q == 1 and count_q == 0
    - from: RELOAD_IRQ
      to: ENABLED_COUNT
      condition: enable_q == 1
    - from: ENABLED_COUNT
      to: DISABLED
      condition: enable_q == 0
    - from: RELOAD_IRQ
      to: DISABLED
      condition: enable_q == 0
    reset_state: DISABLED
    description: Conceptual FSM for timer enable/count/reload behavior; implementation may be simple conditional logic.
timing:
  target_clocks:
  - name: pclk
    frequency_mhz: 100
    period_ns: 10.0
    duty_cycle: 50
  latency_budget:
    apb_read_cycles:
      min: 0
      max: 1
    apb_write_cycles:
      min: 0
      max: 1
    decrement_period_cycles:
      min: 1
      max: 1
    irq_pulse_width_cycles:
      min: 1
      max: 1
  throughput:
    timer_tick: One decrement/reload decision per pclk cycle while enabled.
    apb: One accepted access per APB access phase.
  sta_expectations:
    setup_wns_ns_min: 0.0
    hold_wns_ns_min: 0.0
    required_reports:
    - sta/out/timing.rpt
    - sta/out/wns.json
power:
  domains:
  - name: main
    supplies:
    - vdd
    - vss
    clock: pclk
    description: Single always-on timer power domain.
  power_states:
  - name: true
    domain: main
    behavior: Registers retain and timer operates when presetn is deasserted.
  - name: RESET
    domain: main
    behavior: presetn asserted clears state to reset values.
  clock_gating:
    required: false
    note: Starter timer may rely on enable_q to suppress counter state updates while disabled.
  upf_required: false
security:
  classification: low
  assets:
  - name: timer_configuration
    description: LOAD and CTRL software-visible configuration.
    protection: APB address decode only; no privilege model specified in requirements.
  - name: interrupt_integrity
    description: irq pulse timing must match counter zero events.
    protection: Deterministic reload/decrement logic and scoreboard checks.
  threat_model:
  - threat: Unmapped APB access corrupts timer state.
    mitigation: pslverr asserted and no state update.
  - threat: Reserved CTRL bits alter behavior.
    mitigation: Reserved bits are ignored and read as zero.
  - threat: Spurious or sticky interrupt.
    mitigation: irq pulse generated only by enable_q == 1 and count_q == 0 and deasserted next cycle.
  privilege_model: System-level access control is owned by the integrating bus/firewall unless explicitly declared here.
error_handling:
  error_sources:
  - id: UNMAPPED_APB_ACCESS
    condition: psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)
    architectural_effect: Status/error reporting follows the SSOT error policy
  - id: STATUS_WRITE_IGNORED
    condition: psel == 1 and penable == 1 and pwrite == 1 and paddr == 8
    architectural_effect: Status/error reporting follows the SSOT error policy
  - id: RESERVED_CTRL_BITS_WRITE
    condition: psel == 1 and penable == 1 and pwrite == 1 and paddr == 4 and (pwdata & 0xfffffffe) != 0
    architectural_effect: Status/error reporting follows the SSOT error policy
  propagation:
    pslverr: Asserted for unmapped APB accesses only.
    irq: Not used for APB error propagation; irq is timer expiration only.
  recovery:
  - Software may retry valid APB accesses after an unmapped access.
  - Reset clears LOAD, CTRL.ENABLE, STATUS/count, and irq to zero.
debug_observability:
  waveform_must_probe:
  - pclk
  - presetn
  - psel
  - penable
  - pwrite
  - paddr
  - pwdata
  - prdata
  - pready
  - pslverr
  - irq
  - load_q
  - enable_q
  - count_q
  trace_events:
  - id: TRACE_RESET_RELEASE
    trigger: presetn rises/deasserts
    payload:
    - count_q
    - enable_q
  - id: TRACE_LOAD_WRITE
    trigger: psel == 1 and penable == 1 and pwrite == 1 and paddr == 0
    payload:
    - pwdata
    - load_q
  - id: TRACE_ENABLE_WRITE
    trigger: psel == 1 and penable == 1 and pwrite == 1 and paddr == 4
    payload:
    - pwdata
    - enable_q
  - id: TRACE_STATUS_READ
    trigger: psel == 1 and penable == 1 and pwrite == 0 and paddr == 8
    payload:
    - prdata
    - count_q
  - id: TRACE_IRQ_PULSE
    trigger: irq == 1
    payload:
    - count_q
    - load_q
  status_outputs:
  - status/debug signals declared in io_list or registers
integration:
  bus_attachment:
    bus: APB-style peripheral bus
    base_address: assigned_by_parent
    address_size_bytes: 16
    clock: pclk
    reset: presetn
    irq_connection: irq to parent interrupt controller or top-level interrupt input.
  dependencies:
  - Parent must provide pclk and presetn.
  - Parent APB master must follow setup/access phase semantics.
  - Parent address map must reserve at least 0x10 bytes for timer registers.
  connections:
  - module: timer_regs
    port: pclk
    signal: pclk
  - module: timer_regs
    port: presetn
    signal: presetn
  - module: timer_regs
    port: paddr
    signal: paddr
  - module: timer_regs
    port: psel
    signal: psel
  - module: timer_regs
    port: penable
    signal: penable
  - module: timer_regs
    port: pwrite
    signal: pwrite
  - module: timer_regs
    port: pwdata
    signal: pwdata
  - module: timer_regs
    port: prdata
    signal: prdata
  - module: timer_regs
    port: pready
    signal: pready
  - module: timer_regs
    port: pslverr
    signal: pslverr
  - module: timer_regs
    port: load_q
    signal: load_q
  - module: timer_regs
    port: enable_q
    signal: enable_q
  - module: timer_regs
    port: count_q
    signal: count_q
  - module: timer_core
    port: pclk
    signal: pclk
  - module: timer_core
    port: presetn
    signal: presetn
  - module: timer_core
    port: load_q
    signal: load_q
  - module: timer_core
    port: enable_q
    signal: enable_q
  - module: timer_core
    port: count_q
    signal: count_q
  - module: timer_core
    port: irq
    signal: irq
  connection_contract_status: missing machine-readable module wiring; child RTL drafts may proceed from owner packets, but top integration/signoff must stay blocked until SSOT authors integration.connections or sub_modules[].connections with module/port/signal records
  integration_notes:
  - Integrator must connect every declared io_list port and honor timing/reset assumptions.
dft:
  scan_required: false
  controllability:
  - APB writes provide controllability for LOAD and CTRL.ENABLE.
  - presetn provides deterministic reset of all architectural state.
  observability:
  - STATUS read observes count_q.
  - irq output observes zero/reload events.
  - waveform probes expose load_q, enable_q, and count_q in simulation.
  mbist_required: false
synthesis:
  dialect: systemverilog_2012
  constraints:
  - timer/sdc/timer.sdc declares pclk at 100 MHz.
  - Asynchronous active-low reset presetn must be constrained according to project reset policy.
  - No generated clocks or CDC constraints are required.
  required_outputs:
  - synthesized netlist
  - timing report
  - area report
  - power estimate
  - constraint check report
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
  cts:
    buf_list: []
  routing:
    signal_layers:
      min: met1
      max: met5
    drc_waivers: []
  cts_buf_list:
  - sky130_fd_sc_hd__clkbuf_4
  - sky130_fd_sc_hd__clkbuf_8
coding_rules:
  verilog_style: systemverilog_2012
  file_extension: .sv
  parameter_header: rtl/timer_param.vh
  conventions:
  - Use ANSI SystemVerilog ports with logic types.
  - Use nonblocking assignments in sequential always blocks.
  - Use blocking assignments in combinational always blocks.
  - Active-low reset must clear all architectural state to numeric reset values.
  - No latches; every combinational branch assigns all outputs.
  - Keep irq as a registered or otherwise cycle-stable one-clock pulse matching cycle_model.
  lint_waivers: []
reuse_modules: []
custom:
  run_mode: starter
  assumptions:
  - APB-style interface uses pclk/presetn and responds without wait states.
  - Address offsets are LOAD=0x0, CTRL=0x4, STATUS=0x8 for a compact three-register timer map.
  - Unmapped APB access asserts pslverr and does not change timer state.
dir_structure:
  template_dirs:
    rtl: templates/rtl/
    sim: templates/sim/
  output_dirs:
    rtl: rtl/
    sim: sim/
    tb: tb/
    tc: tc/
    firmware: firmware/
    docs: doc/
  yaml_dir: yaml/
  generators_dir: generators/
filelist:
  headers:
  - rtl/timer_param.vh
  rtl:
  - rtl/timer.sv
  - rtl/timer_regs.sv
  - rtl/timer_core.sv
  sim:
  - sim/tb_top.sv
  - sim/timer_model.py
  firmware:
  - firmware/timer_regs.h
  docs:
  - doc/timer_mas.md
  - doc/register_map.md
  tb:
  - tb/cocotb/test_timer.py
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
    - err
... <truncated 16641 chars>

Base rtl-gen contract:
Prepare rtl-gen for timer using only timer/yaml/timer.ssot.yaml and timer/rtl/rtl_todo_plan.json, timer/rtl/rtl_authoring_plan.json, and packets under timer/rtl/authoring_packets. Return exactly one JSON object and nothing else. Success schema: {"files":[{"path":"timer/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"},{"path":"timer/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"},{"path":"timer/list/timer.f","kind":"filelist","content":"<filelist>"}]}. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=53834821b27363b8d16e5991dc812b9380099860db84ca19bd61cb5db03fa76e. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "reason": "22 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      }
    ],
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "timer",
        "reason": "23 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 19,
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
    "open_required_todos": 24,
    "pass_allowed": false,
    "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
    "stop_conditions": [
      "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
      "Do not claim rtl-gen PASS while pass_allowed is false.",
      "Do not sign off top integration while required connection contracts are missing."
    ],
    "tool_evidence_plan": [
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
        "reason": "23 required non-closure TODO(s) remain open.",
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
      "json": "rtl/authoring_packets/module__timer_regs__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 14,
      "open_required_count": 14,
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "packet_id": "module__timer_regs__function_model_02",
      "required_count": 48,
      "status_counts": {
        "open": 14,
        "pass": 34
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_regs__function_model_01.json",
      "kind": "module",
      "llm_actionable_open_count": 7,
      "open_required_count": 7,
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "packet_id": "module__timer_regs__function_model_01",
      "required_count": 48,
      "status_counts": {
        "open": 7,
        "pass": 41
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_regs__registers.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "packet_id": "module__timer_regs__registers",
      "required_count": 7,
      "status_counts": {
        "open": 1,
        "pass": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
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
      "open_required_count": 1,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 1,
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_regs__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "packet_id": "module__timer_regs__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_regs__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "packet_id": "module__timer_regs__error_handling",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_regs__function_model_03.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "packet_id": "module__timer_regs__function_model_03",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_regs__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "packet_id": "module__timer_regs__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_core.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__cycle_model",
      "required_count": 19,
      "status_counts": {
        "pass": 19
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_core.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__features.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_core.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__features",
      "required_count": 4,
      "status_counts": {
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_core.sv",
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
      "owner_file": "rtl/timer_core.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__function_model",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__interrupts.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_core.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__interrupts",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_core.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__test_requirements",
      "required_count": 12,
      "status_counts": {
        "pass": 12
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer_core__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer_core.sv",
      "owner_module": "timer_core",
      "packet_id": "module__timer_core__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer__integration.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer__integration",
      "required_count": 22,
      "status_counts": {
        "pass": 22
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer__io_list",
      "required_count": 11,
      "status_counts": {
        "pass": 11
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer__parameters",
      "required_count": 4,
      "status_counts": {
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer__rtl_flow.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer__rtl_flow",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer__security.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer__security",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer__synthesis.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer__synthesis",
      "required_count": 6,
      "status_counts": {
        "pass": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__timer__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "module__timer__workflow_todo",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/timer.sv",
      "owner_module": "timer",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 4,
      "status_counts": {
        "pass": 4
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
    "human_locked_packets": 0,
    "human_locked_tasks": 0,
    "llm_actionable_packets": 4,
    "llm_actionable_tasks": 23,
    "max_packet_required_tasks": 48,
    "module_packets": 23,
    "next_llm_packets": [
      "module__timer_regs__function_model_02",
      "module__timer_regs__function_model_01",
      "module__timer_regs__registers",
      "rtl_gate_evidence_closure"
    ],
    "packet_task_limit": 48,
    "packets": 26,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 226,
    "sliced_module_packets": 23,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 1,
    "total_tasks": 226,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "53834821b27363b8d16e5991dc812b9380099860db84ca19bd61cb5db03fa76e",
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

Current owner RTL file (rtl/timer_regs.sv):
module timer_regs #(
    parameter integer DATA_WIDTH = 32,
    parameter integer ADDR_WIDTH = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic [ADDR_WIDTH-1:0] paddr,
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [DATA_WIDTH-1:0] pwdata,
    input  logic [DATA_WIDTH-1:0] count_q,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    output logic [DATA_WIDTH-1:0] load_q,
    output logic                  enable_q
);
    localparam [ADDR_WIDTH-1:0] ADDR_LOAD   = 4'h0;
    localparam [ADDR_WIDTH-1:0] ADDR_CTRL   = 4'h4;
    localparam [ADDR_WIDTH-1:0] ADDR_STATUS = 4'h8;

    logic apb_access;
    logic apb_valid_write;
    logic apb_valid_read;
    logic legal_addr;
    logic wr_load;
    logic rd_load;
    logic wr_ctrl;
    logic rd_ctrl;
    logic wr_status;
    logic rd_status;
    logic pready_unmapped;
    logic pslverr_unmapped;
    logic pready_access_rule;
    logic pslverr_access_rule;
    logic [DATA_WIDTH-1:0] read_mux;
    logic [DATA_WIDTH-1:0] prdata_access_rule;
    logic [DATA_WIDTH-1:0] ctrl_read_data;
    logic [DATA_WIDTH-1:0] ctrl_reserved_mask;

    assign apb_access      = psel & penable;
    assign apb_valid_write = apb_access & pwrite;
    assign apb_valid_read  = apb_access & (~pwrite);
    assign legal_addr      = (paddr == ADDR_LOAD) | (paddr == ADDR_CTRL) | (paddr == ADDR_STATUS);
    assign wr_load         = apb_valid_write & (paddr == ADDR_LOAD);
    assign rd_load         = apb_valid_read  & (paddr == ADDR_LOAD);
    assign wr_ctrl         = apb_valid_write & (paddr == ADDR_CTRL);
    assign rd_ctrl         = apb_valid_read  & (paddr == ADDR_CTRL);
    assign wr_status       = apb_valid_write & (paddr == ADDR_STATUS);
    assign rd_status       = apb_valid_read  & (paddr == ADDR_STATUS);

    // Unmapped APB accesses complete in the access phase with pslverr asserted
    // and no LOAD/CTRL state update; legal STATUS writes are ignored, not errors.
    assign pready_unmapped      = apb_access & (~legal_addr);
    assign pslverr_unmapped     = apb_access & (~legal_addr);
    assign pready_access_rule   = apb_access | pready_unmapped;
    assign pslverr_access_rule  = pslverr_unmapped;

    // CTRL reserved bits are masked on readback and ignored on write; only bit 0
    // updates enable_q, preserving the SSOT RESERVED field read-as-zero behavior.
    assign ctrl_reserved_mask   = {{(DATA_WIDTH-1){1'b0}}, 1'b1};
    assign ctrl_read_data       = {{(DATA_WIDTH-1){1'b0}}, enable_q} & ctrl_reserved_mask;

    always @(*) begin
        read_mux = {DATA_WIDTH{1'b0}};
        if (rd_load) begin
            read_mux = load_q;
        end else if (rd_ctrl) begin
            read_mux = ctrl_read_data;
        end else if (rd_status) begin
            read_mux = count_q;
        end else begin
            read_mux = {DATA_WIDTH{1'b0}};
        end
    end

    always @(*) begin
        prdata_access_rule = read_mux;
        pready  = pready_access_rule;
        pslverr = pslverr_access_rule;
        prdata  = prdata_access_rule;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            load_q   <= {DATA_WIDTH{1'b0}};
            enable_q <= 1'b0;
        end else begin
            if (wr_load) begin
                load_q <= pwdata;
            end

            if (wr_ctrl) begin
                enable_q <= pwdata[0];
            end

            if (wr_status) begin
                enable_q <= enable_q;
            end
        end
    end

endmodule


Current RTL module interface digest (all manifest RTL files):
### rtl/timer_regs.sv
module timer_regs #(
    parameter integer DATA_WIDTH = 32,
    parameter integer ADDR_WIDTH = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic [ADDR_WIDTH-1:0] paddr,
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [DATA_WIDTH-1:0] pwdata,
    input  logic [DATA_WIDTH-1:0] count_q,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    output logic [DATA_WIDTH-1:0] load_q,
    output logic                  enable_q
);

### rtl/timer_core.sv
module timer_core #(
    parameter integer DATA_WIDTH = 32
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic [DATA_WIDTH-1:0] load_q,
    input  logic                  enable_q,
    output logic [DATA_WIDTH-1:0] count_q,
    output logic                  irq
);

### rtl/timer.sv
module timer #(
    parameter integer DATA_WIDTH = 32,
    parameter integer ADDR_WIDTH = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic [ADDR_WIDTH-1:0] paddr,
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [DATA_WIDTH-1:0] pwdata,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    output logic                  irq
);

Current mandatory lint repair directives:
<none>

Current RTL gate audit digest:
{
  "compile": {
    "diagnostics": 0,
    "errors": 0,
    "passed": true,
    "present": true,
    "returncode": 0,
    "source": "timer/rtl/rtl_compile.json",
    "style_violation_details": [],
    "style_violations": 0
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
    "open_required_todos": 24,
    "orphan_tasks": 0,
    "static_missing": 22,
    "status": "fail"
  },
  "lint": {
    "diagnostics": [],
    "errors": 0,
    "passed": true,
    "present": true,
    "repair_hints": [],
    "returncode": 0,
    "source": "timer/lint/dut_lint.json",
    "style_violation_count": 0,
    "suppression_violation_count": 0,
    "warnings": 0
  },
  "manifest_hierarchy_issues": [],
  "manifest_signal_flow_issues": [],
  "open_required_tasks": [
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "22 static-evidence-required task(s) still lack DUT RTL evidence.",
      "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
      "task_id": "RTL-0007"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "23 required non-closure TODO(s) remain open.",
      "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
      "task_id": "RTL-0019"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.state_variables.irq_q",
      "task_id": "RTL-0042"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_APB_WRITE_LOAD.outputs.irq_q",
      "task_id": "RTL-0051"
    },
    {
      "category": "function_model.state_update",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_APB_WRITE_LOAD.state_updates.irq_q",
      "task_id": "RTL-0055"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_APB_WRITE_CTRL.outputs.irq_q",
      "task_id": "RTL-0066"
    },
    {
      "category": "function_model.state_update",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_APB_WRITE_CTRL.state_updates.irq_q",
      "task_id": "RTL-0070"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_APB_READ_STATUS.outputs.irq_q",
      "task_id": "RTL-0082"
    },
    {
      "category": "function_model.state_update",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_APB_READ_STATUS.state_updates.irq_q",
      "task_id": "RTL-0086"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_TICK_DECREMENT.outputs.irq_decrement",
      "task_id": "RTL-0092"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_TICK_DECREMENT.outputs.irq_q",
      "task_id": "RTL-0094"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_TICK_DECREMENT.output_rules.irq_decrement",
      "task_id": "RTL-0095"
    },
    {
      "category": "function_model.state_update",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_TICK_DECREMENT.state_updates.irq_q",
      "task_id": "RTL-0097"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_reload",
      "task_id": "RTL-0103"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_q",
      "task_id": "RTL-0105"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_TICK_RELOAD_IRQ.output_rules.irq_reload",
      "task_id": "RTL-0106"
    },
    {
      "category": "function_model.state_update",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.irq_q",
      "task_id": "RTL-0108"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_DISABLED_HOLD.outputs.irq_disabled",
      "task_id": "RTL-0115"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_DISABLED_HOLD.outputs.irq_q",
      "task_id": "RTL-0117"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_DISABLED_HOLD.output_rules.irq_disabled",
      "task_id": "RTL-0118"
    },
    {
      "category": "function_model.state_update",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_DISABLED_HOLD.state_updates.irq_q",
      "task_id": "RTL-0120"
    },
    {
      "category": "function_model.output",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.irq_q",
      "task_id": "RTL-0130"
    },
    {
      "category": "function_model.state_update",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_APB_UNMAPPED_ACCESS.state_updates.irq_q",
      "task_id": "RTL-0133"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.LOAD.fields.value",
      "task_id": "RTL-0161"
    }
  ],
  "source": "timer/rtl/rtl_todo_plan.json",
  "static_missing_tasks": [
    {
      "category": "function_model.state_variable",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.state_variables.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0042"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_APB_WRITE_LOAD.outputs.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0051"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_APB_WRITE_LOAD.state_updates.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0055"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_APB_WRITE_CTRL.outputs.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0066"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_APB_WRITE_CTRL.state_updates.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0070"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_APB_READ_STATUS.outputs.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0082"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_APB_READ_STATUS.state_updates.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0086"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "decrement",
        "irq",
        "irq_decrement"
      ],
      "source_ref": "function_model.transactions.FM_TICK_DECREMENT.outputs.irq_decrement",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0092"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_TICK_DECREMENT.outputs.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0094"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 2,
      "required_terms": [
        "decrement",
        "irq",
        "irq_decrement"
      ],
      "source_ref": "function_model.transactions.FM_TICK_DECREMENT.output_rules.irq_decrement",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0095"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_TICK_DECREMENT.state_updates.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0097"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_reload",
        "reload"
      ],
      "source_ref": "function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_reload",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0103"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_TICK_RELOAD_IRQ.outputs.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0105"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 2,
      "required_terms": [
        "irq",
        "irq_reload",
        "reload"
      ],
      "source_ref": "function_model.transactions.FM_TICK_RELOAD_IRQ.output_rules.irq_reload",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0106"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_TICK_RELOAD_IRQ.state_updates.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0108"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "disabled",
        "irq",
        "irq_disabled"
      ],
      "source_ref": "function_model.transactions.FM_DISABLED_HOLD.outputs.irq_disabled",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0115"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_DISABLED_HOLD.outputs.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0117"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 2,
      "required_terms": [
        "disabled",
        "irq",
        "irq_disabled"
      ],
      "source_ref": "function_model.transactions.FM_DISABLED_HOLD.output_rules.irq_disabled",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0118"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_DISABLED_HOLD.state_updates.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0120"
    },
    {
      "category": "function_model.output",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_APB_UNMAPPED_ACCESS.outputs.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0130"
    },
    {
      "category": "function_model.state_update",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "irq",
        "irq_q"
      ],
      "source_ref": "function_model.transactions.FM_APB_UNMAPPED_ACCESS.state_updates.irq_q",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0133"
    },
    {
      "category": "registers.field",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/timer_regs.sv",
      "required_match_count": 1,
      "required_terms": [
        "value"
      ],
      "source_ref": "registers.register_list.LOAD.fields.value",
      "source_scope": "rtl/timer_regs.sv",
      "task_id": "RTL-0161"
    }
  ]
}

Current RTL file snapshots for gate/tool-evidence repair:
<included only for gate/tool-evidence packets>

Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__timer_regs__registers.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 19,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 7,
      "enabled": true,
      "index": 4,
      "key": "registers",
      "module_task_count": 110,
      "rule": "Owner module timer_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "registers",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/timer_regs.sv",
      "name": "timer_regs",
      "refs": [
        "error_handling",
        "function_model",
        "function_model.invariants",
        "function_model.state_variables",
        "function_model.transactions.FM_APB_READ_STATUS",
        "function_model.transactions.FM_APB_UNMAPPED_ACCESS",
        "function_model.transactions.FM_APB_WRITE_CTRL",
        "function_model.transactions.FM_APB_WRITE_LOAD",
        "function_model.transactions.FM_DISABLED_HOLD",
        "function_model.transactions.FM_TICK_DECREMENT",
        "function_model.transactions.FM_TICK_RELOAD_IRQ",
        "registers",
        "registers.register_list",
        "registers.register_list.CTRL",
        "registers.register_list.LOAD",
        "registers.register_list.STATUS"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/timer_regs.sv",
        "name": "timer_regs",
        "wiring_only": false
      },
      {
        "file": "rtl/timer_core.sv",
        "name": "timer_core",
        "wiring_only": false
      },
      {
        "file": "rtl/timer.sv",
        "name": "timer",
        "wiring_only": true
      }
    ],
    "quality_profile": "standard",
    "reference_profile": null,
    "ssot_connection_contracts": [
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "pclk",
        "signal": "pclk",
        "signal_terms": [
          "pclk"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "presetn",
        "signal": "presetn",
        "signal_terms": [
          "presetn"
        ],
        "source_ref": "integration.connections[1]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "paddr",
        "signal": "paddr",
        "signal_terms": [
          "paddr"
        ],
        "source_ref": "integration.connections[2]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "psel",
        "signal": "psel",
        "signal_terms": [
          "psel"
        ],
        "source_ref": "integration.connections[3]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "penable",
        "signal": "penable",
        "signal_terms": [
          "penable"
        ],
        "source_ref": "integration.connections[4]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "pwrite",
        "signal": "pwrite",
        "signal_terms": [
          "pwrite"
        ],
        "source_ref": "integration.connections[5]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "pwdata",
        "signal": "pwdata",
        "signal_terms": [
          "pwdata"
        ],
        "source_ref": "integration.connections[6]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "prdata",
        "signal": "prdata",
        "signal_terms": [
          "prdata"
        ],
        "source_ref": "integration.connections[7]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "pready",
        "signal": "pready",
        "signal_terms": [
          "pready"
        ],
        "source_ref": "integration.connections[8]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "pslverr",
        "signal": "pslverr",
        "signal_terms": [
          "pslverr"
        ],
        "source_ref": "integration.connections[9]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "load_q",
        "signal": "load_q",
        "signal_terms": [
          "load_q"
        ],
        "source_ref": "integration.connections[10]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "enable_q",
        "signal": "enable_q",
        "signal_terms": [
          "enable_q"
        ],
        "source_ref": "integration.connections[11]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "timer_regs",
        "port": "count_q",
        "signal": "count_q",
        "signal_terms": [
          "count_q"
        ],
        "source_ref": "integration.connections[12]"
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
    "llm_actionable_open_count": 1,
    "open_required_count": 1,
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
  "kind": "module",
  "owner_file": "rtl/timer_regs.sv",
  "owner_module": "timer_regs",
  "packet_id": "module__timer_regs__registers",
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
      "registers.field": 4,
      "registers.register": 3
    },
    "module_slice": {
      "count": 7,
      "enabled": true,
      "index": 4,
      "key": "registers",
      "module_task_count": 110,
      "rule": "Owner module timer_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "registers",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 1,
    "required_count": 7,
    "source_refs": [
      "registers.register_list.LOAD",
      "registers.register_list.LOAD.fields.value",
      "registers.register_list.CTRL",
      "registers.register_list.CTRL.fields.ENABLE",
      "registers.register_list.CTRL.fields.RESERVED",
      "registers.register_list.STATUS",
      "registers.register_list.STATUS.fields.count"
    ],
    "status_counts": {
      "open": 1,
      "pass": 6
    },
    "task_count": 7
  },
  "tasks": [
    {
      "category": "registers.register",
      "content": "Implement CSR/register LOAD",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.LOAD",
        "Primary implementation evidence is in rtl/timer_regs.sv",
        "LOAD width matches SSOT value 32",
        "LOAD reset behavior matches SSOT value 0",
        "LOAD access policy rw is implemented without read/write shortcuts",
        "LOAD decode uses SSOT address/offset 0"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.LOAD.\nOwner: timer_regs in rtl/timer_regs.sv via registers.register_list.LOAD.\nSSOT item context: name=LOAD; width=32; reset=0; access=rw; offset=0.",
      "evidence_terms": [
        "LOAD"
      ],
      "id": "RTL-0160",
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.LOAD",
      "ssot_context": {
        "access": "rw",
        "name": "LOAD",
        "offset": "0",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.LOAD"
      ],
      "static_evidence": {
        "fallback_scope": "",
        "matched_count": 1,
        "matched_terms": [
          "LOAD"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "LOAD"
        ],
        "source_scope": "rtl/timer_regs.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 9,
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
      "category": "registers.field",
      "content": "Implement field LOAD.value",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.LOAD.fields.value",
        "Primary implementation evidence is in rtl/timer_regs.sv",
        "value reset behavior matches SSOT value 0",
        "value access policy rw is implemented without read/write shortcuts",
        "value readback returns implemented RTL state when readable",
        "value write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.LOAD.fields.value.\nOwner: timer_regs in rtl/timer_regs.sv via registers.register_list.LOAD.\nSSOT item context: name=value; reset=0; access=rw.",
      "evidence_terms": [
        "value"
      ],
      "id": "RTL-0161",
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.LOAD.fields.value",
      "ssot_context": {
        "access": "rw",
        "name": "value",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.LOAD.fields.value"
      ],
      "static_evidence": {
        "fallback_scope": "",
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "value"
        ],
        "source_scope": "rtl/timer_regs.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 11,
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
      "category": "registers.register",
      "content": "Implement CSR/register CTRL",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.CTRL",
        "Primary implementation evidence is in rtl/timer_regs.sv",
        "CTRL width matches SSOT value 32",
        "CTRL reset behavior matches SSOT value 0",
        "CTRL access policy rw is implemented without read/write shortcuts",
        "CTRL decode uses SSOT address/offset 4"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.CTRL.\nOwner: timer_regs in rtl/timer_regs.sv via registers.register_list.CTRL.\nSSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=4.",
      "evidence_terms": [
        "CTRL"
      ],
      "id": "RTL-0162",
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CTRL",
      "ssot_context": {
        "access": "rw",
        "name": "CTRL",
        "offset": "4",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.CTRL"
      ],
      "static_evidence": {
        "fallback_scope": "",
        "matched_count": 1,
        "matched_terms": [
          "CTRL"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "CTRL"
        ],
        "source_scope": "rtl/timer_regs.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 9,
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
      "category": "registers.field",
      "content": "Implement field CTRL.ENABLE",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.CTRL.fields.ENABLE",
        "Primary implementation evidence is in rtl/timer_regs.sv",
        "ENABLE reset behavior matches SSOT value 0",
        "ENABLE access policy rw is implemented without read/write shortcuts",
        "ENABLE readback returns implemented RTL state when readable",
        "ENABLE write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.CTRL.fields.ENABLE.\nOwner: timer_regs in rtl/timer_regs.sv via registers.register_list.CTRL.\nSSOT item context: name=ENABLE; reset=0; access=rw.",
      "evidence_terms": [
        "ENABLE"
      ],
      "id": "RTL-0163",
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CTRL.fields.ENABLE",
      "ssot_context": {
        "access": "rw",
        "name": "ENABLE",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.CTRL.fields.ENABLE"
      ],
      "static_evidence": {
        "fallback_scope": "",
        "matched_count": 1,
        "matched_terms": [
          "ENABLE"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "ENABLE"
        ],
        "source_scope": "rtl/timer_regs.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 11,
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
      "category": "registers.field",
      "content": "Implement field CTRL.RESERVED",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.CTRL.fields.RESERVED",
        "Primary implementation evidence is in rtl/timer_regs.sv",
        "RESERVED reset behavior matches SSOT value 0",
        "RESERVED access policy ro is implemented without read/write shortcuts",
        "RESERVED readback returns implemented RTL state when readable",
        "RESERVED write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.CTRL.fields.RESERVED.\nOwner: timer_regs in rtl/timer_regs.sv via registers.register_list.CTRL.\nSSOT item context: name=RESERVED; reset=0; access=ro.",
      "evidence_terms": [
        "GPIO_MASK",
        "RESERVED",
        "mask"
      ],
      "id": "RTL-0164",
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CTRL.fields.RESERVED",
      "ssot_context": {
        "access": "ro",
        "name": "RESERVED",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.CTRL.fields.RESERVED"
      ],
      "static_evidence": {
        "fallback_scope": "",
        "matched_count": 2,
        "matched_terms": [
          "RESERVED",
          "mask"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "GPIO_MASK",
          "RESERVED",
          "mask"
        ],
        "source_scope": "rtl/timer_regs.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 11,
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
      "category": "registers.register",
      "content": "Implement CSR/register STATUS",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.STATUS",
        "Primary implementation evidence is in rtl/timer_regs.sv",
        "STATUS width matches SSOT value 32",
        "STATUS reset behavior matches SSOT value 0",
        "STATUS access policy ro is implemented without read/write shortcuts",
        "STATUS decode uses SSOT address/offset 8"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.STATUS.\nOwner: timer_regs in rtl/timer_regs.sv via registers.register_list.STATUS.\nSSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=8.",
      "evidence_terms": [
        "STATUS"
      ],
      "id": "RTL-0165",
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.STATUS",
      "ssot_context": {
        "access": "ro",
        "name": "STATUS",
        "offset": "8",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.STATUS"
      ],
      "static_evidence": {
        "fallback_scope": "",
        "matched_count": 1,
        "matched_terms": [
          "STATUS"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "STATUS"
        ],
        "source_scope": "rtl/timer_regs.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 9,
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
      "category": "registers.field",
      "content": "Implement field STATUS.count",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.STATUS.fields.count",
        "Primary implementation evidence is in rtl/timer_regs.sv",
        "count reset behavior matches SSOT value 0",
        "count access policy ro is implemented without read/write shortcuts",
        "count readback returns implemented RTL state when readable",
        "count write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.STATUS.fields.count.\nOwner: timer_regs in rtl/timer_regs.sv via registers.register_list.STATUS.\nSSOT item context: name=count; reset=0; access=ro.",
      "evidence_terms": [
        "count"
      ],
      "id": "RTL-0166",
      "owner_file": "rtl/timer_regs.sv",
      "owner_module": "timer_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.STATUS.fields.count",
      "ssot_context": {
        "access": "ro",
        "name": "count",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.STATUS.fields.count"
      ],
      "static_evidence": {
        "fallback_scope": "",
        "matched_count": 1,
        "matched_terms": [
          "count"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "count"
        ],
        "source_scope": "rtl/timer_regs.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 11,
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
    }
  ],
  "todo_plan_sha256": "53834821b27363b8d16e5991dc812b9380099860db84ca19bd61cb5db03fa76e",
  "top": "timer",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__timer_regs__registers.md):
# RTL Authoring Packet: module__timer_regs__registers

- Kind: module
- Owner module: timer_regs
- Owner file: rtl/timer_regs.sv
- Task count: 7
- Required tasks: 7

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
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: error_handling, function_model, function_model.invariants, function_model.state_variables, function_model.transactions.FM_APB_READ_STATUS, function_model.transactions.FM_APB_UNMAPPED_ACCESS, function_model.transactions.FM_APB_WRITE_CTRL, function_model.transactions.FM_APB_WRITE_LOAD, function_model.transactions.FM_DISABLED_HOLD, function_model.transactions.FM_TICK_DECREMENT, function_model.transactions.FM_TICK_RELOAD_IRQ, registers, registers.register_list, registers.register_list.CTRL, registers.register_list.LOAD, registers.register_list.STATUS
- Module slice: 4/7 section=registers task_limit=48
- Slice rule: Owner module timer_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_regs.pclk <= pclk (integration.connections[0])
  - timer_regs.presetn <= presetn (integration.connections[1])
  - timer_regs.paddr <= paddr (integration.connections[2])
  - timer_regs.psel <= psel (integration.connections[3])
  - timer_regs.penable <= penable (integration.connections[4])
  - timer_regs.pwrite <= pwrite (integration.connections[5])
  - timer_regs.pwdata <= pwdata (integration.connections[6])
  - timer_regs.prdata <= prdata (integration.connections[7])
  - timer_regs.pready <= pready (integration.connections[8])
  - timer_regs.pslverr <= pslverr (integration.connections[9])
  - timer_regs.load_q <= load_q (integration.connections[10])
  - timer_regs.enable_q <= enable_q (integration.connections[11])

## Tasks

### RTL-0160: Implement CSR/register LOAD

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.LOAD
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.LOAD.
Owner: timer_regs in rtl/timer_regs.sv via registers.register_list.LOAD.
SSOT item context: name=LOAD; width=32; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.LOAD
  - Primary implementation evidence is in rtl/timer_regs.sv
  - LOAD width matches SSOT value 32
  - LOAD reset behavior matches SSOT value 0
  - LOAD access policy rw is implemented without read/write shortcuts
  - LOAD decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.LOAD

### RTL-0161: Implement field LOAD.value

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.LOAD.fields.value
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.LOAD.fields.value.
Owner: timer_regs in rtl/timer_regs.sv via registers.register_list.LOAD.
SSOT item context: name=value; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.LOAD.fields.value
  - Primary implementation evidence is in rtl/timer_regs.sv
  - value reset behavior matches SSOT value 0
  - value access policy rw is implemented without read/write shortcuts
  - value readback returns implemented RTL state when readable
  - value write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.LOAD.fields.value

### RTL-0162: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: timer_regs in rtl/timer_regs.sv via registers.register_list.CTRL.
SSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/timer_regs.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 0
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.CTRL

### RTL-0163: Implement field CTRL.ENABLE

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.ENABLE
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.ENABLE.
Owner: timer_regs in rtl/timer_regs.sv via registers.register_list.CTRL.
SSOT item context: name=ENABLE; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.ENABLE
  - Primary implementation evidence is in rtl/timer_regs.sv
  - ENABLE reset behavior matches SSOT value 0
  - ENABLE access policy rw is implemented without read/write shortcuts
  - ENABLE readback returns implemented RTL state when readable
  - ENABLE write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.ENABLE

### RTL-0164: Implement field CTRL.RESERVED

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.RESERVED
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.RESERVED.
Owner: timer_regs in rtl/timer_regs.sv via registers.register_list.CTRL.
SSOT item context: name=RESERVED; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.RESERVED
  - Primary implementation evidence is in rtl/timer_regs.sv
  - RESERVED reset behavior matches SSOT value 0
  - RESERVED access policy ro is implemented without read/write shortcuts
  - RESERVED readback returns implemented RTL state when readable
  - RESERVED write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.RESERVED

### RTL-0165: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: timer_regs in rtl/timer_regs.sv via registers.register_list.STATUS.
SSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/timer_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.STATUS

### RTL-0166: Implement field STATUS.count

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.count.
Owner: timer_regs in rtl/timer_regs.sv via registers.register_list.STATUS.
SSOT item context: name=count; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.count
  - Primary implementation evidence is in rtl/timer_regs.sv
  - count reset behavior matches SSOT value 0
  - count access policy ro is implemented without read/write shortcuts
  - count readback returns implemented RTL state when readable
  - count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.count
