//=============================================================================
// ARM Data Memory
// Simple data memory with 32-bit read/write, byte-enable support
// Supports byte (8-bit), halfword (16-bit), and word (32-bit) access
//=============================================================================

module arm_dmem (
    input  logic        clk,
    input  logic        rst_n,

    // Memory interface
    input  logic        mem_req,      // Request valid
    input  logic        mem_we,       // Write enable
    input  logic        mem_byte,     // Byte access
    input  logic [31:0] addr,         // Address
    input  logic [31:0] wdata,        // Write data
    output logic [31:0] rdata,        // Read data

    // Ready signal
    output logic        mem_ready
);

    // 4KB data memory (1024 x 32-bit words)
    logic [31:0] mem [0:1023];

    // Initialize data memory to zero
    integer i;
    initial begin
        for (i = 0; i < 1024; i++) begin
            mem[i] = 32'd0;
        end
    end

    // Memory ready — combinational (single-cycle access)
    assign mem_ready = mem_req;

    // Write
    always_ff @(posedge clk) begin
        if (mem_req && mem_we) begin
            if (mem_byte) begin
                // Byte write — lane select from addr[1:0]
                case (addr[1:0])
                    2'b00: mem[addr[11:2]][7:0]   <= wdata[7:0];
                    2'b01: mem[addr[11:2]][15:8]  <= wdata[7:0];
                    2'b10: mem[addr[11:2]][23:16] <= wdata[7:0];
                    2'b11: mem[addr[11:2]][31:24] <= wdata[7:0];
                endcase
            end else begin
                // Word write
                mem[addr[11:2]] <= wdata;
            end
        end
    end

    // Read
    always_ff @(posedge clk) begin
        if (mem_req && !mem_we) begin
            if (mem_byte) begin
                // Byte read — zero-extend
                case (addr[1:0])
                    2'b00: rdata <= {24'd0, mem[addr[11:2]][7:0]};
                    2'b01: rdata <= {24'd0, mem[addr[11:2]][15:8]};
                    2'b10: rdata <= {24'd0, mem[addr[11:2]][23:16]};
                    2'b11: rdata <= {24'd0, mem[addr[11:2]][31:24]};
                endcase
            end else begin
                // Word read
                rdata <= mem[addr[11:2]];
            end
        end
    end

endmodule
