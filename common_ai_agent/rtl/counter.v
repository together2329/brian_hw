//-----------------------------------------------------------------------------
// Module: counter
// Description: Parameterizable synchronous up/down counter with enable,
//              synchronous reset, and configurable width.
//
// Parameters:
//   WIDTH - Counter bit width (default: 8)
//
// Ports:
//   clk       - Clock (posedge active)
//   rst_n     - Synchronous active-low reset
//   en        - Count enable
//   up_down   - Direction: 1 = up, 0 = down
//   load      - Load data_in into counter
//   data_in   - Parallel data input [WIDTH-1:0]
//   count     - Current count value [WIDTH-1:0]
//   overflow  - Pulse when counter rolls over (max -> 0 going up)
//   underflow - Pulse when counter rolls under (0 -> max going down)
//-----------------------------------------------------------------------------

`timescale 1ns / 1ps

module counter #(
    parameter WIDTH = 8
)(
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    input  wire             up_down,   // 1: count up, 0: count down
    input  wire             load,
    input  wire [WIDTH-1:0] data_in,
    output reg  [WIDTH-1:0] count,
    output reg              overflow,
    output reg              underflow
);

    // Maximum value for width
    localparam [WIDTH-1:0] MAX_VAL = {WIDTH{1'b1}};

    always @(posedge clk) begin
        if (!rst_n) begin
            // Synchronous active-low reset
            count     <= {WIDTH{1'b0}};
            overflow  <= 1'b0;
            underflow <= 1'b0;
        end else if (load) begin
            // Parallel load has highest priority after reset
            count     <= data_in;
            overflow  <= 1'b0;
            underflow <= 1'b0;
        end else if (en) begin
            if (up_down) begin
                // Count up
                overflow  <= (count == MAX_VAL);
                count     <= count + 1'b1;
            end else begin
                // Count down
                underflow <= (count == {WIDTH{1'b0}});
                count     <= count - 1'b1;
            end
        end else begin
            // Disabled — hold value, clear flags
            overflow  <= 1'b0;
            underflow <= 1'b0;
        end
    end

endmodule
