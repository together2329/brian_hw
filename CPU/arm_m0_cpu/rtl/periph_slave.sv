//============================================================================
// Module : periph_slave
// Description : Simple memory-mapped peripheral register block
//               16 × 32-bit registers, 4KB address space
//               Register 0: ID (read-only, 0xCAFE0001)
//               Registers 1–15: general-purpose read/write
//               For bus address decode testing at architecture level
//============================================================================

module periph_slave (
    input  logic         clk,
    input  logic         rst_n,

    // Bus slave interface
    input  logic [31:0]  addr,
    input  logic [31:0]  wdata,
    output logic [31:0]  rdata,
    input  logic         we,
    input  logic         cs,
    output logic         ack,
    input  logic [1:0]   size
);

    // ===============================================================
    // Register array
    // ===============================================================
    localparam NUM_REGS = 16;
    localparam [31:0] PERIPH_ID = 32'hCAFE0001;

    logic [31:0] regs [0:NUM_REGS-1];

    // ===============================================================
    // Register index from address (word-aligned offset)
    // ===============================================================
    logic [3:0] reg_idx;

    assign reg_idx = addr[5:2];  // 16 regs, 4 bytes each → bits [5:2]

    // ===============================================================
    // Initialize registers
    // ===============================================================
    integer i;

    initial begin
        regs[0]  = PERIPH_ID;  // ID register (read-only)
        for (i = 1; i < NUM_REGS; i = i + 1) begin
            regs[i] = 32'd0;
        end
    end

    // ===============================================================
    // Write logic — register 0 is read-only (ID)
    // ===============================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 1; i < NUM_REGS; i = i + 1) begin
                regs[i] <= 32'd0;
            end
        end else if (cs && we && (reg_idx != 4'd0)) begin
            regs[reg_idx] <= wdata;
        end
    end

    // ===============================================================
    // Read logic — 1-cycle latency (registered output)
    // ===============================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            rdata <= 32'd0;
        end else if (cs && !we) begin
            case (reg_idx)
                4'd0:  rdata <= PERIPH_ID;
                default: rdata <= regs[reg_idx];
            endcase
        end
    end

    // ===============================================================
    // Ack generation — 1 cycle after cs assertion
    // ===============================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            ack <= 1'b0;
        end else begin
            ack <= cs;
        end
    end

endmodule
