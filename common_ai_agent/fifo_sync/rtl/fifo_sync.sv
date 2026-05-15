// fifo_sync.sv — SSOT-backed synchronous FIFO top integration.
module fifo_sync #(
    parameter integer DATA_WIDTH = 32,
    parameter integer DEPTH = 16,
    parameter integer ALMOST_FULL_THRESHOLD = 15,
    parameter integer ALMOST_EMPTY_THRESHOLD = 1,
    parameter integer USE_OUTPUT_REGISTER = 0,
    parameter integer USE_APB = 1,
    parameter integer USE_ECC = 0,
    parameter integer CLOCK_FREQ_MHZ = 50,
    parameter integer ADDR_WIDTH = $clog2(DEPTH),
    parameter integer COUNT_WIDTH = $clog2(DEPTH+1)
) (
    input  logic                   PCLK,
    input  logic                   PRESETn,
    input  logic                   wr_en_i,
    input  logic [DATA_WIDTH-1:0]  wr_data_i,
    output logic                   full_o,
    output logic                   almost_full_o,
    input  logic                   rd_en_i,
    output logic [DATA_WIDTH-1:0]  rd_data_o,
    output logic                   empty_o,
    output logic                   almost_empty_o,
    output logic [COUNT_WIDTH-1:0] count_o,
    input  logic                   flush_i,
    input  logic [3:0]             paddr,
    input  logic                   psel,
    input  logic                   penable,
    input  logic                   pwrite,
    input  logic [31:0]            pwdata,
    output logic [31:0]            prdata,
    output logic                   pready,
    output logic                   pslverr
);

    logic                   push_accepted;
    logic                   pop_accepted;
    logic [ADDR_WIDTH-1:0]  wr_ptr;
    logic [ADDR_WIDTH-1:0]  rd_ptr;
    logic [COUNT_WIDTH-1:0] count;
    logic [DATA_WIDTH-1:0]  mem_rd_data;
    logic [7:0]             cfg_almost_full_thresh;
    logic [7:0]             cfg_almost_empty_thresh;
    logic                   csr_flush_pulse;
    logic                   flush_request;

    // Direct flush and CSR FIFO_CONTROL.flush share the SSOT flush behavior.
    assign flush_request = flush_i || csr_flush_pulse;

    fifo_sync_ptrs #(
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .COUNT_WIDTH(COUNT_WIDTH)
    ) u_ptrs (
        .clk_i(PCLK),
        .rst_ni(PRESETn),
        .wr_en_i(wr_en_i),
        .rd_en_i(rd_en_i),
        .flush_i(flush_request),
        .full_o(full_o),
        .empty_o(empty_o),
        .push_accepted_o(push_accepted),
        .pop_accepted_o(pop_accepted),
        .wr_ptr_o(wr_ptr),
        .rd_ptr_o(rd_ptr),
        .count_o(count)
    );

    fifo_sync_mem #(
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .USE_ECC(USE_ECC)
    ) u_mem (
        .clk_i(PCLK),
        .rst_ni(PRESETn),
        .wr_en_i(push_accepted),
        .wr_addr_i(wr_ptr),
        .wr_data_i(wr_data_i),
        .rd_addr_i(rd_ptr),
        .rd_data_o(mem_rd_data)
    );

    fifo_sync_flags #(
        .DEPTH(DEPTH),
        .ALMOST_FULL_THRESHOLD(ALMOST_FULL_THRESHOLD),
        .ALMOST_EMPTY_THRESHOLD(ALMOST_EMPTY_THRESHOLD),
        .COUNT_WIDTH(COUNT_WIDTH)
    ) u_flags (
        .count_i(count),
        .almost_full_thresh_i(cfg_almost_full_thresh),
        .almost_empty_thresh_i(cfg_almost_empty_thresh),
        .full_o(full_o),
        .empty_o(empty_o),
        .almost_full_o(almost_full_o),
        .almost_empty_o(almost_empty_o),
        .count_o(count_o)
    );

    fifo_sync_output_reg #(
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH(DEPTH),
        .ALMOST_FULL_THRESHOLD(ALMOST_FULL_THRESHOLD),
        .ALMOST_EMPTY_THRESHOLD(ALMOST_EMPTY_THRESHOLD),
        .USE_OUTPUT_REGISTER(USE_OUTPUT_REGISTER),
        .USE_APB(USE_APB),
        .USE_ECC(USE_ECC),
        .CLOCK_FREQ_MHZ(CLOCK_FREQ_MHZ)
    ) u_output_reg (
        .clk_i(PCLK),
        .rst_ni(PRESETn),
        .load_i(pop_accepted),
        .din_i(mem_rd_data),
        .dout_o(rd_data_o)
    );

    fifo_sync_regs #(
        .COUNT_WIDTH(COUNT_WIDTH),
        .ALMOST_FULL_THRESHOLD(ALMOST_FULL_THRESHOLD),
        .ALMOST_EMPTY_THRESHOLD(ALMOST_EMPTY_THRESHOLD),
        .USE_APB(USE_APB)
    ) u_regs (
        .clk_i(PCLK),
        .rst_ni(PRESETn),
        .paddr(paddr),
        .psel(psel),
        .penable(penable),
        .pwrite(pwrite),
        .pwdata(pwdata),
        .empty_i(empty_o),
        .full_i(full_o),
        .almost_empty_i(almost_empty_o),
        .almost_full_i(almost_full_o),
        .count_i(count),
        .prdata(prdata),
        .pready(pready),
        .pslverr(pslverr),
        .almost_full_thresh_o(cfg_almost_full_thresh),
        .almost_empty_thresh_o(cfg_almost_empty_thresh),
        .flush_pulse_o(csr_flush_pulse)
    );

endmodule
