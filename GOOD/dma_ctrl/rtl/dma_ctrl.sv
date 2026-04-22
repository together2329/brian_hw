`default_nettype none
module dma_ctrl #(
    parameter int DATA_WIDTH    = 32,
    parameter int ADDR_WIDTH    = 32,
    parameter int ID_WIDTH      = 4,
    parameter int NUM_CHANNELS  = 8,
    parameter int FIFO_DEPTH    = 16,
    parameter int MAX_BURST_LEN = 16
)(
    // Clock and Reset
    input  logic                      axi_clk,
    input  logic                      axi_rst_n,

    // AXI4-Lite Slave Interface
    input  logic [11:0]               s_axi_awaddr,
    input  logic [2:0]                s_axi_awprot,
    input  logic                      s_axi_awvalid,
    output logic                      s_axi_awready,
    input  logic [31:0]               s_axi_wdata,
    input  logic [3:0]                s_axi_wstrb,
    input  logic                      s_axi_wvalid,
    output logic                      s_axi_wready,
    output logic [1:0]                s_axi_bresp,
    output logic                      s_axi_bvalid,
    input  logic                      s_axi_bready,
    input  logic [11:0]               s_axi_araddr,
    input  logic [2:0]                s_axi_arprot,
    input  logic                      s_axi_arvalid,
    output logic                      s_axi_arready,
    output logic [31:0]               s_axi_rdata,
    output logic [1:0]                s_axi_rresp,
    output logic                      s_axi_rvalid,
    input  logic                      s_axi_rready,

    // AXI4 Master Interface
    output logic [ID_WIDTH-1:0]       m_axi_awid,
    output logic [ADDR_WIDTH-1:0]     m_axi_awaddr,
    output logic [7:0]                m_axi_awlen,
    output logic [2:0]                m_axi_awsize,
    output logic [1:0]                m_axi_awburst,
    output logic [2:0]                m_axi_awprot,
    output logic [3:0]                m_axi_awcache,
    output logic                      m_axi_awvalid,
    input  logic                      m_axi_awready,
    output logic [DATA_WIDTH-1:0]     m_axi_wdata,
    output logic [DATA_WIDTH/8-1:0]   m_axi_wstrb,
    output logic                      m_axi_wlast,
    output logic                      m_axi_wvalid,
    input  logic                      m_axi_wready,
    input  logic [ID_WIDTH-1:0]       m_axi_bid,
    input  logic [1:0]                m_axi_bresp,
    input  logic                      m_axi_bvalid,
    output logic                      m_axi_bready,
    output logic [ID_WIDTH-1:0]       m_axi_arid,
    output logic [ADDR_WIDTH-1:0]     m_axi_araddr,
    output logic [7:0]                m_axi_arlen,
    output logic [2:0]                m_axi_arsize,
    output logic [1:0]                m_axi_arburst,
    output logic [2:0]                m_axi_arprot,
    output logic [3:0]                m_axi_arcache,
    output logic                      m_axi_arvalid,
    input  logic                      m_axi_arready,
    input  logic [ID_WIDTH-1:0]       m_axi_rid,
    input  logic [DATA_WIDTH-1:0]     m_axi_rdata,
    input  logic [1:0]                m_axi_rresp,
    input  logic                      m_axi_rlast,
    input  logic                      m_axi_rvalid,
    output logic                      m_axi_rready,

    // Peripheral DMA Request Interface
    input  logic [NUM_CHANNELS-1:0]   dma_req,
    output logic [NUM_CHANNELS-1:0]   dma_ack,
    input  logic [NUM_CHANNELS-1:0]   dma_eop,

    // Interrupt Interface
    output logic [NUM_CHANNELS-1:0]   irq
);

    // ========================================================================
    // Internal signal declarations
    // ========================================================================

    // Global register outputs from reg_block
    logic        dma_enable;
    logic        endian_swap;
    logic [NUM_CHANNELS-1:0] clk_gating;

    // Per-channel status from channel_manager
    logic [NUM_CHANNELS-1:0] channel_active;
    logic [NUM_CHANNELS-1:0] channel_idle;

    // Per-channel register bus (from reg_block to channels)
    logic [NUM_CHANNELS-1:0][31:0] ch_sar;
    logic [NUM_CHANNELS-1:0][31:0] ch_dar;
    logic [NUM_CHANNELS-1:0][31:0] ch_len;
    logic [NUM_CHANNELS-1:0][31:0] ch_cr;
    logic [NUM_CHANNELS-1:0][31:0] ch_sr_w1c_data;
    logic [NUM_CHANNELS-1:0][31:0] ch_llp;
    logic [NUM_CHANNELS-1:0][31:0] ch_bcr;
    logic [NUM_CHANNELS-1:0][31:0] ch_cfg;

    // Per-channel status inputs to reg_block (from channels)
    logic [NUM_CHANNELS-1:0][2:0]  ch_state;
    logic [NUM_CHANNELS-1:0]       ch_fifo_empty;
    logic [NUM_CHANNELS-1:0]       ch_fifo_full;
    logic [NUM_CHANNELS-1:0][2:0]  ch_fifo_count;
    logic [NUM_CHANNELS-1:0][15:0] ch_bcr_bytes;
    logic [NUM_CHANNELS-1:0]       ch_bus_error;
    logic [NUM_CHANNELS-1:0]       ch_align_error;
    logic [NUM_CHANNELS-1:0]       ch_desc_error;
    logic [NUM_CHANNELS-1:0]       ch_xfer_complete;

    // Channel request/grant to arbiter
    logic [NUM_CHANNELS-1:0]       ch_req;
    logic [NUM_CHANNELS-1:0][1:0]  ch_priority;
    logic [ID_WIDTH-1:0]           arb_grant_id;
    logic                          arb_grant_valid;

    // AXI master request from granted channel
    logic                          axi_rd_req;
    logic [ID_WIDTH-1:0]           axi_rd_id;
    logic [ADDR_WIDTH-1:0]         axi_rd_addr;
    logic [7:0]                    axi_rd_len;
    logic [2:0]                    axi_rd_size;
    logic [1:0]                    axi_rd_burst;
    logic [2:0]                    axi_rd_prot;
    logic [3:0]                    axi_rd_cache;

    logic                          axi_wr_req;
    logic [ID_WIDTH-1:0]           axi_wr_id;
    logic [ADDR_WIDTH-1:0]         axi_wr_addr;
    logic [7:0]                    axi_wr_len;
    logic [2:0]                    axi_wr_size;
    logic [1:0]                    axi_wr_burst;
    logic [2:0]                    axi_wr_prot;
    logic [3:0]                    axi_wr_cache;
    logic [DATA_WIDTH-1:0]         axi_wr_data;
    logic [DATA_WIDTH/8-1:0]       axi_wr_strb;
    logic                          axi_wr_last;

    // AXI master response to channel
    logic                          axi_rd_data_valid;
    logic [DATA_WIDTH-1:0]         axi_rd_data;
    logic [1:0]                    axi_rd_resp;
    logic                          axi_rd_last;
    logic [ID_WIDTH-1:0]           axi_rd_data_id;

    logic                          axi_wr_resp_valid;
    logic [ID_WIDTH-1:0]           axi_wr_resp_id;
    logic [1:0]                    axi_wr_resp;
    logic                          axi_wr_ready;
    assign axi_wr_ready = m_axi_wready;

    // Interrupt controller
    logic [NUM_CHANNELS-1:0]       ch_irq_done;
    logic [NUM_CHANNELS-1:0]       ch_irq_err;

    // Interrupt registers
    logic [31:0]                   dma_ier_reg;
    logic [31:0]                   dma_isr_reg;
    logic [31:0]                   dma_err_reg;
    logic [31:0]                   isr_w1c;

    // ========================================================================
    // Submodule instantiation
    // ========================================================================

    // ------------------------------------------------------------------
    // Register Block (AXI4-Lite Slave)
    // ------------------------------------------------------------------
    dma_reg_block #(
        .NUM_CHANNELS (NUM_CHANNELS)
    ) u_reg_block (
        .clk            (axi_clk),
        .rst_n          (axi_rst_n),

        // AXI4-Lite Slave
        .s_axi_awaddr   (s_axi_awaddr),
        .s_axi_awprot   (s_axi_awprot),
        .s_axi_awvalid  (s_axi_awvalid),
        .s_axi_awready  (s_axi_awready),
        .s_axi_wdata    (s_axi_wdata),
        .s_axi_wstrb    (s_axi_wstrb),
        .s_axi_wvalid   (s_axi_wvalid),
        .s_axi_wready   (s_axi_wready),
        .s_axi_bresp    (s_axi_bresp),
        .s_axi_bvalid   (s_axi_bvalid),
        .s_axi_bready   (s_axi_bready),
        .s_axi_araddr   (s_axi_araddr),
        .s_axi_arprot   (s_axi_arprot),
        .s_axi_arvalid  (s_axi_arvalid),
        .s_axi_arready  (s_axi_arready),
        .s_axi_rdata    (s_axi_rdata),
        .s_axi_rresp    (s_axi_rresp),
        .s_axi_rvalid   (s_axi_rvalid),
        .s_axi_rready   (s_axi_rready),

        // Global register outputs
        .dma_enable     (dma_enable),
        .endian_swap    (endian_swap),
        .clk_gating     (clk_gating),

        // Channel register outputs
        .ch_sar         (ch_sar),
        .ch_dar         (ch_dar),
        .ch_len         (ch_len),
        .ch_cr          (ch_cr),
        .ch_sr          (),             // Computed SR — not used by channels
        .ch_sr_w1c_data (ch_sr_w1c_data),
        .ch_llp         (ch_llp),
        .ch_cfg         (ch_cfg),

        // Channel status inputs
        .ch_state       (ch_state),
        .ch_fifo_empty  (ch_fifo_empty),
        .ch_fifo_full   (ch_fifo_full),
        .ch_fifo_count  (ch_fifo_count),
        .ch_bcr         (ch_bcr),
        .ch_bcr_bytes   (ch_bcr_bytes),
        .ch_bus_error   (ch_bus_error),
        .ch_align_error (ch_align_error),
        .ch_desc_error  (ch_desc_error),
        .ch_xfer_complete(ch_xfer_complete),

        // Global status inputs
        .channel_active (channel_active),
        .channel_idle   (channel_idle),

        // Interrupt register interface
        .dma_ier        (dma_ier_reg),
        .dma_isr_in     (dma_isr_reg),
        .dma_err        (dma_err_reg),
        .isr_w1c        (isr_w1c)
    );

    // ------------------------------------------------------------------
    // Channel Manager (Array of DMA channels)
    // ------------------------------------------------------------------
    dma_channel_manager #(
        .DATA_WIDTH    (DATA_WIDTH),
        .ADDR_WIDTH    (ADDR_WIDTH),
        .ID_WIDTH      (ID_WIDTH),
        .NUM_CHANNELS  (NUM_CHANNELS),
        .FIFO_DEPTH    (FIFO_DEPTH),
        .MAX_BURST_LEN (MAX_BURST_LEN)
    ) u_channel_mgr (
        .clk            (axi_clk),
        .rst_n          (axi_rst_n),

        // Global control
        .dma_enable     (dma_enable),
        .endian_swap    (endian_swap),
        .clk_gating     (clk_gating),

        // Per-channel registers
        .ch_sar         (ch_sar),
        .ch_dar         (ch_dar),
        .ch_len         (ch_len),
        .ch_cr          (ch_cr),
        .ch_sr_w1c_data (ch_sr_w1c_data),
        .ch_llp         (ch_llp),
        .ch_bcr         (ch_bcr),
        .ch_cfg         (ch_cfg),

        // Per-channel status outputs
        .ch_state       (ch_state),
        .ch_fifo_empty  (ch_fifo_empty),
        .ch_fifo_full   (ch_fifo_full),
        .ch_fifo_count  (ch_fifo_count),
        .channel_active (channel_active),
        .channel_idle   (channel_idle),

        // Error/status outputs
        .ch_bus_error    (ch_bus_error),
        .ch_align_error  (ch_align_error),
        .ch_desc_error   (ch_desc_error),
        .ch_xfer_complete(ch_xfer_complete),
        .ch_bcr_bytes    (ch_bcr_bytes),

        // Peripheral interface
        .dma_req        (dma_req),
        .dma_ack        (dma_ack),
        .dma_eop        (dma_eop),

        // Channel requests to arbiter
        .ch_req         (ch_req),
        .ch_priority    (ch_priority),

        // AXI read interface to channel
        .axi_rd_req         (axi_rd_req),
        .axi_rd_id          (axi_rd_id),
        .axi_rd_addr        (axi_rd_addr),
        .axi_rd_len         (axi_rd_len),
        .axi_rd_size        (axi_rd_size),
        .axi_rd_burst       (axi_rd_burst),
        .axi_rd_prot        (axi_rd_prot),
        .axi_rd_cache       (axi_rd_cache),

        // AXI write interface from channel
        .axi_wr_req         (axi_wr_req),
        .axi_wr_id          (axi_wr_id),
        .axi_wr_addr        (axi_wr_addr),
        .axi_wr_len         (axi_wr_len),
        .axi_wr_size        (axi_wr_size),
        .axi_wr_burst       (axi_wr_burst),
        .axi_wr_prot        (axi_wr_prot),
        .axi_wr_cache       (axi_wr_cache),
        .axi_wr_data        (axi_wr_data),
        .axi_wr_strb        (axi_wr_strb),
        .axi_wr_last        (axi_wr_last),

        // AXI read response to channel
        .axi_rd_data_valid  (axi_rd_data_valid),
        .axi_rd_data        (axi_rd_data),
        .axi_rd_resp        (axi_rd_resp),
        .axi_rd_last        (axi_rd_last),
        .axi_rd_data_id     (axi_rd_data_id),

        // AXI write response to channel
        .axi_wr_resp_valid  (axi_wr_resp_valid),
        .axi_wr_resp_id     (axi_wr_resp_id),
        .axi_wr_resp        (axi_wr_resp),

        .axi_wr_ready       (axi_wr_ready),

        // Arbiter grant
        .arb_grant_id       (arb_grant_id),
        .arb_grant_valid    (arb_grant_valid),

        // Interrupt outputs
        .ch_irq_done    (ch_irq_done),
        .ch_irq_err     (ch_irq_err)
    );

    // ------------------------------------------------------------------
    // Arbiter
    // ------------------------------------------------------------------
    dma_arbiter #(
        .NUM_CHANNELS (NUM_CHANNELS),
        .ID_WIDTH     (ID_WIDTH)
    ) u_arbiter (
        .clk            (axi_clk),
        .rst_n          (axi_rst_n),

        .ch_req         (ch_req),
        .ch_priority    (ch_priority),

        .grant_id       (arb_grant_id),
        .grant_valid    (arb_grant_valid)
    );

    // ------------------------------------------------------------------
    // AXI Master Interface
    // ------------------------------------------------------------------
    dma_axi_master #(
        .DATA_WIDTH    (DATA_WIDTH),
        .ADDR_WIDTH    (ADDR_WIDTH),
        .ID_WIDTH      (ID_WIDTH)
    ) u_axi_master (
        .clk            (axi_clk),
        .rst_n          (axi_rst_n),

        // Read request
        .rd_req         (axi_rd_req),
        .rd_id          (axi_rd_id),
        .rd_addr        (axi_rd_addr),
        .rd_len         (axi_rd_len),
        .rd_size        (axi_rd_size),
        .rd_burst       (axi_rd_burst),
        .rd_prot        (axi_rd_prot),
        .rd_cache       (axi_rd_cache),

        // Read response
        .rd_data_valid  (axi_rd_data_valid),
        .rd_data        (axi_rd_data),
        .rd_resp        (axi_rd_resp),
        .rd_last        (axi_rd_last),
        .rd_data_id     (axi_rd_data_id),

        // Write request
        .wr_req         (axi_wr_req),
        .wr_id          (axi_wr_id),
        .wr_addr        (axi_wr_addr),
        .wr_len         (axi_wr_len),
        .wr_size        (axi_wr_size),
        .wr_burst       (axi_wr_burst),
        .wr_prot        (axi_wr_prot),
        .wr_cache       (axi_wr_cache),
        .wr_data        (axi_wr_data),
        .wr_strb        (axi_wr_strb),
        .wr_last        (axi_wr_last),

        // Write response
        .wr_resp_valid  (axi_wr_resp_valid),
        .wr_resp_id     (axi_wr_resp_id),
        .wr_resp        (axi_wr_resp),

        // AXI4 Master ports
        .m_axi_awid     (m_axi_awid),
        .m_axi_awaddr   (m_axi_awaddr),
        .m_axi_awlen    (m_axi_awlen),
        .m_axi_awsize   (m_axi_awsize),
        .m_axi_awburst  (m_axi_awburst),
        .m_axi_awprot   (m_axi_awprot),
        .m_axi_awcache  (m_axi_awcache),
        .m_axi_awvalid  (m_axi_awvalid),
        .m_axi_awready  (m_axi_awready),
        .m_axi_wdata    (m_axi_wdata),
        .m_axi_wstrb    (m_axi_wstrb),
        .m_axi_wlast    (m_axi_wlast),
        .m_axi_wvalid   (m_axi_wvalid),
        .m_axi_wready   (m_axi_wready),
        .m_axi_bid      (m_axi_bid),
        .m_axi_bresp    (m_axi_bresp),
        .m_axi_bvalid   (m_axi_bvalid),
        .m_axi_bready   (m_axi_bready),
        .m_axi_arid     (m_axi_arid),
        .m_axi_araddr   (m_axi_araddr),
        .m_axi_arlen    (m_axi_arlen),
        .m_axi_arsize   (m_axi_arsize),
        .m_axi_arburst  (m_axi_arburst),
        .m_axi_arprot   (m_axi_arprot),
        .m_axi_arcache  (m_axi_arcache),
        .m_axi_arvalid  (m_axi_arvalid),
        .m_axi_arready  (m_axi_arready),
        .m_axi_rid      (m_axi_rid),
        .m_axi_rdata    (m_axi_rdata),
        .m_axi_rresp    (m_axi_rresp),
        .m_axi_rlast    (m_axi_rlast),
        .m_axi_rvalid   (m_axi_rvalid),
        .m_axi_rready   (m_axi_rready)
    );

    // ------------------------------------------------------------------
    // Interrupt Controller
    // ------------------------------------------------------------------
    dma_int_ctrl #(
        .NUM_CHANNELS (NUM_CHANNELS)
    ) u_int_ctrl (
        .clk            (axi_clk),
        .rst_n          (axi_rst_n),

        .ch_irq_done    (ch_irq_done),
        .ch_irq_err     (ch_irq_err),
        .dma_ier        (dma_ier_reg),

        .isr_w1c        (isr_w1c),

        .dma_isr        (dma_isr_reg),
        .irq            (irq)
    );

endmodule
