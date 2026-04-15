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
    localparam int ADDR_LSB = $clog2(DATA_WIDTH/8);
    localparam int INDEX_WIDTH = $clog2(DEPTH);

    logic [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    logic                  busy_q, busy_n;
    logic [ADDR_WIDTH-1:0] addr_q, addr_n;
    logic                  write_q, write_n;
    logic [DATA_WIDTH-1:0] wdata_q, wdata_n;

    assign ready = !busy_q && req;

    // Output read data directly from memory when ready
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy_q  <= 1'b0;
            addr_q  <= '0;
            write_q <= 1'b0;
            wdata_q <= '0;
            rdata   <= '0;
        end else begin
            busy_q  <= busy_n;
            addr_q  <= addr_n;
            write_q <= write_n;
            wdata_q <= wdata_n;

            if (ready && !write) begin
                rdata <= mem[addr[ADDR_LSB +: INDEX_WIDTH]];
            end
            if (ready && write) begin
                mem[addr[ADDR_LSB +: INDEX_WIDTH]] <= wdata;
            end
        end
    end

    // Simple 1-cycle handshake model: ready asserted when not busy and req high
    always_comb begin
        busy_n  = busy_q;
        addr_n  = addr_q;
        write_n = write_q;
        wdata_n = wdata_q;

        if (!busy_q && req) begin
            // accept transaction this cycle
            busy_n  = 1'b0; // still combinationally one-cycle, no wait states
            addr_n  = addr;
            write_n = write;
            wdata_n = wdata;
        end
    end

endmodule
