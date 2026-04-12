//=============================================================================
// ARM ALU (Arithmetic Logic Unit)
// Supports ARM data-processing operations:
//   AND, EOR, SUB, RSB, ADD, ADC, SBC, RSC,
//   TST, TEQ, CMP, CMN, ORR, MOV, BIC, MVN
//=============================================================================

module arm_alu (
    input  logic [31:0] op_a,         // Operand A (Rn)
    input  logic [31:0] op_b,         // Operand B (shifter result)
    input  logic [3:0]  alu_op,       // ALU operation select
    input  logic        carry_in,     // CPSR carry flag
    input  logic        update_flags, // S-bit: update CPSR flags

    output logic [31:0] result,       // ALU result
    output logic        flag_n,       // Negative flag
    output logic        flag_z,       // Zero flag
    output logic        flag_c,       // Carry flag
    output logic        flag_v        // Overflow flag
);

    logic [31:0] alu_result;
    logic        alu_carry;
    logic        alu_overflow;
    logic [32:0] add_result;  // 33-bit for carry
    logic [32:0] sub_result;

    // 64-bit for multiply (optional extension)
    logic [63:0] mul_result;

    always_comb begin
        alu_result  = 32'd0;
        alu_carry   = carry_in;
        alu_overflow = 1'b0;

        case (alu_op)
            // AND: Rd = Rn AND Op2
            4'h0: begin
                alu_result = op_a & op_b;
                alu_carry  = carry_in; // carry from shifter
            end

            // EOR: Rd = Rn XOR Op2
            4'h1: begin
                alu_result = op_a ^ op_b;
                alu_carry  = carry_in;
            end

            // SUB: Rd = Rn - Op2
            4'h2: begin
                sub_result = {1'b0, op_a} - {1'b0, op_b};
                alu_result = sub_result[31:0];
                alu_carry  = ~sub_result[32]; // inverted for SUB
                alu_overflow = (op_a[31] != op_b[31]) && (alu_result[31] != op_a[31]);
            end

            // RSB: Rd = Op2 - Rn
            4'h3: begin
                sub_result = {1'b0, op_b} - {1'b0, op_a};
                alu_result = sub_result[31:0];
                alu_carry  = ~sub_result[32];
                alu_overflow = (op_a[31] != op_b[31]) && (alu_result[31] != op_b[31]);
            end

            // ADD: Rd = Rn + Op2
            4'h4: begin
                add_result = {1'b0, op_a} + {1'b0, op_b};
                alu_result = add_result[31:0];
                alu_carry  = add_result[32];
                alu_overflow = (op_a[31] == op_b[31]) && (alu_result[31] != op_a[31]);
            end

            // ADC: Rd = Rn + Op2 + Carry
            4'h5: begin
                add_result = {1'b0, op_a} + {1'b0, op_b} + {32'd0, carry_in};
                alu_result = add_result[31:0];
                alu_carry  = add_result[32];
                alu_overflow = (op_a[31] == op_b[31]) && (alu_result[31] != op_a[31]);
            end

            // SBC: Rd = Rn - Op2 - !Carry
            4'h6: begin
                sub_result = {1'b0, op_a} - {1'b0, op_b} - {32'd0, ~carry_in};
                alu_result = sub_result[31:0];
                alu_carry  = ~sub_result[32];
                alu_overflow = (op_a[31] != op_b[31]) && (alu_result[31] != op_a[31]);
            end

            // RSC: Rd = Op2 - Rn - !Carry
            4'h7: begin
                sub_result = {1'b0, op_b} - {1'b0, op_a} - {32'd0, ~carry_in};
                alu_result = sub_result[31:0];
                alu_carry  = ~sub_result[32];
                alu_overflow = (op_a[31] != op_b[31]) && (alu_result[31] != op_b[31]);
            end

            // TST: Rn AND Op2 (result not written, flags updated)
            4'h8: begin
                alu_result = op_a & op_b;
                alu_carry  = carry_in;
            end

            // TEQ: Rn XOR Op2
            4'h9: begin
                alu_result = op_a ^ op_b;
                alu_carry  = carry_in;
            end

            // CMP: Rn - Op2 (flags only)
            4'hA: begin
                sub_result = {1'b0, op_a} - {1'b0, op_b};
                alu_result = sub_result[31:0];
                alu_carry  = ~sub_result[32];
                alu_overflow = (op_a[31] != op_b[31]) && (alu_result[31] != op_a[31]);
            end

            // CMN: Rn + Op2 (flags only)
            4'hB: begin
                add_result = {1'b0, op_a} + {1'b0, op_b};
                alu_result = add_result[31:0];
                alu_carry  = add_result[32];
                alu_overflow = (op_a[31] == op_b[31]) && (alu_result[31] != op_a[31]);
            end

            // ORR: Rd = Rn OR Op2
            4'hC: begin
                alu_result = op_a | op_b;
                alu_carry  = carry_in;
            end

            // MOV: Rd = Op2
            4'hD: begin
                alu_result = op_b;
                alu_carry  = carry_in;
            end

            // BIC: Rd = Rn AND NOT Op2
            4'hE: begin
                alu_result = op_a & ~op_b;
                alu_carry  = carry_in;
            end

            // MVN: Rd = NOT Op2
            4'hF: begin
                alu_result = ~op_b;
                alu_carry  = carry_in;
            end

            default: begin
                alu_result  = 32'd0;
                alu_carry   = carry_in;
                alu_overflow = 1'b0;
            end
        endcase
    end

    // Flag generation
    always_comb begin
        if (update_flags) begin
            flag_n = alu_result[31];
            flag_z = (alu_result == 32'd0);
            flag_c = alu_carry;
            flag_v = alu_overflow;
        end else begin
            flag_n = 1'b0;
            flag_z = 1'b0;
            flag_c = carry_in;
            flag_v = 1'b0;
        end
    end

    assign result = alu_result;

endmodule
