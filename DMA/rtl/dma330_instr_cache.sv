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
    // Cache FSM States
    // =========================================================================
    typedef enum logic [2:0] {
        CACHE_IDLE       = 3'h0,
        CACHE_LOOKUP     = 3'h1,
        CACHE_HIT_RETURN = 3'h2,
        CACHE_MISS_FETCH = 3'h3,
        CACHE_MISS_WAIT  = 3'h4,
        CACHE_MISS_FILL  = 3'h5,
        CACHE_MISS_RETURN = 3'h6
    } cache_state_t;

    cache_state_t cache_state;

    // =========================================================================
    // Miss Target Address — line-aligned, latched on miss
    // =========================================================================
    logic [ADDR_WIDTH-1:0]     miss_addr;
    logic [CACHE_LOG2-1:0]     miss_index;
    logic [TAG_WIDTH-1:0]      miss_tag;

    // Line-aligned address: zero out offset bits
    logic [ADDR_WIDTH-1:0] line_aligned_addr;
    assign line_aligned_addr = {lookup_addr[ADDR_WIDTH-1:LINE_SIZE_LOG2],
                                {LINE_SIZE_LOG2{1'b0}}};

    // =========================================================================
    // AXI Burst Beat Counter (for line fills)
    // =========================================================================
    // LINE_SIZE bytes / DATA_WIDTH bytes per beat = beats per line
    localparam int unsigned BEATS_PER_LINE = LINE_SIZE / (DATA_WIDTH / 8);
    localparam int unsigned BEAT_CNT_WIDTH = $clog2(BEATS_PER_LINE);

    logic [BEAT_CNT_WIDTH-1:0] beat_cnt;
    logic [LINE_WIDTH-1:0]     fill_buffer;  // Accumulate burst data

    // =========================================================================
    // Internal hit/miss detection (registered in FSM)
    // =========================================================================
    logic cache_hit_reg;

    // =========================================================================
    // Lookup outputs (driven by FSM)
    // =========================================================================
    assign lookup_hit   = (cache_state == CACHE_HIT_RETURN) ? 1'b1 :
                          (cache_state == CACHE_LOOKUP) ?
                            (tag_valid[lookup_index] &&
                             tag_addr[lookup_index] == lookup_tag) : 1'b0;

    assign lookup_data  = (cache_state == CACHE_HIT_RETURN) ?
                           data_store[lookup_index] :
                           data_store[lookup_index];

    assign lookup_ready = (cache_state == CACHE_IDLE);

    // =========================================================================
    // Fill interface — accept fills when IDLE or from FSM miss path
    // =========================================================================
    assign fill_ready = (cache_state == CACHE_IDLE) ||
                        (cache_state == CACHE_MISS_FILL);

    // =========================================================================
    // Cache FSM
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : cache_fsm
        if (!rst_n) begin
            cache_state   <= CACHE_IDLE;
            miss_addr     <= '0;
            miss_index    <= '0;
            miss_tag      <= '0;
            beat_cnt      <= '0;
            fill_buffer   <= '0;
            cache_hit_reg <= 1'b0;
            for (int i = 0; i < CACHE_LINES; i++) begin
                tag_valid[i]  <= 1'b0;
                tag_addr[i]   <= '0;
                data_store[i] <= '0;
            end
        end else begin
            case (cache_state)
                // ---------------------------------------------------------
                // CACHE_IDLE: wait for lookup request
                // ---------------------------------------------------------
                CACHE_IDLE: begin
                    if (lookup_valid) begin
                        // Latch address decomposition
                        miss_addr  <= line_aligned_addr;
                        miss_index <= lookup_index;
                        miss_tag   <= lookup_tag;
                        // Check hit/miss
                        if (tag_valid[lookup_index] &&
                            tag_addr[lookup_index] == lookup_tag) begin
                            cache_hit_reg <= 1'b1;
                            cache_state   <= CACHE_HIT_RETURN;
                        end else begin
                            cache_hit_reg <= 1'b0;
                            cache_state   <= CACHE_MISS_FETCH;
                        end
                    end
                    // External fill path
                    if (fill_valid) begin
                        data_store[fill_index] <= fill_data;
                        tag_addr[fill_index]   <= fill_tag;
                        tag_valid[fill_index]  <= 1'b1;
                    end
                end

                // ---------------------------------------------------------
                // CACHE_HIT_RETURN: data available for one cycle
                // ---------------------------------------------------------
                CACHE_HIT_RETURN: begin
                    cache_state <= CACHE_IDLE;
                end

                // ---------------------------------------------------------
                // CACHE_MISS_FETCH: issue AXI read request for line
                // ---------------------------------------------------------
                CACHE_MISS_FETCH: begin
                    cache_state <= CACHE_MISS_WAIT;
                end

                // ---------------------------------------------------------
                // CACHE_MISS_WAIT: wait for AXI read response
                // ---------------------------------------------------------
                CACHE_MISS_WAIT: begin
                    if (axi_resp_i.valid) begin
                        // Accumulate beat data
                        fill_buffer[beat_cnt * DATA_WIDTH +: DATA_WIDTH] <= axi_resp_i.data;
                        beat_cnt <= beat_cnt + BEAT_CNT_WIDTH'(1);
                        if (axi_resp_i.last || beat_cnt == BEAT_CNT_WIDTH'(BEATS_PER_LINE - 1)) begin
                            cache_state <= CACHE_MISS_FILL;
                        end
                    end
                end

                // ---------------------------------------------------------
                // CACHE_MISS_FILL: write fetched line to SRAM + tag store
                // ---------------------------------------------------------
                CACHE_MISS_FILL: begin
                    // Write accumulated data to the cache line
                    data_store[miss_index] <= fill_buffer;
                    tag_addr[miss_index]   <= miss_tag;
                    tag_valid[miss_index]  <= 1'b1;
                    beat_cnt               <= '0;
                    cache_state            <= CACHE_MISS_RETURN;
                end

                // ---------------------------------------------------------
                // CACHE_MISS_RETURN: return fetched data to requester
                // ---------------------------------------------------------
                CACHE_MISS_RETURN: begin
                    cache_state <= CACHE_IDLE;
                end

                default: cache_state <= CACHE_IDLE;
            endcase
        end
    end

    // =========================================================================
    // AXI Request — driven during miss fetch
    // =========================================================================
    always_comb begin : axi_req_gen
        axi_req_o = '0;
        if (cache_state == CACHE_MISS_FETCH) begin
            axi_req_o.req_type  = REQ_INSTR_FETCH;
            axi_req_o.addr      = miss_addr;
            axi_req_o.burst_len = 8'(BEATS_PER_LINE - 1);  // AxLEN = beats-1
            axi_req_o.burst_size = 3'($clog2(DATA_WIDTH/8)); // AxSIZE
            axi_req_o.valid     = 1'b1;
            axi_req_o.id        = 4'h0;  // instruction fetch ID
        end
    end

endmodule : dma330_instr_cache
