//============================================================================
// Module: counter
// Description: Parameterized N-bit up/down counter with synchronous reset,
//              count enable, parallel load, and overflow detection.
//============================================================================

module counter #(
    parameter WIDTH = 8  // Counter bit width
)(
    input  wire             clk,       // Clock
    input  wire             rst_n,     // Active-low synchronous reset
    input  wire             en,        // Count enable
    input  wire             load,      // Parallel load enable
    input  wire             up_down,   // Direction: 0 = up, 1 = down
    input  wire [WIDTH-1:0] data_in,   // Parallel load data
    output reg  [WIDTH-1:0] count_out, // Current count value
    output reg              overflow   // Overflow/underflow pulse (1 cycle)
);

    // Maximum count value
    localparam [WIDTH-1:0] MAX_VAL = {WIDTH{1'b1}};

    always @(posedge clk) begin
        if (!rst_n) begin
            // Synchronous reset — highest priority
            count_out <= {WIDTH{1'b0}};
            overflow  <= 1'b0;
        end else if (load) begin
            // Parallel load — second priority
            count_out <= data_in;
            overflow  <= 1'b0;
        end else if (en) begin
            if (!up_down) begin
                // Count up
                if (count_out == MAX_VAL) begin
                    count_out <= {WIDTH{1'b0}};
                    overflow  <= 1'b1;
                end else begin
                    count_out <= count_out + 1'b1;
                    overflow  <= 1'b0;
                end
            end else begin
                // Count down
                if (count_out == {WIDTH{1'b0}}) begin
                    count_out <= MAX_VAL;
                    overflow  <= 1'b1;
                end else begin
                    count_out <= count_out - 1'b1;
                    overflow  <= 1'b0;
                end
            end
        end else begin
            // Disabled — hold value
            overflow <= 1'b0;
        end
    end

endmodule
