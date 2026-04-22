// ============================================================================
// Interface: timer_if
// Description: SystemVerilog interface for the timer module.
//              Provides modports for both DUT and testbench connections.
//              Designed for compatibility with Icarus Verilog (no clocking blocks).
//
// Usage:
//   - DUT connects via dut modport
//   - Testbench drives/samples via tb modport
//   - TB drives clk and rst_n; uses @(posedge clk) + #1 for synchronous access
// ============================================================================

interface timer_if #(
    parameter int WIDTH       = 16,  // Counter width (must match timer instance)
    parameter int PRESCALER_W = 8    // Prescaler width (must match timer instance)
);

    // ---------------------------------------------------------------------------
    // Signals — mirror timer.sv ports exactly
    // ---------------------------------------------------------------------------
    logic                      clk;          // System clock (driven by TB)
    logic                      rst_n;        // Synchronous reset, active-low (driven by TB)
    logic                      timer_en;     // Timer enable (start/stop)
    logic                      mode;         // 0 = one-shot, 1 = periodic
    logic [PRESCALER_W-1:0]    prescaler;    // Clock divider value
    logic [WIDTH-1:0]          compare_val;  // Timeout compare value
    logic [WIDTH-1:0]          count;        // Current timer count (DUT output)
    logic                      timeout;      // Timeout pulse (DUT output)
    logic                      running;      // Timer running flag (DUT output)

    // ---------------------------------------------------------------------------
    // Modport: DUT — direct signal connections
    // ---------------------------------------------------------------------------
    modport dut (
        input  clk,
        input  rst_n,
        input  timer_en,
        input  mode,
        input  prescaler,
        input  compare_val,
        output count,
        output timeout,
        output running
    );

    // ---------------------------------------------------------------------------
    // Modport: TB — all signals accessible (TB drives inputs, samples outputs)
    // ---------------------------------------------------------------------------
    modport tb (
        output clk,
        output rst_n,
        output timer_en,
        output mode,
        output prescaler,
        output compare_val,
        input  count,
        input  timeout,
        input  running
    );

endinterface
