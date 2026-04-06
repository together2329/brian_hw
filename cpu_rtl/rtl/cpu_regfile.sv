// ============================================================================
// Module: cpu_regfile
// Description: 32x32-bit Register File - 2 read ports, 1 write port
//              x0 hardwired to zero
// ============================================================================

module cpu_regfile #(
    parameter DATA_WIDTH = 32,
    parameter REG_ADDR_WIDTH = 5,
    parameter NUM_REGS = 32
)(
    input  logic                          clk,
    input  logic                          rst_n,

    // Read port A
    input  logic [REG_ADDR_WIDTH-1:0]     rs1_addr_i,
    output logic [DATA_WIDTH-1:0]         rs1_data_o,

    // Read port B
    input  logic [REG_ADDR_WIDTH-1:0]     rs2_addr_i,
    output logic [DATA_WIDTH-1:0]         rs2_data_o,

    // Write port
    input  logic                          reg_write_i,
    input  logic [REG_ADDR_WIDTH-1:0]     rd_addr_i,
    input  logic [DATA_WIDTH-1:0]         rd_data_i
);

    // Register array
    logic [DATA_WIDTH-1:0] registers [0:NUM_REGS-1];

    // =========================================================================
    // Read ports (combinational)
    // =========================================================================
    assign rs1_data_o = (rs1_addr_i == 5'b00000) ? 32'b0 : registers[rs1_addr_i];
    assign rs2_data_o = (rs2_addr_i == 5'b00000) ? 32'b0 : registers[rs2_addr_i];

    // =========================================================================
    // Write port (sequential) - x0 is always 0
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (integer i = 0; i < NUM_REGS; i++) begin
                registers[i] <= 32'b0;
            end
        end else if (reg_write_i && (rd_addr_i != 5'b00000)) begin
            registers[rd_addr_i] <= rd_data_i;
        end
    end

endmodule
