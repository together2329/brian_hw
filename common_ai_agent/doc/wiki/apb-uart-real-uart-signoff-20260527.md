# APB UART Real-UART Signoff — 2026-05-27

> **STATUS: SUPERSEDED by [[apb-uart-enhanced-signoff-20260527]]** — the active
> DUT uses framed engines (`uart_rx_framed.sv` / `uart_tx_framed.sv`, per
> `apb_uart_txrx_demo/list/apb_uart_txrx_demo.f`); the 8n1 modules
> (`uart_rx_8n1.sv` / `uart_tx_8n1.sv`) described here are obsolete. Kept below
> as a historical record.

> **Scope**: Current quality/status record for `apb_uart_txrx_demo` after the RX path was upgraded from a simple single-sample UART receiver to a bounded production-style 8N1 receiver.  
> **Decision**: **GO for bounded real-UART APB demo signoff**.  
> **Authority caveat**: This is local default-agent evidence, not a visible ATLAS UI/orchestrator product-flow proof. Validate product-flow claims through the common UI/API/worker path described in [[pipeline-progress-debugging]].

## What changed

`apb_uart_txrx_demo` keeps the same APB/UART top-level interface and register map, but the RX implementation is now materially closer to a real UART:

- two-flop synchronized `uart_rx` input;
- baud-derived early/center/late sample positions with a 16x-style center spread;
- 3-sample majority voting for start, data, and stop decisions;
- false-start/glitch rejection before entering data receive;
- stop-bit majority framing detection;
- overrun handling still preserves the old RX data through the register block.

The relevant implementation is `apb_uart_txrx_demo/rtl/uart_rx_8n1.sv`.

## Fresh evidence summary

| Gate | Result |
|---|---|
| Directed simulation | PASS: `passed=true`, `scoreboard_pass=35`, `scoreboard_fail=0`, `scenario_count=14` |
| Real-UART directed scenarios | PASS: `SC_RX_MAJORITY_NOISE`, `SC_RX_FALSE_START` |
| Directed coverage | PASS: `29/29` bins hit, `missed_bins=0`, `waived_bins=0`, `effective_coverage_pct=100.0` |
| Waveform/debug | PASS: VCD exists at `sim/waves/apb_uart_txrx_demo.vcd`, size `131233` bytes, all required top APB/UART/IRQ signals observed |
| Random smoke | PASS: seed `7`, `txns=12`, `scoreboard_fail_total=0` |
| Static/lint | PASS: `sv_compile` clean, directed/random iverilog builds pass, Verilator warning count `0` |
| SSOT validation | PASS with `blockers=0`; only non-semantic starter-mode canonical-order warning waived |
| Final adversarial review | `recommendation=GO`, `issues=[]` |

## Directed scenarios now required

The directed run now requires 14 scenarios:

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
```

The two added real-UART scenarios prove bounded majority-vote noise tolerance and false-start recovery.

## Real-UART coverage bins

The new real-UART bins are all required and hit:

```text
rx_majority_noise_valid
rx_majority_noise_no_errors
rx_majority_noise_data
rx_false_start_rejected
rx_false_start_recovery
```

`sim/run_sim.sh` now regenerates both `sim/coverage_results.json` and `sim/waveform_manifest.json` after `vvp`, then fails nonzero if either manifest is not passing. This prevents a green scoreboard from hiding stale coverage or waveform evidence.

## Reproduce the evidence

Run from repo root unless noted:

```bash
cd apb_uart_txrx_demo && ./sim/run_sim.sh
cd apb_uart_txrx_demo && ./sim/run_random_regression.sh 7 12
# plus SSOT/static checks used for signoff:
# verify_ssot(ip=apb_uart_txrx_demo, mode=starter, root=., preview=strict)
# sv_compile over the decomposed RTL filelist
# verilator --lint-only -Wall -Wno-fatal -f list/apb_uart_txrx_demo.f
```

Primary evidence files:

```text
apb_uart_txrx_demo/sim/sim_results.json
apb_uart_txrx_demo/sim/scoreboard_events.csv
apb_uart_txrx_demo/sim/coverage_results.json
apb_uart_txrx_demo/sim/waveform_manifest.json
apb_uart_txrx_demo/sim/random/random_regression_summary.json
apb_uart_txrx_demo/verify/static_signoff_results.json
apb_uart_txrx_demo/verify/verilator_lint.log
.session/apb_uart_txrx_demo/signoff/final_signoff_bundle.json
.session/apb_uart_txrx_demo/signoff/final_signoff_report.md
.session/apb_uart_txrx_demo/signoff/final_adversarial_review.json
```

## Residual risks / non-goals

This is a bounded APB UART demo, not a full 16550-class UART. The signed-off scope excludes:

- parity;
- configurable stop/data width;
- FIFOs;
- modem pins;
- DMA;
- hardware flow control;
- CDC hardening beyond the local RX synchronizer;
- formal proofs;
- backend ASIC signoff.

The only recorded waiver is `ssot.canonical_order`: canonical sections are present but not in the standard order. It is waived because it is non-semantic in starter mode and SSOT blockers are zero.

## Relationship to the default-agent flow

This is the current quality snapshot for the `apb_uart_txrx_demo` reference run used by [[default-agent-ip-flow]]. It is also a concrete example of the evidence discipline described in [[golden-todo-evidence]]: complete the implementation, rerun fresh artifacts, reread ground truth, then approve only with cited evidence.

## Related

- [[default-agent-ip-flow]]
- [[golden-todo-evidence]]
- [[pipeline-progress-debugging]]
- [[workflow-ownership-and-boundaries]]
