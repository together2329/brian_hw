// dma_real_engine.sv — hclk domain top connecting arbiter, channels, AHB master, CG cells
// v2: generate-based N_CHANNELS, per-channel clock gating, shared AHB master mux
module dma_real_engine #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer N_CHANNELS = 4,
    parameter integer BURST_MAX  = 16,
    parameter integer FIFO_DEPTH = 16
) (
    input  logic                  hclk,
    input  logic                  hresetn,
    input  logic                  dma_en,
    input  logic [N_CHANNELS-1:0] ch_en,
    input  logic [N_CHANNELS-1:0] ch_start,
    input  logic [ADDR_WIDTH-1:0] cfg_src_addr_0, cfg_src_addr_1, cfg_src_addr_2, cfg_src_addr_3,
    input  logic [ADDR_WIDTH-1:0] cfg_dst_addr_0, cfg_dst_addr_1, cfg_dst_addr_2, cfg_dst_addr_3,
    input  logic [15:0]           cfg_len_0, cfg_len_1, cfg_len_2, cfg_len_3,
    input  logic [ADDR_WIDTH-1:0] cfg_stride_0, cfg_stride_1, cfg_stride_2, cfg_stride_3,
    input  logic [15:0]           cfg_timeout,
    output logic [N_CHANNELS-1:0] ch_busy,
    output logic [N_CHANNELS-1:0] ch_done_pulse,
    output logic [N_CHANNELS-1:0] ch_error_pulse,
    output logic [7:0]            ch_err_code,
    output logic [2:0]            arb_grant,
    output logic [31:0]           perf_words_0, perf_words_1, perf_words_2, perf_words_3,
    output logic [31:0]           perf_cycles_0, perf_cycles_1, perf_cycles_2, perf_cycles_3,
    output logic [ADDR_WIDTH-1:0] haddr,
    output logic                  hwrite,
    output logic [1:0]            htrans,
    output logic [2:0]            hsize,
    output logic [2:0]            hburst,
    output logic [3:0]            hprot,
    output logic [3:0]            hmaster,
    output logic                  hmastlock,
    output logic [DATA_WIDTH-1:0] hwdata,
    input  logic [DATA_WIDTH-1:0] hrdata,
    input  logic                  hready,
    input  logic [1:0]            hresp,
    output logic                  hbusreq,
    input  logic                  hgrant
);

    logic [N_CHANNELS-1:0] ch_request, ch_grant_vec;
    logic [N_CHANNELS-1:0] ahb_start_vec, ahb_write_vec;
    logic [ADDR_WIDTH-1:0] ahb_addr_0, ahb_addr_1, ahb_addr_2, ahb_addr_3;
    logic [15:0]           ahb_len_0, ahb_len_1, ahb_len_2, ahb_len_3;
    logic                  ahb_master_done, ahb_master_error;
    logic [2:0]            ahb_master_err_code;
    logic [DATA_WIDTH-1:0] ahb_master_rdata;

    assign ahb_master_rdata = hrdata;
    wire ahb_bus_busy = (htrans != 2'b00);

    logic [2:0] ch_err_code_0, ch_err_code_1, ch_err_code_2, ch_err_code_3;
    assign ch_err_code = {ch_err_code_3[1:0], ch_err_code_2[1:0], ch_err_code_1[1:0], ch_err_code_0[1:0]};

    logic [DATA_WIDTH-1:0] fifo_wdata_0, fifo_wdata_1, fifo_wdata_2, fifo_wdata_3;
    logic fifo_wen_0, fifo_wen_1, fifo_wen_2, fifo_wen_3;
    logic fifo_ren_0, fifo_ren_1, fifo_ren_2, fifo_ren_3;
    logic [DATA_WIDTH-1:0] fifo_rdata_0, fifo_rdata_1, fifo_rdata_2, fifo_rdata_3;
    logic fifo_empty_0, fifo_empty_1, fifo_empty_2, fifo_empty_3;
    logic fifo_full_0, fifo_full_1, fifo_full_2, fifo_full_3;

    // AHB mux
    wire [ADDR_WIDTH-1:0] mux_ahb_addr  = ch_grant_vec[0] ? ahb_addr_0 : ch_grant_vec[1] ? ahb_addr_1 : ch_grant_vec[2] ? ahb_addr_2 : ahb_addr_3;
    wire [15:0]           mux_ahb_len   = ch_grant_vec[0] ? ahb_len_0  : ch_grant_vec[1] ? ahb_len_1  : ch_grant_vec[2] ? ahb_len_2  : ahb_len_3;
    wire                  mux_ahb_write = ch_grant_vec[0] ? ahb_write_vec[0] : ch_grant_vec[1] ? ahb_write_vec[1] : ch_grant_vec[2] ? ahb_write_vec[2] : ahb_write_vec[3];
    wire                  mux_ahb_start = ch_grant_vec[0] ? ahb_start_vec[0] : ch_grant_vec[1] ? ahb_start_vec[1] : ch_grant_vec[2] ? ahb_start_vec[2] : ahb_start_vec[3];
    wire [DATA_WIDTH-1:0] mux_ahb_wdata = ch_grant_vec[0] ? fifo_rdata_0 : ch_grant_vec[1] ? fifo_rdata_1 : ch_grant_vec[2] ? fifo_rdata_2 : fifo_rdata_3;

    // Arbiter
    dma_real_arbiter #(.N_CHANNELS(N_CHANNELS)) u_arbiter (
        .hclk(hclk), .hresetn(hresetn),
        .ch_request(ch_request), .arb_grant(arb_grant), .ch_grant(ch_grant_vec), .ahb_busy(ahb_bus_busy)
    );

    // Per-channel FIFOs (simple sync FIFOs within hclk domain)
    logic [DATA_WIDTH-1:0] fifo_mem_0 [FIFO_DEPTH];
    logic [3:0] fifo_count_0;
    assign fifo_empty_0 = (fifo_count_0 == 4'd0);
    assign fifo_full_0  = (fifo_count_0 >= FIFO_DEPTH[3:0]);
    assign fifo_rdata_0 = (fifo_count_0 > 4'd0) ? fifo_mem_0[0] : {DATA_WIDTH{1'b0}};
    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) fifo_count_0 <= 4'd0;
        else if (fifo_wen_0 && !fifo_full_0 && !(fifo_ren_0 && !fifo_empty_0)) begin
            fifo_mem_0[fifo_count_0] <= fifo_wdata_0; fifo_count_0 <= fifo_count_0 + 4'd1;
        end else if (fifo_ren_0 && !fifo_empty_0 && !(fifo_wen_0 && !fifo_full_0)) begin
            fifo_mem_0[0] <= fifo_mem_0[1]; fifo_mem_0[1] <= fifo_mem_0[2]; fifo_mem_0[2] <= fifo_mem_0[3];
            fifo_mem_0[3] <= fifo_mem_0[4]; fifo_mem_0[4] <= fifo_mem_0[5]; fifo_mem_0[5] <= fifo_mem_0[6];
            fifo_mem_0[6] <= fifo_mem_0[7]; fifo_count_0 <= fifo_count_0 - 4'd1;
        end
    end

    logic [DATA_WIDTH-1:0] fifo_mem_1 [FIFO_DEPTH]; logic [3:0] fifo_count_1;
    assign fifo_empty_1 = (fifo_count_1 == 4'd0); assign fifo_full_1 = (fifo_count_1 >= FIFO_DEPTH[3:0]);
    assign fifo_rdata_1 = (fifo_count_1 > 4'd0) ? fifo_mem_1[0] : {DATA_WIDTH{1'b0}};
    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) fifo_count_1 <= 4'd0;
        else if (fifo_wen_1 && !fifo_full_1 && !(fifo_ren_1 && !fifo_empty_1)) begin
            fifo_mem_1[fifo_count_1] <= fifo_wdata_1; fifo_count_1 <= fifo_count_1 + 4'd1;
        end else if (fifo_ren_1 && !fifo_empty_1 && !(fifo_wen_1 && !fifo_full_1)) begin
            fifo_mem_1[0] <= fifo_mem_1[1]; fifo_mem_1[1] <= fifo_mem_1[2]; fifo_mem_1[2] <= fifo_mem_1[3];
            fifo_mem_1[3] <= fifo_mem_1[4]; fifo_mem_1[4] <= fifo_mem_1[5]; fifo_mem_1[5] <= fifo_mem_1[6];
            fifo_mem_1[6] <= fifo_mem_1[7]; fifo_count_1 <= fifo_count_1 - 4'd1;
        end
    end

    logic [DATA_WIDTH-1:0] fifo_mem_2 [FIFO_DEPTH]; logic [3:0] fifo_count_2;
    assign fifo_empty_2 = (fifo_count_2 == 4'd0); assign fifo_full_2 = (fifo_count_2 >= FIFO_DEPTH[3:0]);
    assign fifo_rdata_2 = (fifo_count_2 > 4'd0) ? fifo_mem_2[0] : {DATA_WIDTH{1'b0}};
    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) fifo_count_2 <= 4'd0;
        else if (fifo_wen_2 && !fifo_full_2 && !(fifo_ren_2 && !fifo_empty_2)) begin
            fifo_mem_2[fifo_count_2] <= fifo_wdata_2; fifo_count_2 <= fifo_count_2 + 4'd1;
        end else if (fifo_ren_2 && !fifo_empty_2 && !(fifo_wen_2 && !fifo_full_2)) begin
            fifo_mem_2[0] <= fifo_mem_2[1]; fifo_mem_2[1] <= fifo_mem_2[2]; fifo_mem_2[2] <= fifo_mem_2[3];
            fifo_mem_2[3] <= fifo_mem_2[4]; fifo_mem_2[4] <= fifo_mem_2[5]; fifo_mem_2[5] <= fifo_mem_2[6];
            fifo_mem_2[6] <= fifo_mem_2[7]; fifo_count_2 <= fifo_count_2 - 4'd1;
        end
    end

    logic [DATA_WIDTH-1:0] fifo_mem_3 [FIFO_DEPTH]; logic [3:0] fifo_count_3;
    assign fifo_empty_3 = (fifo_count_3 == 4'd0); assign fifo_full_3 = (fifo_count_3 >= FIFO_DEPTH[3:0]);
    assign fifo_rdata_3 = (fifo_count_3 > 4'd0) ? fifo_mem_3[0] : {DATA_WIDTH{1'b0}};
    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) fifo_count_3 <= 4'd0;
        else if (fifo_wen_3 && !fifo_full_3 && !(fifo_ren_3 && !fifo_empty_3)) begin
            fifo_mem_3[fifo_count_3] <= fifo_wdata_3; fifo_count_3 <= fifo_count_3 + 4'd1;
        end else if (fifo_ren_3 && !fifo_empty_3 && !(fifo_wen_3 && !fifo_full_3)) begin
            fifo_mem_3[0] <= fifo_mem_3[1]; fifo_mem_3[1] <= fifo_mem_3[2]; fifo_mem_3[2] <= fifo_mem_3[3];
            fifo_mem_3[3] <= fifo_mem_3[4]; fifo_mem_3[4] <= fifo_mem_3[5]; fifo_mem_3[5] <= fifo_mem_3[6];
            fifo_mem_3[6] <= fifo_mem_3[7]; fifo_count_3 <= fifo_count_3 - 4'd1;
        end
    end

    // Channels
    dma_real_channel #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH), .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH), .CH_ID(0)) u_ch0 (
        .hclk(hclk), .hresetn(hresetn), .ch_en(ch_en[0]), .ch_start(ch_start[0]), .dma_en(dma_en),
        .cfg_src_addr(cfg_src_addr_0), .cfg_dst_addr(cfg_dst_addr_0), .cfg_len(cfg_len_0), .cfg_stride(cfg_stride_0),
        .cfg_hsize(3'b010), .cfg_hburst(3'b001), .cfg_timeout(cfg_timeout),
        .ch_request(ch_request[0]), .ch_grant(ch_grant_vec[0]),
        .ahb_start(ahb_start_vec[0]), .ahb_write(ahb_write_vec[0]), .ahb_addr(ahb_addr_0), .ahb_len(ahb_len_0),
        .ahb_done(ahb_master_done), .ahb_error(ahb_master_error), .ahb_err_code(ahb_master_err_code),
        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),
        .status_busy(ch_busy[0]), .status_done(ch_done_pulse[0]), .status_error(ch_error_pulse[0]), .status_err_code(ch_err_code_0),
        .fifo_wdata(fifo_wdata_0), .fifo_wen(fifo_wen_0), .fifo_rdata(fifo_rdata_0), .fifo_ren(fifo_ren_0),
        .fifo_empty(fifo_empty_0), .fifo_full(fifo_full_0),
        .perf_words(perf_words_0), .perf_cycles(perf_cycles_0)
    );
    dma_real_channel #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH), .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH), .CH_ID(1)) u_ch1 (
        .hclk(hclk), .hresetn(hresetn), .ch_en(ch_en[1]), .ch_start(ch_start[1]), .dma_en(dma_en),
        .cfg_src_addr(cfg_src_addr_1), .cfg_dst_addr(cfg_dst_addr_1), .cfg_len(cfg_len_1), .cfg_stride(cfg_stride_1),
        .cfg_hsize(3'b010), .cfg_hburst(3'b001), .cfg_timeout(cfg_timeout),
        .ch_request(ch_request[1]), .ch_grant(ch_grant_vec[1]),
        .ahb_start(ahb_start_vec[1]), .ahb_write(ahb_write_vec[1]), .ahb_addr(ahb_addr_1), .ahb_len(ahb_len_1),
        .ahb_done(ahb_master_done), .ahb_error(ahb_master_error), .ahb_err_code(ahb_master_err_code),
        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),
        .status_busy(ch_busy[1]), .status_done(ch_done_pulse[1]), .status_error(ch_error_pulse[1]), .status_err_code(ch_err_code_1),
        .fifo_wdata(fifo_wdata_1), .fifo_wen(fifo_wen_1), .fifo_rdata(fifo_rdata_1), .fifo_ren(fifo_ren_1),
        .fifo_empty(fifo_empty_1), .fifo_full(fifo_full_1),
        .perf_words(perf_words_1), .perf_cycles(perf_cycles_1)
    );
    dma_real_channel #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH), .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH), .CH_ID(2)) u_ch2 (
        .hclk(hclk), .hresetn(hresetn), .ch_en(ch_en[2]), .ch_start(ch_start[2]), .dma_en(dma_en),
        .cfg_src_addr(cfg_src_addr_2), .cfg_dst_addr(cfg_dst_addr_2), .cfg_len(cfg_len_2), .cfg_stride(cfg_stride_2),
        .cfg_hsize(3'b010), .cfg_hburst(3'b001), .cfg_timeout(cfg_timeout),
        .ch_request(ch_request[2]), .ch_grant(ch_grant_vec[2]),
        .ahb_start(ahb_start_vec[2]), .ahb_write(ahb_write_vec[2]), .ahb_addr(ahb_addr_2), .ahb_len(ahb_len_2),
        .ahb_done(ahb_master_done), .ahb_error(ahb_master_error), .ahb_err_code(ahb_master_err_code),
        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),
        .status_busy(ch_busy[2]), .status_done(ch_done_pulse[2]), .status_error(ch_error_pulse[2]), .status_err_code(ch_err_code_2),
        .fifo_wdata(fifo_wdata_2), .fifo_wen(fifo_wen_2), .fifo_rdata(fifo_rdata_2), .fifo_ren(fifo_ren_2),
        .fifo_empty(fifo_empty_2), .fifo_full(fifo_full_2),
        .perf_words(perf_words_2), .perf_cycles(perf_cycles_2)
    );
    dma_real_channel #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH), .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH), .CH_ID(3)) u_ch3 (
        .hclk(hclk), .hresetn(hresetn), .ch_en(ch_en[3]), .ch_start(ch_start[3]), .dma_en(dma_en),
        .cfg_src_addr(cfg_src_addr_3), .cfg_dst_addr(cfg_dst_addr_3), .cfg_len(cfg_len_3), .cfg_stride(cfg_stride_3),
        .cfg_hsize(3'b010), .cfg_hburst(3'b001), .cfg_timeout(cfg_timeout),
        .ch_request(ch_request[3]), .ch_grant(ch_grant_vec[3]),
        .ahb_start(ahb_start_vec[3]), .ahb_write(ahb_write_vec[3]), .ahb_addr(ahb_addr_3), .ahb_len(ahb_len_3),
        .ahb_done(ahb_master_done), .ahb_error(ahb_master_error), .ahb_err_code(ahb_master_err_code),
        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),
        .status_busy(ch_busy[3]), .status_done(ch_done_pulse[3]), .status_error(ch_error_pulse[3]), .status_err_code(ch_err_code_3),
        .fifo_wdata(fifo_wdata_3), .fifo_wen(fifo_wen_3), .fifo_rdata(fifo_rdata_3), .fifo_ren(fifo_ren_3),
        .fifo_empty(fifo_empty_3), .fifo_full(fifo_full_3),
        .perf_words(perf_words_3), .perf_cycles(perf_cycles_3)
    );

    // AHB Master
    dma_real_ahb_master #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH), .BURST_MAX(BURST_MAX)) u_ahb_master (
        .hclk(hclk), .hresetn(hresetn),
        .xfer_start(mux_ahb_start), .xfer_write(mux_ahb_write), .xfer_addr(mux_ahb_addr), .xfer_len(mux_ahb_len),
        .xfer_hsize(3'b010), .xfer_hburst(3'b001), .xfer_hprot(4'b0011), .xfer_hmaster({1'b0, arb_grant}), .xfer_hmastlock(1'b0),
        .xfer_timeout(cfg_timeout),
        .xfer_done(ahb_master_done), .xfer_error(ahb_master_error), .xfer_err_code(ahb_master_err_code),
        .write_data(mux_ahb_wdata), .read_data(ahb_master_rdata),
        .haddr(haddr), .hwrite(hwrite), .htrans(htrans), .hsize(hsize), .hburst(hburst),
        .hprot(hprot), .hmaster(hmaster), .hmastlock(hmastlock),
        .hwdata(hwdata), .hrdata(hrdata), .hready(hready), .hresp(hresp),
        .hbusreq(hbusreq), .hgrant(hgrant)
    );

endmodule
