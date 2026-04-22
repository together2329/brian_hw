// ============================================================================
// Module: counter
// Description: Parameterized N-bit up/down counter with synchronous reset,
//              parallel load, and overflow/underflow detection.
//              Priority: load > up > down (simultaneous up+down → up wins).
// ============================================================================

module counter #(
    parameter int WIDTH = 8
)(
    input  logic             clk,
    input  logic             rst_n,      // Synchronous reset, active-low
    input  logic             up_en,      // Count up enable
    input  logic             down_en,    // Count down enable
    input  logic             load_en,    // Parallel load enable
    input  logic [WIDTH-1:0] load_data,  // Data to load
    output logic [WIDTH-1:0] count,      // Current count value
    output logic             overflow,   // Pulse: count wrapped from max → 0
    output logic             underflow   // Pulse: count wrapped from 0 → max
);

    // Constant for maximum count value
    localparam logic [WIDTH-1:0] MAX_VAL = {WIDTH{1'b1}};

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            // Synchronous reset
            count     <= '0;
            overflow  <= 1'b0;
            underflow <= 1'b0;
        end else begin
            // Default: clear flags each cycle
            overflow  <= 1'b0;
            underflow <= 1'b0;

            if (load_en) begin
                // Priority 1: Parallel load
                count <= load_data;
            end else if (up_en) begin
                // Priority 2: Count up (wins over down when both asserted)
                if (count == MAX_VAL) begin
                    count    <= '0;
                    overflow <= 1'b1;
                end else begin
                    count <= count + 1'b1;
                end
            end else if (down_en) begin
                // Priority 3: Count down
                if (count == '0) begin
                    count      <= MAX_VAL;
                    underflow  <= 1'b1;
                end else begin
                    count <= count - 1'b1;
                end
            end
            // else: hold — count unchanged, flags stay 0
        end
    end

endmodule
