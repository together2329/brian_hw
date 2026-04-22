//============================================================================
// Module : arm_m0_cpu
// Description : Simplified ARM Cortex-M0-Style CPU
//               Single-file, multi-cycle implementation for iverilog
//               Supports: MOV, ADD, SUB, CMP, B, BEQ, LDR, STR, NOP
//============================================================================

module arm_m0_cpu (
    input  logic         clk,
    input  logic         rst_n,

    // Instruction fetch interface
    output logic [31:0]  instr_addr,
    output logic         instr_req,
    input  logic [15:0]  instr_rdata,
    input  logic         instr_ack,

    // Data memory interface
    output logic [31:0]  mem_addr,
    output logic [31:0]  mem_wdata,
    input  logic [31:0]  mem_rdata,
    output logic         mem_we,
    output logic         mem_req,
    output logic [1:0]   mem_size,
    input  logic         mem_ack,

    // Interrupt
    input  logic         irq
);

    // ===============================================================
    // FSM States
    // ===============================================================
    typedef enum logic [2:0] {
        RESET  = 3'd0,
        FETCH  = 3'd1,
        DECODE = 3'd2,
        EXEC   = 3'd3,
        WB     = 3'd4,
        MEM_RD = 3'd5,
        MEM_WR = 3'd6
    } state_t;

    state_t state;

    // ===============================================================
    // Registers
    // ===============================================================
    logic [31:0] regs [0:15];
    logic [31:0] pc;
    logic [15:0] instr_reg;
    logic        n_flag, z_flag, c_flag, v_flag;

    // ===============================================================
    // Instruction fields
    // ===============================================================
    logic [15:11] op5;
    logic [15:13] op3;
    logic [2:0]   rd3, rn3, rm3;
    logic [7:0]   imm8;
    logic [10:0]  imm11;
    logic [3:0]   cond;
    logic [3:0]   rd4;  // 4-bit register dest

    // Decoded control
    logic [3:0]  alu_op;
    localparam OP_ADD = 4'd0, OP_SUB = 4'd1, OP_MOV = 4'd2,
               OP_CMP = 4'd3, OP_AND = 4'd4, OP_ORR = 4'd5,
               OP_NOP = 4'd6, OP_LDR = 4'd7, OP_STR = 4'd8,
               OP_B   = 4'd9, OP_MSR = 4'd10;

    logic [3:0]  dec_rd;
    logic [31:0] dec_op_a, dec_op_b;
    logic        dec_wen;
    logic        dec_is_branch, dec_is_mem_rd, dec_is_mem_wr;
    logic [31:0] alu_result;
    logic        res_n, res_z, res_c, res_v;
    logic [31:0] branch_target;
    logic        branch_taken;

    // ===============================================================
    // Register read outputs (combinational)
    // Explicit mux for iverilog compatibility (avoids dynamic array index)
    // Uses intermediate variables to avoid @* sensitivity per-array-element
    // ===============================================================
    logic [3:0]  exec_ra1, exec_ra2;
    logic [31:0] exec_rd1, exec_rd2;
    logic [3:0]  exec_ra;
    logic [31:0] exec_rdd;
    logic [3:0]  exec_ra3;
    logic [31:0] exec_rd3;

    assign exec_ra1 = {1'b0, instr_reg[5:3]}; // Rn
    assign exec_ra2 = {1'b0, instr_reg[8:6]}; // Rm
    assign exec_ra  = {1'b0, instr_reg[10:8]}; // Rd for imm ops
    assign exec_ra3 = {1'b0, instr_reg[2:0]};  // Rt for STR

    // Read port 1 - explicit mux
    always_comb begin
        case (exec_ra1)
            4'd0:  exec_rd1 = regs[0];
            4'd1:  exec_rd1 = regs[1];
            4'd2:  exec_rd1 = regs[2];
            4'd3:  exec_rd1 = regs[3];
            4'd4:  exec_rd1 = regs[4];
            4'd5:  exec_rd1 = regs[5];
            4'd6:  exec_rd1 = regs[6];
            4'd7:  exec_rd1 = regs[7];
            4'd8:  exec_rd1 = regs[8];
            4'd9:  exec_rd1 = regs[9];
            4'd10: exec_rd1 = regs[10];
            4'd11: exec_rd1 = regs[11];
            4'd12: exec_rd1 = regs[12];
            4'd13: exec_rd1 = regs[13];
            4'd14: exec_rd1 = regs[14];
            4'd15: exec_rd1 = pc + 32'd4;
            default: exec_rd1 = regs[0];
        endcase
    end

    // Read port 2 - explicit mux
    always_comb begin
        case (exec_ra2)
            4'd0:  exec_rd2 = regs[0];
            4'd1:  exec_rd2 = regs[1];
            4'd2:  exec_rd2 = regs[2];
            4'd3:  exec_rd2 = regs[3];
            4'd4:  exec_rd2 = regs[4];
            4'd5:  exec_rd2 = regs[5];
            4'd6:  exec_rd2 = regs[6];
            4'd7:  exec_rd2 = regs[7];
            4'd8:  exec_rd2 = regs[8];
            4'd9:  exec_rd2 = regs[9];
            4'd10: exec_rd2 = regs[10];
            4'd11: exec_rd2 = regs[11];
            4'd12: exec_rd2 = regs[12];
            4'd13: exec_rd2 = regs[13];
            4'd14: exec_rd2 = regs[14];
            4'd15: exec_rd2 = pc + 32'd4;
            default: exec_rd2 = regs[0];
        endcase
    end

    // Read port 3 (for immediate ops Rd) - explicit mux
    always_comb begin
        case (exec_ra)
            4'd0:  exec_rdd = regs[0];
            4'd1:  exec_rdd = regs[1];
            4'd2:  exec_rdd = regs[2];
            4'd3:  exec_rdd = regs[3];
            4'd4:  exec_rdd = regs[4];
            4'd5:  exec_rdd = regs[5];
            4'd6:  exec_rdd = regs[6];
            4'd7:  exec_rdd = regs[7];
            4'd8:  exec_rdd = regs[8];
            4'd9:  exec_rdd = regs[9];
            4'd10: exec_rdd = regs[10];
            4'd11: exec_rdd = regs[11];
            4'd12: exec_rdd = regs[12];
            4'd13: exec_rdd = regs[13];
            4'd14: exec_rdd = regs[14];
            4'd15: exec_rdd = pc + 32'd4;
            default: exec_rdd = regs[0];
        endcase
    end

    // Read port 4 (Rt for STR) - explicit mux
    always_comb begin
        case (exec_ra3)
            4'd0:  exec_rd3 = regs[0];
            4'd1:  exec_rd3 = regs[1];
            4'd2:  exec_rd3 = regs[2];
            4'd3:  exec_rd3 = regs[3];
            4'd4:  exec_rd3 = regs[4];
            4'd5:  exec_rd3 = regs[5];
            4'd6:  exec_rd3 = regs[6];
            4'd7:  exec_rd3 = regs[7];
            4'd8:  exec_rd3 = regs[8];
            4'd9:  exec_rd3 = regs[9];
            4'd10: exec_rd3 = regs[10];
            4'd11: exec_rd3 = regs[11];
            4'd12: exec_rd3 = regs[12];
            4'd13: exec_rd3 = regs[13];
            4'd14: exec_rd3 = regs[14];
            4'd15: exec_rd3 = pc + 32'd4;
            default: exec_rd3 = regs[0];
        endcase
    end

    // ===============================================================
    // ALU
    // ===============================================================
    logic [31:0] add_res, sub_res;
    logic        add_c, sub_c, add_v, sub_v;

    assign {add_c, add_res} = {1'b0, dec_op_a} + {1'b0, dec_op_b};
    assign add_v = (dec_op_a[31] == dec_op_b[31]) && (add_res[31] != dec_op_a[31]);
    assign {sub_c, sub_res} = {1'b0, dec_op_a} + {1'b0, ~dec_op_b} + 32'd1;
    assign sub_v = (dec_op_a[31] != dec_op_b[31]) && (sub_res[31] != dec_op_a[31]);

    always @(*) begin
        alu_result = 32'd0;
        res_n = 1'b0; res_z = 1'b0; res_c = 1'b0; res_v = 1'b0;
        case (alu_op)
            OP_ADD: begin alu_result = add_res; res_n = add_res[31]; res_z = (add_res == 0); res_c = add_c; res_v = add_v; end
            OP_SUB: begin alu_result = sub_res; res_n = sub_res[31]; res_z = (sub_res == 0); res_c = sub_c; res_v = sub_v; end
            OP_MOV: begin alu_result = dec_op_a; res_n = dec_op_a[31]; res_z = (dec_op_a == 0); end
            OP_CMP: begin alu_result = sub_res; res_n = sub_res[31]; res_z = (sub_res == 0); res_c = sub_c; res_v = sub_v; end
            OP_AND: begin alu_result = dec_op_a & dec_op_b; res_n = alu_result[31]; res_z = (alu_result == 0); end
            OP_ORR: begin alu_result = dec_op_a | dec_op_b; res_n = alu_result[31]; res_z = (alu_result == 0); end
            default: begin alu_result = 32'd0; end
        endcase
    end

    // ===============================================================
    // Condition evaluation
    // ===============================================================
    logic cond_met;
    always @(*) begin
        case (cond)
            4'h0: cond_met = z_flag;          // EQ
            4'h1: cond_met = !z_flag;         // NE
            4'h2: cond_met = c_flag;          // CS
            4'h3: cond_met = !c_flag;         // CC
            4'h4: cond_met = n_flag;          // MI
            4'h5: cond_met = !n_flag;         // PL
            4'he: cond_met = 1'b1;            // AL
            default: cond_met = 1'b0;
        endcase
    end

    // ===============================================================
    // FSM
    // ===============================================================
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= RESET;
            pc <= 32'd0;
            for (integer i = 0; i < 16; i++)
                regs[i] <= 32'd0;
            regs[13] <= 32'h20004000; // SP default
            n_flag <= 0; z_flag <= 0; c_flag <= 0; v_flag <= 0;
            instr_reg <= 16'd0;
            instr_addr <= 32'd0;
            instr_req <= 1'b0;
            mem_addr <= 32'd0;
            mem_wdata <= 32'd0;
            mem_we <= 1'b0;
            mem_req <= 1'b0;
            mem_size <= 2'b10;
        end else begin
            case (state)
                RESET: begin
                    pc <= 32'd0;
                    state <= FETCH;
                end

                FETCH: begin
                    instr_addr <= pc;
                    instr_req  <= 1'b1;
                    state <= DECODE;
                end

                DECODE: begin
                    if (instr_ack) begin
                        instr_reg <= instr_rdata;
                        instr_req <= 1'b0;
                        state <= EXEC;
                    end
                end

                EXEC: begin
                    // Decode instruction fields
                    op5   <= instr_reg[15:11];
                    op3   <= instr_reg[15:13];
                    rd3   <= instr_reg[2:0];
                    rn3   <= instr_reg[5:3];
                    rm3   <= instr_reg[8:6];
                    imm8  <= instr_reg[7:0];
                    imm11 <= instr_reg[10:0];
                    cond  <= instr_reg[11:8];

                    // Default control signals
                    dec_wen <= 1'b0;
                    dec_is_branch <= 1'b0;
                    dec_is_mem_rd <= 1'b0;
                    dec_is_mem_wr <= 1'b0;
                    alu_op <= OP_NOP;

                    casez (instr_reg)
                        // NOP
                        16'hBF00: begin
                            alu_op <= OP_NOP;
                        end

                        // MOV Rdn, #imm8: 00100 Rdn(3) imm8(8)
                        16'b00100_???_????????: begin
                            dec_rd <= {1'b0, instr_reg[10:8]};
                            dec_op_a <= {24'd0, instr_reg[7:0]};
                            dec_op_b <= 32'd0;
                            alu_op <= OP_MOV;
                            dec_wen <= 1'b1;
                        end

                        // CMP Rdn, #imm8: 00101 Rdn(3) imm8(8)
                        16'b00101_???_????????: begin
                            dec_op_a <= exec_rdd;
                            dec_op_b <= {24'd0, instr_reg[7:0]};
                            alu_op <= OP_CMP;
                        end

                        // ADD Rdn, #imm8: 00110 Rdn(3) imm8(8)
                        16'b00110_???_????????: begin
                            dec_rd <= {1'b0, instr_reg[10:8]};
                            dec_op_a <= exec_rdd;
                            dec_op_b <= {24'd0, instr_reg[7:0]};
                            alu_op <= OP_ADD;
                            dec_wen <= 1'b1;
                        end

                        // SUB Rdn, #imm8: 00111 Rdn(3) imm8(8)
                        16'b00111_???_????????: begin
                            dec_rd <= {1'b0, instr_reg[10:8]};
                            dec_op_a <= exec_rdd;
                            dec_op_b <= {24'd0, instr_reg[7:0]};
                            alu_op <= OP_SUB;
                            dec_wen <= 1'b1;
                        end

                        // ADD Rd, Rn, Rm: 0001100 Rm(3) Rn(3) Rd(3)
                        16'b0001100_???_???_???: begin
                            dec_rd <= {1'b0, instr_reg[2:0]};
                            dec_op_a <= exec_rd1;
                            dec_op_b <= exec_rd2;
                            alu_op <= OP_ADD;
                            dec_wen <= 1'b1;
                        end

                        // SUB Rd, Rn, Rm: 0001101 Rm(3) Rn(3) Rd(3)
                        16'b0001101_???_???_???: begin
                            dec_rd <= {1'b0, instr_reg[2:0]};
                            dec_op_a <= exec_rd1;
                            dec_op_b <= exec_rd2;
                            alu_op <= OP_SUB;
                            dec_wen <= 1'b1;
                        end

                        // CMP Rn, Rm (low): 0100001010 Rm(3) Rn(3)
                        // Format: Rm at [5:3], Rn at [2:0]
                        // CMP computes Rn - Rm
                        16'b0100001010_???_???: begin
                            dec_op_a <= exec_rd3; // Rn from bits [2:0]
                            dec_op_b <= exec_rd1; // Rm from bits [5:3]
                            alu_op <= OP_CMP;
                        end

                        // STR Rt, [Rn, Rm]: 0101000 Rm(3) Rn(3) Rt(3)
                        16'b0101000_???_???_???: begin
                            dec_op_a <= exec_rd1 + exec_rd2;
                            dec_op_b <= exec_rd3; // Rt value via mux
                            alu_op <= OP_STR;
                            dec_is_mem_wr <= 1'b1;
                        end

                        // LDR Rt, [Rn, Rm]: 0101100 Rm(3) Rn(3) Rt(3)
                        16'b0101100_???_???_???: begin
                            dec_rd <= {1'b0, instr_reg[2:0]};
                            dec_op_a <= exec_rd1 + exec_rd2;
                            dec_op_b <= 32'd0;
                            alu_op <= OP_LDR;
                            dec_wen <= 1'b1;
                            dec_is_mem_rd <= 1'b1;
                        end

                        // B (conditional): 1101 cond(4) imm8(8)
                        16'b1101_????_????????: begin
                            if (instr_reg[11:8] != 4'he) begin
                                branch_target <= pc + 32'd4 + {{23{instr_reg[7]}}, instr_reg[7:0], 1'b0};
                                dec_is_branch <= 1'b1;
                                cond <= instr_reg[11:8];
                                alu_op <= OP_B;
                            end
                        end

                        // B (unconditional): 11100 imm11(11)
                        16'b11100_???????????: begin
                            branch_target <= pc + 32'd4 + {{20{instr_reg[10]}}, instr_reg[10:0], 1'b0};
                            dec_is_branch <= 1'b1;
                            cond <= 4'he;
                            alu_op <= OP_B;
                        end

                        default: begin
                            alu_op <= OP_NOP;
                        end
                    endcase

                    state <= WB;
                end

                WB: begin
                    // Update flags for CMP/ADD/SUB
                    if (alu_op == OP_CMP || alu_op == OP_ADD || alu_op == OP_SUB) begin
                        n_flag <= res_n;
                        z_flag <= res_z;
                        c_flag <= res_c;
                        v_flag <= res_v;
                    end

                    // Branch handling
                    branch_taken <= 1'b0;
                    if (dec_is_branch && cond_met) begin
                        pc <= branch_target;
                        branch_taken <= 1'b1;
                    end

                    // Memory write (STR)
                    if (dec_is_mem_wr) begin
                        mem_addr <= dec_op_a;
                        mem_wdata <= dec_op_b;
                        mem_we <= 1'b1;
                        mem_req <= 1'b1;
                        state <= MEM_WR;
                    end
                    // Memory read (LDR)
                    else if (dec_is_mem_rd) begin
                        mem_addr <= dec_op_a;
                        mem_we <= 1'b0;
                        mem_req <= 1'b1;
                        state <= MEM_RD;
                    end
                    // Register writeback (non-branch)
                    else if (!dec_is_branch) begin
                        if (dec_wen) begin
                            if (dec_rd != 4'd15)
                                regs[dec_rd] <= alu_result;
                        end
                        pc <= pc + 32'd2;
                        state <= FETCH;
                    end
                    // Branch: PC already set above
                    else begin
                        // Branch taken path: pc already assigned via branch_target above
                        // Branch not taken path: advance pc
                        if (!cond_met)
                            pc <= pc + 32'd2;
                        state <= FETCH;
                    end
                end

                MEM_WR: begin
                    if (mem_ack) begin
                        mem_we <= 1'b0;
                        mem_req <= 1'b0;
                        pc <= pc + 32'd2;
                        state <= FETCH;
                    end
                end

                MEM_RD: begin
                    if (mem_ack) begin
                        mem_req <= 1'b0;
                        if (dec_wen && dec_rd != 4'd15)
                            regs[dec_rd] <= mem_rdata;
                        pc <= pc + 32'd2;
                        state <= FETCH;
                    end
                end

                default: state <= RESET;
            endcase
        end
    end

endmodule
