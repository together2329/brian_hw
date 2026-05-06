`default_nettype none

// Auto-generated manifest submodule.
// Top-level integration wrapper
module qa_visible_09182_wrapper (
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
