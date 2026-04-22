// =============================================================================
// dma330_manager_thread.sv — DMA-330 Manager Thread
//
// The manager thread is the primary instruction execution engine of the
// DMA-330 controller. It fetches and decodes instructions, manages channel
// thread creation (DMAGO), handles events (WFE/SEV), and reports faults.
//
// FSM States:
//   MGR_STOPPED          — Idle, waiting for DMAGO to start execution
//   MGR_EXECUTING        — Actively fetching and executing instructions
//   MGR_WAITING_FOR_EVENT — Blocked on DMAWFE instruction
//   MGR_FAULT_COMPLETING — Completing current instruction after fault
//   MGR_FAULT_LOCKED     — Locked out due to unrecoverable fault
// =============================================================================

module dma330_manager_thread #(
    parameter int unsigned ADDR_WIDTH   = 32,
    parameter int unsigned NUM_CHANNELS = 4
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // Instruction Interface (from decoder)
    // =========================================================================
    input  dma330_pkg::decoded_instr_t    decoded_instr_i,
    input  logic                          decoded_valid_i,
    output logic                          decoded_ready_o,

    // =========================================================================
    // AXI Fetch Request (for instruction fetch)
    // =========================================================================
    output dma330_pkg::axi_req_t          axi_req_o,
    input  dma330_pkg::axi_resp_t         axi_resp_i,

    // =========================================================================
    // Channel Start Interface (DMAGO target)
    // =========================================================================
    output logic [NUM_CHANNELS-1:0]       ch_start_req,
    output logic [31:0]                   ch_start_pc [0:NUM_CHANNELS-1],
    input  logic [NUM_CHANNELS-1:0]       ch_start_ack,

    // =========================================================================
    // Channel Kill Interface
    // =========================================================================
    output logic [NUM_CHANNELS-1:0]       ch_kill_req,

    // =========================================================================
    // Event Interface
    // =========================================================================
    output logic [3:0]                    event_wait_num,
    input  logic [dma330_pkg::NUM_EVENTS-1:0] event_received,

    // =========================================================================
    // Fault Interface
    // =========================================================================
    output logic                          fault_o,
    output logic [7:0]                    fault_type_o,

    // =========================================================================
    // State Output (for debug / status)
    // =========================================================================
    output dma330_pkg::manager_state_t    mgr_state_o,
    output logic [31:0]                   mgr_pc_o,

    // =========================================================================
    // Debug Injection Interface
    // =========================================================================
    input  logic                          dbginject_valid,
    input  dma330_pkg::decoded_instr_t    dbginject_instr
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Internal State Registers
    // =========================================================================
    manager_state_t  state_reg;
    logic [31:0]     pc_reg;
    logic            security_reg;  // 0=Secure, 1=Non-secure

    // =========================================================================
    // Internal sub-state for DMAGO handshake
    // =========================================================================
    logic                          dmago_active;
    logic [$clog2(NUM_CHANNELS)-1:0] dmago_ch;

    // =========================================================================
    // Selected instruction (from decoder or debug injection)
    // =========================================================================
    decoded_instr_t cur_instr;
    logic           instr_valid;

    assign cur_instr  = dbginject_valid ? dbginject_instr : decoded_instr_i;
    assign instr_valid = dbginject_valid || decoded_valid_i;

    // =========================================================================
    // Channel number extraction helper (from periph_num field, 4 bits wide)
    // =========================================================================
    logic [$clog2(NUM_CHANNELS)-1:0] channel_num;
    logic                            channel_valid;

    assign channel_num   = cur_instr.periph_num[$clog2(NUM_CHANNELS)-1:0];
    assign channel_valid = (cur_instr.periph_num < NUM_CHANNELS);

    // =========================================================================
    // State & PC outputs
    // =========================================================================
    assign mgr_state_o = state_reg;
    assign mgr_pc_o    = pc_reg;

    // =========================================================================
    // Output registers (driven by FSM combinational + sequential logic)
    // =========================================================================
    logic [NUM_CHANNELS-1:0] ch_start_req_r;
    logic [31:0]             ch_start_pc_r [0:NUM_CHANNELS-1];
    logic [NUM_CHANNELS-1:0] ch_kill_req_r;
    logic [3:0]              event_wait_num_r;
    logic                    fault_r;
    logic [7:0]              fault_type_r;
    logic                    decoded_ready_r;

    assign decoded_ready_o = decoded_ready_r;
    assign ch_start_req    = ch_start_req_r;
    assign ch_start_pc     = ch_start_pc_r;
    assign ch_kill_req     = ch_kill_req_r;
    assign event_wait_num  = event_wait_num_r;
    assign fault_o         = fault_r;
    assign fault_type_o    = fault_type_r;

    // AXI fetch request: issue when EXECUTING and need instruction
    assign axi_req_o = '0;  // Instruction fetch handled by cache/decoder upstream

    // =========================================================================
    // FSM — Sequential logic
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : fsm_state
        if (!rst_n) begin
            state_reg      <= MGR_STOPPED;
            pc_reg         <= '0;
            security_reg   <= 1'b0;
            dmago_active   <= 1'b0;
            dmago_ch       <= '0;
            ch_start_req_r <= '0;
            ch_start_pc_r  <= '{default: '0};
            ch_kill_req_r  <= '0;
            event_wait_num_r <= '0;
            fault_r        <= 1'b0;
            fault_type_r   <= '0;
            decoded_ready_r <= 1'b1;
        end else begin
            // Default: clear pulse signals
            ch_start_req_r <= '0;
            ch_kill_req_r  <= '0;
            fault_r        <= 1'b0;

            case (state_reg)
                // ----------------------------------------------------------
                // MGR_STOPPED: wait for external DMAGO targeting manager
                // ----------------------------------------------------------
                MGR_STOPPED: begin
                    decoded_ready_r <= 1'b0;
                    // Manager is started externally; PC is set externally
                    // (via dbginject or separate start-mgr port)
                end

                // ----------------------------------------------------------
                // MGR_EXECUTING: fetch-decode-execute loop
                // ----------------------------------------------------------
                MGR_EXECUTING: begin
                    decoded_ready_r <= 1'b1;

                    if (dmago_active) begin
                        // Waiting for DMAGO channel start acknowledgment
                        decoded_ready_r <= 1'b0;
                        if (ch_start_ack[dmago_ch]) begin
                            dmago_active <= 1'b0;
                            pc_reg       <= pc_reg + ADDR_WIDTH'(cur_instr.instr_len + 1);
                            decoded_ready_r <= 1'b1;
                        end
                    end else if (instr_valid) begin
                        case (cur_instr.opcode)
                            // --------------------------------------------------
                            // DMAEND: stop execution
                            // --------------------------------------------------
                            OPC_DMAEND: begin
                                state_reg      <= MGR_STOPPED;
                                decoded_ready_r <= 1'b0;
                            end

                            // --------------------------------------------------
                            // DMANOP: just advance PC
                            // --------------------------------------------------
                            OPC_DMANOP: begin
                                pc_reg <= pc_reg + ADDR_WIDTH'(cur_instr.instr_len + 1);
                            end

                            // --------------------------------------------------
                            // DMARMB / DMAWMB: advance PC (barrier handled externally)
                            // --------------------------------------------------
                            OPC_DMARMB,
                            OPC_DMAWMB: begin
                                pc_reg <= pc_reg + ADDR_WIDTH'(cur_instr.instr_len + 1);
                            end

                            // --------------------------------------------------
                            // DMAGO: start a channel thread
                            //   periph_num[5:3] = channel number
                            //   imm32           = starting PC
                            // --------------------------------------------------
                            OPC_DMAGO: begin
                                if (!channel_valid) begin
                                    // Invalid channel number → fault
                                    fault_r      <= 1'b1;
                                    fault_type_r <= 8'h01;  // INVALID_CHANNEL
                                    state_reg    <= MGR_FAULT_COMPLETING;
                                end else begin
                                    // Security check: if manager is secure-only
                                    // and NS bit is set, fault
                                    if (security_reg && cur_instr.periph_num[0]) begin
                                        fault_r      <= 1'b1;
                                        fault_type_r <= 8'h02;  // SECURITY_VIOLATION
                                        state_reg    <= MGR_FAULT_COMPLETING;
                                    end else begin
                                        // Start the channel
                                        dmago_active          <= 1'b1;
                                        dmago_ch              <= channel_num;
                                        ch_start_req_r[channel_num] <= 1'b1;
                                        ch_start_pc_r[channel_num]  <= cur_instr.imm32;
                                        decoded_ready_r       <= 1'b0;
                                    end
                                end
                            end

                            // --------------------------------------------------
                            // DMAWFE: wait for event
                            //   event_num = which event to wait for
                            // --------------------------------------------------
                            OPC_DMAWFE: begin
                                event_wait_num_r <= cur_instr.event_num;
                                state_reg        <= MGR_WAITING_FOR_EVENT;
                                decoded_ready_r  <= 1'b0;
                            end

                            // --------------------------------------------------
                            // DMAKILL: kill a channel thread
                            //   periph_num = channel number (from DMAGO encoding)
                            // --------------------------------------------------
                            OPC_DMAKILL: begin
                                if (channel_valid) begin
                                    ch_kill_req_r[channel_num] <= 1'b1;
                                end
                                pc_reg <= pc_reg + ADDR_WIDTH'(cur_instr.instr_len + 1);
                            end

                            // --------------------------------------------------
                            // Other instructions (DMASEV, DMAMOV, DMALP, etc.)
                            // handled in later tasks — just advance PC for now
                            // --------------------------------------------------
                            default: begin
                                pc_reg <= pc_reg + ADDR_WIDTH'(cur_instr.instr_len + 1);
                            end
                        endcase
                    end
                end

                // ----------------------------------------------------------
                // MGR_WAITING_FOR_EVENT: blocked on DMAWFE
                // ----------------------------------------------------------
                MGR_WAITING_FOR_EVENT: begin
                    decoded_ready_r <= 1'b0;
                    if (event_received[event_wait_num_r]) begin
                        // Event received — resume execution
                        state_reg <= MGR_EXECUTING;
                        pc_reg    <= pc_reg + ADDR_WIDTH'(cur_instr.instr_len + 1);
                    end
                end

                // ----------------------------------------------------------
                // MGR_FAULT_COMPLETING: allow current op to drain
                // ----------------------------------------------------------
                MGR_FAULT_COMPLETING: begin
                    decoded_ready_r <= 1'b0;
                    state_reg       <= MGR_FAULT_LOCKED;
                end

                // ----------------------------------------------------------
                // MGR_FAULT_LOCKED: stuck until reset or debug
                // ----------------------------------------------------------
                MGR_FAULT_LOCKED: begin
                    decoded_ready_r <= 1'b0;
                    fault_r         <= 1'b1;  // hold fault high while locked
                end

                default: state_reg <= MGR_STOPPED;
            endcase
        end
    end

endmodule : dma330_manager_thread
