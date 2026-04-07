//============================================================================
// Module      : counter
// Description : Parameterized synchronous up/down counter with async reset,
//               parallel load, enable, overflow and zero (underflow) flags.
//               Clean synthesizable Verilog-2001.
//============================================================================

module counter #(
    parameter int WIDTH = 8
)(
    input  wire             clk,       // Clock (posedge active)
    input  wire             rst_n,     // Async active-low reset
    input  wire             en,        // Count enable
    input  wire             up_down,   // 1 = count up, 0 = count down
    input  wire             load,      // Parallel load enable
    input  wire [WIDTH-1:0] d,         // Parallel load data
    output reg  [WIDTH-1:0] q,         // Counter output
    output wire             overflow,  // Pulse: counted past max value (roll-over)
    output wire             zero       // Pulse: counted past zero (roll-under)
);

    // -------------------------------------------------------------------------
    // Maximum count value (all 1s for given WIDTH)
    // -------------------------------------------------------------------------
    localparam [WIDTH-1:0] MAX_VAL = {WIDTH{1'b1}};

    // -------------------------------------------------------------------------
    // Sequential logic: async reset, synchronous load / count
    // -------------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q <= {WIDTH{1'b0}};
        end else if (load) begin
            q <= d;
        end else if (en) begin
            if (up_down)
                q <= q + 1'b1;
            else
                q <= q - 1'b1;
        end
    end

    // -------------------------------------------------------------------------
    // Overflow flag: asserted for 1 cycle when counter wraps from MAX u2192 0
    // -------------------------------------------------------------------------
    assign overflow = (en && up_down && !load && (q == MAX_VAL));

    // -------------------------------------------------------------------------
    // Zero (underflow) flag: asserted for 1 cycle when counter wraps from 0 u2192 MAX
    // -------------------------------------------------------------------------
    assign zero = (en && !up_down && !load && (q == {WIDTH{1'b0}}));

endmodule
