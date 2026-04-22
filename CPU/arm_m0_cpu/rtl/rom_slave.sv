//============================================================================
// Module : rom_slave
// Description : Read-only instruction memory (ROM) with bus slave interface
//               16-bit wide (Thumb instructions), parameterized depth
//               1-cycle read latency, loadable via $readmemh
//               Address: byte-addressed input, internally indexed by addr[N:1]
//============================================================================

module rom_slave #(
    parameter ADDR_WIDTH = 15,  // 15 bits → 32768 half-words = 64KB
    parameter DATA_WIDTH = 16   // 16-bit Thumb instruction
)(
    input  logic                   clk,
    input  logic                   rst_n,

    // Bus slave interface
    input  logic [31:0]            addr,
    input  logic [DATA_WIDTH-1:0]  wdata,    // Unused (ROM is read-only)
    output logic [DATA_WIDTH-1:0]  rdata,
    input  logic                   we,       // Ignored (ROM is read-only)
    input  logic                   cs,
    output logic                   ack,
    input  logic [1:0]             size      // Unused for ROM
);

    // ===============================================================
    // Memory array — loaded via $readmemh from external file
    // ===============================================================
    logic [DATA_WIDTH-1:0] mem [0:(1 << ADDR_WIDTH) - 1];

    initial begin
        : rom_init
        integer i;
        for (i = 0; i < (1 << ADDR_WIDTH); i = i + 1) begin
            mem[i] = {DATA_WIDTH{1'b0}};
        end
    end

    // ===============================================================
    // Half-word address index from byte address
    // ===============================================================
    logic [ADDR_WIDTH-1:0] hw_addr;

    assign hw_addr = addr[ADDR_WIDTH:1];  // Byte addr → half-word index

    // ===============================================================
    // Read logic — 1-cycle latency (registered output)
    // ===============================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            rdata <= {DATA_WIDTH{1'b0}};
        end else if (cs) begin
            rdata <= mem[hw_addr];
        end
    end

    // ===============================================================
    // Ack generation — 1 cycle after cs assertion
    // ===============================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            ack <= 1'b0;
        end else begin
            ack <= cs;  // Ack follows cs with 1-cycle delay
        end
    end

endmodule
