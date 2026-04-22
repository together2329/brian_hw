//============================================================================
// Module : alu
// Description : Arithmetic Logic Unit for ARM M0-style CPU
//               Operations: ADD, SUB, MOV, CMP, AND, ORR, NOP, BX
//               Outputs: result[31:0] and NZCV flags
//============================================================================

module alu (
    input  logic [3:0]  alu_op,      // ALU operation select
    input  logic [31:0] operand_a,   // First operand (Rn)
    input  logic [31:0] operand_b,   // Second operand (Rm or immediate)
    output logic [31:0] result,      // ALU result
    output logic        flag_n,      // Negative flag
    output logic        flag_z,      // Zero flag
    output logic        flag_c,      // Carry flag
    output logic        flag_v       // Overflow flag
);

    // ALU operation encoding
    localparam [3:0] ALU_ADD = 4'b0000;
    localparam [3:0] ALU_SUB = 4'b0001;
    localparam [3:0] ALU_MOV = 4'b0010;
    localparam [3:0] ALU_CMP = 4'b0011;
    localparam [3:0] ALU_AND = 4'b0100;
    localparam [3:0] ALU_ORR = 4'b0101;
    localparam [3:0] ALU_NOP = 4'b0110;
    localparam [3:0] ALU_BX  = 4'b0111;

    logic [31:0] add_result;
    logic [31:0] sub_result;
    logic        add_carry;
    logic        add_overflow;
    logic        sub_carry;
    logic        sub_overflow;

    // --- ADD with carry/overflow ---
    assign {add_carry, add_result} = {1'b0, operand_a} + {1'b0, operand_b};
    assign add_overflow = (operand_a[31] == operand_b[31]) && (add_result[31] != operand_a[31]);

    // --- SUB with carry/overflow ---
    // SUB: a - b = a + ~b + 1
    // Carry = no borrow (C=1 when no borrow, ARM convention)
    assign {sub_carry, sub_result} = {1'b0, operand_a} + {1'b0, ~operand_b} + 32'd1;
    assign sub_overflow = (operand_a[31] != operand_b[31]) && (sub_result[31] != operand_a[31]);

    // --- Result mux ---
    always_comb begin
        result = 32'd0;
        flag_n = 1'b0;
        flag_z = 1'b0;
        flag_c = 1'b0;
        flag_v = 1'b0;

        case (alu_op)
            ALU_ADD: begin
                result = add_result;
                flag_n = add_result[31];
                flag_z = (add_result == 32'd0);
                flag_c = add_carry;
                flag_v = add_overflow;
            end

            ALU_SUB: begin
                result = sub_result;
                flag_n = sub_result[31];
                flag_z = (sub_result == 32'd0);
                flag_c = sub_carry;
                flag_v = sub_overflow;
            end

            ALU_MOV: begin
                result = operand_a;  // MOV: operand_a has the value (immediate or register)
                flag_n = operand_a[31];
                flag_z = (operand_a == 32'd0);
                flag_c = 1'b0;  // MOV does not affect C/V
                flag_v = 1'b0;
            end

            ALU_CMP: begin
                result = 32'd0;  // CMP discards result
                flag_n = sub_result[31];
                flag_z = (sub_result == 32'd0);
                flag_c = sub_carry;
                flag_v = sub_overflow;
            end

            ALU_AND: begin
                result = operand_a & operand_b;
                flag_n = result[31];
                flag_z = (result == 32'd0);
                flag_c = 1'b0;
                flag_v = 1'b0;
            end

            ALU_ORR: begin
                result = operand_a | operand_b;
                flag_n = result[31];
                flag_z = (result == 32'd0);
                flag_c = 1'b0;
                flag_v = 1'b0;
            end

            ALU_NOP: begin
                result = 32'd0;
                flag_n = 1'b0;
                flag_z = 1'b0;
                flag_c = 1'b0;
                flag_v = 1'b0;
            end

            ALU_BX: begin
                result = operand_b;  // Branch target
                flag_n = 1'b0;
                flag_z = 1'b0;
                flag_c = 1'b0;
                flag_v = 1'b0;
            end

            default: begin
                result = 32'd0;
                flag_n = 1'b0;
                flag_z = 1'b0;
                flag_c = 1'b0;
                flag_v = 1'b0;
            end
        endcase
    end

endmodule
