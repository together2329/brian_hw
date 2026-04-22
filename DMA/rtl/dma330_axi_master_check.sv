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
    // Skeleton — wire assignments TBD in later tasks
    // =========================================================================
    assign error_o = 1'b0;

    // Default AXI outputs (idle)
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

    assign m_araddr   = {ADDR_WIDTH{1'b0}};
    assign m_arlen    = 8'h00;
    assign m_arsize   = 3'b000;
    assign m_arburst  = 2'b00;
    assign m_arvalid  = 1'b0;

    assign m_rready   = 1'b0;

    // Default grant and response
    assign grant_o    = {NUM_REQUESTERS{1'b0}};

    // Generate default responses for all requesters
    genvar g;
    generate
        for (g = 0; g < NUM_REQUESTERS; g++) begin : gen_default_resp
            assign resp_o[g] = '0;
        end
    endgenerate

endmodule : dma330_axi_master
