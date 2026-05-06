`default_nettype none

// Auto-generated manifest submodule.
// Top-level integration wrapper
module demo_i2c_ui4_wrapper (
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
