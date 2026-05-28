# APB UART Enhanced v2+ Signoff — 2026-05-27

> **IP**: `apb_uart_txrx_demo`  
> **Scope**: Enhanced APB UART v2+ bounded demo: configurable framing, TX/RX FIFOs, expanded status/error/IRQ behavior, RX timeout, loopback, random regression evidence, and generic timing-constraint intent.  
> **Decision**: **GO for enhanced v2+ bounded UART demo signoff** based on the fresh local artifacts listed below.  
> **Authority caveat**: This is local implementation/signoff evidence in the repository workspace. Product-flow/orchestrator claims still need validation through the relevant ATLAS UI/API/worker path.

## Implemented v2+ scope

The enhanced UART keeps the original top-level pins (`pclk`, `preset_n`, APB3 pins, `uart_tx`, `uart_rx`, `irq`) and adds the following bounded v2+ behavior internally:

- APB register map extended through `FRAME_CFG`, `FIFO_CTRL`, `FIFO_STATUS`, `FIFO_THRESH`, `RX_TIMEOUT`, and `SCRATCH` while preserving reset/default 8N1 compatibility.
- Configurable UART frame format:
  - 5/6/7/8 data-bit selection;
  - optional parity;
  - even/odd parity selection;
  - one or two stop bit-times.
- TX framed engine with FIFO-fed frame launch, configured parity/stop/data width, `tx_done` source, and TX break handling.
- RX framed engine with synchronized input, majority-vote sampling, false-start rejection, configurable data width/parity/stop checking, break detection, and error pulses.
- TX/RX synchronous FIFOs with FIFO ordering, level/status/full/empty signals, clear controls, threshold status, and full/overrun behavior.
- Expanded interrupt sources for TX done, RX valid, aggregate error, RX timeout, and FIFO thresholds.
- Loopback mode routing the internal TX serial stream into the RX sampler.
- RX timeout sticky status/IRQ behavior and W1C clearing.
- Scratch register with no UART side effects.
- Generic SDC placeholder documenting pclk/APB/UART timing intent and the asynchronous nature of `uart_rx`.

## Key files changed or added

Primary design and verification files in the signed-off scope:

```text
apb_uart_txrx_demo/req/apb_uart_txrx_demo_requirements.md
apb_uart_txrx_demo/yaml/apb_uart_txrx_demo.ssot.yaml
apb_uart_txrx_demo/rtl/baud_div_eff.sv
apb_uart_txrx_demo/rtl/apb_uart_irq.sv
apb_uart_txrx_demo/rtl/uart_fifo_sync.sv
apb_uart_txrx_demo/rtl/uart_tx_framed.sv
apb_uart_txrx_demo/rtl/uart_rx_framed.sv
apb_uart_txrx_demo/rtl/apb_uart_regs.sv
apb_uart_txrx_demo/rtl/apb_uart_txrx_demo.sv
apb_uart_txrx_demo/list/apb_uart_txrx_demo.f
apb_uart_txrx_demo/sim/tb_apb_uart_txrx_demo.sv
apb_uart_txrx_demo/sim/tb_apb_uart_txrx_demo_random.sv
apb_uart_txrx_demo/sim/run_sim.sh
apb_uart_txrx_demo/sim/run_random_regression.sh
apb_uart_txrx_demo/sdc/apb_uart_txrx_demo.sdc
```

The active RTL filelist is dependency ordered and excludes the obsolete fixed-only `uart_tx_8n1.sv`/`uart_rx_8n1.sv` modules from active DUT compilation:

```text
rtl/baud_div_eff.sv
rtl/apb_uart_irq.sv
rtl/uart_fifo_sync.sv
rtl/uart_tx_framed.sv
rtl/uart_rx_framed.sv
rtl/apb_uart_regs.sv
rtl/apb_uart_txrx_demo.sv
```

## Fresh signoff commands run

Run from repository root unless the command itself changes directory:

```bash
# RTL/filelist static build
cd apb_uart_txrx_demo && iverilog -g2012 -Wall -o /tmp/rtl_signoff_only.vvp -c list/apb_uart_txrx_demo.f

# Directed testbench compile
cd apb_uart_txrx_demo && iverilog -g2012 -Wall -o /tmp/tb_directed_signoff.vvp -c list/apb_uart_txrx_demo.f sim/tb_apb_uart_txrx_demo.sv

# Directed simulation, coverage extraction, waveform manifest
cd apb_uart_txrx_demo && ./sim/run_sim.sh

# Random regression
cd apb_uart_txrx_demo && ./sim/run_random_regression.sh 7 20

# Verilator lint
cd apb_uart_txrx_demo && verilator --lint-only --timing -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL -Wno-BLKSEQ -Wno-UNOPTFLAT -Wno-WIDTH -f list/apb_uart_txrx_demo.f

# SSOT starter strict validation
verify_ssot(ip=apb_uart_txrx_demo, mode=starter, root=., preview=strict)

# sv_compile checks
sv_compile(files=[
  "apb_uart_txrx_demo/rtl/baud_div_eff.sv",
  "apb_uart_txrx_demo/rtl/apb_uart_irq.sv",
  "apb_uart_txrx_demo/rtl/uart_fifo_sync.sv",
  "apb_uart_txrx_demo/rtl/uart_tx_framed.sv",
  "apb_uart_txrx_demo/rtl/uart_rx_framed.sv",
  "apb_uart_txrx_demo/rtl/apb_uart_regs.sv",
  "apb_uart_txrx_demo/rtl/apb_uart_txrx_demo.sv"
])

# Known exact-path sv_compile cache cross-check using byte-identical temp copies
sv_compile(files=[
  "/tmp/apb_uart_svcompile_signoff/baud_div_eff.sv",
  "/tmp/apb_uart_svcompile_signoff/apb_uart_irq.sv",
  "/tmp/apb_uart_svcompile_signoff/uart_fifo_sync.sv",
  "/tmp/apb_uart_svcompile_signoff/uart_tx_framed.sv",
  "/tmp/apb_uart_svcompile_signoff/uart_rx_framed.sv",
  "/tmp/apb_uart_svcompile_signoff/apb_uart_regs.sv",
  "/tmp/apb_uart_svcompile_signoff/apb_uart_txrx_demo.sv"
])
```

## Evidence summary

| Gate | Result | Evidence |
|---|---:|---|
| Icarus RTL-only compile | PASS | `iverilog -g2012 -Wall -o /tmp/rtl_signoff_only.vvp -c list/apb_uart_txrx_demo.f` exited 0 |
| Directed TB compile | PASS | `iverilog -g2012 -Wall -o /tmp/tb_directed_signoff.vvp -c list/apb_uart_txrx_demo.f sim/tb_apb_uart_txrx_demo.sv` exited 0 |
| Directed simulation | PASS | `apb_uart_txrx_demo/sim/sim_results.json`: `passed=true`, `scoreboard_pass=106`, `scoreboard_fail=0`, `scenario_count=31` |
| Directed coverage | PASS | `apb_uart_txrx_demo/sim/coverage_results.json`: `signoff_status=pass`, `total_bins=29`, `hit_bins=29`, `missed_bins=0`, `waived_bins=0`, `effective_coverage_pct=100.0` |
| Directed scenario manifest | PASS | `coverage_results.json`: all 31 required scenarios observed, `missing=[]`, `unexpected=[]`, `duplicates=[]` |
| Waveform evidence | PASS | `apb_uart_txrx_demo/sim/waveform_manifest.json`: `status=pass`, VCD `exists=true`, size `370717` bytes, all required APB/UART/IRQ top signals present |
| Random regression | PASS | `apb_uart_txrx_demo/sim/random/random_regression_summary.json`: seed `7`, requested/effective `txns=20`, `scoreboard_pass_total=70`, `scoreboard_fail_total=0`, `csv_fail_rows_total=0`, `all_coverage_flags_hit=true` |
| Verilator lint | PASS | Verilator report completed with configured signoff warning suppressions and no fatal/blocking lint findings |
| SSOT validation | PASS with one non-blocking warning | `apb_uart_txrx_demo/req/ssot_validation.json`: `ok=true`, `blockers=[]`, warning `ssot.canonical_order` only |
| `sv_compile` | PASS by temp-copy cross-check; exact-path diagnostic waived | Exact-path tool repeated stale diagnostics inconsistent with current source; byte-identical temp-copy RTL passed `sv_compile` across all 7 files and FIFO alone |

## Directed scenario coverage

The directed manifest requires and observed 31 scenarios in exact order:

```text
SC_APB_RESET
SC_APB_RW
SC_APB_INVALID
SC_TX_ONE_BYTE
SC_TX_BACK_TO_BACK
SC_TX_IRQ
SC_RX_ONE_BYTE
SC_RX_BACK_TO_BACK
SC_RX_FRAMING_ERROR
SC_RX_OVERRUN
SC_RX_IRQ
SC_BAUD_VARIANTS
SC_RX_MAJORITY_NOISE
SC_RX_FALSE_START
SC_FRAME_CFG
SC_TX_DATA_WIDTHS
SC_RX_DATA_WIDTHS
SC_TX_PARITY_EVEN_ODD
SC_RX_PARITY_GOOD
SC_RX_PARITY_ERROR
SC_TX_STOP2
SC_RX_STOP2
SC_TX_FIFO_BURST
SC_RX_FIFO_ORDER
SC_TX_FIFO_FULL
SC_FIFO_CLEAR
SC_FIFO_THRESHOLD_IRQ
SC_RX_TIMEOUT_IRQ
SC_LOOPBACK
SC_BREAK
SC_SCRATCH
```

Important v2+ bins hit include frame configuration readback, TX/RX data-width masking, TX/RX parity, parity error with IRQ/data preservation, two-stop TX/RX behavior, TX/RX FIFO ordering, TX FIFO full write error, FIFO clear, FIFO threshold IRQ, RX timeout IRQ, loopback, break handling, and scratch no-side-effect behavior.

## Random regression evidence

The enhanced random regression testbench produces deterministic JSON/CSV evidence and per-failure detail. The current signoff run used:

```bash
cd apb_uart_txrx_demo && ./sim/run_random_regression.sh 7 20
```

Current summary artifact:

```text
apb_uart_txrx_demo/sim/random/random_regression_summary.json
```

Recorded values:

```text
passed=true
seed_list=7
requested_txns=20
effective_txns_by_seed.7=20
scoreboard_pass_total=70
scoreboard_fail_total=0
csv_fail_rows_total=0
all_coverage_flags_hit=true
artifacts:
  sim/random/random_seed_7.json
  sim/random/random_seed_7.csv
  sim/random/random_seed_7.log
```

Random coverage flags all hit for seed 7:

```text
frame_cfg
tx_frame_config
rx_frame_config
parity_good
parity_error
stop2
tx_fifo_burst
rx_fifo_order
fifo_full
overrun
threshold_irq
timeout_irq
loopback
invalid_access
break_error
scratch
```

## Waveform/debug evidence

`sim/run_sim.sh` generated waveform evidence without modifying DUT RTL for waveform dumping:

```text
apb_uart_txrx_demo/sim/waveform_manifest.json
apb_uart_txrx_demo/sim/waves/apb_uart_txrx_demo.vcd
```

Manifest values:

```text
status=pass
testbench_only=true
dut_source_modified_for_waveforms=false
waveform.exists=true
waveform.size_bytes=370717
```

Required top-level signal presence is true for:

```text
pclk, preset_n, psel, penable, pwrite, paddr, pwdata, prdata,
pready, pslverr, uart_tx, uart_rx, irq
```

## Waivers and caveats

### Waiver: exact-path `sv_compile` stale diagnostic

- **Observed**: `sv_compile` on exact repo paths repeated stale diagnostics including a FIFO line-48 select-expression error, stale `.full`/`.empty` port messages, missing `fifo_full`/`fifo_empty`, and old unconnected `rx_valid_hw_set`/`rx_data_hw` messages.
- **Why waived**: These diagnostics do not match the current source:
  - `uart_fifo_sync.sv` exposes `fifo_full` and `fifo_empty` ports.
  - Current line 48 is reset assignment `wr_ptr <= PTR_ZERO`, not a select expression.
  - Top-level FIFO instances connect `.fifo_full(...)` and `.fifo_empty(...)`.
  - Grep found no stale `.full`/`.empty` instantiations or `rx_valid_hw_set`/`rx_data_hw` top connections.
- **Independent evidence**: Icarus RTL-only compile passed, directed/random builds passed, Verilator lint passed, and byte-identical temp copies under `/tmp/apb_uart_svcompile_signoff` passed `sv_compile` for all 7 RTL files and FIFO alone.

### Waiver: SSOT canonical section order warning

- **Observed**: `verify_ssot(... mode=starter, preview=strict)` reports warning `ssot.canonical_order`.
- **Why waived**: The validation report has `ok=true`, `blockers=[]`, disk check pass, and zero TBDs. The warning is non-semantic in starter-mode signoff.

## Residual exclusions / non-goals

The signed-off scope is still a bounded APB UART demo, not a full 16550-class or SoC-integrated UART. Explicit non-goals remain:

- no RTS/CTS hardware flow-control pins;
- no modem-control pins;
- no DMA interface;
- no fractional baud generator;
- no additional top-level pins beyond the preserved APB/UART/IRQ interface;
- no multi-clock CDC hardening beyond the local UART RX synchronizer/loopback path;
- no formal proof signoff;
- no physical implementation, board timing, or ASIC backend signoff;
- SDC values are documented placeholders that SoC/board owners must tighten for integration.

## Primary evidence artifacts

```text
apb_uart_txrx_demo/sim/sim.log
apb_uart_txrx_demo/sim/sim_results.json
apb_uart_txrx_demo/sim/scoreboard_events.csv
apb_uart_txrx_demo/sim/coverage_results.json
apb_uart_txrx_demo/sim/waveform_manifest.json
apb_uart_txrx_demo/sim/waves/apb_uart_txrx_demo.vcd
apb_uart_txrx_demo/sim/random/random_regression_summary.json
apb_uart_txrx_demo/sim/random/random_seed_7.json
apb_uart_txrx_demo/sim/random/random_seed_7.csv
apb_uart_txrx_demo/sim/random/random_seed_7.log
apb_uart_txrx_demo/req/ssot_validation.json
apb_uart_txrx_demo/sdc/apb_uart_txrx_demo.sdc
```

## Final status

**GO** for the enhanced v2+ bounded UART demo at the repository evidence level.

The GO decision depends on the waivers above and the cited local artifacts. Any product/release signoff should rerun the same commands in the target CI/orchestrated environment and confirm that the generated artifacts still match these pass/fail numbers.

## Related

- [[apb-uart-real-uart-signoff-20260527]]
- [[golden-todo-evidence]]
- [[default-agent-ip-flow]]
- [[pipeline-progress-debugging]]
