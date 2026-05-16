module rv32i_min_core #(
    parameter integer XLEN = 32
) (
    input  logic         clk,
    input  logic         rst_n,

    input  logic [191:0] id_ex_reg_d,
    input  logic         id_ex_reg_we,
    output logic [191:0] id_ex_reg_q,

    input  logic [159:0] ex_mem_wb_reg_d,
    input  logic         ex_mem_wb_reg_we,
    output logic [159:0] ex_mem_wb_reg_q,

    output logic         excpt_o
);

    // SSOT memory.instances.id_ex_reg: depth=1, width=192, latency=0.
    // Implemented as a single clocked storage element with direct Q visibility.
    logic [191:0] id_ex_reg_storage;

    // SSOT memory.instances.ex_mem_wb_reg: depth=1, width=160, latency=0.
    // Implemented as a single clocked storage element with direct Q visibility.
    logic [159:0] ex_mem_wb_reg_storage;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            id_ex_reg_storage    <= 192'd0;
            ex_mem_wb_reg_storage <= 160'd0;
            excpt_o              <= 1'b0;
        end else begin
            if (id_ex_reg_we) begin
                id_ex_reg_storage <= id_ex_reg_d;
            end
            if (ex_mem_wb_reg_we) begin
                ex_mem_wb_reg_storage <= ex_mem_wb_reg_d;
            end
            excpt_o <= 1'b0;
        end
    end

    always @(*) begin
        id_ex_reg_q     = id_ex_reg_storage;
        ex_mem_wb_reg_q = ex_mem_wb_reg_storage;
    end

endmodule
