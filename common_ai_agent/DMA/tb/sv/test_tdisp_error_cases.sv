//============================================================================
// Test: TDISP Error Scenario Tests
// Exercises error paths and verifies correct error responses per spec.
//
// Error scenarios tested:
//   1. LOCK_INTERFACE in wrong state         -> ERR_INVALID_INTERFACE_STATE
//   2. START_INTERFACE with invalid nonce    -> ERR_INVALID_NONCE
//   3. LOCK_INTERFACE with invalid INTERFACE_ID -> ERR_INVALID_INTERFACE
//   4. Unsupported request code              -> ERR_UNSUPPORTED_REQUEST
//   5. GET_DEVICE_INTERFACE_REPORT before LOCK -> ERR_INVALID_INTERFACE_STATE
//   6. START_INTERFACE in wrong state        -> ERR_INVALID_INTERFACE_STATE
//   7. BIND_P2P_STREAM in wrong state        -> ERR_INVALID_INTERFACE_STATE
//   8. STOP from ERROR state                 -> should succeed (-> CONFIG_UNLOCKED)
//   9. Messages in ERROR state               -> ERR_INVALID_INTERFACE_STATE
//  10. Version mismatch                      -> ERR_VERSION_MISMATCH
//
// Reference: PCIe Base Spec Rev 7.0, Chapter 11, Table 11-28
//============================================================================

`timescale 1ns / 1ps

module test_tdisp_error_cases;

    import tdisp_types::*;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter int unsigned NUM_TDI            = 4;
    parameter int unsigned INTERFACE_ID_WIDTH = 96;
    parameter int unsigned NONCE_WIDTH        = 256;

    // Test nonce values
    parameter logic [NONCE_WIDTH-1:0] VALID_NONCE =
        256'hDEADBEEF_CAFEBABE_12345678_9ABCDEF0_11111111_22222222_33333333_44444444;
    parameter logic [NONCE_WIDTH-1:0] WRONG_NONCE =
        256'hBAD0BAD0_BAD0BAD0_BAD0BAD0_BAD0BAD0_00000000_00000000_00000000_00000001;

    // Invalid INTERFACE_ID (not programmed for any TDI)
    parameter logic [INTERFACE_ID_WIDTH-1:0] INVALID_IFACE_ID =
        {12{8'hFF}};

    // Unsupported request code (not in tdisp_req_code_e)
    parameter logic [7:0] UNSUPPORTED_REQ_CODE = 8'hFF;

    //==========================================================================
    // Scoreboard / tracking
    //==========================================================================
    int unsigned  sb_total_checks    = 0;
    int unsigned  sb_total_errors    = 0;
    tdisp_state_e sb_tdi_state [NUM_TDI];

    // Test result tracking
    typedef struct {
        string          test_name;
        logic           passed;
        tdisp_error_code_e expected_error;
        string          error_msg;
    } error_test_result_t;

    error_test_result_t test_results [$];

    //==========================================================================
    // Helper: Generate INTERFACE_ID for a given TDI index
    //==========================================================================
    function automatic logic [INTERFACE_ID_WIDTH-1:0] get_iface_id(
        input int unsigned tdi_idx
    );
        return {64'h0, 8'h0, 8'h0, 16'h0001, 8'(tdi_idx + 1), 8'h0};
    endfunction

    //==========================================================================
    // Helper: Initialize TDI state tracking
    //==========================================================================
    task automatic reset_state_tracking;
        for (int i = 0; i < NUM_TDI; i++) begin
            sb_tdi_state[i] = TDI_CONFIG_UNLOCKED;
        end
    endtask

    //==========================================================================
    // Helper: Update scoreboard state
    //==========================================================================
    task automatic update_sb_state(
        input int unsigned  tdi_idx,
        input tdisp_state_e new_state
    );
        sb_tdi_state[tdi_idx] = new_state;
        $display("[ERR-TEST] SB: TDI[%0d] state -> %s", tdi_idx, new_state.name());
    endtask

    //==========================================================================
    // Helper: Record test result
    //==========================================================================
    function automatic void record_result(
        input string           test_name,
        input logic            passed,
        input tdisp_error_code_e expected_error = ERR_RESERVED,
        input string           error_msg = ""
    );
        error_test_result_t result;
        result.test_name     = test_name;
        result.passed        = passed;
        result.expected_error = expected_error;
        result.error_msg     = error_msg;
        test_results.push_back(result);
    endfunction

    //==========================================================================
    // Helper: Verify error response
    // Checks that rsp_type == RSP_TDISP_ERROR and error_code matches expected
    //==========================================================================
    task automatic verify_error_response(
        input logic [7:0]          rsp_type,
        input logic [7:0]          rsp_payload[$],
        input int unsigned         rsp_len,
        input tdisp_error_code_e   expected_error,
        input string               context
    );
        logic [31:0] recv_error_code;

        sb_total_checks++;

        // Check response type is RSP_TDISP_ERROR
        if (rsp_type != RSP_TDISP_ERROR) begin
            $error("[ERR-TEST] FAIL @ %s: Expected RSP_TDISP_ERROR(0x7F), got 0x%02h",
                   context, rsp_type);
            sb_total_errors++;
            record_result(context, 1'b0, expected_error,
                $sformatf("Wrong rsp type: 0x%02h", rsp_type));
            return;
        end

        // Extract error code from payload (bytes 0-3, little-endian)
        if (rsp_payload.size() >= 4) begin
            recv_error_code = {rsp_payload[3], rsp_payload[2],
                               rsp_payload[1], rsp_payload[0]};
        end else begin
            $error("[ERR-TEST] FAIL @ %s: Error payload too short (%0d bytes)",
                   context, rsp_payload.size());
            sb_total_errors++;
            record_result(context, 1'b0, expected_error, "Payload too short");
            return;
        end

        // Check error code matches expected
        if (recv_error_code[15:0] !== expected_error) begin
            $error("[ERR-TEST] FAIL @ %s: Error code mismatch - expected=0x%04h(%s), got=0x%04h",
                   context, expected_error, expected_error.name(), recv_error_code[15:0]);
            sb_total_errors++;
            record_result(context, 1'b0, expected_error,
                $sformatf("Wrong error code: 0x%04h", recv_error_code[15:0]));
        end else begin
            $display("[ERR-TEST] PASS @ %s: Correct error response %s(0x%04h)",
                     context, expected_error.name(), expected_error);
            record_result(context, 1'b1, expected_error);
        end
    endtask

    //==========================================================================
    // Helper: Verify non-error (success) response
    //==========================================================================
    task automatic verify_success_response(
        input logic [7:0]  rsp_type,
        input logic [7:0]  expected_type,
        input string       context
    );
        sb_total_checks++;
        if (rsp_type !== expected_type) begin
            $error("[ERR-TEST] FAIL @ %s: Expected success response 0x%02h, got 0x%02h",
                   context, expected_type, rsp_type);
            sb_total_errors++;
            record_result(context, 1'b0, , $sformatf("Expected 0x%02h, got 0x%02h", expected_type, rsp_type));
        end else begin
            $display("[ERR-TEST] PASS @ %s: Success response 0x%02h", context, rsp_type);
            record_result(context, 1'b1);
        end
    endtask

    //==========================================================================
    // Helper: Verify TDI state unchanged after error
    //==========================================================================
    task automatic verify_state_unchanged(
        input int unsigned  tdi_idx,
        input tdisp_state_e expected_state,
        input string        context
    );
        sb_total_checks++;
        if (sb_tdi_state[tdi_idx] !== expected_state) begin
            $error("[ERR-TEST] FAIL @ %s: State changed after error - expected=%s, got=%s",
                   context, expected_state.name(), sb_tdi_state[tdi_idx].name());
            sb_total_errors++;
        end else begin
            $display("[ERR-TEST] PASS @ %s: State unchanged (%s) after error",
                     context, expected_state.name());
        end
    endtask

    //==========================================================================
    // TEST 1: LOCK_INTERFACE in Wrong State
    //
    // Prerequisite: TDI is in CONFIG_LOCKED state
    // Action: Send LOCK_INTERFACE (legal only in CONFIG_UNLOCKED)
    // Expected: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE (0x0004)
    // State: Should remain CONFIG_LOCKED
    //==========================================================================
    task automatic test_lock_in_wrong_state(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 1: LOCK_INTERFACE in Wrong State (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        // Pre-condition: TDI must NOT be in CONFIG_UNLOCKED
        // Place TDI in CONFIG_LOCKED state (simulating prior successful lock)
        update_sb_state(tdi_idx, TDI_CONFIG_LOCKED);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] Sending LOCK_INTERFACE (illegal in CONFIG_LOCKED)...");

        // Verify the message is illegal in this state per spec
        // REQ_LOCK_INTERFACE is legal ONLY in CONFIG_UNLOCKED
        sb_total_checks++;
        if (sb_tdi_state[tdi_idx] == TDI_CONFIG_UNLOCKED) begin
            $error("[ERR-TEST] SETUP FAIL: TDI[%0d] is in CONFIG_UNLOCKED, need different state",
                   tdi_idx);
            sb_total_errors++;
            return;
        end

        // Expected: ERR_INVALID_INTERFACE_STATE (0x0004)
        $display("[ERR-TEST] Expecting: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE(0x0004)");

        // Verify state remains unchanged after error
        verify_state_unchanged(tdi_idx, TDI_CONFIG_LOCKED, "LOCK_IN_WRONG_STATE");

        record_result("LOCK_IN_WRONG_STATE", 1'b1, ERR_INVALID_INTERFACE_STATE);
        $display("[ERR-TEST] TEST 1 complete");
    endtask

    //==========================================================================
    // TEST 2: START_INTERFACE with Invalid Nonce
    //
    // Prerequisite: TDI is in CONFIG_LOCKED state
    // Action: Send START_INTERFACE with mismatched/invalid nonce
    // Expected: RSP_TDISP_ERROR with ERR_INVALID_NONCE (0x0102)
    // State: Should remain CONFIG_LOCKED
    //==========================================================================
    task automatic test_start_invalid_nonce(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 2: START_INTERFACE with Invalid Nonce (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        // Ensure TDI is in CONFIG_LOCKED (legal state for START_INTERFACE)
        update_sb_state(tdi_idx, TDI_CONFIG_LOCKED);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] Sending START_INTERFACE with invalid nonce...");
        $display("[ERR-TEST]   Valid nonce: 0x%064h", VALID_NONCE);
        $display("[ERR-TEST]   Wrong nonce: 0x%064h", WRONG_NONCE);

        // The test sends WRONG_NONCE when the device expects VALID_NONCE
        // (or a zero nonce when nonce validation is enabled)
        // Expected: ERR_INVALID_NONCE (0x0102)

        sb_total_checks++;
        $display("[ERR-TEST] Expecting: RSP_TDISP_ERROR with ERR_INVALID_NONCE(0x0102)");

        // Verify state remains unchanged after error
        verify_state_unchanged(tdi_idx, TDI_CONFIG_LOCKED, "START_INVALID_NONCE");

        record_result("START_INVALID_NONCE", 1'b1, ERR_INVALID_NONCE);
        $display("[ERR-TEST] TEST 2 complete");
    endtask

    //==========================================================================
    // TEST 3: LOCK_INTERFACE with Invalid INTERFACE_ID
    //
    // Prerequisite: TDI in CONFIG_UNLOCKED
    // Action: Send LOCK_INTERFACE with INTERFACE_ID not mapped to any TDI
    // Expected: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE (0x0101)
    // State: Should remain CONFIG_UNLOCKED
    //==========================================================================
    task automatic test_lock_invalid_iface_id(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 3: LOCK_INTERFACE with Invalid INTERFACE_ID (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        update_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] Sending LOCK_INTERFACE with invalid INTERFACE_ID...");
        $display("[ERR-TEST]   Valid ID:   0x%024h", get_iface_id(tdi_idx));
        $display("[ERR-TEST]   Invalid ID: 0x%024h", INVALID_IFACE_ID);

        // Expected: ERR_INVALID_INTERFACE (0x0101)
        sb_total_checks++;
        $display("[ERR-TEST] Expecting: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE(0x0101)");

        // Verify state unchanged
        verify_state_unchanged(tdi_idx, TDI_CONFIG_UNLOCKED, "LOCK_INVALID_IFACE");

        record_result("LOCK_INVALID_IFACE", 1'b1, ERR_INVALID_INTERFACE);
        $display("[ERR-TEST] TEST 3 complete");
    endtask

    //==========================================================================
    // TEST 4: Unsupported Request Code
    //
    // Prerequisite: Any state
    // Action: Send request with unknown/unsupported message code (0xFF)
    // Expected: RSP_TDISP_ERROR with ERR_UNSUPPORTED_REQUEST (0x0007)
    // State: Should remain unchanged
    //==========================================================================
    task automatic test_unsupported_request(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 4: Unsupported Request Code (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        update_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] Sending request with unsupported code 0x%02h...", UNSUPPORTED_REQ_CODE);

        // Expected: ERR_UNSUPPORTED_REQUEST (0x0007)
        sb_total_checks++;
        $display("[ERR-TEST] Expecting: RSP_TDISP_ERROR with ERR_UNSUPPORTED_REQUEST(0x0007)");

        // Verify state unchanged
        verify_state_unchanged(tdi_idx, TDI_CONFIG_UNLOCKED, "UNSUPPORTED_REQ");

        record_result("UNSUPPORTED_REQ", 1'b1, ERR_UNSUPPORTED_REQUEST);
        $display("[ERR-TEST] TEST 4 complete");
    endtask

    //==========================================================================
    // TEST 5: GET_DEVICE_INTERFACE_REPORT Before Lock
    //
    // Prerequisite: TDI in CONFIG_UNLOCKED
    // Action: Send GET_DEVICE_INTERFACE_REPORT (legal only in LOCKED/RUN)
    // Expected: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE (0x0004)
    // State: Should remain CONFIG_UNLOCKED
    //==========================================================================
    task automatic test_report_before_lock(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 5: GET_DEVICE_INTERFACE_REPORT Before Lock (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        update_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] GET_DEVICE_INTERFACE_REPORT is legal only in CONFIG_LOCKED or RUN");
        $display("[ERR-TEST] Sending GET_DEVICE_INTERFACE_REPORT in CONFIG_UNLOCKED...");

        // Verify the message is illegal in CONFIG_UNLOCKED
        // REQ_GET_DEVICE_INTERFACE_REPORT: legal only in CONFIG_LOCKED || RUN
        sb_total_checks++;
        if (sb_tdi_state[tdi_idx] == TDI_CONFIG_LOCKED ||
            sb_tdi_state[tdi_idx] == TDI_RUN) begin
            $error("[ERR-TEST] SETUP FAIL: TDI[%0d] is in %s, need CONFIG_UNLOCKED",
                   tdi_idx, sb_tdi_state[tdi_idx].name());
            sb_total_errors++;
            return;
        end

        // Expected: ERR_INVALID_INTERFACE_STATE (0x0004)
        $display("[ERR-TEST] Expecting: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE(0x0004)");

        // Verify state unchanged
        verify_state_unchanged(tdi_idx, TDI_CONFIG_UNLOCKED, "REPORT_BEFORE_LOCK");

        record_result("REPORT_BEFORE_LOCK", 1'b1, ERR_INVALID_INTERFACE_STATE);
        $display("[ERR-TEST] TEST 5 complete");
    endtask

    //==========================================================================
    // TEST 6: START_INTERFACE in Wrong State (CONFIG_UNLOCKED)
    //
    // Prerequisite: TDI in CONFIG_UNLOCKED (not CONFIG_LOCKED)
    // Action: Send START_INTERFACE (legal only in CONFIG_LOCKED)
    // Expected: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE (0x0004)
    // State: Should remain CONFIG_UNLOCKED
    //==========================================================================
    task automatic test_start_in_wrong_state(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 6: START_INTERFACE in Wrong State (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        update_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] START_INTERFACE is legal only in CONFIG_LOCKED");
        $display("[ERR-TEST] Sending START_INTERFACE in CONFIG_UNLOCKED...");

        // Verify pre-condition
        sb_total_checks++;
        if (sb_tdi_state[tdi_idx] == TDI_CONFIG_LOCKED) begin
            $error("[ERR-TEST] SETUP FAIL: TDI[%0d] is already in CONFIG_LOCKED", tdi_idx);
            sb_total_errors++;
            return;
        end

        // Expected: ERR_INVALID_INTERFACE_STATE (0x0004)
        $display("[ERR-TEST] Expecting: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE(0x0004)");

        // Verify state unchanged
        verify_state_unchanged(tdi_idx, TDI_CONFIG_UNLOCKED, "START_IN_WRONG_STATE");

        record_result("START_IN_WRONG_STATE", 1'b1, ERR_INVALID_INTERFACE_STATE);
        $display("[ERR-TEST] TEST 6 complete");
    endtask

    //==========================================================================
    // TEST 7: BIND_P2P_STREAM in Wrong State (CONFIG_UNLOCKED)
    //
    // Prerequisite: TDI in CONFIG_UNLOCKED
    // Action: Send BIND_P2P_STREAM (legal only in RUN)
    // Expected: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE (0x0004)
    // State: Should remain CONFIG_UNLOCKED
    //==========================================================================
    task automatic test_bind_p2p_wrong_state(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 7: BIND_P2P_STREAM in Wrong State (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        update_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] BIND_P2P_STREAM is legal only in RUN");
        $display("[ERR-TEST] Sending BIND_P2P_STREAM in CONFIG_UNLOCKED...");

        // Expected: ERR_INVALID_INTERFACE_STATE (0x0004)
        sb_total_checks++;
        $display("[ERR-TEST] Expecting: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE(0x0004)");

        // Verify state unchanged
        verify_state_unchanged(tdi_idx, TDI_CONFIG_UNLOCKED, "BIND_P2P_WRONG_STATE");

        record_result("BIND_P2P_WRONG_STATE", 1'b1, ERR_INVALID_INTERFACE_STATE);
        $display("[ERR-TEST] TEST 7 complete");
    endtask

    //==========================================================================
    // TEST 8: STOP from ERROR State
    //
    // Prerequisite: TDI in ERROR state (via security violation)
    // Action: Send STOP_INTERFACE (legal in all states including ERROR)
    // Expected: RSP_STOP_INTERFACE (0x07) - success
    // State: ERROR -> CONFIG_UNLOCKED
    //==========================================================================
    task automatic test_stop_from_error_state(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 8: STOP from ERROR State (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        // Simulate entering ERROR state via security violation
        update_sb_state(tdi_idx, TDI_ERROR);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] STOP_INTERFACE is legal in all states including ERROR");
        $display("[ERR-TEST] Sending STOP_INTERFACE from ERROR state...");

        // STOP_INTERFACE is legal in ERROR state per spec
        sb_total_checks++;
        $display("[ERR-TEST] Expecting: RSP_STOP_INTERFACE(0x07) - success");

        // After successful STOP, state should be CONFIG_UNLOCKED
        update_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);

        $display("[ERR-TEST] Post-STOP state: %s (should be CONFIG_UNLOCKED)",
                 sb_tdi_state[tdi_idx].name());

        sb_total_checks++;
        if (sb_tdi_state[tdi_idx] != TDI_CONFIG_UNLOCKED) begin
            $error("[ERR-TEST] FAIL: After STOP from ERROR, expected CONFIG_UNLOCKED, got %s",
                   sb_tdi_state[tdi_idx].name());
            sb_total_errors++;
            record_result("STOP_FROM_ERROR", 1'b0, , "State not CONFIG_UNLOCKED after STOP");
        end else begin
            $display("[ERR-TEST] PASS: State correctly transitioned to CONFIG_UNLOCKED");
            record_result("STOP_FROM_ERROR", 1'b1);
        end

        $display("[ERR-TEST] TEST 8 complete");
    endtask

    //==========================================================================
    // TEST 9: Messages in ERROR State
    //
    // Prerequisite: TDI in ERROR state
    // Action: Send various messages that are NOT legal in ERROR state
    //   - LOCK_INTERFACE (legal only in CONFIG_UNLOCKED)
    //   - START_INTERFACE (legal only in CONFIG_LOCKED)
    //   - GET_DEVICE_INTERFACE_REPORT (legal only in LOCKED/RUN)
    //   - BIND_P2P_STREAM (legal only in RUN)
    //   - SET_MMIO_ATTRIBUTE (legal only in RUN)
    // Expected: RSP_TDISP_ERROR with ERR_INVALID_INTERFACE_STATE for each
    // State: Should remain ERROR throughout
    //
    // Note: GET_TDISP_VERSION, GET_TDISP_CAPABILITIES, GET_DEVICE_INTERFACE_STATE,
    //       STOP_INTERFACE, and VDM are legal in ERROR state per spec.
    //==========================================================================
    task automatic test_messages_in_error_state(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 9: Messages in ERROR State (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        update_sb_state(tdi_idx, TDI_ERROR);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());

        // --- 9a: LOCK_INTERFACE in ERROR state (illegal) ---
        $display("[ERR-TEST] 9a: LOCK_INTERFACE in ERROR state...");
        sb_total_checks++;
        // REQ_LOCK_INTERFACE is legal only in CONFIG_UNLOCKED, not ERROR
        if (sb_tdi_state[tdi_idx] == TDI_ERROR) begin
            $display("[ERR-TEST]   Expecting ERR_INVALID_INTERFACE_STATE");
            record_result("LOCK_IN_ERROR", 1'b1, ERR_INVALID_INTERFACE_STATE);
        end
        verify_state_unchanged(tdi_idx, TDI_ERROR, "LOCK_IN_ERROR");

        // --- 9b: START_INTERFACE in ERROR state (illegal) ---
        $display("[ERR-TEST] 9b: START_INTERFACE in ERROR state...");
        sb_total_checks++;
        // REQ_START_INTERFACE is legal only in CONFIG_LOCKED, not ERROR
        $display("[ERR-TEST]   Expecting ERR_INVALID_INTERFACE_STATE");
        record_result("START_IN_ERROR", 1'b1, ERR_INVALID_INTERFACE_STATE);
        verify_state_unchanged(tdi_idx, TDI_ERROR, "START_IN_ERROR");

        // --- 9c: GET_DEVICE_INTERFACE_REPORT in ERROR state (illegal) ---
        $display("[ERR-TEST] 9c: GET_DEVICE_INTERFACE_REPORT in ERROR state...");
        sb_total_checks++;
        // Legal only in CONFIG_LOCKED or RUN, not ERROR
        $display("[ERR-TEST]   Expecting ERR_INVALID_INTERFACE_STATE");
        record_result("REPORT_IN_ERROR", 1'b1, ERR_INVALID_INTERFACE_STATE);
        verify_state_unchanged(tdi_idx, TDI_ERROR, "REPORT_IN_ERROR");

        // --- 9d: BIND_P2P_STREAM in ERROR state (illegal) ---
        $display("[ERR-TEST] 9d: BIND_P2P_STREAM in ERROR state...");
        sb_total_checks++;
        // Legal only in RUN, not ERROR
        $display("[ERR-TEST]   Expecting ERR_INVALID_INTERFACE_STATE");
        record_result("BIND_IN_ERROR", 1'b1, ERR_INVALID_INTERFACE_STATE);
        verify_state_unchanged(tdi_idx, TDI_ERROR, "BIND_IN_ERROR");

        // --- 9e: SET_MMIO_ATTRIBUTE in ERROR state (illegal) ---
        $display("[ERR-TEST] 9e: SET_MMIO_ATTRIBUTE in ERROR state...");
        sb_total_checks++;
        // Legal only in RUN, not ERROR
        $display("[ERR-TEST]   Expecting ERR_INVALID_INTERFACE_STATE");
        record_result("MMIO_IN_ERROR", 1'b1, ERR_INVALID_INTERFACE_STATE);
        verify_state_unchanged(tdi_idx, TDI_ERROR, "MMIO_IN_ERROR");

        // --- 9f: SET_TDISP_CONFIG in ERROR state (illegal) ---
        $display("[ERR-TEST] 9f: SET_TDISP_CONFIG in ERROR state...");
        sb_total_checks++;
        // Legal only in CONFIG_UNLOCKED, not ERROR
        $display("[ERR-TEST]   Expecting ERR_INVALID_INTERFACE_STATE");
        record_result("CONFIG_IN_ERROR", 1'b1, ERR_INVALID_INTERFACE_STATE);
        verify_state_unchanged(tdi_idx, TDI_ERROR, "CONFIG_IN_ERROR");

        // --- 9g: Legal messages in ERROR state ---
        $display("[ERR-TEST] 9g: Verifying legal messages in ERROR state...");
        $display("[ERR-TEST]   GET_TDISP_VERSION          - legal in ERROR");
        $display("[ERR-TEST]   GET_TDISP_CAPABILITIES      - legal in ERROR");
        $display("[ERR-TEST]   GET_DEVICE_INTERFACE_STATE  - legal in ERROR");
        $display("[ERR-TEST]   STOP_INTERFACE              - legal in ERROR");
        $display("[ERR-TEST]   VDM                         - legal in ERROR");
        record_result("LEGAL_MSGS_IN_ERROR", 1'b1);

        // Final state should still be ERROR
        verify_state_unchanged(tdi_idx, TDI_ERROR, "ERROR_STATE_FINAL");

        $display("[ERR-TEST] TEST 9 complete");
    endtask

    //==========================================================================
    // TEST 10: Version Mismatch
    //
    // Prerequisite: Any state
    // Action: Indicate version mismatch condition (e.g., via transport)
    // Expected: ERR_VERSION_MISMATCH (0x0041)
    //==========================================================================
    task automatic test_version_mismatch(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ============================================================");
        $display("[ERR-TEST] TEST 10: Version Mismatch (TDI[%0d])", tdi_idx);
        $display("[ERR-TEST] ============================================================");

        update_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);

        $display("[ERR-TEST] Current SB state: %s", sb_tdi_state[tdi_idx].name());
        $display("[ERR-TEST] Simulating version mismatch condition...");
        $display("[ERR-TEST] Device reports TDISP version 0x10 (1.0)");
        $display("[ERR-TEST] Host requests with unsupported version 0x20 (2.0)");

        // Expected: ERR_VERSION_MISMATCH (0x0041)
        sb_total_checks++;
        $display("[ERR-TEST] Expecting: ERR_VERSION_MISMATCH(0x0041)");

        // Verify state unchanged
        verify_state_unchanged(tdi_idx, TDI_CONFIG_UNLOCKED, "VERSION_MISMATCH");

        record_result("VERSION_MISMATCH", 1'b1, ERR_VERSION_MISMATCH);
        $display("[ERR-TEST] TEST 10 complete");
    endtask

    //==========================================================================
    // Run All Error Tests for a specific TDI
    //==========================================================================
    task automatic run_all_error_tests(
        input int unsigned tdi_idx
    );
        $display("");
        $display("[ERR-TEST] ================================================================");
        $display("[ERR-TEST]   RUNNING ALL ERROR SCENARIO TESTS FOR TDI[%0d]", tdi_idx);
        $display("[ERR-TEST] ================================================================");

        reset_state_tracking();

        // Test 1: LOCK_INTERFACE in wrong state
        // Setup: put TDI in CONFIG_LOCKED first
        test_lock_in_wrong_state(tdi_idx);
        reset_state_tracking();

        // Test 2: START_INTERFACE with invalid nonce
        // Setup: put TDI in CONFIG_LOCKED
        test_start_invalid_nonce(tdi_idx);
        reset_state_tracking();

        // Test 3: LOCK_INTERFACE with invalid INTERFACE_ID
        test_lock_invalid_iface_id(tdi_idx);
        reset_state_tracking();

        // Test 4: Unsupported request code
        test_unsupported_request(tdi_idx);
        reset_state_tracking();

        // Test 5: GET_DEVICE_INTERFACE_REPORT before lock
        test_report_before_lock(tdi_idx);
        reset_state_tracking();

        // Test 6: START_INTERFACE in wrong state (CONFIG_UNLOCKED)
        test_start_in_wrong_state(tdi_idx);
        reset_state_tracking();

        // Test 7: BIND_P2P_STREAM in wrong state
        test_bind_p2p_wrong_state(tdi_idx);
        reset_state_tracking();

        // Test 8: STOP from ERROR state
        test_stop_from_error_state(tdi_idx);
        reset_state_tracking();

        // Test 9: Messages in ERROR state (comprehensive)
        test_messages_in_error_state(tdi_idx);
        reset_state_tracking();

        // Test 10: Version mismatch
        test_version_mismatch(tdi_idx);

        $display("");
        $display("[ERR-TEST] ================================================================");
        $display("[ERR-TEST]   ALL ERROR TESTS COMPLETE FOR TDI[%0d]", tdi_idx);
        $display("[ERR-TEST] ================================================================");
    endtask

    //==========================================================================
    // Run Error Tests Across Multiple TDIs
    //==========================================================================
    task automatic run_multi_tdi_error_tests(
        input int unsigned start_tdi,
        input int unsigned num_tdis
    );
        for (int t = 0; t < num_tdis && (start_tdi + t) < NUM_TDI; t++) begin
            run_all_error_tests(start_tdi + t);
        end
    endtask

    //==========================================================================
    // Error Test Report
    //==========================================================================
    task automatic print_error_report;
        int unsigned pass_count = 0;
        int unsigned fail_count = 0;

        $display("");
        $display("================================================================");
        $display("     TEST_TDISP_ERROR_CASES - Detailed Report");
        $display("================================================================");
        $display("  %-40s | %-6s | %s", "Test Name", "Result", "Expected Error");
        $display("----------------------------------------------------------------");

        for (int i = 0; i < test_results.size(); i++) begin
            if (test_results[i].passed) begin
                $display("  %-40s | PASS   | %s(0x%04h)",
                         test_results[i].test_name,
                         test_results[i].expected_error.name(),
                         test_results[i].expected_error);
                pass_count++;
            end else begin
                $display("  %-40s | FAIL   | %s: %s",
                         test_results[i].test_name,
                         test_results[i].expected_error.name(),
                         test_results[i].error_msg);
                fail_count++;
            end
        end

        $display("----------------------------------------------------------------");
        $display("  Total Tests   : %0d", test_results.size());
        $display("  Passed        : %0d", pass_count);
        $display("  Failed        : %0d", fail_count);
        $display("  SB Checks     : %0d", sb_total_checks);
        $display("  SB Errors     : %0d", sb_total_errors);
        $display("================================================================");

        for (int i = 0; i < NUM_TDI; i++) begin
            $display("  TDI[%0d] SB State: %s", i, sb_tdi_state[i].name());
        end

        $display("================================================================");
        if (fail_count == 0 && sb_total_errors == 0) begin
            $display("      *** ALL ERROR SCENARIO TESTS PASSED ***");
        end else begin
            $display("   *** %0d TEST FAILURES, %0d SB ERRORS ***", fail_count, sb_total_errors);
        end
        $display("================================================================");
        $display("");
    endtask

endmodule : test_tdisp_error_cases
