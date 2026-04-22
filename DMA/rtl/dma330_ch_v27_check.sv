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
    // CC Register Field Constants (for documentation / extraction)
    // =========================================================================
    // CC[3:0]    = src_burst_size (encoded: 0=1B, 1=2B, 2=4B, 3=8B, 4=16B, 5=32B, 6=64B, 7=128B)
    // CC[11:4]   = src_burst_len  (number of transfers - 1, max 256)
    // CC[14]     = src_inc (1=incrementing, 0=fixed)
    // CC[15]     = dst_inc (1=incrementing, 0=fixed)
    // CC[23:20]  = src_cache_prot
    // CC[27:24]  = dst_cache_prot
    localparam int CC_SRC_BURST_SIZE_HI = 3;
    localparam int CC_SRC_BURST_SIZE_LO = 0;
    localparam int CC_SRC_BURST_LEN_HI  = 11;
    localparam int CC_SRC_BURST_LEN_LO  = 4;
    localparam int CC_SRC_INC_BIT       = 14;
    localparam int CC_DST_INC_BIT       = 15;
    localparam int CC_SRC_PRIV_HI       = 23;
    localparam int CC_SRC_PRIV_LO       = 20;
    localparam int CC_DST_PRIV_HI       = 27;
    localparam int CC_DST_PRIV_LO       = 24;

    // =========================================================================
    // Internal State & Registers
    // =========================================================================
    channel_state_t state_reg;
    channel_regs_t  regs;

    // =========================================================================
    // Data Transfer Sub-FSM
    // =========================================================================
    typedef enum logic [2:0] {
        XFER_IDLE,
        XFER_WAIT_PERIPH,
        XFER_REQ_AXI,
        XFER_WAIT_AXI,
        XFER_MFIFO_WR,
        XFER_MFIFO_RD,
        XFER_COMPLETE,
        XFER_FAULT
    } xfer_state_t;

    xfer_state_t xfer_state;

    // Current transfer operation info
    logic        xfer_is_load;     // 1=DMALD/DMALDP, 0=DMAST/DMASTP
    logic        xfer_is_periph;   // 1=P variant (wait/ack peripheral)
    logic [3:0]  xfer_periph_num;
    logic [31:0] xfer_total_bytes; // burst_size_bytes * (burst_len+1)

    // =========================================================================
    // AXI burst parameter extraction from CC register
    // =========================================================================
    logic [2:0]  src_burst_size_enc;  // CC[3:0] encoded size
    logic [7:0]  src_burst_len;       // CC[11:4]
    logic        src_inc;             // CC[14]
    logic [2:0]  burst_size_bytes;    // decoded: 2^enc

    assign src_burst_size_enc = regs.CC[CC_SRC_BURST_SIZE_HI:CC_SRC_BURST_SIZE_LO];
    assign src_burst_len      = regs.CC[CC_SRC_BURST_LEN_HI:CC_SRC_BURST_LEN_LO];
    assign src_inc            = regs.CC[CC_SRC_INC_BIT];

    // Decode burst size: encoded as log2(bytes)
    always_comb begin
        case (src_burst_size_enc)
            3'd0: burst_size_bytes = 3'd1;
            3'd1: burst_size_bytes = 3'd2;
            3'd2: burst_size_bytes = 3'd4;
            3'd3: burst_size_bytes = 3'd8;
            default: burst_size_bytes = 3'd1;
        endcase
    end

    // =========================================================================
    // Outputs
    // =========================================================================
    assign ch_state_o = state_reg;
    assign ch_regs_o  = regs;

    // =========================================================================
    // Default output assignments — overridden by transfer logic
    // =========================================================================
    logic [DATA_WIDTH-1:0] mfifo_wr_data_r;
    logic                  mfifo_wr_valid_r;
    logic                  mfifo_rd_valid_r;
    logic                  periph_ack_r;
    logic [3:0]            periph_num_r;
    logic [3:0]            event_send_r;
    logic                  barrier_r;
    axi_req_t              axi_req_r;
    logic                  decoded_ready_r;

    assign decoded_ready_o = decoded_ready_r;
    assign axi_req_o       = axi_req_r;
    assign mfifo_wr_data   = mfifo_wr_data_r;
    assign mfifo_wr_valid  = mfifo_wr_valid_r;
    assign mfifo_rd_valid  = mfifo_rd_valid_r;
    assign periph_ack_o    = periph_ack_r;
    assign periph_num_o    = periph_num_r;
    assign event_send_o    = event_send_r;
    assign barrier_o       = barrier_r;

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
                        // Check for decode fault
                        if (decoded_instr_i.fault) begin
                            state_reg <= CH_FAULT_COMPLETING;
                        end else begin
                            case (decoded_instr_i.opcode)
                                // ----------------------------------------------
                                // DMAMOV: write 32-bit immediate to SA, DA, or CC
                                //   reg_select: 00=SA, 01=DA, 10=CC
                                // ----------------------------------------------
                                OPC_DMAMOV: begin
                                    case (decoded_instr_i.reg_select)
                                        2'd0:    regs.SA <= decoded_instr_i.imm32;
                                        2'd1:    regs.DA <= decoded_instr_i.imm32;
                                        2'd2:    regs.CC <= decoded_instr_i.imm32;
                                        default: state_reg <= CH_FAULT_COMPLETING;
                                    endcase
                                    regs.PC <= regs.PC + ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                end

                                // ----------------------------------------------
                                // DMAADDH: add 16-bit immediate to upper halfword
                                //   reg_select: 00=SA, 01=DA
                                // ----------------------------------------------
                                OPC_DMAADDH: begin
                                    case (decoded_instr_i.reg_select)
                                        2'd0: begin
                                            regs.SA[31:16] <= regs.SA[31:16] +
                                                              decoded_instr_i.imm16[15:0];
                                        end
                                        2'd1: begin
                                            regs.DA[31:16] <= regs.DA[31:16] +
                                                              decoded_instr_i.imm16[15:0];
                                        end
                                        default: state_reg <= CH_FAULT_COMPLETING;
                                    endcase
                                    regs.PC <= regs.PC + ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                end

                                // ----------------------------------------------
                                // DMAADNH: subtract 16-bit imm from upper halfword
                                //   reg_select: 00=SA, 01=DA
                                // ----------------------------------------------
                                OPC_DMAADNH: begin
                                    case (decoded_instr_i.reg_select)
                                        2'd0: begin
                                            regs.SA[31:16] <= regs.SA[31:16] -
                                                              decoded_instr_i.imm16[15:0];
                                        end
                                        2'd1: begin
                                            regs.DA[31:16] <= regs.DA[31:16] -
                                                              decoded_instr_i.imm16[15:0];
                                        end
                                        default: state_reg <= CH_FAULT_COMPLETING;
                                    endcase
                                    regs.PC <= regs.PC + ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                end

                                // ----------------------------------------------
                                // DMAEND: stop execution
                                // ----------------------------------------------
                                OPC_DMAEND: begin
                                    state_reg <= CH_STOPPED;
                                end

                                // ----------------------------------------------
                                // DMANOP: just advance PC
                                // ----------------------------------------------
                                OPC_DMANOP: begin
                                    regs.PC <= regs.PC + ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                end

                                // ----------------------------------------------
                                // DMALD: AXI read from SA, write to MFIFO
                                // ----------------------------------------------
                                OPC_DMALD: begin
                                    xfer_is_load   <= 1'b1;
                                    xfer_is_periph <= 1'b0;
                                    xfer_state     <= XFER_REQ_AXI;
                                    decoded_ready_r <= 1'b0;
                                end

                                // ----------------------------------------------
                                // DMALDP: AXI read from SA after peripheral req
                                // ----------------------------------------------
                                OPC_DMALDP,
                                OPC_DMALDPS: begin
                                    xfer_is_load   <= 1'b1;
                                    xfer_is_periph <= 1'b1;
                                    xfer_periph_num <= decoded_instr_i.periph_num;
                                    xfer_state     <= XFER_WAIT_PERIPH;
                                    decoded_ready_r <= 1'b0;
                                end

                                // ----------------------------------------------
                                // DMAST: read from MFIFO, AXI write to DA
                                // ----------------------------------------------
                                OPC_DMAST: begin
                                    xfer_is_load   <= 1'b0;
                                    xfer_is_periph <= 1'b0;
                                    xfer_state     <= XFER_MFIFO_RD;
                                    decoded_ready_r <= 1'b0;
                                end

                                // ----------------------------------------------
                                // DMASTP: read from MFIFO, AXI write, ack periph
                                // ----------------------------------------------
                                OPC_DMASTP,
                                OPC_DMASTPS: begin
                                    xfer_is_load   <= 1'b0;
                                    xfer_is_periph <= 1'b1;
                                    xfer_periph_num <= decoded_instr_i.periph_num;
                                    xfer_state     <= XFER_MFIFO_RD;
                                    decoded_ready_r <= 1'b0;
                                end

                                // ----------------------------------------------
                                // DMALP: initialize loop counter
                                //   loop_cntr_sel: 0=LC0, 1=LC1
                                //   imm16 = iteration count - 1
                                //   Save next PC as loop start
                                // ----------------------------------------------
                                OPC_DMALP: begin
                                    if (decoded_instr_i.loop_cntr_sel == 1'b0) begin
                                        regs.LC0 <= decoded_instr_i.imm16[7:0];
                                        regs.loop0_start_PC <= regs.PC +
                                            ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                    end else begin
                                        regs.LC1 <= decoded_instr_i.imm16[7:0];
                                        regs.loop1_start_PC <= regs.PC +
                                            ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                    end
                                    regs.PC <= regs.PC + ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                end

                                // ----------------------------------------------
                                // DMALPEND: loop end — decrement & branch or exit
                                //   loop_cntr_sel: 0=LC0, 1=LC1
                                //   Decrement LC; if > 0: PC = loop_start_PC
                                //                 if == 0: PC += instr_len (exit)
                                // ----------------------------------------------
                                OPC_DMALPEND: begin
                                    if (decoded_instr_i.loop_cntr_sel == 1'b0) begin
                                        if (regs.LC0 > 8'd0) begin
                                            regs.LC0 <= regs.LC0 - 8'd1;
                                            regs.PC  <= regs.loop0_start_PC;
                                        end else begin
                                            regs.PC <= regs.PC +
                                                ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                        end
                                    end else begin
                                        if (regs.LC1 > 8'd0) begin
                                            regs.LC1 <= regs.LC1 - 8'd1;
                                            regs.PC  <= regs.loop1_start_PC;
                                        end else begin
                                            regs.PC <= regs.PC +
                                                ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                        end
                                    end
                                end

                                // ----------------------------------------------
                                // Default: advance PC (other instructions)
                                // ----------------------------------------------
                                default: begin
                                    regs.PC <= regs.PC + ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                                end
                            endcase
                        end
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

    // =========================================================================
    // Transfer Sub-FSM — handles load/store data movement
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : xfer_fsm
        if (!rst_n) begin
            xfer_state      <= XFER_IDLE;
            xfer_is_load    <= 1'b0;
            xfer_is_periph  <= 1'b0;
            xfer_periph_num <= '0;
            axi_req_r       <= '0;
            mfifo_wr_data_r <= '0;
            mfifo_wr_valid_r <= 1'b0;
            mfifo_rd_valid_r <= 1'b0;
            periph_ack_r    <= 1'b0;
            periph_num_r    <= '0;
            event_send_r    <= '0;
            barrier_r       <= 1'b0;
            decoded_ready_r <= 1'b1;
        end else begin
            // Default: clear pulse signals
            axi_req_r.valid <= 1'b0;
            mfifo_wr_valid_r <= 1'b0;
            mfifo_rd_valid_r <= 1'b0;
            periph_ack_r    <= 1'b0;
            decoded_ready_r <= 1'b1;

            case (xfer_state)
                // ----------------------------------------------------------
                XFER_IDLE: begin
                    // Waiting for load/store opcode to kick off
                end

                // ----------------------------------------------------------
                // Wait for peripheral request (DMALDP)
                // ----------------------------------------------------------
                XFER_WAIT_PERIPH: begin
                    decoded_ready_r <= 1'b0;
                    periph_num_r    <= xfer_periph_num;
                    if (periph_req_i) begin
                        xfer_state <= XFER_REQ_AXI;
                    end
                end

                // ----------------------------------------------------------
                // Issue AXI request
                // ----------------------------------------------------------
                XFER_REQ_AXI: begin
                    decoded_ready_r <= 1'b0;
                    if (xfer_is_load) begin
                        // DMALD: AXI read from SA
                        axi_req_r.req_type   <= REQ_DMALD;
                        axi_req_r.addr       <= regs.SA;
                        axi_req_r.data       <= '0;
                        axi_req_r.burst_len  <= src_burst_len;
                        axi_req_r.burst_size <= src_burst_size_enc;
                        axi_req_r.id         <= 4'(CHANNEL_ID);
                        axi_req_r.valid      <= 1'b1;
                        axi_req_r.security   <= regs.security;
                    end else begin
                        // DMAST: AXI write to DA — data comes from MFIFO
                        axi_req_r.req_type   <= REQ_DMAST;
                        axi_req_r.addr       <= regs.DA;
                        axi_req_r.data       <= mfifo_rd_data;
                        axi_req_r.burst_len  <= src_burst_len;
                        axi_req_r.burst_size <= src_burst_size_enc;
                        axi_req_r.id         <= 4'(CHANNEL_ID);
                        axi_req_r.valid      <= 1'b1;
                        axi_req_r.security   <= regs.security;
                    end
                    xfer_state <= XFER_WAIT_AXI;
                end

                // ----------------------------------------------------------
                // Wait for AXI response
                // ----------------------------------------------------------
                XFER_WAIT_AXI: begin
                    decoded_ready_r <= 1'b0;
                    if (axi_resp_i.valid) begin
                        if (axi_resp_i.error) begin
                            // AXI error → fault
                            xfer_state <= XFER_FAULT;
                            state_reg  <= CH_FAULT_COMPLETING;
                        end else if (xfer_is_load) begin
                            // Load: write AXI response to MFIFO
                            mfifo_wr_data_r  <= axi_resp_i.data;
                            mfifo_wr_valid_r <= 1'b1;
                            if (mfifo_wr_ready) begin
                                xfer_state <= XFER_COMPLETE;
                            end
                            // If MFIFO full (back-pressure), stay here
                        end else begin
                            // Store: AXI write completed
                            xfer_state <= XFER_COMPLETE;
                        end
                    end
                end

                // ----------------------------------------------------------
                // Read from MFIFO (for DMAST before AXI write)
                // ----------------------------------------------------------
                XFER_MFIFO_RD: begin
                    decoded_ready_r <= 1'b0;
                    mfifo_rd_valid_r <= 1'b1;
                    if (mfifo_rd_ready) begin
                        // Got data from MFIFO, now issue AXI write
                        xfer_state <= XFER_REQ_AXI;
                    end
                end

                // ----------------------------------------------------------
                XFER_MFIFO_WR: begin
                    // (Reserved for future multi-beat support)
                    decoded_ready_r <= 1'b0;
                end

                // ----------------------------------------------------------
                // Transfer complete — auto-increment addresses, advance PC
                // ----------------------------------------------------------
                XFER_COMPLETE: begin
                    // Address auto-increment
                    if (xfer_is_load && src_inc) begin
                        regs.SA <= regs.SA + ADDR_WIDTH'({16'd0, burst_size_bytes} * ADDR_WIDTH'(src_burst_len + 1));
                    end else if (!xfer_is_load && regs.CC[CC_DST_INC_BIT]) begin
                        regs.DA <= regs.DA + ADDR_WIDTH'({16'd0, burst_size_bytes} * ADDR_WIDTH'(src_burst_len + 1));
                    end

                    // Peripheral ack for store-P variants
                    if (!xfer_is_load && xfer_is_periph) begin
                        periph_ack_r  <= 1'b1;
                        periph_num_r  <= xfer_periph_num;
                    end

                    // Advance PC
                    regs.PC    <= regs.PC + ADDR_WIDTH'(decoded_instr_i.instr_len + 1);
                    xfer_state <= XFER_IDLE;
                end

                // ----------------------------------------------------------
                XFER_FAULT: begin
                    xfer_state <= XFER_IDLE;
                end

                default: xfer_state <= XFER_IDLE;
            endcase
        end
    end

endmodule : dma330_channel_thread
