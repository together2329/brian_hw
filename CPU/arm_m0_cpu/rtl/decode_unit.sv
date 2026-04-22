//============================================================================
// Module : decode_unit
// Description : Thumb-16 Instruction Decoder for ARM M0-style CPU
//               Parses 16-bit Thumb opcodes and generates control signals
//               Supported: MOV, ADD, SUB, CMP, LDR, STR, B, BL, BX,
//                          PUSH, POP, NOP
//============================================================================

module decode_unit (
    input  logic         clk,
    input  logic         rst_n,

    // Pipeline input (from FETCH stage)
    input  logic [15:0]  fd_instr,      // 16-bit Thumb instruction
    input  logic [31:0]  fd_pc,         // PC of this instruction
    input  logic         fd_valid,      // Valid instruction from fetch

    // Register read interface
    output logic [3:0]   ra1_addr,      // Read port 1 address (Rn)
    output logic [3:0]   ra2_addr,      // Read port 2 address (Rm)
    input  logic [31:0]  ra1_data,      // Read port 1 data
    input  logic [31:0]  ra2_data,      // Read port 2 data

    // Pipeline output (to EXECUTE stage)
    output logic [31:0]  de_operand_a,  // ALU operand A (Rn value)
    output logic [31:0]  de_operand_b,  // ALU operand B (Rm or immediate)
    output logic [3:0]   de_alu_op,     // ALU operation
    output logic [3:0]   de_reg_write_addr, // Destination register
    output logic         de_reg_write_en,   // Register write enable
    output logic         de_mem_we,         // Memory write enable (STR)
    output logic         de_mem_req,        // Memory access request
    output logic         de_is_branch,      // Is a branch instruction
    output logic [3:0]   de_branch_cond,    // Branch condition code
    output logic [31:0]  de_branch_target,  // Branch target address
    output logic         de_is_bx,          // Is BX instruction
    output logic         de_is_bl,          // Is BL instruction
    output logic [31:0]  de_lr_value,       // LR value for BL (PC+3 with Thumb bit)
    output logic         de_is_push,        // Is PUSH instruction
    output logic         de_is_pop,         // Is POP instruction
    output logic [7:0]   de_reg_list,       // Register list for PUSH/POP
    output logic         de_push_lr,        // PUSH includes LR
    output logic         de_pop_pc,         // POP includes PC
    output logic         de_valid,          // Valid decode output

    // Current PC for PC-relative addressing
    input  logic [31:0]  current_pc,

    // BL first-half tracking (from ctrl_fsm)
    input  logic         bl_first_half,
    input  logic [31:0]  bl_offset_hi,

    // Clear signal (from ctrl_fsm)
    input  logic         de_clear
);

    // ALU operations
    localparam [3:0] ALU_ADD = 4'b0000;
    localparam [3:0] ALU_SUB = 4'b0001;
    localparam [3:0] ALU_MOV = 4'b0010;
    localparam [3:0] ALU_CMP = 4'b0011;
    localparam [3:0] ALU_NOP = 4'b0110;
    localparam [3:0] ALU_BX  = 4'b0111;

    // ---------------------------------------------------------------
    // Instruction field extraction
    // ---------------------------------------------------------------
    logic [15:11] opcode_hi5;
    logic [15:13] opcode_hi3;
    logic [15:10] opcode_hi6;
    logic [9:6]   opcode_mid4;
    logic [12:11] opcode_2bit;
    logic [2:0]   rd_low;
    logic [2:0]   rn_low;
    logic [2:0]   rm_low;
    logic [7:0]   imm8;
    logic [10:0]  imm11;
    logic [3:0]   cond;
    logic [7:0]   rlist;

    assign opcode_hi5  = fd_instr[15:11];
    assign opcode_hi3  = fd_instr[15:13];
    assign opcode_hi6  = fd_instr[15:10];
    assign opcode_mid4 = fd_instr[9:6];
    assign opcode_2bit = fd_instr[12:11];
    assign rd_low      = fd_instr[2:0];
    assign rn_low      = fd_instr[5:3];
    assign rm_low      = fd_instr[8:6];
    assign imm8        = fd_instr[7:0];
    assign imm11       = fd_instr[10:0];
    assign cond        = fd_instr[11:8];
    assign rlist       = fd_instr[7:0];

    // ---------------------------------------------------------------
    // Decode logic (combinational)
    // ---------------------------------------------------------------
    logic [3:0]   dec_ra1_addr;
    logic [3:0]   dec_ra2_addr;
    logic [31:0]  dec_imm_ext;
    logic         dec_use_imm;
    logic         dec_imm_to_b;  // Route immediate to operand_b (for SUB imm)
    logic [3:0]   dec_alu_op;
    logic [3:0]   dec_reg_write_addr;
    logic         dec_reg_write_en;
    logic         dec_mem_we;
    logic         dec_mem_req;
    logic         dec_is_branch;
    logic [3:0]   dec_branch_cond;
    logic [31:0]  dec_branch_target;
    logic         dec_is_bx;
    logic         dec_is_bl;
    logic [31:0]  dec_lr_value;
    logic         dec_is_push;
    logic         dec_is_pop;
    logic         dec_push_lr;
    logic         dec_pop_pc;

    always_comb begin
        // Defaults - prevent latches
        dec_ra1_addr     = 4'd0;
        dec_ra2_addr     = 4'd0;
        dec_imm_ext      = 32'd0;
        dec_use_imm      = 1'b0;
        dec_imm_to_b     = 1'b0;
        dec_alu_op       = ALU_NOP;
        dec_reg_write_addr = 4'd0;
        dec_reg_write_en = 1'b0;
        dec_mem_we       = 1'b0;
        dec_mem_req      = 1'b0;
        dec_is_branch    = 1'b0;
        dec_branch_cond  = 4'b0000;
        dec_branch_target = 32'd0;
        dec_is_bx        = 1'b0;
        dec_is_bl        = 1'b0;
        dec_lr_value     = 32'd0;
        dec_is_push      = 1'b0;
        dec_is_pop       = 1'b0;
        dec_push_lr      = 1'b0;
        dec_pop_pc       = 1'b0;

        if (fd_valid) begin
            casez (fd_instr)

                // -------------------------------------------------------
                // NOP: 1011 1111 0000 0000
                // -------------------------------------------------------
                16'hBF00: begin
                    dec_alu_op       = ALU_NOP;
                    dec_reg_write_en = 1'b0;
                end

                // -------------------------------------------------------
                // MOV Rdn, #imm8: 00100 Rdn(3) imm8(8)
                // -------------------------------------------------------
                16'b00100_???_????????: begin
                    dec_ra1_addr     = {1'b0, fd_instr[10:8]};
                    dec_imm_ext      = {24'd0, imm8};
                    dec_use_imm      = 1'b1;
                    dec_alu_op       = ALU_MOV;
                    dec_reg_write_addr = {1'b0, fd_instr[10:8]};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // CMP Rdn, #imm8: 00101 Rdn(3) imm8(8)
                // CMP computes Rdn - imm8 (doesn't write back)
                // -------------------------------------------------------
                16'b00101_???_????????: begin
                    dec_ra1_addr     = {1'b0, fd_instr[10:8]};
                    dec_ra2_addr     = {1'b0, fd_instr[10:8]};
                    dec_imm_ext      = {24'd0, imm8};
                    dec_use_imm      = 1'b0;
                    dec_imm_to_b     = 1'b1;
                    dec_alu_op       = ALU_CMP;
                    dec_reg_write_en = 1'b0;
                end

                // -------------------------------------------------------
                // ADD Rdn, #imm8: 00110 Rdn(3) imm8(8)
                // -------------------------------------------------------
                16'b00110_???_????????: begin
                    dec_ra1_addr     = {1'b0, fd_instr[10:8]};
                    dec_ra2_addr     = {1'b0, fd_instr[10:8]};
                    dec_imm_ext      = {24'd0, imm8};
                    dec_use_imm      = 1'b1;
                    dec_alu_op       = ALU_ADD;
                    dec_reg_write_addr = {1'b0, fd_instr[10:8]};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // SUB Rdn, #imm8: 00111 Rdn(3) imm8(8)
                // Rdn = Rdn - imm8
                // operand_a = Rdn, operand_b = imm8
                // -------------------------------------------------------
                16'b00111_???_????????: begin
                    dec_ra1_addr     = {1'b0, fd_instr[10:8]};
                    dec_ra2_addr     = {1'b0, fd_instr[10:8]};
                    dec_imm_ext      = {24'd0, imm8};
                    dec_use_imm      = 1'b0;
                    dec_imm_to_b     = 1'b1;
                    dec_alu_op       = ALU_SUB;
                    dec_reg_write_addr = {1'b0, fd_instr[10:8]};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // ADD Rd, Rn, #imm3: 0001110 imm3(3) Rn(3) Rd(3)
                // -------------------------------------------------------
                16'b0001110_???_???_???: begin
                    dec_ra1_addr     = {1'b0, rn_low};
                    dec_imm_ext      = {29'd0, fd_instr[8:6]};
                    dec_use_imm      = 1'b1;
                    dec_alu_op       = ALU_ADD;
                    dec_reg_write_addr = {1'b0, rd_low};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // SUB Rd, Rn, #imm3: 0001111 imm3(3) Rn(3) Rd(3)
                // -------------------------------------------------------
                16'b0001111_???_???_???: begin
                    dec_ra1_addr     = {1'b0, rn_low};
                    dec_imm_ext      = {29'd0, fd_instr[8:6]};
                    dec_use_imm      = 1'b1;
                    dec_alu_op       = ALU_SUB;
                    dec_reg_write_addr = {1'b0, rd_low};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // ADD Rd, Rn, Rm (low registers): 0001100 Rm(3) Rn(3) Rd(3)
                // -------------------------------------------------------
                16'b0001100_???_???_???: begin
                    dec_ra1_addr     = {1'b0, rn_low};
                    dec_ra2_addr     = {1'b0, rm_low};
                    dec_use_imm      = 1'b0;
                    dec_alu_op       = ALU_ADD;
                    dec_reg_write_addr = {1'b0, rd_low};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // SUB Rd, Rn, Rm (low registers): 0001101 Rm(3) Rn(3) Rd(3)
                // -------------------------------------------------------
                16'b0001101_???_???_???: begin
                    dec_ra1_addr     = {1'b0, rn_low};
                    dec_ra2_addr     = {1'b0, rm_low};
                    dec_use_imm      = 1'b0;
                    dec_alu_op       = ALU_SUB;
                    dec_reg_write_addr = {1'b0, rd_low};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // ADD Rd, Rm (high reg): 01000100 D Rm(4) Rdn(3)
                // Rd/Rdn combined: {D, Rdn}
                // -------------------------------------------------------
                16'b01000100_?_????_???: begin
                    dec_ra1_addr     = {fd_instr[7], fd_instr[2:0]}; // {D, Rdn}
                    dec_ra2_addr     = fd_instr[6:3];                 // Rm
                    dec_use_imm      = 1'b0;
                    dec_alu_op       = ALU_ADD;
                    dec_reg_write_addr = {fd_instr[7], fd_instr[2:0]};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // MOV Rd, Rm (high reg): 01000110 D Rm(4) Rdn(3)
                // -------------------------------------------------------
                16'b01000110_?_????_???: begin
                    dec_ra1_addr     = fd_instr[6:3];                 // Rm
                    dec_ra2_addr     = fd_instr[6:3];                 // Rm
                    dec_use_imm      = 1'b0;
                    dec_alu_op       = ALU_MOV;
                    dec_reg_write_addr = {fd_instr[7], fd_instr[2:0]}; // {D, Rdn}
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // BX Rm: 01000111 0 Rm(4) 000
                // -------------------------------------------------------
                16'b01000111_0_????_000: begin
                    dec_ra2_addr     = fd_instr[6:3];
                    dec_alu_op       = ALU_BX;
                    dec_is_bx        = 1'b1;
                    dec_reg_write_en = 1'b0;
                end

                // -------------------------------------------------------
                // LDR Rt, [PC, #imm]: 01001 Rt(3) imm8(8)
                // Address = (PC & ~3) + (imm8 << 2)
                // -------------------------------------------------------
                16'b01001_???_????????: begin
                    dec_ra1_addr     = 4'd15; // PC
                    dec_imm_ext      = {22'd0, imm8, 2'b00}; // imm8 << 2
                    dec_use_imm      = 1'b1;
                    dec_alu_op       = ALU_ADD;
                    dec_mem_req      = 1'b1;
                    dec_reg_write_addr = {1'b0, fd_instr[10:8]};
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // STR Rt, [Rn, Rm]: 0101000 Rm(3) Rn(3) Rt(3)
                // -------------------------------------------------------
                16'b0101000_???_???_???: begin
                    dec_ra1_addr     = {1'b0, rn_low}; // Rn (base)
                    dec_ra2_addr     = {1'b0, rm_low}; // Rm (offset)
                    dec_use_imm      = 1'b0;
                    dec_alu_op       = ALU_ADD; // addr = Rn + Rm
                    dec_mem_we       = 1'b1;
                    dec_mem_req      = 1'b1;
                    // Rt data is needed as write data - will use ra2_data re-read
                    // We store Rt value in operand_a through a special path
                    // Actually: operand_a = Rn (base), operand_b = Rm (offset)
                    // We need Rt for mem_wdata - use separate path in execute
                    dec_reg_write_en = 1'b0;
                end

                // -------------------------------------------------------
                // LDR Rt, [Rn, Rm]: 0101100 Rm(3) Rn(3) Rt(3)
                // -------------------------------------------------------
                16'b0101100_???_???_???: begin
                    dec_ra1_addr     = {1'b0, rn_low}; // Rn (base)
                    dec_ra2_addr     = {1'b0, rm_low}; // Rm (offset)
                    dec_use_imm      = 1'b0;
                    dec_alu_op       = ALU_ADD; // addr = Rn + Rm
                    dec_mem_req      = 1'b1;
                    dec_reg_write_addr = {1'b0, rd_low}; // Rt
                    dec_reg_write_en = 1'b1;
                end

                // -------------------------------------------------------
                // B (conditional): 1101 cond(4) imm8(8)
                // Offset = sign_extend(imm8 << 1) relative to PC+4
                // -------------------------------------------------------
                16'b1101_????_????????: begin
                    if (fd_instr[11:8] != 4'b1110) begin // 1110 is unconditional B (different encoding)
                        dec_is_branch    = 1'b1;
                        dec_branch_cond  = cond;
                        // sign-extend imm8, shift left by 1
                        dec_imm_ext      = {{23{imm8[7]}}, imm8, 1'b0};
                        dec_branch_target = fd_pc + 32'd4 + {{23{imm8[7]}}, imm8, 1'b0};
                        dec_reg_write_en = 1'b0;
                    end
                end

                // -------------------------------------------------------
                // B (unconditional): 11100 imm11(11)
                // Offset = sign_extend(imm11 << 1) relative to PC+4
                // -------------------------------------------------------
                16'b11100_???????????: begin
                    dec_is_branch    = 1'b1;
                    dec_branch_cond  = 4'b1110; // AL (always)
                    dec_imm_ext      = {{20{imm11[10]}}, imm11, 1'b0};
                    dec_branch_target = fd_pc + 32'd4 + {{20{imm11[10]}}, imm11, 1'b0};
                    dec_reg_write_en = 1'b0;
                end

                // -------------------------------------------------------
                // BL first half: 11110 imm11(11) — save offset high
                // -------------------------------------------------------
                16'b11110_???????????: begin
                    dec_is_bl        = 1'b1;
                    dec_reg_write_en = 1'b0;
                end

                // -------------------------------------------------------
                // BL second half: 11101 imm11(11) — compute target, set LR
                // -------------------------------------------------------
                16'b11111_???????????: begin
                    dec_is_branch    = 1'b1;
                    dec_branch_cond  = 4'b1110; // Always
                    dec_is_bl        = 1'b1;
                    // LR = PC of BL first half + 3 (with Thumb bit)
                    dec_lr_value     = fd_pc + 32'd3; // Approximate: PC+3 with Thumb bit
                    dec_reg_write_addr = 4'd14; // LR
                    dec_reg_write_en = 1'b1;
                    // Target computed in execute using both halves
                    if (bl_first_half) begin
                        // offset = (offset_hi << 12) | (imm11 << 1)
                        dec_branch_target = fd_pc + 32'd4 + {bl_offset_hi[19:0], imm11, 1'b0};
                    end
                end

                // -------------------------------------------------------
                // PUSH {Rlist, LR}: 1011 0 M Rlist(8)
                // -------------------------------------------------------
                16'b1011_0_1_????????: begin
                    dec_is_push      = 1'b1;
                    dec_push_lr      = 1'b1;
                    dec_ra1_addr     = 4'd13; // SP
                    dec_reg_write_en = 1'b0;
                end

                16'b1011_0_0_????????: begin
                    if (fd_instr[7:0] != 8'd0) begin
                        dec_is_push      = 1'b1;
                        dec_push_lr      = 1'b0;
                        dec_ra1_addr     = 4'd13; // SP
                        dec_reg_write_en = 1'b0;
                    end else begin
                        dec_alu_op       = ALU_NOP;
                        dec_reg_write_en = 1'b0;
                    end
                end

                // -------------------------------------------------------
                // POP {Rlist, PC}: 1011 1 M Rlist(8)
                // -------------------------------------------------------
                16'b1011_1_1_????????: begin
                    dec_is_pop       = 1'b1;
                    dec_pop_pc       = 1'b1;
                    dec_ra1_addr     = 4'd13; // SP
                    dec_reg_write_en = 1'b0;
                end

                16'b1011_1_0_????????: begin
                    if (fd_instr[7:0] != 8'd0) begin
                        dec_is_pop       = 1'b1;
                        dec_pop_pc       = 1'b0;
                        dec_ra1_addr     = 4'd13; // SP
                        dec_reg_write_en = 1'b0;
                    end else begin
                        dec_alu_op       = ALU_NOP;
                        dec_reg_write_en = 1'b0;
                    end
                end

                // -------------------------------------------------------
                // Default: treat as NOP
                // -------------------------------------------------------
                default: begin
                    dec_alu_op       = ALU_NOP;
                    dec_reg_write_en = 1'b0;
                end
            endcase
        end
    end

    // ---------------------------------------------------------------
    // Pipeline register (FETCH → DECODE → EXECUTE)
    // Holds values stable until new instruction arrives or reset
    // ---------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            de_operand_a      <= 32'd0;
            de_operand_b      <= 32'd0;
            de_alu_op         <= ALU_NOP;
            de_reg_write_addr <= 4'd0;
            de_reg_write_en   <= 1'b0;
            de_mem_we         <= 1'b0;
            de_mem_req        <= 1'b0;
            de_is_branch      <= 1'b0;
            de_branch_cond    <= 4'b0000;
            de_branch_target  <= 32'd0;
            de_is_bx          <= 1'b0;
            de_is_bl          <= 1'b0;
            de_lr_value       <= 32'd0;
            de_is_push        <= 1'b0;
            de_is_pop         <= 1'b0;
            de_reg_list       <= 8'd0;
            de_push_lr        <= 1'b0;
            de_pop_pc         <= 1'b0;
            de_valid          <= 1'b0;
        end else if (de_clear) begin
            de_valid          <= 1'b0;
        end else if (fd_valid) begin
            // Route operands based on decode control
            if (dec_imm_to_b) begin
                // SUB/CMP immediate: operand_a = Rn, operand_b = imm
                de_operand_a <= ra1_data;
                de_operand_b <= dec_imm_ext;
            end else if (dec_use_imm) begin
                // MOV/ADD immediate: operand_a = imm, operand_b = Rm
                de_operand_a <= dec_imm_ext;
                de_operand_b <= ra2_data;
            end else begin
                // Register operations: operand_a = Rn, operand_b = Rm
                de_operand_a <= ra1_data;
                de_operand_b <= ra2_data;
            end

            // For LDR literal: align PC and add offset
            if (opcode_hi5 == 5'b01001) begin
                de_operand_a <= (current_pc & ~32'd3) + dec_imm_ext;
            end

            de_alu_op         <= dec_alu_op;
            de_reg_write_addr <= dec_reg_write_addr;
            de_reg_write_en   <= dec_reg_write_en;
            de_mem_we         <= dec_mem_we;
            de_mem_req        <= dec_mem_req;
            de_is_branch      <= dec_is_branch;
            de_branch_cond    <= dec_branch_cond;
            de_branch_target  <= dec_branch_target;
            de_is_bx          <= dec_is_bx;
            de_is_bl          <= dec_is_bl;
            de_lr_value       <= dec_lr_value;
            de_is_push        <= dec_is_push;
            de_is_pop         <= dec_is_pop;
            de_reg_list       <= rlist;
            de_push_lr        <= dec_push_lr;
            de_pop_pc         <= dec_pop_pc;
            de_valid          <= 1'b1;
        end
        // Hold values stable when fd_valid=0 (no new instruction)
    end

endmodule
