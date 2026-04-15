`timescale 1ns/1ps

module dma_cocotb_top #(
    parameter int ADDR_WIDTH = 32,
    parameter int DATA_WIDTH = 512,
    parameter int LEN_WIDTH  = 16,
    parameter int DEPTH      = 1024
) (
    input  logic                      clk,
    input  logic                      rst_n,

    // DMA control interface
    input  logic                      start,
    input  logic [ADDR_WIDTH-1:0]     src_addr,
    input  logic [ADDR_WIDTH-1:0]     dst_addr,
    input  logic [LEN_WIDTH-1:0]      length,
    output logic                      busy,
    output logic                      done
);

    // Internal memory bus
    logic                      mem_req;
    logic [ADDR_WIDTH-1:0]     mem_addr;
    logic                      mem_write;
    logic [DATA_WIDTH-1:0]     mem_wdata;
    logic [DATA_WIDTH-1:0]     mem_rdata;
    logic                      mem_ready;

    // Instantiate DMA
    dma #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .LEN_WIDTH (LEN_WIDTH)
    ) u_dma (
        .clk      (clk),
        .rst_n    (rst_n),
        .start    (start),
        .src_addr (src_addr),
        .dst_addr (dst_addr),
        .length   (length),
        .busy     (busy),
        .done     (done),
        .mem_req  (mem_req),
        .mem_addr (mem_addr),
        .mem_write(mem_write),
        .mem_wdata(mem_wdata),
        .mem_rdata(mem_rdata),
        .mem_ready(mem_ready)
    );

    // Instantiate RAM model
    ram_model #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH     (DEPTH)
    ) u_ram (
        .clk  (clk),
        .rst_n(rst_n),
        .req  (mem_req),
        .addr (mem_addr),
        .write(mem_write),
        .wdata(mem_wdata),
        .rdata(mem_rdata),
        .ready(mem_ready)
    );

endmodule
