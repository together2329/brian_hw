RTL-GEN PACKET MODE for clkdiv. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "clkdiv/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "clkdiv/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "clkdiv/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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

Current packet: module__clkdiv_regs
kind: module
work queue: 1/1 active packets (2 closed packets skipped from 10 total)
batch limit: 1; deferred active packets after this batch: 7
owner_module: clkdiv_regs
owner_file: rtl/clkdiv_regs.sv

SSOT observable latency contract:
{
  "cycle_model.latency": {
    "divisor_update": {
      "description": "A new divisor applies at the next terminal count boundary.",
      "max_cycles": null,
      "min_cycles": 1
    },
    "output_toggle": {
      "description": "clk_o toggles after active_divisor input clock rising edges while enabled.",
      "max_cycles": null,
      "min_cycles": 1
    },
    "register_read": {
      "description": "APB access completes with pready in the access phase.",
      "max_cycles": 1,
      "min_cycles": 1
    },
    "register_write": {
      "description": "APB writes update register storage on completing access phase.",
      "max_cycles": 1,
      "min_cycles": 1
    }
  },
  "cycle_model.pipeline": [
    {
      "action": "Capture paddr/pwrite context when psel=1 and penable=0.",
      "cycle": 0,
      "stage": "S0_APB_SETUP"
    },
    {
      "action": "Complete APB read/write; update CTRL/DIVISOR/INTCLR effects.",
      "cycle": 1,
      "stage": "S1_APB_ACCESS"
    },
    {
      "action": "Increment counter while counter < active_divisor-1.",
      "cycle": "each enabled clk_i edge",
      "stage": "S2_COUNT"
    },
    {
      "action": "Reset counter, toggle clk_o, load pending_divisor, set locked and optional irq_pending.",
      "cycle": "terminal edge",
      "stage": "S3_TERMINAL"
    },
    {
      "action": "Force counter and clk_o low and clear locked.",
      "cycle": "first edge after enable=0",
      "stage": "S4_DISABLE"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": "state and outputs update on clk_i rising edge after reset deassertion; APB writes sample on completing access phase.",
  "timing.latency_budget": {
    "divisor_update_cycles": {
      "max": null,
      "measured_from": "DIVISOR write",
      "measured_to": "next terminal boundary",
      "min": 1
    },
    "interrupt_latency_cycles": {
      "max": 1,
      "measured_from": "terminal_event",
      "measured_to": "irq_o assertion",
      "min": 0
    },
    "register_access_cycles": {
      "max": 1,
      "measured_from": "psel && penable",
      "measured_to": "pready",
      "min": 1
    }
  }
}

Locked SSOT YAML excerpt (clkdiv/yaml/clkdiv.ssot.yaml):
top_module:
  name: "clkdiv"
  file: "rtl/clkdiv.sv"
  version: "1.0"
  type: "peripheral"
  description: "Programmable integer clock divider with APB4 control, glitchless enable, status, and optional terminal interrupt."
  reference_spec: "user-defined"
  target:
    technology: "generic"
    clock_freq_mhz: 100
    area_um2: null
    power_mw: null
sub_modules:
  - name: "clkdiv_regs"
    file: "rtl/clkdiv_regs.sv"
    ownership: "manifest"
    ssot_gen: true
    implements: ["registers.register_list", "io_list.interfaces.apb_slave", "interrupts", "error_handling"]
    source_sections: ["registers", "io_list", "interrupts", "error_handling"]
    register_refs: ["registers.register_list.CTRL", "registers.register_list.DIVISOR", "registers.register_list.STATUS", "registers.register_list.INTCLR"]
    ssot_refs: ["io_list.interfaces.apb_slave"]
    description: "APB register decode and software-visible control/status block."
    connections:
      - { module: "clkdiv_regs", port: "clk_i", signal: "clk_i" }
      - { module: "clkdiv_regs", port: "rst_ni", signal: "rst_ni" }
      - { module: "clkdiv_regs", port: "enable_o", signal: "enable" }
      - { module: "clkdiv_regs", port: "divisor_o", signal: "active_divisor" }
      - { module: "clkdiv_regs", port: "irq_pending_i", signal: "irq_pending" }
  - name: "clkdiv_core"
    file: "rtl/clkdiv_core.sv"
    ownership: "manifest"
    ssot_gen: false
    implements: ["function_model.transactions.FM_DIVIDE", "cycle_model.pipeline", "fsm.divider_fsm", "dataflow"]
    source_sections: ["function_model", "cycle_model", "fsm", "dataflow"]
    function_model_refs: ["function_model.transactions.FM_DIVIDE", "function_model.state_variables"]
    cycle_model_refs: ["cycle_model.handshake_rules", "cycle_model.pipeline", "cycle_model.performance"]
    dataflow_refs: ["dataflow.control_path", "dataflow.clock_path"]
    fsm_refs: ["fsm.divider_fsm"]
    description: "Divider counter, output toggle, glitchless divisor update, and terminal event generation."
    connections:
      - { module: "clkdiv_core", port: "clk_i", signal: "clk_i" }
      - { module: "clkdiv_core", port: "rst_ni", signal: "rst_ni" }
      - { module: "clkdiv_core", port: "enable_i", signal: "enable" }
      - { module: "clkdiv_core", port: "divisor_i", signal: "active_divisor" }
      - { module: "clkdiv_core", port: "clk_o", signal: "clk_o" }
      - { module: "clkdiv_core", port: "locked_o", signal: "locked_o" }
      - { module: "clkdiv_core", port: "terminal_event_o", signal: "terminal_event" }
decomposition:
  units:
    - { id: "apb_decode", kind: "control/status", source_refs: ["registers.register_list", "io_list.interfaces.apb_slave"], rtl_candidates: ["clkdiv_regs"], verification_impact: ["test_requirements.scenarios.SC_APB"] }
    - { id: "divider_execute", kind: "datapath/control", source_refs: ["function_model.transactions.FM_DIVIDE", "cycle_model.pipeline", "fsm.divider_fsm"], rtl_candidates: ["clkdiv_core"], verification_impact: ["test_requirements.coverage_goals"] }
rtl_contract:
  transaction: "FM_DIVIDE"
  sample_condition: "state and outputs update on clk_i rising edge after reset deassertion; APB writes sample on completing access phase."
  input_map:
    clock: "clk_i"
    reset: "rst_ni"
    enable: "registers.CTRL.enable"
    divisor: "registers.DIVISOR.divisor"
    clear_irq: "registers.INTCLR.clear_irq"
  output_map:
    divided_clock: "clk_o"
    lock_indicator: "locked_o"
    interrupt: "irq_o"
    register_read_data: "prdata"
    apb_error: "pslverr"
  state_updates:
    - { name: "counter", reset: 0, expr: "enable ? (terminal_count ? 0 : counter + 1) : 0" }
    - { name: "clk_state", reset: 0, expr: "enable && terminal_count ? ~clk_state : (enable ? clk_state : 0)" }
    - { name: "active_divisor", reset: 2, expr: "terminal_count ? pending_divisor : active_divisor" }
    - { name: "irq_pending", reset: 0, expr: "set on terminal_event when irq_enable; clear on INTCLR.clear_irq W1C" }
parameters:
  - name: "DIV_WIDTH"
    default: 16
    type: int
    description: "Width of programmable divisor register; legal divisor values are 1..2^DIV_WIDTH-1."
    drives: ["rtl/clkdiv_core.sv", "rtl/clkdiv_regs.sv"]
  - name: "RESET_POLARITY"
    default: "active_low"
    type: enum
    values: ["active_low", "active_high"]
    description: "Reset polarity for rst_ni."
    drives: ["ALL .sv files"]
  - name: "CLOCK_FREQ_MHZ"
    default: 100
    type: int
    description: "Nominal input clock frequency."
    drives: ["sdc/clkdiv.sdc", "test_requirements"]
io_list:
  clock_domains:
    - name: "clk_i"
      frequency_mhz: 100
      description: "Input/reference clock to be divided."
      ports:
        - { name: "clk_i", width: 1, direction: "input", description: "Reference input clock" }
  resets:
    - name: "rst_ni"
      polarity: "active_low"
      sync_async: "async_assert_sync_deassert"
      description: "Active-low reset for register and divider state."
      ports:
        - { name: "rst_ni", width: 1, direction: "input", description: "Active-low reset" }
  interfaces:
    - name: "apb_slave"
      type: "APB4"
      role: "slave"
      clock_domain: "clk_i"
      reset_domain: "rst_ni"
      description: "Control/status register access interface."
      protocol:
        setup_phase: "psel=1 and penable=0 captures address/control."
        access_phase: "psel=1 and penable=1 completes in one cycle with pready=1."
        read_rule: "prdata is valid in the completing access phase for reads."
        write_rule: "pwdata and pstrb are sampled in the completing access phase for writes."
        error_rule: "pslverr asserts with pready for unsupported address or illegal write access."
      ports:
        - { name: "paddr", width: 8, direction: "input", description: "Byte address" }
        - { name: "psel", width: 1, direction: "input", description: "APB select" }
        - { name: "penable", width: 1, direction: "input", description: "APB enable" }
        - { name: "pwrite", width: 1, direction: "input", description: "APB write qualifier" }
        - { name: "pwdata", width: 32, direction: "input", description: "APB write data" }
        - { name: "pstrb", width: 4, direction: "input", description: "APB byte strobes" }
        - { name: "prdata", width: 32, direction: "output", description: "APB read data" }
        - { name: "pready", width: 1, direction: "output", description: "APB ready" }
        - { name: "pslverr", width: 1, direction: "output", description: "APB error" }
    - name: "divided_clock"
      type: "custom"
      role: "source"
      clock_domain: "clk_i"
      reset_domain: "rst_ni"
      description: "Generated divided clock and status outputs."
      protocol:
        output_timing: "clk_o changes only on rising edges of clk_i after reset deassertion."
        enable_rule: "When enable is clear, clk_o is driven low and locked_o is 0."
        divisor_rule: "A pending divisor write takes effect only when the divider counter returns to zero, avoiding runt pulses."
        irq_rule: "irq_o is active high when enabled terminal-toggle event status is pending."
      ports:
        - { name: "clk_o", width: 1, direction: "output", description: "Divided output clock" }
        - { name: "locked_o", width: 1, direction: "output", description: "Divider active/stable indicator" }
        - { name: "irq_o", width: 1, direction: "output", description: "Optional terminal event interrupt" }
features:
  - name: "Programmable divide"
    trigger: "CTRL.enable set and DIVISOR configured through APB"
    datapath: "Counter counts clk_i edges up to divisor-1, then toggles clk_o and reloads."
    control: "DISABLED, RUNNING_LOW, RUNNING_HIGH"
    output: "clk_o toggles at a rate determined by DIVISOR."
  - name: "Glitchless divisor update"
    trigger: "Software writes DIVISOR while divider is enabled"
    datapath: "Write updates pending divisor; active divisor updates only at terminal count/reload boundary."
    control: "RUNNING_LOW and RUNNING_HIGH retain output polarity until terminal boundary."
    output: "No runt pulse or asynchronous clk_o edge occurs due to divisor write."
  - name: "Terminal event interrupt"
    trigger: "Counter reaches terminal count and CTRL.irq_enable=1"
    datapath: "terminal_event sets STATUS.irq_pending; INTCLR.clear_irq clears pending status."
    control: "RUNNING_LOW/RUNNING_HIGH terminal transitions"
    output: "irq_o asserted while interrupt is enabled and pending."
dataflow:
  control_path:
    source: "APB writes to CTRL and DIVISOR"
    staging: "DIVISOR writes update pending_divisor before active_divisor changes."
    destination: "clkdiv_core enable_i and divisor_i inputs"
    sequence: "APB write -> register storage -> core boundary sampling -> counter reload boundary"
  clock_path:
    source: "clk_i rising edges"
    transform: "counter increments until active_divisor-1 and then toggles clk_o"
    destination: "clk_o output"
    sequence: "clk_i edge -> counter update -> optional terminal event -> clk_o toggle"
  status_path:
    source: "core running/locked/terminal_event signals"
    destination: "STATUS fields, locked_o, irq_o"
    sequence: "core event -> status latch -> APB read/IRQ output"
function_model:
  purpose: "Behavioral contract for programmable clock division independent of APB cycle timing."
  state_variables:
    - { name: "enable", source: "registers.CTRL.enable", reset: 0, description: "Divider enable state" }
    - { name: "pending_divisor", source: "registers.DIVISOR.divisor", reset: 2, description: "Software-programmed divisor, with write value 0 coerced to 1" }
    - { name: "active_divisor", source: "clkdiv_core.active_divisor", reset: 2, description: "Divisor currently used by the counter" }
    - { name: "counter", source: "clkdiv_core.counter", reset: 0, description: "Counts input clock cycles toward terminal count" }
    - { name: "clk_state", source: "clk_o", reset: 0, description: "Current divided clock output state" }
    - { name: "irq_pending", source: "registers.STATUS.irq_pending", reset: 0, description: "Sticky terminal event interrupt pending bit" }
  transactions:
    - id: "FM_DIVIDE"
      name: "integer_clock_divide"
      preconditions:
        - "rst_ni is deasserted"
        - "CTRL.enable == 1"
        - "active_divisor >= 1"
      inputs:
        - "clk_i rising edge"
        - "active_divisor"
        - "CTRL.irq_enable"
      outputs:
        - "clk_o toggles exactly when counter reaches active_divisor-1"
        - "locked_o is 1 after the first terminal reload while enabled"
        - "irq_o is 1 when irq_pending and CTRL.irq_enable are both 1"
      output_rules:
        - { name: "divided_clock", expr: "((~clk_state) & 1) if terminal_count else clk_state", width: 1, port: "clk_o" }
        - { name: "lock_indicator", expr: "1 if enable and first_reload_seen else 0", width: 1, port: "locked_o" }
        - { name: "interrupt", expr: "1 if irq_pending and irq_enable else 0", width: 1, port: "irq_o" }
      side_effects:
        - "If counter == active_divisor-1, counter resets to 0 and clk_state toggles."
        - "If counter != active_divisor-1, counter increments by one and clk_state is stable."
        - "At terminal count, active_divisor loads pending_divisor for the next half-period."
        - "At terminal count, irq_pending is set when CTRL.irq_enable=1."
        - "When enable=0, counter=0, clk_state=0, locked_o=0."
      error_cases:
        - { condition: "APB write to DIVISOR with value 0", result: "pending_divisor is coerced to 1; no pslverr" }
        - { condition: "APB access to unsupported address", result: "pslverr asserted for the access and state is unchanged" }
  invariants:
    - "clk_o changes only on clk_i rising edges while rst_ni is deasserted."
    - "DIVISOR writes do not directly toggle clk_o."
    - "Reserved register fields read as zero and ignore writes."
    - "irq_pending remains set until INTCLR.clear_irq is written as 1."
  reference_model_hint: "tb-gen should model counter, active_divisor, pending_divisor, clk_state, locked, and irq_pending in Python and compare outputs cycle-by-cycle."
cycle_model:
  purpose: "Cycle and handshake contract for APB register access and divider output timing."
  executable: "pymtl3"
  backend_policy: "Use a clocked PyMTL3 model as cycle reference and direct Python smoke checks for divider timing."
  clock: "clk_i"
  reset:
    assertion: "rst_ni low asynchronously clears registers, counter, clk_o, locked_o, and irq_pending to reset values."
    deassertion: "State is usable on the first rising edge after synchronized deassertion."
  latency:
    register_read: { min_cycles: 1, max_cycles: 1, description: "APB access completes with pready in the access phase." }
    register_write: { min_cycles: 1, max_cycles: 1, description: "APB writes update register storage on completing access phase." }
    divisor_update: { min_cycles: 1, max_cycles: null, description: "A new divisor applies at the next terminal count boundary." }
    output_toggle: { min_cycles: 1, max_cycles: null, description: "clk_o toggles after active_divisor input clock rising edges while enabled." }
  handshake_rules:
    - { signal: "pready", rule: "pready is asserted for every selected APB access phase; no wait states in baseline." }
    - { signal: "pslverr", rule: "pslverr is asserted only with pready for unsupported address or illegal access." }
    - { signal: "prdata", rule: "prdata is stable in the APB read completing access phase." }
    - { signal: "clk_o", rule: "clk_o toggles only at terminal count on clk_i rising edge and is held low when disabled." }
    - { signal: "irq_o", rule: "irq_o is combinational/registered reflection of irq_pending && irq_enable and deasserts after INTCLR clear." }
  pipeline:
    - { stage: "S0_APB_SETUP", cycle: 0, action: "Capture paddr/pwrite context when psel=1 and penable=0." }
    - { stage: "S1_APB_ACCESS", cycle: 1, action: "Complete APB read/write; update CTRL/DIVISOR/INTCLR effects." }
    - { stage: "S2_COUNT", cycle: "each enabled clk_i edge", action: "Increment counter while counter < active_divisor-1." }
    - { stage: "S3_TERMINAL", cycle: "terminal edge", action: "Reset counter, toggle clk_o, load pending_divisor, set locked and optional irq_pending." }
    - { stage: "S4_DISABLE", cycle: "first edge after enable=0", action: "Force counter and clk_o low and clear locked." }
  ordering:
    - "APB DIVISOR writes update pending_divisor before the next core reload boundary."
    - "active_divisor changes only in S3_TERMINAL or reset."
    - "INTCLR.clear_irq write clears irq_pending no later than the completing APB access edge."
  backpressure:
    - "No backpressure exists on divided_clock outputs; APB baseline has no wait states."
  performance:
    frequency_mhz: 100
    throughput: { sustained_register_accesses_per_cycle: 0.5, condition: "APB requires setup and access phases" }
    divider_range: { min_divisor: 1, max_divisor: 65535, description: "DIV_WIDTH=16 baseline" }
    output_rate: { half_period_input_cycles: "active_divisor", full_period_input_cycles: "2*active_divisor" }
  observability:
    - "Every function_model transaction maps to S2_COUNT/S3_TERMINAL and a test_requirements scenario."
clock_reset_domains:
  domains:
    - { name: "clk_i", frequency_mhz: 100, description: "Input/reference clock and APB/control clock" }
  reset_scheme:
    signal: "rst_ni"
    polarity: "active_low"
    type: "async_assert_sync_deassert"
cdc_requirements:
  crossings: []
  synchronizers: []
  note: "Single clk_i domain; clk_o is a generated output and not a separate internal control domain in this IP revision."
rdc_requirements:
  crossings: []
  synchronizers: []
  note: "No reset domain crossings; all state uses rst_ni."
registers:
  config:
    register_width: 32
    addr_width: 8
    byte_addressable: true
  bit_order: "lsb0"
  bits_format: "[msb, lsb]"
  reserved_field_policy:
    read_value: 0
    write_effect: "ignore"
    rtl_requirement: "Reserved fields read as zero and writes have no effect."
  register_list:
    - name: "CTRL"
      offset: 0x00
      width: 32
      access: "rw"
      reset: 0x00000000
      category: "control"
      description: "Divider control register."
      write_side_effects:
        - "enable controls whether clk_o toggles; disabling forces clk_o low and clears locked_o."
        - "irq_enable gates terminal event interrupt generation."
      fields:
        - { name: "enable", bits: [0, 0], access: "rw", reset: 0x0, write_effect: "1 enables divider, 0 disables and clears active output", description: "Divider enable" }
        - { name: "irq_enable", bits: [1, 1], access: "rw", reset: 0x0, write_effect: "1 enables irq_o when STATUS.irq_pending is set", description: "Interrupt enable" }
        - { name: "reserved_31_2", bits: [31, 2], access: "reserved", reset: 0x0, read_value: 0, write_effect: "ignore", description: "Reserved" }
    - name: "DIVISOR"
      offset: 0x04
      width: 32
      access: "rw"
      reset: 0x00000002
      category: "configuration"
      description: "Programmable divide ratio."
      write_side_effects:
        - "Writing divisor stores pending_divisor; value 0 is coerced to 1 for safe behavior."
        - "New divisor takes effect on the next counter reload boundary."
      fields:
        - { name: "divisor", bits: [15, 0], access: "rw", reset: 0x0002, write_effect: "Program divide ratio; 0 coerces to 1", description: "Integer divisor value" }
        - { name: "reserved_31_16", bits: [31, 16], access: "reserved", reset: 0x0, read_value: 0, write_effect: "ignore", description: "Reserved" }
    - name: "STATUS"
      offset: 0x08
      width: 32
      access: "ro"
      reset: 0x00000000
      category: "status"
      description: "Divider status."
      fields:
        - { name: "running", bits: [0, 0], access: "ro", reset: 0x0, description: "1 when divider is enabled" }
        - { name: "locked", bits: [1, 1], access: "ro", reset: 0x0, description: "1 after first valid reload while enabled" }
        - { name: "irq_pending", bits: [2, 2], access: "ro", reset: 0x0, description: "Terminal-toggle event pending until INTCLR write" }
        - { name: "reserved_31_3", bits: [31, 3], access: "reserved", reset: 0x0, read_value: 0, write_effect: "ignore", description: "Reserved" }
    - name: "INTCLR"
      offset: 0x0C
      width: 32
      access: "wo"
      reset: 0x00000000
      category: "interrupt"
      description: "Interrupt clear register."
      write_side_effects:
        - "Writing bit0=1 clears STATUS.irq_pending."
      fields:
        - { name: "clear_irq", bits: [0, 0], access: "wo", reset: 0x0, write_effect: "W1C clear of terminal event pending status", description: "Clear interrupt pending" }
        - { name: "reserved_31_1", bits: [31, 1], access: "reserved", reset: 0x0, read_value: 0, write_effect: "ignore", description: "Reserved" }
memory:
  instances: []
  note: "No RAM, ROM, FIFO, or SRAM macros required; divider uses flops for registers and counter."
interrupts:
  sources:
    - { name: "TERMINAL_EVENT", bit: 0, type: "level", enable_reg: "CTRL.irq_enable", status_reg: "STATUS.irq_pending", clear: "INTCLR.clear_irq W1C", description: "Divider terminal toggle event" }
  output:
    signal: "irq_o"
    polarity: "active_high"
    type: "level"
fsm:
  divider_fsm:
    states:
      - "DISABLED"
      - "RUNNING_LOW"
      - "RUNNING_HIGH"
    transitions:
      - { from: "DISABLED", to: "RUNNING_LOW", condition: "CTRL.enable=1" }
      - { from: "RUNNING_LOW", to: "RUNNING_HIGH", condition: "counter reaches terminal count" }
      - { from: "RUNNING_HIGH", to: "RUNNING_LOW", condition: "counter reaches terminal count" }
      - { from: "RUNNING_LOW", to: "DISABLED", condition: "CTRL.enable=0 or reset asserted" }
      - { from: "RUNNING_HIGH", to: "DISABLED", condition: "CTRL.enable=0 or reset asserted" }
    reset_state: "DISABLED"
    encoding: "localparam binary encoding selected by rtl-gen"
timing:
  target_clocks:
    - { name: "clk_i", frequency_mhz: 100, duty_cycle: 0.5, uncertainty_ns: 0.1 }
  latency_budget:
    register_access_cycles: { min: 1, max: 1, measured_from: "psel && penable", measured_to: "pready" }
    interrupt_latency_cycles: { min: 0, max: 1, measured_from: "terminal_event", measured_to: "irq_o assertion" }
    divisor_update_cycles: { min: 1, max: null, measured_from: "DIVISOR write", measured_to: "next terminal boundary" }
  throughput:
    apb_accesses_per_two_cycles: 1
    output_half_period_input_cycles: "active_divisor"
  timing_exceptions: []
  io_delays:
    inputs:
      - { ports: "all_inputs_except_clocks_resets", clock: "clk_i", delay_ns: 0.2, source: "default system-level timing budget" }
    outputs:
      - { ports: "all_outputs", clock: "clk_i", delay_ns: 0.2, source: "default system-level timing budget" }
  false_paths:
    - { from: "rst_ni", to: "all_registers", reason: "async reset assertion" }
  multicycle_paths: []
  sta_expectations:
    setup_wns_ns_min: 0.0
    hold_wns_ns_min: 0.0
    required_reports: ["sta/out/setup.rpt", "sta/out/hold.rpt", "sta/out/wns.json"]
power:
  domains:
    - { name: "PD_CORE", voltage: "nominal", clock_domains: ["clk_i"], isolation: "not_required_single_domain" }
  clock_gating:
    required: false
    rationale: "Divider enable prevents output toggling but no integrated clock gate is required by this SSOT."
  reset_retention:
    retention_required: false
    reset_value_source: "registers and function_model state variables"
  power_states:
    - { name: "ON", entry: "rst_ni deasserted", exit: "rst_ni asserted", guarantees: ["Register access and divider behavior active"] }
  upf_required: false
security:
  classification: "non_secure_control_ip"
  assets:
    - { name: "divider_configuration", protection: "External APB fabric enforces privilege; IP enforces field access and reserved behavior." }
    - { name: "generated_clock_output", protection: "Glitchless update invariant prevents asynchronous/runt pulse from software writes." }
  threat_model:
    - { threat: "illegal register access", mitigation: "pslverr on unsupported address and no state mutation" }
    - { threat: "software writes divisor 0", mitigation: "Coerce to divisor 1 to avoid stalled or undefined output" }
    - { threat: "reserved field manipulation", mitigation: "Reserved fields read zero and ignore writes" }
  privilege_model: "External bus fabric enforces privilege; no internal privilege levels."
  safety_goals:
    - "No runt output pulse on divisor update."
    - "Divider output is forced low on reset or disable."
error_handling:
  error_sources:
    - { id: "ERR_APB_ADDR", condition: "APB access to unsupported offset", architectural_effect: "pslverr=1 for access; no register state change on illegal write" }
    - { id: "ERR_APB_WRITE_RO", condition: "APB write to read-only STATUS", architectural_effect: "pslverr=1 for access; no status mutation" }
    - { id: "WARN_DIV_ZERO", condition: "DIVISOR write data divisor field is 0", architectural_effect: "pending_divisor coerced to 1 without pslverr" }
  propagation:
    - "APB errors are reported only during completing APB access phase."
    - "WARN_DIV_ZERO is observable by reading back DIVISOR=1 after the write."
  recovery:
    - { action: "legal APB access", clears: ["pslverr transient"], preserves: ["valid configuration"] }
    - { action: "INTCLR.clear_irq W1C", clears: ["STATUS.irq_pending"], preserves: ["CTRL", "DIVISOR"] }
debug_observability:
  waveform_must_probe:
    - "clk_i"
    - "rst_ni"
    - "counter"
    - "active_divisor"
    - "pending_divisor"
    - "clk_o"
    - "locked_o"
    - "irq_pending"
    - "APB psel/penable/pwrite/paddr/prdata/pwdata/pready/pslverr"
  status_outputs: ["locked_o", "irq_o", "STATUS.running", "STATUS.locked", "STATUS.irq_pending"]
  trace_events:
    - { name: "divider_enable", trigger: "CTRL.enable transitions 0->1" }
    - { name: "divider_terminal", trigger: "counter reaches active_divisor-1" }
    - { name: "divisor_update", trigger: "active_divisor loads pending_divisor" }
    - { name: "irq_clear", trigger: "INTCLR.clear_irq W1C write" }
  debug_registers: ["CTRL", "DIVISOR", "STATUS", "INTCLR"]
integration:
  bus_attachment:
    control: "APB4 slave"
    data: "custom divided_clock output"
  connections:
    - { module: "clkdiv_regs", port: "clk_i", signal: "clk_i" }
    - { module: "clkdiv_regs", port: "rst_ni", signal: "rst_ni" }
    - { module: "clkdiv_regs", port: "paddr", signal: "paddr" }
    - { module: "clkdiv_regs", port: "psel", signal: "psel" }
    - { module: "clkdiv_regs", port: "penable", signal: "penable" }
    - { module: "clkdiv_regs", port: "pwrite", signal: "pwrite" }
    - { module: "clkdiv_regs", port: "pwdata", signal: "pwdata" }
    - { module: "clkdiv_regs", port: "pstrb", signal: "pstrb" }
    - { module: "clkdiv_regs", port: "prdata", signal: "prdata" }
    - { module: "clkdiv_regs", port: "pready", signal: "pready" }
    - { module: "clkdiv_regs", port: "pslverr", signal: "pslverr" }
    - { module: "clkdiv_core", port: "clk_i", signal: "clk_i" }
    - { module: "clkdiv_core", port: "rst_ni", signal: "rst_ni" }
    - { module: "clkdiv_core", port: "enable_i", signal: "enable" }
    - { module: "clkdiv_core", port: "divisor_i", signal: "active_divisor" }
    - { module: "clkdiv_core", port: "clk_o", signal: "clk_o" }
    - { module: "clkdiv_core", port: "locked_o", signal: "locked_o" }
    - { module: "clkdiv_core", port: "terminal_event_o", signal: "terminal_event" }
    - { module: "clkdiv_regs", port: "terminal_event_i", signal: "terminal_event" }
    - { module: "clkdiv_regs", port: "irq_o", signal: "irq_o" }
  address_map_requirements:
    alignment_bytes: 4
    decode_owner: "clkdiv_regs"
    illegal_access_response: "pslverr for unsupported APB access"
  dependencies:
    external_modules: []
    external_clocks: ["clk_i"]
    external_resets: ["rst_ni"]
  integration_notes:
    - "SoC must treat clk_o as a generated clock if used as a downstream clock."
    - "SoC APB fabric must provide clk_i-synchronous APB accesses."
dft:
  scan_required: false
  scan_ports: []
  test_mode_ports: []
  controllability:
    reset: "rst_ni must be controllable in test mode"
    clocks: ["clk_i"]
    registers: "APB can program CTRL/DIVISOR and clear IRQ"
  observability:
    required_internal_points: ["counter", "active_divisor", "clk_o", "locked_o", "irq_pending"]
  mbist_required: false
  notes: "No memory macros; scan insertion is an SoC-level decision."
synthesis:
  dialect: "systemverilog_2012"
  top_module: "clkdiv"
  technology:
    pdk: "sky130"
    standard_cell_library: "sky130_fd_sc_hd"
    liberty_corner: "ss_100C_1v40"
    liberty_env: "SKY130_LIB"
    lef_env: "SKY130_LEF"
    tech_lef_env: "SKY130_TLEF"
    rcx_rules_env: "SKY130_RCX_RULES"
  constraints:
    - "No inferred latches"
    - "All architectural flops reset according to clock_reset_domains.reset_scheme"
    - "No package/interface/modport/function/task/for/while constructs in generated RTL"
    - "clk_o must be driven by sequential logic only; no combinational clock gating for clk_o"
  ppa_targets:
    area_um2_max: null
    power_mw_max: null
    frequency_mhz_min: 100
  required_outputs:
    - "syn/out/clkdiv.json or syn/out/clkdiv.v"
    - "syn/out/area.rpt"
    - "syn/out/timing_summary.rpt"
pnr:
  utilization_pct: 60
  aspect_ratio: 1.0
  core_space_um: 2.0
  global_density: 0.65
  io_layers:
    horizontal: "met3"
    vertical: "met2"
  placement:
    density_target: 0.65
    max_displacement_um: null
  cts:
    buf_list: ["sky130_fd_sc_hd__clkbuf_4", "sky130_fd_sc_hd__clkbuf_8"]
    functional_mode_case_analysis: []
  routing:
    signal_layers: { min: "met1", max: "met5" }
    clock_layers: { min: "met3", max: "met5" }
    drc_waivers: []
  required_outputs:
    - "pnr/out/floorplan.def"
    - "pnr/out/placed.def"
    - "pnr/out/cts.def"
    - "pnr/out/routed.def"
    - "pnr/out/routed.v"
    - "pnr/out/routed.spef"
    - "pnr/out/pnr.report.md"
coding_rules:
  verilog_style: "systemverilog_2012"
  file_extension: ".sv"
  parameter_header: "rtl/clkdiv_param.vh"
  conventions:
    - "nonblocking (<=) in sequential always @(posedge clk_i or negedge rst_ni)"
    - "blocking (=) in combinational always @(*)"
    - "No latches: every combinational branch assigns all outputs"
    - "Active-low async reset"
    - "Parameterize widths using DIV_WIDTH"
    - "ALLOW: input logic / output logic ANSI ports and internal single-driver logic"
    - "BANNED: typedef / enum / always_ff / always_comb / always_latch / package / endpackage / import / interface / modport / function / endfunction / task / endtask / for / while / *_pkg.sv"
    - "Use localparam state encoding with logic state/next_state signals"
  lint_waivers:
    - "UNUSEDSIGNAL: explicit approved tie-offs only"
    - "UNUSEDPARAM: none expected"
reuse_modules: []
custom:
  assumptions:
    - "No external clkdiv requirements file was present; this SSOT defines a baseline APB-controlled programmable divider contract."
    - "Default target clock is 100 MHz because no user clock target was supplied."
    - "DIVISOR write value 0 is coerced to 1 as safe RTL semantics."
  note: "Pending user review may refine frequency, divisor width, and register map."
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
  headers:
    - "rtl/clkdiv_param.vh"
  rtl:
    - "rtl/clkdiv.sv"
    - "rtl/clkdiv_regs.sv"
    - "rtl/clkdiv_core.sv"
  sim:
    - "sim/tb_top.sv"
    - "sim/tb_program.sv"
    - "sim/clkdiv_model.sv"
  firmware:
    - "firmware/clkdiv_regs.h"
  docs:
    - "docs/register_map.md"
    - "docs/README.md"
test_requirements:
  scenarios:
    - id: "SC_APB"
      name: "APB register access"
      stimulus: "Read reset registers; write CTRL/DIVISOR; attempt unsupported address and RO STATUS write."
      expected: "Register readback, reserved zero behavior, pslverr, and side effects match registers and error_handling."
      checker: "APB monitor and scoreboard compare prdata/pslverr and internal model state."
      coverage: ["registers.register_list", "ERR_APB_ADDR", "ERR_APB_WRITE_RO"]
    - id: "SC_DIV2"
      name: "Divide by two baseline"
      stimulus: "Program DIVISOR=2, set enable, observe clk_o toggles."
      expected: "clk_o toggles every 2 clk_i rising edges and locked_o asserts after first reload."
      checker: "Cycle model counts clk_i edges between clk_o transitions."
      coverage: ["FM_DIVIDE", "S2_COUNT", "S3_TERMINAL"]
    - id: "SC_DIV_UPDATE"
      name: "Glitchless divisor update"
      stimulus: "While enabled, write new DIVISOR value mid-count."
      expected: "active_divisor changes only at terminal boundary; no runt/asynchronous output pulse."
      checker: "Waveform/cycle checker verifies clk_o edge spacing and active_divisor load ordering."
      coverage: ["glitchless_update", "cycle_model.ordering"]
    - id: "SC_IRQ"
      name: "Terminal interrupt set and clear"
      stimulus: "Set irq_enable, enable divider, wait terminal event, then write INTCLR.clear_irq."
      expected: "irq_pending and irq_o assert on terminal event and deassert after W1C clear."
      checker: "Scoreboard checks STATUS.irq_pending and irq_o timing."
      coverage: ["TERMINAL_EVENT", "irq_clear"]
    - id: "SC_DIV_ZERO"
      name: "DIVISOR zero write policy"
      stimulus: "Write DIVISOR=0 and read back/divide."
      expected: "pending_divisor coerces to 1 without pslverr and output follows divide-by-one half-period contract."
      checker: "APB readback and cycle checker compare coerced divisor behavior."
      coverage: ["WARN_DIV_ZERO", "function_model.transactions.FM_DIVIDE.error_cases"]
  scoreboard_checks: 12
  coverage_goals:
    function:
      target_pct: 100
      model: "function_model"
      description: "Behavioral coverage for clock divide operation, register side effects, and interrupt/error behavior."
      bins:
        - { id: "FCOV_FM_DIVIDE", source_ref: "function_model.transactions.FM_DIVIDE", class: "transaction", description: "Primary divide transaction observed" }
        - { id: "FCOV_DIV_ZERO", source_ref: "function_model.transactions.FM_DIVIDE.error_cases.WARN_DIV_ZERO", class: "error_case", description: "Zero divisor coercion observed" }
        - { id: "FCOV_IRQ", source_ref: "function_model.transactions.FM_DIVIDE.side_effects.terminal_irq", class: "interrupt", description: "Terminal event interrupt set and clear observed" }
    cycle:
      target_pct: 100
      model: "cycle_model"
      description: "Cycle/handshake/timing coverage for APB accesses, counter pipeline, and output timing."
      bins:
        - { id: "CCOV_APB_ACCESS", source_ref: "cycle_model.pipeline.S1_APB_ACCESS", class: "pipeline_stage", description: "APB access completion observed" }
        - { id: "CCOV_COUNT", source_ref: "cycle_model.pipeline.S2_COUNT", class: "pipeline_stage", description: "Counter increment stage observed" }
        - { id: "CCOV_TERMINAL", source_ref: "cycle_model.pipeline.S3_TERMINAL", class: "pipeline_stage", description: "Terminal toggle/reload observed" }
        - { id: "CCOV_CLK_TOGGLE_RULE", source_ref: "cycle_model.handshake_rules.clk_o", class: "output_timing", description: "clk_o toggles only at terminal count" }
        - { id: "CCOV_FSM_TRANSITIONS", source_ref: "fsm.divider_fsm.transitions", class: "state_transition", description: "Declared FSM transitions observed" }
    functional: "Legacy alias: function + cycle coverage must both close."
    line: ">= 90% instrumented line coverage or explicit project waiver"
    branch: ">= 85% instrumented branch coverage or explicit project waiver"
    fsm: "100% declared FSM states and legal transitions covered"
    assertions: "All protocol/order/error assertions pass"
quality_gates:
  ssot:
    pass: "All canonical sections are present, substantive, internally consistent, and have no live template placeholders."
    evidence: ["check_ssot_disk.sh PASS", "traceability covers function_model/cycle_model/test_requirements"]
  rtl_gen:
    profile: "production"
    target_scale:
      basis: "small programmable peripheral; no human-locked structural depth minima"
      source_files_min: 0
      modules_min: 0
      procedural_blocks_min: 0
      state_updates_min: 0
      depth_score_min: 0
      logic_modules_min: 0
      behavior_owner_logic_modules_min: 0
    target_scale_waiver:
      approved: false
      reason: ""
      owner: ""
    pass: "RTL implements SSOT-derived register block, divider core, and top integration with fresh compile/lint/provenance evidence."
    evidence: ["rtl/rtl_todo_plan.json", "rtl/rtl_authoring_provenance.json", "rtl/rtl_traceability.json", "rtl/rtl_compile.json", "lint/dut_lint.json", "sim/fl_rtl_goal_audit.json"]
  rtl:
    pass: "RTL implements function_model and cycle_model, compiles, lints, and maps every output_rule to declared ports."
    evidence: ["rtl compile report", "dut lint report", "FL-vs-RTL scoreboard/audit"]
  dv:
    pass: "APB, divide timing, glitchless update, interrupt, and divisor-zero scenarios pass."
    evidence: ["sim/test_results.json", "sim/scoreboard_report.md", "sim/assertion_failures.jsonl"]
  coverage:
    pass: "SSOT-declared functional and cycle coverage goals pass or have approved waivers."
    evidence: ["cov/coverage.json", "sim/coverage_report.md"]
  eda:
    pass: "Synthesis, STA, PnR, and post-route STA meet SSOT timing/area/power/physical targets or have approved waivers."
    evidence: ["syn report", "sta reports", "pnr report", "routed.spef", "sta-post reports"]
  signoff:
    pass: "All SSOT/RTL/DV/coverage/EDA gates pass with current evidence."
    evidence: ["signoff/signoff_summary.md", "quality_gates evidence bundle"]
traceability:
  yaml_to_output:
    - { yaml: "top_module.name", output: "RTL module clkdiv and downstream file naming" }
    - { yaml: "parameters", output: "rtl/clkdiv_param.vh and parameterized RTL widths" }
    - { yaml: "io_list.interfaces", output: "rtl/clkdiv.sv top ports and protocol checks" }
    - { yaml: "registers.register_list", output: "rtl/clkdiv_regs.sv, firmware header, register docs" }
    - { yaml: "function_model", output: "rtl/clkdiv_core.sv and verification reference model" }
    - { yaml: "cycle_model", output: "RTL sequential timing and cycle checkers" }
    - { yaml: "fsm", output: "clkdiv_core state implementation and FSM coverage" }
    - { yaml: "integration.connections", output: "clkdiv top named port maps" }
    - { yaml: "timing", output: "sdc/clkdiv.sdc and STA pass/fail criteria" }
    - { yaml: "security", output: "negative tests for illegal accesses and glitchless update" }
    - { yaml: "error_handling", output: "RTL error responses and DV fault scenarios" }
    - { yaml: "test_requirements.scenarios", output: "tb/sim scenario implementation" }
    - { yaml: "quality_gates", output: "ATLAS workflow evidence and signoff criteria" }
workflow_todos:
  fl-model-gen:
    - id: "FL_TODO_CLKDIV_MODEL"
      content: "Implement clocked functional/cycle reference model for clkdiv"
      detail: "Model APB register side effects, counter, active/pending divisor, clk_o, locked_o, irq_pending, and pslverr behavior from function_model and cycle_model."
      criteria:
        - "Model output_rules produce clk_o/locked_o/irq_o expected values"
        - "Model covers DIVISOR=0 coercion and unsupported APB access"
      source_refs: ["function_model", "cycle_model", "registers.register_list"]
      priority: "high"
      required: true
  rtl-gen:
    - id: "RTL_TODO_CLKDIV_TOP"
      content: "Implement clkdiv top integration"
      detail: "Create rtl/clkdiv.sv with declared IO ports and instantiate/wire clkdiv_regs and clkdiv_core according to integration.connections."
      criteria:
        - "Top module ports match io_list exactly"
        - "Named port connections satisfy integration.connections"
        - "No wrapper-only top pattern; top file is rtl/clkdiv.sv"
      source_refs: ["top_module", "io_list", "integration.connections", "sub_modules"]
      owner_module: "clkdiv"
      owner_file: "rtl/clkdiv.sv"
      priority: "high"
      required: true
    - id: "RTL_TODO_CLKDIV_REGS"
      content: "Implement APB register/status block"
      detail: "Implement CTRL, DIVISOR, STATUS, INTCLR, APB one-cycle pready/prdata/pslverr behavior, reserved-field policy, divisor zero coercion, and irq pending clear/set policy."
      criteria:
        - "Register reset, access, bit ranges, write effects, and reserved fields match registers.register_list"
        - "Unsupported address and RO write pslverr behavior matches error_handling"
        - "irq_o reflects irq_pending && irq_enable"
      source_refs: ["registers.register_list", "io_list.interfaces.apb_slave", "interrupts", "error_handling"]
      owner_module: "clkdiv_regs"
      owner_file: "rtl/clkdiv_regs.sv"
      priority: "high"
      required: true
    - id: "RTL_TODO_CLKDIV_CORE"
      content: "Implement divider counter and output timing core"
      detail: "Implement enable behavior, active/pending divisor boundary update, counter terminal detection, clk_o sequential toggle, locked_o, and terminal_event_o from function_model and cycle_model."
      criteria:
        - "clk_o changes only on clk_i rising edge terminal count"
        - "DIVISOR updates are glitchless and apply only at terminal boundary"
        - "FSM states/transitions and coverage hooks align with fsm.divider_fsm"
      source_refs: ["function_model.transactions.FM_DIVIDE", "cycle_model.pipeline", "cycle_model.ordering", "fsm.divider_fsm"]
      owner_module: "clkdiv_core"
      owner_file: "rtl/clkdiv_core.sv"
      priorit
... <truncated 1628 chars>

Base rtl-gen contract:
Prepare rtl-gen for clkdiv using only clkdiv/yaml/clkdiv.ssot.yaml and clkdiv/rtl/rtl_todo_plan.json, clkdiv/rtl/rtl_authoring_plan.json, and packets under clkdiv/rtl/authoring_packets. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=3e8e19ce43da418bd8054b5f78147a151541d8ad18282c75587963810b660352. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "clkdiv",
        "reason": "42 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "clkdiv",
        "reason": "3 owner logic structure issue(s) remain. clkdiv_regs: Behavior-owner module is not declared in its owner file; clkdiv_core: Behavior-owner module is not declared in its owner file; clkdiv: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "rtl_placeholder_free_evidence",
        "owner_module": "clkdiv",
        "reason": "1 RTL placeholder/policy issue(s) remain. None:None: None (No listed RTL source files were readable, so placeholder-free evidence cannot be checked)",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "status": "open",
        "task_id": "RTL-0009"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "clkdiv",
        "reason": "1 top IO contract issue(s) remain. clkdiv: SSOT top module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "top_output_drive_evidence",
        "owner_module": "clkdiv",
        "reason": "1 top output drive issue(s) remain. clkdiv: SSOT top module is not declared, so output drive evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
        "status": "open",
        "task_id": "RTL-0011"
      },
      {
        "gate_kind": "top_input_consumption_evidence",
        "owner_module": "clkdiv",
        "reason": "1 top input consumption issue(s) remain. clkdiv: SSOT top module is not declared, so input consumption evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
        "status": "open",
        "task_id": "RTL-0012"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "clkdiv",
        "reason": "3 manifest hierarchy integration issue(s) remain. clkdiv: SSOT top module is not declared in listed RTL sources; clkdiv_regs: SSOT manifest child module is not declared in listed RTL sources; clkdiv_core: SSOT manifest child module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "clkdiv",
        "reason": "1 manifest signal-flow issue(s) remain. clkdiv: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "status": "open",
        "task_id": "RTL-0015"
      },
      {
        "gate_kind": "rtl_implementation_depth_evidence",
        "owner_module": "clkdiv",
        "reason": "4 production RTL implementation-depth issue(s) remain. No listed DUT RTL sources are available for production implementation-depth audit; Production RTL implementation depth score is below the SSOT-derived or target-scale threshold: actual=0 required=103; Too few RTL modules contain implementation structure for the SSOT behavior complexity: actual=0 required=3",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_implementation_depth_evidence",
        "status": "open",
        "task_id": "RTL-0022"
      }
    ],
    "blocked_by_locked_truth": [
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "owner_module": "clkdiv",
        "reason": "32 SSOT connection contract issue(s) remain. clkdiv_regs: SSOT connection contract targets a module not declared in RTL; clkdiv_regs: SSOT connection contract targets a module not declared in RTL; clkdiv_regs: SSOT connection contract targets a module not declared in RTL",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      },
      {
        "gate_kind": "golden_authority_artifacts",
        "owner_module": "clkdiv",
        "reason": "Missing production golden authority artifact(s): governance/authority.json, model/model_signature.json",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.golden_authority_artifacts",
        "status": "open",
        "task_id": "RTL-0020"
      }
    ],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "clkdiv",
        "reason": "Missing common_ai_agent RTL authoring provenance.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "clkdiv",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "clkdiv",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "clkdiv",
        "reason": "155 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "gate_kind": "protocol_assertion_evidence",
        "owner_module": "clkdiv",
        "reason": "Missing protocol assertion artifact: verify/protocol_assertions.sva.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "gate_kind": "fl_rtl_goal_audit",
        "owner_module": "clkdiv",
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "gate_kind": "coverage_closure",
        "owner_module": "clkdiv",
        "reason": "Missing coverage closure artifact: cov/coverage.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "status": "open",
        "task_id": "RTL-0026"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 32,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
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
    "open_required_todos": 156,
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
          "clkdiv/rtl/rtl_authoring_provenance.json",
          "clkdiv/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip clkdiv --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py clkdiv --root . --audit-rtl"
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
          "clkdiv/rtl/rtl_compile.json",
          "clkdiv/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py clkdiv --top clkdiv --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py clkdiv --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "clkdiv/list/clkdiv.f covers the current DUT RTL sources."
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
          "clkdiv/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py clkdiv --top clkdiv",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py clkdiv --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "clkdiv/list/clkdiv.f covers the current DUT RTL/header sources."
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
          "clkdiv/rtl/rtl_todo_plan.json",
          "clkdiv/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py clkdiv --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "155 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "artifact": "verify/protocol_assertions.sva",
        "artifacts": [
          "clkdiv/verify/protocol_assertions.sva",
          "clkdiv/verify/protocol_assertions.summary.json",
          "clkdiv/sim/assertion_failures.jsonl"
        ],
        "closure_rule": "Generated assertions exist and latest simulation has zero assertion failure records.",
        "commands": [
          "python3 workflow/fl-model-gen/scripts/emit_protocol_assertions.py clkdiv --root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py clkdiv --root . --audit-rtl"
        ],
        "gate_kind": "protocol_assertion_evidence",
        "prerequisites": [
          "SSOT cycle_model/protocol rules are machine-checkable.",
          "Simulation has run after RTL edits."
        ],
        "reason": "Missing protocol assertion artifact: verify/protocol_assertions.sva.",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "stage_sequence": [
          "ssot-protocol-assertions",
          "sim"
        ],
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "artifact": "sim/fl_rtl_goal_audit.json",
        "artifacts": [
          "clkdiv/sim/fl_rtl_goal_audit.json"
        ],
        "closure_rule": "fl_rtl_goal_audit.json must be fresh and status=pass.",
        "commands": [
          "python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py clkdiv --root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py clkdiv --root . --audit-rtl"
        ],
        "gate_kind": "fl_rtl_goal_audit",
        "prerequisites": [
          "FL model, equivalence goals, TB, and simulation evidence are current."
        ],
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "stage_sequence": [
          "ssot-fl-model",
          "ssot-equiv-goals",
          "ssot-tb-cocotb",
          "sim",
          "goal-audit"
        ],
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "artifact": "cov/coverage.json",
        "artifacts": [
          "clkdiv/cov/coverage.json"
        ],
        "closure_rule": "coverage.json must be fresh, come from ssot_coverage_summary, and close every planned required bin.",
        "commands": [
          "python3 workflow/coverage/scripts/ssot_coverage_summary.py clkdiv",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py clkdiv --root . --audit-rtl"
        ],
        "gate_kind": "coverage_closure",
        "prerequisites": [
          "Simulation evidence exists and planned coverage bins are observable."
        ],
        "reason": "Missing coverage closure artifact: cov/coverage.json.",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "stage_sequence": [
          "sim",
          "coverage"
        ],
        "status": "open",
        "task_id": "RTL-0026"
      }
    ]
  },
  "ip": "clkdiv",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__clkdiv_regs.json",
      "kind": "module",
      "llm_actionable_open_count": 34,
      "open_required_count": 34,
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "packet_id": "module__clkdiv_regs",
      "required_count": 34,
      "status_counts": {
        "open": 34
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__clkdiv_core__function_model.json",
      "kind": "module",
      "llm_actionable_open_count": 30,
      "open_required_count": 30,
      "owner_file": "rtl/clkdiv_core.sv",
      "owner_module": "clkdiv_core",
      "packet_id": "module__clkdiv_core__function_model",
      "required_count": 30,
      "status_counts": {
        "open": 30
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__clkdiv_core__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 18,
      "open_required_count": 18,
      "owner_file": "rtl/clkdiv_core.sv",
      "owner_module": "clkdiv_core",
      "packet_id": "module__clkdiv_core__cycle_model",
      "required_count": 18,
      "status_counts": {
        "open": 18
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__clkdiv_core__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 8,
      "open_required_count": 8,
      "owner_file": "rtl/clkdiv_core.sv",
      "owner_module": "clkdiv_core",
      "packet_id": "module__clkdiv_core__fsm",
      "required_count": 8,
      "status_counts": {
        "open": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__clkdiv_core__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/clkdiv_core.sv",
      "owner_module": "clkdiv_core",
      "packet_id": "module__clkdiv_core__equivalence",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__clkdiv_core__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/clkdiv_core.sv",
      "owner_module": "clkdiv_core",
      "packet_id": "module__clkdiv_core__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__clkdiv.json",
      "kind": "module",
      "llm_actionable_open_count": 46,
      "open_required_count": 46,
      "owner_file": "rtl/clkdiv.sv",
      "owner_module": "clkdiv",
      "packet_id": "module__clkdiv",
      "required_count": 47,
      "status_counts": {
        "open": 46,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 9,
      "open_required_count": 9,
      "owner_file": "rtl/clkdiv.sv",
      "owner_module": "clkdiv",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 10,
      "status_counts": {
        "open": 9,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 2,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 2,
      "owner_file": "rtl/clkdiv.sv",
      "owner_module": "clkdiv",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 7,
      "status_counts": {
        "open": 2,
        "pass": 5
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 7,
      "owner_file": "rtl/clkdiv.sv",
      "owner_module": "clkdiv",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 7,
      "status_counts": {
        "open": 7
      }
    }
  ],
  "policy": {
    "dynamic_task_rule": "Use every required task in this file as the authoritative RTL implementation/evidence ledger. Expose Atlas/UI TodoTracker items as a flat one-to-one projection of this ledger so the existing flat TodoTracker executes one SSOT-derived RTL task at a time.",
    "fixed_template_role": "seed_only",
    "no_orphan_function_level": true,
    "reference_profile_rule": "Optional rtl_reference_profile artifacts are calibration-only scale reports; they must not be copied, transformed, or used as fixed RTL templates.",
    "rtl_gate_todo_rule": "RTL-gen quality gates are first-class rtl_gate.rtl_gen TODOs; compile/lint/static/ownership/owner-logic/placeholder-free/implementation-depth/top-io/top-output-drive/top-input-consumption/hierarchy/port-connection/signal-flow/connection-contract gates must close as TODOs before PASS.",
    "rtl_quality_profile": "production",
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
    "human_locked_tasks": 2,
    "llm_actionable_packets": 8,
    "llm_actionable_tasks": 147,
    "max_packet_required_tasks": 47,
    "module_packets": 7,
    "next_llm_packets": [
      "module__clkdiv_regs",
      "module__clkdiv_core__function_model",
      "module__clkdiv_core__cycle_model",
      "module__clkdiv_core__fsm",
      "module__clkdiv_core__equivalence",
      "module__clkdiv_core__workflow_todo",
      "module__clkdiv",
      "rtl_gate_evidence_closure"
    ],
    "packet_task_limit": 48,
    "packets": 10,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 163,
    "sliced_module_packets": 5,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 7,
    "total_tasks": 163,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "3e8e19ce43da418bd8054b5f78147a151541d8ad18282c75587963810b660352",
  "top": "clkdiv",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/clkdiv_regs.sv):
<missing or not authored yet>

Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__clkdiv_regs.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 32,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 34,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/clkdiv_regs.sv",
      "name": "clkdiv_regs",
      "refs": [
        "error_handling",
        "interrupts",
        "io_list",
        "io_list.interfaces.apb_slave",
        "registers",
        "registers.register_list",
        "registers.register_list.CTRL",
        "registers.register_list.DIVISOR",
        "registers.register_list.INTCLR",
        "registers.register_list.STATUS"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/clkdiv_regs.sv",
        "name": "clkdiv_regs",
        "wiring_only": false
      },
      {
        "file": "rtl/clkdiv_core.sv",
        "name": "clkdiv_core",
        "wiring_only": false
      },
      {
        "file": "rtl/clkdiv.sv",
        "name": "clkdiv",
        "wiring_only": false
      }
    ],
    "quality_profile": "production",
    "reference_profile": null,
    "ssot_connection_contracts": [
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "clk_i",
        "signal": "clk_i",
        "signal_terms": [
          "clk_i"
        ],
        "source_ref": "sub_modules[0].connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "rst_ni",
        "signal": "rst_ni",
        "signal_terms": [
          "rst_ni"
        ],
        "source_ref": "sub_modules[0].connections[1]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "enable_o",
        "signal": "enable",
        "signal_terms": [
          "enable"
        ],
        "source_ref": "sub_modules[0].connections[2]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "divisor_o",
        "signal": "active_divisor",
        "signal_terms": [
          "active_divisor"
        ],
        "source_ref": "sub_modules[0].connections[3]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "irq_pending_i",
        "signal": "irq_pending",
        "signal_terms": [
          "irq_pending"
        ],
        "source_ref": "sub_modules[0].connections[4]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "clk_i",
        "signal": "clk_i",
        "signal_terms": [
          "clk_i"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "rst_ni",
        "signal": "rst_ni",
        "signal_terms": [
          "rst_ni"
        ],
        "source_ref": "integration.connections[1]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
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
        "module": "clkdiv_regs",
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
        "module": "clkdiv_regs",
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
        "module": "clkdiv_regs",
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
        "module": "clkdiv_regs",
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
        "module": "clkdiv_regs",
        "port": "pstrb",
        "signal": "pstrb",
        "signal_terms": [
          "pstrb"
        ],
        "source_ref": "integration.connections[7]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "prdata",
        "signal": "prdata",
        "signal_terms": [
          "prdata"
        ],
        "source_ref": "integration.connections[8]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "pready",
        "signal": "pready",
        "signal_terms": [
          "pready"
        ],
        "source_ref": "integration.connections[9]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "pslverr",
        "signal": "pslverr",
        "signal_terms": [
          "pslverr"
        ],
        "source_ref": "integration.connections[10]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "terminal_event_i",
        "signal": "terminal_event",
        "signal_terms": [
          "terminal_event"
        ],
        "source_ref": "integration.connections[18]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "clkdiv_regs",
        "port": "irq_o",
        "signal": "irq_o",
        "signal_terms": [
          "irq_o"
        ],
        "source_ref": "integration.connections[19]"
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
    "llm_actionable_open_count": 34,
    "open_required_count": 34,
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
  "ip": "clkdiv",
  "kind": "module",
  "owner_file": "rtl/clkdiv_regs.sv",
  "owner_module": "clkdiv_regs",
  "packet_id": "module__clkdiv_regs",
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
      "equivalence.module": 1,
      "error_handling.recovery": 2,
      "interrupts.sources": 1,
      "io_list.port": 14,
      "registers.field": 11,
      "registers.register": 4,
      "workflow_todo.rtl_gen": 1
    },
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 34,
      "task_limit": 48
    },
    "open_required_count": 34,
    "required_count": 34,
    "source_refs": [
      "workflow_todos.rtl-gen[1]",
      "registers.register_list.CTRL",
      "registers.register_list.CTRL.fields.enable",
      "registers.register_list.CTRL.fields.irq_enable",
      "registers.register_list.CTRL.fields.reserved_31_2",
      "registers.register_list.DIVISOR",
      "registers.register_list.DIVISOR.fields.divisor",
      "registers.register_list.DIVISOR.fields.reserved_31_16",
      "registers.register_list.STATUS",
      "registers.register_list.STATUS.fields.running",
      "registers.register_list.STATUS.fields.locked",
      "registers.register_list.STATUS.fields.irq_pending",
      "registers.register_list.STATUS.fields.reserved_31_3",
      "registers.register_list.INTCLR",
      "registers.register_list.INTCLR.fields.clear_irq",
      "registers.register_list.INTCLR.fields.reserved_31_1",
      "interrupts.sources.TERMINAL_EVENT",
      "error_handling.recovery.recovery_0",
      "error_handling.recovery.recovery_1",
      "sub_modules.clkdiv_regs.module_equivalence",
      "io_list.clock_domains.clk_i.ports.clk_i",
      "io_list.resets.rst_ni.ports.rst_ni",
      "io_list.interfaces.apb_slave.ports.paddr",
      "io_list.interfaces.apb_slave.ports.psel"
    ],
    "status_counts": {
      "open": 34
    },
    "task_count": 34
  },
  "tasks": [
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement APB register/status block",
      "criteria": [
        "Register reset, access, bit ranges, write effects, and reserved fields match registers.register_list",
        "Unsupported address and RO write pslverr behavior matches error_handling",
        "irq_o reflects irq_pending && irq_enable",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[1]",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "Semantic source_refs covered: error_handling, interrupts, io_list.interfaces.apb_slave, registers.register_list"
      ],
      "detail": "Implement CTRL, DIVISOR, STATUS, INTCLR, APB one-cycle pready/prdata/pslverr behavior, reserved-field policy, divisor zero coercion, and irq pending clear/set policy.\nSSOT ref: workflow_todos.rtl-gen[1].\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via workflow_todos.owner.\nSSOT item context: id=RTL_TODO_CLKDIV_REGS.",
      "evidence_terms": [
        "CLKDIV",
        "REGS",
        "RTL_TODO_CLKDIV_REGS",
        "TODO",
        "apb",
        "apb_slave",
        "clkdiv",
        "clkdiv_regs",
        "error_handling",
        "handling",
        "io",
        "io_list",
        "list",
        "regs",
        "slave"
      ],
      "id": "RTL-0028",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[1]",
      "ssot_context": {
        "id": "RTL_TODO_CLKDIV_REGS"
      },
      "ssot_refs": [
        "error_handling",
        "interrupts",
        "io_list.interfaces.apb_slave",
        "registers.register_list",
        "workflow_todos.rtl-gen[1]"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "CLKDIV",
          "REGS",
          "RTL_TODO_CLKDIV_REGS",
          "TODO",
          "apb",
          "apb_slave",
          "clkdiv",
          "clkdiv_regs",
          "error_handling",
          "handling",
          "io",
          "io_list",
          "list",
          "regs",
          "slave"
        ],
        "source_scope": "rtl/clkdiv_regs.sv",
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
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      },
      "workflow_todo": {
        "id": "RTL_TODO_CLKDIV_REGS",
        "source_refs": [
          "error_handling",
          "interrupts",
          "io_list.interfaces.apb_slave",
          "registers.register_list"
        ],
        "stage": "rtl-gen",
        "user_category": ""
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
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "CTRL width matches SSOT value 32",
        "CTRL reset behavior matches SSOT value 0",
        "CTRL access policy rw is implemented without read/write shortcuts",
        "CTRL decode uses SSOT address/offset 0"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.CTRL.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.\nSSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=0.",
      "evidence_terms": [],
      "id": "RTL-0095",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CTRL",
      "ssot_context": {
        "access": "rw",
        "name": "CTRL",
        "offset": "0",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.CTRL"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field CTRL.enable",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.CTRL.fields.enable",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "enable reset behavior matches SSOT value 0",
        "enable access policy rw is implemented without read/write shortcuts",
        "enable readback returns implemented RTL state when readable",
        "enable write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.CTRL.fields.enable.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.\nSSOT item context: name=enable; reset=0; access=rw.",
      "evidence_terms": [],
      "id": "RTL-0096",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CTRL.fields.enable",
      "ssot_context": {
        "access": "rw",
        "name": "enable",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.CTRL.fields.enable"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field CTRL.irq_enable",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.CTRL.fields.irq_enable",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "irq_enable reset behavior matches SSOT value 0",
        "irq_enable access policy rw is implemented without read/write shortcuts",
        "irq_enable readback returns implemented RTL state when readable",
        "irq_enable write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.CTRL.fields.irq_enable.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.\nSSOT item context: name=irq_enable; reset=0; access=rw.",
      "evidence_terms": [],
      "id": "RTL-0097",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CTRL.fields.irq_enable",
      "ssot_context": {
        "access": "rw",
        "name": "irq_enable",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.CTRL.fields.irq_enable"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field CTRL.reserved_31_2",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.CTRL.fields.reserved_31_2",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "reserved_31_2 reset behavior matches SSOT value 0",
        "reserved_31_2 access policy reserved is implemented without read/write shortcuts",
        "reserved_31_2 readback returns implemented RTL state when readable",
        "reserved_31_2 write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.CTRL.fields.reserved_31_2.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.\nSSOT item context: name=reserved_31_2; reset=0; access=reserved.",
      "evidence_terms": [],
      "id": "RTL-0098",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CTRL.fields.reserved_31_2",
      "ssot_context": {
        "access": "reserved",
        "name": "reserved_31_2",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.CTRL.fields.reserved_31_2"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register DIVISOR",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.DIVISOR",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "DIVISOR width matches SSOT value 32",
        "DIVISOR reset behavior matches SSOT value 2",
        "DIVISOR access policy rw is implemented without read/write shortcuts",
        "DIVISOR decode uses SSOT address/offset 4"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.DIVISOR.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.\nSSOT item context: name=DIVISOR; width=32; reset=2; access=rw; offset=4.",
      "evidence_terms": [],
      "id": "RTL-0099",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.DIVISOR",
      "ssot_context": {
        "access": "rw",
        "name": "DIVISOR",
        "offset": "4",
        "reset": "2",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.DIVISOR"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field DIVISOR.divisor",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.DIVISOR.fields.divisor",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "divisor reset behavior matches SSOT value 2",
        "divisor access policy rw is implemented without read/write shortcuts",
        "divisor readback returns implemented RTL state when readable",
        "divisor write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.DIVISOR.fields.divisor.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.\nSSOT item context: name=divisor; reset=2; access=rw.",
      "evidence_terms": [],
      "id": "RTL-0100",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.DIVISOR.fields.divisor",
      "ssot_context": {
        "access": "rw",
        "name": "divisor",
        "reset": "2"
      },
      "ssot_refs": [
        "registers.register_list.DIVISOR.fields.divisor"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field DIVISOR.reserved_31_16",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.DIVISOR.fields.reserved_31_16",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "reserved_31_16 reset behavior matches SSOT value 0",
        "reserved_31_16 access policy reserved is implemented without read/write shortcuts",
        "reserved_31_16 readback returns implemented RTL state when readable",
        "reserved_31_16 write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.DIVISOR.fields.reserved_31_16.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.\nSSOT item context: name=reserved_31_16; reset=0; access=reserved.",
      "evidence_terms": [],
      "id": "RTL-0101",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.DIVISOR.fields.reserved_31_16",
      "ssot_context": {
        "access": "reserved",
        "name": "reserved_31_16",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.DIVISOR.fields.reserved_31_16"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
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
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "STATUS width matches SSOT value 32",
        "STATUS reset behavior matches SSOT value 0",
        "STATUS access policy ro is implemented without read/write shortcuts",
        "STATUS decode uses SSOT address/offset 8"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.STATUS.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.\nSSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=8.",
      "evidence_terms": [],
      "id": "RTL-0102",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
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
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field STATUS.running",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.STATUS.fields.running",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "running reset behavior matches SSOT value 0",
        "running access policy ro is implemented without read/write shortcuts",
        "running readback returns implemented RTL state when readable",
        "running write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.STATUS.fields.running.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.\nSSOT item context: name=running; reset=0; access=ro.",
      "evidence_terms": [],
      "id": "RTL-0103",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.STATUS.fields.running",
      "ssot_context": {
        "access": "ro",
        "name": "running",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.STATUS.fields.running"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field STATUS.locked",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.STATUS.fields.locked",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "locked reset behavior matches SSOT value 0",
        "locked access policy ro is implemented without read/write shortcuts",
        "locked readback returns implemented RTL state when readable",
        "locked write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.STATUS.fields.locked.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.\nSSOT item context: name=locked; reset=0; access=ro.",
      "evidence_terms": [],
      "id": "RTL-0104",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.STATUS.fields.locked",
      "ssot_context": {
        "access": "ro",
        "name": "locked",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.STATUS.fields.locked"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field STATUS.irq_pending",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.STATUS.fields.irq_pending",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "irq_pending reset behavior matches SSOT value 0",
        "irq_pending access policy ro is implemented without read/write shortcuts",
        "irq_pending readback returns implemented RTL state when readable",
        "irq_pending write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.STATUS.fields.irq_pending.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.\nSSOT item context: name=irq_pending; reset=0; access=ro.",
      "evidence_terms": [],
      "id": "RTL-0105",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.STATUS.fields.irq_pending",
      "ssot_context": {
        "access": "ro",
        "name": "irq_pending",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.STATUS.fields.irq_pending"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field STATUS.reserved_31_3",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.STATUS.fields.reserved_31_3",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "reserved_31_3 reset behavior matches SSOT value 0",
        "reserved_31_3 access policy reserved is implemented without read/write shortcuts",
        "reserved_31_3 readback returns implemented RTL state when readable",
        "reserved_31_3 write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.STATUS.fields.reserved_31_3.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.\nSSOT item context: name=reserved_31_3; reset=0; access=reserved.",
      "evidence_terms": [],
      "id": "RTL-0106",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.STATUS.fields.reserved_31_3",
      "ssot_context": {
        "access": "reserved",
        "name": "reserved_31_3",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.STATUS.fields.reserved_31_3"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register INTCLR",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.INTCLR",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "INTCLR width matches SSOT value 32",
        "INTCLR reset behavior matches SSOT value 0",
        "INTCLR access policy wo is implemented without read/write shortcuts",
        "INTCLR decode uses SSOT address/offset 12"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.INTCLR.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.INTCLR.\nSSOT item context: name=INTCLR; width=32; reset=0; access=wo; offset=12.",
      "evidence_terms": [],
      "id": "RTL-0107",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.INTCLR",
      "ssot_context": {
        "access": "wo",
        "name": "INTCLR",
        "offset": "12",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.INTCLR"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field INTCLR.clear_irq",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.INTCLR.fields.clear_irq",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "clear_irq reset behavior matches SSOT value 0",
        "clear_irq access policy wo is implemented without read/write shortcuts",
        "clear_irq readback returns implemented RTL state when readable",
        "clear_irq write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.INTCLR.fields.clear_irq.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.INTCLR.\nSSOT item context: name=clear_irq; reset=0; access=wo.",
      "evidence_terms": [],
      "id": "RTL-0108",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.INTCLR.fields.clear_irq",
      "ssot_context": {
        "access": "wo",
        "name": "clear_irq",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.INTCLR.fields.clear_irq"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.field",
      "content": "Implement field INTCLR.reserved_31_1",
      "criteria": [
        "Field bit range, mask, and write strobe decode match SSOT",
        "Field reset/access policy matches SSOT",
        "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
        "Reserved fields read as the SSOT value and ignore writes",
        "Field side effects are connected to owning control/status logic",
        "Traceability keeps source_ref registers.register_list.INTCLR.fields.reserved_31_1",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "reserved_31_1 reset behavior matches SSOT value 0",
        "reserved_31_1 access policy reserved is implemented without read/write shortcuts",
        "reserved_31_1 readback returns implemented RTL state when readable",
        "reserved_31_1 write/clear side effects are connected to owning control/status logic"
      ],
      "detail": "Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.\nSSOT ref: registers.register_list.INTCLR.fields.reserved_31_1.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.INTCLR.\nSSOT item context: name=reserved_31_1; reset=0; access=reserved.",
      "evidence_terms": [],
      "id": "RTL-0109",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.INTCLR.fields.reserved_31_1",
      "ssot_context": {
        "access": "reserved",
        "name": "reserved_31_1",
        "reset": "0"
      },
      "ssot_refs": [
        "registers.register_list.INTCLR.fields.reserved_31_1"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 11,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "interrupts.sources",
      "content": "Implement interrupt item TERMINAL_EVENT",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref interrupts.sources.TERMINAL_EVENT",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv",
        "TERMINAL_EVENT clear behavior matches SSOT clear policy INTCLR.clear_irq W1C"
      ],
      "detail": "This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: interrupts.sources.TERMINAL_EVENT.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via interrupts.\nSSOT item context: name=TERMINAL_EVENT; clear=INTCLR.clear_irq W1C.",
      "evidence_terms": [],
      "id": "RTL-0110",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "interrupts.sources.TERMINAL_EVENT",
      "ssot_context": {
        "clear": "INTCLR.clear_irq W1C",
        "name": "TERMINAL_EVENT"
      },
      "ssot_refs": [
        "interrupts.sources.TERMINAL_EVENT"
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
        "reason": "Owner RTL file is missing: rtl/clkdiv_regs.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "error_handling.recovery",
      "content": "Implement error/fault item recovery_0",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref error_handling.recovery.recovery_0",
        "Primary implementation evidence is in rtl/clkdiv_regs.sv"
      ],
      "detail": "This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: error_handling.recovery.recovery_0.\nOwner: clkdiv_regs in rtl/clkdiv_regs.sv via error_handling.\nSSOT item context: action=legal APB access.",
      "evidence_terms": [],
      "id": "RTL-0122",
      "owner_file": "rtl/clkdiv_regs.sv",
      "owner_module": "clkdiv_regs",
      "priority": "high",
      "required": true,
      "source_ref": "error_handling.recovery.recovery_0",
      "ssot_context": {
        "action": "legal APB access"
      },
      "ssot_refs": [
        "error_handling.recovery.recovery_0"
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
... <truncated 30780 chars>

Current packet Markdown (rtl/authoring_packets/module__clkdiv_regs.md):
# RTL Authoring Packet: module__clkdiv_regs

- Kind: module
- Owner module: clkdiv_regs
- Owner file: rtl/clkdiv_regs.sv
- Task count: 34
- Required tasks: 34

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 34
- Human-locked open tasks: 0
- Owner refs: error_handling, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, registers.register_list.CTRL, registers.register_list.DIVISOR, registers.register_list.INTCLR, registers.register_list.STATUS
- SSOT connection contracts:
  - clkdiv_regs.clk_i <= clk_i (sub_modules[0].connections[0])
  - clkdiv_regs.rst_ni <= rst_ni (sub_modules[0].connections[1])
  - clkdiv_regs.enable_o <= enable (sub_modules[0].connections[2])
  - clkdiv_regs.divisor_o <= active_divisor (sub_modules[0].connections[3])
  - clkdiv_regs.irq_pending_i <= irq_pending (sub_modules[0].connections[4])
  - clkdiv_regs.clk_i <= clk_i (integration.connections[0])
  - clkdiv_regs.rst_ni <= rst_ni (integration.connections[1])
  - clkdiv_regs.paddr <= paddr (integration.connections[2])
  - clkdiv_regs.psel <= psel (integration.connections[3])
  - clkdiv_regs.penable <= penable (integration.connections[4])
  - clkdiv_regs.pwrite <= pwrite (integration.connections[5])
  - clkdiv_regs.pwdata <= pwdata (integration.connections[6])

## Tasks

### RTL-0028: Implement APB register/status block

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Implement CTRL, DIVISOR, STATUS, INTCLR, APB one-cycle pready/prdata/pslverr behavior, reserved-field policy, divisor zero coercion, and irq pending clear/set policy.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CLKDIV_REGS.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Register reset, access, bit ranges, write effects, and reserved fields match registers.register_list
  - Unsupported address and RO write pslverr behavior matches error_handling
  - irq_o reflects irq_pending && irq_enable
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - Semantic source_refs covered: error_handling, interrupts, io_list.interfaces.apb_slave, registers.register_list
- SSOT refs: error_handling, interrupts, io_list.interfaces.apb_slave, registers.register_list, workflow_todos.rtl-gen[1]

### RTL-0095: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.
SSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=0.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 0
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CTRL

### RTL-0096: Implement field CTRL.enable

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.enable.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.
SSOT item context: name=enable; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.enable
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - enable reset behavior matches SSOT value 0
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.enable

### RTL-0097: Implement field CTRL.irq_enable

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.irq_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.irq_enable.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.
SSOT item context: name=irq_enable; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.irq_enable
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - irq_enable reset behavior matches SSOT value 0
  - irq_enable access policy rw is implemented without read/write shortcuts
  - irq_enable readback returns implemented RTL state when readable
  - irq_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.irq_enable

### RTL-0098: Implement field CTRL.reserved_31_2

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.reserved_31_2
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.reserved_31_2.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.
SSOT item context: name=reserved_31_2; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.reserved_31_2
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - reserved_31_2 reset behavior matches SSOT value 0
  - reserved_31_2 access policy reserved is implemented without read/write shortcuts
  - reserved_31_2 readback returns implemented RTL state when readable
  - reserved_31_2 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.reserved_31_2

### RTL-0099: Implement CSR/register DIVISOR

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.DIVISOR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DIVISOR.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.
SSOT item context: name=DIVISOR; width=32; reset=2; access=rw; offset=4.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DIVISOR
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - DIVISOR width matches SSOT value 32
  - DIVISOR reset behavior matches SSOT value 2
  - DIVISOR access policy rw is implemented without read/write shortcuts
  - DIVISOR decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.DIVISOR

### RTL-0100: Implement field DIVISOR.divisor

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DIVISOR.fields.divisor
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DIVISOR.fields.divisor.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.
SSOT item context: name=divisor; reset=2; access=rw.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DIVISOR.fields.divisor
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - divisor reset behavior matches SSOT value 2
  - divisor access policy rw is implemented without read/write shortcuts
  - divisor readback returns implemented RTL state when readable
  - divisor write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DIVISOR.fields.divisor

### RTL-0101: Implement field DIVISOR.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DIVISOR.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DIVISOR.fields.reserved_31_16.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.
SSOT item context: name=reserved_31_16; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DIVISOR.fields.reserved_31_16
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy reserved is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DIVISOR.fields.reserved_31_16

### RTL-0102: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.
SSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=8.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.STATUS

### RTL-0103: Implement field STATUS.running

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.running
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.running.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.
SSOT item context: name=running; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.running
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - running reset behavior matches SSOT value 0
  - running access policy ro is implemented without read/write shortcuts
  - running readback returns implemented RTL state when readable
  - running write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.running

### RTL-0104: Implement field STATUS.locked

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.locked
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.locked.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.
SSOT item context: name=locked; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented
... <truncated 26030 chars>