// ============================================================================
// Module: cpu_imm_gen
// Description: Immediate Generator for RISC-V RV32I
//              Generates sign-extended immediates for I, S, B, U, J types
//              Also handles CSR immediate (5-bit zero-extended for CSRRWI etc.)
// ============================================================================

module cpu_imm_gen (
    input  logic [31:0] instruction_i,

    output logic [31:0] imm_i_type_o,   // I-type immediate
    output logic [31:0] imm_s_type_o,   // S-type immediate
    output logic [31:0] imm_b_type_o,   // B-type immediate
    output logic [31:0] imm_u_type_o,   // U-type immediate
    output logic [31:0] imm_j_type_o,   // J-type immediate
    output logic [31:0] imm_csr_o       // CSR immediate (5-bit, zero-extended)
);

    // =========================================================================
    // I-type: imm[31:20] -> sign extend
    // =========================================================================
    assign imm_i_type_o = {{20{instruction_i[31]}}, instruction_i[31:20]};

    // =========================================================================
    // S-type: imm[31:25] + imm[11:7] -> sign extend
    // =========================================================================
    assign imm_s_type_o = {{20{instruction_i[31]}}, instruction_i[31:25], instruction_i[11:7]};

    // =========================================================================
    // B-type: imm[12|10:5|4:1|11] -> sign extend
    // =========================================================================
    assign imm_b_type_o = {{19{instruction_i[31]}},
                           instruction_i[31],
                           instruction_i[7],
                           instruction_i[30:25],
                           instruction_i[11:8],
                           1'b0};

    // =========================================================================
    // U-type: imm[31:12] << 12
    // =========================================================================
    assign imm_u_type_o = {instruction_i[31:12], 12'b0};

    // =========================================================================
    // J-type: imm[20|10:1|11|19:12] -> sign extend
    // =========================================================================
    assign imm_j_type_o = {{11{instruction_i[31]}},
                           instruction_i[19:12],
                           instruction_i[20],
                           instruction_i[30:21],
                           1'b0};

    // =========================================================================
    // CSR immediate: uimm[19:15] -> zero extend to 32 bits
    // =========================================================================
    assign imm_csr_o = {27'b0, instruction_i[19:15]};

endmodule
