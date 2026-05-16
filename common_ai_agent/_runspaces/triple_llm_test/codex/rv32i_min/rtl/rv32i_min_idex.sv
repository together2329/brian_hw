module rv32i_min_idex #(
    parameter integer XLEN = 32
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic              valid_i,
    input  logic [XLEN-1:0]   instr_i,
    input  logic [XLEN-1:0]   pc_i,
    input  logic [XLEN-1:0]   rs1_i,
    input  logic [XLEN-1:0]   rs2_i,
    input  logic [XLEN-1:0]   imm_i,

    input  logic              gpr_wr_en_i,
    input  logic              gpr_rd_en_i,
    input  logic [4:0]        gpr_addr_i,
    input  logic [XLEN-1:0]   gpr_wdata_i,
    output logic [XLEN-1:0]   gpr_rdata_o,

    output logic              valid_o,
    output logic [4:0]        rd_idx_o,
    output logic [XLEN-1:0]   wb_data_o,
    output logic              wb_we_o,
    output logic [XLEN-1:0]   alu_result_o,
    output logic              is_branch_o,
    output logic              branch_taken_o,
    output logic [XLEN-1:0]   branch_imm_o,
    output logic              is_jump_o,
    output logic              is_jalr_o,
    output logic [XLEN-1:0]   jump_target_o,
    output logic              is_system_o,
    output logic              is_fence_o,
    output logic              is_ecall_o,
    output logic              is_ebreak_o,
    output logic              illegal_shamt_o,
    output logic              excpt_o,
    output logic [XLEN-1:0]   pc_state_o,
    output logic [XLEN-1:0]   next_pc_o,
    output logic              bubble_o
);

    localparam [1:0] RESET = 2'd0;
    localparam [1:0] RUN = 2'd1;
    localparam [1:0] FENCE_BUBBLE = 2'd2;

    localparam [4:0] OPCODE_CLASS_ALU_IMM = 5'd0;
    localparam [4:0] OPCODE_CLASS_ALU_REG = 5'd1;
    localparam [4:0] OPCODE_CLASS_BRANCH  = 5'd2;
    localparam [4:0] OPCODE_CLASS_JUMP    = 5'd3;
    localparam [4:0] OPCODE_CLASS_LOAD    = 5'd4;
    localparam [4:0] OPCODE_CLASS_STORE   = 5'd5;
    localparam [4:0] OPCODE_CLASS_SYSTEM  = 5'd6;

    logic [1:0] state_q;
    logic [1:0] state_d;

    logic [XLEN-1:0] pc_q;
    logic [XLEN-1:0] next_pc_d;

    logic [XLEN-1:0] gpr_value_q;

    logic [6:0] opcode;
    logic [2:0] funct3;
    logic [6:0] funct7;
    logic [4:0] rd_idx;
    logic [4:0] shamt;

    logic [4:0] opcode_class;
    logic opcode_class_is_alu;

    logic decoded_branch;
    logic decoded_jal;
    logic decoded_jalr;
    logic decoded_system;
    logic decoded_fence;
    logic decoded_ecall;
    logic decoded_ebreak;

    logic branch_taken_d;
    logic [XLEN-1:0] alu_result;
    logic [XLEN-1:0] wb_data_d;
    logic wb_we_d;
    logic illegal_shamt_d;
    logic excpt_d;

    assign opcode = instr_i[6:0];
    assign rd_idx = instr_i[11:7];
    assign funct3 = instr_i[14:12];
    assign shamt  = instr_i[24:20];
    assign funct7 = instr_i[31:25];

    always @(*) begin
        opcode_class = OPCODE_CLASS_ALU_IMM;
        decoded_branch = 1'b0;
        decoded_jal = 1'b0;
        decoded_jalr = 1'b0;
        decoded_system = 1'b0;
        decoded_fence = 1'b0;
        decoded_ecall = 1'b0;
        decoded_ebreak = 1'b0;

        case (opcode)
            7'b0010011: opcode_class = OPCODE_CLASS_ALU_IMM;
            7'b0110011: opcode_class = OPCODE_CLASS_ALU_REG;
            7'b1100011: begin
                opcode_class = OPCODE_CLASS_BRANCH;
                decoded_branch = 1'b1;
            end
            7'b1101111: begin
                opcode_class = OPCODE_CLASS_JUMP;
                decoded_jal = 1'b1;
            end
            7'b1100111: begin
                opcode_class = OPCODE_CLASS_JUMP;
                decoded_jalr = 1'b1;
            end
            7'b0000011: opcode_class = OPCODE_CLASS_LOAD;
            7'b0100011: opcode_class = OPCODE_CLASS_STORE;
            7'b1110011: begin
                opcode_class = OPCODE_CLASS_SYSTEM;
                decoded_system = 1'b1;
                if (funct3 == 3'b000 && instr_i[31:20] == 12'h000) decoded_ecall = 1'b1;
                if (funct3 == 3'b000 && instr_i[31:20] == 12'h001) decoded_ebreak = 1'b1;
            end
            7'b0001111: begin
                opcode_class = OPCODE_CLASS_SYSTEM;
                decoded_system = 1'b1;
                decoded_fence = 1'b1;
            end
            default: opcode_class = OPCODE_CLASS_ALU_IMM;
        endcase
    end

    assign opcode_class_is_alu = (opcode_class == OPCODE_CLASS_ALU_IMM) || (opcode_class == OPCODE_CLASS_ALU_REG);

    always @(*) begin
        alu_result = {XLEN{1'b0}};
        case (funct3)
            3'b000: begin
                if (opcode == 7'b0110011 && funct7 == 7'b0100000) alu_result = rs1_i - rs2_i;
                else if (opcode == 7'b0110011)                    alu_result = rs1_i + rs2_i;
                else                                               alu_result = rs1_i + imm_i;
            end
            3'b001: alu_result = rs1_i << rs2_i[4:0];
            3'b010: alu_result = ($signed(rs1_i) < $signed((opcode == 7'b0110011) ? rs2_i : imm_i)) ? 32'd1 : 32'd0;
            3'b011: alu_result = (rs1_i < ((opcode == 7'b0110011) ? rs2_i : imm_i)) ? 32'd1 : 32'd0;
            3'b100: alu_result = rs1_i ^ ((opcode == 7'b0110011) ? rs2_i : imm_i);
            3'b101: begin
                if (opcode == 7'b0110011 && funct7 == 7'b0100000) alu_result = $signed(rs1_i) >>> rs2_i[4:0];
                else if (opcode == 7'b0010011 && funct7 == 7'b0100000) alu_result = $signed(rs1_i) >>> shamt;
                else if (opcode == 7'b0110011) alu_result = rs1_i >> rs2_i[4:0];
                else alu_result = rs1_i >> shamt;
            end
            3'b110: alu_result = rs1_i | ((opcode == 7'b0110011) ? rs2_i : imm_i);
            3'b111: alu_result = rs1_i & ((opcode == 7'b0110011) ? rs2_i : imm_i);
            default: alu_result = {XLEN{1'b0}};
        endcase
    end

    always @(*) begin
        branch_taken_d = 1'b0;
        if (decoded_branch) begin
            case (funct3)
                3'b000: branch_taken_d = (rs1_i == rs2_i);
                3'b001: branch_taken_d = (rs1_i != rs2_i);
                3'b100: branch_taken_d = ($signed(rs1_i) < $signed(rs2_i));
                3'b101: branch_taken_d = ($signed(rs1_i) >= $signed(rs2_i));
                3'b110: branch_taken_d = (rs1_i < rs2_i);
                3'b111: branch_taken_d = (rs1_i >= rs2_i);
                default: branch_taken_d = 1'b0;
            endcase
        end
    end

    always @(*) begin
        illegal_shamt_d = 1'b0;
        if (opcode == 7'b0010011 && (funct3 == 3'b001 || funct3 == 3'b101)) begin
            if (instr_i[31:26] != 6'b000000 && instr_i[31:26] != 6'b010000) illegal_shamt_d = 1'b1;
        end
    end

    always @(*) begin
        next_pc_d = pc_q + 32'd4;
        if (decoded_branch && branch_taken_d) next_pc_d = pc_q + imm_i;
        if (decoded_jal) next_pc_d = pc_q + imm_i;
        if (decoded_jalr) next_pc_d = (rs1_i + imm_i) & 32'hFFFF_FFFE;
    end

    always @(*) begin
        wb_data_d = alu_result & 32'hFFFF_FFFF;
        wb_we_d = 1'b0;
        if (valid_i && opcode_class_is_alu && !illegal_shamt_d && (state_q == RUN) && (rd_idx != 5'd0)) wb_we_d = 1'b1;
        if (valid_i && (decoded_jal || decoded_jalr) && (state_q == RUN) && (rd_idx != 5'd0)) begin
            wb_we_d = 1'b1;
            wb_data_d = pc_q + 32'd4;
        end
    end

    always @(*) begin
        excpt_d = 1'b0;
        if (valid_i && state_q == RUN) begin
            if (illegal_shamt_d) excpt_d = 1'b1;
            if (decoded_ecall || decoded_ebreak) excpt_d = 1'b1;
        end
    end

    always @(*) begin
        state_d = state_q;
        case (state_q)
            RESET: begin
                if (rst_n) state_d = RUN;
            end
            RUN: begin
                if (valid_i && decoded_fence) state_d = FENCE_BUBBLE;
            end
            FENCE_BUBBLE: begin
                state_d = RUN;
            end
            default: state_d = RESET;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q <= RESET;
            pc_q <= 32'd0;
            valid_o <= 1'b0;
            rd_idx_o <= 5'd0;
            wb_data_o <= 32'd0;
            wb_we_o <= 1'b0;
            alu_result_o <= 32'd0;
            is_branch_o <= 1'b0;
            branch_taken_o <= 1'b0;
            branch_imm_o <= 32'd0;
            is_jump_o <= 1'b0;
            is_jalr_o <= 1'b0;
            jump_target_o <= 32'd0;
            is_system_o <= 1'b0;
            is_fence_o <= 1'b0;
            is_ecall_o <= 1'b0;
            is_ebreak_o <= 1'b0;
            illegal_shamt_o <= 1'b0;
            excpt_o <= 1'b0;
            next_pc_o <= 32'd0;
            bubble_o <= 1'b0;
            gpr_value_q <= 32'd0;
        end else begin
            state_q <= state_d;
            bubble_o <= (state_q == FENCE_BUBBLE);

            if (state_q == RESET) begin
                pc_q <= 32'd0;
                valid_o <= 1'b0;
                excpt_o <= 1'b0;
            end else if (state_q == RUN) begin
                pc_q <= pc_i;
                valid_o <= valid_i;
                rd_idx_o <= rd_idx;
                alu_result_o <= alu_result;
                wb_data_o <= wb_data_d;
                wb_we_o <= wb_we_d;
                is_branch_o <= decoded_branch;
                branch_taken_o <= branch_taken_d;
                branch_imm_o <= imm_i;
                is_jump_o <= decoded_jal || decoded_jalr;
                is_jalr_o <= decoded_jalr;
                jump_target_o <= (decoded_jalr) ? ((rs1_i + imm_i) & 32'hFFFF_FFFE) : (pc_q + imm_i);
                is_system_o <= decoded_system;
                is_fence_o <= decoded_fence;
                is_ecall_o <= decoded_ecall;
                is_ebreak_o <= decoded_ebreak;
                illegal_shamt_o <= illegal_shamt_d;
                excpt_o <= excpt_d;
                next_pc_o <= next_pc_d;
            end else begin
                valid_o <= 1'b0;
                wb_we_o <= 1'b0;
                excpt_o <= 1'b0;
                is_fence_o <= 1'b0;
            end

            if (gpr_wr_en_i && (gpr_addr_i == 5'd0)) gpr_value_q <= gpr_wdata_i;
        end
    end

    always @(*) begin
        gpr_rdata_o = 32'd0;
        if (gpr_rd_en_i && (gpr_addr_i == 5'd0)) gpr_rdata_o = gpr_value_q;
    end

    assign pc_state_o = pc_q;

endmodule
