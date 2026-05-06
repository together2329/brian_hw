`default_nettype none

// Auto-generated manifest submodule.
// Byte-level I2C transaction FSM
module demo_i2c_ui4_byte_ctrl (
    input wire clk,
    input wire rst_n
);
    reg alive_q;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            alive_q <= 1'b0;
        end else begin
            alive_q <= 1'b1;
        end
    end
endmodule

`default_nettype wire
