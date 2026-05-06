// =============================================================================
// uart_baud.v — 16x Baud Rate Clock Divider
// =============================================================================
`default_nettype none
`include "uart_defines.vh"

module uart_baud (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] divisor,
    output reg         baud_tick,
    output reg  [3:0]  sample_count
);

    reg [15:0] counter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter      <= 16'd0;
            baud_tick    <= 1'b0;
            sample_count <= 4'd0;
        end else begin
            baud_tick <= 1'b0;
            if (counter >= divisor) begin
                counter   <= 16'd0;
                baud_tick <= 1'b1;
                if (sample_count >= 4'd15)
                    sample_count <= 4'd0;
                else
                    sample_count <= sample_count + 4'd1;
            end else begin
                counter <= counter + 16'd1;
            end
        end
    end

endmodule

`default_nettype wire
