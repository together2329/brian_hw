`default_nettype none

// PL330 TARGET AXI behavior-owner slice.
// Traceability: pl330_target_axi, SSOT sub_modules[6], workflow item RTL_MODULE_PL330_TARGET_AXI.
// Implements cycle_model handshake rules for AXI AW/W/B/AR/R and ordering.axi_outstanding.
module pl330_target_axi #(
    parameter int AXI_DATA_WIDTH        = 32,
    parameter int AXI_ID_WIDTH          = 4,
    parameter int AXI_ADDR_WIDTH        = 32,
    parameter int AXI_STRB_WIDTH        = (AXI_DATA_WIDTH / 8),
    parameter int AXI_OUTSTANDING_LIMIT = 1
) (
    input  logic                         clk,
    input  logic                         rst_n,

    // Internal write-address request stream from PL330 target datapath.
    input  logic                         s_aw_valid,
    output logic                         s_aw_ready,
    input  logic [AXI_ID_WIDTH-1:0]      s_aw_id,
    input  logic [AXI_ADDR_WIDTH-1:0]    s_aw_addr,
    input  logic [7:0]                   s_aw_len,
    input  logic [2:0]                   s_aw_size,
    input  logic [1:0]                   s_aw_burst,

    // Internal write-data stream from PL330 target datapath.
    input  logic                         s_w_valid,
    output logic                         s_w_ready,
    input  logic [AXI_DATA_WIDTH-1:0]    s_w_data,
    input  logic [AXI_STRB_WIDTH-1:0]    s_w_strb,
    input  logic                         s_w_last,

    // Internal write-response stream toward PL330 target datapath.
    output logic                         m_b_valid,
    input  logic                         m_b_ready,
    output logic [AXI_ID_WIDTH-1:0]      m_b_id,
    output logic [1:0]                   m_b_resp,
    output logic                         m_b_fault,

    // Internal read-address request stream from PL330 target datapath.
    input  logic                         s_ar_valid,
    output logic                         s_ar_ready,
    input  logic [AXI_ID_WIDTH-1:0]      s_ar_id,
    input  logic [AXI_ADDR_WIDTH-1:0]    s_ar_addr,
    input  logic [7:0]                   s_ar_len,
    input  logic [2:0]                   s_ar_size,
    input  logic [1:0]                   s_ar_burst,

    // Internal read-data stream toward PL330 target datapath.
    output logic                         m_r_valid,
    input  logic                         m_r_ready,
    output logic [AXI_ID_WIDTH-1:0]      m_r_id,
    output logic [AXI_DATA_WIDTH-1:0]    m_r_data,
    output logic [1:0]                   m_r_resp,
    output logic                         m_r_last,
    output logic                         m_r_fault,

    // External AXI write-address channel.
    output logic [AXI_ID_WIDTH-1:0]      m_axi_awid,
    output logic [AXI_ADDR_WIDTH-1:0]    m_axi_awaddr,
    output logic [7:0]                   m_axi_awlen,
    output logic [2:0]                   m_axi_awsize,
    output logic [1:0]                   m_axi_awburst,
    output logic                         m_axi_awvalid,
    input  logic                         m_axi_awready,

    // External AXI write-data channel.
    output logic [AXI_DATA_WIDTH-1:0]    m_axi_wdata,
    output logic [AXI_STRB_WIDTH-1:0]    m_axi_wstrb,
    output logic                         m_axi_wlast,
    output logic                         m_axi_wvalid,
    input  logic                         m_axi_wready,

    // External AXI write-response channel.
    input  logic [AXI_ID_WIDTH-1:0]      m_axi_bid,
    input  logic [1:0]                   m_axi_bresp,
    input  logic                         m_axi_bvalid,
    output logic                         m_axi_bready,

    // External AXI read-address channel.
    output logic [AXI_ID_WIDTH-1:0]      m_axi_arid,
    output logic [AXI_ADDR_WIDTH-1:0]    m_axi_araddr,
    output logic [7:0]                   m_axi_arlen,
    output logic [2:0]                   m_axi_arsize,
    output logic [1:0]                   m_axi_arburst,
    output logic                         m_axi_arvalid,
    input  logic                         m_axi_arready,

    // External AXI read-data channel.
    input  logic [AXI_ID_WIDTH-1:0]      m_axi_rid,
    input  logic [AXI_DATA_WIDTH-1:0]    m_axi_rdata,
    input  logic [1:0]                   m_axi_rresp,
    input  logic                         m_axi_rlast,
    input  logic                         m_axi_rvalid,
    output logic                         m_axi_rready,

    // Ordering, error, and debug visibility for the PL330 target wrapper.
    output logic                         axi_busy,
    output logic [7:0]                   wr_outstanding,
    output logic [7:0]                   rd_outstanding,
    output logic                         axi_error_sticky
);

    localparam logic [1:0] AXI_RESP_OKAY   = 2'b00;
    localparam logic [1:0] AXI_RESP_EXOKAY = 2'b01;

    logic aw_can_accept;
    logic ar_can_accept;
    logic w_can_accept;
    logic b_can_accept;
    logic r_can_accept;

    logic aw_fire_in;
    logic aw_fire_out;
    logic w_fire_in;
    logic w_fire_out;
    logic b_fire_in;
    logic b_fire_out;
    logic ar_fire_in;
    logic ar_fire_out;
    logic r_fire_in;
    logic r_fire_out;

    logic b_resp_fault_next;
    logic r_resp_fault_next;
    logic any_outstanding;
    logic any_channel_valid;

    always_comb begin
        aw_can_accept = (wr_outstanding < AXI_OUTSTANDING_LIMIT[7:0]) && !m_axi_awvalid;
        ar_can_accept = (rd_outstanding < AXI_OUTSTANDING_LIMIT[7:0]) && !m_axi_arvalid;
        w_can_accept  = !m_axi_wvalid || m_axi_wready;
        b_can_accept  = !m_b_valid || m_b_ready;
        r_can_accept  = !m_r_valid || m_r_ready;

        s_aw_ready    = aw_can_accept;
        s_ar_ready    = ar_can_accept;
        s_w_ready     = w_can_accept;
        m_axi_bready  = b_can_accept;
        m_axi_rready  = r_can_accept;

        aw_fire_in    = s_aw_valid && s_aw_ready;
        aw_fire_out   = m_axi_awvalid && m_axi_awready;
        w_fire_in     = s_w_valid && s_w_ready;
        w_fire_out    = m_axi_wvalid && m_axi_wready;
        b_fire_in     = m_axi_bvalid && m_axi_bready;
        b_fire_out    = m_b_valid && m_b_ready;
        ar_fire_in    = s_ar_valid && s_ar_ready;
        ar_fire_out   = m_axi_arvalid && m_axi_arready;
        r_fire_in     = m_axi_rvalid && m_axi_rready;
        r_fire_out    = m_r_valid && m_r_ready;

        b_resp_fault_next = (m_axi_bresp != AXI_RESP_OKAY) && (m_axi_bresp != AXI_RESP_EXOKAY);
        r_resp_fault_next = (m_axi_rresp != AXI_RESP_OKAY) && (m_axi_rresp != AXI_RESP_EXOKAY);

        any_outstanding   = (wr_outstanding != 8'd0) || (rd_outstanding != 8'd0);
        any_channel_valid = m_axi_awvalid || m_axi_wvalid || m_b_valid || m_axi_arvalid || m_r_valid;
        axi_busy          = any_outstanding || any_channel_valid;
    end

    // AW channel: latch address/control and hold VALID until AXI accepts it.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_axi_awvalid <= 1'b0;
            m_axi_awid    <= {AXI_ID_WIDTH{1'b0}};
            m_axi_awaddr  <= {AXI_ADDR_WIDTH{1'b0}};
            m_axi_awlen   <= 8'h00;
            m_axi_awsize  <= 3'b000;
            m_axi_awburst <= 2'b01;
        end else begin
            if (aw_fire_out) begin
                m_axi_awvalid <= 1'b0;
            end
            if (aw_fire_in) begin
                m_axi_awvalid <= 1'b1;
                m_axi_awid    <= s_aw_id;
                m_axi_awaddr  <= s_aw_addr;
                m_axi_awlen   <= s_aw_len;
                m_axi_awsize  <= s_aw_size;
                m_axi_awburst <= s_aw_burst;
            end
        end
    end

    // W channel: one-beat skid buffer preserving DATA, STRB, and LAST until accepted.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_axi_wvalid <= 1'b0;
            m_axi_wdata  <= {AXI_DATA_WIDTH{1'b0}};
            m_axi_wstrb  <= {AXI_STRB_WIDTH{1'b0}};
            m_axi_wlast  <= 1'b0;
        end else begin
            if (w_fire_out) begin
                m_axi_wvalid <= 1'b0;
            end
            if (w_fire_in) begin
                m_axi_wvalid <= 1'b1;
                m_axi_wdata  <= s_w_data;
                m_axi_wstrb  <= s_w_strb;
                m_axi_wlast  <= s_w_last;
            end
        end
    end

    // B channel: return real AXI response to PL330 logic and latch sticky errors.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_b_valid        <= 1'b0;
            m_b_id           <= {AXI_ID_WIDTH{1'b0}};
            m_b_resp         <= AXI_RESP_OKAY;
            m_b_fault        <= 1'b0;
            axi_error_sticky <= 1'b0;
        end else begin
            if (b_fire_out) begin
                m_b_valid <= 1'b0;
            end
            if (b_fire_in) begin
                m_b_valid        <= 1'b1;
                m_b_id           <= m_axi_bid;
                m_b_resp         <= m_axi_bresp;
                m_b_fault        <= b_resp_fault_next;
                axi_error_sticky <= axi_error_sticky || b_resp_fault_next;
            end
            if (r_fire_in) begin
                axi_error_sticky <= axi_error_sticky || r_resp_fault_next;
            end
        end
    end

    // AR channel: latch address/control and hold VALID until AXI accepts it.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_axi_arvalid <= 1'b0;
            m_axi_arid    <= {AXI_ID_WIDTH{1'b0}};
            m_axi_araddr  <= {AXI_ADDR_WIDTH{1'b0}};
            m_axi_arlen   <= 8'h00;
            m_axi_arsize  <= 3'b000;
            m_axi_arburst <= 2'b01;
        end else begin
            if (ar_fire_out) begin
                m_axi_arvalid <= 1'b0;
            end
            if (ar_fire_in) begin
                m_axi_arvalid <= 1'b1;
                m_axi_arid    <= s_ar_id;
                m_axi_araddr  <= s_ar_addr;
                m_axi_arlen   <= s_ar_len;
                m_axi_arsize  <= s_ar_size;
                m_axi_arburst <= s_ar_burst;
            end
        end
    end

    // R channel: skid-buffer read data and response so backpressure cannot drop beats.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_r_valid <= 1'b0;
            m_r_id    <= {AXI_ID_WIDTH{1'b0}};
            m_r_data  <= {AXI_DATA_WIDTH{1'b0}};
            m_r_resp  <= AXI_RESP_OKAY;
            m_r_last  <= 1'b0;
            m_r_fault <= 1'b0;
        end else begin
            if (r_fire_out) begin
                m_r_valid <= 1'b0;
            end
            if (r_fire_in) begin
                m_r_valid <= 1'b1;
                m_r_id    <= m_axi_rid;
                m_r_data  <= m_axi_rdata;
                m_r_resp  <= m_axi_rresp;
                m_r_last  <= m_axi_rlast;
                m_r_fault <= r_resp_fault_next;
            end
        end
    end

    // Outstanding ordering counters. AW acceptance creates a write transaction; B completes it.
    // AR acceptance creates a read transaction; the accepted R beat with LAST completes it.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_outstanding <= 8'd0;
            rd_outstanding <= 8'd0;
        end else begin
            case ({aw_fire_out, b_fire_in})
                2'b10: wr_outstanding <= wr_outstanding + 8'd1;
                2'b01: wr_outstanding <= (wr_outstanding != 8'd0) ? (wr_outstanding - 8'd1) : 8'd0;
                default: wr_outstanding <= wr_outstanding;
            endcase

            case ({ar_fire_out, (r_fire_in && m_axi_rlast)})
                2'b10: rd_outstanding <= rd_outstanding + 8'd1;
                2'b01: rd_outstanding <= (rd_outstanding != 8'd0) ? (rd_outstanding - 8'd1) : 8'd0;
                default: rd_outstanding <= rd_outstanding;
            endcase
        end
    end

endmodule

`default_nettype wire
