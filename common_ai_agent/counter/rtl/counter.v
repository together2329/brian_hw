//----------------------------------------------------------------------------
// Module:       counter
// Description:  Parametric N-bit up/down counter with async reset, enable,
//               parallel load, and overflow/underflow detection.
//
// Ports:
//   clk      - Clock (rising edge)
//   rst_n    - Active-low asynchronous reset
//   en       - Count enable (active high)
//   up_dn    - Direction: 1 = count up, 0 = count down
//   load     - Parallel load enable (active high, takes priority over count)
//   din      - Parallel load data input [WIDTH-1:0]
//   count    - Current count value output [WIDTH-1:0]
//   overflow - Pulse flag: 1 when count rolls over (maxu21920) or underflows (0u2192max)
//
// Parameters:
//   WIDTH    - Bit width of counter (default 8, min 1)
//----------------------------------------------------------------------------

module counter #(
    parameter int WIDTH = 8
)(
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    input  wire             up_dn,
    input  wire             load,
    input  wire [WIDTH-1:0] din,
    output reg  [WIDTH-1:0] count,
    output reg              overflow
);

    // Local constants for min/max values
    localparam [WIDTH-1:0] MAX_VAL = {WIDTH{1'b1}};
    localparam [WIDTH-1:0] MIN_VAL = {WIDTH{1'b0}};

    //--------------------------------------------------------------------------
    // Sequential logic: async reset, rising-edge clock
    //--------------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Asynchronous reset: clear counter and overflow flag
            count    <= MIN_VAL;
            overflow <= 1'b0;
        end else begin
            overflow <= 1'b0;  // default: clear overflow each cycle

            if (load) begin
                // Parallel load has highest priority
                count <= din;
            end else if (en) begin
                if (up_dn) begin
                    // Count up
                    if (count == MAX_VAL) begin
                        count    <= MIN_VAL;
                        overflow <= 1'b1;
                    end else begin
                        count <= count + 1'b1;
                    end
                end else begin
                    // Count down
                    if (count == MIN_VAL) begin
                        count    <= MAX_VAL;
                        overflow <= 1'b1;
                    end else begin
                        count <= count - 1'b1;
                    end
                end
            end
            // else: en=0 u2192 hold current value
        end
    end

    //--------------------------------------------------------------------------
    // Parameter sanity check (simulation only)
    //--------------------------------------------------------------------------
    initial begin
        if (WIDTH < 1) begin
            $error("counter: WIDTH must be >= 1 (got %0d)", WIDTH);
            $finish;
        end
    end

endmodule
