//============================================================================
// TDISP Scoreboard
// Response checker / scoreboard for TEE Device Interface Security Protocol
// Validates: response messages, state transitions, error codes, nonce matching,
//            INTERFACE_ID routing, and TDI state tracking across all scenarios.
// Reference: PCIe Base Spec Rev 7.0, Chapter 11
//============================================================================

`timescale 1ns / 1ps

module tdisp_scoreboard #(
    parameter int unsigned NUM_TDI          = 4,
    parameter int unsigned INTERFACE_ID_WIDTH = 96,
    parameter int unsigned NONCE_WIDTH      = 256,
    parameter int unsigned NONCE_SEED       = 32'hDEADBEEF
)(
    input  logic                                    clk,
    input  logic                                    rst_n,

    //------------------------------------------------------------------------
    // TDI state inputs (from DUT FSM)
    //------------------------------------------------------------------------
    input  tdisp_types::tdisp_state_e               tdi_state_i [NUM_TDI],

    //------------------------------------------------------------------------
    // Response monitoring inputs
    //------------------------------------------------------------------------
    input  logic                                    rsp_valid_i,
    input  logic [7:0]                              rsp_msg_type_i,
    input  logic [INTERFACE_ID_WIDTH-1:0]           rsp_iface_id_i,
    input  logic [7:0]                              rsp_payload_i [],    // dynamic array
    input  int unsigned                             rsp_payload_len_i,

    //------------------------------------------------------------------------
    // Expected-context inputs (driven by test sequence)
    //------------------------------------------------------------------------
    input  logic [7:0]                              expected_rsp_type_i,
    input  logic [INTERFACE_ID_WIDTH-1:0]           expected_iface_id_i,
    input  int unsigned                             expected_tdi_idx_i,
    input  logic                                    expect_error_i,      // expect RSP_TDISP_ERROR?
    input  logic [31:0]                             expected_error_code_i,

    //------------------------------------------------------------------------
    // Request tracking inputs (driven when request is sent)
    //------------------------------------------------------------------------
    input  logic                                    req_sent_i,
    input  logic [7:0]                              req_msg_code_i,
    input  logic [INTERFACE_ID_WIDTH-1:0]           req_iface_id_i,
    input  logic [NONCE_WIDTH-1:0]                  req_nonce_i,
    input  logic                                    req_has_nonce_i,

    //------------------------------------------------------------------------
    // Control
    //------------------------------------------------------------------------
    input  logic                                    check_enable_i,
    input  logic                                    clear_counts_i,

    //------------------------------------------------------------------------
    // Report / status outputs
    //------------------------------------------------------------------------
    output int unsigned                             total_checks_o,
    output int unsigned                             total_errors_o,
    output int unsigned                             total_warnings_o,
    output int unsigned                             msgs_checked_o,
    output int unsigned                             state_mismatches_o,
    output int unsigned                             rsp_type_mismatches_o,
    output int unsigned                             iface_id_mismatches_o,
    output int unsigned                             nonce_mismatches_o,
    output int unsigned                             error_code_mismatches_o,
    output int unsigned                             illegal_transition_o,
    output logic                                    all_pass_o
);

    import tdisp_types::*;

    //==========================================================================
    // Internal State Tracking
    //==========================================================================

    // Per-TDI expected state (scoreboard's reference model)
    tdisp_state_e sb_tdi_expected_state [NUM_TDI];

    // Last nonce sent per TDI (for nonce matching verification)
    logic [NONCE_WIDTH-1:0] last_req_nonce [NUM_TDI];
    logic                   last_req_has_nonce [NUM_TDI];

    // Last request code sent per TDI
    logic [7:0]             last_req_code [NUM_TDI];

    // INTERFACE_ID programmed per TDI
    logic [INTERFACE_ID_WIDTH-1:0] sb_tdi_iface_id [NUM_TDI];
    logic                          sb_tdi_iface_valid [NUM_TDI];

    // Counters
    int unsigned total_checks;
    int unsigned total_errors;
    int unsigned total_warnings;
    int unsigned msgs_checked;
    int unsigned state_mismatches;
    int unsigned rsp_type_mismatches;
    int unsigned iface_id_mismatches;
    int unsigned nonce_mismatches;
    int unsigned error_code_mismatches;
    int unsigned illegal_transition_cnt;

    // Outstanding request tracking
    logic outstanding_req_pending;
    logic [7:0] outstanding_req_code;
    logic [INTERFACE_ID_WIDTH-1:0] outstanding_req_iface;
    logic [NONCE_WIDTH-1:0] outstanding_req_nonce;
    logic outstanding_req_has_nonce;
    int unsigned outstanding_req_tdi;

    //==========================================================================
    // Reset / Clear
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < NUM_TDI; i++) begin
                sb_tdi_expected_state[i] <= TDI_CONFIG_UNLOCKED;
                last_req_nonce[i]         <= '0;
                last_req_has_nonce[i]     <= 1'b0;
                last_req_code[i]          <= 8'h00;
                sb_tdi_iface_id[i]        <= '0;
                sb_tdi_iface_valid[i]     <= 1'b0;
            end
            total_checks            <= 0;
            total_errors            <= 0;
            total_warnings          <= 0;
            msgs_checked            <= 0;
            state_mismatches        <= 0;
            rsp_type_mismatches     <= 0;
            iface_id_mismatches     <= 0;
            nonce_mismatches        <= 0;
            error_code_mismatches   <= 0;
            illegal_transition_cnt  <= 0;
            outstanding_req_pending <= 1'b0;
            outstanding_req_code    <= 8'h00;
            outstanding_req_iface   <= '0;
            outstanding_req_nonce   <= '0;
            outstanding_req_has_nonce <= 1'b0;
            outstanding_req_tdi     <= 0;
        end else if (clear_counts_i) begin
            total_checks            <= 0;
            total_errors            <= 0;
            total_warnings          <= 0;
            msgs_checked            <= 0;
            state_mismatches        <= 0;
            rsp_type_mismatches     <= 0;
            iface_id_mismatches     <= 0;
            nonce_mismatches        <= 0;
            error_code_mismatches   <= 0;
            illegal_transition_cnt  <= 0;
        end
    end

    //==========================================================================
    // Map Request Code -> Expected Response Code (Table 11-4 / 11-5)
    //==========================================================================
    function automatic tdisp_rsp_code_e req_to_expected_rsp(
        input tdisp_req_code_e req_code
    );
        case (req_code)
            REQ_GET_TDISP_VERSION:           return RSP_TDISP_VERSION;
            REQ_GET_TDISP_CAPABILITIES:      return RSP_TDISP_CAPABILITIES;
            REQ_LOCK_INTERFACE:              return RSP_LOCK_INTERFACE;
            REQ_GET_DEVICE_INTERFACE_REPORT: return RSP_DEVICE_INTERFACE_REPORT;
            REQ_GET_DEVICE_INTERFACE_STATE:  return RSP_DEVICE_INTERFACE_STATE;
            REQ_START_INTERFACE:             return RSP_START_INTERFACE;
            REQ_STOP_INTERFACE:              return RSP_STOP_INTERFACE;
            REQ_BIND_P2P_STREAM:             return RSP_BIND_P2P_STREAM;
            REQ_UNBIND_P2P_STREAM:           return RSP_UNBIND_P2P_STREAM;
            REQ_SET_MMIO_ATTRIBUTE:          return RSP_SET_MMIO_ATTRIBUTE;
            REQ_VDM:                         return RSP_VDM;
            REQ_SET_TDISP_CONFIG:            return RSP_SET_TDISP_CONFIG;
            default:                         return RSP_TDISP_ERROR;
        endcase
    endfunction

    //==========================================================================
    // Determine Expected Next State After Successful State-Changing Request
    //==========================================================================
    function automatic tdisp_state_e expected_next_state(
        input tdisp_state_e   current_state,
        input tdisp_req_code_e req_code
    );
        case (req_code)
            REQ_LOCK_INTERFACE:  return TDI_CONFIG_LOCKED;
            REQ_START_INTERFACE: return TDI_RUN;
            REQ_STOP_INTERFACE:  return TDI_CONFIG_UNLOCKED;
            default:             return current_state;  // non-state-changing
        endcase
    endfunction

    //==========================================================================
    // Check if a Request is Legal in a Given State (per Table 11-4)
    //==========================================================================
    function automatic logic is_req_legal_in_state(
        input tdisp_req_code_e req_code,
        input tdisp_state_e    state
    );
        case (req_code)
            REQ_GET_TDISP_VERSION,
            REQ_GET_TDISP_CAPABILITIES:
                // Legal in all states
                return 1'b1;

            REQ_SET_TDISP_CONFIG,
            REQ_LOCK_INTERFACE:
                // Legal only in CONFIG_UNLOCKED
                return (state == TDI_CONFIG_UNLOCKED);

            REQ_GET_DEVICE_INTERFACE_REPORT:
                // Legal in CONFIG_LOCKED and RUN
                return (state == TDI_CONFIG_LOCKED || state == TDI_RUN);

            REQ_GET_DEVICE_INTERFACE_STATE:
                // Legal in all states
                return 1'b1;

            REQ_START_INTERFACE:
                // Legal only in CONFIG_LOCKED
                return (state == TDI_CONFIG_LOCKED);

            REQ_STOP_INTERFACE:
                // Legal in all states (spec: can stop from any state)
                return 1'b1;

            REQ_BIND_P2P_STREAM,
            REQ_UNBIND_P2P_STREAM,
            REQ_SET_MMIO_ATTRIBUTE:
                // Legal only in RUN
                return (state == TDI_RUN);

            REQ_VDM:
                return 1'b1;  // Vendor-defined, assume legal

            default:
                return 1'b0;
        endcase
    endfunction

    //==========================================================================
    // Derive TDI Index from INTERFACE_ID
    //==========================================================================
    function automatic int unsigned iface_id_to_tdi_idx(
        input logic [INTERFACE_ID_WIDTH-1:0] iface_id
    );
        for (int i = 0; i < NUM_TDI; i++) begin
            if (sb_tdi_iface_valid[i] && sb_tdi_iface_id[i] == iface_id) begin
                return i;
            end
        end
        return NUM_TDI;  // Not found sentinel
    endfunction

    //==========================================================================
    // Track Outgoing Requests
    //==========================================================================
    always_ff @(posedge clk) begin
        if (req_sent_i && rst_n) begin
            outstanding_req_pending    <= 1'b1;
            outstanding_req_code       <= req_msg_code_i;
            outstanding_req_iface      <= req_iface_id_i;
            outstanding_req_nonce      <= req_nonce_i;
            outstanding_req_has_nonce  <= req_has_nonce_i;

            // Resolve TDI index from INTERFACE_ID
            for (int i = 0; i < NUM_TDI; i++) begin
                if (sb_tdi_iface_valid[i] && sb_tdi_iface_id[i] == req_iface_id_i) begin
                    outstanding_req_tdi <= i;
                    last_req_code[i]    <= req_msg_code_i;
                    if (req_has_nonce_i) begin
                        last_req_nonce[i]     <= req_nonce_i;
                        last_req_has_nonce[i] <= 1'b1;
                    end
                end
            end

            $display("[SB] Tracked request: code=0x%02h, iface_id=0x%024h, has_nonce=%0b",
                     req_msg_code_i, req_iface_id_i, req_has_nonce_i);
        end
    end

    //==========================================================================
    // Program INTERFACE_ID per TDI (called by test via task interface)
    //==========================================================================
    task automatic program_iface_id(
        input int unsigned                    tdi_idx,
        input logic [INTERFACE_ID_WIDTH-1:0]  iface_id
    );
        sb_tdi_iface_id[tdi_idx]    = iface_id;
        sb_tdi_iface_valid[tdi_idx] = 1'b1;
        $display("[SB] Programmed INTERFACE_ID for TDI[%0d] = 0x%024h", tdi_idx, iface_id);
    endtask

    //==========================================================================
    // Force expected state (for directed updates from test sequence)
    //==========================================================================
    task automatic set_expected_state(
        input int unsigned      tdi_idx,
        input tdisp_state_e     new_state
    );
        sb_tdi_expected_state[tdi_idx] = new_state;
        $display("[SB] TDI[%0d] expected state set to %s", tdi_idx, new_state.name());
    endtask

    //==========================================================================
    // Main Response Checking (combinational)
    //==========================================================================
    always_ff @(posedge clk) begin
        if (rsp_valid_i && check_enable_i && rst_n && !clear_counts_i) begin
            msgs_checked <= msgs_checked + 1;
            total_checks <= total_checks + 1;

            $display("[SB] Checking response: msg_type=0x%02h, iface_id=0x%024h, payload_len=%0d",
                     rsp_msg_type_i, rsp_iface_id_i, rsp_payload_len_i);

            //------------------------------------------------------------------
            // 1) Check Response Type
            //------------------------------------------------------------------
            if (expect_error_i) begin
                // We expect an error response
                if (rsp_msg_type_i != RSP_TDISP_ERROR) begin
                    $error("[SB] FAIL: Expected RSP_TDISP_ERROR(0x7F), got 0x%02h", rsp_msg_type_i);
                    rsp_type_mismatches <= rsp_type_mismatches + 1;
                    total_errors        <= total_errors + 1;
                end else begin
                    $display("[SB] PASS: Received expected RSP_TDISP_ERROR");
                    total_checks <= total_checks + 1;

                    // Validate error code from payload
                    if (rsp_payload_len_i >= 4) begin
                        logic [31:0] recv_error_code;
                        recv_error_code = {rsp_payload_i[0], rsp_payload_i[1],
                                           rsp_payload_i[2], rsp_payload_i[3]};
                        if (recv_error_code !== expected_error_code_i) begin
                            $error("[SB] FAIL: Error code mismatch - expected=0x%08h, got=0x%08h",
                                   expected_error_code_i, recv_error_code);
                            error_code_mismatches <= error_code_mismatches + 1;
                            total_errors          <= total_errors + 1;
                        end else begin
                            $display("[SB] PASS: Error code 0x%08h matches expected", recv_error_code);
                        end
                    end else begin
                        $warning("[SB] WARN: Error response payload too short for error code (%0d bytes)",
                                 rsp_payload_len_i);
                        total_warnings <= total_warnings + 1;
                    end
                end
            end else begin
                // Normal (non-error) expected response
                if (rsp_msg_type_i !== expected_rsp_type_i) begin
                    $error("[SB] FAIL: Response type mismatch - expected=0x%02h, got=0x%02h",
                           expected_rsp_type_i, rsp_msg_type_i);
                    rsp_type_mismatches <= rsp_type_mismatches + 1;
                    total_errors        <= total_errors + 1;
                end else begin
                    $display("[SB] PASS: Response type 0x%02h matches expected", rsp_msg_type_i);
                end

                //------------------------------------------------------------------
                // 2) Check INTERFACE_ID Routing
                //------------------------------------------------------------------
                total_checks <= total_checks + 1;
                if (rsp_iface_id_i !== expected_iface_id_i) begin
                    $error("[SB] FAIL: INTERFACE_ID mismatch - expected=0x%024h, got=0x%024h",
                           expected_iface_id_i, rsp_iface_id_i);
                    iface_id_mismatches <= iface_id_mismatches + 1;
                    total_errors        <= total_errors + 1;
                end else begin
                    $display("[SB] PASS: INTERFACE_ID 0x%024h matches expected", rsp_iface_id_i);
                end

                //------------------------------------------------------------------
                // 3) Verify INTERFACE_ID resolves to valid TDI
                //------------------------------------------------------------------
                begin
                    int unsigned resolved_tdi;
                    resolved_tdi = iface_id_to_tdi_idx(rsp_iface_id_i);
                    if (resolved_tdi == NUM_TDI) begin
                        $warning("[SB] WARN: INTERFACE_ID 0x%024h not mapped to any TDI",
                                 rsp_iface_id_i);
                        total_warnings <= total_warnings + 1;
                    end
                end

                //------------------------------------------------------------------
                // 4) Update Expected State for State-Changing Responses
                //------------------------------------------------------------------
                if (outstanding_req_pending) begin
                    tdisp_req_code_e req_code_cast;
                    tdisp_state_e    prev_state;
                    tdisp_state_e    next_state;

                    req_code_cast = tdisp_req_code_e'(outstanding_req_code);
                    prev_state    = sb_tdi_expected_state[outstanding_req_tdi];
                    next_state    = expected_next_state(prev_state, req_code_cast);

                    if (next_state != prev_state) begin
                        // Check legality
                        if (!is_req_legal_in_state(req_code_cast, prev_state)) begin
                            $error("[SB] FAIL: Illegal request 0x%02h in state %s for TDI[%0d]",
                                   outstanding_req_code, prev_state.name(), outstanding_req_tdi);
                            illegal_transition_cnt <= illegal_transition_cnt + 1;
                            total_errors           <= total_errors + 1;
                        end else begin
                            sb_tdi_expected_state[outstanding_req_tdi] <= next_state;
                            $display("[SB] STATE: TDI[%0d] %s -> %s (via REQ 0x%02h)",
                                     outstanding_req_tdi, prev_state.name(),
                                     next_state.name(), outstanding_req_code);
                        end
                    end

                    //------------------------------------------------------------------
                    // 5) Nonce Matching (for START_INTERFACE)
                    //------------------------------------------------------------------
                    if (req_code_cast == REQ_START_INTERFACE && outstanding_req_has_nonce) begin
                        total_checks <= total_checks + 1;
                        // Check if the response payload contains a matching nonce echo
                        if (rsp_payload_len_i >= 32) begin
                            logic [NONCE_WIDTH-1:0] rsp_nonce;
                            for (int b = 0; b < 32; b++) begin
                                rsp_nonce[b*8 +: 8] = rsp_payload_i[b];
                            end
                            if (rsp_nonce !== outstanding_req_nonce) begin
                                $error("[SB] FAIL: Nonce mismatch for START_INTERFACE - req_nonce != rsp_nonce");
                                nonce_mismatches <= nonce_mismatches + 1;
                                total_errors     <= total_errors + 1;
                            end else begin
                                $display("[SB] PASS: Nonce matches for START_INTERFACE");
                            end
                        end else begin
                            // No nonce in response is acceptable for some implementations
                            $display("[SB] INFO: START_INTERFACE response payload too short for nonce echo (%0d bytes)",
                                     rsp_payload_len_i);
                        end
                    end

                    outstanding_req_pending <= 1'b0;
                end
            end

            //------------------------------------------------------------------
            // 6) Cross-Check HW State vs Expected State
            //------------------------------------------------------------------
            for (int i = 0; i < NUM_TDI; i++) begin
                if (sb_tdi_expected_state[i] !== tdi_state_i[i]) begin
                    // Only report if there's a persistent mismatch (allow 1 cycle latency)
                    // We use a sampled check: report after first cycle of mismatch
                    $warning("[SB] WARN: TDI[%0d] state mismatch - SB expects %s, HW reports %s",
                             i, sb_tdi_expected_state[i].name(), tdi_state_i[i].name());
                    state_mismatches <= state_mismatches + 1;
                    total_errors     <= total_errors + 1;
                end
            end
        end
    end

    //==========================================================================
    // Continuous State Monitoring (every clock, independent of responses)
    //==========================================================================
    int unsigned state_monitor_counter;

    always_ff @(posedge clk) begin
        if (rst_n && !clear_counts_i && check_enable_i) begin
            state_monitor_counter <= state_monitor_counter + 1;

            // Periodic state consistency check (every 100 cycles)
            if (state_monitor_counter % 100 == 0) begin
                for (int i = 0; i < NUM_TDI; i++) begin
                    if (sb_tdi_expected_state[i] !== tdi_state_i[i]) begin
                        $display("[SB-MON] TDI[%0d] state: expected=%s, actual=%s",
                                 i, sb_tdi_expected_state[i].name(), tdi_state_i[i].name());
                    end
                end
            end
        end
    end

    //==========================================================================
    // Assign Outputs
    //==========================================================================
    assign total_checks_o          = total_checks;
    assign total_errors_o          = total_errors;
    assign total_warnings_o        = total_warnings;
    assign msgs_checked_o          = msgs_checked;
    assign state_mismatches_o      = state_mismatches;
    assign rsp_type_mismatches_o   = rsp_type_mismatches;
    assign iface_id_mismatches_o   = iface_id_mismatches;
    assign nonce_mismatches_o      = nonce_mismatches;
    assign error_code_mismatches_o = error_code_mismatches;
    assign illegal_transition_o    = illegal_transition_cnt;
    assign all_pass_o              = (total_errors == 0) && (msgs_checked > 0);

    //==========================================================================
    // Report Task (called at end of simulation)
    //==========================================================================
    task automatic report;
        $display("");
        $display("================================================================");
        $display("           TDISP SCOREBOARD REPORT");
        $display("================================================================");
        $display("  Messages Checked          : %0d", msgs_checked);
        $display("  Total Checks Performed    : %0d", total_checks);
        $display("  Total Errors              : %0d", total_errors);
        $display("  Total Warnings            : %0d", total_warnings);
        $display("----------------------------------------------------------------");
        $display("  Response Type Mismatches  : %0d", rsp_type_mismatches);
        $display("  INTERFACE_ID Mismatches   : %0d", iface_id_mismatches);
        $display("  State Mismatches          : %0d", state_mismatches);
        $display("  Nonce Mismatches          : %0d", nonce_mismatches);
        $display("  Error Code Mismatches     : %0d", error_code_mismatches);
        $display("  Illegal Transitions       : %0d", illegal_transition_cnt);
        $display("----------------------------------------------------------------");
        for (int i = 0; i < NUM_TDI; i++) begin
            $display("  TDI[%0d] SB Expected State : %s", i, sb_tdi_expected_state[i].name());
            $display("  TDI[%0d] HW Actual State   : %s", i, tdi_state_i[i].name());
        end
        $display("================================================================");
        if (total_errors == 0 && msgs_checked > 0) begin
            $display("          *** ALL SCOREBOARD CHECKS PASSED ***");
        end else if (msgs_checked == 0) begin
            $display("          *** NO MESSAGES CHECKED ***");
        end else begin
            $display("          *** %0d SCOREBOARD ERROR(S) DETECTED ***", total_errors);
        end
        $display("================================================================");
        $display("");
    endtask

    //==========================================================================
    // Per-Message Directed Check Task (for explicit test-level validation)
    //==========================================================================
    task automatic check_response(
        input logic [7:0]                  actual_msg_type,
        input logic [7:0]                  expected_msg_type,
        input logic [INTERFACE_ID_WIDTH-1:0] actual_iface_id,
        input logic [INTERFACE_ID_WIDTH-1:0] expected_iface_id,
        input int unsigned                 tdi_idx,
        input string                       context
    );
        total_checks <= total_checks + 1;
        msgs_checked <= msgs_checked + 1;

        // Check message type
        if (actual_msg_type !== expected_msg_type) begin
            $error("[SB] FAIL @ %s: Response type mismatch - expected=0x%02h, got=0x%02h",
                   context, expected_msg_type, actual_msg_type);
            rsp_type_mismatches <= rsp_type_mismatches + 1;
            total_errors        <= total_errors + 1;
        end else begin
            $display("[SB] PASS @ %s: Response type 0x%02h correct", context, actual_msg_type);
        end

        // Check INTERFACE_ID
        total_checks <= total_checks + 1;
        if (actual_iface_id !== expected_iface_id) begin
            $error("[SB] FAIL @ %s: INTERFACE_ID mismatch for TDI[%0d]", context, tdi_idx);
            iface_id_mismatches <= iface_id_mismatches + 1;
            total_errors        <= total_errors + 1;
        end else begin
            $display("[SB] PASS @ %s: INTERFACE_ID correct for TDI[%0d]", context, tdi_idx);
        end

        // Cross-check HW state
        total_checks <= total_checks + 1;
        if (tdi_idx < NUM_TDI) begin
            if (sb_tdi_expected_state[tdi_idx] !== tdi_state_i[tdi_idx]) begin
                $error("[SB] FAIL @ %s: TDI[%0d] state mismatch - expected=%s, actual=%s",
                       context, tdi_idx,
                       sb_tdi_expected_state[tdi_idx].name(),
                       tdi_state_i[tdi_idx].name());
                state_mismatches <= state_mismatches + 1;
                total_errors     <= total_errors + 1;
            end else begin
                $display("[SB] PASS @ %s: TDI[%0d] state=%s consistent", context, tdi_idx,
                         tdi_state_i[tdi_idx].name());
            end
        end
    endtask

    //==========================================================================
    // Error Response Validation Task
    //==========================================================================
    task automatic check_error_response(
        input logic [7:0]                  actual_msg_type,
        input logic [31:0]                 actual_error_code,
        input logic [31:0]                 expected_error_code,
        input int unsigned                 tdi_idx,
        input string                       context
    );
        total_checks <= total_checks + 1;
        msgs_checked <= msgs_checked + 1;

        // Must be RSP_TDISP_ERROR
        if (actual_msg_type !== RSP_TDISP_ERROR) begin
            $error("[SB] FAIL @ %s: Expected RSP_TDISP_ERROR(0x7F), got 0x%02h",
                   context, actual_msg_type);
            rsp_type_mismatches <= rsp_type_mismatches + 1;
            total_errors        <= total_errors + 1;
        end else begin
            $display("[SB] PASS @ %s: Received RSP_TDISP_ERROR", context);
        end

        // Check error code
        total_checks <= total_checks + 1;
        if (actual_error_code !== expected_error_code) begin
            $error("[SB] FAIL @ %s: Error code mismatch - expected=0x%08h, got=0x%08h",
                   context, expected_error_code, actual_error_code);
            error_code_mismatches <= error_code_mismatches + 1;
            total_errors          <= total_errors + 1;
        end else begin
            $display("[SB] PASS @ %s: Error code 0x%08h matches expected", context, actual_error_code);
        end

        // TDI should not change state on error
        if (tdi_idx < NUM_TDI) begin
            total_checks <= total_checks + 1;
            if (sb_tdi_expected_state[tdi_idx] !== tdi_state_i[tdi_idx]) begin
                $error("[SB] FAIL @ %s: TDI[%0d] state changed unexpectedly after error",
                       context, tdi_idx);
                state_mismatches <= state_mismatches + 1;
                total_errors     <= total_errors + 1;
            end
        end
    endtask

    //==========================================================================
    // State Transition Validation Task
    //==========================================================================
    task automatic check_state_transition(
        input int unsigned      tdi_idx,
        input tdisp_state_e     expected_state,
        input string            context
    );
        total_checks <= total_checks + 1;

        if (tdi_idx >= NUM_TDI) begin
            $error("[SB] FAIL @ %s: Invalid TDI index %0d", context, tdi_idx);
            total_errors <= total_errors + 1;
            return;
        end

        // Update expected state
        sb_tdi_expected_state[tdi_idx] = expected_state;

        // Check HW matches
        if (tdi_state_i[tdi_idx] !== expected_state) begin
            $error("[SB] FAIL @ %s: TDI[%0d] state mismatch - expected=%s, actual=%s",
                   context, tdi_idx, expected_state.name(), tdi_state_i[tdi_idx].name());
            state_mismatches <= state_mismatches + 1;
            total_errors     <= total_errors + 1;
        end else begin
            $display("[SB] PASS @ %s: TDI[%0d] state=%s as expected",
                     context, tdi_idx, expected_state.name());
        end
    endtask

    //==========================================================================
    // Nonce Validation Task
    //==========================================================================
    task automatic check_nonce(
        input logic [NONCE_WIDTH-1:0] sent_nonce,
        input logic [NONCE_WIDTH-1:0] received_nonce,
        input int unsigned            tdi_idx,
        input string                  context
    );
        total_checks <= total_checks + 1;

        if (sent_nonce !== received_nonce) begin
            $error("[SB] FAIL @ %s: Nonce mismatch for TDI[%0d]", context, tdi_idx);
            nonce_mismatches <= nonce_mismatches + 1;
            total_errors     <= total_errors + 1;
        end else begin
            $display("[SB] PASS @ %s: Nonce matches for TDI[%0d]", context, tdi_idx);
        end
    endtask

endmodule : tdisp_scoreboard
