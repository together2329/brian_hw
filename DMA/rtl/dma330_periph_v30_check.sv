// =============================================================================
// dma330_periph_intf.sv — DMA-330 Peripheral Interface
//
// Manages the handshake between DMA channel threads and external peripherals.
// Each peripheral has a dmareq (DMA request) / dmaack (DMA acknowledge)
// handshake protocol.
//
// Features:
//   - 2-flop synchronizers for asynchronous dmareq_i inputs
//   - Per-peripheral state machine (IDLE → REQUESTED → ACKNOWLEDGED)
//   - Channel-to-peripheral routing via periph_num
//   - Round-robin arbitration when multiple channels request same peripheral
//   - DMAFLUSHP support to clear peripheral request state
//   - Ack routing from peripherals back to the requesting channel
// =============================================================================

module dma330_periph_intf #(
    parameter int unsigned NUM_PERIPHERALS = 4,
    parameter int unsigned NUM_CHANNELS    = 4
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                              clk,
    input  logic                              rst_n,

    // =========================================================================
    // External Peripheral Interface (asynchronous dmareq, synchronous dmaack)
    // =========================================================================
    input  logic [NUM_PERIPHERALS-1:0]        dmareq_i,
    output logic [NUM_PERIPHERALS-1:0]        dmaack_o,

    // =========================================================================
    // Channel Request Interface
    // =========================================================================
    input  logic [NUM_CHANNELS-1:0]            ch_periph_req_i,
    input  logic [NUM_CHANNELS-1:0]            ch_periph_ack_i,
    input  logic [$clog2(NUM_PERIPHERALS)-1:0] ch_periph_num [0:NUM_CHANNELS-1],

    // =========================================================================
    // Channel-side Requested Output (peripheral ack routed back to channel)
    // =========================================================================
    output logic [NUM_CHANNELS-1:0]            ch_periph_ack_o,

    // =========================================================================
    // Flush Interface (DMAFLUSHP)
    // =========================================================================
    input  logic                              flush_req_i,
    input  logic [$clog2(NUM_PERIPHERALS)-1:0] flush_periph_num_i
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Derived Constants
    // =========================================================================
    localparam int unsigned PERIPH_WIDTH = $clog2(NUM_PERIPHERALS);
    localparam int unsigned CH_WIDTH     = $clog2(NUM_CHANNELS);

    // =========================================================================
    // Per-peripheral state machine
    // =========================================================================
    typedef enum logic [1:0] {
        PERIPH_IDLE,
        PERIPH_REQUESTED,
        PERIPH_ACKNOWLEDGED
    } periph_state_t;

    periph_state_t periph_state [0:NUM_PERIPHERALS-1];

    // =========================================================================
    // Per-peripheral owner tracking
    //   owner[pi] = channel index that currently owns peripheral pi
    //   Valid only when periph_state[pi] != PERIPH_IDLE
    // =========================================================================
    logic [CH_WIDTH-1:0] periph_owner [0:NUM_PERIPHERALS-1];

    // =========================================================================
    // Round-robin priority pointer per peripheral
    // =========================================================================
    logic [CH_WIDTH-1:0] rr_ptr [0:NUM_PERIPHERALS-1];

    // =========================================================================
    // 2-flop synchronizers for asynchronous dmareq_i
    // =========================================================================
    logic [NUM_PERIPHERALS-1:0] dmareq_meta;
    logic [NUM_PERIPHERALS-1:0] dmareq_sync;

    always_ff @(posedge clk or negedge rst_n) begin : sync_dmareq
        if (!rst_n) begin
            dmareq_meta <= '0;
            dmareq_sync <= '0;
        end else begin
            dmareq_meta <= dmareq_i;
            dmareq_sync <= dmareq_meta;
        end
    end

    // =========================================================================
    // Per-peripheral request aggregation from channels
    //   periph_ch_req[pi][ch] = 1 if channel ch requests peripheral pi
    // =========================================================================
    logic [NUM_CHANNELS-1:0] periph_ch_req [0:NUM_PERIPHERALS-1];

    always_comb begin
        for (int pi = 0; pi < NUM_PERIPHERALS; pi++) begin
            periph_ch_req[pi] = '0;
            for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                if (ch_periph_req_i[ch] && (ch_periph_num[ch] == PERIPH_WIDTH'(pi))) begin
                    periph_ch_req[pi][ch] = 1'b1;
                end
            end
        end
    end

    // =========================================================================
    // Round-robin arbitration: find next requesting channel >= rr_ptr
    // =========================================================================
    logic [NUM_CHANNELS-1:0] periph_ch_winner [0:NUM_PERIPHERALS-1];

    always_comb begin
        for (int pi = 0; pi < NUM_PERIPHERALS; pi++) begin
            periph_ch_winner[pi] = '0;
            // Search from rr_ptr upward, then wrap around
            for (int offset = 0; offset < NUM_CHANNELS; offset++) begin
                automatic int ch = (rr_ptr[pi] + offset) % NUM_CHANNELS;
                if (periph_ch_req[pi][ch] && periph_ch_winner[pi] == '0) begin
                    periph_ch_winner[pi] = 1 << ch;
                end
            end
        end
    end

    // =========================================================================
    // Per-peripheral has_request flag
    // =========================================================================
    logic [NUM_PERIPHERALS-1:0] periph_has_req;

    always_comb begin
        for (int pi = 0; pi < NUM_PERIPHERALS; pi++) begin
            periph_has_req[pi] = |periph_ch_req[pi];
        end
    end

    // =========================================================================
    // DMAACK output — one bit per peripheral, asserted in ACKNOWLEDGED state
    // =========================================================================
    always_comb begin
        dmaack_o = '0;
        for (int pi = 0; pi < NUM_PERIPHERALS; pi++) begin
            if (periph_state[pi] == PERIPH_ACKNOWLEDGED) begin
                dmaack_o[pi] = 1'b1;
            end
        end
    end

    // =========================================================================
    // Channel ack routing: when peripheral acknowledges, route to owner channel
    // =========================================================================
    always_comb begin
        ch_periph_ack_o = '0;
        for (int pi = 0; pi < NUM_PERIPHERALS; pi++) begin
            if (periph_state[pi] == PERIPH_ACKNOWLEDGED) begin
                ch_periph_ack_o[periph_owner[pi]] = 1'b1;
            end
        end
    end

    // =========================================================================
    // Per-peripheral state machines with DMAFLUSHP support
    // =========================================================================
    genvar pi;
    generate
        for (pi = 0; pi < NUM_PERIPHERALS; pi++) begin : gen_periph
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    periph_state[pi] <= PERIPH_IDLE;
                    periph_owner[pi] <= '0;
                    rr_ptr[pi]       <= '0;
                end else begin
                    // DMAFLUSHP: clear state for this peripheral
                    if (flush_req_i && (flush_periph_num_i == PERIPH_WIDTH'(pi))) begin
                        periph_state[pi] <= PERIPH_IDLE;
                        periph_owner[pi] <= '0;
                    end else begin
                        case (periph_state[pi])
                            PERIPH_IDLE: begin
                                if (periph_has_req[pi]) begin
                                    // Pick winner via round-robin
                                    for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                                        if (periph_ch_winner[pi][ch]) begin
                                            periph_owner[pi] <= CH_WIDTH'(ch);
                                            // Update round-robin pointer to ch+1
                                            rr_ptr[pi] <= CH_WIDTH'((ch + 1) % NUM_CHANNELS);
                                        end
                                    end
                                    periph_state[pi] <= PERIPH_REQUESTED;
                                end
                            end

                            PERIPH_REQUESTED: begin
                                // Wait for peripheral to assert dmareq (synchronized)
                                if (dmareq_sync[pi]) begin
                                    periph_state[pi] <= PERIPH_ACKNOWLEDGED;
                                end
                            end

                            PERIPH_ACKNOWLEDGED: begin
                                // Wait for owning channel to deassert request
                                if (!ch_periph_req_i[periph_owner[pi]]) begin
                                    periph_state[pi] <= PERIPH_IDLE;
                                    periph_owner[pi] <= '0;
                                end
                            end

                            default: periph_state[pi] <= PERIPH_IDLE;
                        endcase
                    end
                end
            end
        end
    endgenerate

endmodule : dma330_periph_intf
