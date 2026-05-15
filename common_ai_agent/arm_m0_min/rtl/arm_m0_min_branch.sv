module arm_m0_min_branch #(
    parameter integer XLEN = 32
) (
    input  logic [XLEN-1:0] pc_in,
    input  logic [XLEN-1:0] imm_ext,
    input  logic            is_b,
    input  logic            is_beq,
    input  logic            is_bne,
    input  logic            z_flag,
    output logic            branch_taken,
    output logic [XLEN-1:0] branch_target
);

    always @(*) begin
        branch_taken  = 1'b0;
        branch_target = pc_in + imm_ext;
        if (is_b) begin
            branch_taken = 1'b1;
        end else if (is_beq) begin
            if (z_flag) branch_taken = 1'b1;
        end else if (is_bne) begin
            if (!z_flag) branch_taken = 1'b1;
        end
    end

endmodule
