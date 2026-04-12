//=============================================================================
// ARM Instruction Decoder
// Decodes ARM (32-bit) instruction encoding:
//   [31:28] Condition
//   [27:26] Instruction type
//   [25]    Immediate/Operand2 type
//   [24:21] Opcode (for data processing)
//   [20]    S-bit (set flags)
//   [19:16] Rn
//   [15:12] Rd
//   [11:0]  Operand2
//=============================================================================

package arm_defs;

    // Instruction class encoding (bits [27:25])
    localparam logic [2:0] INST_DATA_PROC  = 3'b000;
    localparam logic [2:0] INST_DATA_PROC_IMM = 3'b001; // bit 25=1 means imm for data proc
    localparam logic [2:0] INST_LOAD_STORE  = 3'b010;
    localparam logic [2:0] INST_LOAD_STORE_IMM = 3'b011;
    localparam logic [2:0] INST_BRANCH      = 3'b101;
    localparam logic [2:0] INST_BLOCK_TRANS = 3'b100;
    localparam logic [2:0] INST_SWI         = 3'b111;

    // ALU operations
    localparam logic [3:0] ALU_AND = 4'h0;
    localparam logic [3:0] ALU_EOR = 4'h1;
    localparam logic [3:0] ALU_SUB = 4'h2;
    localparam logic [3:0] ALU_RSB = 4'h3;
    localparam logic [3:0] ALU_ADD = 4'h4;
    localparam logic [3:0] ALU_ADC = 4'h5;
    localparam logic [3:0] ALU_SBC = 4'h6;
    localparam logic [3:0] ALU_RSC = 4'h7;
    localparam logic [3:0] ALU_TST = 4'h8;
    localparam logic [3:0] ALU_TEQ = 4'h9;
    localparam logic [3:0] ALU_CMP = 4'hA;
    localparam logic [3:0] ALU_CMN = 4'hB;
    localparam logic [3:0] ALU_ORR = 4'hC;
    localparam logic [3:0] ALU_MOV = 4'hD;
    localparam logic [3:0] ALU_BIC = 4'hE;
    localparam logic [3:0] ALU_MVN = 4'hF;

endpackage


module arm_decoder (
    input  logic [31:0] instr,         // 32-bit instruction

    // Decoded fields
    output logic [3:0]  cond,          // Condition code [31:28]
    output logic [3:0]  opcode,        // ALU operation [24:21]
    output logic        s_bit,         // Set flags [20]
    output logic [3:0]  rn,            // Rn field [19:16]
    output logic [3:0]  rd,            // Rd field [15:12]
    output logic [11:0] operand2,      // Operand2 [11:0]
    output logic [23:0] signed_offset, // Branch offset [23:0]
    output logic [3:0]  rd_ls,         // Load/store Rd [15:12]
    output logic [11:0] ls_offset,     // Load/store offset [11:0]
    output logic [15:0] reg_list,      // Block transfer register list [15:0]

    // Control signals
    output logic        is_data_proc,  // Data processing instruction
    output logic        is_imm_op2,    // Immediate operand2 (bit [25])
    output logic        is_load_store, // Load/Store instruction
    output logic        is_load,       // Load (L-bit)
    output logic        is_store,      // Store
    output logic        is_byte,       // Byte access (B-bit)
    output logic        is_pre_index,  // Pre-indexed (U-bit)
    output logic        is_writeback,  // Writeback (W-bit)
    output logic        is_branch,     // Branch instruction
    output logic        is_branch_link,// Branch with Link (BL)
    output logic        is_block_trans,// Block transfer (LDM/STM)
    output logic        is_swi,        // Software interrupt
    output logic        is_mul,        // Multiply instruction
    output logic        is_msr,        // MSR instruction
    output logic        is_mrs         // MRS instruction
);

    // Bit extraction
    assign cond         = instr[31:28];
    assign opcode       = instr[24:21];
    assign s_bit        = instr[20];
    assign rn           = instr[19:16];
    assign rd           = instr[15:12];
    assign operand2     = instr[11:0];
    assign signed_offset= instr[23:0];
    assign rd_ls        = instr[15:12];
    assign ls_offset    = instr[11:0];
    assign reg_list     = instr[15:0];

    // Instruction classification
    always_comb begin
        // Default all control signals
        is_data_proc   = 1'b0;
        is_imm_op2     = 1'b0;
        is_load_store  = 1'b0;
        is_load        = 1'b0;
        is_store       = 1'b0;
        is_byte        = 1'b0;
        is_pre_index   = 1'b0;
        is_writeback   = 1'b0;
        is_branch      = 1'b0;
        is_branch_link = 1'b0;
        is_block_trans = 1'b0;
        is_swi         = 1'b0;
        is_mul         = 1'b0;
        is_msr         = 1'b0;
        is_mrs         = 1'b0;

        case (instr[27:26])
            2'b00: begin
                // Data processing or multiply
                if (instr[25:24] == 2'b00 && instr[7] == 1'b1 && instr[4] == 1'b1) begin
                    // Multiply instruction pattern
                    is_mul = 1'b1;
                end
                else if (opcode == 4'h2 && rd == 4'hF && s_bit == 1'b0) begin
                    // MSR (register)
                    is_msr = 1'b1;
                end
                else if (opcode == 4'hF && rn == 4'hF && s_bit == 1'b0) begin
                    // MRS
                    is_mrs = 1'b1;
                end
                else begin
                    is_data_proc = 1'b1;
                end
                is_imm_op2 = instr[25];
            end

            2'b01: begin
                // Load/Store
                is_load_store = 1'b1;
                is_load       = instr[20];
                is_store      = ~instr[20];
                is_byte       = instr[22];
                is_pre_index  = instr[24];  // P-bit: 1=pre, 0=post
                is_writeback  = instr[21];  // W-bit
                is_imm_op2    = ~instr[25]; // I-bit: 0=immediate offset, 1=register offset
            end

            2'b10: begin
                if (instr[25]) begin
                    // Branch (L-bit at [24])
                    is_branch      = 1'b1;
                    is_branch_link = instr[24];
                end else begin
                    // Block data transfer (LDM/STM)
                    is_block_trans = 1'b1;
                    is_load        = instr[20];
                    is_store       = ~instr[20];
                    is_writeback   = instr[21]; // W-bit
                end
            end

            2'b11: begin
                if (instr[25]) begin
                    is_swi = 1'b1; // Software interrupt
                end else begin
                    // Coprocessor — not implemented
                end
            end
        endcase
    end

endmodule
