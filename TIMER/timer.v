`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: timer
// Description: 32-bit countdown timer with 16-bit prescaler and period register.
//
// Ports:
//   clk         - Rising-edge clock
//   rst_n       - Active-low synchronous reset
//   enable      - Timer count enable
//   load        - Synchronous load: loads period into counter & latches prescaler
//   prescaler   - 16-bit clock divider (1 = no division, N = divide by N)
//   period      - 32-bit countdown start value (loaded on load or auto-reload)
//   auto_reload - When set, timer reloads period on reaching zero
//   timer_out   - Current 32-bit counter value (read-only)
//   done        - Single-clock pulse when counter reaches zero
//   running     - High while timer is actively counting
//
// Operation:
//   - The prescaler divides the clock. When prescaler=1, the counter
//     decrements every clock. When prescaler=N, the counter decrements
//     every N clocks.
//   - On load, the period value is loaded into the counter and the
//     prescaler value is latched internally.
//   - The counter decrements by 1 each prescaler tick.
//   - When counter reaches 0, done pulses for one clock.
//   - If auto_reload is set, counter reloads period and continues.
//     Otherwise it stops.
//   - load has priority over counting.
//----------------------------------------------------------------------------

module timer (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         enable,
    input  wire         load,
    input  wire [15:0]  prescaler,
    input  wire [31:0]  period,
    input  wire         auto_reload,
    output wire [31:0]  timer_out,
    output reg          done,
    output wire         running
);

    //--------------------------------------------------------------------------
    // Internal registers
    //--------------------------------------------------------------------------
    reg [31:0] count;          // 32-bit down-counter
    reg [15:0] psr;            // Prescaler shadow register (latched on load)
    reg [15:0] ps_count;       // Prescaler down-counter

    //--------------------------------------------------------------------------
    // Prescaler tick generation
    //--------------------------------------------------------------------------
    wire ps_tick = (ps_count == 16'd1);

    always @(posedge clk) begin
        if (!rst_n) begin
            ps_count <= 16'd1;
            psr      <= 16'd1;
        end else if (load) begin
            // Latch new prescaler value and reset prescaler counter
            psr      <= prescaler;
            ps_count <= prescaler;
        end else if (enable && (count != 32'd0)) begin
            // Count down prescaler while timer is running
            if (ps_tick) begin
                ps_count <= psr;
            end else begin
                ps_count <= ps_count - 16'd1;
            end
        end
    end

    //--------------------------------------------------------------------------
    // Timer counter logic
    //--------------------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 32'd0;
            done  <= 1'b0;
        end else begin
            // Default: clear done pulse after one cycle
            done <= 1'b0;

            if (load) begin
                // Load takes highest priority
                count <= period;
            end else if (enable && (count != 32'd0) && ps_tick) begin
                // Decrement counter on prescaler tick
                count <= count - 32'd1;

                // Terminal count: counter will be zero next tick
                if (count == 32'd1) begin
                    done <= 1'b1;
                    if (auto_reload) begin
                        count <= period;
                    end
                end
            end
        end
    end

    //--------------------------------------------------------------------------
    // Output assignments
    //--------------------------------------------------------------------------
    assign timer_out = count;
    assign running   = enable && (count != 32'd0);

endmodule
