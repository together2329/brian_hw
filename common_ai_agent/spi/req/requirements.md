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
