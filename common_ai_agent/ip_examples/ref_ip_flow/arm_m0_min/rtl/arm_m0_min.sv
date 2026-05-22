module arm_m0_min #(
    parameter integer XLEN = 32,
    parameter integer RESET_PC = 0,
    parameter integer ENABLE_FAULT_HALT = 1
) (
    input  logic             clk,
    input  logic             rst,
    output logic [31:0]      i_haddr,
    output logic [1:0]       i_htrans,
    output logic             i_hwrite,
    output logic [2:0]       i_hsize,
    output logic [2:0]       i_hburst,
    output logic [3:0]       i_hprot,
    output logic             i_hmastlock,
    input  logic             i_hready,
    input  logic [31:0]      i_hrdata,
    input  logic             i_hresp,
    output logic [31:0]      d_haddr,
    output logic [1:0]       d_htrans,
    output logic             d_hwrite,
    output logic [2:0]       d_hsize,
    output logic [2:0]       d_hburst,
    output logic [3:0]       d_hprot,
    output logic             d_hmastlock,
    output logic [31:0]      d_hwdata,
    input  logic             d_hready,
    input  logic [31:0]      d_hrdata,
    input  logic             d_hresp
);

    logic [XLEN-1:0] pc;
    logic if_valid;
    logic [31:0] if_instr;
    logic id_valid;
    logic [3:0] rs1_addr, rs2_addr, rd_addr, rf_waddr;
    logic [XLEN-1:0] rs1_data, rs2_data, imm_ext, rf_wdata;
    logic [3:0] alu_op;
    logic is_cmp, is_ldr, is_str, is_b, is_beq, is_bne, is_undef;
    logic rf_we;
    logic [3:0] nzcv;
    logic fault_halt;
    logic hold_pc;
    logic branch_taken;
    logic [XLEN-1:0] branch_target;

    arm_m0_min_if #(.XLEN(XLEN), .RESET_PC(RESET_PC)) u_if (
        .clk(clk), .rst(rst), .fault_halt(fault_halt), .hold_pc(hold_pc), .branch_taken(branch_taken),
        .branch_target(branch_target), .pc_out(pc), .if_valid(if_valid), .if_instr(if_instr), .i_haddr(i_haddr),
        .i_htrans(i_htrans), .i_hwrite(i_hwrite), .i_hsize(i_hsize), .i_hburst(i_hburst), .i_hprot(i_hprot),
        .i_hmastlock(i_hmastlock), .i_hready(i_hready), .i_hrdata(i_hrdata), .i_hresp(i_hresp),
        .d_hready(d_hready), .d_hwdata(d_hwdata), .d_htrans(d_htrans)
    );

    arm_m0_min_id #(.XLEN(XLEN)) u_id (
        .fault_halt(fault_halt), .i_hready(i_hready), .i_hresp(i_hresp), .d_hready(d_hready), .d_hresp(d_hresp),
        .if_valid(if_valid), .if_instr(if_instr), .pc_in(pc), .nzcv(nzcv),
        .id_valid(id_valid), .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .rd_addr(rd_addr), .imm_ext(imm_ext), .alu_op(alu_op),
        .is_cmp(is_cmp), .is_ldr(is_ldr), .is_str(is_str), .is_b(is_b), .is_beq(is_beq), .is_bne(is_bne), .is_undef(is_undef)
    );

    arm_m0_min_rf #(.XLEN(XLEN)) u_rf (
        .clk(clk), .rst(rst), .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .rs1_data(rs1_data), .rs2_data(rs2_data),
        .we(rf_we), .rd_addr(rf_waddr), .rd_data(rf_wdata)
    );

    arm_m0_min_ex #(.XLEN(XLEN), .ENABLE_FAULT_HALT(ENABLE_FAULT_HALT)) u_ex (
        .clk(clk), .rst(rst), .id_valid(id_valid), .pc_in(pc), .rs1_data(rs1_data), .rs2_data(rs2_data), .rd_addr(rd_addr),
        .imm_ext(imm_ext), .alu_op(alu_op), .is_cmp(is_cmp), .is_ldr(is_ldr), .is_str(is_str), .is_b(is_b),
        .is_beq(is_beq), .is_bne(is_bne), .is_undef(is_undef), .i_hready(i_hready), .i_hresp(i_hresp),
        .d_hready(d_hready), .d_hrdata(d_hrdata), .d_hresp(d_hresp), .rf_we(rf_we), .rf_waddr(rf_waddr),
        .rf_wdata(rf_wdata), .nzcv(nzcv), .fault_halt(fault_halt), .hold_pc(hold_pc), .branch_taken(branch_taken),
        .branch_target(branch_target), .d_haddr(d_haddr), .d_htrans(d_htrans), .d_hwrite(d_hwrite), .d_hsize(d_hsize),
        .d_hburst(d_hburst), .d_hprot(d_hprot), .d_hmastlock(d_hmastlock), .d_hwdata(d_hwdata)
    );

endmodule
