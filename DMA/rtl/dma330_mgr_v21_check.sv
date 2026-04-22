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
    // State & PC outputs
    // =========================================================================
    assign mgr_state_o = state_reg;
    assign mgr_pc_o    = pc_reg;

    // =========================================================================
    // Default output assignments (overridden in FSM later)
    // =========================================================================
    assign decoded_ready_o = 1'b1;
    assign axi_req_o       = '0;
    assign ch_start_req    = '0;
    assign ch_kill_req     = '0;
    assign event_wait_num  = '0;
    assign fault_o         = 1'b0;
    assign fault_type_o    = '0;

    // =========================================================================
    // FSM State Register
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : fsm_state
        if (!rst_n) begin
            state_reg    <= MGR_STOPPED;
            pc_reg       <= '0;
            security_reg <= 1'b0;
        end else begin
            case (state_reg)
                MGR_STOPPED: begin
                    // Wait for external start (DMAGO targeting manager)
                    // PC loaded on start
                end

                MGR_EXECUTING: begin
                    // Advance PC after each instruction consumed
                    if (decoded_valid_i && decoded_ready_o) begin
                        pc_reg <= pc_reg + ADDR_WIDTH'(decoded_instr_i.instr_len);
                    end
                end

                MGR_WAITING_FOR_EVENT: begin
                    // Blocked until event_received matches event_wait_num
                end

                MGR_FAULT_COMPLETING: begin
                    // Allow current instruction to complete, then lock
                    state_reg <= MGR_FAULT_LOCKED;
                end

                MGR_FAULT_LOCKED: begin
                    // Stuck until reset or debug intervention
                end

                default: state_reg <= MGR_STOPPED;
            endcase
        end
    end

endmodule : dma330_manager_thread
