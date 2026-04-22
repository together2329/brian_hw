// =============================================================================
// dma330_axi_master.sv — DMA-330 AXI4 Master Interface
//
// Arbitrates internal DMA requesters (instruction fetch, channel LD/ST,
// manager) onto a shared AXI4 bus.  Supports:
//   - Up to NUM_REQUESTERS internal requesters
//   - Separate read and write channels (full-duplex)
//   - Fixed-priority or round-robin arbitration (to be implemented)
//   - Error capture and reporting
// =============================================================================

module dma330_axi_master #(
    parameter int unsigned DATA_WIDTH      = 32,
    parameter int unsigned ADDR_WIDTH      = 32,
    parameter int unsigned NUM_REQUESTERS  = 6   // 1 instr_fetch + 4 channels + 1 manager
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // AXI4 Master — Write Address Channel (AW)
    // =========================================================================
    output logic [ADDR_WIDTH-1:0]         m_awaddr,
    output logic [7:0]                    m_awlen,
    output logic [2:0]                    m_awsize,
    output logic [1:0]                    m_awburst,
    output logic                          m_awvalid,
    input  logic                          m_awready,

    // =========================================================================
    // AXI4 Master — Write Data Channel (W)
    // =========================================================================
    output logic [DATA_WIDTH-1:0]         m_wdata,
    output logic [(DATA_WIDTH/8)-1:0]     m_wstrb,
    output logic                          m_wlast,
    output logic                          m_wvalid,
    input  logic                          m_wready,

    // =========================================================================
    // AXI4 Master — Write Response Channel (B)
    // =========================================================================
    input  logic [1:0]                    m_bresp,
    input  logic                          m_bvalid,
    output logic                          m_bready,

    // =========================================================================
    // AXI4 Master — Read Address Channel (AR)
    // =========================================================================
    output logic [ADDR_WIDTH-1:0]         m_araddr,
    output logic [7:0]                    m_arlen,
    output logic [2:0]                    m_arsize,
    output logic [1:0]                    m_arburst,
    output logic                          m_arvalid,
    input  logic                          m_arready,

    // =========================================================================
    // AXI4 Master — Read Data Channel (R)
    // =========================================================================
    input  logic [DATA_WIDTH-1:0]         m_rdata,
    input  logic [1:0]                    m_rresp,
    input  logic                          m_rlast,
    input  logic                          m_rvalid,
    output logic                          m_rready,

    // =========================================================================
    // Internal Requester Interface (array of requesters)
    // =========================================================================
    input  dma330_pkg::axi_req_t          req_i    [NUM_REQUESTERS-1:0],
    output dma330_pkg::axi_resp_t         resp_o   [NUM_REQUESTERS-1:0],
    output logic [NUM_REQUESTERS-1:0]     grant_o,

    // =========================================================================
    // Error output
    // =========================================================================
    output logic                          error_o
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Read-Channel FSM States
    // =========================================================================
    typedef enum logic [1:0] {
        R_IDLE = 2'h0,
        R_ADDR = 2'h1,
        R_DATA = 2'h2
    } r_fsm_state_t;

    // =========================================================================
    // Read-Channel Internal Registers
    // =========================================================================
    r_fsm_state_t             r_state;
    logic [CH_ID_WIDTH:0]     r_grant_id;       // winning requester (extended to hold max index)
    logic [7:0]               r_beat_cnt;       // current beat within burst
    logic [7:0]               r_beat_total;     // total beats in this burst (ARLEN+1)
    logic                     r_error_flag;     // sticky error per burst
    logic [ADDR_WIDTH-1:0]    r_araddr_reg;
    logic [7:0]               r_arlen_reg;
    logic [2:0]               r_arsize_reg;

    // =========================================================================
    // Simple priority arbiter for read requests
    // Lowest index = highest priority
    // =========================================================================
    logic [$clog2(NUM_REQUESTERS)-1:0] r_winner;
    logic                               r_any_req;

    always_comb begin : read_arbiter
        r_any_req = 1'b0;
        r_winner  = '0;
        for (int i = NUM_REQUESTERS - 1; i >= 0; i--) begin
            if (req_i[i].valid &&
                (req_i[i].req_type == REQ_INSTR_FETCH ||
                 req_i[i].req_type == REQ_DMALD)) begin
                r_winner  = i[$clog2(NUM_REQUESTERS)-1:0];
                r_any_req = 1'b1;
            end
        end
    end

    // =========================================================================
    // Read-Channel FSM
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : read_fsm
        if (!rst_n) begin
            r_state       <= R_IDLE;
            r_grant_id    <= '0;
            r_beat_cnt    <= 8'h00;
            r_beat_total  <= 8'h00;
            r_error_flag  <= 1'b0;
            r_araddr_reg  <= '0;
            r_arlen_reg   <= 8'h00;
            r_arsize_reg  <= 3'b000;
        end else begin
            case (r_state)
                // -----------------------------------------------------------------
                // R_IDLE: wait for a read request from any requester
                // -----------------------------------------------------------------
                R_IDLE: begin
                    r_error_flag <= 1'b0;
                    r_beat_cnt   <= 8'h00;
                    if (r_any_req) begin
                        // Capture requester info
                        r_araddr_reg <= req_i[r_winner].addr;
                        r_arlen_reg  <= req_i[r_winner].burst_len;
                        r_arsize_reg <= req_i[r_winner].burst_size;
                        r_beat_total <= req_i[r_winner].burst_len;  // ARLEN = beats-1
                        r_grant_id   <= r_winner;
                        r_state      <= R_ADDR;
                    end
                end

                // -----------------------------------------------------------------
                // R_ADDR: drive AR channel, wait for ARREADY handshake
                // -----------------------------------------------------------------
                R_ADDR: begin
                    if (m_arvalid && m_arready) begin
                        // Address phase accepted
                        r_state <= R_DATA;
                    end
                end

                // -----------------------------------------------------------------
                // R_DATA: receive RDATA beats, count until RLAST
                // -----------------------------------------------------------------
                R_DATA: begin
                    if (m_rvalid && m_rready) begin
                        // Capture error from RRESP
                        if (m_rresp != 2'b00) begin  // 2'b00 = OKAY
                            r_error_flag <= 1'b1;
                        end
                        r_beat_cnt <= r_beat_cnt + 8'h01;

                        if (m_rlast) begin
                            r_state <= R_IDLE;
                        end
                    end
                end

                default: r_state <= R_IDLE;
            endcase
        end
    end

    // =========================================================================
    // Read-Channel AXI Signal Driving
    // =========================================================================

    // AR channel — active only in R_ADDR
    assign m_araddr  = r_araddr_reg;
    assign m_arlen   = r_arlen_reg;
    assign m_arsize  = r_arsize_reg;
    assign m_arburst = 2'b01;  // INCR burst
    assign m_arvalid = (r_state == R_ADDR) ? 1'b1 : 1'b0;

    // R channel — accept data in R_DATA, always ready
    assign m_rready  = (r_state == R_DATA) ? 1'b1 : 1'b0;

    // =========================================================================
    // Read-Channel Grant — asserted during entire read transaction
    // =========================================================================
    logic [NUM_REQUESTERS-1:0] r_grant_mask;
    always_comb begin
        r_grant_mask = '0;
        if (r_state != R_IDLE) begin
            r_grant_mask[r_grant_id[$clog2(NUM_REQUESTERS)-1:0]] = 1'b1;
        end
    end

    // =========================================================================
    // Write-Channel Outputs — defaults (implemented in Task 6)
    // =========================================================================
    assign m_awaddr   = {ADDR_WIDTH{1'b0}};
    assign m_awlen    = 8'h00;
    assign m_awsize   = 3'b000;
    assign m_awburst  = 2'b00;
    assign m_awvalid  = 1'b0;

    assign m_wdata    = {DATA_WIDTH{1'b0}};
    assign m_wstrb    = {(DATA_WIDTH/8){1'b0}};
    assign m_wlast    = 1'b0;
    assign m_wvalid   = 1'b0;

    assign m_bready   = 1'b0;

    // =========================================================================
    // Combined Grant & Response
    // =========================================================================
    // TODO: add write grant in Task 6/7
    assign grant_o = r_grant_mask;

    // Generate responses per requester
    genvar g;
    generate
        for (g = 0; g < NUM_REQUESTERS; g++) begin : gen_resp
            always_comb begin
                resp_o[g] = '0;
                if (r_state == R_DATA && r_grant_id[$clog2(NUM_REQUESTERS)-1:0] == g) begin
                    resp_o[g].data  = m_rdata;
                    resp_o[g].last  = m_rlast && m_rvalid && m_rready;
                    resp_o[g].valid = m_rvalid && m_rready;
                    resp_o[g].resp  = m_rresp;
                    resp_o[g].error = r_error_flag;
                end
            end
        end
    endgenerate

    // =========================================================================
    // Error Output
    // =========================================================================
    assign error_o = r_error_flag;

endmodule : dma330_axi_master
