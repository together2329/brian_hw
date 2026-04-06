// =============================================================================
// Module: dma_top
// Description: Simple AXI4-Lite DMA Controller
//              - Memory-to-memory DMA transfers
//              - Programmable source/destination addresses
//              - Configurable transfer length
//              - Interrupt on completion
//              - Supports single and burst transfers
// =============================================================================

module dma_top #(
    parameter DATA_WIDTH    = 32,
    parameter ADDR_WIDTH    = 32,
    parameter MAX_BURST_LEN = 16,
    parameter FIFO_DEPTH    = 8
)(
    // Clock and Reset
    input  logic                     clk,
    input  logic                     rst_n,

    // AXI4-Lite Slave Interface (Register Access)
    input  logic [ADDR_WIDTH-1:0]    s_axi_awaddr,
    input  logic                     s_axi_awvalid,
    output logic                     s_axi_awready,
    input  logic [DATA_WIDTH-1:0]    s_axi_wdata,
    input  logic [(DATA_WIDTH/8)-1:0] s_axi_wstrb,
    input  logic                     s_axi_wvalid,
    output logic                     s_axi_wready,
    output logic [1:0]               s_axi_bresp,
    output logic                     s_axi_bvalid,
    input  logic                     s_axi_bready,
    input  logic [ADDR_WIDTH-1:0]    s_axi_araddr,
    input  logic                     s_axi_arvalid,
    output logic                     s_axi_arready,
    output logic [DATA_WIDTH-1:0]    s_axi_rdata,
    output logic [1:0]               s_axi_rresp,
    output logic                     s_axi_rvalid,
    input  logic                     s_axi_rready,

    // AXI4 Master Interface (DMA Read - from source)
    output logic [ADDR_WIDTH-1:0]    m_axi_araddr,
    output logic [7:0]               m_axi_arlen,
    output logic [2:0]               m_axi_arsize,
    output logic [1:0]               m_axi_arburst,
    output logic                     m_axi_arvalid,
    input  logic                     m_axi_arready,
    input  logic [DATA_WIDTH-1:0]    m_axi_rdata,
    input  logic [1:0]               m_axi_rresp,
    input  logic                     m_axi_rlast,
    input  logic                     m_axi_rvalid,
    output logic                     m_axi_rready,

    // AXI4 Master Interface (DMA Write - to destination)
    output logic [ADDR_WIDTH-1:0]    m_axi_awaddr,
    output logic [7:0]               m_axi_awlen,
    output logic [2:0]               m_axi_awsize,
    output logic [1:0]               m_axi_awburst,
    output logic                     m_axi_awvalid,
    input  logic                     m_axi_awready,
    output logic [DATA_WIDTH-1:0]    m_axi_wdata,
    output logic [(DATA_WIDTH/8)-1:0] m_axi_wstrb,
    output logic                     m_axi_wlast,
    output logic                     m_axi_wvalid,
    input  logic                     m_axi_wready,
    input  logic [1:0]               m_axi_bresp,
    input  logic                     m_axi_bvalid,
    output logic                     m_axi_bready,

    // Interrupt
    output logic                     dma_irq
);

    // =========================================================================
    // Register Map (offset addresses)
    // =========================================================================
    localparam ADDR_SRC_LO   = 4'h0;  // Source address [31:0]
    localparam ADDR_SRC_HI   = 4'h4;  // Source address [63:32] (reserved for 64-bit)
    localparam ADDR_DST_LO   = 4'h8;  // Destination address [31:0]
    localparam ADDR_DST_HI   = 4'hC;  // Destination address [63:32] (reserved)
    localparam ADDR_XFER_LEN = 4'h10; // Transfer length in bytes
    localparam ADDR_CTRL     = 4'h14; // Control register
    localparam ADDR_STATUS   = 4'h18; // Status register
    localparam ADDR_INT_STAT = 4'h1C; // Interrupt status register

    // =========================================================================
    // Control/Status Register Bits
    // =========================================================================
    localparam CTRL_START      = 0;
    localparam CTRL_INT_EN     = 1;
    localparam CTRL_SOFT_RESET = 2;

    localparam STATUS_BUSY     = 0;
    localparam STATUS_DONE     = 1;
    localparam STATUS_ERR      = 2;

    // =========================================================================
    // Internal Registers
    // =========================================================================
    logic [ADDR_WIDTH-1:0] src_addr_reg;
    logic [ADDR_WIDTH-1:0] dst_addr_reg;
    logic [ADDR_WIDTH-1:0] xfer_len_reg;
    logic                  int_en_reg;
    logic                  soft_reset_reg;

    // Status signals
    logic                  dma_busy;
    logic                  dma_done;
    logic                  dma_error;
    logic                  int_pending;

    // =========================================================================
    // DMA FSM States
    // =========================================================================
    typedef enum logic [2:0] {
        DMA_IDLE    = 3'd0,
        DMA_READ    = 3'd1,
        DMA_WRITE   = 3'd2,
        DMA_WAIT_WR = 3'd3,
        DMA_DONE_ST = 3'd4,
        DMA_ERROR_ST= 3'd5
    } dma_state_t;

    dma_state_t dma_state, dma_state_next;

    // Transfer counters
    logic [ADDR_WIDTH-1:0] src_addr_cnt;
    logic [ADDR_WIDTH-1:0] dst_addr_cnt;
    logic [ADDR_WIDTH-1:0] bytes_remaining;

    // Internal FIFO for read data
    logic [DATA_WIDTH-1:0] fifo_data  [0:FIFO_DEPTH-1];
    logic [$clog2(FIFO_DEPTH):0] fifo_wptr;
    logic [$clog2(FIFO_DEPTH):0] fifo_rptr;
    logic [$clog2(FIFO_DEPTH):0] fifo_count;
    logic                  fifo_full;
    logic                  fifo_empty;
    logic                  fifo_wr_en;
    logic                  fifo_rd_en;
    logic [DATA_WIDTH-1:0] fifo_dout;

    // AXI handshake internal signals
    logic                  rd_req;
    logic                  wr_req;

    // =========================================================================
    // FIFO Logic
    // =========================================================================
    assign fifo_full  = (fifo_count == FIFO_DEPTH);
    assign fifo_empty = (fifo_count == 0);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fifo_wptr  <= '0;
            fifo_rptr  <= '0;
            fifo_count <= '0;
        end else begin
            // Write to FIFO
            if (fifo_wr_en && !fifo_full) begin
                fifo_data[fifo_wptr[$clog2(FIFO_DEPTH)-1:0]] <= m_axi_rdata;
                fifo_wptr  <= fifo_wptr + 1;
            end
            // Read from FIFO
            if (fifo_rd_en && !fifo_empty) begin
                fifo_rptr <= fifo_rptr + 1;
            end
            // Update count
            case ({fifo_wr_en && !fifo_full, fifo_rd_en && !fifo_empty})
                2'b10: fifo_count <= fifo_count + 1;
                2'b01: fifo_count <= fifo_count - 1;
                default: fifo_count <= fifo_count;
            endcase
        end
    end

    assign fifo_dout = fifo_data[fifo_rptr[$clog2(FIFO_DEPTH)-1:0]];

    // =========================================================================
    // AXI4-Lite Slave Interface - Write Path
    // =========================================================================
    logic [2:0] axi_aw_state;
    logic [ADDR_WIDTH-1:0] awaddr_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_awready <= 1'b0;
            s_axi_wready  <= 1'b0;
            s_axi_bvalid  <= 1'b0;
            s_axi_bresp   <= 2'b00;
            awaddr_reg    <= '0;
            axi_aw_state  <= 3'd0;
        end else begin
            case (axi_aw_state)
                3'd0: begin // Wait for AWVALID
                    s_axi_awready <= 1'b1;
                    s_axi_wready  <= 1'b0;
                    s_axi_bvalid  <= 1'b0;
                    if (s_axi_awvalid) begin
                        awaddr_reg    <= s_axi_awaddr;
                        s_axi_awready <= 1'b0;
                        axi_aw_state  <= 3'd1;
                    end
                end
                3'd1: begin // Assert WREADY
                    s_axi_wready <= 1'b1;
                    axi_aw_state <= 3'd2;
                end
                3'd2: begin // Wait for WVALID
                    if (s_axi_wvalid) begin
                        s_axi_wready <= 1'b0;
                        axi_aw_state <= 3'd3;
                    end
                end
                3'd3: begin // Assert BVALID
                    s_axi_bvalid <= 1'b1;
                    s_axi_bresp  <= 2'b00;
                    axi_aw_state <= 3'd4;
                end
                3'd4: begin // Wait for BREADY
                    if (s_axi_bready) begin
                        s_axi_bvalid <= 1'b0;
                        axi_aw_state <= 3'd0;
                    end
                end
                default: axi_aw_state <= 3'd0;
            endcase
        end
    end

    // Register write logic
    logic [DATA_WIDTH-1:0] reg_wdata;
    logic                  reg_wr_en;

    assign reg_wr_en  = (axi_aw_state == 3'd2) && s_axi_wvalid;
    assign reg_wdata  = s_axi_wdata;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            src_addr_reg   <= '0;
            dst_addr_reg   <= '0;
            xfer_len_reg   <= '0;
            int_en_reg     <= 1'b0;
            soft_reset_reg <= 1'b0;
        end else if (soft_reset_reg) begin
            src_addr_reg   <= '0;
            dst_addr_reg   <= '0;
            xfer_len_reg   <= '0;
            int_en_reg     <= 1'b0;
            soft_reset_reg <= 1'b0;
        end else if (reg_wr_en && !dma_busy) begin
            case (awaddr_reg[3:0])
                ADDR_SRC_LO[3:0]:   src_addr_reg <= reg_wdata;
                ADDR_DST_LO[3:0]:   dst_addr_reg <= reg_wdata;
                ADDR_XFER_LEN[3:0]: xfer_len_reg <= reg_wdata;
                ADDR_CTRL[3:0]: begin
                    int_en_reg     <= reg_wdata[CTRL_INT_EN];
                    soft_reset_reg <= reg_wdata[CTRL_SOFT_RESET];
                end
                default: ;
            endcase
        end
    end

    // =========================================================================
    // AXI4-Lite Slave Interface - Read Path
    // =========================================================================
    logic [2:0] axi_ar_state;
    logic [ADDR_WIDTH-1:0] araddr_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_arready <= 1'b0;
            s_axi_rvalid  <= 1'b0;
            s_axi_rresp   <= 2'b00;
            s_axi_rdata   <= '0;
            araddr_reg    <= '0;
            axi_ar_state  <= 3'd0;
        end else begin
            case (axi_ar_state)
                3'd0: begin // Wait for ARVALID
                    s_axi_arready <= 1'b1;
                    s_axi_rvalid  <= 1'b0;
                    if (s_axi_arvalid) begin
                        araddr_reg    <= s_axi_araddr;
                        s_axi_arready <= 1'b0;
                        axi_ar_state  <= 3'd1;
                    end
                end
                3'd1: begin // Assert RVALID, drive RDATA
                    s_axi_rvalid <= 1'b1;
                    s_axi_rresp  <= 2'b00;
                    case (araddr_reg[3:0])
                        ADDR_SRC_LO[3:0]:   s_axi_rdata <= src_addr_reg;
                        ADDR_DST_LO[3:0]:   s_axi_rdata <= dst_addr_reg;
                        ADDR_XFER_LEN[3:0]: s_axi_rdata <= xfer_len_reg;
                        ADDR_CTRL[3:0]:     s_axi_rdata <= {28'd0, soft_reset_reg, int_en_reg, 1'b0};
                        ADDR_STATUS[3:0]:   s_axi_rdata <= {28'd0, dma_error, dma_done, dma_busy};
                        ADDR_INT_STAT[3:0]: s_axi_rdata <= {31'd0, int_pending};
                        default:            s_axi_rdata <= '0;
                    endcase
                    axi_ar_state <= 3'd2;
                end
                3'd2: begin // Wait for RREADY
                    if (s_axi_rready) begin
                        s_axi_rvalid <= 1'b0;
                        axi_ar_state <= 3'd0;
                    end
                end
                default: axi_ar_state <= 3'd0;
            endcase
        end
    end

    // =========================================================================
    // DMA Start Detection
    // =========================================================================
    logic start_pulse;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            start_pulse <= 1'b0;
        else if (reg_wr_en && !dma_busy && (awaddr_reg[3:0] == ADDR_CTRL[3:0]) && reg_wdata[CTRL_START])
            start_pulse <= 1'b1;
        else
            start_pulse <= 1'b0;
    end

    // =========================================================================
    // DMA FSM - Sequential
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dma_state     <= DMA_IDLE;
            src_addr_cnt  <= '0;
            dst_addr_cnt  <= '0;
            bytes_remaining <= '0;
        end else begin
            dma_state <= dma_state_next;
            case (dma_state)
                DMA_IDLE: begin
                    if (start_pulse) begin
                        src_addr_cnt    <= src_addr_reg;
                        dst_addr_cnt    <= dst_addr_reg;
                        bytes_remaining <= xfer_len_reg;
                    end
                end
                DMA_READ: begin
                    if (m_axi_arready && m_axi_arvalid) begin
                        src_addr_cnt <= src_addr_cnt + (DATA_WIDTH/8);
                        bytes_remaining <= bytes_remaining - (DATA_WIDTH/8);
                    end
                end
                DMA_WRITE: begin
                    if (m_axi_wready && m_axi_wvalid) begin
                        dst_addr_cnt <= dst_addr_cnt + (DATA_WIDTH/8);
                    end
                end
                default: ;
            endcase
        end
    end

    // =========================================================================
    // DMA FSM - Combinational
    // =========================================================================
    always_comb begin
        dma_state_next = dma_state;
        rd_req = 1'b0;
        wr_req = 1'b0;

        case (dma_state)
            DMA_IDLE: begin
                if (start_pulse && xfer_len_reg > 0) begin
                    dma_state_next = DMA_READ;
                end
            end
            DMA_READ: begin
                rd_req = 1'b1;
                if (bytes_remaining == 0) begin
                    // Always go to WRITE to drain FIFO (data may be
                    // arriving this cycle but count not yet updated)
                    dma_state_next = DMA_WRITE;
                end else if (fifo_count >= FIFO_DEPTH - 1) begin
                    dma_state_next = DMA_WAIT_WR;
                end
            end
            DMA_WAIT_WR: begin
                if (fifo_empty && bytes_remaining == 0)
                    dma_state_next = DMA_DONE_ST;
                else if (!fifo_full)
                    dma_state_next = DMA_READ;
            end
            DMA_WRITE: begin
                wr_req = 1'b1;
                if (fifo_empty) begin
                    if (bytes_remaining == 0)
                        dma_state_next = DMA_DONE_ST;
                    else
                        dma_state_next = DMA_READ;
                end
            end
            DMA_DONE_ST: begin
                dma_state_next = DMA_IDLE;
            end
            DMA_ERROR_ST: begin
                dma_state_next = DMA_IDLE;
            end
            default: dma_state_next = DMA_IDLE;
        endcase
    end

    // =========================================================================
    // FIFO control signals
    // =========================================================================
    assign fifo_wr_en = (dma_state == DMA_READ) && m_axi_rvalid && m_axi_rready;
    assign fifo_rd_en = (dma_state == DMA_WRITE) && m_axi_wvalid && m_axi_wready;

    // =========================================================================
    // AXI4 Master Read Interface
    // =========================================================================
    assign m_axi_araddr  = src_addr_cnt;
    assign m_axi_arlen   = 8'd0;  // Single transfer per phase
    assign m_axi_arsize  = $clog2(DATA_WIDTH/8);
    assign m_axi_arburst = 2'b01; // INCR
    assign m_axi_arvalid = rd_req && !fifo_full;
    assign m_axi_rready  = (dma_state == DMA_READ) && !fifo_full;

    // =========================================================================
    // AXI4 Master Write Interface
    // =========================================================================
    assign m_axi_awaddr  = dst_addr_cnt;
    assign m_axi_awlen   = 8'd0;
    assign m_axi_awsize  = $clog2(DATA_WIDTH/8);
    assign m_axi_awburst = 2'b01; // INCR
    assign m_axi_awvalid = wr_req;
    assign m_axi_wdata   = fifo_dout;
    assign m_axi_wstrb   = {(DATA_WIDTH/8){1'b1}};
    assign m_axi_wlast   = (bytes_remaining == 0) && fifo_count == 1;
    assign m_axi_wvalid  = wr_req && !fifo_empty;
    assign m_axi_bready  = 1'b1;

    // =========================================================================
    // Status & Interrupt
    // =========================================================================
    assign dma_busy  = (dma_state != DMA_IDLE);
    assign dma_error = (dma_state == DMA_ERROR_ST) ||
                       (m_axi_rresp == 2'b10) || (m_axi_rresp == 2'b11) ||
                       (m_axi_bresp == 2'b10) || (m_axi_bresp == 2'b11);

    // Latch done flag so polling can observe it
    logic dma_done_latched;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            dma_done_latched <= 1'b0;
        else if (dma_state == DMA_DONE_ST)
            dma_done_latched <= 1'b1;
        else if (start_pulse)
            dma_done_latched <= 1'b0;
    end
    assign dma_done = dma_done_latched;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            int_pending <= 1'b0;
        else if (dma_done && int_en_reg)
            int_pending <= 1'b1;
        else if (reg_wr_en && (awaddr_reg[3:0] == ADDR_INT_STAT[3:0]))
            int_pending <= 1'b0;  // Clear on write
    end

    assign dma_irq = int_pending && int_en_reg;

endmodule
