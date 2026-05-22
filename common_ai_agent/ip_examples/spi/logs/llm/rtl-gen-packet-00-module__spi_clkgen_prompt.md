RTL-GEN PACKET MODE for spi. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "spi/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "spi/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "spi/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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

Current packet: module__spi_clkgen
kind: module
work queue: 1/1 active packets (14 closed packets skipped from 20 total)
batch limit: 1; deferred active packets after this batch: 5
owner_module: spi_clkgen
owner_file: rtl/spi_clkgen.sv

SSOT observable latency contract:
{
  "cycle_model.latency": {
    "apb_read": {
      "description": "PRDATA/PREADY returned in same or next cycle; no multi-cycle wait-state required",
      "max_cycles": 1,
      "min_cycles": 0
    },
    "apb_write": {
      "description": "Register writes accepted in same or next cycle",
      "max_cycles": 1,
      "min_cycles": 0
    },
    "frame_launch_to_first_sclk_toggle": {
      "description": "Depends on prescale divisor",
      "max_cycles": null,
      "min_cycles": 1
    },
    "frame_total": {
      "description": "Proportional to frame_bits and prescale, plus APB/control overhead",
      "max_cycles": null,
      "min_cycles": 2
    }
  },
  "cycle_model.pipeline": [
    {
      "action": "Program mode/prescale/CS and push TX words",
      "cycle": "t",
      "stage": "S0_APB_CFG"
    },
    {
      "action": "Evaluate launch preconditions and latch frame context",
      "cycle": "t+0..t+1",
      "stage": "S1_LAUNCH_CHECK"
    },
    {
      "action": "Drive selected chip select active-low",
      "cycle": "next",
      "stage": "S2_ASSERT_CS"
    },
    {
      "action": "Generate sclk_o edges and launch MOSI bits",
      "cycle": "repeating",
      "stage": "S3_SHIFT"
    },
    {
      "action": "Sample MISO/loopback bit and advance bit_index",
      "cycle": "repeating",
      "stage": "S4_SAMPLE"
    },
    {
      "action": "Push RX word if possible, update done/errors/pending, manage CS hold/deassert",
      "cycle": "terminal",
      "stage": "S5_COMPLETE"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": null,
  "timing.latency_budget": {
    "apb_access_cycles": {
      "max": 1,
      "min": 0
    },
    "launch_to_done_cycles_formula": "(data_width_bits*2*(prescale+1)) + control_overhead"
  }
}

Locked SSOT YAML excerpt (spi/yaml/spi.ssot.yaml):
top_module:
  name: "spi"
  file: "rtl/spi.sv"
  version: "1.0"
  type: "peripheral"
  description: "APB-lite controlled SPI master with programmable frame format, TX/RX FIFOs, interrupting, and debug observability."
  reference_spec: "Project requirement seed: spi/req/spi_requirements.md"
  target:
    technology: "generic"
    clock_freq_mhz: 100
    area_um2: null
    power_mw: null

sub_modules:
  - name: "spi_regs"
    file: "rtl/spi_regs.sv"
    ownership: "manifest"
    ssot_gen: true
    implements:
      - "registers.register_list"
      - "interrupts"
      - "error_handling"
      - "io_list.interfaces.apb_slave"
    source_sections: ["registers", "interrupts", "error_handling", "io_list"]
    register_refs: ["registers.register_list"]
    description: "APB register decode, policy checks, sticky/status update plumbing"
  - name: "spi_fifo"
    file: "rtl/spi_fifo.sv"
    ownership: "manifest"
    ssot_gen: true
    implements:
      - "memory.instances"
      - "cycle_model.backpressure"
      - "dataflow"
    source_sections: ["memory", "cycle_model", "dataflow"]
    dataflow_refs: ["dataflow.tx_path", "dataflow.rx_path"]
    cycle_model_refs: ["cycle_model.backpressure"]
    description: "TX/RX FIFO storage and level tracking"
  - name: "spi_clkgen"
    file: "rtl/spi_clkgen.sv"
    ownership: "manifest"
    ssot_gen: true
    implements:
      - "parameters.PRESCALE_WIDTH"
      - "cycle_model.handshake_rules"
      - "timing"
    source_sections: ["parameters", "cycle_model", "timing"]
    cycle_model_refs: ["cycle_model.handshake_rules", "cycle_model.pipeline"]
    description: "SCLK waveform generation from PCLK prescale"
  - name: "spi_shift"
    file: "rtl/spi_shift.sv"
    ownership: "manifest"
    ssot_gen: false
    implements:
      - "function_model.transactions"
      - "cycle_model.pipeline"
      - "fsm.channel_level"
      - "features"
    source_sections: ["function_model", "cycle_model", "fsm", "features"]
    function_model_refs: ["function_model.transactions"]
    cycle_model_refs: ["cycle_model.pipeline", "cycle_model.ordering"]
    fsm_refs: ["fsm.channel_level"]
    description: "Frame launch/shift/sample engine and chip-select control"
  - name: "spi_int"
    file: "rtl/spi_int.sv"
    ownership: "manifest"
    ssot_gen: true
    implements:
      - "interrupts"
      - "registers.register_list"
      - "error_handling"
    source_sections: ["interrupts", "registers", "error_handling"]
    description: "Interrupt pending/mask/clear logic and irq_o generation"

decomposition:
  units:
    - id: "csr_decode"
      kind: "control"
      source_refs: ["registers.register_list", "io_list.interfaces.apb_slave"]
      rtl_candidates: ["spi_regs"]
      verification_impact: ["test_requirements.scenarios.SC_APB_CONFIG"]
    - id: "fifo_buffering"
      kind: "datapath"
      source_refs: ["memory.instances", "dataflow"]
      rtl_candidates: ["spi_fifo"]
      verification_impact: ["test_requirements.scenarios.SC_FIFO_LIMITS"]
    - id: "serial_engine"
      kind: "datapath/control"
      source_refs: ["function_model.transactions", "cycle_model", "fsm.channel_level"]
      rtl_candidates: ["spi_shift", "spi_clkgen"]
      verification_impact: ["test_requirements.scenarios.SC_BASIC_TRANSFER", "test_requirements.scenarios.SC_CPOL_CPHA_SWEEP"]

rtl_contract:
  top_owner: "spi"
  architectural_state_owner: "spi_shift"
  register_owner: "spi_regs"
  fifo_owner: "spi_fifo"
  interrupt_owner: "spi_int"
  clocking_owner: "spi_clkgen"
  integration_notes:
    - "All sequential logic uses PCLK only; sclk_o is generated waveform and not an internal clock domain."
    - "PSLVERR is asserted on access cycle for illegal APB address, unsupported byte strobe, or access-policy violation."

parameters:
  - name: "APB_ADDR_WIDTH"
    default: 12
    type: int
    description: "APB address width"
    drives: ["rtl/spi_regs.sv", "rtl/spi.sv"]
  - name: "APB_DATA_WIDTH"
    default: 32
    type: int
    description: "APB data width"
    drives: ["rtl/spi_regs.sv", "rtl/spi.sv"]
  - name: "DATA_WIDTH"
    default: 8
    type: int
    description: "Default frame width; runtime legal range controlled by CTRL.data_width_m1"
    drives: ["rtl/spi_shift.sv", "rtl/spi_fifo.sv"]
  - name: "FIFO_DEPTH"
    default: 16
    type: int
    description: "Depth of TX and RX FIFOs; must be power of two"
    drives: ["rtl/spi_fifo.sv", "rtl/spi_regs.sv"]
  - name: "NUM_CS"
    default: 4
    type: int
    description: "Number of chip-select outputs"
    drives: ["rtl/spi_shift.sv", "rtl/spi.sv"]
  - name: "PRESCALE_WIDTH"
    default: 16
    type: int
    description: "Width of programmable prescale divisor"
    drives: ["rtl/spi_clkgen.sv", "rtl/spi_regs.sv"]
  - name: "CPOL_RESET"
    default: 0
    type: int
    description: "Reset value for CTRL.cpol"
    drives: ["rtl/spi_regs.sv", "rtl/spi_shift.sv"]
  - name: "CPHA_RESET"
    default: 0
    type: int
    description: "Reset value for CTRL.cpha"
    drives: ["rtl/spi_regs.sv", "rtl/spi_shift.sv"]
  - name: "LSB_FIRST_RESET"
    default: 0
    type: int
    description: "Reset value for CTRL.lsb_first"
    drives: ["rtl/spi_regs.sv", "rtl/spi_shift.sv"]
  - name: "PCLK_FREQ_MHZ"
    default: 100
    type: int
    description: "Nominal input clock frequency"
    drives: ["timing", "sdc/spi.sdc"]

io_list:
  clock_domains:
    - name: "pclk"
      frequency_mhz: 100
      description: "Primary APB and engine clock"
      ports:
        - { name: "PCLK", width: 1, direction: "input", description: "Peripheral clock" }
  resets:
    - name: "presetn"
      polarity: "active_low"
      sync_async: "async_assert_sync_deassert"
      description: "Global reset"
      ports:
        - { name: "PRESETn", width: 1, direction: "input", description: "Active-low reset" }
  interfaces:
    - name: "apb_slave"
      type: "APB4-lite"
      role: "slave"
      description: "Control/status register interface"
      ports:
        - { name: "PADDR", width: 12, direction: "input", description: "Byte address" }
        - { name: "PSEL", width: 1, direction: "input", description: "Peripheral select" }
        - { name: "PENABLE", width: 1, direction: "input", description: "Enable phase" }
        - { name: "PWRITE", width: 1, direction: "input", description: "Write/read select" }
        - { name: "PWDATA", width: 32, direction: "input", description: "Write data" }
        - { name: "PSTRB", width: 4, direction: "input", description: "Byte strobes" }
        - { name: "PRDATA", width: 32, direction: "output", description: "Read data" }
        - { name: "PREADY", width: 1, direction: "output", description: "Transfer ready" }
        - { name: "PSLVERR", width: 1, direction: "output", description: "Access error" }
    - name: "spi_master"
      type: "custom_spi"
      role: "master"
      description: "External SPI pins"
      ports:
        - { name: "sclk_o", width: 1, direction: "output", description: "SPI serial clock" }
        - { name: "mosi_o", width: 1, direction: "output", description: "SPI master out" }
        - { name: "miso_i", width: 1, direction: "input", description: "SPI master in" }
        - { name: "csn_o", width: 4, direction: "output", description: "Active-low chip selects" }
    - name: "irq"
      type: "custom"
      role: "output"
      description: "Combined interrupt"
      ports:
        - { name: "irq_o", width: 1, direction: "output", description: "Masked interrupt output" }

features:
  - name: "APB-programmed frame transfer"
    trigger: "SW writes CTRL.start pulse with CTRL.enable=1 and legal launch conditions"
    datapath: "TX FIFO word -> shift register -> MOSI; sampled MISO bits -> RX shift register -> RX FIFO"
    control: "IDLE->LOAD->ASSERT_CS->SHIFT->COMPLETE"
    output: "Serialized frame on mosi_o/sclk_o and optional received frame in RX FIFO"
  - name: "Programmable SPI mode and bit order"
    trigger: "CTRL.{cpol,cpha,lsb_first,data_width_m1} programmed"
    datapath: "Edge select controls launch/sample timing; shift direction depends on lsb_first"
    control: "Mode latched per frame at launch"
    output: "Protocol-compliant phase/polarity behavior and chosen bit ordering"
  - name: "Interrupt and sticky error reporting"
    trigger: "Status/error/fifo events"
    datapath: "Raw event -> INT_PENDING, mask via INT_MASK -> irq_o"
    control: "Sticky bits clear on INT_CLEAR W1C; level bits follow source levels"
    output: "irq_o and software-readable status/error telemetry"

dataflow:
  tx_path:
    source: "APB write to TXDATA"
    enqueue: "Accepted when TX FIFO not full; otherwise dropped and tx_overrun set"
    sequence: "TXDATA write -> tx_fifo push -> frame launch pops word -> shift register"
  rx_path:
    source: "miso_i sampled during active frame"
    enqueue: "At frame complete, sampled word pushed if RX FIFO not full; else dropped and rx_overrun set"
    sequence: "sample bits -> rx_shift_reg -> rx_fifo push -> APB read RXDATA pop"
  control_path:
    launch_gate: "enable && start_pulse && !busy && tx_fifo_not_empty && legal_cs && legal_width"
    completion: "done pulse and status update when last configured bit is sampled"
    continuous_cs: "When continuous_cs=1 and next frame launches back-to-back with legal mode, csn_o remains asserted for same cs_sel"

function_model:
  purpose: "Executable behavioral contract for SPI transactions independent of exact cycle latency."
  state_variables:
    - { name: "ctrl_enable", source: "registers.CTRL.enable", reset: 0, description: "Global transfer enable" }
    - { name: "ctrl_mode", source: "registers.CTRL.{cpol,cpha,lsb_first,continuous_cs,loopback}", reset: "{cpol:CPOL_RESET,cpha:CPHA_RESET,lsb_first:LSB_FIRST_RESET,continuous_cs:0,loopback:0}", description: "Latched transfer mode" }
    - { name: "active_cs", source: "registers.CTRL.cs_sel", reset: 0, description: "Selected chip-select index" }
    - { name: "frame_bits", source: "registers.CTRL.data_width_m1+1", reset: 8, description: "Runtime frame bit count (legal 4..32)" }
    - { name: "prescale_div", source: "registers.PRESCALE.divisor", reset: 0, description: "SCLK half-period divisor" }
    - { name: "tx_fifo", source: "memory.instances.tx_fifo", reset: "empty", description: "Pending TX frames" }
    - { name: "rx_fifo", source: "memory.instances.rx_fifo", reset: "empty", description: "Received RX frames" }
    - { name: "busy", source: "registers.STATUS.busy", reset: 0, description: "Frame in progress" }
    - { name: "sticky_errors", source: "registers.STATUS.{tx_overrun,rx_overrun,rx_underrun,mode_fault,illegal_access}", reset: 0, description: "Sticky error latches" }
    - { name: "int_pending", source: "registers.INT_PENDING", reset: 0, description: "Pending interrupt sources" }
  transactions:
    - id: "FM_APB_TX_PUSH"
      name: "apb_write_txdata"
      preconditions:
        - "APB write handshake to TXDATA"
      inputs:
        - "PWDATA[DATA_WIDTH-1:0]"
      outputs:
        - "TX FIFO occupancy increments by one when not full"
      side_effects:
        - "If tx_fifo full, payload is discarded and STATUS.tx_overrun set"
        - "tx_empty/tx_full level indicators update"
      error_cases:
        - { condition: "unsupported PSTRB for TXDATA width", result: "PSLVERR asserted and STATUS.illegal_access set" }
    - id: "FM_FRAME_LAUNCH"
      name: "launch_frame"
      preconditions:
        - "CTRL.start pulse observed"
        - "ctrl_enable == 1"
        - "busy == 0"
        - "tx_fifo not empty"
        - "cs_sel in [0, NUM_CS-1]"
        - "frame_bits in [4, 32]"
      outputs:
        - "busy transitions to 1"
        - "One TX word is consumed from TX FIFO for shift register load"
      side_effects:
        - "csn_o drives exactly one active-low bit at selected CS"
        - "SCLK idle level driven per CPOL before first active edge"
      error_cases:
        - { condition: "cs_sel illegal or frame_bits illegal", result: "No frame activity; STATUS.mode_fault set; pending mode fault interrupt source raised" }
        - { condition: "CTRL.enable == 0 or tx_fifo empty or busy==1", result: "Launch suppressed without consuming TX FIFO" }
    - id: "FM_SHIFT_SAMPLE"
      name: "shift_and_sample_bits"
      preconditions:
        - "busy == 1"
      inputs:
        - "miso_i sampled on mode-dependent sample edges or internal mosi_o if loopback=1"
      outputs:
        - "mosi_o presents serialized transmit bits with configured bit order"
        - "rx_shift_reg accumulates sampled bits"
      side_effects:
        - "bit_index progresses from 0 to frame_bits-1"
        - "done asserted when terminal sample edge occurs"
      error_cases:
        - { condition: "none during legal frame", result: "normal completion" }
    - id: "FM_FRAME_COMPLETE"
      name: "complete_frame_and_store_rx"
      preconditions:
        - "terminal sample edge reached"
      outputs:
        - "busy transitions to 0"
        - "STATUS.done pulse/latched event generated"
      side_effects:
        - "If RX FIFO has space, received frame pushed; else discard and STATUS.rx_overrun set"
        - "CS deasserts to CS_IDLE unless continuous_cs holds across back-to-back frame"
        - "Interrupt pending bits update for done and FIFO level"
      error_cases:
        - { condition: "RX FIFO full", result: "received word dropped, rx_overrun sticky set" }
    - id: "FM_APB_RX_POP"
      name: "apb_read_rxdata"
      preconditions:
        - "APB read handshake to RXDATA"
      outputs:
        - "Returns oldest RX word when FIFO non-empty"
      side_effects:
        - "RX FIFO occupancy decrements on successful pop"
      error_cases:
        - { condition: "RX FIFO empty", result: "Read returns zero and STATUS.rx_underrun set" }
    - id: "FM_INT_CLEAR"
      name: "w1c_interrupt_and_status_clear"
      preconditions:
        - "APB write handshake to INT_CLEAR"
      outputs:
        - "Selected sticky pending/status bits cleared"
      side_effects:
        - "FIFO level-derived pending bits remain level-sensitive and unaffected by W1C"
      error_cases:
        - { condition: "write to read-only register or bad byte strobes", result: "PSLVERR asserted and STATUS.illegal_access set" }
  invariants:
    - "Only one csn_o bit may be active-low during an active frame."
    - "No frame launch consumes TX FIFO unless all launch preconditions are true."
    - "irq_o equals OR(INT_PENDING & INT_MASK) at all times."
    - "sclk_o is a generated output waveform; no internal sequential process is clocked by sclk_o."
    - "Sticky bits clear only via reset or INT_CLEAR W1C semantics."
  reference_model_hint: "tb-gen scoreboard should model FIFO queues, mode-dependent edge behavior, bit order, and sticky/level interrupt semantics from these transactions."

cycle_model:
  purpose: "Cycle-level timing and handshake contract for APB access and SPI serial engine"
  executable: "pymtl3"
  backend_policy: "Use Python behavioral model for expected values and cycle checkers for ready/valid, edge timing, and status updates."
  clock: "PCLK"
  reset:
    assertion: "PRESETn low asynchronously clears control/FIFOs/status/interrupt pending and drives csn_o to CS_IDLE"
    deassertion: "State is valid after first rising PCLK edge following synchronized PRESETn release"
  latency:
    apb_read: { min_cycles: 0, max_cycles: 1, description: "PRDATA/PREADY returned in same or next cycle; no multi-cycle wait-state required" }
    apb_write: { min_cycles: 0, max_cycles: 1, description: "Register writes accepted in same or next cycle" }
    frame_launch_to_first_sclk_toggle: { min_cycles: 1, max_cycles: null, description: "Depends on prescale divisor" }
    frame_total: { min_cycles: 2, max_cycles: null, description: "Proportional to frame_bits and prescale, plus APB/control overhead" }
  handshake_rules:
    - { signal: "APB", rule: "Transfer occurs when PSEL && PENABLE && PREADY; PSLVERR valid in same transfer." }
    - { signal: "CTRL.start", rule: "Sampled as pulse request; hardware may auto-clear start bit after acceptance." }
    - { signal: "launch_gate", rule: "Shift FSM leaves IDLE only when all launch preconditions are simultaneously true." }
    - { signal: "sclk_o", rule: "Half-period equals (PRESCALE.divisor+1) PCLK cycles; CPOL controls idle level." }
    - { signal: "sample_edge", rule: "CPHA selects whether first active edge launches then samples or samples then launches." }
  pipeline:
    - { stage: "S0_APB_CFG", cycle: "t", action: "Program mode/prescale/CS and push TX words" }
    - { stage: "S1_LAUNCH_CHECK", cycle: "t+0..t+1", action: "Evaluate launch preconditions and latch frame context" }
    - { stage: "S2_ASSERT_CS", cycle: "next", action: "Drive selected chip select active-low" }
    - { stage: "S3_SHIFT", cycle: "repeating", action: "Generate sclk_o edges and launch MOSI bits" }
    - { stage: "S4_SAMPLE", cycle: "repeating", action: "Sample MISO/loopback bit and advance bit_index" }
    - { stage: "S5_COMPLETE", cycle: "terminal", action: "Push RX word if possible, update done/errors/pending, manage CS hold/deassert" }
  ordering:
    - "For each frame, TX dequeue precedes first MOSI launch edge."
    - "Final RX sample precedes done event and interrupt pending update for completion."
    - "INT_CLEAR W1C effects apply after the write transfer edge and before next irq_o observation edge."
  backpressure:
    - "TX backpressure appears as tx_full; writes are dropped with tx_overrun when full."
    - "RX backpressure appears as rx_full at completion; received frame is dropped with rx_overrun when full."
  performance:
    throughput: "One frame every frame_bits*2*(divisor+1) PCLK cycles in steady state, excluding optional inter-frame gap"
    max_sclk_hz_formula: "PCLK_FREQ_MHZ*1e6 / (2*(PRESCALE+1))"
  observability:
    - "Probe launch_accept, sample_edge, shift_edge, bit_index, cs_active, tx_fifo_level, rx_fifo_level, done_event"

clock_reset_domains:
  domains:
    - { name: "pclk", frequency_mhz: 100, description: "Single synchronous domain" }
  reset_scheme:
    signal: "PRESETn"
    polarity: "active_low"
    type: "async_assert_sync_deassert"

cdc_requirements:
  crossings: []
  synchronizers: []
  note: "Single clock domain; no CDC crossings allowed in this revision"

rdc_requirements:
  crossings: []
  synchronizers: []
  note: "Single reset domain; no RDC crossings"

registers:
  config:
    register_width: 32
    addr_width: 12
    byte_addressable: true
  register_list:
    - name: "CTRL"
      offset: 0x000
      width: 32
      access: "rw"
      reset: 0x00000000
      description: "Control register"
      fields:
        - { name: "enable", bits: [0,0], access: "rw", reset: 0x0, description: "Enable transfer launches" }
        - { name: "start", bits: [1,1], access: "wo", reset: 0x0, description: "Start pulse request" }
        - { name: "cpol", bits: [2,2], access: "rw", reset: 0x0, description: "Clock polarity" }
        - { name: "cpha", bits: [3,3], access: "rw", reset: 0x0, description: "Clock phase" }
        - { name: "lsb_first", bits: [4,4], access: "rw", reset: 0x0, description: "1=LSB first, 0=MSB first" }
        - { name: "continuous_cs", bits: [5,5], access: "rw", reset: 0x0, description: "Hold CS across back-to-back frames" }
        - { name: "loopback", bits: [6,6], access: "rw", reset: 0x0, description: "Internal MOSI->MISO loopback" }
        - { name: "soft_reset", bits: [7,7], access: "wo", reset: 0x0, description: "Pulse to clear FIFOs/status and return idle" }
        - { name: "cs_sel", bits: [10,8], access: "rw", reset: 0x0, description: "Active chip-select index" }
        - { name: "data_width_m1", bits: [15,11], access: "rw", reset: 0x7, description: "Frame width minus one; legal width 4..32" }
    - name: "STATUS"
      offset: 0x004
      width: 32
      access: "ro"
      reset: 0x00000012
      description: "Status and sticky error bits"
      fields:
        - { name: "busy", bits: [0,0], access: "ro", reset: 0x0, description: "Transfer in progress" }
        - { name: "tx_full", bits: [1,1], access: "ro", reset: 0x0, description: "TX FIFO full level" }
        - { name: "tx_empty", bits: [2,2], access: "ro", reset: 0x1, description: "TX FIFO empty level" }
        - { name: "rx_full", bits: [3,3], access: "ro", reset: 0x0, description: "RX FIFO full level" }
        - { name: "rx_empty", bits: [4,4], access: "ro", reset: 0x1, description: "RX FIFO empty level" }
        - { name: "done", bits: [5,5], access: "ro", reset: 0x0, description: "Frame-complete sticky event" }
        - { name: "tx_overrun", bits: [6,6], access: "ro", reset: 0x0, description: "TX write while full" }
        - { name: "rx_overrun", bits: [7,7], access: "ro", reset: 0x0, description: "RX push while full" }
        - { name: "rx_underrun", bits: [8,8], access: "ro", reset: 0x0, description: "RX read while empty" }
        - { name: "mode_fault", bits: [9,9], access: "ro", reset: 0x0, description: "Illegal launch config" }
        - { name: "illegal_access", bits: [10,10], access: "ro", reset: 0x0, description: "Illegal APB access" }
        - { name: "cs_active", bits: [11,11], access: "ro", reset: 0x0, description: "Any CS asserted" }
    - name: "PRESCALE"
      offset: 0x008
      width: 32
      access: "rw"
      reset: 0x00000000
      description: "SCLK prescale divisor"
      fields:
        - { name: "divisor", bits: [15,0], access: "rw", reset: 0x0000, description: "Half-period cycles = divisor+1" }
    - name: "TXDATA"
      offset: 0x00C
      width: 32
      access: "wo"
      reset: 0x00000000
      description: "TX FIFO push payload"
      fields:
        - { name: "tx_payload", bits: [31,0], access: "wo", reset: 0x0, description: "Frame data; only lower frame width bits used" }
    - name: "RXDATA"
      offset: 0x010
      width: 32
      access: "ro"
      reset: 0x00000000
      description: "RX FIFO pop payload"
      fields:
        - { name: "rx_payload", bits: [31,0], access: "ro", reset: 0x0, description: "Received frame data" }
    - name: "INT_MASK"
      offset: 0x014
      width: 32
      access: "rw"
      reset: 0x00000000
      description: "Interrupt enables"
      fields:
        - { name: "done_en", bits: [0,0], access: "rw", reset: 0x0, description: "Enable done interrupt" }
        - { name: "tx_overrun_en", bits: [1,1], access: "rw", reset: 0x0, description: "Enable tx_overrun interrupt" }
        - { name: "rx_overrun_en", bits: [2,2], access: "rw", reset: 0x0, description: "Enable rx_overrun interrupt" }
        - { name: "rx_underrun_en", bits: [3,3], access: "rw", reset: 0x0, description: "Enable rx_underrun interrupt" }
        - { name: "mode_fault_en", bits: [4,4], access: "rw", reset: 0x0, description: "Enable mode_fault interrupt" }
        - { name: "illegal_access_en", bits: [5,5], access: "rw", reset: 0x0, description: "Enable illegal_access interrupt" }
        - { name: "tx_empty_en", bits: [6,6], access: "rw", reset: 0x0, description: "Enable tx_empty level interrupt" }
        - { name: "rx_full_en", bits: [7,7], access: "rw", reset: 0x0, description: "Enable rx_full level interrupt" }
    - name: "INT_PENDING"
      offset: 0x018
      width: 32
      access: "ro"
      reset: 0x00000040
      description: "Raw pending interrupt sources"
      fields:
        - { name: "done_pend", bits: [0,0], access: "ro", reset: 0x0, description: "Sticky done pending" }
        - { name: "tx_overrun_pend", bits: [1,1], access: "ro", reset: 0x0, description: "Sticky tx_overrun pending" }
        - { name: "rx_overrun_pend", bits: [2,2], access: "ro", reset: 0x0, description: "Sticky rx_overrun pending" }
        - { name: "rx_underrun_pend", bits: [3,3], access: "ro", reset: 0x0, description: "Sticky rx_underrun pending" }
        - { name: "mode_fault_pend", bits: [4,4], access: "ro", reset: 0x0, description: "Sticky mode_fault pending" }
        - { name: "illegal_access_pend", bits: [5,5], access: "ro", reset: 0x0, description: "Sticky illegal_access pending" }
        - { name: "tx_empty_level", bits: [6,6], access: "ro", reset: 0x1, description: "Level pending mirrors tx_empty" }
        - { name: "rx_full_level", bits: [7,7], access: "ro", reset: 0x0, description: "Level pending mirrors rx_full" }
    - name: "INT_CLEAR"
      offset: 0x01C
      width: 32
      access: "wo"
      reset: 0x00000000
      description: "W1C for sticky pending/status bits"
      fields:
        - { name: "w1c", bits: [7,0], access: "wo", reset: 0x00, description: "Write 1 clears corresponding sticky bits; level bits unaffected" }
    - name: "CS_IDLE"
      offset: 0x020
      width: 32
      access: "rw"
      reset: 0x0000000F
      description: "Idle chip-select output value"
      fields:
        - { name: "cs_idle_val", bits: [7,0], access: "rw", reset: 0x0F, description: "Bit value driven on csn_o when idle" }
    - name: "DEBUG"
      offset: 0x024
      width: 32
      access: "ro"
      reset: 0x00000000
      description: "Debug counters/state"
      fields:
        - { name: "tx_count", bits: [4,0], access: "ro", reset: 0x0, description: "TX FIFO occupancy" }
        - { name: "rx_count", bits: [9,5], access: "ro", reset: 0x0, description: "RX FIFO occupancy" }
        - { name: "bit_index", bits: [15,10], access: "ro", reset: 0x0, description: "Current bit index in active frame" }
        - { name: "active_cs", bits: [18,16], access: "ro", reset: 0x0, description: "Currently asserted CS index" }

memory:
  instances:
    - { name: "tx_fifo", type: "sync_fifo", depth: 16, width: 32, read_ports: 1, write_ports: 1, latency: 0, description: "Transmit frame queue" }
    - { name: "rx_fifo", type: "sync_fifo", depth: 16, width: 32, read_ports: 1, write_ports: 1, latency: 0, description: "Receive frame queue" }
  note: "FIFO_DEPTH parameter scales both queues; occupancy exported via STATUS/DEBUG"

interrupts:
  sources:
    - { name: "DONE", bit: 0, type: "sticky_level", enable_reg: "INT_MASK.done_en", status_reg: "INT_PENDING.done_pend", clear: "INT_CLEAR.W1C[0]", description: "Frame complete event" }
    - { name: "TX_OVERRUN", bit: 1, type: "sticky_level", enable_reg: "INT_MASK.tx_overrun_en", status_reg: "INT_PENDING.tx_overrun_pend", clear: "INT_CLEAR.W1C[1]", description: "TX FIFO write while full" }
    - { name: "RX_OVERRUN", bit: 2, type: "sticky_level", enable_reg: "INT_MASK.rx_overrun_en", status_reg: "INT_PENDING.rx_overrun_pend", clear: "INT_CLEAR.W1C[2]", description: "RX FIFO full on completion" }
    - { name: "RX_UNDERRUN", bit: 3, type: "sticky_level", enable_reg: "INT_MASK.rx_underrun_en", status_reg: "INT_PENDING.rx_underrun_pend", clear: "INT_CLEAR.W1C[3]", description: "RXDATA read while empty" }
    - { name: "MODE_FAULT", bit: 4, type: "sticky_level", enable_reg: "INT_MASK.mode_fault_en", status_reg: "INT_PENDING.mode_fault_pend", clear: "INT_CLEAR.W1C[4]", description: "Illegal launch config" }
    - { name: "ILLEGAL_ACCESS", bit: 5, type: "sticky_level", enable_reg: "INT_MASK.illegal_access_en", status_reg: "INT_PENDING.illegal_access_pend", clear: "INT_CLEAR.W1C[5]", description: "Illegal APB access" }
    - { name: "TX_EMPTY", bit: 6, type: "level", enable_reg: "INT_MASK.tx_empty_en", status_reg: "INT_PENDING.tx_empty_level", clear: "not_w1c", description: "TX FIFO empty level" }
    - { name: "RX_FULL", bit: 7, type: "level", enable_reg: "INT_MASK.rx_full_en", status_reg: "INT_PENDING.rx_full_level", clear: "not_w1c", description: "RX FIFO full level" }
  output:
    signal: "irq_o"
    polarity: "active_high"
    type: "level"

fsm:
  channel_level:
    states:
      - "IDLE"
      - "CHECK_LAUNCH"
      - "ASSERT_CS"
      - "SHIFT_EDGE"
      - "SAMPLE_EDGE"
      - "COMPLETE"
      - "ERROR_SUPPRESS"
    transitions:
      - { from: "IDLE", to: "CHECK_LAUNCH", condition: "start_pulse" }
      - { from: "CHECK_LAUNCH", to: "ASSERT_CS", condition: "launch_gate_true" }
      - { from: "CHECK_LAUNCH", to: "ERROR_SUPPRESS", condition: "illegal_cs_or_width" }
      - { from: "CHECK_LAUNCH", to: "IDLE", condition: "launch_gate_false_without_fault" }
      - { from: "ASSERT_CS", to: "SHIFT_EDGE", condition: "prescale_tick" }
      - { from: "SHIFT_EDGE", to: "SAMPLE_EDGE", condition: "mode_edge_progress" }
      - { from: "SAMPLE_EDGE", to: "SHIFT_EDGE", condition: "bit_index_not_last" }
      - { from: "SAMPLE_EDGE", to: "COMPLETE", condition: "bit_index_last" }
      - { from: "COMPLETE", to: "ASSERT_CS", condition: "continuous_cs_and_next_launch_ready" }
      - { from: "COMPLETE", to: "IDLE", condition: "otherwise" }
      - { from: "ERROR_SUPPRESS", to: "IDLE", condition: "one_cycle_report_done" }

timing:
  target_clocks:
    - { domain: "pclk", freq_mhz: 100, duty_cycle: 50 }
  latency_budget:
    apb_access_cycles: { min: 0, max: 1 }
    launch_to_done_cycles_formula: "(data_width_bits*2*(prescale+1)) + control_overhead"
  protocol_timing:
    - "SCLK half-period is divisor+1 PCLK cycles."
    - "CPOL sets idle SCLK level when busy=0."
    - "CPHA selects first action edge; sampling and launching alternate each active edge."

power:
  domains:
    - { name: "PD_MAIN", supply: "VDD", description: "Primary logic domain for APB/SPI core" }
  power_states:
    - { name: "ON", description: "Clock active, transfers allowed when enabled" }
    - { name: "IDLE", description: "No active frame; static outputs per CS_IDLE/CPOL" }
    - { name: "RESET", description: "PRESETn asserted; state cleared" }
  clock_gating:
    - "Optional internal clock enable may gate shift datapath when busy=0; APB register interface remains responsive."

security:
  classification: "non-cryptographic peripheral control"
  assets:
    - "Correct APB register access policy"
    - "Integrity of serialized command/data words"
    - "Integrity of interrupt/error telemetry"
  threat_model:
    - { threat: "malformed APB accesses", mitigation: "PSLVERR + illegal_access sticky logging" }
    - { threat: "protocol misuse via illegal cs_sel/data_width", mitigation: "frame suppression + mode_fault sticky" }
    - { threat: "faulty software interrupt clear sequencing", mitigation: "W1C policy isolated to sticky bits; level sources are non-W1C" }
  privilege_assumptions:
    - "APB bus fabric enforces initiator permissions; SPI IP does not implement internal privilege levels."

error_handling:
  error_sources:
    - { name: "illegal_apb_address", detect: "decode miss", effect: "PSLVERR=1 for transfer; STATUS.illegal_access sticky set; INT_PENDING.illegal_access_pend sticky set" }
    - { name: "unsupported_write_strobe", detect: "PSTRB mismatch for accessed register policy", effect: "PSLVERR=1; STATUS.illegal_access set" }
    - { name: "access_policy_violation", detect: "write RO or read side-effect misuse policy", effect: "PSLVERR=1; STATUS.illegal_access set" }
    - { name: "tx_overrun", detect: "TXDATA write when tx_full=1", effect: "drop write data; set STATUS.tx_overrun and INT pending" }
    - { name: "rx_overrun", detect: "frame completion when rx_full=1", effect: "drop received frame; set STATUS.rx_overrun and INT pending" }
    - { name: "rx_underrun", detect: "RXDATA read when rx_empty=1", effect: "return zero; set STATUS.rx_underrun and INT pending" }
    - { name: "mode_fault", detect: "launch attempt with illegal cs_sel or data_width", effect: "suppress frame launch; set STATUS.mode_fault and INT pending" }
  recovery:
    - "Sticky status and sticky interrupt pending bits clear via INT_CLEAR W1C or reset."
    - "soft_reset pulse in CTRL clears FIFOs, busy, done, and sticky status bits while preserving programmable static configuration fields unless software rewrites them."

debug_observability:
  waveform_probes:
    - "spi_shift.state"
    - "spi_shift.bit_index"
    - "spi_shift.launch_accept"
    - "spi_clkgen.prescale_cnt"
    - "spi_clkgen.sclk_toggle"
    - "spi_fifo.tx_level"
    - "spi_fifo.rx_level"
    - "spi_int.int_pending_raw"
    - "spi_int.irq_masked"
  trace_events:
    - { name: "evt_apb_write", payload: "addr,data,pstrb,pslverr" }
    - { name: "evt_launch", payload: "cs_sel,data_width,cpol,cpha,lsb_first" }
    - { name: "evt_frame_done", payload: "rx_word,rx_push_ok,errors" }
    - { name: "evt_int_change", payload: "pending,mask,irq_o" }
  source_tracking:
    requirement_to_signal_examples:
      - { req: "illegal APB access asserts PSLVERR and sticky flag", signals: ["PSLVERR", "STATUS.illegal_access", "INT_PENDING.illegal_access_pend"] }
      - { req: "irq_o is OR reduction of INT_PENDING & INT_MASK", signals: ["INT_PENDING", "INT_MASK", "irq_o"] }

integration:
  bus_attachment:
    bus: "APB-lite"
    role: "slave"
    address_width: 12
    data_width: 32
  dependencies:
    - "External SPI slave device timing is out of scope; this IP only guarantees generated SCLK/MOSI/CS waveform contract."
  connections:
    - { from: "spi_regs.start_pulse", to: "spi_shift.start_req", signal: "start_req" }
    - { from: "spi_regs.ctrl_cfg", to: "spi_shift.ctrl_cfg", signal: "ctrl_cfg" }
    - { from: "spi_fifo.tx_pop_data", to: "spi_shift.tx_word", signal: "tx_word" }
    - { from: "spi_shift.rx_word", to: "spi_fifo.rx_push_data", signal: "rx_word" }
    - { from: "spi_int.irq_o", to: "spi.irq_o", signal: "irq_o" }

dft:
  scan:
    strategy: "single_clock_scan"
    assumptions:
      - "PCLK is controllable in test mode."
      - "PRESETn can be asserted/deasserted from test controller."
  test_points:
    - "FIFO full/empty boundary conditions should be controllable via APB writes and frame completions."

synthesis:
  language: "systemverilog_2012"
  constraints:
    - "Use PCLK as only sequential clock."
    - "Do not infer latches."
  ppa_targets:
    fmax_mhz: 100
    area_priority: "balanced"
    power_priority: "low_dynamic_when_idle"

pnr:
  utilization_pct: 60
  aspect_ratio: 1.0
  core_space_um: 2.0
  global_density: 0.65
  io_layers: { horizontal: "met3", vertical: "met2" }
  cts: { buf_list: ["sky130_fd_sc_hd__clkbuf_4", "sky130_fd_sc_hd__clkbuf_8"] }
  routing: { signal_layers: { min: "met1", max: "met5" }, drc_waivers: [] }

coding_rules:
  verilog_style: "systemverilog_2012"
  file_extension: ".sv"
  parameter_header: "rtl/spi_param.vh"
  conventions:
    - "nonblocking (<=) in sequential always @(posedge PCLK or negedge PRESETn)"
    - "blocking (=) in combinational always @(*)"
    - "No latches: every combinational branch assigns all outputs"
    - "sclk_o is output waveform only and never used as internal RTL clock"
    - "Parameterize widths and limits"
  lint_waivers:
    - "UNUSEDSIGNAL: optional debug probe nets in synthesis-off blocks"

reuse_modules: []

custom:
  assumptions:
    - "CTRL.start is treated as edge-detected launch request and does not need software clear."
    - "When CTRL.enable transitions low during active frame, in-flight frame is allowed to complete; only new launches are blocked."
    - "CS_IDLE reset value 0x0F assumes NUM_CS<=4 default; hardware masks cs_idle_val to NUM_CS width at runtime."
  note: "Assumptions are conservative and can be tightened by future change request without altering required behavior semantics."

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
    - "rtl/spi_param.vh"
  rtl:
    - "rtl/spi.sv"
    - "rtl/spi_regs.sv"
    - "rtl/spi_fifo.sv"
    - "rtl/spi_clkgen.sv"
    - "rtl/spi_shift.sv"
    - "rtl/spi_int.sv"
  sim:
    - "sim/tb_top.sv"
    - "sim/tb_program.sv"
    - "sim/spi_model.py"
  firmware:
    - "firmware/spi_regs.h"
  docs:
    - "docs/spi_register_map.md"
    - "docs/spi_programming_guide.md"

test_requirements:
  scenarios:
    - { id: "SC_APB_CONFIG", name: "APB config/readback", stimulus: "Program CTRL/PRESCALE/CS_IDLE/INT_MASK and read back RW fields", expected: "Readback matches writes; RO/WO behavior and PSLVERR policy hold", checker: "APB scoreboard and access-policy assertions", coverage: ["function_model.transactions.FM_APB_TX_PUSH", "cycle_model.handshake_rules"] }
    - { id: "SC_BASIC_TRANSFER", name: "Basic frame transfer", stimulus: "Push TXDATA then start single 8-bit frame", expected: "busy asserts then clears, done pending sets, RXDATA returns sampled value", checker: "frame scoreboard and status checks", coverage: ["function_model.transactions.FM_FRAME_LAUNCH", "function_model.transactions.FM_FRAME_COMPLETE", "fsm.channel_level"] }
    - { id: "SC_CPOL_CPHA_SWEEP", name: "CPOL/CPHA sweep", stimulus: "Run frames in all four CPOL/CPHA combinations", expected: "edge launch/sample ordering follows mode", checker: "edge timing monitor", coverage: ["cycle_model.handshake_rules", "cycle_model.pipeline"] }
    - { id: "SC_LSB_FIRST", name: "LSB-first ordering", stimulus: "Set lsb_first=1 and run known pattern", expected: "MOSI bit order reversed relative to MSB-first", checker: "serial bit-sequence checker", coverage: ["function_model.transactions.FM_SHIFT_SAMPLE"] }
    - { id: "SC_WIDTH_SWEEP", name: "Frame width sweep", stimulus: "Program data_width_m1 to legal widths 4..32 and transfer", expected: "exact configured bit count shifted/sampled", checker: "bit counter and waveform checks", coverage: ["function_model.state_variables.frame_bits", "fsm.channel_level"] }
    - { id: "SC_FIFO_LIMITS", name: "FIFO boundary behavior", stimulus: "Fill TX FIFO, overflow writes, fill RX FIFO then complete another frame", expected: "tx_overrun and rx_overrun sticky behavior with data drop policy", checker: "FIFO occupancy scoreboard", coverage: ["memory.instances", "cycle_model.backpressure"] }
    - { id: "SC_IRQ_W1C", name: "Interrupt mask and W1C", stimulus: "Trigger sticky and level sources, toggle mask, clear via INT_CLEAR", expected: "irq_o == OR(INT_PENDING & INT_MASK); W1C clears sticky only", checker: "interrupt equation assertions", coverage: ["interrupts.sources", "function_model.transactions.FM_INT_CLEAR"] }
    - { id: "SC_ERROR_PATHS", name: "Error paths", stimulus: "Illegal address/strobe/access, invalid cs_sel, illegal width, RX empty read", expected: "PSLVERR and corresponding sticky bits/pending bits set", checker: "error monitor and CSR checks", coverage: ["error_handling.error_sources"] }
    - { id: "SC_PRESCALE_TIMING", name: "Prescale timing", stimulus: "Sweep divisor values", expected: "SCLK half-period equals divisor+1 PCLK cycles", checker: "cycle-accurate period checker", coverage: ["timing.protocol_timing", "cycle_model.performance"] }
    - { id: "SC_LOOPBACK_DEBUG", name: "Loopback and debug observability", stimulus: "Enable loopback and capture debug register/probes across frames", expected: "RX equals MOSI sequence and debug counters/probes align", checker: "debug trace checker", coverage: ["debug_observability.waveform_probes", "registers.register_list.DEBUG"] }
  scoreboard_checks: 24
  coverage_goals:
    function:
      target_pct: 100
      model: "function_model"
      bins:
        - { id: "FCOV_TX_PUSH_OK", source_ref: "function_model.transactions.FM_APB_TX_PUSH", class: "transaction", description: "TXDATA accepted path" }
        - { id: "FCOV_TX_PUSH_OVERRUN", source_ref: "function_model.transactions.FM_APB_TX_PUSH", class: "error_case", description: "TX full drop path" }
        - { id: "FCOV_LAUNCH_SUPPRESS", source_ref: "function_model.transactions.FM_FRAME_LAUNCH", class: "error_case", description: "Launch suppression paths" }
        - { id: "FCOV_FRAME_COMPLETE", source_ref: "function_model.transactions.FM_FRAME_COMPLETE", class: "transaction", description: "Normal frame completion" }
    cycle:
      target_pct: 100
      model: "cycle_model"
      bins:
        - { id: "CCOV_APB_HANDSHAKE", source_ref: "cycle_model.handshake_rules", class: "handshake", description: "APB transfer and PSLVERR timing" }
        - { id: "CCOV_SPI_PIPELINE", s
... <truncated 8045 chars>

Base rtl-gen contract:
Prepare rtl-gen for spi using only spi/yaml/spi.ssot.yaml and spi/rtl/rtl_todo_plan.json, spi/rtl/rtl_authoring_plan.json, and packets under spi/rtl/authoring_packets. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=2a60bf453550d0ce8554eb62210062c7cf9b821cfd849f3ea1217a035cfae11d. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "spi",
        "reason": "14 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "rtl_implementation_depth_evidence",
        "owner_module": "spi",
        "reason": "1 production RTL implementation-depth issue(s) remain. Production RTL procedural block count is below the SSOT-locked target scale: actual=17 required=20",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_implementation_depth_evidence",
        "status": "open",
        "task_id": "RTL-0022"
      }
    ],
    "blocked_by_locked_truth": [
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "owner_module": "spi",
        "reason": "1 SSOT connection contract issue(s) remain. spi_shift: SSOT connection contract port is not connected by the RTL named port map",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      },
      {
        "gate_kind": "golden_authority_artifacts",
        "owner_module": "spi",
        "reason": "Missing production golden authority artifact(s): governance/authority.json, model/model_signature.json, verify/equivalence_goals.json",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.golden_authority_artifacts",
        "status": "open",
        "task_id": "RTL-0020"
      },
      {
        "gate_kind": "cycle_model_artifacts",
        "owner_module": "spi",
        "reason": "Missing executable cycle model: model/cycle_model.py.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.cycle_model_artifacts",
        "status": "open",
        "task_id": "RTL-0023"
      }
    ],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "spi",
        "reason": "22 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "gate_kind": "protocol_assertion_evidence",
        "owner_module": "spi",
        "reason": "Missing protocol assertion artifact: verify/protocol_assertions.sva.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "gate_kind": "fl_rtl_goal_audit",
        "owner_module": "spi",
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "gate_kind": "coverage_closure",
        "owner_module": "spi",
        "reason": "Missing coverage closure artifact: cov/coverage.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "status": "open",
        "task_id": "RTL-0026"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 5,
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
    "open_required_todos": 23,
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
          "spi/rtl/rtl_todo_plan.json",
          "spi/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py spi --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "22 required non-closure TODO(s) remain open.",
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
          "spi/verify/protocol_assertions.sva",
          "spi/verify/protocol_assertions.summary.json",
          "spi/sim/assertion_failures.jsonl"
        ],
        "closure_rule": "Generated assertions exist and latest simulation has zero assertion failure records.",
        "commands": [
          "python3 workflow/fl-model-gen/scripts/emit_protocol_assertions.py spi --root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py spi --root . --audit-rtl"
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
          "spi/sim/fl_rtl_goal_audit.json"
        ],
        "closure_rule": "fl_rtl_goal_audit.json must be fresh and status=pass.",
        "commands": [
          "python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py spi --root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py spi --root . --audit-rtl"
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
          "spi/cov/coverage.json"
        ],
        "closure_rule": "coverage.json must be fresh, come from ssot_coverage_summary, and close every planned required bin.",
        "commands": [
          "python3 workflow/coverage/scripts/ssot_coverage_summary.py spi",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py spi --root . --audit-rtl"
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
  "ip": "spi",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_clkgen.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "packet_id": "module__spi_clkgen",
      "required_count": 21,
      "status_counts": {
        "open": 2,
        "pass": 19
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_shift__function_model_01.json",
      "kind": "module",
      "llm_actionable_open_count": 5,
      "open_required_count": 5,
      "owner_file": "rtl/spi_shift.sv",
      "owner_module": "spi_shift",
      "packet_id": "module__spi_shift__function_model_01",
      "required_count": 48,
      "status_counts": {
        "open": 5,
        "pass": 43
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_shift__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 5,
      "open_required_count": 5,
      "owner_file": "rtl/spi_shift.sv",
      "owner_module": "spi_shift",
      "packet_id": "module__spi_shift__function_model_02",
      "required_count": 13,
      "status_counts": {
        "open": 5,
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_shift__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/spi_shift.sv",
      "owner_module": "spi_shift",
      "packet_id": "module__spi_shift__cycle_model",
      "required_count": 4,
      "status_counts": {
        "open": 1,
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_shift__features.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/spi_shift.sv",
      "owner_module": "spi_shift",
      "packet_id": "module__spi_shift__features",
      "required_count": 3,
      "status_counts": {
        "open": 1,
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/spi.sv",
      "owner_module": "spi",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 10,
      "status_counts": {
        "open": 2,
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 3,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 3,
      "owner_file": "rtl/spi.sv",
      "owner_module": "spi",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 7,
      "status_counts": {
        "open": 3,
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 4,
      "owner_file": "rtl/spi.sv",
      "owner_module": "spi",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 7,
      "status_counts": {
        "open": 4,
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_regs__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_regs.sv",
      "owner_module": "spi_regs",
      "packet_id": "module__spi_regs__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_regs__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_regs.sv",
      "owner_module": "spi_regs",
      "packet_id": "module__spi_regs__error_handling",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_regs__interrupts.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_regs.sv",
      "owner_module": "spi_regs",
      "packet_id": "module__spi_regs__interrupts",
      "required_count": 8,
      "status_counts": {
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_regs__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_regs.sv",
      "owner_module": "spi_regs",
      "packet_id": "module__spi_regs__io_list",
      "required_count": 16,
      "status_counts": {
        "pass": 16
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_regs__registers.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_regs.sv",
      "owner_module": "spi_regs",
      "packet_id": "module__spi_regs__registers",
      "required_count": 37,
      "status_counts": {
        "pass": 37
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_regs__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_regs.sv",
      "owner_module": "spi_regs",
      "packet_id": "module__spi_regs__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_fifo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_fifo.sv",
      "owner_module": "spi_fifo",
      "packet_id": "module__spi_fifo",
      "required_count": 9,
      "status_counts": {
        "pass": 9
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_shift__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_shift.sv",
      "owner_module": "spi_shift",
      "packet_id": "module__spi_shift__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_shift__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_shift.sv",
      "owner_module": "spi_shift",
      "packet_id": "module__spi_shift__fsm",
      "required_count": 18,
      "status_counts": {
        "pass": 18
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_shift__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_shift.sv",
      "owner_module": "spi_shift",
      "packet_id": "module__spi_shift__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi_int.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi_int.sv",
      "owner_module": "spi_int",
      "packet_id": "module__spi_int",
      "required_count": 21,
      "status_counts": {
        "pass": 21
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__spi.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/spi.sv",
      "owner_module": "spi",
      "packet_id": "module__spi",
      "required_count": 30,
      "status_counts": {
        "pass": 30
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
    "rtl_target_scale": {
      "basis": "spi peripheral complexity",
      "min_behavior_owner_logic_modules": 3,
      "min_depth_score": 40,
      "min_logic_modules": 4,
      "min_modules": 6,
      "min_procedural_blocks": 20,
      "min_source_files": 6,
      "min_state_updates": 25,
      "policy": "SSOT-locked scale target. It may be calibrated from a reference profile, but rtl-gen must satisfy it through IP-specific SSOT behavior, not by copying reference RTL."
    },
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
    "human_locked_tasks": 3,
    "llm_actionable_packets": 6,
    "llm_actionable_tasks": 16,
    "max_packet_required_tasks": 48,
    "module_packets": 17,
    "next_llm_packets": [
      "module__spi_clkgen",
      "module__spi_shift__function_model_01",
      "module__spi_shift__function_model_02",
      "module__spi_shift__cycle_model",
      "module__spi_shift__features",
      "rtl_gate_evidence_closure"
    ],
    "packet_task_limit": 48,
    "packets": 20,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 258,
    "sliced_module_packets": 13,
    "target_scale_present": true,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 4,
    "total_tasks": 258,
    "unowned_packets": 0
  },
  "target_scale": {
    "basis": "spi peripheral complexity",
    "min_behavior_owner_logic_modules": 3,
    "min_depth_score": 40,
    "min_logic_modules": 4,
    "min_modules": 6,
    "min_procedural_blocks": 20,
    "min_source_files": 6,
    "min_state_updates": 25,
    "policy": "SSOT-locked scale target. It may be calibrated from a reference profile, but rtl-gen must satisfy it through IP-specific SSOT behavior, not by copying reference RTL."
  },
  "todo_plan_sha256": "2a60bf453550d0ce8554eb62210062c7cf9b821cfd849f3ea1217a035cfae11d",
  "top": "spi",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/spi_clkgen.sv):
// spi_clkgen.sv — PCLK-based SCLK half-period ticker from SSOT cycle_model/timing
module spi_clkgen #(
    parameter integer PRESCALE_WIDTH = 16,
    parameter integer CPOL_RESET = 0
) (
    input  logic                      PCLK,
    input  logic                      PRESETn,
    input  logic                      soft_reset,
    input  logic                      busy,
    input  logic                      cpol,
    input  logic [PRESCALE_WIDTH-1:0] prescale_div,
    output logic                      sclk_o,
    output logic                      prescale_tick,
    output logic                      sample_edge,
    output logic                      shift_edge
);
    logic [PRESCALE_WIDTH-1:0] prescale_cnt;
    logic edge_phase;
    logic tick_next;

    always @(*) begin
        tick_next = 1'b0;
        if (busy && (prescale_cnt == prescale_div)) begin
            tick_next = 1'b1;
        end
    end

    // SSOT timing: each SCLK half-period lasts divisor+1 PCLK cycles.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            prescale_cnt <= {PRESCALE_WIDTH{1'b0}};
            prescale_tick <= 1'b0;
            edge_phase <= 1'b0;
            sclk_o <= CPOL_RESET[0];
        end else if (soft_reset) begin
            prescale_cnt <= {PRESCALE_WIDTH{1'b0}};
            prescale_tick <= 1'b0;
            edge_phase <= 1'b0;
            sclk_o <= cpol;
        end else begin
            prescale_tick <= tick_next;
            if (!busy) begin
                prescale_cnt <= {PRESCALE_WIDTH{1'b0}};
                edge_phase <= 1'b0;
                sclk_o <= cpol;
            end else if (tick_next) begin
                prescale_cnt <= {PRESCALE_WIDTH{1'b0}};
                edge_phase <= ~edge_phase;
                sclk_o <= ~sclk_o;
            end else begin
                prescale_cnt <= prescale_cnt + {{(PRESCALE_WIDTH-1){1'b0}}, 1'b1};
            end
        end
    end

    // The shift engine combines these alternating edges with CPHA for launch/sample order.
    always @(*) begin
        shift_edge = 1'b0;
        sample_edge = 1'b0;
        if (prescale_tick) begin
            if (edge_phase == 1'b0) begin
                shift_edge = 1'b1;
            end else begin
                sample_edge = 1'b1;
            end
        end
    end
endmodule


Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__spi_clkgen.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 5,
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
      "module_task_count": 21,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/spi_clkgen.sv",
      "name": "spi_clkgen",
      "refs": [
        "cycle_model",
        "cycle_model.handshake_rules",
        "cycle_model.pipeline",
        "parameters",
        "parameters.PRESCALE_WIDTH",
        "timing"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/spi_regs.sv",
        "name": "spi_regs",
        "wiring_only": false
      },
      {
        "file": "rtl/spi_fifo.sv",
        "name": "spi_fifo",
        "wiring_only": false
      },
      {
        "file": "rtl/spi_clkgen.sv",
        "name": "spi_clkgen",
        "wiring_only": false
      },
      {
        "file": "rtl/spi_shift.sv",
        "name": "spi_shift",
        "wiring_only": false
      },
      {
        "file": "rtl/spi_int.sv",
        "name": "spi_int",
        "wiring_only": false
      },
      {
        "file": "rtl/spi.sv",
        "name": "spi",
        "wiring_only": false
      }
    ],
    "quality_profile": "production",
    "reference_profile": null,
    "ssot_connection_contracts": [],
    "ssot_top_io_contracts": [],
    "target_scale": {
      "basis": "spi peripheral complexity",
      "min_behavior_owner_logic_modules": 3,
      "min_depth_score": 40,
      "min_logic_modules": 4,
      "min_modules": 6,
      "min_procedural_blocks": 20,
      "min_source_files": 6,
      "min_state_updates": 25,
      "policy": "SSOT-locked scale target. It may be calibrated from a reference profile, but rtl-gen must satisfy it through IP-specific SSOT behavior, not by copying reference RTL."
    }
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
  "ip": "spi",
  "kind": "module",
  "owner_file": "rtl/spi_clkgen.sv",
  "owner_module": "spi_clkgen",
  "packet_id": "module__spi_clkgen",
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
      "cycle_model.handshake_rules": 5,
      "cycle_model.pipeline": 5,
      "equivalence.module": 1,
      "parameters.item": 10
    },
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 21,
      "task_limit": 48
    },
    "open_required_count": 2,
    "required_count": 21,
    "source_refs": [
      "cycle_model.handshake_rules.APB",
      "cycle_model.handshake_rules.CTRL_start",
      "cycle_model.handshake_rules.launch_gate",
      "cycle_model.handshake_rules.sclk_o",
      "cycle_model.handshake_rules.sample_edge",
      "cycle_model.pipeline.S0_APB_CFG",
      "cycle_model.pipeline.S1_LAUNCH_CHECK",
      "cycle_model.pipeline.S2_ASSERT_CS",
      "cycle_model.pipeline.S4_SAMPLE",
      "cycle_model.pipeline.S5_COMPLETE",
      "sub_modules.spi_clkgen.module_equivalence",
      "parameters.APB_ADDR_WIDTH",
      "parameters.APB_DATA_WIDTH",
      "parameters.DATA_WIDTH",
      "parameters.FIFO_DEPTH",
      "parameters.NUM_CS",
      "parameters.PRESCALE_WIDTH",
      "parameters.CPOL_RESET",
      "parameters.CPHA_RESET",
      "parameters.LSB_FIRST_RESET",
      "parameters.PCLK_FREQ_MHZ"
    ],
    "status_counts": {
      "open": 2,
      "pass": 19
    },
    "task_count": 21
  },
  "tasks": [
    {
      "category": "cycle_model.handshake_rules",
      "content": "Implement handshake rule: APB",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.handshake_rules.APB",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.handshake_rules.APB appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.handshake_rules.APB.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.\nSSOT item context: signal=APB.",
      "evidence_terms": [],
      "id": "RTL-0119",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.handshake_rules.APB",
      "ssot_context": {
        "signal": "APB"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules.APB"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "cycle_model.handshake_rules",
      "content": "Implement handshake rule: CTRL.start",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.handshake_rules.CTRL_start",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.handshake_rules.CTRL_start appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.handshake_rules.CTRL_start.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.\nSSOT item context: signal=CTRL.start.",
      "evidence_terms": [],
      "id": "RTL-0120",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.handshake_rules.CTRL_start",
      "ssot_context": {
        "signal": "CTRL.start"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules.CTRL_start"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "cycle_model.handshake_rules",
      "content": "Implement handshake rule: launch_gate",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.handshake_rules.launch_gate",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.handshake_rules.launch_gate appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.handshake_rules.launch_gate.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.\nSSOT item context: signal=launch_gate.",
      "evidence_terms": [
        "gate",
        "launch",
        "launch_gate"
      ],
      "id": "RTL-0121",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.handshake_rules.launch_gate",
      "ssot_context": {
        "signal": "launch_gate"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules.launch_gate"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "gate",
          "launch",
          "launch_gate"
        ],
        "source_scope": "rtl/spi_clkgen.sv",
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
      "category": "cycle_model.handshake_rules",
      "content": "Implement handshake rule: sclk_o",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.handshake_rules.sclk_o",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.handshake_rules.sclk_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.handshake_rules.sclk_o.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.\nSSOT item context: signal=sclk_o.",
      "evidence_terms": [
        "sclk",
        "sclk_o"
      ],
      "id": "RTL-0122",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.handshake_rules.sclk_o",
      "ssot_context": {
        "signal": "sclk_o"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules.sclk_o"
      ],
      "static_evidence": {
        "matched_count": 2,
        "matched_terms": [
          "sclk",
          "sclk_o"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "sclk",
          "sclk_o"
        ],
        "source_scope": "rtl/spi_clkgen.sv",
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
      "category": "cycle_model.handshake_rules",
      "content": "Implement handshake rule: sample_edge",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.handshake_rules.sample_edge",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.handshake_rules.sample_edge appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.handshake_rules.sample_edge.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.\nSSOT item context: signal=sample_edge.",
      "evidence_terms": [
        "edge",
        "sample",
        "sample_edge"
      ],
      "id": "RTL-0123",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.handshake_rules.sample_edge",
      "ssot_context": {
        "signal": "sample_edge"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules.sample_edge"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "edge",
          "sample",
          "sample_edge"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "edge",
          "sample",
          "sample_edge"
        ],
        "source_scope": "rtl/spi_clkgen.sv",
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
      "category": "cycle_model.pipeline",
      "content": "Implement pipeline stage: S0_APB_CFG",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.pipeline.S0_APB_CFG",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.pipeline.S0_APB_CFG timing uses SSOT cycle/latency t",
        "cycle_model.pipeline.S0_APB_CFG appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.pipeline.S0_APB_CFG.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.\nSSOT item context: stage=S0_APB_CFG; action=Program mode/prescale/CS and push TX words; cycle=t.",
      "evidence_terms": [],
      "id": "RTL-0124",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.pipeline.S0_APB_CFG",
      "ssot_context": {
        "action": "Program mode/prescale/CS and push TX words",
        "cycle": "t",
        "stage": "S0_APB_CFG"
      },
      "ssot_refs": [
        "cycle_model.pipeline.S0_APB_CFG"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
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
      "category": "cycle_model.pipeline",
      "content": "Implement pipeline stage: S1_LAUNCH_CHECK",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.pipeline.S1_LAUNCH_CHECK",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.pipeline.S1_LAUNCH_CHECK timing uses SSOT cycle/latency t+0..t+1",
        "cycle_model.pipeline.S1_LAUNCH_CHECK appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.pipeline.S1_LAUNCH_CHECK.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.\nSSOT item context: stage=S1_LAUNCH_CHECK; action=Evaluate launch preconditions and latch frame context; cycle=t+0..t+1.",
      "evidence_terms": [],
      "id": "RTL-0125",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.pipeline.S1_LAUNCH_CHECK",
      "ssot_context": {
        "action": "Evaluate launch preconditions and latch frame context",
        "cycle": "t+0..t+1",
        "stage": "S1_LAUNCH_CHECK"
      },
      "ssot_refs": [
        "cycle_model.pipeline.S1_LAUNCH_CHECK"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
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
      "category": "cycle_model.pipeline",
      "content": "Implement pipeline stage: S2_ASSERT_CS",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.pipeline.S2_ASSERT_CS",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.pipeline.S2_ASSERT_CS timing uses SSOT cycle/latency next",
        "cycle_model.pipeline.S2_ASSERT_CS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.pipeline.S2_ASSERT_CS.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.\nSSOT item context: stage=S2_ASSERT_CS; action=Drive selected chip select active-low; cycle=next.",
      "evidence_terms": [],
      "id": "RTL-0126",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.pipeline.S2_ASSERT_CS",
      "ssot_context": {
        "action": "Drive selected chip select active-low",
        "cycle": "next",
        "stage": "S2_ASSERT_CS"
      },
      "ssot_refs": [
        "cycle_model.pipeline.S2_ASSERT_CS"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
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
      "category": "cycle_model.pipeline",
      "content": "Implement pipeline stage: S4_SAMPLE",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.pipeline.S4_SAMPLE",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.pipeline.S4_SAMPLE timing uses SSOT cycle/latency repeating",
        "cycle_model.pipeline.S4_SAMPLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.pipeline.S4_SAMPLE.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.\nSSOT item context: stage=S4_SAMPLE; action=Sample MISO/loopback bit and advance bit_index; cycle=repeating.",
      "evidence_terms": [
        "bit",
        "bit_index",
        "index"
      ],
      "id": "RTL-0128",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.pipeline.S4_SAMPLE",
      "ssot_context": {
        "action": "Sample MISO/loopback bit and advance bit_index",
        "cycle": "repeating",
        "stage": "S4_SAMPLE"
      },
      "ssot_refs": [
        "cycle_model.pipeline.S4_SAMPLE"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "bit",
          "bit_index",
          "index"
        ],
        "source_scope": "rtl/spi_clkgen.sv",
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
      "category": "cycle_model.pipeline",
      "content": "Implement pipeline stage: S5_COMPLETE",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.pipeline.S5_COMPLETE",
        "Primary implementation evidence is in rtl/spi_clkgen.sv",
        "cycle_model.pipeline.S5_COMPLETE timing uses SSOT cycle/latency terminal",
        "cycle_model.pipeline.S5_COMPLETE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.pipeline.S5_COMPLETE.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.\nSSOT item context: stage=S5_COMPLETE; action=Push RX word if possible, update done/errors/pending, manage CS hold/deassert; cycle=terminal.",
      "evidence_terms": [],
      "id": "RTL-0129",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.pipeline.S5_COMPLETE",
      "ssot_context": {
        "action": "Push RX word if possible, update done/errors/pending, manage CS hold/deassert",
        "cycle": "terminal",
        "stage": "S5_COMPLETE"
      },
      "ssot_refs": [
        "cycle_model.pipeline.S5_COMPLETE"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
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
      "category": "equivalence.module",
      "content": "Prove module spi_clkgen is functionally equivalent to FL",
      "criteria": [
        "verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module",
        "cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff",
        "scoreboard row fl_expected.model_api is FunctionalModel.apply",
        "scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data",
        "Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong",
        "Traceability keeps source_ref sub_modules.spi_clkgen.module_equivalence",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.\nSSOT ref: sub_modules.spi_clkgen.module_equivalence.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via module_equivalence.",
      "evidence_terms": [],
      "id": "RTL-0245",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "high",
      "required": true,
      "source_ref": "sub_modules.spi_clkgen.module_equivalence",
      "ssot_context": {},
      "ssot_refs": [
        "sub_modules.spi_clkgen.module_equivalence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
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
      "category": "parameters.item",
      "content": "Implement parameter APB_ADDR_WIDTH",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.APB_ADDR_WIDTH",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.APB_ADDR_WIDTH.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=APB_ADDR_WIDTH.",
      "evidence_terms": [],
      "id": "RTL-0029",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.APB_ADDR_WIDTH",
      "ssot_context": {
        "name": "APB_ADDR_WIDTH"
      },
      "ssot_refs": [
        "parameters.APB_ADDR_WIDTH"
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
      "category": "parameters.item",
      "content": "Implement parameter APB_DATA_WIDTH",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.APB_DATA_WIDTH",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.APB_DATA_WIDTH.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=APB_DATA_WIDTH.",
      "evidence_terms": [],
      "id": "RTL-0030",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.APB_DATA_WIDTH",
      "ssot_context": {
        "name": "APB_DATA_WIDTH"
      },
      "ssot_refs": [
        "parameters.APB_DATA_WIDTH"
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
      "category": "parameters.item",
      "content": "Implement parameter DATA_WIDTH",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.DATA_WIDTH",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.DATA_WIDTH.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=DATA_WIDTH.",
      "evidence_terms": [],
      "id": "RTL-0031",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.DATA_WIDTH",
      "ssot_context": {
        "name": "DATA_WIDTH"
      },
      "ssot_refs": [
        "parameters.DATA_WIDTH"
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
      "category": "parameters.item",
      "content": "Implement parameter FIFO_DEPTH",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.FIFO_DEPTH",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.FIFO_DEPTH.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=FIFO_DEPTH.",
      "evidence_terms": [],
      "id": "RTL-0032",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.FIFO_DEPTH",
      "ssot_context": {
        "name": "FIFO_DEPTH"
      },
      "ssot_refs": [
        "parameters.FIFO_DEPTH"
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
      "category": "parameters.item",
      "content": "Implement parameter NUM_CS",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.NUM_CS",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.NUM_CS.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=NUM_CS.",
      "evidence_terms": [],
      "id": "RTL-0033",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.NUM_CS",
      "ssot_context": {
        "name": "NUM_CS"
      },
      "ssot_refs": [
        "parameters.NUM_CS"
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
      "category": "parameters.item",
      "content": "Implement parameter PRESCALE_WIDTH",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.PRESCALE_WIDTH",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.PRESCALE_WIDTH.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.PRESCALE_WIDTH.\nSSOT item context: name=PRESCALE_WIDTH.",
      "evidence_terms": [],
      "id": "RTL-0034",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.PRESCALE_WIDTH",
      "ssot_context": {
        "name": "PRESCALE_WIDTH"
      },
      "ssot_refs": [
        "parameters.PRESCALE_WIDTH"
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
      "category": "parameters.item",
      "content": "Implement parameter CPOL_RESET",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.CPOL_RESET",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.CPOL_RESET.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=CPOL_RESET.",
      "evidence_terms": [],
      "id": "RTL-0035",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.CPOL_RESET",
      "ssot_context": {
        "name": "CPOL_RESET"
      },
      "ssot_refs": [
        "parameters.CPOL_RESET"
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
      "category": "parameters.item",
      "content": "Implement parameter CPHA_RESET",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.CPHA_RESET",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.CPHA_RESET.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=CPHA_RESET.",
      "evidence_terms": [],
      "id": "RTL-0036",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.CPHA_RESET",
      "ssot_context": {
        "name": "CPHA_RESET"
      },
      "ssot_refs": [
        "parameters.CPHA_RESET"
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
      "category": "parameters.item",
      "content": "Implement parameter LSB_FIRST_RESET",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.LSB_FIRST_RESET",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.LSB_FIRST_RESET.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=LSB_FIRST_RESET.",
      "evidence_terms": [],
      "id": "RTL-0037",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.LSB_FIRST_RESET",
      "ssot_context": {
        "name": "LSB_FIRST_RESET"
      },
      "ssot_refs": [
        "parameters.LSB_FIRST_RESET"
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
      "category": "parameters.item",
      "content": "Implement parameter PCLK_FREQ_MHZ",
      "criteria": [
        "Parameter default/value matches SSOT",
        "Parameter-derived widths are implemented outside procedural part-selects",
        "Compile/lint evidence covers the parameterized form",
        "Traceability keeps source_ref parameters.PCLK_FREQ_MHZ",
        "Primary implementation evidence is in rtl/spi_clkgen.sv"
      ],
      "detail": "Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.\nSSOT ref: parameters.PCLK_FREQ_MHZ.\nOwner: spi_clkgen in rtl/spi_clkgen.sv via parameters.\nSSOT item context: name=PCLK_FREQ_MHZ.",
      "evidence_terms": [],
      "id": "RTL-0038",
      "owner_file": "rtl/spi_clkgen.sv",
      "owner_module": "spi_clkgen",
      "priority": "normal",
      "required": true,
      "source_ref": "parameters.PCLK_FREQ_MHZ",
      "ssot_context": {
        "name": "PCLK_FREQ_MHZ"
      },
      "ssot_refs": [
        "parameters.PCLK_FREQ_MHZ"
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
    }
  ],
  "todo_plan_sha256": "2a60bf453550d0ce8554eb62210062c7cf9b821cfd849f3ea1217a035cfae11d",
  "top": "spi",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__spi_clkgen.md):
# RTL Authoring Packet: module__spi_clkgen

- Kind: module
- Owner module: spi_clkgen
- Owner file: rtl/spi_clkgen.sv
- Task count: 21
- Required tasks: 21

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
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, parameters, parameters.PRESCALE_WIDTH, timing
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25

## Tasks

### RTL-0119: Implement handshake rule: APB

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.APB
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.APB.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=APB.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.APB
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.APB appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.APB

### RTL-0120: Implement handshake rule: CTRL.start

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.CTRL_start
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.CTRL_start.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=CTRL.start.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.CTRL_start
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.CTRL_start appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.CTRL_start

### RTL-0121: Implement handshake rule: launch_gate

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.launch_gate
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.launch_gate.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=launch_gate.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.launch_gate
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.launch_gate appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.launch_gate

### RTL-0122: Implement handshake rule: sclk_o

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sclk_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sclk_o.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=sclk_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sclk_o
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.sclk_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sclk_o

### RTL-0123: Implement handshake rule: sample_edge

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sample_edge
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sample_edge.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=sample_edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sample_edge
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.sample_edge appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sample_edge

### RTL-0124: Implement pipeline stage: S0_APB_CFG

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_APB_CFG
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_APB_CFG.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S0_APB_CFG; action=Program mode/prescale/CS and push TX words; cycle=t.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_APB_CFG
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S0_APB_CFG timing uses SSOT cycle/latency t
  - cycle_model.pipeline.S0_APB_CFG appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_APB_CFG

### RTL-0125: Implement pipeline stage: S1_LAUNCH_CHECK

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_LAUNCH_CHECK
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_LAUNCH_CHECK.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S1_LAUNCH_CHECK; action=Evaluate launch preconditions and latch frame context; cycle=t+0..t+1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_LAUNCH_CHECK
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S1_LAUNCH_CHECK timing uses SSOT cycle/latency t+0..t+1
  - cycle_model.pipeline.S1_LAUNCH_CHECK appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_LAUNCH_CHECK

### RTL-0126: Implement pipeline stage: S2_ASSERT_CS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_ASSERT_CS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_ASSERT_CS.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S2_ASSERT_CS; action=Drive selected chip select active-low; cycle=next.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_ASSERT_CS
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S2_ASSERT_CS timing uses SSOT cycle/latency next
  - cycle_model.pipeline.S2_ASSERT_CS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_ASSERT_CS

### RTL-0128: Implement pipeline stage: S4_SAMPLE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S4_SAMPLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S4_SAMPLE.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S4_SAMPLE; action=Sample MISO/loopback bit and advance bit_index; cycle=repeating.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S4_SAMPLE
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S4_SAMPLE timing uses SSOT cycle/latency repeating
  - cycle_model.pipeline.S4_SAMPLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S4_SAMPLE

### RTL-0129: Implement pipeline stage: S5_COMPLETE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S5_COMPLETE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S5_COMPLETE.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S5_COMPLETE; action=Push RX word if possible, update done/errors/pending, manage CS hold/deassert; cycle=terminal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S5_COMPLETE
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S5_COMPLETE timing uses SSOT cycle/latency terminal
  - cycle_model.pipeline.S5_COMPLETE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S5_COMPLETE

### RTL-0245: Prove module spi_clkgen is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.spi_clkgen.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.spi_clkgen.module_equivalence.
Owner: spi_clkgen in rtl/spi_clkgen.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.spi_clkgen.module_equivalence
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: sub_modules.spi_clkgen.module_equivalence

### RTL-0029: Implement parameter APB_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.APB_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_ADDR_WIDTH.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=APB_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_ADDR_WIDTH
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.APB_ADDR_WIDTH

### RTL-0030: Implement parameter APB_DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.APB_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_DATA_WIDTH.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=APB_DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_DATA_WIDTH
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.APB_DATA_WIDTH

### RTL-0031: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Sou
... <truncated 6780 chars>