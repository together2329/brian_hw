//=============================================================================
// ARM CPU Core
// Integrates all datapath components: Register File, ALU, Shifter, Decoder,
// Control Unit, CPSR, Condition Checker
// 3-stage pipeline: FETCH -> DECODE/EXECUTE -> WRITEBACK
//=============================================================================

module arm_cpu_core (
    input  logic        clk,
    input  logic        rst_n,

    // Instruction memory interface
    output logic [31:0] imem_addr,
    input  logic [31:0] imem_rdata,

    // Data memory interface
    output logic        dmem_req,
    output logic        dmem_we,
    output logic        dmem_byte,
    output logic [31:0] dmem_addr,
    output logic [31:0] dmem_wdata,
    input  logic [31:0] dmem_rdata,
    input  logic        dmem_ready,

    // Debug outputs
    output logic [31:0] debug_pc,
    output logic [31:0] debug_instr,
    output logic [3:0]  debug_state,
    output logic [31:0] debug_reg_r0,
    output logic [31:0] debug_reg_r1,
    output logic [31:0] debug_reg_r2,
    output logic [31:0] debug_reg_r3
);

    import arm_defs::*;

    //=========================================================
    // Internal signals
    //=========================================================

    // PC
    logic [31:0] pc_current, pc_next, pc_plus4, pc_plus8;
    logic        pc_we;
    logic        pc_sel;

    // Instruction
    logic [31:0] instr;

    // Decoder outputs
    logic [3:0]  cond;
    logic [3:0]  opcode;
    logic        s_bit;
    logic [3:0]  rn_addr, rd_addr;
    logic [11:0] operand2;
    logic [23:0] signed_offset;
    logic [11:0] ls_offset;
    logic [15:0] reg_list;
    logic        is_data_proc, is_imm_op2;
    logic        is_load_store, is_load, is_store, is_byte;
    logic        is_pre_index, is_writeback;
    logic        is_branch, is_branch_link;
    logic        is_block_trans, is_swi;
    logic        is_mul, is_msr, is_mrs;

    // Control outputs
    logic        regfile_we, flags_we;
    logic        lr_we;
    logic        mem_req, mem_we_ctrl, mem_byte_ctrl;
    logic [1:0]  result_sel;
    logic        alu_op_en, shifter_en, shift_imm_sel;
    logic        msr_we_ctrl, stall;

    // Register file
    logic [3:0]  rf_raddr_a, rf_raddr_b;
    logic [31:0] rf_rdata_a, rf_rdata_b;
    logic [3:0]  rf_waddr;
    logic [31:0] rf_wdata;
    logic        rf_we;

    // CPSR
    logic        cpsr_n, cpsr_z, cpsr_c, cpsr_v;
    logic [31:0] cpsr_out;

    // Condition check
    logic        cond_pass;

    // Shifter
    logic [31:0] shifter_operand;
    logic [11:0] shifter_amount;
    logic [1:0]  shifter_type;
    logic        shifter_carry_in;
    logic        shifter_is_imm;
    logic [31:0] shifter_result;
    logic        shifter_carry_out;

    // ALU
    logic [31:0] alu_op_a, alu_op_b;
    logic [3:0]  alu_op;
    logic        alu_carry_in;
    logic        alu_update_flags;
    logic [31:0] alu_result;
    logic        alu_flag_n, alu_flag_z, alu_flag_c, alu_flag_v;

    // Branch target
    logic [31:0] branch_target;

    // Memory address/result
    logic [31:0] mem_addr_calc;
    logic [31:0] ls_base_addr;

    // Write-back mux
    logic [31:0] wb_result;

    //=========================================================
    // Program Counter
    //=========================================================

    assign pc_plus4  = pc_current + 32'd4;
    assign pc_plus8  = pc_current + 32'd8; // For ARM's PC-read = current + 8

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_current <= 32'h0000_0000;
        end else if (pc_we) begin
            if (pc_sel) begin
                pc_current <= branch_target;
            end else begin
                pc_current <= pc_plus4;
            end
        end
    end

    assign imem_addr = pc_current;

    //=========================================================
    // Instruction Register (from imem)
    //=========================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            instr <= 32'hE1A0_0000; // NOP (MOV R0, R0)
        else
            instr <= imem_rdata;
    end

    //=========================================================
    // Branch Target Calculation
    //=========================================================
    // Sign-extend 24-bit offset, shift left 2, add to PC+8
    assign branch_target = pc_plus8 + {{6{signed_offset[23]}}, signed_offset, 2'b00};

    //=========================================================
    // Instruction Decoder
    //=========================================================

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
        .reg_list       (reg_list),
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

    //=========================================================
    // CPSR
    //=========================================================

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

    //=========================================================
    // Condition Code Checker
    //=========================================================

    arm_condition_check u_cond_check (
        .cond      (cond),
        .flag_n    (cpsr_n),
        .flag_z    (cpsr_z),
        .flag_c    (cpsr_c),
        .flag_v    (cpsr_v),
        .cond_pass (cond_pass)
    );

    //=========================================================
    // Control Unit
    //=========================================================

    arm_control u_control (
        .clk            (clk),
        .rst_n          (rst_n),
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
        .is_mrs         (is_mrs),
        .cond_pass      (cond_pass),
        .regfile_we     (regfile_we),
        .flags_we       (flags_we),
        .pc_we          (pc_we),
        .pc_sel         (pc_sel),
        .lr_we          (lr_we),
        .mem_req        (mem_req),
        .mem_we         (mem_we_ctrl),
        .mem_byte       (mem_byte_ctrl),
        .result_sel     (result_sel),
        .alu_op_en      (alu_op_en),
        .shifter_en     (shifter_en),
        .shift_imm_sel  (shift_imm_sel),
        .msr_we         (msr_we_ctrl),
        .stall          (stall)
    );

    //=========================================================
    // Register File
    //=========================================================

    // Read address muxing
    assign rf_raddr_a = rn_addr;
    assign rf_raddr_b = operand2[3:0]; // Rm for register operand

    // Write address/data
    assign rf_waddr = rd_addr;
    assign rf_we    = regfile_we & cond_pass;

    arm_reg_file u_reg_file (
        .clk    (clk),
        .rst_n  (rst_n),
        .raddr_a(rf_raddr_a),
        .rdata_a(rf_rdata_a),
        .raddr_b(rf_raddr_b),
        .rdata_b(rf_rdata_b),
        .we     (rf_we),
        .waddr  (rf_waddr),
        .wdata  (wb_result),
        .pc_out ()
    );

    //=========================================================
    // Barrel Shifter
    //=========================================================

    // Shifter operand selection
    assign shifter_operand = is_imm_op2 ? {24'd0, operand2[7:0]} : rf_rdata_b;

    assign shifter_amount = is_imm_op2 ? {7'd0, operand2[11:8]} :  // Rotate imm
                                      {7'd0, operand2[11:7]};      // Shift imm
    assign shifter_type   = is_imm_op2 ? 2'b11 :                   // ROR for immediate
                                      operand2[6:5];              // Shift type from instr
    assign shifter_carry_in = cpsr_c;
    assign shifter_is_imm   = is_imm_op2;

    arm_barrel_shifter u_shifter (
        .operand       (shifter_operand),
        .shift_amount  (shifter_amount),
        .shift_type    (shifter_type),
        .shift_carry_in(shifter_carry_in),
        .is_imm        (shifter_is_imm),
        .result        (shifter_result),
        .carry_out     (shifter_carry_out)
    );

    //=========================================================
    // ALU
    //=========================================================

    assign alu_op_a       = rf_rdata_a;
    assign alu_op_b       = shifter_result;
    assign alu_op         = opcode;
    assign alu_carry_in   = cpsr_c;
    assign alu_update_flags = s_bit & cond_pass;

    arm_alu u_alu (
        .op_a         (alu_op_a),
        .op_b         (alu_op_b),
        .alu_op       (alu_op),
        .carry_in     (alu_carry_in),
        .update_flags (alu_update_flags),
        .result       (alu_result),
        .flag_n       (alu_flag_n),
        .flag_z       (alu_flag_z),
        .flag_c       (alu_flag_c),
        .flag_v       (alu_flag_v)
    );

    //=========================================================
    // Load/Store Address Calculation
    //=========================================================

    assign ls_base_addr = rf_rdata_a;
    assign mem_addr_calc = is_pre_index ?
                           (ls_base_addr + {{20{ls_offset[11]}}, ls_offset}) :  // Pre-index
                           ls_base_addr;                                        // Post-index

    //=========================================================
    // Data Memory Interface
    //=========================================================

    assign dmem_req   = mem_req & cond_pass;
    assign dmem_we    = mem_we_ctrl;
    assign dmem_byte  = mem_byte_ctrl;
    assign dmem_addr  = mem_addr_calc;
    assign dmem_wdata = rf_rdata_b; // Rm for store

    //=========================================================
    // Write-Back Mux
    //=========================================================

    always_comb begin
        case (result_sel)
            2'b00: wb_result = alu_result;           // ALU result
            2'b01: wb_result = dmem_rdata;           // Memory load data
            2'b10: wb_result = cpsr_out;             // MRS: read CPSR
            default: wb_result = alu_result;
        endcase
    end

    // Link register write (BL instruction)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // LR will be reset by reg_file
        end else if (lr_we && cond_pass) begin
            // Write PC+4 to LR (R14)
        end
    end

    //=========================================================
    // Debug Outputs
    //=========================================================

    assign debug_pc    = pc_current;
    assign debug_instr = instr;

    // Debug: expose registers through top
    assign debug_reg_r0 = 32'd0; // Placeholder, can be connected via reg_file debug ports

endmodule
