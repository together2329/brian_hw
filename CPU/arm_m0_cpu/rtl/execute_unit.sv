//============================================================================
// Module : execute_unit
// Description : Execute Stage for ARM M0-style CPU
//               ALU operation, flag update, branch resolution,
//               memory interface, register writeback
//============================================================================

module execute_unit (
    input  logic         clk,
    input  logic         rst_n,

    // Pipeline input (from DECODE stage)
    input  logic [31:0]  de_operand_a,      // ALU operand A
    input  logic [31:0]  de_operand_b,      // ALU operand B
    input  logic [3:0]   de_alu_op,         // ALU operation
    input  logic [3:0]   de_reg_write_addr, // Destination register
    input  logic         de_reg_write_en,   // Register write enable
    input  logic         de_mem_we,         // Memory write enable
    input  logic         de_mem_req,        // Memory access request
    input  logic         de_is_branch,      // Branch instruction
    input  logic [3:0]   de_branch_cond,    // Condition code
    input  logic [31:0]  de_branch_target,  // Branch target
    input  logic         de_is_bx,          // BX instruction
    input  logic         de_is_bl,          // BL instruction
    input  logic [31:0]  de_lr_value,       // LR value for BL
    input  logic         de_is_push,        // PUSH instruction
    input  logic         de_is_pop,         // POP instruction
    input  logic [7:0]   de_reg_list,       // Register list for PUSH/POP
    input  logic         de_push_lr,        // PUSH includes LR
    input  logic         de_pop_pc,         // POP includes PC
    input  logic         de_valid,          // Valid decode output

    // ALU interface
    output logic [3:0]   alu_op,
    output logic [31:0]  alu_operand_a,
    output logic [31:0]  alu_operand_b,
    input  logic [31:0]  alu_result,
    input  logic         alu_flag_n,
    input  logic         alu_flag_z,
    input  logic         alu_flag_c,
    input  logic         alu_flag_v,

    // APSR (condition flags) register
    output logic         apsr_n,
    output logic         apsr_z,
    output logic         apsr_c,
    output logic         apsr_v,

    // Branch resolution output
    output logic         branch_taken,
    output logic [31:0]  branch_target_out,

    // Memory interface (external)
    output logic [31:0]  mem_addr,
    output logic [31:0]  mem_wdata,
    output logic         mem_we,
    output logic         mem_req,
    output logic [1:0]   mem_size,
    input  logic [31:0]  mem_rdata,
    input  logic         mem_ack,

    // Register writeback output
    output logic [3:0]   wb_reg_addr,
    output logic [31:0]  wb_reg_data,
    output logic         wb_reg_en,

    // SP control for PUSH/POP
    output logic         sp_write_en,
    output logic [31:0]  sp_write_data,

    // IRQ return detection
    output logic         exc_return_detected
);

    // ---------------------------------------------------------------
    // APSR register
    // ---------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            apsr_n <= 1'b0;
            apsr_z <= 1'b0;
            apsr_c <= 1'b0;
            apsr_v <= 1'b0;
        end else if (de_valid) begin
            // Update flags for ALU operations (not for NOP, BX, branches)
            if (de_alu_op != 4'b0110 && de_alu_op != 4'b0111 && !de_is_branch) begin
                apsr_n <= alu_flag_n;
                apsr_z <= alu_flag_z;
                apsr_c <= alu_flag_c;
                apsr_v <= alu_flag_v;
            end
        end
    end

    // ---------------------------------------------------------------
    // Condition evaluation (combinational)
    // ---------------------------------------------------------------
    logic cond_met;

    always_comb begin
        case (de_branch_cond)
            4'b0000: cond_met = apsr_z;                              // EQ
            4'b0001: cond_met = !apsr_z;                             // NE
            4'b0010: cond_met = apsr_c;                              // CS
            4'b0011: cond_met = !apsr_c;                             // CC
            4'b0100: cond_met = apsr_n;                              // MI
            4'b0101: cond_met = !apsr_n;                             // PL
            4'b0110: cond_met = apsr_v;                              // VS
            4'b0111: cond_met = !apsr_v;                             // VC
            4'b1000: cond_met = apsr_c && !apsr_z;                   // HI
            4'b1001: cond_met = !apsr_c || apsr_z;                   // LS
            4'b1010: cond_met = (apsr_n == apsr_v);                  // GE
            4'b1011: cond_met = (apsr_n != apsr_v);                  // LT
            4'b1100: cond_met = !apsr_z && (apsr_n == apsr_v);       // GT
            4'b1101: cond_met = apsr_z || (apsr_n != apsr_v);        // LE
            4'b1110: cond_met = 1'b1;                                // AL (always)
            default: cond_met = 1'b0;
        endcase
    end

    // ---------------------------------------------------------------
    // Branch resolution
    // ---------------------------------------------------------------
    assign branch_taken = de_valid && (de_is_branch || de_is_bx) && cond_met;
    assign branch_target_out = de_is_bx ? de_operand_b : de_branch_target;

    // ---------------------------------------------------------------
    // EXC_RETURN detection (BX LR with LR=0xFFFFFFFx)
    // ---------------------------------------------------------------
    assign exc_return_detected = de_valid && de_is_bx &&
                                  (de_operand_b[31:28] == 4'hF);

    // ---------------------------------------------------------------
    // ALU connections
    // ---------------------------------------------------------------
    assign alu_op       = de_alu_op;
    assign alu_operand_a = de_operand_a;
    assign alu_operand_b = de_operand_b;

    // ---------------------------------------------------------------
    // Memory interface
    // ---------------------------------------------------------------
    always_comb begin
        mem_addr = 32'd0;
        mem_wdata = 32'd0;
        mem_we   = 1'b0;
        mem_req  = 1'b0;
        mem_size = 2'b10; // Default: word

        if (de_valid) begin
            if (de_mem_req && !de_mem_we) begin
                // LDR: read from memory
                mem_addr = de_operand_a; // Rn + offset (computed in decode)
                mem_req  = 1'b1;
                mem_we   = 1'b0;
            end else if (de_mem_req && de_mem_we) begin
                // STR: write to memory
                mem_addr  = de_operand_a; // Rn + Rm
                mem_wdata = de_operand_b; // Rt value
                mem_req   = 1'b1;
                mem_we    = 1'b1;
            end
        end
    end

    // ---------------------------------------------------------------
    // Register writeback
    // ---------------------------------------------------------------
    always_comb begin
        wb_reg_addr = de_reg_write_addr;
        wb_reg_data = 32'd0;
        wb_reg_en   = 1'b0;
        sp_write_en = 1'b0;
        sp_write_data = 32'd0;

        if (de_valid && !de_is_push && !de_is_pop) begin
            if (de_mem_req && !de_mem_we && mem_ack) begin
                // LDR: write memory read data to register
                wb_reg_data = mem_rdata;
                wb_reg_en   = de_reg_write_en;
            end else if (!de_mem_req) begin
                // ALU result: write to register (unless CMP/NOP/BX)
                if (de_alu_op == 4'b0011 || de_alu_op == 4'b0110 || de_is_branch || de_is_bx) begin
                    wb_reg_en = 1'b0;
                end else begin
                    wb_reg_data = alu_result;
                    wb_reg_en   = de_reg_write_en;
                end
            end
        end

        // BL: write LR
        if (de_valid && de_is_bl && de_reg_write_en) begin
            wb_reg_addr = 4'd14; // LR
            wb_reg_data = de_lr_value;
            wb_reg_en   = 1'b1;
        end
    end

endmodule
