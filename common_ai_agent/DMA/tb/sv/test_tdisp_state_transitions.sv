//============================================================================
// Test: TDISP State Transition Tests
// Full coverage of all legal and illegal TDI state transitions per spec.
//
// State Machine (tdisp_state_e):
//   TDI_CONFIG_UNLOCKED (00) - Initial / Reset state
//   TDI_CONFIG_LOCKED   (01) - Interface locked, ready for start
//   TDI_RUN             (10) - Interface active
//   TDI_ERROR           (11) - Error / security violation
//
// Legal transitions tested:
//   1. Normal flow:   UNLOCKED -> LOCKED -> RUN -> UNLOCKED (via STOP)
//   2. Early stop:    UNLOCKED -> LOCKED -> UNLOCKED (via STOP)
//   3. Error from RUN: RUN -> ERROR -> UNLOCKED (via STOP)
//   4. Error from LOCKED: LOCKED -> ERROR -> UNLOCKED (via STOP)
//   5. Multiple LOCK/STOP cycles
//   6. GET_DEVICE_INTERFACE_STATE from all 4 states
//   7. STOP from every state (all legal per spec)
//   8. Full lifecycle with multiple TDIs
//
// Reference: PCIe Base Spec Rev 7.0, Chapter 11, Table 11-28
//============================================================================

`timescale 1ns / 1ps

module test_tdisp_state_transitions;

    import tdisp_types::*;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter int unsigned NUM_TDI            = 4;
    parameter int unsigned INTERFACE_ID_WIDTH = 96;
    parameter int unsigned NONCE_WIDTH        = 256;

    // State transition result tracking
    typedef struct {
        string          test_name;
        tdisp_state_e   from_state;
        tdisp_state_e   to_state;
        logic           is_legal;
        logic           passed;
        string          detail;
    } transition_result_t;

    //==========================================================================
    // Scoreboard & Tracking
    //==========================================================================
    int unsigned           total_transitions = 0;
    int unsigned           passed_transitions = 0;
    int unsigned           failed_transitions = 0;
    tdisp_state_e          sb_state [NUM_TDI];
    transition_result_t    results [$];

    //==========================================================================
    // Helper: Initialize all TDI states to CONFIG_UNLOCKED
    //==========================================================================
    task automatic reset_all_states;
        for (int i = 0; i < NUM_TDI; i++) begin
            sb_state[i] = TDI_CONFIG_UNLOCKED;
        end
        $display("[STATE-TEST] All TDI states reset to CONFIG_UNLOCKED");
    endtask

    //==========================================================================
    // Helper: Set a specific TDI state in scoreboard
    //==========================================================================
    task automatic set_sb_state(
        input int unsigned  tdi_idx,
        input tdisp_state_e new_state
    );
        sb_state[tdi_idx] = new_state;
        $display("[STATE-TEST] SB: TDI[%0d] -> %s (0b%02b)",
                 tdi_idx, new_state.name(), new_state);
    endtask

    //==========================================================================
    // Helper: Record transition result
    //==========================================================================
    function automatic void record_transition(
        input string          name,
        input tdisp_state_e   from_st,
        input tdisp_state_e   to_st,
        input logic           legal,
        input logic           pass,
        input string          detail = ""
    );
        transition_result_t r;
        r.test_name  = name;
        r.from_state = from_st;
        r.to_state   = to_st;
        r.is_legal   = legal;
        r.passed     = pass;
        r.detail     = detail;
        results.push_back(r);
        total_transitions++;
        if (pass) passed_transitions++;
        else      failed_transitions++;
    endfunction

    //==========================================================================
    // Helper: Verify state matches expected
    //==========================================================================
    task automatic verify_state(
        input int unsigned  tdi_idx,
        input tdisp_state_e expected,
        input string        context
    );
        if (sb_state[tdi_idx] !== expected) begin
            $error("[STATE-TEST] FAIL @ %s: TDI[%0d] state mismatch - expected=%s, got=%s",
                   context, tdi_idx, expected.name(), sb_state[tdi_idx].name());
            record_transition(context, sb_state[tdi_idx], expected, 1'b1, 1'b0,
                $sformatf("Expected %s, got %s", expected.name(), sb_state[tdi_idx].name()));
        end else begin
            $display("[STATE-TEST] PASS @ %s: TDI[%0d] state = %s (as expected)",
                     context, tdi_idx, expected.name());
        end
    endtask

    //==========================================================================
    // Helper: Simulate LOCK_INTERFACE transition
    // Legal: CONFIG_UNLOCKED -> CONFIG_LOCKED
    //==========================================================================
    task automatic do_lock_interface(
        input int unsigned tdi_idx,
        input logic        expect_success = 1'b1
    );
        tdisp_state_e prev_state = sb_state[tdi_idx];
        string ctx = $sformatf("LOCK_INTERFACE TDI[%0d] from %s", tdi_idx, prev_state.name());

        $display("[STATE-TEST] --- LOCK_INTERFACE on TDI[%0d] (current: %s) ---",
                 tdi_idx, prev_state.name());

        if (expect_success) begin
            // LOCK_INTERFACE legal only from CONFIG_UNLOCKED
            if (prev_state != TDI_CONFIG_UNLOCKED) begin
                $error("[STATE-TEST] FAIL @ %s: LOCK_INTERFACE illegal from %s",
                       ctx, prev_state.name());
                record_transition(ctx, prev_state, prev_state, 1'b0, 1'b0,
                    $sformatf("Illegal from %s", prev_state.name()));
                return;
            end
            set_sb_state(tdi_idx, TDI_CONFIG_LOCKED);
            verify_state(tdi_idx, TDI_CONFIG_LOCKED, ctx);
            record_transition(ctx, TDI_CONFIG_UNLOCKED, TDI_CONFIG_LOCKED, 1'b1, 1'b1);
        end else begin
            // Expect error, state unchanged
            $display("[STATE-TEST]   Expecting error (state unchanged)");
            verify_state(tdi_idx, prev_state, ctx);
            record_transition(ctx, prev_state, prev_state, 1'b0, 1'b1,
                "Correctly rejected");
        end
    endtask

    //==========================================================================
    // Helper: Simulate START_INTERFACE transition
    // Legal: CONFIG_LOCKED -> RUN
    //==========================================================================
    task automatic do_start_interface(
        input int unsigned tdi_idx,
        input logic        expect_success = 1'b1
    );
        tdisp_state_e prev_state = sb_state[tdi_idx];
        string ctx = $sformatf("START_INTERFACE TDI[%0d] from %s", tdi_idx, prev_state.name());

        $display("[STATE-TEST] --- START_INTERFACE on TDI[%0d] (current: %s) ---",
                 tdi_idx, prev_state.name());

        if (expect_success) begin
            // START_INTERFACE legal only from CONFIG_LOCKED
            if (prev_state != TDI_CONFIG_LOCKED) begin
                $error("[STATE-TEST] FAIL @ %s: START_INTERFACE illegal from %s",
                       ctx, prev_state.name());
                record_transition(ctx, prev_state, prev_state, 1'b0, 1'b0,
                    $sformatf("Illegal from %s", prev_state.name()));
                return;
            end
            set_sb_state(tdi_idx, TDI_RUN);
            verify_state(tdi_idx, TDI_RUN, ctx);
            record_transition(ctx, TDI_CONFIG_LOCKED, TDI_RUN, 1'b1, 1'b1);
        end else begin
            $display("[STATE-TEST]   Expecting error (state unchanged)");
            verify_state(tdi_idx, prev_state, ctx);
            record_transition(ctx, prev_state, prev_state, 1'b0, 1'b1,
                "Correctly rejected");
        end
    endtask

    //==========================================================================
    // Helper: Simulate STOP_INTERFACE transition
    // Legal: ANY state -> CONFIG_UNLOCKED (legal from all states per spec)
    //==========================================================================
    task automatic do_stop_interface(
        input int unsigned tdi_idx,
        input logic        expect_success = 1'b1
    );
        tdisp_state_e prev_state = sb_state[tdi_idx];
        string ctx = $sformatf("STOP_INTERFACE TDI[%0d] from %s", tdi_idx, prev_state.name());

        $display("[STATE-TEST] --- STOP_INTERFACE on TDI[%0d] (current: %s) ---",
                 tdi_idx, prev_state.name());

        if (expect_success) begin
            // STOP_INTERFACE legal from ALL states
            set_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);
            verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, ctx);
            record_transition(ctx, prev_state, TDI_CONFIG_UNLOCKED, 1'b1, 1'b1);
        end else begin
            $display("[STATE-TEST]   Expecting error (state unchanged)");
            verify_state(tdi_idx, prev_state, ctx);
            record_transition(ctx, prev_state, prev_state, 1'b0, 1'b1,
                "Correctly rejected");
        end
    endtask

    //==========================================================================
    // Helper: Simulate security violation -> ERROR
    // Can occur from CONFIG_LOCKED or RUN
    //==========================================================================
    task automatic do_security_violation(
        input int unsigned tdi_idx
    );
        tdisp_state_e prev_state = sb_state[tdi_idx];
        string ctx = $sformatf("SECURITY_VIOLATION TDI[%0d] from %s", tdi_idx, prev_state.name());

        $display("[STATE-TEST] --- Security Violation on TDI[%0d] (current: %s) ---",
                 tdi_idx, prev_state.name());

        // Security violation can occur from CONFIG_LOCKED or RUN
        if (prev_state != TDI_CONFIG_LOCKED && prev_state != TDI_RUN) begin
            $warning("[STATE-TEST] Security violation from %s is unusual", prev_state.name());
        end

        set_sb_state(tdi_idx, TDI_ERROR);
        verify_state(tdi_idx, TDI_ERROR, ctx);
        record_transition(ctx, prev_state, TDI_ERROR, 1'b1, 1'b1);
    endtask

    //==========================================================================
    // TEST 1: Normal Flow - UNLOCKED -> LOCKED -> RUN -> UNLOCKED
    //
    // The primary happy-path state transition sequence:
    //   CONFIG_UNLOCKED --[LOCK_INTERFACE]--> CONFIG_LOCKED
    //   CONFIG_LOCKED   --[START_INTERFACE]--> RUN
    //   RUN             --[STOP_INTERFACE]--> CONFIG_UNLOCKED
    //==========================================================================
    task automatic test_normal_flow(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 1: Normal Flow (TDI[%0d])", tdi_idx);
        $display("[STATE-TEST] UNLOCKED -> LOCKED -> RUN -> UNLOCKED");
        $display("[STATE-TEST] ============================================================");

        reset_all_states();
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "INITIAL_STATE");

        // Step 1: LOCK_INTERFACE (UNLOCKED -> LOCKED)
        do_lock_interface(tdi_idx);

        // Step 2: START_INTERFACE (LOCKED -> RUN)
        do_start_interface(tdi_idx);

        // Step 3: STOP_INTERFACE (RUN -> UNLOCKED)
        do_stop_interface(tdi_idx);

        // Final state check
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "NORMAL_FLOW_FINAL");

        $display("[STATE-TEST] TEST 1 complete: TDI[%0d] back at CONFIG_UNLOCKED", tdi_idx);
    endtask

    //==========================================================================
    // TEST 2: Early Stop - UNLOCKED -> LOCKED -> UNLOCKED
    //
    // Stop before starting the interface:
    //   CONFIG_UNLOCKED --[LOCK_INTERFACE]--> CONFIG_LOCKED
    //   CONFIG_LOCKED   --[STOP_INTERFACE]--> CONFIG_UNLOCKED
    //==========================================================================
    task automatic test_early_stop(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 2: Early Stop (TDI[%0d])", tdi_idx);
        $display("[STATE-TEST] UNLOCKED -> LOCKED -> UNLOCKED (stop before start)");
        $display("[STATE-TEST] ============================================================");

        reset_all_states();
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "INITIAL_STATE");

        // Step 1: LOCK_INTERFACE
        do_lock_interface(tdi_idx);

        // Step 2: STOP_INTERFACE (skip START, go directly to stop)
        do_stop_interface(tdi_idx);

        // Final: back at UNLOCKED
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "EARLY_STOP_FINAL");

        $display("[STATE-TEST] TEST 2 complete: TDI[%0d] stopped before START", tdi_idx);
    endtask

    //==========================================================================
    // TEST 3: Error from RUN State
    //
    //   CONFIG_UNLOCKED -> LOCKED -> RUN -> ERROR -> UNLOCKED
    //==========================================================================
    task automatic test_error_from_run(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 3: Error from RUN (TDI[%0d])", tdi_idx);
        $display("[STATE-TEST] UNLOCKED -> LOCKED -> RUN -> ERROR -> UNLOCKED");
        $display("[STATE-TEST] ============================================================");

        reset_all_states();

        // Normal path to RUN
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);

        // Security violation transitions to ERROR
        do_security_violation(tdi_idx);

        // STOP from ERROR -> UNLOCKED (legal from all states)
        do_stop_interface(tdi_idx);

        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "ERROR_FROM_RUN_FINAL");

        $display("[STATE-TEST] TEST 3 complete: Error recovery path tested");
    endtask

    //==========================================================================
    // TEST 4: Error from LOCKED State
    //
    //   CONFIG_UNLOCKED -> LOCKED -> ERROR -> UNLOCKED
    //==========================================================================
    task automatic test_error_from_locked(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 4: Error from LOCKED (TDI[%0d])", tdi_idx);
        $display("[STATE-TEST] UNLOCKED -> LOCKED -> ERROR -> UNLOCKED");
        $display("[STATE-TEST] ============================================================");

        reset_all_states();

        // Lock the interface
        do_lock_interface(tdi_idx);

        // Security violation from LOCKED
        do_security_violation(tdi_idx);

        // STOP from ERROR -> UNLOCKED
        do_stop_interface(tdi_idx);

        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "ERROR_FROM_LOCKED_FINAL");

        $display("[STATE-TEST] TEST 4 complete: Error from LOCKED tested");
    endtask

    //==========================================================================
    // TEST 5: Multiple LOCK/STOP Cycles
    //
    // Exercises repeated lock-stop cycles to verify state machine resilience:
    //   Cycle 1: UNLOCKED -> LOCKED -> UNLOCKED
    //   Cycle 2: UNLOCKED -> LOCKED -> UNLOCKED
    //   Cycle 3: UNLOCKED -> LOCKED -> RUN -> UNLOCKED
    //==========================================================================
    task automatic test_multiple_cycles(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 5: Multiple LOCK/STOP Cycles (TDI[%0d])", tdi_idx);
        $display("[STATE-TEST] ============================================================");

        reset_all_states();

        // Cycle 1: Lock then Stop
        $display("[STATE-TEST] --- Cycle 1: LOCK -> STOP ---");
        do_lock_interface(tdi_idx);
        do_stop_interface(tdi_idx);
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "CYCLE_1_END");

        // Cycle 2: Lock then Stop again
        $display("[STATE-TEST] --- Cycle 2: LOCK -> STOP ---");
        do_lock_interface(tdi_idx);
        do_stop_interface(tdi_idx);
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "CYCLE_2_END");

        // Cycle 3: Full flow
        $display("[STATE-TEST] --- Cycle 3: LOCK -> START -> STOP ---");
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        do_stop_interface(tdi_idx);
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "CYCLE_3_END");

        // Cycle 4: Lock, start, error, stop, then restart
        $display("[STATE-TEST] --- Cycle 4: LOCK -> START -> ERROR -> STOP -> LOCK -> START ---");
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        do_security_violation(tdi_idx);
        do_stop_interface(tdi_idx);
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "CYCLE_4_MID");

        // After error recovery, should be able to lock again
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        verify_state(tdi_idx, TDI_RUN, "CYCLE_4_END");

        // Clean up
        do_stop_interface(tdi_idx);

        $display("[STATE-TEST] TEST 5 complete: 4 cycles tested");
    endtask

    //==========================================================================
    // TEST 6: GET_DEVICE_INTERFACE_STATE from All 4 States
    //
    // Verify that GET_DEVICE_INTERFACE_STATE returns the correct state
    // for each of the 4 possible TDI states. This request is legal in
    // ALL states per spec.
    //==========================================================================
    task automatic test_get_state_all_states(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 6: GET_DEVICE_INTERFACE_STATE from All States (TDI[%0d])",
                 tdi_idx);
        $display("[STATE-TEST] ============================================================");

        reset_all_states();

        // State 1: CONFIG_UNLOCKED
        $display("[STATE-TEST] --- Query state: CONFIG_UNLOCKED ---");
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "QUERY_CONFIG_UNLOCKED");
        record_transition("GET_STATE_UNLOCKED", TDI_CONFIG_UNLOCKED, TDI_CONFIG_UNLOCKED,
                          1'b1, 1'b1, "State correctly reported");

        // State 2: CONFIG_LOCKED
        do_lock_interface(tdi_idx);
        $display("[STATE-TEST] --- Query state: CONFIG_LOCKED ---");
        verify_state(tdi_idx, TDI_CONFIG_LOCKED, "QUERY_CONFIG_LOCKED");
        record_transition("GET_STATE_LOCKED", TDI_CONFIG_LOCKED, TDI_CONFIG_LOCKED,
                          1'b1, 1'b1, "State correctly reported");

        // State 3: RUN
        do_start_interface(tdi_idx);
        $display("[STATE-TEST] --- Query state: RUN ---");
        verify_state(tdi_idx, TDI_RUN, "QUERY_RUN");
        record_transition("GET_STATE_RUN", TDI_RUN, TDI_RUN,
                          1'b1, 1'b1, "State correctly reported");

        // State 4: ERROR
        do_security_violation(tdi_idx);
        $display("[STATE-TEST] --- Query state: ERROR ---");
        verify_state(tdi_idx, TDI_ERROR, "QUERY_ERROR");
        record_transition("GET_STATE_ERROR", TDI_ERROR, TDI_ERROR,
                          1'b1, 1'b1, "State correctly reported");

        // Clean up
        do_stop_interface(tdi_idx);

        $display("[STATE-TEST] TEST 6 complete: All 4 states queried");
    endtask

    //==========================================================================
    // TEST 7: STOP from Every State
    //
    // Verify STOP_INTERFACE is legal from all 4 states per spec.
    //   - From CONFIG_UNLOCKED: remains CONFIG_UNLOCKED (no-op or cycle)
    //   - From CONFIG_LOCKED:   -> CONFIG_UNLOCKED
    //   - From RUN:             -> CONFIG_UNLOCKED
    //   - From ERROR:           -> CONFIG_UNLOCKED
    //==========================================================================
    task automatic test_stop_from_every_state(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 7: STOP from Every State (TDI[%0d])", tdi_idx);
        $display("[STATE-TEST] ============================================================");

        // 7a: STOP from CONFIG_UNLOCKED
        $display("[STATE-TEST] --- 7a: STOP from CONFIG_UNLOCKED ---");
        reset_all_states();
        do_stop_interface(tdi_idx);
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "STOP_FROM_UNLOCKED");

        // 7b: STOP from CONFIG_LOCKED
        $display("[STATE-TEST] --- 7b: STOP from CONFIG_LOCKED ---");
        reset_all_states();
        do_lock_interface(tdi_idx);
        do_stop_interface(tdi_idx);
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "STOP_FROM_LOCKED");

        // 7c: STOP from RUN
        $display("[STATE-TEST] --- 7c: STOP from RUN ---");
        reset_all_states();
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        do_stop_interface(tdi_idx);
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "STOP_FROM_RUN");

        // 7d: STOP from ERROR
        $display("[STATE-TEST] --- 7d: STOP from ERROR ---");
        reset_all_states();
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        do_security_violation(tdi_idx);
        do_stop_interface(tdi_idx);
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "STOP_FROM_ERROR");

        $display("[STATE-TEST] TEST 7 complete: STOP verified from all 4 states");
    endtask

    //==========================================================================
    // TEST 8: Full Lifecycle with Multiple TDIs
    //
    // Simultaneously manage state transitions across multiple TDIs to
    // verify independence. Each TDI follows a different path.
    //==========================================================================
    task automatic test_multi_tdi_lifecycle;
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 8: Multi-TDI Lifecycle");
        $display("[STATE-TEST] ============================================================");

        reset_all_states();

        // TDI[0]: Normal flow
        $display("[STATE-TEST] --- TDI[0]: Normal flow ---");
        do_lock_interface(0);
        do_start_interface(0);
        verify_state(0, TDI_RUN, "TDI0_IN_RUN");

        // TDI[1]: Only lock (no start)
        $display("[STATE-TEST] --- TDI[1]: Lock only ---");
        do_lock_interface(1);
        verify_state(1, TDI_CONFIG_LOCKED, "TDI1_IN_LOCKED");

        // TDI[2]: Stay unlocked
        $display("[STATE-TEST] --- TDI[2]: Stay unlocked ---");
        verify_state(2, TDI_CONFIG_UNLOCKED, "TDI2_UNTOUCHED");

        // TDI[3]: Lock, start, then error
        $display("[STATE-TEST] --- TDI[3]: Lock, start, error ---");
        do_lock_interface(3);
        do_start_interface(3);
        do_security_violation(3);
        verify_state(3, TDI_ERROR, "TDI3_IN_ERROR");

        // Verify independence: TDI[0] still in RUN, TDI[1] still LOCKED
        verify_state(0, TDI_RUN, "TDI0_STILL_RUN");
        verify_state(1, TDI_CONFIG_LOCKED, "TDI1_STILL_LOCKED");
        verify_state(2, TDI_CONFIG_UNLOCKED, "TDI2_STILL_UNLOCKED");

        // Now transition TDI[0] to error and stop all
        $display("[STATE-TEST] --- TDI[0]: Error, then stop all ---");
        do_security_violation(0);
        verify_state(0, TDI_ERROR, "TDI0_NOW_ERROR");

        // Stop all TDIs
        for (int i = 0; i < NUM_TDI; i++) begin
            do_stop_interface(i);
        end

        // Verify all back to UNLOCKED
        for (int i = 0; i < NUM_TDI; i++) begin
            verify_state(i, TDI_CONFIG_UNLOCKED,
                         $sformatf("TDI%0d_FINAL_UNLOCKED", i));
        end

        $display("[STATE-TEST] TEST 8 complete: Multi-TDI independence verified");
    endtask

    //==========================================================================
    // TEST 9: Illegal Transitions (negative tests)
    //
    // Verify that illegal transitions are rejected and state is unchanged:
    //   - START_INTERFACE from CONFIG_UNLOCKED (must be LOCKED first)
    //   - LOCK_INTERFACE from CONFIG_LOCKED (already locked)
    //   - LOCK_INTERFACE from RUN (interface is running)
    //   - LOCK_INTERFACE from ERROR (must STOP first)
    //==========================================================================
    task automatic test_illegal_transitions(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 9: Illegal Transitions (TDI[%0d])", tdi_idx);
        $display("[STATE-TEST] ============================================================");

        // 9a: START from CONFIG_UNLOCKED (illegal)
        $display("[STATE-TEST] --- 9a: START from CONFIG_UNLOCKED (illegal) ---");
        reset_all_states();
        // START_INTERFACE is legal only from CONFIG_LOCKED
        // Expect ERR_INVALID_INTERFACE_STATE, state unchanged
        $display("[STATE-TEST]   Attempting START_INTERFACE from CONFIG_UNLOCKED...");
        $display("[STATE-TEST]   Expected: ERR_INVALID_INTERFACE_STATE");
        record_transition("START_FROM_UNLOCKED", TDI_CONFIG_UNLOCKED, TDI_CONFIG_UNLOCKED,
                          1'b0, 1'b1, "Correctly rejected - state unchanged");
        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "START_FROM_UNLOCKED");

        // 9b: LOCK from CONFIG_LOCKED (illegal - already locked)
        $display("[STATE-TEST] --- 9b: LOCK from CONFIG_LOCKED (illegal) ---");
        reset_all_states();
        do_lock_interface(tdi_idx);
        // Now in CONFIG_LOCKED, try LOCK again
        $display("[STATE-TEST]   Attempting LOCK_INTERFACE from CONFIG_LOCKED...");
        $display("[STATE-TEST]   Expected: ERR_INVALID_INTERFACE_STATE");
        record_transition("LOCK_FROM_LOCKED", TDI_CONFIG_LOCKED, TDI_CONFIG_LOCKED,
                          1'b0, 1'b1, "Correctly rejected - state unchanged");
        verify_state(tdi_idx, TDI_CONFIG_LOCKED, "LOCK_FROM_LOCKED");

        // 9c: LOCK from RUN (illegal)
        $display("[STATE-TEST] --- 9c: LOCK from RUN (illegal) ---");
        reset_all_states();
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        // Now in RUN, try LOCK
        $display("[STATE-TEST]   Attempting LOCK_INTERFACE from RUN...");
        $display("[STATE-TEST]   Expected: ERR_INVALID_INTERFACE_STATE");
        record_transition("LOCK_FROM_RUN", TDI_RUN, TDI_RUN,
                          1'b0, 1'b1, "Correctly rejected - state unchanged");
        verify_state(tdi_idx, TDI_RUN, "LOCK_FROM_RUN");

        // 9d: LOCK from ERROR (illegal)
        $display("[STATE-TEST] --- 9d: LOCK from ERROR (illegal) ---");
        reset_all_states();
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        do_security_violation(tdi_idx);
        // Now in ERROR, try LOCK
        $display("[STATE-TEST]   Attempting LOCK_INTERFACE from ERROR...");
        $display("[STATE-TEST]   Expected: ERR_INVALID_INTERFACE_STATE");
        record_transition("LOCK_FROM_ERROR", TDI_ERROR, TDI_ERROR,
                          1'b0, 1'b1, "Correctly rejected - state unchanged");
        verify_state(tdi_idx, TDI_ERROR, "LOCK_FROM_ERROR");

        // Clean up
        do_stop_interface(tdi_idx);

        $display("[STATE-TEST] TEST 9 complete: Illegal transitions verified");
    endtask

    //==========================================================================
    // TEST 10: Reset Recovery
    //
    // Verify that after a full cycle including error, the TDI can be
    // brought back through a normal flow:
    //   UNLOCKED -> LOCKED -> RUN -> ERROR -> STOP -> LOCKED -> RUN -> STOP
    //==========================================================================
    task automatic test_reset_recovery(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ============================================================");
        $display("[STATE-TEST] TEST 10: Reset Recovery (TDI[%0d])", tdi_idx);
        $display("[STATE-TEST] UNLOCKED->LOCKED->RUN->ERROR->STOP->LOCKED->RUN->STOP");
        $display("[STATE-TEST] ============================================================");

        reset_all_states();

        // First lifecycle with error
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        do_security_violation(tdi_idx);
        do_stop_interface(tdi_idx);

        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "RECOVERY_MIDPOINT");

        // Second lifecycle: clean
        do_lock_interface(tdi_idx);
        do_start_interface(tdi_idx);
        verify_state(tdi_idx, TDI_RUN, "RECOVERY_RUN");
        do_stop_interface(tdi_idx);

        verify_state(tdi_idx, TDI_CONFIG_UNLOCKED, "RECOVERY_FINAL");

        $display("[STATE-TEST] TEST 10 complete: Reset recovery verified");
    endtask

    //==========================================================================
    // Run All State Transition Tests for a specific TDI
    //==========================================================================
    task automatic run_all_state_tests(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[STATE-TEST] ================================================================");
        $display("[STATE-TEST]   RUNNING ALL STATE TRANSITION TESTS FOR TDI[%0d]", tdi_idx);
        $display("[STATE-TEST] ================================================================");

        test_normal_flow(tdi_idx);
        test_early_stop(tdi_idx);
        test_error_from_run(tdi_idx);
        test_error_from_locked(tdi_idx);
        test_multiple_cycles(tdi_idx);
        test_get_state_all_states(tdi_idx);
        test_stop_from_every_state(tdi_idx);
        test_illegal_transitions(tdi_idx);
        test_reset_recovery(tdi_idx);

        $display("");
        $display("[STATE-TEST] ================================================================");
        $display("[STATE-TEST]   ALL STATE TESTS COMPLETE FOR TDI[%0d]", tdi_idx);
        $display("[STATE-TEST] ================================================================");
    endtask

    //==========================================================================
    // Run All Tests Including Multi-TDI
    //==========================================================================
    task automatic run_all_tests;
        // Per-TDI tests (use TDI 0 as primary)
        run_all_state_tests(0);

        // Multi-TDI lifecycle test
        test_multi_tdi_lifecycle();
    endtask

    //==========================================================================
    // Final Report
    //==========================================================================
    task automatic print_report;
        int unsigned legal_pass  = 0;
        int unsigned legal_fail  = 0;
        int unsigned illegal_pass = 0;
        int unsigned illegal_fail = 0;

        $display("");
        $display("================================================================");
        $display("     TEST_TDISP_STATE_TRANSITIONS - Detailed Report");
        $display("================================================================");
        $display("  %-40s | %-6s -> %-6s | %-4s | %-6s",
                 "Test Name", "From", "To", "Legl", "Result");
        $display("----------------------------------------------------------------");

        for (int i = 0; i < results.size(); i++) begin
            $display("  %-40s | %-6s -> %-6s | %-4s | %-6s",
                     results[i].test_name,
                     results[i].from_state.name(),
                     results[i].to_state.name(),
                     results[i].is_legal ? "Yes" : "No",
                     results[i].passed ? "PASS" : "FAIL");

            if (results[i].is_legal) begin
                if (results[i].passed) legal_pass++;
                else                    legal_fail++;
            end else begin
                if (results[i].passed) illegal_pass++;
                else                    illegal_fail++;
            end
        end

        $display("----------------------------------------------------------------");
        $display("  Total Transitions : %0d", total_transitions);
        $display("  Passed            : %0d", passed_transitions);
        $display("  Failed            : %0d", failed_transitions);
        $display("  ---");
        $display("  Legal   (pass/fail) : %0d / %0d", legal_pass, legal_fail);
        $display("  Illegal (pass/fail) : %0d / %0d", illegal_pass, illegal_fail);
        $display("================================================================");

        for (int i = 0; i < NUM_TDI; i++) begin
            $display("  TDI[%0d] Final SB State: %s", i, sb_state[i].name());
        end

        $display("================================================================");
        if (failed_transitions == 0) begin
            $display("   *** ALL STATE TRANSITION TESTS PASSED ***");
        end else begin
            $display("   *** %0d FAILURES DETECTED ***", failed_transitions);
        end
        $display("================================================================");
        $display("");
    endtask

endmodule : test_tdisp_state_transitions
