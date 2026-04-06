//============================================================================
// Test: TDISP Lock Interface Validation Tests
// Directly instantiates tdisp_lock_ctrl and verifies all validation checks
// for LOCK_INTERFACE_REQUEST processing per spec.
//
// Test scenarios:
//   1.  Successful LOCK with all checks passing (golden path)
//   2.  Wrong TDI state (not CONFIG_UNLOCKED) → error
//   3.  INTERFACE_ID mismatch → error
//   4.  IDE stream not valid → error
//   5.  IDE keys not programmed → error
//   6.  SPDM session mismatch → error
//   7.  TC0 not enabled → error
//   8.  Phantom functions enabled → error
//   9.  BAR overlap detected → error
//  10.  Invalid page size → error
//  11.  Cache line size mismatch → error
//  12.  Reserved flags non-zero → error
//  13.  Nonce generation failure (insufficient entropy)
//  14.  NO_FW_UPDATE flag binding to context
//  15.  LOCK_MSIX flag in context
//  16.  BIND_P2P flag with address mask binding
//  17.  ALL_REQUEST_REDIRECT flag in context
//  18.  MMIO_REPORTING_OFFSET binding to context
//  19.  Multiple sequential lock operations
//  20.  Lock request while busy is rejected
//
// Reference: PCIe Base Spec Rev 7.0, Chapter 11, Table 11-11
//============================================================================

`timescale 1ns / 1ps

module test_tdisp_lock_validation;

    import tdisp_types::*;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter int unsigned NUM_TDI            = 4;
    parameter int unsigned INTERFACE_ID_WIDTH = 96;
    parameter int unsigned NONCE_WIDTH        = 256;
    parameter int unsigned MAX_OUTSTANDING    = 8;
    parameter int unsigned CLK_PERIOD         = 10;

    //==========================================================================
    // Clock / Reset
    //==========================================================================
    logic clk;
    logic rst_n;

    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    //==========================================================================
    // DUT Signals
    //==========================================================================
    // Lock request interface
    logic                            lock_req;
    logic [$clog2(NUM_TDI)-1:0]      tdi_index;
    logic [INTERFACE_ID_WIDTH-1:0]   interface_id;
    tdisp_types::tdisp_lock_flags_s  lock_flags;
    logic [7:0]                      stream_id;
    logic [63:0]                     mmio_reporting_offset;
    logic [63:0]                     bind_p2p_addr_mask;

    // TDI context lookup
    tdisp_types::tdisp_state_e       tdi_state;
    logic [INTERFACE_ID_WIDTH-1:0]   tdi_interface_id;

    // IDE stream validation inputs
    logic                            ide_stream_valid;
    logic                            ide_keys_programmed;
    logic                            ide_spdm_session_match;
    logic                            ide_tc0_enabled;

    // Device configuration inputs
    logic                            phantom_fn_disabled;
    logic                            no_bar_overlap;
    logic                            valid_page_size;
    logic [6:0]                      dev_cache_line_size;
    logic                            fw_update_supported;

    // Nonce generation interface
    logic                            nonce_req;
    logic                            nonce_ack;
    logic [NONCE_WIDTH-1:0]          nonce_data;

    // TDI context update interface
    logic                            ctx_update;
    logic [$clog2(NUM_TDI)-1:0]      ctx_tdi_index;
    tdisp_types::tdisp_state_e       ctx_new_state;
    tdisp_types::tdisp_lock_flags_s  ctx_lock_flags;
    logic [7:0]                      ctx_stream_id;
    logic [63:0]                     ctx_mmio_offset;
    logic [63:0]                     ctx_p2p_mask;
    logic [NONCE_WIDTH-1:0]          ctx_nonce;
    logic                            ctx_nonce_valid;
    logic                            ctx_fw_update_locked;

    // Response interface
    logic                            rsp_valid;
    logic                            rsp_error;
    tdisp_types::tdisp_error_code_e  rsp_error_code;
    logic [NONCE_WIDTH-1:0]          rsp_nonce;
    logic                            rsp_done;

    // Status
    logic                            busy;

    //==========================================================================
    // Scoreboard / Tracking
    //==========================================================================
    int unsigned total_checks = 0;
    int unsigned total_passed = 0;
    int unsigned total_failed = 0;

    typedef struct {
        string          test_name;
        logic           passed;
        string          detail;
    } lock_test_result_t;

    lock_test_result_t results [$];

    //==========================================================================
    // DUT Instantiation (explicit port connections)
    //==========================================================================
    tdisp_lock_ctrl #(
        .NUM_TDI           (NUM_TDI),
        .INTERFACE_ID_WIDTH(INTERFACE_ID_WIDTH),
        .NONCE_WIDTH       (NONCE_WIDTH),
        .MAX_OUTSTANDING   (MAX_OUTSTANDING)
    ) dut (
        .clk                (clk),
        .rst_n              (rst_n),
        // Lock request
        .lock_req_i         (lock_req),
        .tdi_index_i        (tdi_index),
        .interface_id_i     (interface_id),
        .lock_flags_i       (lock_flags),
        .stream_id_i        (stream_id),
        .mmio_reporting_offset_i (mmio_reporting_offset),
        .bind_p2p_addr_mask_i    (bind_p2p_addr_mask),
        // TDI context lookup
        .tdi_state_i        (tdi_state),
        .tdi_interface_id_i (tdi_interface_id),
        // IDE stream validation
        .ide_stream_valid_i       (ide_stream_valid),
        .ide_keys_programmed_i    (ide_keys_programmed),
        .ide_spdm_session_match_i (ide_spdm_session_match),
        .ide_tc0_enabled_i        (ide_tc0_enabled),
        // Device configuration
        .phantom_fn_disabled_i    (phantom_fn_disabled),
        .no_bar_overlap_i         (no_bar_overlap),
        .valid_page_size_i        (valid_page_size),
        .dev_cache_line_size_i    (dev_cache_line_size),
        .fw_update_supported_i    (fw_update_supported),
        // Nonce generation
        .nonce_req_o        (nonce_req),
        .nonce_ack_i        (nonce_ack),
        .nonce_data_i       (nonce_data),
        // Context update
        .ctx_update_o       (ctx_update),
        .ctx_tdi_index_o    (ctx_tdi_index),
        .ctx_new_state_o    (ctx_new_state),
        .ctx_lock_flags_o   (ctx_lock_flags),
        .ctx_stream_id_o    (ctx_stream_id),
        .ctx_mmio_offset_o  (ctx_mmio_offset),
        .ctx_p2p_mask_o     (ctx_p2p_mask),
        .ctx_nonce_o        (ctx_nonce),
        .ctx_nonce_valid_o  (ctx_nonce_valid),
        .ctx_fw_update_locked_o (ctx_fw_update_locked),
        // Response
        .rsp_valid_o        (rsp_valid),
        .rsp_error_o        (rsp_error),
        .rsp_error_code_o   (rsp_error_code),
        .rsp_nonce_o        (rsp_nonce),
        .rsp_done_i         (rsp_done),
        // Status
        .busy_o             (busy)
    );

    //==========================================================================
    // Helper: Record test result
    //==========================================================================
    function automatic void record_result(
        input string test_name,
        input logic  passed,
        input string detail = ""
    );
        lock_test_result_t r;
        r.test_name = test_name;
        r.passed    = passed;
        r.detail    = detail;
        results.push_back(r);
        total_checks++;
        if (passed) total_passed++;
        else        total_failed++;
    endfunction

    //==========================================================================
    // Helper: Initialize all inputs to passing defaults
    //==========================================================================
    task automatic init_passing_defaults;
        // TDI context: CONFIG_UNLOCKED with matching INTERFACE_ID
        tdi_state        = TDI_CONFIG_UNLOCKED;
        tdi_interface_id = 96'h0000_0001_0000_0000_0000_0001;

        // Lock request fields
        lock_req              = 1'b0;
        tdi_index             = '0;
        interface_id          = tdi_interface_id; // Match by default
        lock_flags            = '0;
        lock_flags.sys_cache_line_size = 1'b0; // 64B CLS
        stream_id             = 8'h05;
        mmio_reporting_offset = 64'h0000_1000_0000_0000;
        bind_p2p_addr_mask    = 64'hFFFF_FFFF_FFFF_F000;

        // IDE stream: all valid
        ide_stream_valid       = 1'b1;
        ide_keys_programmed    = 1'b1;
        ide_spdm_session_match = 1'b1;
        ide_tc0_enabled        = 1'b1;

        // Device configuration: all passing
        phantom_fn_disabled    = 1'b1;
        no_bar_overlap         = 1'b1;
        valid_page_size        = 1'b1;
        dev_cache_line_size    = 7'd0; // 64B
        fw_update_supported    = 1'b1;

        // Nonce interface
        nonce_ack   = 1'b0;
        nonce_data  = 256'hDEADBEEF_CAFEBABE_12345678_9ABCDEF0_11111111_22222222_33333333_44444444;

        // Response interface
        rsp_done = 1'b0;
    endtask

    //==========================================================================
    // Helper: Apply reset
    //==========================================================================
    task automatic apply_reset;
        rst_n = 1'b0;
        init_passing_defaults;
        repeat(5) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
    endtask

    //==========================================================================
    // Helper: Issue a lock request and drive the FSM through completion
    // Supports injecting failures by overriding specific signals before call
    //==========================================================================
    task automatic run_lock_transaction(
        input logic            expect_success,
        input tdisp_error_code_e expect_error = ERR_RESERVED
    );
        // Pulse lock request
        lock_req = 1'b1;
        @(posedge clk);
        lock_req = 1'b0;

        // FSM: LCK_IDLE -> LCK_VALIDATE (next cycle)
        @(posedge clk);

        if (expect_success) begin
            // LCK_VALIDATE -> LCK_NONCE_REQ
            @(posedge clk);

            // LCK_NONCE_REQ -> LCK_NONCE_WAIT (nonce_req asserted)
            @(posedge clk);

            // Provide nonce ack
            nonce_ack  = 1'b1;
            @(posedge clk);
            nonce_ack  = 1'b0;

            // LCK_NONCE_WAIT -> LCK_COMMIT
            @(posedge clk);

            // LCK_COMMIT -> LCK_RESPOND
            @(posedge clk);
        end else begin
            // LCK_VALIDATE -> LCK_ERROR
            @(posedge clk);

            // LCK_ERROR presents response
            @(posedge clk);
        end

        // NOTE: Response ack (rsp_done) is handled by check_response task
    endtask

    //==========================================================================
    // Helper: Verify response
    //==========================================================================
    task automatic check_response(
        input logic            expect_success,
        input tdisp_error_code_e expect_error,
        input string           context
    );
        total_checks++;
        if (expect_success) begin
            if (rsp_error) begin
                $error("[LOCK-VAL] FAIL @ %s: Expected success, got error %s(0x%04h)",
                       context, rsp_error_code.name(), rsp_error_code);
                total_failed++;
                record_result(context, 1'b0,
                    $sformatf("Unexpected error: %s", rsp_error_code.name()));
            end else begin
                $display("[LOCK-VAL] PASS @ %s: Success response", context);
                record_result(context, 1'b1);
            end
        end else begin
            if (!rsp_error) begin
                $error("[LOCK-VAL] FAIL @ %s: Expected error but got success", context);
                total_failed++;
                record_result(context, 1'b0, "Expected error, got success");
            end else if (rsp_error_code !== expect_error) begin
                $error("[LOCK-VAL] FAIL @ %s: Error code mismatch - expected %s(0x%04h), got %s(0x%04h)",
                       context, expect_error.name(), expect_error,
                       rsp_error_code.name(), rsp_error_code);
                total_failed++;
                record_result(context, 1'b0,
                    $sformatf("Wrong error: %s vs %s", rsp_error_code.name(), expect_error.name()));
            end else begin
                $display("[LOCK-VAL] PASS @ %s: Correct error %s(0x%04h)",
                         context, rsp_error_code.name(), rsp_error_code);
                record_result(context, 1'b1);
            end
        end
    endtask

    //==========================================================================
    // Helper: Verify context update values
    //==========================================================================
    task automatic check_context(
        input logic [$clog2(NUM_TDI)-1:0]  exp_tdi_index,
        input tdisp_state_e                 exp_state,
        input logic [7:0]                   exp_stream_id,
        input logic [63:0]                  exp_mmio_offset,
        input string                        context
    );
        total_checks++;
        if (ctx_tdi_index !== exp_tdi_index) begin
            $error("[LOCK-VAL] FAIL @ %s: ctx_tdi_index=%0d, expected=%0d",
                   context, ctx_tdi_index, exp_tdi_index);
            total_failed++;
            record_result(context + " ctx_tdi", 1'b0,
                $sformatf("index %0d vs %0d", ctx_tdi_index, exp_tdi_index));
        end
        if (ctx_new_state !== exp_state) begin
            $error("[LOCK-VAL] FAIL @ %s: ctx_state=%s, expected=%s",
                   context, ctx_new_state.name(), exp_state.name());
            total_failed++;
            record_result(context + " ctx_state", 1'b0,
                $sformatf("%s vs %s", ctx_new_state.name(), exp_state.name()));
        end
        if (ctx_stream_id !== exp_stream_id) begin
            $error("[LOCK-VAL] FAIL @ %s: ctx_stream_id=0x%02h, expected=0x%02h",
                   context, ctx_stream_id, exp_stream_id);
            total_failed++;
            record_result(context + " ctx_stream", 1'b0,
                $sformatf("0x%02h vs 0x%02h", ctx_stream_id, exp_stream_id));
        end
        if (ctx_mmio_offset !== exp_mmio_offset) begin
            $error("[LOCK-VAL] FAIL @ %s: ctx_mmio_offset=0x%016h, expected=0x%016h",
                   context, ctx_mmio_offset, exp_mmio_offset);
            total_failed++;
            record_result(context + " ctx_mmio", 1'b0, "MMIO offset mismatch");
        end else begin
            $display("[LOCK-VAL] PASS @ %s: Context correct (tdi=%0d state=%s stream=0x%02h mmio=0x%016h)",
                     context, exp_tdi_index, exp_state.name(), exp_stream_id, exp_mmio_offset);
            record_result(context + " context", 1'b1);
        end
    endtask

    //=========================================================================
    // TEST 1: Successful LOCK with all checks passing (golden path)
    //=========================================================================
    task automatic test_golden_path;
        $display("[LOCK-VAL] --- TEST 1: Golden path - all checks pass ---");
        init_passing_defaults;

        run_lock_transaction(.expect_success(1'b1));

        check_response(1'b1, ERR_RESERVED, "Golden path response");
        check_context(.exp_tdi_index('d0),
                      .exp_state(TDI_CONFIG_LOCKED),
                      .exp_stream_id(8'h05),
                      .exp_mmio_offset(64'h0000_1000_0000_0000),
                      "Golden path context");
    endtask

    //=========================================================================
    // TEST 2: Wrong TDI state (not CONFIG_UNLOCKED)
    //=========================================================================
    task automatic test_wrong_state;
        $display("[LOCK-VAL] --- TEST 2: Wrong TDI state ---");
        apply_reset;

        tdi_state = TDI_CONFIG_LOCKED;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_INTERFACE_STATE));

        check_response(1'b0, ERR_INVALID_INTERFACE_STATE, "Wrong state");
    endtask

    //=========================================================================
    // TEST 3: INTERFACE_ID mismatch
    //=========================================================================
    task automatic test_iface_id_mismatch;
        $display("[LOCK-VAL] --- TEST 3: INTERFACE_ID mismatch ---");
        apply_reset;

        // Set mismatching INTERFACE_ID in request
        interface_id = 96'hFFFF_FFFF_FFFF_FFFF_FFFF_FFFF;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_INTERFACE));

        check_response(1'b0, ERR_INVALID_INTERFACE, "IFACE_ID mismatch");
    endtask

    //=========================================================================
    // TEST 4: IDE stream not valid
    //=========================================================================
    task automatic test_ide_stream_invalid;
        $display("[LOCK-VAL] --- TEST 4: IDE stream not valid ---");
        apply_reset;

        ide_stream_valid = 1'b0;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_DEVICE_CONFIGURATION));

        check_response(1'b0, ERR_INVALID_DEVICE_CONFIGURATION, "IDE stream invalid");
    endtask

    //=========================================================================
    // TEST 5: IDE keys not programmed
    //=========================================================================
    task automatic test_ide_keys_not_programmed;
        $display("[LOCK-VAL] --- TEST 5: IDE keys not programmed ---");
        apply_reset;

        ide_keys_programmed = 1'b0;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_DEVICE_CONFIGURATION));

        check_response(1'b0, ERR_INVALID_DEVICE_CONFIGURATION, "IDE keys");
    endtask

    //=========================================================================
    // TEST 6: SPDM session mismatch
    //=========================================================================
    task automatic test_spdm_session_mismatch;
        $display("[LOCK-VAL] --- TEST 6: SPDM session mismatch ---");
        apply_reset;

        ide_spdm_session_match = 1'b0;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_DEVICE_CONFIGURATION));

        check_response(1'b0, ERR_INVALID_DEVICE_CONFIGURATION, "SPDM mismatch");
    endtask

    //=========================================================================
    // TEST 7: TC0 not enabled
    //=========================================================================
    task automatic test_tc0_not_enabled;
        $display("[LOCK-VAL] --- TEST 7: TC0 not enabled ---");
        apply_reset;

        ide_tc0_enabled = 1'b0;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_DEVICE_CONFIGURATION));

        check_response(1'b0, ERR_INVALID_DEVICE_CONFIGURATION, "TC0 disabled");
    endtask

    //=========================================================================
    // TEST 8: Phantom functions enabled
    //=========================================================================
    task automatic test_phantom_fn_enabled;
        $display("[LOCK-VAL] --- TEST 8: Phantom functions enabled ---");
        apply_reset;

        phantom_fn_disabled = 1'b0;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_DEVICE_CONFIGURATION));

        check_response(1'b0, ERR_INVALID_DEVICE_CONFIGURATION, "Phantom FN");
    endtask

    //=========================================================================
    // TEST 9: BAR overlap detected
    //=========================================================================
    task automatic test_bar_overlap;
        $display("[LOCK-VAL] --- TEST 9: BAR overlap detected ---");
        apply_reset;

        no_bar_overlap = 1'b0;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_DEVICE_CONFIGURATION));

        check_response(1'b0, ERR_INVALID_DEVICE_CONFIGURATION, "BAR overlap");
    endtask

    //=========================================================================
    // TEST 10: Invalid page size
    //=========================================================================
    task automatic test_invalid_page_size;
        $display("[LOCK-VAL] --- TEST 10: Invalid page size ---");
        apply_reset;

        valid_page_size = 1'b0;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_DEVICE_CONFIGURATION));

        check_response(1'b0, ERR_INVALID_DEVICE_CONFIGURATION, "Page size");
    endtask

    //=========================================================================
    // TEST 11: Cache line size mismatch
    //=========================================================================
    task automatic test_cls_mismatch;
        $display("[LOCK-VAL] --- TEST 11: Cache line size mismatch ---");
        apply_reset;

        // Request CLS flag=1 (128B) but device reports CLS=0 (64B)
        lock_flags.sys_cache_line_size = 1'b1;
        dev_cache_line_size = 7'd0;
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_DEVICE_CONFIGURATION));

        check_response(1'b0, ERR_INVALID_DEVICE_CONFIGURATION, "CLS mismatch");
    endtask

    //=========================================================================
    // TEST 12: Reserved flags non-zero
    //=========================================================================
    task automatic test_reserved_flags_nonzero;
        $display("[LOCK-VAL] --- TEST 12: Reserved flags non-zero ---");
        apply_reset;

        lock_flags.reserved = 11'h001; // Non-zero reserved
        run_lock_transaction(.expect_success(1'b0),
                             .expect_error(ERR_INVALID_REQUEST));

        check_response(1'b0, ERR_INVALID_REQUEST, "Reserved flags");
    endtask

    //=========================================================================
    // TEST 13: Nonce generation failure (insufficient entropy)
    //=========================================================================
    task automatic test_nonce_entropy_failure;
        $display("[LOCK-VAL] --- TEST 13: Nonce entropy failure ---");
        apply_reset;

        // Start lock request
        lock_req = 1'b1;
        @(posedge clk);
        lock_req = 1'b0;

        // Wait for LCK_VALIDATE -> LCK_NONCE_REQ
        @(posedge clk);
        @(posedge clk);
        @(posedge clk);

        // Provide zero nonce (entropy failure)
        nonce_data = '0;
        nonce_ack  = 1'b1;
        @(posedge clk);
        nonce_ack  = 1'b0;

        // Should go to LCK_ERROR with INSUFFICIENT_ENTROPY
        @(posedge clk);
        @(posedge clk);

        check_response(1'b0, ERR_INSUFFICIENT_ENTROPY, "Nonce entropy");

        // Ack response
        rsp_done = 1'b1;
        @(posedge clk);
        rsp_done = 1'b0;
        @(posedge clk);
    endtask

    //=========================================================================
    // TEST 14: NO_FW_UPDATE flag binding to context
    //=========================================================================
    task automatic test_no_fw_update_flag;
        $display("[LOCK-VAL] --- TEST 14: NO_FW_UPDATE flag ---");
        apply_reset;

        lock_flags.no_fw_update = 1'b1;
        fw_update_supported     = 1'b1;

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "NO_FW_UPDATE response");

        // Verify ctx_fw_update_locked is set
        total_checks++;
        if (!ctx_fw_update_locked) begin
            $error("[LOCK-VAL] FAIL: ctx_fw_update_locked not set with NO_FW_UPDATE=1);
            total_failed++;
            record_result("NO_FW_UPDATE ctx", 1'b0, "fw_update_locked not set");
        end else begin
            $display("[LOCK-VAL] PASS: NO_FW_UPDATE flag -> ctx_fw_update_locked=1);
            record_result("NO_FW_UPDATE ctx", 1'b1);
        end

        // Now test with NO_FW_UPDATE=0
        apply_reset;
        lock_flags.no_fw_update = 1'b0;
        run_lock_transaction(.expect_success(1'b1));

        total_checks++;
        if (ctx_fw_update_locked) begin
            $error("[LOCK-VAL] FAIL: ctx_fw_update_locked set with NO_FW_UPDATE=0);
            total_failed++;
            record_result("NO_FW_UPDATE=0 ctx", 1'b0, "fw_update_locked incorrectly set");
        end else begin
            $display("[LOCK-VAL] PASS: NO_FW_UPDATE=0 -> ctx_fw_update_locked=0);
            record_result("NO_FW_UPDATE=0 ctx", 1'b1);
        end
    endtask

    //=========================================================================
    // TEST 15: LOCK_MSIX flag in context
    //=========================================================================
    task automatic test_lock_msix_flag;
        $display("[LOCK-VAL] --- TEST 15: LOCK_MSIX flag ---");
        apply_reset;

        lock_flags.lock_msix = 1'b1;

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "LOCK_MSIX response");

        // Verify lock_flags propagated to context
        total_checks++;
        if (!ctx_lock_flags.lock_msix) begin
            $error("[LOCK-VAL] FAIL: ctx_lock_flags.lock_msix not set");
            total_failed++;
            record_result("LOCK_MSIX ctx", 1'b0, "flag not propagated");
        end else begin
            $display("[LOCK-VAL] PASS: LOCK_MSIX flag propagated to context");
            record_result("LOCK_MSIX ctx", 1'b1);
        end
    endtask

    //=========================================================================
    // TEST 16: BIND_P2P flag with address mask binding
    //=========================================================================
    task automatic test_bind_p2p_flag;
        $display("[LOCK-VAL] --- TEST 16: BIND_P2P flag with address mask ---");
        apply_reset;

        lock_flags.bind_p2p = 1'b1;
        bind_p2p_addr_mask  = 64'hAAAA_BBBB_CCCC_DDD0;

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "BIND_P2P response");

        // Verify P2P mask propagated to context
        total_checks++;
        if (ctx_p2p_mask !== 64'hAAAA_BBBB_CCCC_DDD0) begin
            $error("[LOCK-VAL] FAIL: ctx_p2p_mask mismatch");
            total_failed++;
            record_result("BIND_P2P ctx", 1'b0, "P2P mask mismatch");
        end else begin
            $display("[LOCK-VAL] PASS: P2P address mask propagated to context");
            record_result("BIND_P2P ctx", 1'b1);
        end

        // Verify bind_p2p flag in context
        total_checks++;
        if (!ctx_lock_flags.bind_p2p) begin
            $error("[LOCK-VAL] FAIL: ctx_lock_flags.bind_p2p not set");
            total_failed++;
            record_result("BIND_P2P flag", 1'b0, "flag not set");
        end else begin
            $display("[LOCK-VAL] PASS: bind_p2p flag in context");
            record_result("BIND_P2P flag", 1'b1);
        end
    endtask

    //=========================================================================
    // TEST 17: ALL_REQUEST_REDIRECT flag in context
    //=========================================================================
    task automatic test_all_request_redirect;
        $display("[LOCK-VAL] --- TEST 17: ALL_REQUEST_REDIRECT flag ---");
        apply_reset;

        lock_flags.all_request_redirect = 1'b1;

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "ALL_REQ_REDIRECT response");

        total_checks++;
        if (!ctx_lock_flags.all_request_redirect) begin
            $error("[LOCK-VAL] FAIL: ctx_lock_flags.all_request_redirect not set");
            total_failed++;
            record_result("ALL_REQ_REDIRECT ctx", 1'b0, "flag not set");
        end else begin
            $display("[LOCK-VAL] PASS: all_request_redirect in context");
            record_result("ALL_REQ_REDIRECT ctx", 1'b1);
        end
    endtask

    //=========================================================================
    // TEST 18: MMIO_REPORTING_OFFSET binding to context
    //=========================================================================
    task automatic test_mmio_reporting_offset;
        $display("[LOCK-VAL] --- TEST 18: MMIO_REPORTING_OFFSET binding ---");
        apply_reset;

        mmio_reporting_offset = 64'h0000_2000_0000_0000;

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "MMIO offset response");

        total_checks++;
        if (ctx_mmio_offset !== 64'h0000_2000_0000_0000) begin
            $error("[LOCK-VAL] FAIL: ctx_mmio_offset=0x%016h, expected=0x%016h",
                   ctx_mmio_offset, 64'h0000_2000_0000_0000);
            total_failed++;
            record_result("MMIO offset ctx", 1'b0, "offset mismatch");
        end else begin
            $display("[LOCK-VAL] PASS: MMIO offset propagated to context");
            record_result("MMIO offset ctx", 1'b1);
        end
    endtask

    //=========================================================================
    // TEST 19: Multiple sequential lock operations on different TDIs
    //=========================================================================
    task automatic test_sequential_locks;
        $display("[LOCK-VAL] --- TEST 19: Sequential locks on different TDIs ---");
        apply_reset;

        // Lock TDI[0]
        tdi_index    = 'd0;
        tdi_state    = TDI_CONFIG_UNLOCKED;
        tdi_interface_id = 96'h0000_0001_0000_0000_0000_0000;
        interface_id = tdi_interface_id;
        stream_id    = 8'h10;

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "Seq lock TDI[0]");
        check_context(.exp_tdi_index('d0),
                      .exp_state(TDI_CONFIG_LOCKED),
                      .exp_stream_id(8'h10),
                      .exp_mmio_offset(64'h0000_1000_0000_0000),
                      "Seq lock TDI[0] context");

        // Lock TDI[2]
        tdi_index    = 'd2;
        tdi_interface_id = 96'h0000_0002_0000_0000_0000_0000;
        interface_id = tdi_interface_id;
        stream_id    = 8'h20;

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "Seq lock TDI[2]");
        check_context(.exp_tdi_index('d2),
                      .exp_state(TDI_CONFIG_LOCKED),
                      .exp_stream_id(8'h20),
                      .exp_mmio_offset(64'h0000_1000_0000_0000),
                      "Seq lock TDI[2] context");
    endtask

    //=========================================================================
    // TEST 20: Lock request while busy is ignored
    //=========================================================================
    task automatic test_lock_while_busy;
        $display("[LOCK-VAL] --- TEST 20: Lock while busy ---");
        apply_reset;

        // Start first lock request
        lock_req = 1'b1;
        @(posedge clk);
        lock_req = 1'b0;

        // Wait for LCK_VALIDATE
        @(posedge clk);

        // Try another lock request while FSM is processing
        // The DUT only latches on lock_req_i in LCK_IDLE, so
        // this second request should be ignored
        lock_req = 1'b1;
        @(posedge clk);
        lock_req = 1'b0;

        // Verify busy is asserted
        total_checks++;
        if (!busy) begin
            $error("[LOCK-VAL] FAIL: busy not asserted during processing");
            total_failed++;
            record_result("Busy check", 1'b0, "busy not set");
        end else begin
            $display("[LOCK-VAL] PASS: busy asserted during lock processing");
            record_result("Busy check", 1'b1);
        end

        // Complete the first transaction normally
        @(posedge clk); // LCK_NONCE_REQ
        @(posedge clk); // LCK_NONCE_WAIT

        nonce_ack = 1'b1;
        @(posedge clk);
        nonce_ack = 1'b0;

        @(posedge clk); // LCK_COMMIT
        @(posedge clk); // LCK_RESPOND

        check_response(1'b1, ERR_RESERVED, "Lock while busy (first)");

        rsp_done = 1'b1;
        @(posedge clk);
        rsp_done = 1'b0;
        @(posedge clk);
    endtask

    //=========================================================================
    // TEST 21: FW update not supported but NO_FW_UPDATE=1 (no-op, should pass)
    //=========================================================================
    task automatic test_fw_update_not_supported;
        $display("[LOCK-VAL] --- TEST 21: FW update not supported, NO_FW_UPDATE=1 ---");
        apply_reset;

        lock_flags.no_fw_update = 1'b1;
        fw_update_supported     = 1'b0; // FW update not supported

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "FW not supported response");

        // ctx_fw_update_locked should be 0 (no_fw_update & fw_update_supported = 1 & 0 = 0)
        total_checks++;
        if (ctx_fw_update_locked) begin
            $error("[LOCK-VAL] FAIL: fw_update_locked set when FW not supported");
            total_failed++;
            record_result("FW not supported ctx", 1'b0, "fw locked incorrectly");
        end else begin
            $display("[LOCK-VAL] PASS: fw_update_locked=0 when FW not supported");
            record_result("FW not supported ctx", 1'b1);
        end
    endtask

    //=========================================================================
    // TEST 22: 128B cache line size (CLS_128B)
    //=========================================================================
    task automatic test_cls_128b;
        $display("[LOCK-VAL] --- TEST 22: 128B CLS ---");
        apply_reset;

        lock_flags.sys_cache_line_size = 1'b1; // 128B requested
        dev_cache_line_size = 7'd1;             // Device supports 128B

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "128B CLS response");
    endtask

    //=========================================================================
    // TEST 23: Nonce value propagated to response and context
    //=========================================================================
    task automatic test_nonce_propagation;
        logic [NONCE_WIDTH-1:0] expected_nonce;
        $display("[LOCK-VAL] --- TEST 23: Nonce propagation ---");
        apply_reset;

        expected_nonce = 256'hAAAA_1111_BBBB_2222_CCCC_3333_DDDD_4444_EEEE_5555_FFFF_6666_1111_7771_2222_8882;
        nonce_data = expected_nonce;

        run_lock_transaction(.expect_success(1'b1));
        check_response(1'b1, ERR_RESERVED, "Nonce propagation response");

        // Check nonce in response
        total_checks++;
        if (rsp_nonce !== expected_nonce) begin
            $error("[LOCK-VAL] FAIL: rsp_nonce mismatch");
            total_failed++;
            record_result("Nonce in response", 1'b0, "nonce mismatch");
        end else begin
            $display("[LOCK-VAL] PASS: rsp_nonce matches generated nonce");
            record_result("Nonce in response", 1'b1);
        end

        // Check nonce in context
        total_checks++;
        if (ctx_nonce !== expected_nonce) begin
            $error("[LOCK-VAL] FAIL: ctx_nonce mismatch");
            total_failed++;
            record_result("Nonce in context", 1'b0, "nonce mismatch");
        end else begin
            $display("[LOCK-VAL] PASS: ctx_nonce matches generated nonce");
            record_result("Nonce in context", 1'b1);
        end

        // Check nonce_valid
        total_checks++;
        if (!ctx_nonce_valid) begin
            $error("[LOCK-VAL] FAIL: ctx_nonce_valid not set");
            total_failed++;
            record_result("Nonce valid", 1'b0, "not set");
        end else begin
            $display("[LOCK-VAL] PASS: ctx_nonce_valid=1);
            record_result("Nonce valid", 1'b1);
        end
    endtask

    //==========================================================================
    // Run all tests
    //==========================================================================
    task automatic run_all_tests;
        $display("[LOCK-VAL] ================================================================");
        $display("[LOCK-VAL]   Starting Lock Interface Validation Tests");
        $display("[LOCK-VAL] ================================================================");

        test_golden_path;
        apply_reset;

        test_wrong_state;
        apply_reset;

        test_iface_id_mismatch;
        apply_reset;

        test_ide_stream_invalid;
        apply_reset;

        test_ide_keys_not_programmed;
        apply_reset;

        test_spdm_session_mismatch;
        apply_reset;

        test_tc0_not_enabled;
        apply_reset;

        test_phantom_fn_enabled;
        apply_reset;

        test_bar_overlap;
        apply_reset;

        test_invalid_page_size;
        apply_reset;

        test_cls_mismatch;
        apply_reset;

        test_reserved_flags_nonzero;
        apply_reset;

        test_nonce_entropy_failure;
        apply_reset;

        test_no_fw_update_flag;
        apply_reset;

        test_lock_msix_flag;
        apply_reset;

        test_bind_p2p_flag;
        apply_reset;

        test_all_request_redirect;
        apply_reset;

        test_mmio_reporting_offset;
        apply_reset;

        test_sequential_locks;
        apply_reset;

        test_lock_while_busy;
        apply_reset;

        test_fw_update_not_supported;
        apply_reset;

        test_cls_128b;
        apply_reset;

        test_nonce_propagation;

        $display("[LOCK-VAL] ================================================================");
        $display("[LOCK-VAL]   ALL LOCK VALIDATION TESTS COMPLETE");
        $display("[LOCK-VAL] ================================================================");
    endtask

    //==========================================================================
    // Final Report
    //==========================================================================
    task automatic print_report;
        int unsigned pass_count = 0;
        int unsigned fail_count = 0;

        $display("");
        $display("================================================================");
        $display("     TEST_TDISP_LOCK_VALIDATION - Detailed Report");
        $display("================================================================");
        $display("  %-50s | %-6s | %s", "Test Name", "Result", "Detail");
        $display("----------------------------------------------------------------");

        for (int i = 0; i < results.size(); i++) begin
            $display("  %-50s | %-6s | %s",
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

        if (fail_count == 0) begin
            $display("   *** ALL LOCK VALIDATION TESTS PASSED ***");
        end else begin
            $display("   *** %0d TEST FAILURES ***", fail_count);
        end
        $display("================================================================");
        $display("");
    endtask

    //==========================================================================
    // Main stimulus
    //==========================================================================
    initial begin
        apply_reset;
        run_all_tests;
        print_report;
        $finish;
    end

    //==========================================================================
    // Watchdog timeout
    //==========================================================================
    initial begin
        #200us;
        $error("[LOCK-VAL] WATCHDOG: Simulation timeout");
        $finish;
    end

endmodule : test_tdisp_lock_validation
