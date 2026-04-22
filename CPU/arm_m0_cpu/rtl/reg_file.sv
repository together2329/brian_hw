//============================================================================
// Module : reg_file
// Description : 16x32-bit Register File for ARM M0-style CPU
//               2 read ports, 1 write port
//               R13=SP (auto-adjusted), R14=LR, R15=PC (reads as PC+4)
//============================================================================

module reg_file (
    input  logic         clk,
    input  logic         rst_n,

    // Read port 1
    input  logic [3:0]   ra1_addr,
    output logic [31:0]  ra1_data,

    // Read port 2
    input  logic [3:0]   ra2_addr,
    output logic [31:0]  ra2_data,

    // Write port
    input  logic         wa3_en,
    input  logic [3:0]   wa3_addr,
    input  logic [31:0]  wa3_data,

    // PC interface (for PC+4 read behavior)
    input  logic [31:0]  current_pc,

    // Direct SP write (for IRQ stack adjust)
    input  logic         sp_write_en,
    input  logic [31:0]  sp_write_data
);

    logic [31:0] regs [16];

    // ---------------------------------------------------------------
    // Write port (synchronous)
    // ---------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 16; i++) begin
                regs[i] <= 32'd0;
            end
            // Initialize SP to default
            regs[13] <= 32'h20004000;
        end else begin
            // Direct SP write has priority (used during IRQ stacking)
            if (sp_write_en) begin
                regs[13] <= sp_write_data;
            end
            // Normal register write
            if (wa3_en && (wa3_addr != 4'd15)) begin
                // Don't write to PC through normal write port
                // PC is managed by fetch_unit
                regs[wa3_addr] <= wa3_data;
            end
        end
    end

    // ---------------------------------------------------------------
    // Read port 1 (combinational)
    // R15 (PC) reads as current_pc + 4 (ARM convention)
    // ---------------------------------------------------------------
    always_comb begin
        if (ra1_addr == 4'd15) begin
            ra1_data = current_pc + 32'd4;
        end else begin
            ra1_data = regs[ra1_addr];
        end
    end

    // ---------------------------------------------------------------
    // Read port 2 (combinational)
    // R15 (PC) reads as current_pc + 4 (ARM convention)
    // ---------------------------------------------------------------
    always_comb begin
        if (ra2_addr == 4'd15) begin
            ra2_data = current_pc + 32'd4;
        end else begin
            ra2_data = regs[ra2_addr];
        end
    end

endmodule
