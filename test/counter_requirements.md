# Counter Requirements

Confirmed implementation spec for this task set:

- Language: SystemVerilog
- RTL filename: `counter.sv`
- Testbench filename: `counter_tb.sv`
- Simulation helper filename: `Makefile`
- Counter width: 8 bits
- Counter direction: up-counter
- Count behavior: wraparound on overflow
- Reset: active-low asynchronous reset
- Reset value: `8'h00`
- Control input: enable (`en`)

Assumed top-level DUT interface to implement in RTL/TB:

- `input  logic clk`
- `input  logic rst_n`
- `input  logic en`
- `output logic [7:0] count`

No additional assumptions remain about reset polarity/type, count direction, width, or wrap behavior.
