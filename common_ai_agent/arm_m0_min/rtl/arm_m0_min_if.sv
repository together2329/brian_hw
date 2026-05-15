module arm_m0_min_if #(
    parameter integer XLEN = 32,
    parameter integer RESET_PC = 0
) (
    input  logic             clk,
    input  logic             rst,
    input  logic             fault_halt,
    input  logic             hold_pc,
    input  logic             branch_taken,
    input  logic [XLEN-1:0]  branch_target,
    output logic [XLEN-1:0]  pc_out,
    output logic             if_valid,
    output logic [31:0]      if_instr,
    output logic [XLEN-1:0]  i_haddr,
    output logic [1:0]       i_htrans,
    output logic             i_hwrite,
    output logic [2:0]       i_hsize,
    output logic [2:0]       i_hburst,
    output logic [3:0]       i_hprot,
    output logic             i_hmastlock,
    input  logic             i_hready,
    input  logic [31:0]      i_hrdata,
    input  logic             i_hresp
);

    localparam [1:0] HTRANS_IDLE   = 2'b00,
                     HTRANS_NONSEQ = 2'b10;

    logic [XLEN-1:0] pc_reg;
    logic [XLEN-1:0] reset_pc_w;

    assign reset_pc_w = RESET_PC;

    always @(posedge clk) begin
        if (rst) begin
            pc_reg   <= reset_pc_w;
            if_instr <= 32'h00000000;
            if_valid <= 1'b0;
        end else if (!fault_halt) begin
            if (i_hready) begin
                if_instr <= i_hrdata;
                if_valid <= 1'b1;
                if (branch_taken) begin
                    pc_reg <= branch_target;
                end else if (!hold_pc) begin
                    pc_reg <= pc_reg + 32'd2;
                end
            end
        end
    end

    assign pc_out      = pc_reg;
    assign i_haddr     = pc_reg;
    assign i_htrans    = (fault_halt) ? HTRANS_IDLE : HTRANS_NONSEQ;
    assign i_hwrite    = 1'b0;
    assign i_hsize     = 3'b001;
    assign i_hburst    = 3'b000;
    assign i_hprot     = 4'b0011;
    assign i_hmastlock = 1'b0;

endmodule
