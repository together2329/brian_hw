// ============================================================================
// Module: counter
// Description: Parameterized N-bit up/down counter with synchronous controls
//              and asynchronous reset.
// ============================================================================

`timescale 1ns/1ps

module counter #(
    parameter int WIDTH = 8  // Counter width in bits
)(
    input  logic             clk,       // Clock
    input  logic             rst_n,     // Asynchronous active-low reset
    input  logic             enable,    // Count enable (active-high)
    input  logic             up_down,   // Direction: 1 = count up, 0 = count down
    input  logic             load,      // Synchronous load enable (active-high)
    input  logic [WIDTH-1:0] data_in,   // Data to load
    output logic [WIDTH-1:0] count,     // Current counter value
    output logic             zero,      // Flag: counter is zero
    output logic             overflow   // Flag: counter rolled over (max→0 or 0→max)
);

    // ------------------------------------------------------------------
    // Counter logic
    // ------------------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count    <= '0;
            overflow <= 1'b0;
        end else if (load) begin
            count    <= data_in;
            overflow <= 1'b0;
        end else if (enable) begin
            if (up_down) begin
                // Counting up
                overflow <= (count == {WIDTH{1'b1}});
                count    <= count + 1'b1;
            end else begin
                // Counting down
                overflow <= (count == '0);
                count    <= count - 1'b1;
            end
        end else begin
            overflow <= 1'b0;
        end
    end

    // ------------------------------------------------------------------
    // Zero flag (combinational)
    // ------------------------------------------------------------------
    assign zero = (count == '0);

endmodule
