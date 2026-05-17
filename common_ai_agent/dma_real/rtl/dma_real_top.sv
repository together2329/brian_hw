// dma_real_top.sv — Top-level wiring connecting APB, AHB, arbiter, channels, and IRQ
//
// SSOT refs: io_list, sub_modules, integration
//
// FIXES:
//   - ahb_bus_busy uses htrans (actual AHB bus state) instead of |ch_request (deadlock)
//   - ahb_master_rdata driven from hrdata
//   - fifo_rdata connected properly (was unconnected)
//   - IRQ int_done/int_error routed to APB cfg for STATUS readback

module dma_real_top #(
    parameter integer ADDR_WIDTH  = 32,
    parameter integer DATA_WIDTH  = 32,
    parameter integer N_CHANNELS  = 4,
    parameter integer BURST_MAX   = 16,
    parameter integer FIFO_DEPTH  = 8
) (
    // Clock and reset
    input  logic                  pclk,
    input  logic                  presetn,
    // APB slave interface
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [11:0]           paddr,
    input  logic [DATA_WIDTH-1:0] pwdata,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    // AHB-Lite master interface
    output logic [ADDR_WIDTH-1:0] haddr,
    output logic                  hwrite,
    output logic [1:0]            htrans,
    output logic [2:0]            hsize,
    output logic [2:0]            hburst,
    output logic [DATA_WIDTH-1:0] hwdata,
    input  logic [DATA_WIDTH-1:0] hrdata,
    input  logic                  hready,
    input  logic                  hresp,
    output logic                  hbusreq,
    input  logic                  hgrant,
    // IRQ outputs
    output logic [N_CHANNELS-1:0] irq,
    output logic                  irq_combined,
    // DMA status (observable debug outputs)
    output logic [N_CHANNELS-1:0] ch_busy,
    output logic [N_CHANNELS-1:0] ch_done,
    output logic [N_CHANNELS-1:0] ch_error,
    output logic [7:0]            ch_err_code,
    output logic [2:0]            arb_grant
);

    // ===== All internal wire declarations =====

    // APB config -> channels
    logic                  dma_en;
    logic [N_CHANNELS-1:0] ch_en;
    logic [N_CHANNELS-1:0] ch_start_pulse;
    logic [ADDR_WIDTH-1:0] cfg_src_addr_0, cfg_src_addr_1, cfg_src_addr_2, cfg_src_addr_3;
    logic [ADDR_WIDTH-1:0] cfg_dst_addr_0, cfg_dst_addr_1, cfg_dst_addr_2, cfg_dst_addr_3;
    logic [15:0]           cfg_len_0, cfg_len_1, cfg_len_2, cfg_len_3;

    // Channel -> arbiter
    logic [N_CHANNELS-1:0] ch_request;
    logic [N_CHANNELS-1:0] ch_grant_vec;

    // Channel -> IRQ (1-cycle pulses)
    logic [N_CHANNELS-1:0] ch_done_pulse;
    logic [N_CHANNELS-1:0] ch_error_pulse;

    // Per-channel status
    logic [1:0] ch_err_code_0, ch_err_code_1, ch_err_code_2, ch_err_code_3;

    // IRQ -> APB
    logic [N_CHANNELS-1:0] int_enable_wr;
    logic [N_CHANNELS-1:0] int_enable_wdata;
    logic [N_CHANNELS-1:0] int_clear_wr;
    logic [N_CHANNELS-1:0] int_status;
    logic [N_CHANNELS-1:0] int_enable_rd;
    logic [N_CHANNELS-1:0] int_done;
    logic [N_CHANNELS-1:0] int_error;

    // Channel -> AHB master (per-channel)
    logic [N_CHANNELS-1:0] ahb_start_vec;
    logic [N_CHANNELS-1:0] ahb_write_vec;
    logic [ADDR_WIDTH-1:0] ahb_addr_0, ahb_addr_1, ahb_addr_2, ahb_addr_3;
    logic [15:0]           ahb_len_0, ahb_len_1, ahb_len_2, ahb_len_3;

    // Shared AHB master signals
    logic                  ahb_master_done;
    logic                  ahb_master_error;
    logic [DATA_WIDTH-1:0] ahb_master_rdata;

    // Per-channel FIFO signals
    logic [DATA_WIDTH-1:0] fifo_wdata_0, fifo_wdata_1, fifo_wdata_2, fifo_wdata_3;
    logic                  fifo_wen_0, fifo_wen_1, fifo_wen_2, fifo_wen_3;
    logic                  fifo_ren_0, fifo_ren_1, fifo_ren_2, fifo_ren_3;
    logic [DATA_WIDTH-1:0] fifo_rdata_0, fifo_rdata_1, fifo_rdata_2, fifo_rdata_3;
    logic                  fifo_empty_0, fifo_empty_1, fifo_empty_2, fifo_empty_3;
    logic                  fifo_full_0, fifo_full_1, fifo_full_2, fifo_full_3;

    // AHB mux
    wire [ADDR_WIDTH-1:0] mux_ahb_addr  = ch_grant_vec[0] ? ahb_addr_0  : ch_grant_vec[1] ? ahb_addr_1  : ch_grant_vec[2] ? ahb_addr_2  : ahb_addr_3;
    wire [15:0]           mux_ahb_len   = ch_grant_vec[0] ? ahb_len_0   : ch_grant_vec[1] ? ahb_len_1   : ch_grant_vec[2] ? ahb_len_2   : ahb_len_3;
    wire                  mux_ahb_write = ch_grant_vec[0] ? ahb_write_vec[0] : ch_grant_vec[1] ? ahb_write_vec[1] : ch_grant_vec[2] ? ahb_write_vec[2] : ahb_write_vec[3];
    wire                  mux_ahb_start = ch_grant_vec[0] ? ahb_start_vec[0] : ch_grant_vec[1] ? ahb_start_vec[1] : ch_grant_vec[2] ? ahb_start_vec[2] : ahb_start_vec[3];
    wire [DATA_WIDTH-1:0] mux_ahb_wdata = ch_grant_vec[0] ? fifo_rdata_0 : ch_grant_vec[1] ? fifo_rdata_1 : ch_grant_vec[2] ? fifo_rdata_2 : fifo_rdata_3;

    // FIX: ahb_master_rdata driven from AHB bus hrdata
    assign ahb_master_rdata = hrdata;

    // Pack error codes
    assign ch_err_code = {ch_err_code_3, ch_err_code_2, ch_err_code_1, ch_err_code_0};

    // FIX: ahb_bus_busy reflects actual AHB bus activity (htrans != IDLE), not channel request
    wire ahb_bus_busy = (htrans != 2'b00);

    // ===== APB Configuration Module =====
    dma_real_apb_cfg #(
        .ADDR_WIDTH (ADDR_WIDTH),
        .DATA_WIDTH (DATA_WIDTH),
        .N_CHANNELS (N_CHANNELS)
    ) u_apb_cfg (
        .pclk           (pclk),
        .presetn        (presetn),
        .psel           (psel),
        .penable        (penable),
        .pwrite         (pwrite),
        .paddr          (paddr),
        .pwdata         (pwdata),
        .prdata         (prdata),
        .pready         (pready),
        .pslverr        (pslverr),
        .dma_en         (dma_en),
        .ch_en          (ch_en),
        .ch_start_pulse (ch_start_pulse),
        .cfg_src_addr_0 (cfg_src_addr_0), .cfg_src_addr_1 (cfg_src_addr_1),
        .cfg_src_addr_2 (cfg_src_addr_2), .cfg_src_addr_3 (cfg_src_addr_3),
        .cfg_dst_addr_0 (cfg_dst_addr_0), .cfg_dst_addr_1 (cfg_dst_addr_1),
        .cfg_dst_addr_2 (cfg_dst_addr_2), .cfg_dst_addr_3 (cfg_dst_addr_3),
        .cfg_len_0 (cfg_len_0), .cfg_len_1 (cfg_len_1),
        .cfg_len_2 (cfg_len_2), .cfg_len_3 (cfg_len_3),
        .ch_busy        (ch_busy),
        .ch_done        (ch_done_pulse),
        .ch_error       (ch_error_pulse),
        .ch_err_code    (ch_err_code),
        .int_done       (int_done),
        .int_error      (int_error),
        .int_enable_wr    (int_enable_wr),
        .int_enable_wdata (int_enable_wdata),
        .int_clear_wr     (int_clear_wr),
        .int_status       (int_status),
        .int_enable_rd    (int_enable_rd)
    );

    // ===== Arbiter =====
    dma_real_arbiter #(
        .N_CHANNELS (N_CHANNELS)
    ) u_arbiter (
        .pclk      (pclk),
        .presetn   (presetn),
        .ch_request(ch_request),
        .arb_grant (arb_grant),
        .ch_grant  (ch_grant_vec),
        .ahb_busy  (ahb_bus_busy)
    );

    // ===== Channel 0 =====
    logic [DATA_WIDTH-1:0] fifo_mem_0 [FIFO_DEPTH];
    logic [3:0] fifo_count_0;
    assign fifo_empty_0 = (fifo_count_0 == 4'd0);
    assign fifo_full_0  = (fifo_count_0 >= FIFO_DEPTH[3:0]);
    assign fifo_rdata_0 = (fifo_count_0 > 4'd0) ? fifo_mem_0[0] : {DATA_WIDTH{1'b0}};

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            fifo_count_0 <= 4'd0;
        end else begin
            if (fifo_wen_0 && !fifo_full_0 && !(fifo_ren_0 && !fifo_empty_0)) begin
                fifo_mem_0[fifo_count_0] <= fifo_wdata_0;
                fifo_count_0 <= fifo_count_0 + 4'd1;
            end
            else if (fifo_ren_0 && !fifo_empty_0 && !(fifo_wen_0 && !fifo_full_0)) begin
                fifo_mem_0[0] <= fifo_mem_0[1];
                fifo_mem_0[1] <= fifo_mem_0[2];
                fifo_mem_0[2] <= fifo_mem_0[3];
                fifo_mem_0[3] <= fifo_mem_0[4];
                fifo_mem_0[4] <= fifo_mem_0[5];
                fifo_mem_0[5] <= fifo_mem_0[6];
                fifo_mem_0[6] <= fifo_mem_0[7];
                fifo_count_0 <= fifo_count_0 - 4'd1;
            end
        end
    end

    dma_real_channel #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH),
        .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH), .CH_ID(0)) u_ch0 (
        .pclk(pclk), .presetn(presetn),
        .ch_en(ch_en[0]), .ch_start(ch_start_pulse[0]), .dma_en(dma_en),
        .cfg_src_addr(cfg_src_addr_0), .cfg_dst_addr(cfg_dst_addr_0), .cfg_len(cfg_len_0),
        .ch_request(ch_request[0]), .ch_grant(ch_grant_vec[0]),
        .ahb_start(ahb_start_vec[0]), .ahb_write(ahb_write_vec[0]),
        .ahb_addr(ahb_addr_0), .ahb_len(ahb_len_0),
        .ahb_done(ahb_master_done), .ahb_error(ahb_master_error),
        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),
        .status_busy(ch_busy[0]), .status_done(ch_done_pulse[0]),
        .status_error(ch_error_pulse[0]), .status_err_code(ch_err_code_0),
        .fifo_wdata(fifo_wdata_0), .fifo_wen(fifo_wen_0),
        .fifo_rdata(fifo_rdata_0), .fifo_ren(fifo_ren_0),
        .fifo_empty(fifo_empty_0), .fifo_full(fifo_full_0)
    );

    // ===== Channel 1 =====
    logic [DATA_WIDTH-1:0] fifo_mem_1 [FIFO_DEPTH];
    logic [3:0] fifo_count_1;
    assign fifo_empty_1 = (fifo_count_1 == 4'd0);
    assign fifo_full_1  = (fifo_count_1 >= FIFO_DEPTH[3:0]);
    assign fifo_rdata_1 = (fifo_count_1 > 4'd0) ? fifo_mem_1[0] : {DATA_WIDTH{1'b0}};

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            fifo_count_1 <= 4'd0;
        end else begin
            if (fifo_wen_1 && !fifo_full_1 && !(fifo_ren_1 && !fifo_empty_1)) begin
                fifo_mem_1[fifo_count_1] <= fifo_wdata_1;
                fifo_count_1 <= fifo_count_1 + 4'd1;
            end
            else if (fifo_ren_1 && !fifo_empty_1 && !(fifo_wen_1 && !fifo_full_1)) begin
                fifo_mem_1[0] <= fifo_mem_1[1];
                fifo_mem_1[1] <= fifo_mem_1[2];
                fifo_mem_1[2] <= fifo_mem_1[3];
                fifo_mem_1[3] <= fifo_mem_1[4];
                fifo_mem_1[4] <= fifo_mem_1[5];
                fifo_mem_1[5] <= fifo_mem_1[6];
                fifo_mem_1[6] <= fifo_mem_1[7];
                fifo_count_1 <= fifo_count_1 - 4'd1;
            end
        end
    end

    dma_real_channel #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH),
        .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH), .CH_ID(1)) u_ch1 (
        .pclk(pclk), .presetn(presetn),
        .ch_en(ch_en[1]), .ch_start(ch_start_pulse[1]), .dma_en(dma_en),
        .cfg_src_addr(cfg_src_addr_1), .cfg_dst_addr(cfg_dst_addr_1), .cfg_len(cfg_len_1),
        .ch_request(ch_request[1]), .ch_grant(ch_grant_vec[1]),
        .ahb_start(ahb_start_vec[1]), .ahb_write(ahb_write_vec[1]),
        .ahb_addr(ahb_addr_1), .ahb_len(ahb_len_1),
        .ahb_done(ahb_master_done), .ahb_error(ahb_master_error),
        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),
        .status_busy(ch_busy[1]), .status_done(ch_done_pulse[1]),
        .status_error(ch_error_pulse[1]), .status_err_code(ch_err_code_1),
        .fifo_wdata(fifo_wdata_1), .fifo_wen(fifo_wen_1),
        .fifo_rdata(fifo_rdata_1), .fifo_ren(fifo_ren_1),
        .fifo_empty(fifo_empty_1), .fifo_full(fifo_full_1)
    );

    // ===== Channel 2 =====
    logic [DATA_WIDTH-1:0] fifo_mem_2 [FIFO_DEPTH];
    logic [3:0] fifo_count_2;
    assign fifo_empty_2 = (fifo_count_2 == 4'd0);
    assign fifo_full_2  = (fifo_count_2 >= FIFO_DEPTH[3:0]);
    assign fifo_rdata_2 = (fifo_count_2 > 4'd0) ? fifo_mem_2[0] : {DATA_WIDTH{1'b0}};

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            fifo_count_2 <= 4'd0;
        end else begin
            if (fifo_wen_2 && !fifo_full_2 && !(fifo_ren_2 && !fifo_empty_2)) begin
                fifo_mem_2[fifo_count_2] <= fifo_wdata_2;
                fifo_count_2 <= fifo_count_2 + 4'd1;
            end
            else if (fifo_ren_2 && !fifo_empty_2 && !(fifo_wen_2 && !fifo_full_2)) begin
                fifo_mem_2[0] <= fifo_mem_2[1];
                fifo_mem_2[1] <= fifo_mem_2[2];
                fifo_mem_2[2] <= fifo_mem_2[3];
                fifo_mem_2[3] <= fifo_mem_2[4];
                fifo_mem_2[4] <= fifo_mem_2[5];
                fifo_mem_2[5] <= fifo_mem_2[6];
                fifo_mem_2[6] <= fifo_mem_2[7];
                fifo_count_2 <= fifo_count_2 - 4'd1;
            end
        end
    end

    dma_real_channel #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH),
        .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH), .CH_ID(2)) u_ch2 (
        .pclk(pclk), .presetn(presetn),
        .ch_en(ch_en[2]), .ch_start(ch_start_pulse[2]), .dma_en(dma_en),
        .cfg_src_addr(cfg_src_addr_2), .cfg_dst_addr(cfg_dst_addr_2), .cfg_len(cfg_len_2),
        .ch_request(ch_request[2]), .ch_grant(ch_grant_vec[2]),
        .ahb_start(ahb_start_vec[2]), .ahb_write(ahb_write_vec[2]),
        .ahb_addr(ahb_addr_2), .ahb_len(ahb_len_2),
        .ahb_done(ahb_master_done), .ahb_error(ahb_master_error),
        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),
        .status_busy(ch_busy[2]), .status_done(ch_done_pulse[2]),
        .status_error(ch_error_pulse[2]), .status_err_code(ch_err_code_2),
        .fifo_wdata(fifo_wdata_2), .fifo_wen(fifo_wen_2),
        .fifo_rdata(fifo_rdata_2), .fifo_ren(fifo_ren_2),
        .fifo_empty(fifo_empty_2), .fifo_full(fifo_full_2)
    );

    // ===== Channel 3 =====
    logic [DATA_WIDTH-1:0] fifo_mem_3 [FIFO_DEPTH];
    logic [3:0] fifo_count_3;
    assign fifo_empty_3 = (fifo_count_3 == 4'd0);
    assign fifo_full_3  = (fifo_count_3 >= FIFO_DEPTH[3:0]);
    assign fifo_rdata_3 = (fifo_count_3 > 4'd0) ? fifo_mem_3[0] : {DATA_WIDTH{1'b0}};

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            fifo_count_3 <= 4'd0;
        end else begin
            if (fifo_wen_3 && !fifo_full_3 && !(fifo_ren_3 && !fifo_empty_3)) begin
                fifo_mem_3[fifo_count_3] <= fifo_wdata_3;
                fifo_count_3 <= fifo_count_3 + 4'd1;
            end
            else if (fifo_ren_3 && !fifo_empty_3 && !(fifo_wen_3 && !fifo_full_3)) begin
                fifo_mem_3[0] <= fifo_mem_3[1];
                fifo_mem_3[1] <= fifo_mem_3[2];
                fifo_mem_3[2] <= fifo_mem_3[3];
                fifo_mem_3[3] <= fifo_mem_3[4];
                fifo_mem_3[4] <= fifo_mem_3[5];
                fifo_mem_3[5] <= fifo_mem_3[6];
                fifo_mem_3[6] <= fifo_mem_3[7];
                fifo_count_3 <= fifo_count_3 - 4'd1;
            end
        end
    end

    dma_real_channel #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH),
        .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH), .CH_ID(3)) u_ch3 (
        .pclk(pclk), .presetn(presetn),
        .ch_en(ch_en[3]), .ch_start(ch_start_pulse[3]), .dma_en(dma_en),
        .cfg_src_addr(cfg_src_addr_3), .cfg_dst_addr(cfg_dst_addr_3), .cfg_len(cfg_len_3),
        .ch_request(ch_request[3]), .ch_grant(ch_grant_vec[3]),
        .ahb_start(ahb_start_vec[3]), .ahb_write(ahb_write_vec[3]),
        .ahb_addr(ahb_addr_3), .ahb_len(ahb_len_3),
        .ahb_done(ahb_master_done), .ahb_error(ahb_master_error),
        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),
        .status_busy(ch_busy[3]), .status_done(ch_done_pulse[3]),
        .status_error(ch_error_pulse[3]), .status_err_code(ch_err_code_3),
        .fifo_wdata(fifo_wdata_3), .fifo_wen(fifo_wen_3),
        .fifo_rdata(fifo_rdata_3), .fifo_ren(fifo_ren_3),
        .fifo_empty(fifo_empty_3), .fifo_full(fifo_full_3)
    );

    // ===== AHB Master =====
    dma_real_ahb_master #(
        .ADDR_WIDTH (ADDR_WIDTH),
        .DATA_WIDTH (DATA_WIDTH),
        .BURST_MAX  (BURST_MAX)
    ) u_ahb_master (
        .pclk       (pclk),
        .presetn    (presetn),
        .xfer_start (mux_ahb_start),
        .xfer_write (mux_ahb_write),
        .xfer_addr  (mux_ahb_addr),
        .xfer_len   (mux_ahb_len),
        .xfer_done  (ahb_master_done),
        .xfer_error (ahb_master_error),
        .write_data (mux_ahb_wdata),
        .read_data  (ahb_master_rdata),
        .haddr      (haddr),
        .hwrite     (hwrite),
        .htrans     (htrans),
        .hsize      (hsize),
        .hburst     (hburst),
        .hwdata     (hwdata),
        .hrdata     (hrdata),
        .hready     (hready),
        .hresp      (hresp),
        .hbusreq    (hbusreq),
        .hgrant     (hgrant)
    );

    // ===== IRQ Aggregation =====
    dma_real_irq #(
        .N_CHANNELS (N_CHANNELS)
    ) u_irq (
        .pclk            (pclk),
        .presetn         (presetn),
        .ch_done         (ch_done_pulse),
        .ch_error        (ch_error_pulse),
        .int_enable_wr   (int_enable_wr),
        .int_enable_wdata(int_enable_wdata),
        .int_clear_wr    (int_clear_wr),
        .int_status      (int_status),
        .int_enable_rd   (int_enable_rd),
        .int_done        (int_done),
        .int_error       (int_error),
        .irq             (irq),
        .irq_combined    (irq_combined)
    );

endmodule
