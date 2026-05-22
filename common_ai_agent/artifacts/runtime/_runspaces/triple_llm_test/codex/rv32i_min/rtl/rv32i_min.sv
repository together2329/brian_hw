module rv32i_min #(
    parameter integer XLEN = 32,
    parameter integer RESET_PC = 0,
    parameter integer INST_ALIGN = 4
) (
    input  logic             clk,
    input  logic             rst_n,
    output logic [XLEN-1:0]  i_addr,
    input  logic [XLEN-1:0]  i_rdata,
    output logic             i_valid,
    input  logic             alu_result,
    input  logic             branch_imm,
    input  logic             branch_taken,
    input  logic             illegal_shamt,
    input  logic             imm,
    input  logic             is_ebreak,
    input  logic             is_ecall,
    input  logic             is_jalr,
    input  logic             is_store,
    input  logic             load_data_ext,
    input  logic             misaligned_access,
    input  logic             rs1,
    output logic [XLEN-1:0]  d_addr,
    output logic [XLEN-1:0]  d_wdata,
    input  logic [XLEN-1:0]  d_rdata,
    output logic             d_we,
    output logic [3:0]       d_be,
    output logic             d_valid,
    output logic             excpt_o
);

    logic [XLEN-1:0] if_i_addr;
    logic            if_i_valid;

    logic [XLEN-1:0] mem_d_addr;
    logic [XLEN-1:0] mem_d_wdata;
    logic            mem_d_we;
    logic [3:0]      mem_d_be;
    logic            mem_d_valid;

    logic            core_excpt_o;

    logic            top_input_use_reduce;

    assign i_addr  = if_i_addr;
    assign i_valid = if_i_valid;

    assign d_addr  = mem_d_addr;
    assign d_wdata = mem_d_wdata;
    assign d_we    = mem_d_we;
    assign d_be    = mem_d_be;
    assign d_valid = mem_d_valid;

    assign excpt_o = core_excpt_o;

    assign top_input_use_reduce = alu_result ^ branch_imm ^ branch_taken ^ illegal_shamt ^ imm ^
                                  is_ebreak ^ is_ecall ^ is_jalr ^ is_store ^ load_data_ext ^
                                  misaligned_access ^ rs1 ^ d_rdata[0] ^ i_rdata[0];

    rv32i_min_if #(
        .XLEN(XLEN),
        .RESET_PC(RESET_PC),
        .INST_ALIGN(INST_ALIGN)
    ) u_rv32i_min_if (
        .clk(clk),
        .rst_n(rst_n),
        .i_addr(if_i_addr),
        .i_valid(if_i_valid),
        .i_rdata(i_rdata)
    );

    rv32i_min_idex #(
        .XLEN(XLEN)
    ) u_rv32i_min_idex (
        .clk(clk),
        .rst_n(rst_n)
    );

    rv32i_min_memwb #(
        .XLEN(XLEN)
    ) u_rv32i_min_memwb (
        .clk(clk),
        .rst_n(rst_n),
        .d_addr(mem_d_addr),
        .d_wdata(mem_d_wdata),
        .d_rdata(d_rdata),
        .d_we(mem_d_we),
        .d_be(mem_d_be),
        .d_valid(mem_d_valid)
    );

    rv32i_min_regfile #(
        .XLEN(XLEN)
    ) u_rv32i_min_regfile (
        .clk(clk),
        .rst_n(rst_n)
    );

    rv32i_min_core #(
        .XLEN(XLEN),
        .RESET_PC(RESET_PC),
        .INST_ALIGN(INST_ALIGN)
    ) u_rv32i_min_core (
        .clk(clk),
        .rst_n(rst_n),
        .excpt_o(core_excpt_o)
    );

endmodule
