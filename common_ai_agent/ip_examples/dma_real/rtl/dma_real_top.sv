// dma_real_top.sv — Dual-clock top-level wiring
// v2: pclk domain (APB + IRQ) + hclk domain (engine) with CDC bridges
module dma_real_top #(
    parameter integer ADDR_WIDTH  = 32,
    parameter integer DATA_WIDTH  = 32,
    parameter integer N_CHANNELS  = 4,
    parameter integer BURST_MAX   = 16,
    parameter integer FIFO_DEPTH  = 16
) (
    input  logic pclk, input  logic hclk,
    input  logic presetn, input  logic hresetn,
    input  logic psel, input  logic penable, input  logic pwrite,
    input  logic [11:0] paddr, input  logic [DATA_WIDTH-1:0] pwdata,
    output logic [DATA_WIDTH-1:0] prdata, output logic pready, output logic pslverr,
    output logic [ADDR_WIDTH-1:0] haddr, output logic hwrite, output logic [1:0] htrans,
    output logic [2:0] hsize, output logic [2:0] hburst, output logic [3:0] hprot,
    output logic [3:0] hmaster, output logic hmastlock,
    output logic [DATA_WIDTH-1:0] hwdata,
    input  logic [DATA_WIDTH-1:0] hrdata, input  logic hready, input  logic [1:0] hresp,
    output logic hbusreq, input  logic hgrant,
    output logic [N_CHANNELS-1:0] irq, output logic irq_combined,
    output logic [N_CHANNELS-1:0] ch_busy, output logic [N_CHANNELS-1:0] ch_done,
    output logic [N_CHANNELS-1:0] ch_error, output logic [7:0] ch_err_code,
    output logic [2:0] arb_grant
);

    logic dma_en;
    logic [N_CHANNELS-1:0] ch_en, ch_start_pulse;
    logic [ADDR_WIDTH-1:0] cfg_src_addr_0, cfg_src_addr_1, cfg_src_addr_2, cfg_src_addr_3;
    logic [ADDR_WIDTH-1:0] cfg_dst_addr_0, cfg_dst_addr_1, cfg_dst_addr_2, cfg_dst_addr_3;
    logic [15:0] cfg_len_0, cfg_len_1, cfg_len_2, cfg_len_3;
    logic [ADDR_WIDTH-1:0] cfg_stride_0, cfg_stride_1, cfg_stride_2, cfg_stride_3;
    logic [15:0] cfg_timeout;
    logic [N_CHANNELS-1:0] int_enable_wr, int_enable_wdata, int_clear_wr, int_status, int_enable_rd;
    logic [N_CHANNELS-1:0] int_done, int_error;
    logic [N_CHANNELS-1:0] ch_done_pulse, ch_error_pulse;
    logic [31:0] perf_words_0, perf_words_1, perf_words_2, perf_words_3;
    logic [31:0] perf_cycles_0, perf_cycles_1, perf_cycles_2, perf_cycles_3;

    // CDC: hclk -> pclk status sync (2-stage)
    logic [N_CHANNELS-1:0] ch_busy_hclk, ch_busy_pclk;
    logic [N_CHANNELS-1:0] ch_done_pulse_hclk, ch_done_pulse_pclk;
    logic [N_CHANNELS-1:0] ch_error_pulse_hclk, ch_error_pulse_pclk;
    logic [7:0] ch_err_code_hclk;

    assign ch_busy_hclk = ch_busy;

    // CDC: hclk -> pclk status sync (simplified: direct pass-through for sim)
    // Production: replace with proper 2-stage synchronizers + pulse-to-level
    assign ch_busy_pclk      = ch_busy_hclk;
    assign ch_done_pulse_pclk  = ch_done_pulse;
    assign ch_error_pulse_pclk = ch_error_pulse;

    assign ch_err_code = ch_err_code_hclk;
    assign ch_done  = ch_done_pulse_pclk;
    assign ch_error = ch_error_pulse_pclk;

    // APB CFG (pclk domain)
    dma_real_apb_cfg #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH), .N_CHANNELS(N_CHANNELS)) u_apb_cfg (
        .pclk(pclk), .presetn(presetn), .psel(psel), .penable(penable), .pwrite(pwrite),
        .paddr(paddr), .pwdata(pwdata), .prdata(prdata), .pready(pready), .pslverr(pslverr),
        .dma_en(dma_en), .ch_en(ch_en), .ch_start_pulse(ch_start_pulse),
        .cfg_src_addr_0(cfg_src_addr_0), .cfg_src_addr_1(cfg_src_addr_1),
        .cfg_src_addr_2(cfg_src_addr_2), .cfg_src_addr_3(cfg_src_addr_3),
        .cfg_dst_addr_0(cfg_dst_addr_0), .cfg_dst_addr_1(cfg_dst_addr_1),
        .cfg_dst_addr_2(cfg_dst_addr_2), .cfg_dst_addr_3(cfg_dst_addr_3),
        .cfg_len_0(cfg_len_0), .cfg_len_1(cfg_len_1), .cfg_len_2(cfg_len_2), .cfg_len_3(cfg_len_3),
        .cfg_stride_0(cfg_stride_0), .cfg_stride_1(cfg_stride_1),
        .cfg_stride_2(cfg_stride_2), .cfg_stride_3(cfg_stride_3),
        .cfg_timeout(cfg_timeout),
        .ch_busy(ch_busy_pclk), .ch_done(ch_done_pulse_pclk), .ch_error(ch_error_pulse_pclk),
        .ch_err_code(ch_err_code_hclk),
        .int_done(int_done), .int_error(int_error),
        .int_enable_wr(int_enable_wr), .int_enable_wdata(int_enable_wdata),
        .int_clear_wr(int_clear_wr), .int_status(int_status), .int_enable_rd(int_enable_rd),
        .perf_words_0(perf_words_0), .perf_words_1(perf_words_1),
        .perf_words_2(perf_words_2), .perf_words_3(perf_words_3),
        .perf_cycles_0(perf_cycles_0), .perf_cycles_1(perf_cycles_1),
        .perf_cycles_2(perf_cycles_2), .perf_cycles_3(perf_cycles_3)
    );

    // Engine (hclk domain)
    dma_real_engine #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH),
        .N_CHANNELS(N_CHANNELS), .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH)) u_engine (
        .hclk(hclk), .hresetn(hresetn), .dma_en(dma_en), .ch_en(ch_en), .ch_start(ch_start_pulse),
        .cfg_src_addr_0(cfg_src_addr_0), .cfg_src_addr_1(cfg_src_addr_1),
        .cfg_src_addr_2(cfg_src_addr_2), .cfg_src_addr_3(cfg_src_addr_3),
        .cfg_dst_addr_0(cfg_dst_addr_0), .cfg_dst_addr_1(cfg_dst_addr_1),
        .cfg_dst_addr_2(cfg_dst_addr_2), .cfg_dst_addr_3(cfg_dst_addr_3),
        .cfg_len_0(cfg_len_0), .cfg_len_1(cfg_len_1), .cfg_len_2(cfg_len_2), .cfg_len_3(cfg_len_3),
        .cfg_stride_0(cfg_stride_0), .cfg_stride_1(cfg_stride_1),
        .cfg_stride_2(cfg_stride_2), .cfg_stride_3(cfg_stride_3),
        .cfg_timeout(cfg_timeout),
        .ch_busy(ch_busy), .ch_done_pulse(ch_done_pulse), .ch_error_pulse(ch_error_pulse),
        .ch_err_code(ch_err_code_hclk), .arb_grant(arb_grant),
        .perf_words_0(perf_words_0), .perf_words_1(perf_words_1),
        .perf_words_2(perf_words_2), .perf_words_3(perf_words_3),
        .perf_cycles_0(perf_cycles_0), .perf_cycles_1(perf_cycles_1),
        .perf_cycles_2(perf_cycles_2), .perf_cycles_3(perf_cycles_3),
        .haddr(haddr), .hwrite(hwrite), .htrans(htrans), .hsize(hsize), .hburst(hburst),
        .hprot(hprot), .hmaster(hmaster), .hmastlock(hmastlock),
        .hwdata(hwdata), .hrdata(hrdata), .hready(hready), .hresp(hresp),
        .hbusreq(hbusreq), .hgrant(hgrant)
    );

    // IRQ (pclk domain)
    dma_real_irq #(.N_CHANNELS(N_CHANNELS)) u_irq (
        .pclk(pclk), .presetn(presetn),
        .ch_done(ch_done_pulse_pclk), .ch_error(ch_error_pulse_pclk),
        .int_enable_wr(int_enable_wr), .int_enable_wdata(int_enable_wdata),
        .int_clear_wr(int_clear_wr), .int_status(int_status), .int_enable_rd(int_enable_rd),
        .int_done(int_done), .int_error(int_error),
        .irq(irq), .irq_combined(irq_combined)
    );

endmodule
