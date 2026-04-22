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
    // Fault Outputs
    // =========================================================================
    output logic                              overflow_fault,
    output logic                              underflow_fault
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
    // =========================================================================
    genvar gi;
    generate
        for (gi = 0; gi < NUM_CHANNELS; gi++) begin : ch_status_gen
            assign ch_full[gi]  = (ch_count_r[gi] == COUNT_WIDTH'(MFIFO_DEPTH));
            assign ch_empty[gi] = (ch_count_r[gi] == COUNT_WIDTH'(0));
            assign ch_count[gi] = ch_count_r[gi];
        end
    endgenerate

    // =========================================================================
    // Fault Registers
    // =========================================================================
    assign overflow_fault  = wr_valid & ~wr_ready;   // write when full
    assign underflow_fault = rd_valid & ~rd_ready;   // read when empty

    // =========================================================================
    // Write Logic — load data into channel's virtual FIFO
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : wr_logic
        if (!rst_n) begin
            free_count <= COUNT_WIDTH'(MFIFO_DEPTH);
            for (int i = 0; i < NUM_CHANNELS; i++) begin
                wr_ptr[i]    <= '0;
                ch_count_r[i] <= '0;
            end
        end else begin
            if (wr_valid && wr_ready) begin
                mem[wr_ptr[wr_ch_id]] <= wr_data;
                wr_ptr[wr_ch_id]      <= wr_ptr[wr_ch_id] + ADDR_WIDTH'(1);
                ch_count_r[wr_ch_id]  <= ch_count_r[wr_ch_id] + COUNT_WIDTH'(1);
                free_count            <= free_count - COUNT_WIDTH'(1);
            end
        end
    end

    // =========================================================================
    // Read Logic — store data from channel's virtual FIFO
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : rd_logic
        if (!rst_n) begin
            for (int i = 0; i < NUM_CHANNELS; i++) begin
                rd_ptr[i] <= '0;
            end
        end else begin
            if (rd_valid && rd_ready) begin
                rd_ptr[rd_ch_id] <= rd_ptr[rd_ch_id] + ADDR_WIDTH'(1);
                ch_count_r[rd_ch_id] <= ch_count_r[rd_ch_id] - COUNT_WIDTH'(1);
                free_count            <= free_count + COUNT_WIDTH'(1);
            end
        end
    end

endmodule : dma330_mfifo
