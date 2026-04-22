// ============================================================================
// Module: timer
// Description: Parameterized timer with prescaler, one-shot/periodic modes,
//              and timeout interrupt pulse.
//
// Features:
//   - Prescaler resets when timer is disabled/stopped for deterministic first tick
//   - Prescaler divides input clock by (prescaler + 1) to produce timer ticks
//   - ps_tick is combinational for zero-latency prescaler-to-counter path
//   - Counts up from 0; generates timeout pulse when count == compare_val
//   - Periodic mode (mode=1): auto-reloads count to 0 after timeout, continues
//   - One-shot mode (mode=0): holds count after timeout, auto-disables (running=0)
//     Re-arming requires de-asserting timer_en for at least 1 cycle
//   - Synchronous reset (active-low), parameterized counter and prescaler widths
//   - Running flag indicates the timer is actively counting
// ============================================================================

module timer #(
    parameter int WIDTH       = 16,  // Counter width (bits)
    parameter int PRESCALER_W = 8    // Prescaler width (bits)
)(
    input  logic                      clk,          // System clock
    input  logic                      rst_n,        // Synchronous reset, active-low
    input  logic                      timer_en,     // Timer enable (start/stop)
    input  logic                      mode,         // 0 = one-shot, 1 = periodic
    input  logic [PRESCALER_W-1:0]    prescaler,    // Clock divider value (tick every prescaler+1 clks)
    input  logic [WIDTH-1:0]          compare_val,  // Timeout compare value
    output logic [WIDTH-1:0]          count,        // Current timer count
    output logic                      timeout,      // Pulse: count reached compare_val (1 cycle)
    output logic                      running       // Timer is actively counting
);

    // ---------------------------------------------------------------------------
    // Internal signals
    // ---------------------------------------------------------------------------
    logic [PRESCALER_W:0] ps_counter;   // Prescaler counter (one bit wider for wrap detect)
    logic                 stopped;      // One-shot auto-stop flag (cleared when timer_en goes low)

    // Combinational prescaler tick: fires when ps_counter reaches prescaler value
    // Uses registered ps_counter, so tick is available in same always_ff evaluation
    wire ps_tick = timer_en & ~stopped & (ps_counter == {1'b0, prescaler});

    // ---------------------------------------------------------------------------
    // Prescaler: count from 0 to prescaler, then reset
    // Resets when timer is disabled or one-shot is stopped for deterministic startup
    // ---------------------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            ps_counter <= '0;
        end else if (timer_en && !stopped) begin
            if (ps_counter == {1'b0, prescaler}) begin
                ps_counter <= '0;
            end else begin
                ps_counter <= ps_counter + 1'b1;
            end
        end else begin
            // Timer disabled or one-shot stopped: reset prescaler
            ps_counter <= '0;
        end
    end

    // ---------------------------------------------------------------------------
    // One-shot stop flag management
    // Set when one-shot timeout occurs; cleared when timer_en is de-asserted or reset
    // ---------------------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            stopped <= 1'b0;
        end else if (!timer_en) begin
            stopped <= 1'b0;  // Re-arm: clear stop when timer is disabled
        end else if (ps_tick && count == compare_val && !mode) begin
            stopped <= 1'b1;  // One-shot completed
        end
    end

    // ---------------------------------------------------------------------------
    // Main counter and timeout logic
    // ---------------------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            count   <= '0;
            timeout <= 1'b0;
            running <= 1'b0;
        end else begin
            // Default: clear timeout pulse each cycle
            timeout <= 1'b0;

            if (timer_en && !stopped) begin
                running <= 1'b1;

                if (ps_tick) begin
                    if (count == compare_val) begin
                        // Timeout event
                        timeout <= 1'b1;
                        if (mode) begin
                            // Periodic: reload and continue
                            count <= '0;
                        end else begin
                            // One-shot: hold count (stopped flag set above)
                            count   <= count;
                            running <= 1'b0;
                        end
                    end else begin
                        // Normal increment
                        count <= count + 1'b1;
                    end
                end
            end else begin
                // Timer disabled or one-shot stopped: hold count, not running
                running <= 1'b0;
            end
        end
    end

endmodule
