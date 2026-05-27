# uart_fifo_sync compile checker note

During Task 3, the `sv_compile` tool repeatedly returned a stale/path-specific diagnostic for the exact path `apb_uart_txrx_demo/rtl/uart_fifo_sync.sv`:

```text
Line 48: select expression is not allowed here
```

Ground-truth observations made during the task:

- The file was replaced with a tiny constant-output stub shorter than 48 lines, but the exact-path `sv_compile` result still reported line 48.
- Exact-content copies of the FIFO under other filenames passed `sv_compile`.
- `iverilog -g2012 -Wall -tnull rtl/uart_fifo_sync.sv` passed.
- `verilator --lint-only -Wall -Wno-fatal rtl/uart_fifo_sync.sv` passed after explicit DEPTH-derived casts were added.

Because exact-content copies pass and independent compilers accept the file, the remaining exact-path `sv_compile` diagnostic is treated as a stale tool/cache anomaly, not a source syntax defect. Full integrated `sv_compile` will be retried during the final signoff loop.
