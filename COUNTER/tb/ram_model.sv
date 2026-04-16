`timescale 1ns/1ps

module ram_model #(
    parameter int ADDR_WIDTH = 32,
    parameter int DATA_WIDTH = 512,
    parameter int DEPTH      = 1024
) (
    input  logic                      clk,
    input  logic                      rst_n,

    // Simple request/ready interface
    input  logic                      req,
    input  logic [ADDR_WIDTH-1:0]     addr,
    input  logic                      write,
    input  logic [DATA_WIDTH-1:0]     wdata,
    output logic [DATA_WIDTH-1:0]     rdata,
    output logic                      ready
);

    // Memory array is word-addressed; low bits of addr select word index
    localparam int ADDR_LSB    = $clog2(DATA_WIDTH / 8);
    localparam int INDEX_WIDTH = $clog2(DEPTH);

    logic [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // Extract word index from byte address
    logic [INDEX_WIDTH-1:0] word_idx;
    assign word_idx = addr[ADDR_LSB +: INDEX_WIDTH];

    // Suppress Verilator UNUSEDSIGNAL for upper addr bits (intentionally
    // unused — the RAM only indexes ADDR_LSB..ADDR_LSB+INDEX_WIDTH-1).
    logic _unused_addr;
    assign _unused_addr = ^(addr);

    // Always ready (single-cycle, no wait states)
    assign ready = req;

    // Combinational read — immediately reflects memory contents
    assign rdata = mem[word_idx];

    // Registered write — committed on clock edge when requested
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Memory retains contents across reset (no zeroing)
        end else begin
            if (req && write) begin
                mem[word_idx] <= wdata;
            end
        end
    end

endmodule
