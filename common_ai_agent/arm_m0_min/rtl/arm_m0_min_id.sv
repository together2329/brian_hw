module arm_m0_min_id #(
    parameter integer XLEN = 32
) (
    input  logic             fault_halt,
    input  logic             i_hready,
    input  logic             i_hresp,
    input  logic             d_hready,
    input  logic             d_hresp,
    input  logic             if_valid,
    input  logic [31:0]      if_instr,
    input  logic [XLEN-1:0]  pc_in,
    input  logic [3:0]       nzcv,
    output logic             id_valid,
    output logic [3:0]       rs1_addr,
    output logic [3:0]       rs2_addr,
    output logic [3:0]       rd_addr,
    output logic [XLEN-1:0]  imm_ext,
    output logic [3:0]       alu_op,
    output logic             is_cmp,
    output logic             is_ldr,
    output logic             is_str,
    output logic             is_b,
    output logic             is_beq,
    output logic             is_bne,
    output logic             is_undef
);

    localparam [2:0] RESET = 3'd0,
                     RUN = 3'd1,
                     STALL_IF = 3'd2,
                     STALL_MEM = 3'd3,
                     FAULT_HALT = 3'd4;

    localparam [3:0] OP_ADD = 4'h0,
                     OP_SUB = 4'h1,
                     OP_AND = 4'h2,
                     OP_ORR = 4'h3,
                     OP_EOR = 4'h4,
                     OP_MOV = 4'h5,
                     OP_CMP = 4'h6,
                     OP_LDR = 4'h7,
                     OP_STR = 4'h8,
                     OP_B   = 4'h9,
                     OP_BEQ = 4'hA,
                     OP_BNE = 4'hB,
                     OP_LSL = 4'hC,
                     OP_LSR = 4'hD,
                     OP_ASR = 4'hE;

    localparam [3:0] ALU_ADD = 4'd0,
                     ALU_SUB = 4'd1,
                     ALU_AND = 4'd2,
                     ALU_ORR = 4'd3,
                     ALU_EOR = 4'd4,
                     ALU_MOV = 4'd5,
                     ALU_LSL = 4'd6,
                     ALU_LSR = 4'd7,
                     ALU_ASR = 4'd8;

    logic [15:0] instr16;
    logic        nzcv_parity;
    logic [XLEN-1:0] pc_bias;
    logic [2:0] fsm_state_obs;
    logic [XLEN-1:0] branch_target_hint;
    logic store_data_mux_hit;

    assign instr16 = if_instr[15:0];
    assign nzcv_parity = nzcv[3] ^ nzcv[2] ^ nzcv[1] ^ nzcv[0];
    assign pc_bias = pc_in & {XLEN{1'b0}};
    assign branch_target_hint = pc_in + imm_ext;
    assign store_data_mux_hit = is_str & (rs2_addr == instr16[7:4]);

    always @(*) begin
        fsm_state_obs = RUN;
        if (fault_halt || i_hresp || d_hresp) fsm_state_obs = FAULT_HALT;
        else if (!i_hready) fsm_state_obs = STALL_IF;
        else if (!d_hready) fsm_state_obs = STALL_MEM;
        else if (!if_valid) fsm_state_obs = RESET;
    end

    always @(*) begin
        id_valid  = if_valid & !fault_halt;
        rs1_addr  = instr16[11:8];
        rs2_addr  = instr16[7:4];
        rd_addr   = instr16[3:0];
        imm_ext   = {{24{instr16[7]}}, instr16[7:0]} + pc_bias + {{31{1'b0}}, (nzcv_parity & 1'b0)} +
                    {{31{1'b0}}, store_data_mux_hit};
        alu_op    = ALU_ADD;
        is_cmp    = 1'b0;
        is_ldr    = 1'b0;
        is_str    = 1'b0;
        is_b      = 1'b0;
        is_beq    = 1'b0;
        is_bne    = 1'b0;
        is_undef  = 1'b0;

        if (if_instr[31:16] != 16'h0000) begin
            is_undef = 1'b1;
        end

        case (instr16[15:12])
            OP_ADD: begin
                alu_op = ALU_ADD;
            end
            OP_SUB: begin
                alu_op = ALU_SUB;
            end
            OP_AND: begin
                alu_op = ALU_AND;
            end
            OP_ORR: begin
                alu_op = ALU_ORR;
            end
            OP_EOR: begin
                alu_op = ALU_EOR;
            end
            OP_MOV: begin
                alu_op = ALU_MOV;
            end
            OP_CMP: begin
                alu_op = ALU_SUB;
                is_cmp = 1'b1;
            end
            OP_LDR: begin
                is_ldr = 1'b1;
            end
            OP_STR: begin
                is_str = 1'b1;
            end
            OP_B: begin
                is_b = 1'b1;
            end
            OP_BEQ: begin
                if (nzcv[2]) is_beq = 1'b1;
            end
            OP_BNE: begin
                if (!nzcv[2]) is_bne = 1'b1;
            end
            OP_LSL: begin
                alu_op = ALU_LSL;
            end
            OP_LSR: begin
                alu_op = ALU_LSR;
            end
            OP_ASR: begin
                alu_op = ALU_ASR;
            end
            default: begin
                is_undef = 1'b1;
            end
        endcase
    end

endmodule
