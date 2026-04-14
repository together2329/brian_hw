//=============================================================================
// ARM CPU Core
// Integrates all datapath components: Register File, ALU, Shifter, Decoder,
// Control Unit, CPSR, Condition Checker
// 3-stage pipeline: FETCH -> DECODE/EXECUTE -> WRITEBACK
//=============================================================================

module arm_cpu_core (
    input  logic        clk,
    input  logic        rst_n,
    output logic [31:0] imem_addr,
    input  logic [31:0] imem_rdata,
    output logic        dmem_req,
    output logic        dmem_we,
    output logic        dmem_byte,
    output logic [31:0] dmem_addr,
    output logic [31:0] dmem_wdata,
    input  logic [31:0] dmem_rdata,
    input  logic        dmem_ready,
    output logic [31:0] debug_pc,
    output logic [31:0] debug_instr,
    output logic [3:0]  debug_state,
    output logic [31:0] debug_reg_r0,
    output logic [31:0] debug_reg_r1,
    output logic [31:0] debug_reg_r2,
    output logic [31:0] debug_reg_r3
);
    logic [31:0] pc_current;
    logic [31:0] instr;
    logic [31:0] pc_plus4, pc_plus8;
    logic [31:0] branch_target;

    logic [3:0]  cond, opcode, rn_addr, rd_addr;
    logic [11:0] operand2, ls_offset;
    logic [23:0] signed_offset;
    logic        s_bit;
    logic        is_data_proc, is_imm_op2, is_load_store, is_load, is_store, is_byte;
    logic        is_pre_index, is_writeback, is_branch, is_branch_link, is_block_trans, is_swi;
    logic        is_mul, is_msr, is_mrs;

    logic [31:0] rf_rdata_a, rf_rdata_b;
    logic [3:0]  rf_raddr_b;
    logic        rf_we;
    logic [3:0]  rf_waddr;
    logic [31:0] rf_wdata;

    logic [31:0] shifter_operand, shifter_result;
    logic [11:0] shifter_amount;
    logic [1:0]  shifter_type;
    logic        shifter_carry_out;

    logic [31:0] alu_result;
    logic        alu_flag_n, alu_flag_z, alu_flag_c, alu_flag_v;

    logic        cpsr_n, cpsr_z, cpsr_c, cpsr_v;
    logic [31:0] cpsr_out;
    logic        cond_pass;
    logic        flags_we;
    logic        msr_we_ctrl;

    logic [31:0] mem_addr_calc;
    logic [31:0] next_pc;

    logic        do_branch;
    logic        do_pc_write_from_alu;
    logic        do_lr_write;
    logic        do_reg_write;
    logic        do_load_start;
    logic        do_store;
    logic        do_mrs_write;

    logic        load_pending;
    logic [3:0]  load_rd_pending;

    assign pc_plus4 = pc_current + 32'd4;
    assign pc_plus8 = pc_current + 32'd8;
    assign imem_addr = pc_current;
    assign branch_target = pc_plus8 + {{6{signed_offset[23]}}, signed_offset, 2'b00};

    arm_decoder u_decoder (
        .instr          (instr),
        .cond           (cond),
        .opcode         (opcode),
        .s_bit          (s_bit),
        .rn             (rn_addr),
        .rd             (rd_addr),
        .operand2       (operand2),
        .signed_offset  (signed_offset),
        .rd_ls          (),
        .ls_offset      (ls_offset),
        .reg_list       (),
        .is_data_proc   (is_data_proc),
        .is_imm_op2     (is_imm_op2),
        .is_load_store  (is_load_store),
        .is_load        (is_load),
        .is_store       (is_store),
        .is_byte        (is_byte),
        .is_pre_index   (is_pre_index),
        .is_writeback   (is_writeback),
        .is_branch      (is_branch),
        .is_branch_link (is_branch_link),
        .is_block_trans (is_block_trans),
        .is_swi         (is_swi),
        .is_mul         (is_mul),
        .is_msr         (is_msr),
        .is_mrs         (is_mrs)
    );

    arm_condition_check u_cond_check (
        .cond      (cond),
        .flag_n    (cpsr_n),
        .flag_z    (cpsr_z),
        .flag_c    (cpsr_c),
        .flag_v    (cpsr_v),
        .cond_pass (cond_pass)
    );

    assign rf_raddr_b = (is_load_store && is_store) ? rd_addr : operand2[3:0];

    arm_reg_file u_reg_file (
        .clk    (clk),
        .rst_n  (rst_n),
        .raddr_a(rn_addr),
        .rdata_a(rf_rdata_a),
        .raddr_b(rf_raddr_b),
        .rdata_b(rf_rdata_b),
        .we     (rf_we),
        .waddr  (rf_waddr),
        .wdata  (rf_wdata),
        .pc_out ()
    );

    assign shifter_operand = is_imm_op2 ? {24'd0, operand2[7:0]} : rf_rdata_b;
    assign shifter_amount  = is_imm_op2 ? {7'd0, operand2[11:8]} : {7'd0, operand2[11:7]};
    assign shifter_type    = is_imm_op2 ? 2'b11 : operand2[6:5];

    arm_barrel_shifter u_shifter (
        .operand       (shifter_operand),
        .shift_amount  (shifter_amount),
        .shift_type    (shifter_type),
        .shift_carry_in(cpsr_c),
        .is_imm        (is_imm_op2),
        .result        (shifter_result),
        .carry_out     (shifter_carry_out)
    );

    arm_alu u_alu (
        .op_a         (rf_rdata_a),
        .op_b         (shifter_result),
        .alu_op       (opcode),
        .carry_in     (cpsr_c),
        .update_flags (s_bit & cond_pass & is_data_proc),
        .result       (alu_result),
        .flag_n       (alu_flag_n),
        .flag_z       (alu_flag_z),
        .flag_c       (alu_flag_c),
        .flag_v       (alu_flag_v)
    );

    arm_cpsr u_cpsr (
        .clk          (clk),
        .rst_n        (rst_n),
        .update_flags (flags_we),
        .flag_n_in    (alu_flag_n),
        .flag_z_in    (alu_flag_z),
        .flag_c_in    (alu_flag_c),
        .flag_v_in    (alu_flag_v),
        .msr_we       (msr_we_ctrl),
        .msr_data     (rf_rdata_a),
        .flag_n       (cpsr_n),
        .flag_z       (cpsr_z),
        .flag_c       (cpsr_c),
        .flag_v       (cpsr_v),
        .cpsr_out     (cpsr_out),
        .mode         (),
        .thumb        (),
        .fiq_disable  (),
        .irq_disable  ()
    );

    always_comb begin
        mem_addr_calc = rf_rdata_a;
        if (is_pre_index) begin
            mem_addr_calc = rf_rdata_a + {{20{ls_offset[11]}}, ls_offset};
        end
    end

    always_comb begin
        do_branch            = 1'b0;
        do_pc_write_from_alu = 1'b0;
        do_lr_write          = 1'b0;
        do_reg_write         = 1'b0;
        do_load_start        = 1'b0;
        do_store             = 1'b0;
        do_mrs_write         = 1'b0;
        flags_we             = 1'b0;
        msr_we_ctrl          = 1'b0;
        next_pc              = pc_plus4;

        if (!load_pending && cond_pass) begin
            if (is_branch) begin
                do_branch = 1'b1;
                next_pc   = branch_target;
                do_lr_write = is_branch_link;
            end else if (is_swi) begin
                do_branch = 1'b1;
                next_pc   = 32'h0000_0008;
            end else if (is_load_store) begin
                if (is_store) begin
                    do_store = 1'b1;
                end else if (is_load) begin
                    do_load_start = 1'b1;
                end
            end else if (is_msr) begin
                msr_we_ctrl = 1'b1;
            end else if (is_mrs) begin
                do_mrs_write = 1'b1;
            end else if (is_data_proc) begin
                if (rd_addr == 4'd15) begin
                    do_pc_write_from_alu = 1'b1;
                    next_pc = alu_result;
                end else begin
                    do_reg_write = 1'b1;
                end
                flags_we = s_bit;
            end
        end
    end

    always_comb begin
        dmem_req   = 1'b0;
        dmem_we    = 1'b0;
        dmem_byte  = 1'b0;
        dmem_addr  = 32'd0;
        dmem_wdata = 32'd0;

        if (do_store || do_load_start) begin
            dmem_req   = 1'b1;
            dmem_we    = do_store;
            dmem_byte  = is_byte;
            dmem_addr  = mem_addr_calc;
            dmem_wdata = rf_rdata_b;
        end
    end

    always_comb begin
        rf_we    = 1'b0;
        rf_waddr = 4'd0;
        rf_wdata = 32'd0;

        if (load_pending) begin
            rf_we    = 1'b1;
            rf_waddr = load_rd_pending;
            rf_wdata = dmem_rdata;
        end else if (do_lr_write) begin
            rf_we    = 1'b1;
            rf_waddr = 4'd14;
            rf_wdata = pc_plus4;
        end else if (do_mrs_write) begin
            rf_we    = 1'b1;
            rf_waddr = rd_addr;
            rf_wdata = cpsr_out;
        end else if (do_reg_write) begin
            rf_we    = 1'b1;
            rf_waddr = rd_addr;
            rf_wdata = alu_result;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_current       <= 32'd0;
            instr            <= 32'hE1A0_0000;
            load_pending     <= 1'b0;
            load_rd_pending  <= 4'd0;
        end else begin
            instr <= imem_rdata;

            if (load_pending) begin
                load_pending <= 1'b0;
                pc_current   <= pc_plus4;
            end else if (do_branch || do_pc_write_from_alu) begin
                pc_current <= next_pc;
            end else if (do_load_start) begin
                load_pending    <= 1'b1;
                load_rd_pending <= rd_addr;
            end else begin
                pc_current <= pc_plus4;
            end
        end
    end

    assign debug_pc    = pc_current;
    assign debug_instr = instr;
    assign debug_state = {2'b00, load_pending, dmem_ready};
    assign debug_reg_r0 = 32'd0;
    assign debug_reg_r1 = 32'd0;
    assign debug_reg_r2 = 32'd0;
    assign debug_reg_r3 = 32'd0;
endmodule
