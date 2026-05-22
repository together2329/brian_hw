module arm_m0_min_ex #(
    parameter integer XLEN = 32,
    parameter integer ENABLE_FAULT_HALT = 1
) (
    input  logic             clk,
    input  logic             rst,
    input  logic             id_valid,
    input  logic [XLEN-1:0]  pc_in,
    input  logic [XLEN-1:0]  rs1_data,
    input  logic [XLEN-1:0]  rs2_data,
    input  logic [3:0]       rd_addr,
    input  logic [XLEN-1:0]  imm_ext,
    input  logic [3:0]       alu_op,
    input  logic             is_cmp,
    input  logic             is_ldr,
    input  logic             is_str,
    input  logic             is_b,
    input  logic             is_beq,
    input  logic             is_bne,
    input  logic             is_undef,
    input  logic             i_hready,
    input  logic             i_hresp,
    input  logic             d_hready,
    input  logic [XLEN-1:0]  d_hrdata,
    input  logic             d_hresp,
    output logic             rf_we,
    output logic [3:0]       rf_waddr,
    output logic [XLEN-1:0]  rf_wdata,
    output logic [3:0]       nzcv,
    output logic             fault_halt,
    output logic             hold_pc,
    output logic             branch_taken,
    output logic [XLEN-1:0]  branch_target,
    output logic [XLEN-1:0]  d_haddr,
    output logic [1:0]       d_htrans,
    output logic             d_hwrite,
    output logic [2:0]       d_hsize,
    output logic [2:0]       d_hburst,
    output logic [3:0]       d_hprot,
    output logic             d_hmastlock,
    output logic [XLEN-1:0]  d_hwdata
);
    localparam [2:0] ST_RESET = 3'd0,
                     ST_RUN = 3'd1,
                     ST_STALL_IF = 3'd2,
                     ST_STALL_MEM = 3'd3,
                     ST_FAULT_HALT = 3'd4;

    logic [2:0] state, next_state;
    logic [XLEN-1:0] alu_res;
    logic cmp_eq, cmp_neg;
    logic branch_taken_w;
    logic [XLEN-1:0] branch_target_w;

    arm_m0_min_alu #(.XLEN(XLEN)) u_alu (
        .alu_op(alu_op), .op_a(rs1_data), .op_b(rs2_data), .alu_res(alu_res), .cmp_eq(cmp_eq), .cmp_neg(cmp_neg)
    );

    arm_m0_min_branch #(.XLEN(XLEN)) u_branch (
        .pc_in(pc_in), .imm_ext(imm_ext), .is_b(is_b), .is_beq(is_beq), .is_bne(is_bne), .z_flag(nzcv[2]),
        .branch_taken(branch_taken_w), .branch_target(branch_target_w)
    );

    arm_m0_min_mem_if #(.XLEN(XLEN)) u_memif (
        .is_ldr(is_ldr), .is_str(is_str), .base_addr(rs1_data), .imm_ext(imm_ext), .store_data(rs2_data),
        .d_haddr(d_haddr), .d_htrans(d_htrans), .d_hwrite(d_hwrite), .d_hsize(d_hsize), .d_hburst(d_hburst),
        .d_hprot(d_hprot), .d_hmastlock(d_hmastlock), .d_hwdata(d_hwdata)
    );

    always @(posedge clk) begin
        if (rst) begin
            state <= ST_RESET;
            fault_halt <= 1'b0;
            nzcv <= 4'b0000;
        end else begin
            state <= next_state;
            if (ENABLE_FAULT_HALT == 1) begin
                if ((i_hready & i_hresp) || ((is_ldr || is_str) && d_hready && d_hresp) || (id_valid && is_undef))
                    fault_halt <= 1'b1;
            end
            if (is_cmp && id_valid && !fault_halt) begin
                nzcv[3] <= alu_res[XLEN-1];
                nzcv[2] <= cmp_eq;
                nzcv[1] <= 1'b0;
                nzcv[0] <= cmp_neg;
            end
        end
    end

    always @(*) begin
        next_state = state;
        case (state)
            ST_RESET: next_state = ST_RUN;
            ST_RUN: begin
                if (fault_halt) next_state = ST_FAULT_HALT;
                else if (!i_hready) next_state = ST_STALL_IF;
                else if ((is_ldr || is_str) && !d_hready) next_state = ST_STALL_MEM;
            end
            ST_STALL_IF: begin
                if (fault_halt) next_state = ST_FAULT_HALT;
                else if (i_hready) next_state = ST_RUN;
            end
            ST_STALL_MEM: begin
                if (fault_halt) next_state = ST_FAULT_HALT;
                else if (d_hready && !d_hresp) next_state = ST_RUN;
            end
            ST_FAULT_HALT: next_state = ST_FAULT_HALT;
            default: next_state = ST_RESET;
        endcase
    end

    always @(*) begin
        rf_we = 1'b0;
        rf_waddr = rd_addr;
        rf_wdata = alu_res;
        hold_pc = 1'b0;
        branch_taken = 1'b0;
        branch_target = branch_target_w;

        if (state == ST_STALL_IF || state == ST_STALL_MEM || fault_halt)
            hold_pc = 1'b1;

        if (id_valid && !fault_halt) begin
            if (is_ldr) begin
                if (d_hready) begin
                    rf_we = 1'b1;
                    rf_wdata = d_hrdata;
                end
            end else if (is_str) begin
                rf_we = 1'b0;
            end else if (is_cmp) begin
                rf_we = 1'b0;
            end else if (is_b || is_beq || is_bne) begin
                branch_taken = branch_taken_w;
                rf_we = 1'b0;
            end else if (!is_undef) begin
                rf_we = 1'b1;
            end
        end
    end

endmodule
