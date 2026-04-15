//=============================================================================
// ARM Barrel Shifter
// Supports: LSL, LSR, ASR, ROR, RRX
// Used for data-processing operand2 shifted immediates and register shifts
//=============================================================================

module arm_barrel_shifter (
    input  logic [31:0] operand,      // Input value to shift
    input  logic [11:0] shift_amount, // Shift amount (5-bit for register, immediate encoded)
    input  logic [1:0]  shift_type,   // 00=LSL, 01=LSR, 10=ASR, 11=ROR
    input  logic        shift_carry_in, // Carry flag input
    input  logic        is_imm,       // 1 = immediate shift (from instruction decode)

    output logic [31:0] result,       // Shifted result
    output logic        carry_out     // Carry output from shifter
);

    logic [4:0]  actual_shift;
    logic [31:0] shifted;
    logic        shifter_carry;

    // Determine actual shift amount
    // For immediate: rotate by 2*rotate_imm from shift_amount[4:0]
    // For register: shift_amount[4:0]
    always_comb begin
        if (is_imm) begin
            // Rotated immediate: rotate_right by 2*rotate_imm
            actual_shift = {shift_amount[3:0], 1'b0};
        end else begin
            actual_shift = shift_amount[4:0];
        end
    end

    // Barrel shift operation
    always_comb begin
        shifted = 32'd0;
        shifter_carry = shift_carry_in;

        case (shift_type)
            2'b00: begin // LSL
                case (actual_shift)
                    5'd0:    begin shifted = operand;              shifter_carry = shift_carry_in; end
                    5'd1:    begin shifted = operand << 1;         shifter_carry = operand[31];    end
                    5'd2:    begin shifted = operand << 2;         shifter_carry = operand[30];    end
                    5'd3:    begin shifted = operand << 3;         shifter_carry = operand[29];    end
                    5'd4:    begin shifted = operand << 4;         shifter_carry = operand[28];    end
                    5'd5:    begin shifted = operand << 5;         shifter_carry = operand[27];    end
                    5'd6:    begin shifted = operand << 6;         shifter_carry = operand[26];    end
                    5'd7:    begin shifted = operand << 7;         shifter_carry = operand[25];    end
                    5'd8:    begin shifted = operand << 8;         shifter_carry = operand[24];    end
                    5'd16:   begin shifted = operand << 16;        shifter_carry = operand[16];    end
                    5'd24:   begin shifted = operand << 24;        shifter_carry = operand[8];     end
                    default: begin shifted = operand << actual_shift; shifter_carry = (actual_shift > 0) ? operand[32 - actual_shift] : shift_carry_in; end
                endcase
                if (actual_shift >= 5'd32) begin
                    shifted = 32'd0;
                    shifter_carry = (actual_shift == 5'd32) ? operand[0] : 1'b0;
                end
            end

            2'b01: begin // LSR
                if (actual_shift == 5'd0 && !is_imm) begin
                    // LSR #0 means LSR #32
                    shifted = 32'd0;
                    shifter_carry = operand[31];
                end else begin
                    case (actual_shift)
                        5'd1:    begin shifted = operand >> 1;         shifter_carry = operand[0];     end
                        5'd2:    begin shifted = operand >> 2;         shifter_carry = operand[1];     end
                        5'd8:    begin shifted = operand >> 8;         shifter_carry = operand[7];     end
                        5'd16:   begin shifted = operand >> 16;        shifter_carry = operand[15];    end
                        5'd24:   begin shifted = operand >> 24;        shifter_carry = operand[23];    end
                        default: begin shifted = operand >> actual_shift; shifter_carry = operand[actual_shift - 1]; end
                    endcase
                    if (actual_shift >= 5'd32) begin
                        shifted = 32'd0;
                        shifter_carry = (actual_shift == 5'd32) ? operand[31] : 1'b0;
                    end
                end
            end

            2'b10: begin // ASR
                if (actual_shift == 5'd0 && !is_imm) begin
                    // ASR #0 means ASR #32
                    shifted = {32{operand[31]}};
                    shifter_carry = operand[31];
                end else begin
                    case (actual_shift)
                        5'd1:  begin shifted = $signed(operand) >>> 1;  shifter_carry = operand[0]; end
                        5'd8:  begin shifted = $signed(operand) >>> 8;  shifter_carry = operand[7]; end
                        5'd16: begin shifted = $signed(operand) >>> 16; shifter_carry = operand[15]; end
                        default: begin shifted = $signed(operand) >>> actual_shift; shifter_carry = operand[actual_shift - 1]; end
                    endcase
                    if (actual_shift >= 5'd32) begin
                        shifted = {32{operand[31]}};
                        shifter_carry = operand[31];
                    end
                end
            end

            2'b11: begin // ROR
                if (actual_shift == 5'd0 && !is_imm) begin
                    // RRX (rotate right extended through carry)
                    shifted = {shift_carry_in, operand[31:1]};
                    shifter_carry = operand[0];
                end else begin
                    // ROR by actual_shift mod 32
                    logic [4:0] rot;
                    rot = actual_shift[4:0];
                    case (rot)
                        5'd0:  begin shifted = operand;           shifter_carry = operand[31]; end
                        5'd1:  begin shifted = {operand[0], operand[31:1]};   shifter_carry = operand[0];  end
                        5'd8:  begin shifted = {operand[7:0], operand[31:8]}; shifter_carry = operand[7];  end
                        5'd16: begin shifted = {operand[15:0], operand[31:16]}; shifter_carry = operand[15]; end
                        default: begin shifted = (operand >> rot) | (operand << (32 - rot)); shifter_carry = operand[rot - 1]; end
                    endcase
                end
            end
        endcase
    end

    assign result    = shifted;
    assign carry_out = shifter_carry;

endmodule
