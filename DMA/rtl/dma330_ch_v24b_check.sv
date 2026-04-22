// =============================================================================
// dma330_channel_thread.sv — DMA-330 Channel Thread
//
// Each DMA channel thread independently executes its own instruction stream.
// Channel threads perform the actual data movement: load from source to MFIFO,
// store from MFIFO to destination, manage loop counters, update registers
// (SA/DA/CC), and signal events.
//
// FSM States:
//   CH_STOPPED            — Idle, waiting for start from manager
//   CH_EXECUTING          — Fetching and executing instructions
//   CH_CACHE_MISS         — Waiting for instruction cache line fill
//   CH_UPDATING_PC        — Updating PC after instruction execution
//   CH_WAITING_FOR_EVENT  — Blocked on DMAWFE
//   CH_AT_BARRIER         — Blocked on DMAWMB/DMARMB barrier
//   CH_WAITING_FOR_PERIPH — Blocked waiting for peripheral acknowledgement
//   CH_FAULT_COMPLETING   — Completing current op after fault
//   CH_FAULT_LOCKED       — Locked due to unrecoverable fault
// =============================================================================

module dma330_channel_thread #(
    parameter int unsigned CHANNEL_ID = 0,
    parameter int unsigned ADDR_WIDTH = 32,
    parameter int unsigned DATA_WIDTH = 32
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // Start / Kill Control (from manager thread)
    // =========================================================================
    input  logic                          start_i,
    input  logic [31:0]                   start_pc_i,
    input  logic                          start_security_i,
    input  logic                          kill_i,

    // =========================================================================
    // Instruction Interface (from decoder)
    // =========================================================================
    input  dma330_pkg::decoded_instr_t    decoded_instr_i,
    input  logic                          decoded_valid_i,
    output logic                          decoded_ready_o,

    // =========================================================================
    // AXI Interface (for data transfers)
    // =========================================================================
    output dma330_pkg::axi_req_t          axi_req_o,
    input  dma330_pkg::axi_resp_t         axi_resp_i,

    // =========================================================================
    // MFIFO Interface (shared multi-channel data buffer)
    // =========================================================================
    output logic [DATA_WIDTH-1:0]         mfifo_wr_data,
    output logic                          mfifo_wr_valid,
    input  logic                          mfifo_wr_ready,

    input  logic [DATA_WIDTH-1:0]         mfifo_rd_data,
    output logic                          mfifo_rd_valid,
    input  logic                          mfifo_rd_ready,

    // =========================================================================
    // Peripheral Interface
    // =========================================================================
    input  logic                          periph_req_i,
    output logic                          periph_ack_o,
    output logic [3:0]                    periph_num_o,

    // =========================================================================
    // Event Interface
    // =========================================================================
    output logic [3:0]                    event_send_o,
    input  logic [dma330_pkg::NUM_EVENTS-1:0] event_recv_i,

    // =========================================================================
    // Barrier Interface
    // =========================================================================
    output logic                          barrier_o,
    input  logic                          barrier_ack_i,

    // =========================================================================
    // Register & State Output
    // =========================================================================
    output dma330_pkg::channel_regs_t     ch_regs_o,
    output dma330_pkg::channel_state_t    ch_state_o
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Internal State & Registers
    // =========================================================================
    channel_state_t state_reg;
    channel_regs_t  regs;

    // =========================================================================
    // Outputs
    // =========================================================================
    assign ch_state_o = state_reg;
    assign ch_regs_o  = regs;

    // =========================================================================
    // Default output assignments
    // =========================================================================
    assign decoded_ready_o = (state_reg == CH_EXECUTING);
    assign axi_req_o       = '0;
    assign mfifo_wr_data   = '0;
    assign mfifo_wr_valid  = 1'b0;
    assign mfifo_rd_valid  = 1'b0;
    assign periph_ack_o    = 1'b0;
    assign periph_num_o    = '0;
    assign event_send_o    = '0;
    assign barrier_o       = 1'b0;

    // =========================================================================
    // FSM — State register with start/kill/execute logic
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : ch_fsm
        if (!rst_n) begin
            state_reg        <= CH_STOPPED;
            regs             <= '0;
        end else begin
            case (state_reg)
                // ----------------------------------------------------------
                // CH_STOPPED: idle — wait for start signal
                // ----------------------------------------------------------
                CH_STOPPED: begin
                    if (start_i) begin
                        state_reg      <= CH_EXECUTING;
                        regs.SA        <= '0;
                        regs.DA        <= '0;
                        regs.CC        <= '0;
                        regs.PC        <= start_pc_i;
                        regs.LC0       <= '0;
                        regs.LC1       <= '0;
                        regs.loop0_start_PC <= start_pc_i;
                        regs.loop1_start_PC <= start_pc_i;
                        regs.security  <= start_security_i;
                    end
                end

                // ----------------------------------------------------------
                // CH_EXECUTING: fetch-decode-execute loop
                // ----------------------------------------------------------
                CH_EXECUTING: begin
                    if (kill_i) begin
                        state_reg <= CH_STOPPED;
                    end else if (decoded_valid_i && decoded_ready_o) begin
                        // PC advancement (instr_len is bytes-1)
                        regs.PC <= regs.PC + ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                    end
                end

                // ----------------------------------------------------------
                // CH_CACHE_MISS: waiting for instruction cache line fill
                // ----------------------------------------------------------
                CH_CACHE_MISS: begin
                    if (kill_i) begin
                        state_reg <= CH_STOPPED;
                    end
                    // Transition handled by cache logic (future task)
                end

                // ----------------------------------------------------------
                // CH_UPDATING_PC: updating PC after instruction execution
                // ----------------------------------------------------------
                CH_UPDATING_PC: begin
                    state_reg <= CH_EXECUTING;
                end

                // ----------------------------------------------------------
                // CH_WAITING_FOR_EVENT: blocked on DMAWFE
                // ----------------------------------------------------------
                CH_WAITING_FOR_EVENT: begin
                    if (kill_i) begin
                        state_reg <= CH_STOPPED;
                    end
                    // Event check handled in future task
                end

                // ----------------------------------------------------------
                // CH_AT_BARRIER: blocked on DMAWMB/DMARMB
                // ----------------------------------------------------------
                CH_AT_BARRIER: begin
                    if (kill_i) begin
                        state_reg <= CH_STOPPED;
                    end
                    // Barrier handling in future task
                end

                // ----------------------------------------------------------
                // CH_WAITING_FOR_PERIPH: waiting for peripheral response
                // ----------------------------------------------------------
                CH_WAITING_FOR_PERIPH: begin
                    if (kill_i) begin
                        state_reg <= CH_STOPPED;
                    end
                    // Peripheral handshake in future task
                end

                // ----------------------------------------------------------
                // CH_FAULT_COMPLETING: drain current operation
                // ----------------------------------------------------------
                CH_FAULT_COMPLETING: begin
                    state_reg <= CH_FAULT_LOCKED;
                end

                // ----------------------------------------------------------
                // CH_FAULT_LOCKED: stuck until reset
                // ----------------------------------------------------------
                CH_FAULT_LOCKED: begin
                    // Only reset or kill can clear this
                end

                default: state_reg <= CH_STOPPED;
            endcase
        end
    end

endmodule : dma330_channel_thread
