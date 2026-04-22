`default_nettype none
module dma_axi_master #(
    parameter int DATA_WIDTH = 32,
    parameter int ADDR_WIDTH = 32,
    parameter int ID_WIDTH   = 4
)(
    input  logic                      clk,
    input  logic                      rst_n,

    // Read request from channel
    input  logic                      rd_req,
    input  logic [ID_WIDTH-1:0]       rd_id,
    input  logic [ADDR_WIDTH-1:0]     rd_addr,
    input  logic [7:0]                rd_len,
    input  logic [2:0]                rd_size,
    input  logic [1:0]                rd_burst,
    input  logic [2:0]                rd_prot,
    input  logic [3:0]                rd_cache,

    // Read response to channel
    output logic                      rd_data_valid,
    output logic [DATA_WIDTH-1:0]     rd_data,
    output logic [1:0]                rd_resp,
    output logic                      rd_last,
    output logic [ID_WIDTH-1:0]       rd_data_id,

    // Write request from channel
    input  logic                      wr_req,
    input  logic [ID_WIDTH-1:0]       wr_id,
    input  logic [ADDR_WIDTH-1:0]     wr_addr,
    input  logic [7:0]                wr_len,
    input  logic [2:0]                wr_size,
    input  logic [1:0]                wr_burst,
    input  logic [2:0]                wr_prot,
    input  logic [3:0]                wr_cache,
    input  logic [DATA_WIDTH-1:0]     wr_data,
    input  logic [DATA_WIDTH/8-1:0]   wr_strb,
    input  logic                      wr_last,

    // Write response to channel
    output logic                      wr_resp_valid,
    output logic [ID_WIDTH-1:0]       wr_resp_id,
    output logic [1:0]                wr_resp,

    // AXI4 Master Read Address Channel
    output logic [ID_WIDTH-1:0]       m_axi_arid,
    output logic [ADDR_WIDTH-1:0]     m_axi_araddr,
    output logic [7:0]                m_axi_arlen,
    output logic [2:0]                m_axi_arsize,
    output logic [1:0]                m_axi_arburst,
    output logic [2:0]                m_axi_arprot,
    output logic [3:0]                m_axi_arcache,
    output logic                      m_axi_arvalid,
    input  logic                      m_axi_arready,

    // AXI4 Master Read Data Channel
    input  logic [ID_WIDTH-1:0]       m_axi_rid,
    input  logic [DATA_WIDTH-1:0]     m_axi_rdata,
    input  logic [1:0]                m_axi_rresp,
    input  logic                      m_axi_rlast,
    input  logic                      m_axi_rvalid,
    output logic                      m_axi_rready,

    // AXI4 Master Write Address Channel
    output logic [ID_WIDTH-1:0]       m_axi_awid,
    output logic [ADDR_WIDTH-1:0]     m_axi_awaddr,
    output logic [7:0]                m_axi_awlen,
    output logic [2:0]                m_axi_awsize,
    output logic [1:0]                m_axi_awburst,
    output logic [2:0]                m_axi_awprot,
    output logic [3:0]                m_axi_awcache,
    output logic                      m_axi_awvalid,
    input  logic                      m_axi_awready,

    // AXI4 Master Write Data Channel
    output logic [DATA_WIDTH-1:0]     m_axi_wdata,
    output logic [DATA_WIDTH/8-1:0]   m_axi_wstrb,
    output logic                      m_axi_wlast,
    output logic                      m_axi_wvalid,
    input  logic                      m_axi_wready,

    // AXI4 Master Write Response Channel
    input  logic [ID_WIDTH-1:0]       m_axi_bid,
    input  logic [1:0]                m_axi_bresp,
    input  logic                      m_axi_bvalid,
    output logic                      m_axi_bready
);

    // ========================================================================
    // Read Address Channel
    // ========================================================================
    logic                      rd_addr_pending;
    logic                      rd_prev_req;
    logic [ID_WIDTH-1:0]       rd_addr_id_q;
    logic [ADDR_WIDTH-1:0]     rd_addr_q;
    logic [7:0]                rd_len_q;
    logic [2:0]                rd_size_q;
    logic [1:0]                rd_burst_q;
    logic [2:0]                rd_prot_q;
    logic [3:0]                rd_cache_q;

    // Track whether current read burst data is fully received
    logic                      rd_burst_done;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rd_burst_done <= 1'b0;
        else if (rd_data_valid && rd_last)
            rd_burst_done <= 1'b1;
        else if (rd_addr_pending && m_axi_arready)
            rd_burst_done <= 1'b0;
    end

    // Detect rising edge of rd_req
    wire rd_rising = rd_req && !rd_prev_req;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_addr_pending <= 1'b0;
            rd_prev_req     <= 1'b0;
        end else begin
            rd_prev_req <= rd_req;
            // Accept on rising edge when no pending address
            if (rd_rising && !rd_addr_pending) begin
                rd_addr_pending <= 1'b1;
            end
            // Clear when slave accepts
            if (rd_addr_pending && m_axi_arready) begin
                rd_addr_pending <= 1'b0;
            end
        end
    end

    // Latch read address parameters on request acceptance
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_addr_id_q   <= '0;
            rd_addr_q      <= '0;
            rd_len_q       <= '0;
            rd_size_q      <= '0;
            rd_burst_q     <= '0;
            rd_prot_q      <= '0;
            rd_cache_q     <= '0;
        end else if (rd_rising && !rd_addr_pending) begin
            rd_addr_id_q   <= rd_id;
            rd_addr_q      <= rd_addr;
            rd_len_q       <= rd_len;
            rd_size_q      <= rd_size;
            rd_burst_q     <= rd_burst;
            rd_prot_q      <= rd_prot;
            rd_cache_q     <= rd_cache;
        end
    end

    assign m_axi_arvalid  = rd_addr_pending;
    assign m_axi_arid     = rd_addr_id_q;
    assign m_axi_araddr   = rd_addr_q;
    assign m_axi_arlen    = rd_len_q;
    assign m_axi_arsize   = rd_size_q;
    assign m_axi_arburst  = rd_burst_q;
    assign m_axi_arprot   = rd_prot_q;
    assign m_axi_arcache  = rd_cache_q;

    // ========================================================================
    // Read Data Channel - pass-through
    // ========================================================================
    assign m_axi_rready   = 1'b1; // Always accept read data
    assign rd_data_valid  = m_axi_rvalid;
    assign rd_data        = m_axi_rdata;
    assign rd_resp        = m_axi_rresp;
    assign rd_last        = m_axi_rlast;
    assign rd_data_id     = m_axi_rid;

    // ========================================================================
    // Write Address Channel
    // ========================================================================
    logic                      wr_addr_pending;
    logic                      wr_prev_req;
    logic [ID_WIDTH-1:0]       wr_addr_id_q;
    logic [ADDR_WIDTH-1:0]     wr_addr_q;
    logic [7:0]                wr_len_q;
    logic [2:0]                wr_size_q;
    logic [1:0]                wr_burst_q;
    logic [2:0]                wr_prot_q;
    logic [3:0]                wr_cache_q;

    // Detect rising edge of wr_req
    wire wr_rising = wr_req && !wr_prev_req;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_addr_pending <= 1'b0;
            wr_prev_req     <= 1'b0;
        end else begin
            wr_prev_req <= wr_req;
            // Accept on rising edge when no pending address
            if (wr_rising && !wr_addr_pending) begin
                wr_addr_pending <= 1'b1;
            end
            // Clear when slave accepts
            if (wr_addr_pending && m_axi_awready) begin
                wr_addr_pending <= 1'b0;
            end
        end
    end

    // Latch write address parameters on request acceptance
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_addr_id_q   <= '0;
            wr_addr_q      <= '0;
            wr_len_q       <= '0;
            wr_size_q      <= '0;
            wr_burst_q     <= '0;
            wr_prot_q      <= '0;
            wr_cache_q     <= '0;
        end else if (wr_rising && !wr_addr_pending) begin
            wr_addr_id_q   <= wr_id;
            wr_addr_q      <= wr_addr;
            wr_len_q       <= wr_len;
            wr_size_q      <= wr_size;
            wr_burst_q     <= wr_burst;
            wr_prot_q      <= wr_prot;
            wr_cache_q     <= wr_cache;
        end
    end

    assign m_axi_awvalid  = wr_addr_pending;
    assign m_axi_awid     = wr_addr_id_q;
    assign m_axi_awaddr   = wr_addr_q;
    assign m_axi_awlen    = wr_len_q;
    assign m_axi_awsize   = wr_size_q;
    assign m_axi_awburst  = wr_burst_q;
    assign m_axi_awprot   = wr_prot_q;
    assign m_axi_awcache  = wr_cache_q;

    // ========================================================================
    // Write Data Channel
    // ========================================================================
    // WVALID should only be asserted after AW channel handshake is done.
    // Track AW handshake completion with a registered flag.
    logic wr_aw_done;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            wr_aw_done <= 1'b0;
        else if (wr_addr_pending && m_axi_awready)
            wr_aw_done <= 1'b1;
        else if (!wr_req)
            wr_aw_done <= 1'b0;
    end

    assign m_axi_wdata    = wr_data;
    assign m_axi_wstrb    = wr_strb;
    assign m_axi_wlast    = wr_last;
    assign m_axi_wvalid   = wr_req && wr_aw_done;

    // ========================================================================
    // Write Response Channel - pass-through
    // ========================================================================
    assign m_axi_bready   = 1'b1; // Always accept write responses
    assign wr_resp_valid  = m_axi_bvalid;
    assign wr_resp_id     = m_axi_bid;
    assign wr_resp        = m_axi_bresp;

endmodule
