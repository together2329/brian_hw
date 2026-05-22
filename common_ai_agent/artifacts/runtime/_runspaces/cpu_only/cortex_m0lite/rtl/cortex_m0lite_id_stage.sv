module id_stage #(
    parameter integer XLEN = 32
) (
    input  logic clk,
    input  logic rst_n,
    input  logic if_id_valid,
    output logic id_ex_valid,
    input  logic id_ex_ready
);
    // Consume XLEN parameter — SSOT requires this parameter for interface consistency
    wire xlen_ok;
    assign xlen_ok = (XLEN == 32);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) id_ex_valid <= 1'b0;
        else if (id_ex_ready) id_ex_valid <= if_id_valid;
    end
endmodule
