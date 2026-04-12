//=============================================================================
// ARM Condition Code Checker
// Evaluates the 4-bit condition field against CPSR flags
// Condition codes: EQ,NE,CS/HS,CC/LO,MI,PL,VS,VC,HI,LS,GE,LT,GT,LE,AL,NV
//=============================================================================

module arm_condition_check (
    input  logic [3:0] cond,      // Condition field from instruction [31:28]
    input  logic       flag_n,    // Negative flag from CPSR
    input  logic       flag_z,    // Zero flag from CPSR
    input  logic       flag_c,    // Carry flag from CPSR
    input  logic       flag_v,    // Overflow flag from CPSR

    output logic       cond_pass  // 1 = condition satisfied, execute instruction
);

    always_comb begin
        case (cond)
            4'b0000: cond_pass = flag_z;                          // EQ: Z set
            4'b0001: cond_pass = ~flag_z;                         // NE: Z clear
            4'b0010: cond_pass = flag_c;                          // CS/HS: C set
            4'b0011: cond_pass = ~flag_c;                         // CC/LO: C clear
            4'b0100: cond_pass = flag_n;                          // MI: N set
            4'b0101: cond_pass = ~flag_n;                         // PL: N clear
            4'b0110: cond_pass = flag_v;                          // VS: V set
            4'b0111: cond_pass = ~flag_v;                         // VC: V clear
            4'b1000: cond_pass = flag_c & ~flag_z;                // HI: C set, Z clear
            4'b1001: cond_pass = ~flag_c | flag_z;                // LS: C clear or Z set
            4'b1010: cond_pass = (flag_n == flag_v);              // GE: N == V
            4'b1011: cond_pass = (flag_n != flag_v);              // LT: N != V
            4'b1100: cond_pass = ~flag_z & (flag_n == flag_v);    // GT: Z clear, N == V
            4'b1101: cond_pass = flag_z | (flag_n != flag_v);     // LE: Z set or N != V
            4'b1110: cond_pass = 1'b1;                            // AL: always
            4'b1111: cond_pass = 1'b0;                            // NV: never (reserved)
            default: cond_pass = 1'b1;
        endcase
    end

endmodule
