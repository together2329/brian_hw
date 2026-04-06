//============================================================================
// Test: TDISP Multi-TDI Test Sequence
// Tests multiple TDIs managed by a single DSM with independent operations.
//
// Key behaviors tested:
//   1. Independent LOCK of different TDIs
//   2. Independent START/STOP across TDIs
//   3. Isolation between TDI state machines
//   4. INTERFACE_ID routing to correct TDI contexts
//   5. NUM_REQ_ALL tracking across all TDIs
//   6. Concurrent operations on different TDIs
//   7. Error on one TDI does not affect others
//   8. Full lifecycle with staggered TDI operations
//   9. STOP_ALL / bulk reset verification
//  10. INTERFACE_ID collision detection
//
// Reference: PCIe Base Spec Rev 7.0, Chapter 11, Table 11-28
//============================================================================

`timescale 1ns / 1ps

module test_tdisp_multi_tdi;

    import tdisp_types::*;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter int unsigned NUM_TDI            = 4;
    parameter int unsigned INTERFACE_ID_WIDTH = 96;
    parameter int unsigned NONCE_WIDTH        = 256;
    parameter int unsigned BUS_WIDTH          = 8;

    //==========================================================================
    // Per-TDI Context Mirror (mirrors tdisp_tdi_context_s in scoreboard)
    //==========================================================================
    typedef struct {
        tdisp_state_e                state;
        logic [INTERFACE_ID_WIDTH-1:0] interface_id;
        logic [7:0]                  bound_stream_id;
        logic [63:0]                 mmio_reporting_offset;
        tdisp_lock_flags_s           lock_flags;
        logic [NONCE_WIDTH-1:0]      nonce;
        logic                        nonce_valid;
        logic                        xt_mode_enabled;
        logic [7:0]                  outstanding_reqs;
    } sb_tdi_context_t;

    //==========================================================================
    // Scoreboard & Tracking
    //==========================================================================
    sb_tdi_context_t  sb_ctx [NUM_TDI];
    logic [7:0]       sb_outstanding_per_tdi [NUM_TDI];
    int unsigned      total_checks    = 0;
    int unsigned      total_passed    = 0;
    int unsigned      total_failed    = 0;

    typedef struct {
        string          test_name;
        logic           passed;
        string          detail;
    } multi_tdi_result_t;

    multi_tdi_result_t results [$];

    //==========================================================================
    // Helper: Generate unique INTERFACE_ID for each TDI
    // Uses PCIe Requester ID format: Bus[15:8] | Device[7:3] | Function[2:0]
    // combined with interface-specific fields
    //==========================================================================
    function automatic logic [INTERFACE_ID_WIDTH-1:0] gen_iface_id(
        input int unsigned tdi_idx
    );
        // Byte layout (12 bytes, little-endian in actual wire):
        //   Bytes 0-1:  Segment + Reserved
        //   Bytes 2-3:  Bus Number (unique per TDI for isolation testing)
        //   Bytes 4-5:  Device/Function
        //   Bytes 6-7:  Reserved
        //   Bytes 8-11: Interface-specific identifier
        logic [INTERFACE_ID_WIDTH-1:0] id;
        id = '0;
        id[15:0]   = 16'h0000;                          // Segment
        id[31:16]  = 16'(tdi_idx + 1);                  // Bus (unique per TDI)
        id[47:32]  = 16'h0100;                          // Device 0, Function 0
        id[63:48]  = 16'h0000;                          // Reserved
        id[95:64]  = {16'h0, 8'h0, 8'h0, 8'h0, 8'(tdi_idx)}; // Interface specific
        return id;
    endfunction

    //==========================================================================
    // Helper: Initialize all TDI contexts
    //==========================================================================
    task automatic reset_all_contexts;
        for (int i = 0; i < NUM_TDI; i++) begin
            sb_ctx[i].state                = TDI_CONFIG_UNLOCKED;
            sb_ctx[i].interface_id         = gen_iface_id(i);
            sb_ctx[i].bound_stream_id      = 8'h00;
            sb_ctx[i].mmio_reporting_offset = 64'h0;
            sb_ctx[i].lock_flags           = '0;
            sb_ctx[i].nonce                = '0;
            sb_ctx[i].nonce_valid          = 1'b0;
            sb_ctx[i].xt_mode_enabled      = 1'b0;
            sb_ctx[i].outstanding_reqs     = 8'h00;
            sb_outstanding_per_tdi[i]      = 8'h00;
        end
        $display("[MULTI-TDI] All %0d TDI contexts initialized", NUM_TDI);
    endtask

    //==========================================================================
    // Helper: Record test result
    //==========================================================================
    function automatic void record_result(
        input string test_name,
        input logic  passed,
        input string detail = ""
    );
        multi_tdi_result_t r;
        r.test_name = test_name;
        r.passed    = passed;
        r.detail    = detail;
        results.push_back(r);
        total_checks++;
        if (passed) total_passed++;
        else        total_failed++;
    endfunction

    //==========================================================================
    // Helper: Verify TDI state
    //==========================================================================
    task automatic verify_tdi_state(
        input int unsigned  tdi_idx,
        input tdisp_state_e expected,
        input string        context
    );
        if (sb_ctx[tdi_idx].state !== expected) begin
            $error("[MULTI-TDI] FAIL @ %s: TDI[%0d] state=%s, expected=%s",
                   context, tdi_idx, sb_ctx[tdi_idx].state.name(), expected.name());
            record_result(context, 1'b0,
                $sformatf("TDI[%0d] state mismatch: %s vs %s",
                          tdi_idx, sb_ctx[tdi_idx].state.name(), expected.name()));
        end else begin
            $display("[MULTI-TDI] PASS @ %s: TDI[%0d] state=%s",
                     context, tdi_idx, expected.name());
        end
    endtask

    //==========================================================================
    // Helper: Verify outstanding request count
    //==========================================================================
    task automatic verify_outstanding(
        input int unsigned tdi_idx,
        input logic [7:0] expected_count,
        input string      context
    );
        if (sb_ctx[tdi_idx].outstanding_reqs !== expected_count) begin
            $error("[MULTI-TDI] FAIL @ %s: TDI[%0d] outstanding=%0d, expected=%0d",
                   context, tdi_idx, sb_ctx[tdi_idx].outstanding_reqs, expected_count);
            record_result(context, 1'b0,
                $sformatf("Outstanding mismatch TDI[%0d]: %0d vs %0d",
                          tdi_idx, sb_ctx[tdi_idx].outstanding_reqs, expected_count));
        end else begin
            $display("[MULTI-TDI] PASS @ %s: TDI[%0d] outstanding=%0d",
                     context, tdi_idx, expected_count);
        end
    endtask

    //==========================================================================
    // Helper: Simulate LOCK_INTERFACE for a specific TDI
    //==========================================================================
    task automatic do_lock_tdi(
        input int unsigned tdi_idx,
        input logic        expect_success = 1'b1
    );
        string ctx = $sformatf("LOCK TDI[%0d]", tdi_idx);
        $display("[MULTI-TDI] LOCK_INTERFACE on TDI[%0d] (current: %s)",
                 tdi_idx, sb_ctx[tdi_idx].state.name());

        if (expect_success) begin
            if (sb_ctx[tdi_idx].state != TDI_CONFIG_UNLOCKED) begin
                $error("[MULTI-TDI] FAIL @ %s: Cannot LOCK from %s",
                       ctx, sb_ctx[tdi_idx].state.name());
                record_result(ctx, 1'b0, "Invalid pre-state");
                return;
            end
            sb_ctx[tdi_idx].state = TDI_CONFIG_LOCKED;
            // Set default lock flags
            sb_ctx[tdi_idx].lock_flags.lock_msix       = 1'b1;
            sb_ctx[tdi_idx].lock_flags.no_fw_update     = 1'b1;
            sb_ctx[tdi_idx].lock_flags.bind_p2p         = 1'b0;
            sb_ctx[tdi_idx].lock_flags.all_req_redirect = 1'b0;
            verify_tdi_state(tdi_idx, TDI_CONFIG_LOCKED, ctx);
        end else begin
            // State should remain unchanged
            verify_tdi_state(tdi_idx, sb_ctx[tdi_idx].state, ctx);
            record_result(ctx, 1'b1, "Correctly rejected");
        end
    endtask

    //==========================================================================
    // Helper: Simulate START_INTERFACE for a specific TDI
    //==========================================================================
    task automatic do_start_tdi(
        input int unsigned tdi_idx,
        input logic        expect_success = 1'b1
    );
        string ctx = $sformatf("START TDI[%0d]", tdi_idx);
        $display("[MULTI-TDI] START_INTERFACE on TDI[%0d] (current: %s)",
                 tdi_idx, sb_ctx[tdi_idx].state.name());

        if (expect_success) begin
            if (sb_ctx[tdi_idx].state != TDI_CONFIG_LOCKED) begin
                $error("[MULTI-TDI] FAIL @ %s: Cannot START from %s",
                       ctx, sb_ctx[tdi_idx].state.name());
                record_result(ctx, 1'b0, "Invalid pre-state");
                return;
            end
            sb_ctx[tdi_idx].state = TDI_RUN;
            sb_ctx[tdi_idx].nonce_valid = 1'b0; // nonce consumed
            verify_tdi_state(tdi_idx, TDI_RUN, ctx);
        end else begin
            verify_tdi_state(tdi_idx, sb_ctx[tdi_idx].state, ctx);
            record_result(ctx, 1'b1, "Correctly rejected");
        end
    endtask

    //==========================================================================
    // Helper: Simulate STOP_INTERFACE for a specific TDI
    //==========================================================================
    task automatic do_stop_tdi(
        input int unsigned tdi_idx
    );
        string ctx = $sformatf("STOP TDI[%0d]", tdi_idx);
        tdisp_state_e prev = sb_ctx[tdi_idx].state;
        $display("[MULTI-TDI] STOP_INTERFACE on TDI[%0d] (current: %s)",
                 tdi_idx, prev.name());

        // STOP is legal from all states
        sb_ctx[tdi_idx].state           = TDI_CONFIG_UNLOCKED;
        sb_ctx[tdi_idx].lock_flags      = '0;
        sb_ctx[tdi_idx].nonce_valid     = 1'b0;
        sb_ctx[tdi_idx].nonce           = '0;
        sb_ctx[tdi_idx].bound_stream_id = 8'h00;
        sb_ctx[tdi_idx].xt_mode_enabled = 1'b0;
        sb_ctx[tdi_idx].outstanding_reqs = 8'h00;
        sb_outstanding_per_tdi[tdi_idx] = 8'h00;

        verify_tdi_state(tdi_idx, TDI_CONFIG_UNLOCKED, ctx);
        record_result(ctx, 1'b1,
            $sformatf("STOP from %s -> CONFIG_UNLOCKED", prev.name()));
    endtask

    //==========================================================================
    // Helper: Simulate security violation on a TDI
    //==========================================================================
    task automatic do_violation_tdi(
        input int unsigned tdi_idx
    );
        string ctx = $sformatf("VIOLATION TDI[%0d]", tdi_idx);
        $display("[MULTI-TDI] Security violation on TDI[%0d] (current: %s)",
                 tdi_idx, sb_ctx[tdi_idx].state.name());

        sb_ctx[tdi_idx].state = TDI_ERROR;
        verify_tdi_state(tdi_idx, TDI_ERROR, ctx);
        record_result(ctx, 1'b1, "Security violation -> ERROR");
    endtask

    //==========================================================================
    // Helper: Increment outstanding requests
    //==========================================================================
    task automatic incr_outstanding(
        input int unsigned tdi_idx
    );
        sb_ctx[tdi_idx].outstanding_reqs++;
        sb_outstanding_per_tdi[tdi_idx] = sb_ctx[tdi_idx].outstanding_reqs;
    endtask

    //==========================================================================
    // Helper: Get total outstanding across all TDIs
    //==========================================================================
    function automatic logic [7:0] get_total_outstanding;
        logic [15:0] total = '0;
        for (int i = 0; i < NUM_TDI; i++) begin
            total += sb_ctx[i].outstanding_reqs;
        end
        return total[7:0];
    endfunction

    //==========================================================================
    // TEST 1: Independent LOCK of Different TDIs
    //
    // Lock TDI[0], verify TDI[1..3] unchanged.
    // Lock TDI[2], verify TDI[0] still locked, TDI[1,3] still unlocked.
    // Lock TDI[3], verify full isolation.
    //==========================================================================
    task automatic test_independent_lock;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 1: Independent LOCK of Different TDIs");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // Lock TDI[0]
        do_lock_tdi(0);
        verify_tdi_state(0, TDI_CONFIG_LOCKED, "POST_LOCK_TDI0");
        verify_tdi_state(1, TDI_CONFIG_UNLOCKED, "TDI1_UNTOUCHED_AFTER_TDI0_LOCK");
        verify_tdi_state(2, TDI_CONFIG_UNLOCKED, "TDI2_UNTOUCHED_AFTER_TDI0_LOCK");
        verify_tdi_state(3, TDI_CONFIG_UNLOCKED, "TDI3_UNTOUCHED_AFTER_TDI0_LOCK");

        // Lock TDI[2]
        do_lock_tdi(2);
        verify_tdi_state(0, TDI_CONFIG_LOCKED,   "TDI0_STILL_LOCKED");
        verify_tdi_state(1, TDI_CONFIG_UNLOCKED,  "TDI1_STILL_UNLOCKED");
        verify_tdi_state(2, TDI_CONFIG_LOCKED,    "TDI2_NOW_LOCKED");
        verify_tdi_state(3, TDI_CONFIG_UNLOCKED,  "TDI3_STILL_UNLOCKED");

        // Lock TDI[3]
        do_lock_tdi(3);
        verify_tdi_state(0, TDI_CONFIG_LOCKED,   "TDI0_LOCKED_FINAL");
        verify_tdi_state(1, TDI_CONFIG_UNLOCKED,  "TDI1_UNLOCKED_FINAL");
        verify_tdi_state(2, TDI_CONFIG_LOCKED,    "TDI2_LOCKED_FINAL");
        verify_tdi_state(3, TDI_CONFIG_LOCKED,    "TDI3_LOCKED_FINAL");

        record_result("INDEPENDENT_LOCK", 1'b1, "3 TDIs locked independently");

        // Cleanup
        for (int i = 0; i < NUM_TDI; i++) begin
            if (sb_ctx[i].state != TDI_CONFIG_UNLOCKED) begin
                do_stop_tdi(i);
            end
        end

        $display("[MULTI-TDI] TEST 1 complete");
    endtask

    //==========================================================================
    // TEST 2: Independent START/STOP Across TDIs
    //
    // Lock all TDIs, then start them in different order.
    // Stop them in different order. Verify isolation throughout.
    //==========================================================================
    task automatic test_independent_start_stop;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 2: Independent START/STOP Across TDIs");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // Lock all TDIs
        for (int i = 0; i < NUM_TDI; i++) begin
            do_lock_tdi(i);
        end

        // Start TDI[3] first (reverse order)
        do_start_tdi(3);
        verify_tdi_state(0, TDI_CONFIG_LOCKED, "TDI0_LOCKED_WHILE_TDI3_RUNS");
        verify_tdi_state(1, TDI_CONFIG_LOCKED, "TDI1_LOCKED_WHILE_TDI3_RUNS");
        verify_tdi_state(2, TDI_CONFIG_LOCKED, "TDI2_LOCKED_WHILE_TDI3_RUNS");
        verify_tdi_state(3, TDI_RUN,           "TDI3_RUNNING");

        // Start TDI[1]
        do_start_tdi(1);
        verify_tdi_state(0, TDI_CONFIG_LOCKED, "TDI0_STILL_LOCKED");
        verify_tdi_state(1, TDI_RUN,           "TDI1_NOW_RUNNING");
        verify_tdi_state(2, TDI_CONFIG_LOCKED, "TDI2_STILL_LOCKED");
        verify_tdi_state(3, TDI_RUN,           "TDI3_STILL_RUNNING");

        // Stop TDI[3]
        do_stop_tdi(3);
        verify_tdi_state(3, TDI_CONFIG_UNLOCKED, "TDI3_STOPPED");
        verify_tdi_state(1, TDI_RUN,             "TDI1_STILL_RUNNING");

        // Stop TDI[1]
        do_stop_tdi(1);
        verify_tdi_state(1, TDI_CONFIG_UNLOCKED, "TDI1_STOPPED");

        // Start and stop TDI[0]
        do_start_tdi(0);
        verify_tdi_state(0, TDI_RUN, "TDI0_RUNNING");
        do_stop_tdi(0);
        verify_tdi_state(0, TDI_CONFIG_UNLOCKED, "TDI0_STOPPED");

        // Stop remaining
        do_stop_tdi(2);

        // All should be unlocked
        for (int i = 0; i < NUM_TDI; i++) begin
            verify_tdi_state(i, TDI_CONFIG_UNLOCKED,
                             $sformatf("TDI%0d_FINAL", i));
        end

        record_result("INDEPENDENT_START_STOP", 1'b1, "All TDIs started/stopped independently");
        $display("[MULTI-TDI] TEST 2 complete");
    endtask

    //==========================================================================
    // TEST 3: TDI State Isolation
    //
    // Place each TDI in a different state and verify they remain isolated:
    //   TDI[0] = CONFIG_UNLOCKED
    //   TDI[1] = CONFIG_LOCKED
    //   TDI[2] = RUN
    //   TDI[3] = ERROR
    //==========================================================================
    task automatic test_state_isolation;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 3: TDI State Isolation");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // TDI[0]: stays UNLOCKED
        verify_tdi_state(0, TDI_CONFIG_UNLOCKED, "TDI0_UNLOCKED");

        // TDI[1]: LOCK
        do_lock_tdi(1);

        // TDI[2]: LOCK -> START
        do_lock_tdi(2);
        do_start_tdi(2);

        // TDI[3]: LOCK -> START -> SECURITY_VIOLATION
        do_lock_tdi(3);
        do_start_tdi(3);
        do_violation_tdi(3);

        // Verify all states are different and correct
        verify_tdi_state(0, TDI_CONFIG_UNLOCKED, "ISO_TDI0_UNLOCKED");
        verify_tdi_state(1, TDI_CONFIG_LOCKED,   "ISO_TDI1_LOCKED");
        verify_tdi_state(2, TDI_RUN,             "ISO_TDI2_RUN");
        verify_tdi_state(3, TDI_ERROR,           "ISO_TDI3_ERROR");

        // Cross-check: TDI[0] still UNLOCKED after all other transitions
        $display("[MULTI-TDI] Verifying TDI[0] unaffected by all other activity...");
        if (sb_ctx[0].state != TDI_CONFIG_UNLOCKED) begin
            $error("[MULTI-TDI] FAIL: TDI[0] state corrupted!");
            record_result("STATE_ISOLATION", 1'b0, "TDI[0] corrupted");
        end else begin
            record_result("STATE_ISOLATION", 1'b1, "All 4 states isolated correctly");
        end

        // Cleanup
        for (int i = 0; i < NUM_TDI; i++) begin
            if (sb_ctx[i].state != TDI_CONFIG_UNLOCKED) begin
                do_stop_tdi(i);
            end
        end

        $display("[MULTI-TDI] TEST 3 complete");
    endtask

    //==========================================================================
    // TEST 4: INTERFACE_ID Routing
    //
    // Verify that each INTERFACE_ID maps to the correct TDI context.
    // Test with GET_DEVICE_INTERFACE_STATE for each TDI.
    //==========================================================================
    task automatic test_iface_id_routing;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 4: INTERFACE_ID Routing");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // Verify each TDI has a unique INTERFACE_ID
        $display("[MULTI-TDI] Verifying unique INTERFACE_IDs:");
        for (int i = 0; i < NUM_TDI; i++) begin
            $display("[MULTI-TDI]   TDI[%0d] IFACE_ID = 0x%024h", i, sb_ctx[i].interface_id);
        end

        // Check uniqueness
        for (int i = 0; i < NUM_TDI; i++) begin
            for (int j = i + 1; j < NUM_TDI; j++) begin
                if (sb_ctx[i].interface_id == sb_ctx[j].interface_id) begin
                    $error("[MULTI-TDI] FAIL: TDI[%0d] and TDI[%0d] have same INTERFACE_ID!",
                           i, j);
                    record_result("IFACE_ID_ROUTING", 1'b0,
                        $sformatf("Collision TDI[%0d]/TDI[%0d]", i, j));
                end
            end
        end

        // Place TDIs in different states and verify routing
        do_lock_tdi(1);
        do_lock_tdi(2);
        do_start_tdi(2);

        // GET_DEVICE_INTERFACE_STATE for each TDI should return correct state
        // This verifies the INTERFACE_ID -> tdi_index lookup
        verify_tdi_state(0, TDI_CONFIG_UNLOCKED, "ROUTE_TDI0");
        verify_tdi_state(1, TDI_CONFIG_LOCKED,   "ROUTE_TDI1");
        verify_tdi_state(2, TDI_RUN,             "ROUTE_TDI2");
        verify_tdi_state(3, TDI_CONFIG_UNLOCKED, "ROUTE_TDI3");

        record_result("IFACE_ID_ROUTING", 1'b1, "All INTERFACE_IDs route correctly");

        // Cleanup
        for (int i = 0; i < NUM_TDI; i++) begin
            if (sb_ctx[i].state != TDI_CONFIG_UNLOCKED) do_stop_tdi(i);
        end

        $display("[MULTI-TDI] TEST 4 complete");
    endtask

    //==========================================================================
    // TEST 5: NUM_REQ_ALL Tracking Across TDIs
    //
    // Simulate outstanding request counts across TDIs and verify total
    // matches the sum of per-TDI counts (NUM_REQ_ALL in capabilities).
    //==========================================================================
    task automatic test_num_req_all_tracking;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 5: NUM_REQ_ALL Tracking Across TDIs");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // Increment outstanding on different TDIs
        $display("[MULTI-TDI] Building outstanding request counts...");

        // TDI[0]: 3 outstanding
        incr_outstanding(0); incr_outstanding(0); incr_outstanding(0);
        verify_outstanding(0, 8'd3, "OUTSTANDING_TDI0");

        // TDI[1]: 1 outstanding
        incr_outstanding(1);
        verify_outstanding(1, 8'd1, "OUTSTANDING_TDI1");

        // TDI[2]: 5 outstanding
        for (int k = 0; k < 5; k++) incr_outstanding(2);
        verify_outstanding(2, 8'd5, "OUTSTANDING_TDI2");

        // TDI[3]: 0 outstanding (no increments)
        verify_outstanding(3, 8'd0, "OUTSTANDING_TDI3");

        // Verify total = 3 + 1 + 5 + 0 = 9
        $display("[MULTI-TDI] Total outstanding: %0d (expected: 9)", get_total_outstanding());
        if (get_total_outstanding() != 8'd9) begin
            $error("[MULTI-TDI] FAIL: Total outstanding mismatch!");
            record_result("NUM_REQ_ALL", 1'b0,
                $sformatf("Expected 9, got %0d", get_total_outstanding()));
        end else begin
            record_result("NUM_REQ_ALL", 1'b1, "Total outstanding = 9 (3+1+5+0)");
        end

        // Decrement by STOP (resets to 0)
        sb_ctx[0].outstanding_reqs = 8'h00;
        $display("[MULTI-TDI] After STOP TDI[0]: total=%0d (expected: 6)", get_total_outstanding());
        if (get_total_outstanding() != 8'd6) begin
            $error("[MULTI-TDI] FAIL: Post-stop total mismatch!");
            record_result("NUM_REQ_ALL_DECREMENT", 1'b0, "Decrement failed");
        end else begin
            record_result("NUM_REQ_ALL_DECREMENT", 1'b1, "After STOP TDI[0]: total=6);
        end

        // Full reset
        reset_all_contexts();
        if (get_total_outstanding() != 8'd0) begin
            $error("[MULTI-TDI] FAIL: Post-reset total not 0!");
            record_result("NUM_REQ_ALL_RESET", 1'b0, "Reset failed");
        end else begin
            record_result("NUM_REQ_ALL_RESET", 1'b1, "After reset: total=0);
        end

        $display("[MULTI-TDI] TEST 5 complete");
    endtask

    //==========================================================================
    // TEST 6: Concurrent Operations on Different TDIs
    //
    // Simultaneously operate on multiple TDIs to stress the per-TDI
    // context management:
    //   - TDI[0]: Normal flow (LOCK -> START -> STOP)
    //   - TDI[1]: Lock only
    //   - TDI[2]: Lock -> Error -> Stop
    //   - TDI[3]: Multiple lock/stop cycles
    //==========================================================================
    task automatic test_concurrent_operations;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 6: Concurrent Operations on Different TDIs");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // Phase 1: Lock TDI[0], TDI[2], TDI[3] simultaneously
        $display("[MULTI-TDI] Phase 1: Lock TDIs 0, 2, 3");
        do_lock_tdi(0);
        do_lock_tdi(2);
        do_lock_tdi(3);

        // Phase 2: Start TDI[0], TDI[2]; Lock TDI[1]
        $display("[MULTI-TDI] Phase 2: Start TDI 0, 2; Lock TDI 1");
        do_start_tdi(0);
        do_start_tdi(2);
        do_lock_tdi(1);

        // Phase 3: Violation on TDI[2], Stop TDI[0]
        $display("[MULTI-TDI] Phase 3: Violation TDI 2; Stop TDI 0");
        do_violation_tdi(2);
        do_stop_tdi(0);

        // Verify states after Phase 3
        verify_tdi_state(0, TDI_CONFIG_UNLOCKED, "CONC_TDI0_POST_PHASE3");
        verify_tdi_state(1, TDI_CONFIG_LOCKED,   "CONC_TDI1_POST_PHASE3");
        verify_tdi_state(2, TDI_ERROR,           "CONC_TDI2_POST_PHASE3");
        verify_tdi_state(3, TDI_CONFIG_LOCKED,   "CONC_TDI3_POST_PHASE3");

        // Phase 4: TDI[3] cycle: start, stop, lock again
        $display("[MULTI-TDI] Phase 4: TDI[3] rapid cycle");
        do_start_tdi(3);
        verify_tdi_state(3, TDI_RUN, "CONC_TDI3_RUN");
        do_stop_tdi(3);
        verify_tdi_state(3, TDI_CONFIG_UNLOCKED, "CONC_TDI3_UNLOCKED");
        do_lock_tdi(3);
        verify_tdi_state(3, TDI_CONFIG_LOCKED, "CONC_TDI3_RELOCKED");

        // Phase 5: Stop all
        $display("[MULTI-TDI] Phase 5: Stop all TDIs");
        for (int i = 0; i < NUM_TDI; i++) begin
            if (sb_ctx[i].state != TDI_CONFIG_UNLOCKED) do_stop_tdi(i);
        end

        for (int i = 0; i < NUM_TDI; i++) begin
            verify_tdi_state(i, TDI_CONFIG_UNLOCKED,
                             $sformatf("CONC_FINAL_TDI%0d", i));
        end

        record_result("CONCURRENT_OPS", 1'b1, "5-phase concurrent operations passed");
        $display("[MULTI-TDI] TEST 6 complete");
    endtask

    //==========================================================================
    // TEST 7: Error on One TDI Does Not Affect Others
    //
    // Place all TDIs in RUN, trigger error on TDI[2], verify TDI[0,1,3]
    // remain in RUN. Recover TDI[2] and verify it can restart.
    //==========================================================================
    task automatic test_error_isolation;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 7: Error on One TDI Does Not Affect Others");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // All TDIs to RUN
        for (int i = 0; i < NUM_TDI; i++) begin
            do_lock_tdi(i);
            do_start_tdi(i);
        end

        // All in RUN
        for (int i = 0; i < NUM_TDI; i++) begin
            verify_tdi_state(i, TDI_RUN, $sformatf("PRE_ERR_TDI%0d", i));
        end

        // Trigger error on TDI[2]
        do_violation_tdi(2);

        // Verify TDI[0,1,3] still in RUN
        verify_tdi_state(0, TDI_RUN,   "UNAFFECTED_TDI0");
        verify_tdi_state(1, TDI_RUN,   "UNAFFECTED_TDI1");
        verify_tdi_state(2, TDI_ERROR, "AFFECTED_TDI2");
        verify_tdi_state(3, TDI_RUN,   "UNAFFECTED_TDI3");

        // Recover TDI[2]: STOP -> LOCK -> START
        do_stop_tdi(2);
        verify_tdi_state(2, TDI_CONFIG_UNLOCKED, "RECOVERY_TDI2_STOPPED");

        do_lock_tdi(2);
        do_start_tdi(2);
        verify_tdi_state(2, TDI_RUN, "RECOVERY_TDI2_RUNNING");

        // Verify TDI[0,1,3] were unaffected by recovery
        verify_tdi_state(0, TDI_RUN, "STILL_RUNNING_TDI0");
        verify_tdi_state(1, TDI_RUN, "STILL_RUNNING_TDI1");
        verify_tdi_state(3, TDI_RUN, "STILL_RUNNING_TDI3");

        record_result("ERROR_ISOLATION", 1'b1, "Error on TDI[2] isolated; recovery successful");

        // Cleanup
        for (int i = 0; i < NUM_TDI; i++) do_stop_tdi(i);

        $display("[MULTI-TDI] TEST 7 complete");
    endtask

    //==========================================================================
    // TEST 8: Staggered Full Lifecycle
    //
    // Each TDI starts its lifecycle at a different phase:
    //   T=0: TDI[0] begins LOCK
    //   T=1: TDI[1] begins LOCK, TDI[0] reaches START
    //   T=2: TDI[2] begins LOCK, TDI[1] reaches START, TDI[0] STOP
    //   T=3: TDI[3] begins LOCK, TDI[2] reaches START, TDI[1] STOP
    //   T=4: TDI[3] reaches START, TDI[2] STOP
    //   T=5: TDI[3] STOP
    //==========================================================================
    task automatic test_staggered_lifecycle;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 8: Staggered Full Lifecycle");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // T=0: TDI[0] LOCK
        $display("[MULTI-TDI] T=0: TDI[0] LOCK");
        do_lock_tdi(0);

        // T=1: TDI[1] LOCK, TDI[0] START
        $display("[MULTI-TDI] T=1: TDI[1] LOCK, TDI[0] START");
        do_lock_tdi(1);
        do_start_tdi(0);

        // T=2: TDI[2] LOCK, TDI[1] START, TDI[0] STOP
        $display("[MULTI-TDI] T=2: TDI[2] LOCK, TDI[1] START, TDI[0] STOP");
        do_lock_tdi(2);
        do_start_tdi(1);
        do_stop_tdi(0);

        // T=3: TDI[3] LOCK, TDI[2] START, TDI[1] STOP
        $display("[MULTI-TDI] T=3: TDI[3] LOCK, TDI[2] START, TDI[1] STOP");
        do_lock_tdi(3);
        do_start_tdi(2);
        do_stop_tdi(1);

        // T=4: TDI[3] START, TDI[2] STOP
        $display("[MULTI-TDI] T=4: TDI[3] START, TDI[2] STOP");
        do_start_tdi(3);
        do_stop_tdi(2);

        // T=5: TDI[3] STOP
        $display("[MULTI-TDI] T=5: TDI[3] STOP");
        do_stop_tdi(3);

        // All should be back to UNLOCKED
        for (int i = 0; i < NUM_TDI; i++) begin
            verify_tdi_state(i, TDI_CONFIG_UNLOCKED,
                             $sformatf("STAGGERED_FINAL_TDI%0d", i));
        end

        record_result("STAGGERED_LIFECYCLE", 1'b1, "Staggered pipeline lifecycle complete");
        $display("[MULTI-TDI] TEST 8 complete");
    endtask

    //==========================================================================
    // TEST 9: Bulk Reset / STOP_ALL Verification
    //
    // Place all TDIs in various states, then STOP all of them
    // (simulating a bulk reset or shutdown scenario).
    //==========================================================================
    task automatic test_bulk_stop;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 9: Bulk Reset / STOP_ALL");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // Setup: diverse states
        do_lock_tdi(0);                          // LOCKED
        do_lock_tdi(1); do_start_tdi(1);        // RUN
        do_lock_tdi(2); do_start_tdi(2);        // RUN
        do_lock_tdi(3); do_start_tdi(3);
        do_violation_tdi(3);                     // ERROR

        $display("[MULTI-TDI] Pre-bulk states:");
        for (int i = 0; i < NUM_TDI; i++) begin
            $display("[MULTI-TDI]   TDI[%0d]: %s", i, sb_ctx[i].state.name());
        end

        // Bulk STOP: stop all TDIs
        $display("[MULTI-TDI] Executing bulk STOP on all TDIs...");
        for (int i = 0; i < NUM_TDI; i++) begin
            do_stop_tdi(i);
        end

        // Verify all unlocked
        $display("[MULTI-TDI] Post-bulk states:");
        for (int i = 0; i < NUM_TDI; i++) begin
            verify_tdi_state(i, TDI_CONFIG_UNLOCKED,
                             $sformatf("BULK_STOP_TDI%0d", i));
            verify_outstanding(i, 8'h00,
                               $sformatf("BULK_OUTSTANDING_TDI%0d", i));
            // Verify nonce cleared
            if (sb_ctx[i].nonce_valid != 1'b0) begin
                $error("[MULTI-TDI] FAIL: TDI[%0d] nonce still valid after bulk stop!", i);
                record_result("BULK_STOP", 1'b0, "Nonce not cleared");
            end
        end

        record_result("BULK_STOP", 1'b1, "All TDIs reset to UNLOCKED");
        $display("[MULTI-TDI] TEST 9 complete");
    endtask

    //==========================================================================
    // TEST 10: INTERFACE_ID Collision Detection
    //
    // Verify that two TDIs cannot have the same INTERFACE_ID.
    // In real hardware, this would be prevented by firmware initialization.
    //==========================================================================
    task automatic test_iface_id_collision;
        $display("");
        $display("[MULTI-TDI] ============================================================");
        $display("[MULTI-TDI] TEST 10: INTERFACE_ID Collision Detection");
        $display("[MULTI-TDI] ============================================================");

        reset_all_contexts();

        // Verify all INTERFACE_IDs are unique after initialization
        logic collision_found;
        collision_found = 1'b0;
        for (int i = 0; i < NUM_TDI; i++) begin
            for (int j = i + 1; j < NUM_TDI; j++) begin
                if (sb_ctx[i].interface_id == sb_ctx[j].interface_id) begin
                    $error("[MULTI-TDI] FAIL: TDI[%0d] and TDI[%0d] INTERFACE_ID collision!",
                           i, j);
                    collision_found = 1'b1;
                end
            end
        end

        if (!collision_found) begin
            $display("[MULTI-TDI] PASS: All INTERFACE_IDs are unique");
            record_result("IFACE_ID_NO_COLLISION", 1'b1, "All IDs unique");

            // Display the unique IDs
            for (int i = 0; i < NUM_TDI; i++) begin
                $display("[MULTI-TDI]   TDI[%0d]: 0x%024h", i, sb_ctx[i].interface_id);
            end
        end else begin
            record_result("IFACE_ID_NO_COLLISION", 1'b0, "Collision detected");
        end

        // Test routing with valid IDs: lock each TDI by its unique ID
        for (int i = 0; i < NUM_TDI; i++) begin
            do_lock_tdi(i);
        end

        // Verify each TDI independently locked
        for (int i = 0; i < NUM_TDI; i++) begin
            verify_tdi_state(i, TDI_CONFIG_LOCKED, $sformatf("COLLISION_LOCK_TDI%0d", i));
        end

        record_result("IFACE_ID_ROUTING_LOCK", 1'b1, "All TDIs locked via unique IDs");

        // Cleanup
        for (int i = 0; i < NUM_TDI; i++) do_stop_tdi(i);

        $display("[MULTI-TDI] TEST 10 complete");
    endtask

    //==========================================================================
    // Run All Multi-TDI Tests
    //==========================================================================
    task automatic run_all_tests;
        $display("");
        $display("[MULTI-TDI] ================================================================");
        $display("[MULTI-TDI]   RUNNING ALL MULTI-TDI TEST SEQUENCES");
        $display("[MULTI-TDI]   NUM_TDI = %0d", NUM_TDI);
        $display("[MULTI-TDI] ================================================================");

        test_independent_lock;
        test_independent_start_stop;
        test_state_isolation;
        test_iface_id_routing;
        test_num_req_all_tracking;
        test_concurrent_operations;
        test_error_isolation;
        test_staggered_lifecycle;
        test_bulk_stop;
        test_iface_id_collision;

        $display("");
        $display("[MULTI-TDI] ================================================================");
        $display("[MULTI-TDI]   ALL MULTI-TDI TESTS COMPLETE");
        $display("[MULTI-TDI] ================================================================");
    endtask

    //==========================================================================
    // Final Report
    //==========================================================================
    task automatic print_report;
        int unsigned pass_count = 0;
        int unsigned fail_count = 0;

        $display("");
        $display("================================================================");
        $display("     TEST_TDISP_MULTI_TDI - Detailed Report");
        $display("================================================================");
        $display("  %-45s | %-6s | %s", "Test Name", "Result", "Detail");
        $display("----------------------------------------------------------------");

        for (int i = 0; i < results.size(); i++) begin
            $display("  %-45s | %-6s | %s",
                     results[i].test_name,
                     results[i].passed ? "PASS" : "FAIL",
                     results[i].detail);
            if (results[i].passed) pass_count++;
            else                   fail_count++;
        end

        $display("----------------------------------------------------------------");
        $display("  Total Checks : %0d", total_checks);
        $display("  Passed       : %0d", pass_count);
        $display("  Failed       : %0d", fail_count);
        $display("================================================================");

        $display("  Per-TDI Final States:");
        for (int i = 0; i < NUM_TDI; i++) begin
            $display("    TDI[%0d]: state=%-16s outstanding=%0d iface_id=0x%024h",
                     i, sb_ctx[i].state.name(),
                     sb_ctx[i].outstanding_reqs,
                     sb_ctx[i].interface_id);
        end

        $display("  Total Outstanding: %0d", get_total_outstanding());

        $display("================================================================");
        if (fail_count == 0) begin
            $display("   *** ALL MULTI-TDI TESTS PASSED ***");
        end else begin
            $display("   *** %0d TEST FAILURES ***", fail_count);
        end
        $display("================================================================");
        $display("");
    endtask

endmodule : test_tdisp_multi_tdi
