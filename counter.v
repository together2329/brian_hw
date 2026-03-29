`timescale 1ns / 1ps

/**
 * 8-bit Up Counter with Enable and Overflow Detection
 * 
 * Features:
 * - Asynchronous active-low reset
 * - Synchronous enable control
 * - Counts from 0 to 255 (8 bits)
 * - Overflow flag asserted when count reaches 255 and wraps to 0
 */

module counter (
    input  wire       clk,      // Clock input
    input  wire       rst_n,    // Asynchronous reset (active low)
    input  wire       en,       // Count enable
    output reg  [7:0] count,    // 8-bit count output
    output reg        overflow  // Overflow flag (pulse when count wraps from 255 to 0)
);

    // Counter logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset: counter to 0, overflow to 0
            count    <= 8'h00;
            overflow <= 1'b0;
        end else if (en) begin
            if (count == 8'hFF) begin
                // At max value, wrap to 0 and assert overflow
                count    <= 8'h00;
                overflow <= 1'b1;
            end else begin
                // Increment counter
                count    <= count + 8'h01;
                overflow <= 1'b0;
            end
        end else begin
            // Enable is low: hold current value, clear overflow
            count    <= count;
            overflow <= 1'b0;
        end
    end

endmodule
