module if_stage #(
    parameter integer XLEN = 32
) (
    input  logic            clk,
    input  logic            rst_n,
    output logic            if_id_valid,
    input  logic            if_id_ready,
    output logic [XLEN-1:0] if_id_pc,
    output logic [15:0]     if_id_instr
);
    logic [XLEN-1:0] pc_q;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_q <= {XLEN{1'b0}};
            if_id_valid <= 1'b0;
            if_id_instr <= 16'h0000;
        end else begin
            if_id_valid <= 1'b1;
            if (if_id_ready) begin
                pc_q <= pc_q + {{(XLEN-2){1'b0}},2'b10};
                if_id_instr <= if_id_instr + 16'h0001;
            end
        end
    end
    assign if_id_pc = pc_q;
endmodule
