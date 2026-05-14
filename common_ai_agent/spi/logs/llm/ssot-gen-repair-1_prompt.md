Repair the SSOT YAML artifact for spi. This is repair attempt 1.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "spi/yaml/spi.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}
  ]
}

Repair rules:
- Do not use a fixed IP template or hardcoded workaround.
- Preserve product semantics from the requirement and current SSOT wherever they are valid.
- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.
- Fix the concrete parse/validator failures below, and also check for sibling contract defects.
- The repaired YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh spi`.
- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.

Failure summary:
human_gate: SSOT disk validator failed: [check_ssot_disk] FAIL: spi/yaml/spi.ssot.yaml failed YAML/model validation

Blocker artifact:


Validator log:
cmd: bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh spi
cwd: /Users/brian/Desktop/Project/brian_hw/common_ai_agent
returncode: 1
stdout:
[check_ssot_disk] FAIL: spi/yaml/spi.ssot.yaml failed YAML/model validation
  io_list.interfaces.apb_slave.clock_domain is required


Requirements:
# SPI IP Requirement Seed for ssot-gen

Use the loaded `/new-ip spi peripheral` workflow intent and create only the
canonical SSOT for IP `spi`.

IP intent: parameterized APB-lite controlled SPI master peripheral. It provides
software-programmed full-duplex SPI frame transfers to external SPI slaves with
TX/RX FIFOs, selectable chip select, programmable SCLK prescale, CPOL/CPHA
mode support, MSB-first and LSB-first transfer order, masked interrupts,
sticky error reporting, and debug observability for waveform/source tracking.

Scope:
- Generate the SSOT only at `spi/yaml/spi.ssot.yaml`.
- Do not generate RTL, TB, simulation, lint, waveform, coverage, synthesis,
  STA, PNR, or documentation artifacts in `ssot-gen`.
- Record conservative assumptions in `custom.assumptions` rather than blocking
  on non-critical choices.
- Make the SSOT behavior-rich enough for downstream `rtl-gen`, `tb-gen`,
  `sim_debug`, `lint`, `coverage`, `syn`, `sta`, and `pnr` workflows.

External interfaces:
- `PCLK`: primary APB and SPI engine clock, nominal 100 MHz.
- `PRESETn`: active-low reset, asynchronous assert and synchronous deassert.
- APB-lite slave CSR interface with `PADDR[11:0]`, `PSEL`, `PENABLE`,
  `PWRITE`, `PWDATA[31:0]`, `PSTRB[3:0]`, `PRDATA[31:0]`, `PREADY`, and
  `PSLVERR`.
- SPI master pins: `sclk_o`, `mosi_o`, `miso_i`, and `csn_o[NUM_CS-1:0]`.
- Combined interrupt output `irq_o`.

Parameters:
- `APB_ADDR_WIDTH` default 12.
- `APB_DATA_WIDTH` default 32.
- `DATA_WIDTH` default 8, legal runtime frame width 4 through 32 bits.
- `FIFO_DEPTH` default 16, power-of-two depth for both TX and RX FIFOs.
- `NUM_CS` default 4, legal range 1 through 8.
- `PRESCALE_WIDTH` default 16.
- `CPOL_RESET`, `CPHA_RESET`, and `LSB_FIRST_RESET` default 0.
- `PCLK_FREQ_MHZ` default 100.

CSR map requirement:
- `CTRL` at 0x00: enable, start pulse, cpol, cpha, lsb_first, continuous_cs,
  loopback, soft_reset pulse, cs_sel, and data_width_m1.
- `STATUS` at 0x04: busy, tx_full, tx_empty, rx_full, rx_empty, done,
  tx_overrun, rx_overrun, rx_underrun, mode_fault, illegal_access, cs_active.
- `PRESCALE` at 0x08: divisor. SCLK half-period is divisor+1 PCLK cycles.
- `TXDATA` at 0x0C: write-only frame payload push into TX FIFO.
- `RXDATA` at 0x10: read-only frame payload pop from RX FIFO.
- `INT_MASK` at 0x14: per-source interrupt enables.
- `INT_PENDING` at 0x18: raw pending/level sources.
- `INT_CLEAR` at 0x1C: write-one-to-clear for sticky pending/status bits.
- `CS_IDLE` at 0x20: idle chip-select output value.
- `DEBUG` at 0x24: tx_count, rx_count, bit_index, and active_cs.

Behavior:
- All internal state is synchronous to `PCLK`; `sclk_o` is generated as an
  output waveform and must not be used as an internal RTL clock.
- `CTRL.enable=0` blocks new frame launches. Active frame completion behavior
  must be explicitly defined.
- `CTRL.start` creates a launch request. A frame can launch only when enabled,
  TX FIFO is non-empty, chip select is in range, frame width is legal, and the
  shift FSM is idle.
- `CPOL` defines SCLK idle level. `CPHA` defines launch/sample edge placement.
- `lsb_first=0` shifts MSB first; `lsb_first=1` shifts LSB first.
- Exactly one chip-select bit may be active-low during a frame.
- `continuous_cs=1` may hold chip select active across back-to-back queued
  frames when mode fields remain legal.
- TX FIFO full causes TXDATA writes to be discarded and sets `tx_overrun`.
- RX FIFO full at frame completion discards the received word and sets
  `rx_overrun`.
- RXDATA read while RX FIFO is empty returns zero and sets `rx_underrun`.
- Invalid chip select or frame width at launch suppresses frame activity and
  sets `mode_fault`.
- Illegal APB address, unsupported write strobe, or access-policy violation
  asserts `PSLVERR` on that access and sets `illegal_access`.
- Sticky pending/status bits clear via `INT_CLEAR` W1C. FIFO level pending bits
  track FIFO level and are not cleared by W1C.
- `irq_o` equals OR reduction of `INT_PENDING & INT_MASK`.
- Debug observability must include waveform probes and trace events suitable
  for sim_debug waveform viewer, RTL hierarchy/source tracking, TB debugging,
  and chat context.

SSOT depth requirements:
- Include top_module, sub_modules, decomposition, rtl_contract, parameters,
  io_list, features, dataflow, function_model, cycle_model,
  clock_reset_domains, cdc_requirements, rdc_requirements, registers, memory,
  interrupts, fsm, timing, power, security, error_handling,
  debug_observability, integration, dft, synthesis, pnr, coding_rules,
  reuse_modules, custom, dir_structure, filelist, test_requirements,
  quality_gates, traceability, workflow_todos, and generation_flow.
- Function model must include state variables, transactions, preconditions,
  outputs, side effects, error cases, invariants, and reference-model guidance.
- Cycle model must include reset behavior, latency, APB handshake rules, SPI
  launch/sample rules, pipeline stages, ordering, backpressure, performance,
  and waveform observability.
- Test requirements must include concrete scenarios for APB config/readback,
  basic frame transfer, CPOL/CPHA sweep, LSB-first transfer, multiple frame
  widths, FIFO limits, interrupt/W1C semantics, error paths, prescale timing,
  and loopback/debug observability.
- Coverage goals must include function coverage, cycle/FSM coverage, static
  code coverage intent for verilator and pyslang reports, and VCD/FST observed
  coverage mapping for sim_debug.
- workflow_todos must contain downstream stage-specific work items with
  content, detail, criteria, source_refs, and owner module/file where inferable.

Quality gate:
- The produced SSOT must pass:
  `bash workflow/ssot-gen/scripts/check_ssot_disk.sh spi`
- Literal unresolved marker strings should not appear in the final SSOT.


Current SSOT YAML:
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
    source_sections: ["registers", "interrupts", "error_handling"]
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
    drives: ["spi_regs.sv", "spi.sv"]
  - name: "APB_DATA_WIDTH"
    default: 32
    type: int
    description: "APB data width"
    drives: ["spi_regs.sv", "spi.sv"]
  - name: "DATA_WIDTH"
    default: 8
    type: int
    description: "Default frame width; runtime legal range controlled by CTRL.data_width_m1"
    drives: ["spi_shift.sv", "spi_fifo.sv"]
  - name: "FIFO_DEPTH"
    default: 16
    type: int
    description: "Depth of TX and RX FIFOs; must be power of two"
    drives: ["spi_fifo.sv", "spi_regs.sv"]
  - name: "NUM_CS"
    default: 4
    type: int
    description: "Number of chip-select outputs"
    drives: ["spi_shift.sv", "spi.sv"]
  - name: "PRESCALE_WIDTH"
    default: 16
    type: int
    description: "Width of programmable prescale divisor"
    drives: ["spi_clkgen.sv", "spi_regs.sv"]
  - name: "CPOL_RESET"
    default: 0
    type: int
    description: "Reset value for CTRL.cpol"
    drives: ["spi_regs.sv", "spi_shift.sv"]
  - name: "CPHA_RESET"
    default: 0
    type: int
    description: "Reset value for CTRL.cpha"
    drives: ["spi_regs.sv", "spi_shift.sv"]
  - name: "LSB_FIRST_RESET"
    default: 0
    type: int
    description: "Reset value for CTRL.lsb_first"
    drives: ["spi_regs.sv", "spi_shift.sv"]
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
    - 
... <truncated 20954 chars>