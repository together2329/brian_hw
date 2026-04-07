// ============================================================================
// Module:    tdisp_fsm.sv
// Purpose:   TDISP TDI State Machine u2014 manages TDI state transitions per
//            PCIe 7.0 Spec Chapter 11, Table 11-4
// Spec:      PCI Express Base Specification Revision 7.0, Section 11.2/11.3
//
// State Transitions (Table 11-4):
//   CONFIG_UNLOCKED:
//     - LOCK_INTERFACE_REQUEST   u2192 CONFIG_LOCKED
//     - error_trigger            u2192 ERROR
//     - STOP_INTERFACE_REQUEST   u2192 stays CONFIG_UNLOCKED (no-op)
//   CONFIG_LOCKED:
//     - START_INTERFACE_REQUEST  u2192 RUN
//     - STOP_INTERFACE_REQUEST   u2192 CONFIG_UNLOCKED
//     - error_trigger            u2192 ERROR
//   RUN:
//     - STOP_INTERFACE_REQUEST   u2192 CONFIG_UNLOCKED
//     - error_trigger            u2192 ERROR
//   ERROR:
//     - STOP_INTERFACE_REQUEST   u2192 CONFIG_UNLOCKED
//
// Nonce Management (Section 11.3.9):
//   - Generated on CONFIG_LOCKED entry (LOCK_INTERFACE_RESPONSE)
//   - Destroyed on CONFIG_LOCKED exit (u2192CONFIG_UNLOCKED or u2192ERROR)
//   - Destroyed on RUN exit (u2192CONFIG_UNLOCKED or u2192ERROR)
//
// One instance per TDI. Replicated via generate in top-level.
// ============================================================================

module tdisp_fsm
    import tdisp_pkg::*;
#(
    parameter int TDI_INDEX = 0  // TDI instance identifier
)(
    input  logic                clk,
    input  logic                rst_n,

    // --- Transition request inputs (priority-encoded, one-hot expected) ---
    input  logic                lock_req,            // LOCK_INTERFACE success
    input  logic                start_req,           // START_INTERFACE success
    input  logic                stop_req,            // STOP_INTERFACE_REQUEST
    input  logic                error_trigger,       // Register mod / IDE failure / etc.
    input  logic                reset_to_unlocked,   // External reset (e.g., FLR, Conventional Reset)

    // --- State outputs ---
    output tdisp_tdi_state_e    current_state,
    output logic                state_is_locked,     // CONFIG_LOCKED || RUN
    output logic                state_is_run,        // RUN
    output logic                state_is_error,      // ERROR

    // --- Event outputs (pulses) ---
    output logic                ev_entered_locked,   // Pulse: just entered CONFIG_LOCKED
    output logic                ev_entered_run,      // Pulse: just entered RUN
    output logic                ev_exited_locked,    // Pulse: left CONFIG_LOCKED or RUN
    output logic                ev_entered_error,    // Pulse: just entered ERROR
    output logic                ev_nonce_valid,      // Level: nonce is valid (CONFIG_LOCKED only)

    // --- Nonce interface ---
    output logic [NONCE_WIDTH-1:0] nonce_out,        // Current START_INTERFACE_NONCE
    input  logic [NONCE_WIDTH-1:0] nonce_in          // Newly generated nonce from entropy source
);

    // =========================================================================
    // Internal state register
    // =========================================================================
    tdisp_tdi_state_e state_reg, state_next;

    // Nonce storage register
    logic [NONCE_WIDTH-1:0] nonce_reg;
    logic                   nonce_valid_reg;

    // Event pulses (registered outputs for clean timing)
    logic ev_entered_locked_d,  ev_entered_locked_q;
    logic ev_entered_run_d,     ev_entered_run_q;
    logic ev_exited_locked_d,   ev_exited_locked_q;
    logic ev_entered_error_d,   ev_entered_error_q;

    // =========================================================================
    // State Register
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_reg <= TDI_STATE_CONFIG_UNLOCKED;
        end else if (reset_to_unlocked) begin
            state_reg <= TDI_STATE_CONFIG_UNLOCKED;
        end else begin
            state_reg <= state_next;
        end
    end

    // =========================================================================
    // Next-State Logic (priority: error > stop > start > lock)
    // Error has highest priority to ensure fail-safe behavior
    // =========================================================================
    always_comb begin
        state_next = state_reg;  // Default: hold state

        case (state_reg)
            TDI_STATE_CONFIG_UNLOCKED: begin
                if (error_trigger) begin
                    state_next = TDI_STATE_ERROR;
                end else if (lock_req) begin
                    state_next = TDI_STATE_CONFIG_LOCKED;
                end
                // stop_req is a no-op (already CONFIG_UNLOCKED per spec)
            end

            TDI_STATE_CONFIG_LOCKED: begin
                if (error_trigger) begin
                    state_next = TDI_STATE_ERROR;
                end else if (stop_req) begin
                    state_next = TDI_STATE_CONFIG_UNLOCKED;
                end else if (start_req) begin
                    state_next = TDI_STATE_RUN;
                end
            end

            TDI_STATE_RUN: begin
                if (error_trigger) begin
                    state_next = TDI_STATE_ERROR;
                end else if (stop_req) begin
                    state_next = TDI_STATE_CONFIG_UNLOCKED;
                end
                // No other transitions from RUN
            end

            TDI_STATE_ERROR: begin
                if (stop_req) begin
                    state_next = TDI_STATE_CONFIG_UNLOCKED;
                end
                // error_trigger in ERROR state is a no-op (already in ERROR)
            end

            default: begin
                // Defensive: invalid state u2192 ERROR
                state_next = TDI_STATE_ERROR;
            end
        endcase
    end

    // =========================================================================
    // Nonce Management (Section 11.3.9)
    //   - Captured when entering CONFIG_LOCKED (from lock_req)
    //   - Destroyed (zeroed) when leaving CONFIG_LOCKED or RUN
    //     to any state other than RUN (i.e., u2192CONFIG_UNLOCKED or u2192ERROR)
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            nonce_reg       <= '0;
            nonce_valid_reg <= 1'b0;
        end else if (reset_to_unlocked) begin
            nonce_reg       <= '0;
            nonce_valid_reg <= 1'b0;
        end else begin
            case (state_reg)
                TDI_STATE_CONFIG_UNLOCKED: begin
                    if (state_next == TDI_STATE_CONFIG_LOCKED) begin
                        // Capture nonce on lock transition
                        nonce_reg       <= nonce_in;
                        nonce_valid_reg <= 1'b1;
                    end
                end

                TDI_STATE_CONFIG_LOCKED: begin
                    if (state_next != TDI_STATE_CONFIG_LOCKED &&
                        state_next != TDI_STATE_RUN) begin
                        // Leaving CONFIG_LOCKED u2192 destroy nonce
                        nonce_reg       <= '0;
                        nonce_valid_reg <= 1'b0;
                    end else if (state_next == TDI_STATE_RUN) begin
                        // CONFIG_LOCKED u2192 RUN: nonce consumed, invalidate
                        nonce_reg       <= '0;
                        nonce_valid_reg <= 1'b0;
                    end
                end

                TDI_STATE_RUN: begin
                    if (state_next != TDI_STATE_RUN) begin
                        // Leaving RUN u2192 destroy nonce (if still held)
                        nonce_reg       <= '0;
                        nonce_valid_reg <= 1'b0;
                    end
                end

                TDI_STATE_ERROR: begin
                    // Nonce already destroyed on entry to ERROR
                    nonce_reg       <= '0;
                    nonce_valid_reg <= 1'b0;
                end

                default: begin
                    nonce_reg       <= '0;
                    nonce_valid_reg <= 1'b0;
                end
            endcase
        end
    end

    // =========================================================================
    // Event Pulse Generation
    // =========================================================================
    always_comb begin
        ev_entered_locked_d = 1'b0;
        ev_entered_run_d    = 1'b0;
        ev_exited_locked_d  = 1'b0;
        ev_entered_error_d  = 1'b0;

        case (state_reg)
            TDI_STATE_CONFIG_UNLOCKED: begin
                if (state_next == TDI_STATE_CONFIG_LOCKED)
                    ev_entered_locked_d = 1'b1;
                if (state_next == TDI_STATE_ERROR)
                    ev_entered_error_d = 1'b1;
            end

            TDI_STATE_CONFIG_LOCKED: begin
                if (state_next == TDI_STATE_RUN) begin
                    ev_entered_run_d   = 1'b1;
                    ev_exited_locked_d = 1'b1;  // Also exiting locked state
                end
                if (state_next == TDI_STATE_CONFIG_UNLOCKED)
                    ev_exited_locked_d = 1'b1;
                if (state_next == TDI_STATE_ERROR)
                    ev_entered_error_d = 1'b1;
            end

            TDI_STATE_RUN: begin
                if (state_next == TDI_STATE_CONFIG_UNLOCKED ||
                    state_next == TDI_STATE_ERROR)
                    ev_exited_locked_d = 1'b1;
                if (state_next == TDI_STATE_ERROR)
                    ev_entered_error_d = 1'b1;
            end

            TDI_STATE_ERROR: begin
                // No special event on leaving ERROR
            end

            default: ;
        endcase
    end

    // Register event pulses
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ev_entered_locked_q <= 1'b0;
            ev_entered_run_q    <= 1'b0;
            ev_exited_locked_q  <= 1'b0;
            ev_entered_error_q  <= 1'b0;
        end else begin
            ev_entered_locked_q <= ev_entered_locked_d;
            ev_entered_run_q    <= ev_entered_run_d;
            ev_exited_locked_q  <= ev_exited_locked_d;
            ev_entered_error_q  <= ev_entered_error_d;
        end
    end

    // =========================================================================
    // Output Assignments
    // =========================================================================
    assign current_state     = state_reg;
    assign state_is_locked   = (state_reg == TDI_STATE_CONFIG_LOCKED) ||
                               (state_reg == TDI_STATE_RUN);
    assign state_is_run      = (state_reg == TDI_STATE_RUN);
    assign state_is_error    = (state_reg == TDI_STATE_ERROR);

    assign ev_entered_locked = ev_entered_locked_q;
    assign ev_entered_run    = ev_entered_run_q;
    assign ev_exited_locked  = ev_exited_locked_q;
    assign ev_entered_error  = ev_entered_error_q;

    assign ev_nonce_valid    = nonce_valid_reg;
    assign nonce_out         = nonce_reg;

    // =========================================================================
    // Assertions
    // =========================================================================
    // pragma synthesis_off
    `ifdef FORMAL
        // Assert: state should always be a legal value
        assert property (@(posedge clk) disable iff (!rst_n)
            state_reg inside {TDI_STATE_CONFIG_UNLOCKED, TDI_STATE_CONFIG_LOCKED,
                              TDI_STATE_RUN, TDI_STATE_ERROR})
        else $error("TDI[%0d] FSM entered illegal state: %0b", TDI_INDEX, state_reg);

        // Assert: LOCK_INTERFACE only legal from CONFIG_UNLOCKED
        assert property (@(posedge clk) disable iff (!rst_n)
            lock_req |-> state_reg == TDI_STATE_CONFIG_UNLOCKED)
        else $error("TDI[%0d] LOCK_INTERFACE received in illegal state: %0s",
                     TDI_INDEX, state_reg.name());

        // Assert: START_INTERFACE only legal from CONFIG_LOCKED
        assert property (@(posedge clk) disable iff (!rst_n)
            start_req |-> state_reg == TDI_STATE_CONFIG_LOCKED)
        else $error("TDI[%0d] START_INTERFACE received in illegal state: %0s",
                     TDI_INDEX, state_reg.name());

        // Assert: nonce is zero when not in CONFIG_LOCKED
        assert property (@(posedge clk) disable iff (!rst_n)
            !nonce_valid_reg |-> nonce_out == '0)
        else $error("TDI[%0d] Nonce not zeroed when invalid", TDI_INDEX);

        // Assert: lock_req and start_req are mutually exclusive
        assert property (@(posedge clk) disable iff (!rst_n)
            !(lock_req && start_req))
        else $error("TDI[%0d] lock_req and start_req asserted simultaneously", TDI_INDEX);

        // Cover: all state transitions exercised
        cover property (@(posedge clk) disable iff (!rst_n)
            state_reg == TDI_STATE_CONFIG_UNLOCKED ##1 state_reg == TDI_STATE_CONFIG_LOCKED);
        cover property (@(posedge clk) disable iff (!rst_n)
            state_reg == TDI_STATE_CONFIG_LOCKED ##1 state_reg == TDI_STATE_RUN);
        cover property (@(posedge clk) disable iff (!rst_n)
            state_reg == TDI_STATE_RUN ##1 state_reg == TDI_STATE_CONFIG_UNLOCKED);
        cover property (@(posedge clk) disable iff (!rst_n)
            state_reg == TDI_STATE_CONFIG_LOCKED ##1 state_reg == TDI_STATE_ERROR);
        cover property (@(posedge clk) disable iff (!rst_n)
            state_reg == TDI_STATE_ERROR ##1 state_reg == TDI_STATE_CONFIG_UNLOCKED);
    `endif
    // pragma synthesis_on

endmodule : tdisp_fsm
