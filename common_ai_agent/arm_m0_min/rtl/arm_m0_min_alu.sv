module arm_m0_min_alu #(
    parameter integer XLEN = 32
) (
    input  logic [3:0]       alu_op,
    input  logic [XLEN-1:0]  op_a,
    input  logic [XLEN-1:0]  op_b,
    output logic [XLEN-1:0]  alu_res,
    output logic             cmp_eq,
    output logic             cmp_neg
);

    localparam [3:0] ALU_ADD = 4'd0,
                     ALU_SUB = 4'd1,
                     ALU_AND = 4'd2,
                     ALU_ORR = 4'd3,
                     ALU_EOR = 4'd4,
                     ALU_MOV = 4'd5,
                     ALU_LSL = 4'd6,
                     ALU_LSR = 4'd7,
                     ALU_ASR = 4'd8;

    logic [4:0] shamt;
    logic [XLEN-1:0] asr_res_u;
    logic [XLEN-1:0] sign_fill;
    assign shamt = op_b[4:0];
    assign sign_fill = {XLEN{op_a[XLEN-1]}};

    always @(*) begin
        if (shamt == 5'd0) asr_res_u = op_a;
        else asr_res_u = (op_a >> shamt) | (sign_fill << (6'd32 - {1'b0, shamt}));
    end

    always @(*) begin
        alu_res = {XLEN{1'b0}};
        case (alu_op)
            ALU_ADD: alu_res = op_a + op_b;
            ALU_SUB: alu_res = op_a - op_b;
            ALU_AND: alu_res = op_a & op_b;
            ALU_ORR: alu_res = op_a | op_b;
            ALU_EOR: alu_res = op_a ^ op_b;
            ALU_MOV: alu_res = op_b;
            ALU_LSL: alu_res = op_a << shamt;
            ALU_LSR: alu_res = op_a >> shamt;
            ALU_ASR: alu_res = asr_res_s;
            default: alu_res = {XLEN{1'b0}};
        endcase
    end

    assign cmp_eq  = (op_a == op_b);
    assign cmp_neg = (op_a < op_b);

endmodule
