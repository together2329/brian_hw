// =============================================================================
// dma330_instr_cache.sv — DMA-330 Instruction Cache
//
// Simple direct-mapped instruction cache for the DMA-330 controller.
// Caches instruction bytes fetched from AXI to reduce bus traffic when
// the DMA thread loops over the same instruction stream.
//
// Features:
//   - Direct-mapped (1-way set associative)
//   - Parameterized cache lines and line size
//   - Lookup interface for the instruction fetch unit
//   - Fill interface for cache line refills via AXI
// =============================================================================

module dma330_instr_cache #(
    parameter int unsigned CACHE_LINES = 16,
    parameter int unsigned LINE_SIZE   = 64,    // bytes per cache line
    parameter int unsigned ADDR_WIDTH  = 32
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // Lookup Interface (from instruction fetch unit)
    // =========================================================================
    input  logic [ADDR_WIDTH-1:0]         lookup_addr,
    input  logic                          lookup_valid,
    output logic                          lookup_ready,
    output logic                          lookup_hit,
    output logic [LINE_SIZE*8-1:0]        lookup_data,

    // =========================================================================
    // Fill Interface (for cache line refill)
    // =========================================================================
    input  logic [ADDR_WIDTH-1:0]         fill_addr,
    input  logic [LINE_SIZE*8-1:0]        fill_data,
    input  logic                          fill_valid,
    output logic                          fill_ready,

    // =========================================================================
    // AXI Fetch Request (to AXI master for line fills)
    // =========================================================================
    output dma330_pkg::axi_req_t          axi_req_o,
    input  dma330_pkg::axi_resp_t         axi_resp_i
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Derived Constants
    // =========================================================================
    localparam int unsigned LINE_SIZE_LOG2 = $clog2(LINE_SIZE);
    localparam int unsigned CACHE_LOG2     = $clog2(CACHE_LINES);
    localparam int unsigned TAG_WIDTH      = ADDR_WIDTH - LINE_SIZE_LOG2 - CACHE_LOG2;
    localparam int unsigned LINE_WIDTH     = LINE_SIZE * 8;  // bits

    // =========================================================================
    // Address Decomposition — Index / Tag extraction
    // =========================================================================
    logic [CACHE_LOG2-1:0]     lookup_index;
    logic [CACHE_LOG2-1:0]     fill_index;
    logic [TAG_WIDTH-1:0]      lookup_tag;
    logic [TAG_WIDTH-1:0]      fill_tag;

    // index = addr[LINE_SIZE_LOG2+CACHE_LOG2-1 : LINE_SIZE_LOG2]
    assign lookup_index = lookup_addr[LINE_SIZE_LOG2 + CACHE_LOG2 - 1 : LINE_SIZE_LOG2];
    assign fill_index   = fill_addr  [LINE_SIZE_LOG2 + CACHE_LOG2 - 1 : LINE_SIZE_LOG2];

    // tag = addr[ADDR_WIDTH-1 : LINE_SIZE_LOG2+CACHE_LOG2]
    assign lookup_tag   = lookup_addr[ADDR_WIDTH - 1 : LINE_SIZE_LOG2 + CACHE_LOG2];
    assign fill_tag     = fill_addr  [ADDR_WIDTH - 1 : LINE_SIZE_LOG2 + CACHE_LOG2];

    // =========================================================================
    // SRAM Data Store — one line per entry
    // =========================================================================
    logic [LINE_WIDTH-1:0] data_store [0:CACHE_LINES-1];

    // =========================================================================
    // Tag Store — valid bit + tag per entry
    // =========================================================================
    logic                   tag_valid [0:CACHE_LINES-1];
    logic [TAG_WIDTH-1:0]   tag_addr  [0:CACHE_LINES-1];

    // =========================================================================
    // Lookup — combinational hit/miss detection
    // =========================================================================
    assign lookup_hit   = tag_valid[lookup_index] &&
                          (tag_addr[lookup_index] == lookup_tag);

    assign lookup_data  = data_store[lookup_index];

    assign lookup_ready = 1'b1;  // Always ready to accept lookups

    // =========================================================================
    // Fill — write cache line on valid fill
    // =========================================================================
    assign fill_ready = 1'b1;  // Always ready to accept fills

    always_ff @(posedge clk or negedge rst_n) begin : fill_write
        if (!rst_n) begin
            for (int i = 0; i < CACHE_LINES; i++) begin
                tag_valid[i] <= 1'b0;
                tag_addr[i]  <= '0;
                data_store[i] <= '0;
            end
        end else begin
            if (fill_valid) begin
                data_store[fill_index] <= fill_data;
                tag_addr[fill_index]   <= fill_tag;
                tag_valid[fill_index]  <= 1'b1;
            end
        end
    end

    // =========================================================================
    // AXI Fetch Request — default (full implementation in later task)
    // =========================================================================
    assign axi_req_o = '0;

endmodule : dma330_instr_cache
