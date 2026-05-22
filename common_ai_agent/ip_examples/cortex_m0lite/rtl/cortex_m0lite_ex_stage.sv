module cortex_m0lite_ex_stage #(
    parameter integer XLEN = 32
) (
    input  logic clk,
    input  logic rst_n,
    input  logic id_ex_valid,
    output logic ex_wb_valid,
    output logic ex_bus_req
);
    // XLEN parameter validated for interface consistency — SSOT requires this parameter
    wire xlen_ok;
    assign xlen_ok = (XLEN == 32);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ex_wb_valid <= 1'b0;
            ex_bus_req <= 1'b0;
        end else begin
            ex_wb_valid <= id_ex_valid && xlen_ok;
            ex_bus_req <= id_ex_valid;
        end
    end
endmodule
