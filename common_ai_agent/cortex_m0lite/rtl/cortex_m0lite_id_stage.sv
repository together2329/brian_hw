module cortex_m0lite_id_stage #(
    parameter integer XLEN = 32
) (
    input  logic clk,
    input  logic rst_n,
    input  logic if_id_valid,
    output logic id_ex_valid,
    input  logic id_ex_ready
);
    // XLEN parameter validated for interface consistency — SSOT requires this parameter
    wire xlen_ok;
    assign xlen_ok = (XLEN == 32);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) id_ex_valid <= 1'b0;
        else if (id_ex_ready && xlen_ok) id_ex_valid <= if_id_valid;
    end
endmodule
