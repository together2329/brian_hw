// -----------------------------------------------------------------------------
// counter.sv — Parameterized N-bit up-counter
//   - Async active-low reset (rst_n)
//   - Synchronous parallel load (load + d)
//   - Synchronous count enable (en)
//   - Rollover: wraps from 2^WIDTH-1 back to 0
// -----------------------------------------------------------------------------

`timescale 1ns/1ps

module counter #(
    parameter int WIDTH = 128
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             en,
    input  logic             load,
    input  logic [WIDTH-1:0] d,
    output logic [WIDTH-1:0] q
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            q <= '0;
        else if (load)
            q <= d;
        else if (en)
            q <= q + 1'b1;
        // else: hold current value
    end

endmodule
