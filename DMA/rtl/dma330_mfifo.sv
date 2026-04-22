// =============================================================================
// dma330_mfifo.sv — DMA-330 Multi-Channel FIFO (MFIFO)
//
// Shared data buffer between DMA load and store operations.
// Implements virtual per-channel FIFOs within a shared dual-port RAM.
// Each channel has independent write (load) and read (store) pointers.
// Global free-space tracking ensures the total usage never exceeds MFIFO_DEPTH.
//
// Architecture:
//   - Single dual-port RAM shared by all channels
//   - Per-channel wr_ptr / rd_ptr for virtual FIFO partitioning
//   - Global free_count tracks total available slots
//   - Overflow and underflow fault detection
// =============================================================================

module dma330_mfifo #(
    parameter int unsigned MFIFO_DEPTH  = 64,
    parameter int unsigned DATA_WIDTH   = 32,
    parameter int unsigned NUM_CHANNELS = 4
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                              clk,
    input  logic                              rst_n,

    // =========================================================================
    // Write Port (Load side — channel writes data from AXI read)
    // =========================================================================
    input  logic [$clog2(NUM_CHANNELS)-1:0]   wr_ch_id,
    input  logic [DATA_WIDTH-1:0]             wr_data,
    input  logic                              wr_valid,
    output logic                              wr_ready,

    // =========================================================================
    // Read Port (Store side — channel reads data for AXI write)
    // =========================================================================
    input  logic [$clog2(NUM_CHANNELS)-1:0]   rd_ch_id,
    output logic [DATA_WIDTH-1:0]             rd_data,
    input  logic                              rd_valid,
    output logic                              rd_ready,

    // =========================================================================
    // Per-Channel Status
    // =========================================================================
    output logic [NUM_CHANNELS-1:0]           ch_full,
    output logic [NUM_CHANNELS-1:0]           ch_empty,
    output logic [$clog2(MFIFO_DEPTH):0]      ch_count [0:NUM_CHANNELS-1],

    // =========================================================================
    // Per-Channel Configuration
    // =========================================================================
    input  logic [$clog2(MFIFO_DEPTH):0]      allocated_depth [0:NUM_CHANNELS-1],

    // =========================================================================
    // Fault Outputs (sticky — cleared by explicit fault clear)
    // =========================================================================
    output logic                              overflow_fault,
    output logic                              underflow_fault,
    input  logic                              fault_clear
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Derived Constants
    // =========================================================================
    localparam int unsigned ADDR_WIDTH = $clog2(MFIFO_DEPTH);
    localparam int unsigned CH_ID_WIDTH = $clog2(NUM_CHANNELS);
    localparam int unsigned COUNT_WIDTH = $clog2(MFIFO_DEPTH) + 1;  // extra bit for full range

    // =========================================================================
    // Dual-Port RAM Storage
    // =========================================================================
    logic [DATA_WIDTH-1:0] mem [0:MFIFO_DEPTH-1];

    // =========================================================================
    // Per-Channel Write and Read Pointers
    // =========================================================================
    logic [ADDR_WIDTH-1:0]  wr_ptr [0:NUM_CHANNELS-1];
    logic [ADDR_WIDTH-1:0]  rd_ptr [0:NUM_CHANNELS-1];

    // =========================================================================
    // Per-Channel Occupancy Count
    // =========================================================================
    logic [COUNT_WIDTH-1:0] ch_count_r [0:NUM_CHANNELS-1];

    // =========================================================================
    // Global Free-Space Counter
    // =========================================================================
    logic [COUNT_WIDTH-1:0] free_count;

    // =========================================================================
    // Write Ready — not full for that channel AND global free space available
    // =========================================================================
    assign wr_ready = (~ch_full[wr_ch_id]) && (free_count > 0);

    // =========================================================================
    // Read Data — from dual-port RAM at the read channel's pointer
    // =========================================================================
    assign rd_data  = mem[rd_ptr[rd_ch_id]];

    // =========================================================================
    // Read Ready — channel has data available (not empty)
    // =========================================================================
    assign rd_ready = ~ch_empty[rd_ch_id];

    // =========================================================================
    // Per-Channel Status Outputs
    //   ch_full:  count >= allocated_depth (per-channel back-pressure)
    //   ch_empty: count == 0
    // =========================================================================
    genvar gi;
    generate
        for (gi = 0; gi < NUM_CHANNELS; gi++) begin : ch_status_gen
            assign ch_full[gi]  = (ch_count_r[gi] >= allocated_depth[gi]);
            assign ch_empty[gi] = (ch_count_r[gi] == COUNT_WIDTH'(0));
            assign ch_count[gi] = ch_count_r[gi];
        end
    endgenerate

    // =========================================================================
    // Sticky Fault Registers — latched on error, cleared by fault_clear
    // =========================================================================
    logic overflow_fault_r;
    logic underflow_fault_r;

    assign overflow_fault  = overflow_fault_r;
    assign underflow_fault = underflow_fault_r;

    always_ff @(posedge clk or negedge rst_n) begin : fault_logic
        if (!rst_n) begin
            overflow_fault_r  <= 1'b0;
            underflow_fault_r <= 1'b0;
        end else begin
            if (fault_clear) begin
                overflow_fault_r  <= 1'b0;
                underflow_fault_r <= 1'b0;
            end else begin
                if (wr_valid & ~wr_ready)    overflow_fault_r  <= 1'b1;
                if (rd_valid & ~rd_ready)    underflow_fault_r <= 1'b1;
            end
        end
    end

    // =========================================================================
    // Combined Write/Read Logic — single always_ff to avoid multi-driver
    // =========================================================================
    logic wr_accept;  // internal: write accepted this cycle
    logic rd_accept;  // internal: read accepted this cycle

    assign wr_accept = wr_valid && wr_ready;
    assign rd_accept = rd_valid && rd_ready;

    always_ff @(posedge clk or negedge rst_n) begin : mfifo_logic
        if (!rst_n) begin
            free_count <= COUNT_WIDTH'(MFIFO_DEPTH);
            for (int i = 0; i < NUM_CHANNELS; i++) begin
                wr_ptr[i]     <= '0;
                rd_ptr[i]     <= '0;
                ch_count_r[i] <= '0;
            end
        end else begin
            // Write path
            if (wr_accept) begin
                mem[wr_ptr[wr_ch_id]] <= wr_data;
                wr_ptr[wr_ch_id]      <= wr_ptr[wr_ch_id] + ADDR_WIDTH'(1);
                ch_count_r[wr_ch_id]  <= ch_count_r[wr_ch_id] + COUNT_WIDTH'(1);
            end
            // Read path
            if (rd_accept) begin
                rd_ptr[rd_ch_id]      <= rd_ptr[rd_ch_id] + ADDR_WIDTH'(1);
                ch_count_r[rd_ch_id]  <= ch_count_r[rd_ch_id] - COUNT_WIDTH'(1);
            end
            // Free-space update
            if (wr_accept && rd_accept) begin
                free_count <= free_count;  // net zero change
            end else if (wr_accept) begin
                free_count <= free_count - COUNT_WIDTH'(1);
            end else if (rd_accept) begin
                free_count <= free_count + COUNT_WIDTH'(1);
            end
        end
    end

endmodule : dma330_mfifo
