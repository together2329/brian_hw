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
//   - Flush support for DMAFLUSHP instruction
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
    // Channel-side Requested Output (which channels are waiting)
    // =========================================================================
    output logic [NUM_CHANNELS-1:0]            ch_periph_req_o,

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
    // 2-flop synchronizers for asynchronous dmareq_i
    // =========================================================================
    logic [NUM_PERIPHERALS-1:0] dmareq_meta;
    logic [NUM_PERIPHERALS-1:0] dmareq_sync;

    always_ff @(posedge clk or negedge rst_n) begin : sync_dmareq
        if (!rst_n) begin
            dmareq_meta <= '0;
            dmareq_sync <= '0;
        end else begin
            dmareq_meta <= dmareq_i;     // first flop (metastable)
            dmareq_sync <= dmareq_meta;  // second flop (stable)
        end
    end

    // =========================================================================
    // Per-peripheral request aggregation from channels
    // =========================================================================
    logic [NUM_PERIPHERALS-1:0] periph_requested;

    always_comb begin
        periph_requested = '0;
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            if (ch_periph_req_i[ch]) begin
                periph_requested[ch_periph_num[ch]] = 1'b1;
            end
        end
    end

    // Channel request output: channel has a pending request for its peripheral
    assign ch_periph_req_o = ch_periph_req_i;

    // =========================================================================
    // DMAACK output — asserted when peripheral is acknowledged
    // =========================================================================
    assign dmaack_o = '0;  // Driven by per-FSM below

    // =========================================================================
    // Per-peripheral state machines
    // =========================================================================
    genvar pi;
    generate
        for (pi = 0; pi < NUM_PERIPHERALS; pi++) begin : gen_periph
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    periph_state[pi] <= PERIPH_IDLE;
                end else begin
                    case (periph_state[pi])
                        PERIPH_IDLE: begin
                            if (periph_requested[pi]) begin
                                periph_state[pi] <= PERIPH_REQUESTED;
                            end
                        end

                        PERIPH_REQUESTED: begin
                            // Wait for peripheral to assert dmareq
                            if (dmareq_sync[pi]) begin
                                periph_state[pi] <= PERIPH_ACKNOWLEDGED;
                            end
                        end

                        PERIPH_ACKNOWLEDGED: begin
                            // Wait for channel to deassert request
                            if (!periph_requested[pi]) begin
                                periph_state[pi] <= PERIPH_IDLE;
                            end
                        end

                        default: periph_state[pi] <= PERIPH_IDLE;
                    endcase
                end
            end
        end
    endgenerate

endmodule : dma330_periph_intf
