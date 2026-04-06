//============================================================================
// TDISP FSM - TDI State Machine
// Manages per-TDI state transitions per PCIe Base Spec Rev 7.0, Chapter 11
// Legal states per message type defined in Table 11-4
//============================================================================

module tdisp_fsm #(
    parameter int unsigned NUM_TDI = 4
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //--- Per-TDI state transition interface ---
    input  logic [$clog2(NUM_TDI)-1:0]      tdi_index_i,       // Which TDI to operate on
    input  logic                            transition_req_i,   // Request a state transition
    input  tdisp_types::tdisp_state_e       target_state_i,     // Target state for transition
    input  tdisp_types::tdisp_req_code_e    msg_code_i,         // Message type that triggered request
    input  logic                            security_violation_i,// Signal security violation
    input  logic [$clog2(NUM_TDI)-1:0]      violation_tdi_i,    // TDI index with violation

    //--- Per-TDI state outputs ---
    output tdisp_types::tdisp_state_e       tdi_state_o  [NUM_TDI], // Current state per TDI
    output logic                            transition_ack_o,   // Transition accepted
    output logic                            transition_err_o,   // Transition rejected (illegal)

    //--- Legal state check for incoming messages ---
    input  logic [$clog2(NUM_TDI)-1:0]      chk_tdi_index_i,
    input  tdisp_types::tdisp_req_code_e    chk_msg_code_i,
    output logic                            chk_legal_o         // 1 = message legal in current state
);

    import tdisp_types::*;

    //==========================================================================
    // State registers - one per TDI
    //==========================================================================
    tdisp_state_e tdi_state [NUM_TDI];
    tdisp_state_e tdi_state_next;

    //==========================================================================
    // Legal state table per message type (Table 11-4)
    // Returns 1 if the message is legal in the given TDI state
    //==========================================================================
    function automatic logic is_msg_legal_in_state(
        input tdisp_req_code_e msg_code,
        input tdisp_state_e    state
    );
        logic legal;
        legal = 1'b0;
        case (msg_code)
            REQ_GET_TDISP_VERSION,
            REQ_GET_TDISP_CAPABILITIES,
            REQ_VDM:
                // N/A - legal in any state
                legal = 1'b1;

            REQ_LOCK_INTERFACE:
                // Legal only in CONFIG_UNLOCKED
                legal = (state == TDI_CONFIG_UNLOCKED);

            REQ_GET_DEVICE_INTERFACE_REPORT:
                // Legal in CONFIG_LOCKED and RUN
                legal = (state == TDI_CONFIG_LOCKED || state == TDI_RUN);

            REQ_GET_DEVICE_INTERFACE_STATE:
                // Legal in CONFIG_UNLOCKED, CONFIG_LOCKED, RUN, ERROR
                legal = 1'b1;  // All states

            REQ_START_INTERFACE:
                // Legal only in CONFIG_LOCKED
                legal = (state == TDI_CONFIG_LOCKED);

            REQ_STOP_INTERFACE:
                // Legal in CONFIG_UNLOCKED, CONFIG_LOCKED, RUN, ERROR
                legal = 1'b1;  // All states

            REQ_BIND_P2P_STREAM,
            REQ_UNBIND_P2P_STREAM:
                // Legal only in RUN
                legal = (state == TDI_RUN);

            REQ_SET_MMIO_ATTRIBUTE:
                // Legal only in RUN
                legal = (state == TDI_RUN);

            REQ_SET_TDISP_CONFIG:
                // Legal only in CONFIG_UNLOCKED
                legal = (state == TDI_CONFIG_UNLOCKED);

            default:
                legal = 1'b0;
        endcase
        return legal;
    endfunction

    //==========================================================================
    // State transition validation
    // Returns 1 if the transition is valid per spec
    //==========================================================================
    function automatic logic is_transition_valid(
        input tdisp_state_e current_state,
        input tdisp_state_e target,
        input tdisp_req_code_e msg_code
    );
        logic valid;
        valid = 1'b0;
        case (current_state)
            TDI_CONFIG_UNLOCKED: begin
                // LOCK_INTERFACE moves to CONFIG_LOCKED
                // STOP_INTERFACE stays in CONFIG_UNLOCKED
                if (msg_code == REQ_LOCK_INTERFACE && target == TDI_CONFIG_LOCKED)
                    valid = 1'b1;
                else if (msg_code == REQ_STOP_INTERFACE && target == TDI_CONFIG_UNLOCKED)
                    valid = 1'b1;
            end

            TDI_CONFIG_LOCKED: begin
                // START_INTERFACE moves to RUN
                // STOP_INTERFACE moves to CONFIG_UNLOCKED
                if (msg_code == REQ_START_INTERFACE && target == TDI_RUN)
                    valid = 1'b1;
                else if (msg_code == REQ_STOP_INTERFACE && target == TDI_CONFIG_UNLOCKED)
                    valid = 1'b1;
            end

            TDI_RUN: begin
                // STOP_INTERFACE moves to CONFIG_UNLOCKED
                if (msg_code == REQ_STOP_INTERFACE && target == TDI_CONFIG_UNLOCKED)
                    valid = 1'b1;
            end

            TDI_ERROR: begin
                // STOP_INTERFACE moves to CONFIG_UNLOCKED
                if (msg_code == REQ_STOP_INTERFACE && target == TDI_CONFIG_UNLOCKED)
                    valid = 1'b1;
            end

            default: valid = 1'b0;
        endcase
        return valid;
    endfunction

    //==========================================================================
    // Sequential logic - state registers + security violation handling
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < NUM_TDI; i++) begin
                tdi_state[i] <= TDI_CONFIG_UNLOCKED;
            end
        end else begin
            //--- Handle security violation (any state -> ERROR) ---
            if (security_violation_i) begin
                tdi_state[violation_tdi_i] <= TDI_ERROR;
            end
            //--- Handle normal state transition ---
            else if (transition_req_i) begin
                if (is_transition_valid(tdi_state[tdi_index_i], target_state_i, msg_code_i)) begin
                    tdi_state[tdi_index_i] <= target_state_i;
                end
                // If transition is invalid, state remains unchanged
            end
        end
    end

    //==========================================================================
    // Combinational outputs
    //==========================================================================
    // Transition acknowledgment
    always_comb begin
        transition_ack_o = 1'b0;
        transition_err_o = 1'b0;
        if (transition_req_i) begin
            if (is_transition_valid(tdi_state[tdi_index_i], target_state_i, msg_code_i)) begin
                transition_ack_o = 1'b1;
            end else begin
                transition_err_o = 1'b1;
            end
        end
    end

    // Legal state check for incoming messages (combinational lookup)
    always_comb begin
        chk_legal_o = is_msg_legal_in_state(chk_msg_code_i, tdi_state[chk_tdi_index_i]);
    end

    // Output current states
    always_comb begin
        for (int i = 0; i < NUM_TDI; i++) begin
            tdi_state_o[i] = tdi_state[i];
        end
    end

endmodule : tdisp_fsm
