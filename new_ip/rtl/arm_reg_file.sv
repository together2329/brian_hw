//=============================================================================
// ARM Register File
// 32-bit x 16 registers (R0-R15) with dual read ports and single write port
// R13 = SP (Stack Pointer), R14 = LR (Link Register), R15 = PC (Program Counter)
//=============================================================================

module arm_reg_file (
    input  logic        clk,
    input  logic        rst_n,

    // Read port A
    input  logic [3:0]  raddr_a,
    output logic [31:0] rdata_a,

    // Read port B
    input  logic [3:0]  raddr_b,
    output logic [31:0] rdata_b,

    // Write port
    input  logic        we,          // Write enable
    input  logic [3:0]  waddr,
    input  logic [31:0] wdata,

    // PC direct access
    output logic [31:0] pc_out       // R15 = PC (current instruction address)
);

    logic [31:0] registers [0:15];

    // Synthesizable synchronous read
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < 16; i++) begin
                registers[i] <= 32'd0;
            end
            registers[13] <= 32'h0000_1000;  // SP init
        end else begin
            // Write (R15 is handled separately for PC)
            if (we && waddr != 4'd15) begin
                registers[waddr] <= wdata;
            end
        end
    end

    // Asynchronous read — combinational
    assign rdata_a = (raddr_a == 4'd15) ? pc_out : registers[raddr_a];
    assign rdata_b = (raddr_b == 4'd15) ? pc_out : registers[raddr_b];

    // PC is R15 — exposed directly
    assign pc_out = registers[15];

endmodule
