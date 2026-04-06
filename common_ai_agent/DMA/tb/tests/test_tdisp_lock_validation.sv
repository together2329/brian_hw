//============================================================================
// TDISP Lock Interface Validation Test
// Tests LOCK_INTERFACE_REQUEST validation scenarios per PCIe TDISP spec
// Chapter 11: State checks, IDE validation, device config checks, flag validation
//
// Standalone test module - compiles and runs independently with RTL sources
//============================================================================

`timescale 1ns / 1ps

module test_tdisp_lock_validation;

    import tdisp_types::*;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter int unsigned DATA_WIDTH         = 32;
    parameter int unsigned NUM_TDI            = 4;
    parameter int unsigned ADDR_WIDTH         = 64;
    parameter int unsigned BUS_WIDTH          = 8;
    parameter int unsigned MAX_OUTSTANDING    = 255;
    parameter int unsigned MAX_MSG_BYTES      = 1024;
    parameter int unsigned MAC_WIDTH          = 32;
    parameter int unsigned SESSION_ID_WIDTH   = 32;
    parameter int unsigned NONCE_WIDTH        = 256;
    parameter int unsigned INTERFACE_ID_WIDTH = 96;
    parameter int unsigned MAX_PAYLOAD_BYTES  = 256;
    parameter int unsigned PAGE_SIZE          = 4096;
    parameter int unsigned NONCE_SEED         = 32'hDEADBEEF;
    parameter time          CLK_PERIOD        = 10ns;
    parameter int unsigned  TIMEOUT_CYCLES    = 10000;

    //==========================================================================
    // Signals
    //==========================================================================
    logic clk;
    logic rst_n;

    logic [DATA_WIDTH-1:0]       doe_rx_tdata;
    logic [DATA_WIDTH/8-1:0]     doe_rx_tkeep;
    logic                        doe_rx_tlast;
    logic                        doe_rx_tvalid;
    logic                        doe_rx_tready;

    logic [DATA_WIDTH-1:0]       doe_tx_tdata;
    logic [DATA_WIDTH/8-1:0]     doe_tx_tkeep;
    logic                        doe_tx_tlast;
    logic                        doe_tx_tvalid;
    logic                        doe_tx_tready;

    logic                        tlp_valid_i;
    logic [31:0]                 tlp_header_dw0_i;
    logic [31:0]                 tlp_header_dw2_i;
    logic [31:0]                 tlp_header_dw3_i;
    logic                        tlp_is_4dw_i;
    logic [15:0]                 tlp_requester_id_i;
    logic [1:0]                  tlp_at_i;
    logic                        tlp_tee_originator_i;
    logic                        tlp_xt_enabled_i;
    logic                        tlp_allow_o;
    logic                        tlp_blocked_o;
    logic [$clog2(NUM_TDI)-1:0]  tlp_tdi_index_o;
    logic                        tlp_violation_irq_o;

    logic                        ide_stream_valid_i;
    logic                        ide_keys_programmed_i;
    logic                        ide_spdm_session_match_i;
    logic                        ide_tc0_enabled_i;
    logic                        phantom_fn_disabled_i;
    logic                        no_bar_overlap_i;
    logic                        valid_page_size_i;
    logic [6:0]                  dev_cache_line_size_i;
    logic                        fw_update_supported_i;

    logic                        iface_id_update_i;
    logic [$clog2(NUM_TDI)-1:0]  iface_id_tdi_index_i;
    logic [INTERFACE_ID_WIDTH-1:0] iface_id_value_i;

    tdisp_state_e                tdi_state_out [NUM_TDI];
    logic [7:0]                  total_outstanding_o;
    logic                        transport_error_o;
    tdisp_error_code_e           transport_error_code_o;
    logic                        entropy_warn_o;

    //==========================================================================
    // Scoreboard
    //==========================================================================
    int unsigned pass_count = 0;
    int unsigned fail_count = 0;
    int unsigned check_count = 0;

    //==========================================================================
    // Clock / Reset
    //==========================================================================
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    initial begin
        rst_n = 1'b0;
        repeat (20) @(posedge clk);
        rst_n = 1'b1;
        $display("[LOCK_TEST] Reset deasserted at time %0t", $time);
    end

    //==========================================================================
    // DUT Instance
    //==========================================================================
    tdisp_top #(
        .DATA_WIDTH        (DATA_WIDTH),
        .NUM_TDI           (NUM_TDI),
        .ADDR_WIDTH        (ADDR_WIDTH),
        .BUS_WIDTH         (BUS_WIDTH),
        .MAX_OUTSTANDING   (MAX_OUTSTANDING),
        .MAX_MSG_BYTES     (MAX_MSG_BYTES),
        .MAC_WIDTH         (MAC_WIDTH),
        .SESSION_ID_WIDTH  (SESSION_ID_WIDTH),
        .NONCE_WIDTH       (NONCE_WIDTH),
        .INTERFACE_ID_WIDTH(INTERFACE_ID_WIDTH),
        .MAX_PAYLOAD_BYTES (MAX_PAYLOAD_BYTES),
        .PAGE_SIZE         (PAGE_SIZE),
        .NONCE_SEED        (NONCE_SEED)
    ) u_dut (
        .clk                    (clk),
        .rst_n                  (rst_n),
        .doe_rx_tdata           (doe_rx_tdata),
        .doe_rx_tkeep           (doe_rx_tkeep),
        .doe_rx_tlast           (doe_rx_tlast),
        .doe_rx_tvalid          (doe_rx_tvalid),
        .doe_rx_tready          (doe_rx_tready),
        .doe_tx_tdata           (doe_tx_tdata),
        .doe_tx_tkeep           (doe_tx_tkeep),
        .doe_tx_tlast           (doe_tx_tlast),
        .doe_tx_tvalid          (doe_tx_tvalid),
        .doe_tx_tready          (doe_tx_tready),
        .tlp_valid_i            (tlp_valid_i),
        .tlp_header_dw0_i       (tlp_header_dw0_i),
        .tlp_header_dw2_i       (tlp_header_dw2_i),
        .tlp_header_dw3_i       (tlp_header_dw3_i),
        .tlp_is_4dw_i           (tlp_is_4dw_i),
        .tlp_requester_id_i     (tlp_requester_id_i),
        .tlp_at_i               (tlp_at_i),
        .tlp_tee_originator_i   (tlp_tee_originator_i),
        .tlp_xt_enabled_i       (tlp_xt_enabled_i),
        .tlp_allow_o            (tlp_allow_o),
        .tlp_blocked_o          (tlp_blocked_o),
        .tlp_tdi_index_o        (tlp_tdi_index_o),
        .tlp_violation_irq_o    (tlp_violation_irq_o),
        .ide_stream_valid_i         (ide_stream_valid_i),
        .ide_keys_programmed_i      (ide_keys_programmed_i),
        .ide_spdm_session_match_i   (ide_spdm_session_match_i),
        .ide_tc0_enabled_i          (ide_tc0_enabled_i),
        .phantom_fn_disabled_i      (phantom_fn_disabled_i),
        .no_bar_overlap_i           (no_bar_overlap_i),
        .valid_page_size_i          (valid_page_size_i),
        .dev_cache_line_size_i      (dev_cache_line_size_i),
        .fw_update_supported_i      (fw_update_supported_i),
        .iface_id_update_i      (iface_id_update_i),
        .iface_id_tdi_index_i   (iface_id_tdi_index_i),
        .iface_id_value_i       (iface_id_value_i),
        .tdi_state_out          (tdi_state_out),
        .total_outstanding_o    (total_outstanding_o),
        .transport_error_o      (transport_error_o),
        .transport_error_code_o (transport_error_code_o),
        .entropy_warn_o         (entropy_warn_o)
    );

    //==========================================================================
    // BFM Tasks
    //==========================================================================
    logic [7:0] tx_byte_queue [$];
    logic [7:0] rx_byte_queue [$];
    logic [15:0] last_error_code;

    task automatic tb_axi_reset;
        doe_rx_tdata  <= '0;
        doe_rx_tkeep  <= '0;
        doe_rx_tlast  <= 1'b0;
        doe_rx_tvalid <= 1'b0;
        doe_tx_tready <= 1'b0;
        tlp_valid_i   <= 1'b0;
    endtask

    task automatic tb_init_device_config;
        ide_stream_valid_i       <= 1'b1;
        ide_keys_programmed_i    <= 1'b1;
        ide_spdm_session_match_i <= 1'b1;
        ide_tc0_enabled_i        <= 1'b1;
        phantom_fn_disabled_i    <= 1'b1;
        no_bar_overlap_i         <= 1'b1;
        valid_page_size_i        <= 1'b1;
        dev_cache_line_size_i    <= 7'd0; // 64B cache line
        fw_update_supported_i    <= 1'b1;
    endtask

    task automatic tb_program_iface_ids;
        for (int i = 0; i < NUM_TDI; i++) begin
            @(posedge clk);
            iface_id_tdi_index_i <= i;
            iface_id_value_i     <= {64'h0, 8'h0, 8'h0, 16'h0001, 8'(i+1), 8'h0};
            iface_id_update_i    <= 1'b1;
            @(posedge clk);
            iface_id_update_i    <= 1'b0;
        end
    endtask

    function automatic logic [INTERFACE_ID_WIDTH-1:0] tb_get_iface_id(input int unsigned tdi_idx);
        return {64'h0, 8'h0, 8'h0, 16'h0001, 8'(tdi_idx+1), 8'h0};
    endfunction

    task automatic tb_build_request_msg(
        input logic [7:0] msg_code,
        input logic [INTERFACE_ID_WIDTH-1:0] iface_id,
        input logic [7:0] payload[],
        input int unsigned payload_len
    );
        tx_byte_queue = {};
        tx_byte_queue.push_back(TDISP_VERSION_1_0);
        tx_byte_queue.push_back(msg_code);
        tx_byte_queue.push_back(8'h00);
        tx_byte_queue.push_back(8'h00);
        for (int i = 0; i < 12; i++)
            tx_byte_queue.push_back(iface_id[i*8 +: 8]);
        for (int i = 0; i < payload_len; i++)
            tx_byte_queue.push_back(payload[i]);
    endtask

    task automatic tb_send_msg;
        int unsigned total_bytes;
        int unsigned num_beats;
        logic [DATA_WIDTH-1:0]  tdata;
        logic [DATA_WIDTH/8-1:0] tkeep;
        total_bytes = tx_byte_queue.size();
        if (total_bytes == 0) return;
        num_beats = (total_bytes + (DATA_WIDTH/8 - 1)) / (DATA_WIDTH/8);
        for (int b = 0; b < num_beats; b++) begin
            int byte_idx;
            tdata = '0;
            tkeep = '0;
            for (int lane = 0; lane < DATA_WIDTH/8; lane++) begin
                byte_idx = b * (DATA_WIDTH/8) + lane;
                if (byte_idx < total_bytes) begin
                    tdata[lane*8 +: 8] = tx_byte_queue[byte_idx];
                    tkeep[lane] = 1'b1;
                end
            end
            @(posedge clk);
            doe_rx_tdata  <= tdata;
            doe_rx_tkeep  <= tkeep;
            doe_rx_tvalid <= 1'b1;
            doe_rx_tlast  <= (b == num_beats - 1) ? 1'b1 : 1'b0;
            while (!doe_rx_tready) @(posedge clk);
        end
        @(posedge clk);
        doe_rx_tvalid <= 1'b0;
        doe_rx_tlast  <= 1'b0;
    endtask

    task automatic tb_recv_msg(
        output logic [7:0] rsp_msg_type,
        output logic [INTERFACE_ID_WIDTH-1:0] rsp_iface_id,
        output logic [7:0] rsp_payload[$],
        output int unsigned rsp_payload_len
    );
        rx_byte_queue = {};
        rsp_payload_len = 0;
        doe_tx_tready <= 1'b1;
        forever begin
            @(posedge clk);
            if (doe_tx_tvalid && doe_tx_tready) begin
                for (int lane = 0; lane < DATA_WIDTH/8; lane++) begin
                    if (doe_tx_tkeep[lane])
                        rx_byte_queue.push_back(doe_tx_tdata[lane*8 +: 8]);
                end
                if (doe_tx_tlast) break;
            end
        end
        if (rx_byte_queue.size() >= 16) begin
            rsp_msg_type = rx_byte_queue[1];
            rsp_iface_id = '0;
            for (int i = 0; i < 12; i++)
                rsp_iface_id[i*8 +: 8] = rx_byte_queue[4 + i];
            for (int i = 16; i < rx_byte_queue.size(); i++) begin
                rsp_payload.push_back(rx_byte_queue[i]);
                rsp_payload_len++;
            end
        end else begin
            rsp_msg_type = 8'hFF;
            rsp_iface_id = '0;
        end
    endtask

    //----------------------------------------------------------------------
    // LOCK_INTERFACE send + receive
    //----------------------------------------------------------------------
    task automatic tb_send_lock_interface(
        input int unsigned       tdi_idx,
        input tdisp_lock_flags_s flags,
        input logic [7:0]        stream_id,
        output logic             success,
        output logic [15:0]      error_code
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        payload.push_back(flags[7:0]);
        payload.push_back(flags[15:8]);
        payload.push_back(stream_id);
        payload.push_back(8'h00);
        for (int i = 0; i < 8; i++) payload.push_back(8'h00); // mmio_offset
        for (int i = 0; i < 8; i++) payload.push_back(8'hFF); // p2p_mask

        tb_build_request_msg(REQ_LOCK_INTERFACE, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);

        success = 1'b0;
        error_code = '0;
        if (rsp_type == RSP_LOCK_INTERFACE) begin
            success = 1'b1;
            $display("[LOCK_TEST] LOCK TDI[%0d] SUCCESS", tdi_idx);
        end else if (rsp_type == RSP_TDISP_ERROR && rsp_payload.size() >= 4) begin
            error_code = {rsp_payload[3], rsp_payload[2], rsp_payload[1], rsp_payload[0]};
            $display("[LOCK_TEST] LOCK TDI[%0d] ERROR: code=0x%04h", tdi_idx, error_code);
        end else begin
            $error("[LOCK_TEST] LOCK TDI[%0d] UNEXPECTED rsp_type=0x%02h", tdi_idx, rsp_type);
        end
    endtask

    //----------------------------------------------------------------------
    // STOP_INTERFACE send + receive
    //----------------------------------------------------------------------
    task automatic tb_send_stop_interface(
        input int unsigned tdi_idx,
        output logic       success
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        tb_build_request_msg(REQ_STOP_INTERFACE, tb_get_iface_id(tdi_idx), payload, 0);
        tb_send_msg();
        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);

        success = (rsp_type == RSP_STOP_INTERFACE);
    endtask

    //----------------------------------------------------------------------
    // Assertion helpers
    //----------------------------------------------------------------------
    task automatic tb_check(input condition, input string test_name);
        check_count++;
        if (condition) begin
            pass_count++;
            $display("[LOCK_TEST] PASS: %s", test_name);
        end else begin
            fail_count++;
            $error("[LOCK_TEST] FAIL: %s", test_name);
        end
    endtask

    task automatic tb_assert_tdi_state(input int unsigned tdi_idx, input tdisp_state_e expected, input string ctx);
        check_count++;
        if (tdi_state_out[tdi_idx] === expected) begin
            pass_count++;
            $display("[LOCK_TEST] PASS: TDI[%0d] state=%s @ %s", tdi_idx, expected.name(), ctx);
        end else begin
            fail_count++;
            $error("[LOCK_TEST] FAIL: TDI[%0d] expected=%s got=%s @ %s",
                   tdi_idx, expected.name(), tdi_state_out[tdi_idx].name(), ctx);
        end
    endtask

    //----------------------------------------------------------------------
    // Test: Lock with specific device config override
    //----------------------------------------------------------------------
    task automatic tb_set_device_config(
        input logic stream_valid,
        input logic keys_programmed,
        input logic spdm_match,
        input logic tc0_en,
        input logic phantom_dis,
        input logic no_overlap,
        input logic valid_pg_sz,
        input logic [6:0] cls
    );
        ide_stream_valid_i       <= stream_valid;
        ide_keys_programmed_i    <= keys_programmed;
        ide_spdm_session_match_i <= spdm_match;
        ide_tc0_enabled_i        <= tc0_en;
        phantom_fn_disabled_i    <= phantom_dis;
        no_bar_overlap_i         <= no_overlap;
        valid_page_size_i        <= valid_pg_sz;
        dev_cache_line_size_i    <= cls;
    endtask

    //==========================================================================
    // Main Test Sequence
    //==========================================================================
    logic test_done;

    initial begin
        tb_axi_reset();
        tb_init_device_config();

        test_done = 1'b0;

        @(posedge rst_n);
        repeat (10) @(posedge clk);

        $display("");
        $display("============================================================");
        $display("  TDISP Lock Interface Validation Test Suite");
        $display("  Time: %0t", $time);
        $display("============================================================");

        tb_program_iface_ids();
        repeat (5) @(posedge clk);

        //======================================================================
        // TEST 1: Valid LOCK_INTERFACE with default (all-zero) flags
        //======================================================================
        $display("");
        $display("--- TEST 1: Valid LOCK with default flags ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;
            tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
            tb_check(success, "TEST1: Lock TDI[0] with zero flags succeeds");
            tb_assert_tdi_state(0, TDI_CONFIG_LOCKED, "TEST1");
        end

        // Reset back to CONFIG_UNLOCKED
        begin
            logic ok;
            tb_send_stop_interface(0, ok);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 2: Lock from CONFIG_LOCKED state → INVALID_INTERFACE_STATE
        //======================================================================
        $display("");
        $display("--- TEST 2: Lock from CONFIG_LOCKED state ---");
        begin
            logic s1, s2;
            logic [15:0] ec1, ec2;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;

            // First lock succeeds
            tb_send_lock_interface(1, zero_flags, 8'h01, s1, ec1);
            tb_check(s1, "TEST2a: First lock on TDI[1] succeeds");

            // Second lock should fail
            tb_send_lock_interface(1, zero_flags, 8'h01, s2, ec2);
            tb_check(!s2, "TEST2b: Second lock on TDI[1] fails");
            tb_check(ec2 == ERR_INVALID_INTERFACE_STATE,
                     "TEST2c: Error code is INVALID_INTERFACE_STATE");

            // Clean up
            tb_send_stop_interface(1, s1);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 3: Lock with IDE stream not valid
        //======================================================================
        $display("");
        $display("--- TEST 3: Lock with IDE stream invalid ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;
            tb_set_device_config(1'b0, 1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 7'd0);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
            tb_check(!success, "TEST3a: Lock fails when IDE stream invalid");
            tb_check(ec == ERR_INVALID_DEVICE_CONFIGURATION,
                     "TEST3b: Error is INVALID_DEVICE_CONFIGURATION");
            tb_assert_tdi_state(0, TDI_CONFIG_UNLOCKED, "TEST3");
            tb_init_device_config();
            repeat (2) @(posedge clk);
        end

        //======================================================================
        // TEST 4: Lock with IDE keys not programmed
        //======================================================================
        $display("");
        $display("--- TEST 4: Lock with IDE keys not programmed ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;
            tb_set_device_config(1'b1, 1'b0, 1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 7'd0);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
            tb_check(!success, "TEST4a: Lock fails when IDE keys not programmed");
            tb_check(ec == ERR_INVALID_DEVICE_CONFIGURATION,
                     "TEST4b: Error is INVALID_DEVICE_CONFIGURATION");
            tb_init_device_config();
            repeat (2) @(posedge clk);
        end

        //======================================================================
        // TEST 5: Lock with SPDM session mismatch
        //======================================================================
        $display("");
        $display("--- TEST 5: Lock with SPDM session mismatch ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;
            tb_set_device_config(1'b1, 1'b1, 1'b0, 1'b1, 1'b1, 1'b1, 1'b1, 7'd0);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
            tb_check(!success, "TEST5a: Lock fails on SPDM session mismatch");
            tb_check(ec == ERR_INVALID_DEVICE_CONFIGURATION,
                     "TEST5b: Error is INVALID_DEVICE_CONFIGURATION");
            tb_init_device_config();
            repeat (2) @(posedge clk);
        end

        //======================================================================
        // TEST 6: Lock with TC0 not enabled
        //======================================================================
        $display("");
        $display("--- TEST 6: Lock with TC0 not enabled ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;
            tb_set_device_config(1'b1, 1'b1, 1'b1, 1'b0, 1'b1, 1'b1, 1'b1, 7'd0);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
            tb_check(!success, "TEST6a: Lock fails when TC0 not enabled");
            tb_check(ec == ERR_INVALID_DEVICE_CONFIGURATION,
                     "TEST6b: Error is INVALID_DEVICE_CONFIGURATION");
            tb_init_device_config();
            repeat (2) @(posedge clk);
        end

        //======================================================================
        // TEST 7: Lock with phantom functions enabled
        //======================================================================
        $display("");
        $display("--- TEST 7: Lock with phantom functions enabled ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;
            tb_set_device_config(1'b1, 1'b1, 1'b1, 1'b1, 1'b0, 1'b1, 1'b1, 7'd0);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
            tb_check(!success, "TEST7a: Lock fails when phantom functions enabled");
            tb_check(ec == ERR_INVALID_DEVICE_CONFIGURATION,
                     "TEST7b: Error is INVALID_DEVICE_CONFIGURATION");
            tb_init_device_config();
            repeat (2) @(posedge clk);
        end

        //======================================================================
        // TEST 8: Lock with BAR overlap
        //======================================================================
        $display("");
        $display("--- TEST 8: Lock with BAR overlap ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;
            tb_set_device_config(1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 1'b0, 1'b1, 7'd0);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
            tb_check(!success, "TEST8a: Lock fails when BAR overlap exists");
            tb_check(ec == ERR_INVALID_DEVICE_CONFIGURATION,
                     "TEST8b: Error is INVALID_DEVICE_CONFIGURATION");
            tb_init_device_config();
            repeat (2) @(posedge clk);
        end

        //======================================================================
        // TEST 9: Lock with invalid page size
        //======================================================================
        $display("");
        $display("--- TEST 9: Lock with invalid page size ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;
            tb_set_device_config(1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 1'b0, 7'd0);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
            tb_check(!success, "TEST9a: Lock fails when page size invalid");
            tb_check(ec == ERR_INVALID_DEVICE_CONFIGURATION,
                     "TEST9b: Error is INVALID_DEVICE_CONFIGURATION");
            tb_init_device_config();
            repeat (2) @(posedge clk);
        end

        //======================================================================
        // TEST 10: Lock with cache line size mismatch
        //======================================================================
        $display("");
        $display("--- TEST 10: Lock with cache line size mismatch ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.sys_cache_line_size = 1'b1; // Request 128B but device is 64B
            tb_set_device_config(1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 7'd0);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, flags, 8'h01, success, ec);
            tb_check(!success, "TEST10a: Lock fails on CLS mismatch (request 128B, dev 64B)");
            tb_check(ec == ERR_INVALID_DEVICE_CONFIGURATION,
                     "TEST10b: Error is INVALID_DEVICE_CONFIGURATION");
        end

        //======================================================================
        // TEST 11: Lock with matching 128B cache line size
        //======================================================================
        $display("");
        $display("--- TEST 11: Lock with matching 128B cache line size ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.sys_cache_line_size = 1'b1;
            tb_set_device_config(1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 1'b1, 7'd1);
            repeat (2) @(posedge clk);
            tb_send_lock_interface(0, flags, 8'h01, success, ec);
            tb_check(success, "TEST11: Lock succeeds with matching 128B CLS");
            tb_assert_tdi_state(0, TDI_CONFIG_LOCKED, "TEST11");
            // Clean up
            tb_send_stop_interface(0, success);
            tb_init_device_config();
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 12: Lock with reserved flags non-zero
        //======================================================================
        $display("");
        $display("--- TEST 12: Lock with reserved flags non-zero ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.reserved = 11'h001; // Non-zero reserved bits
            tb_send_lock_interface(0, flags, 8'h01, success, ec);
            tb_check(!success, "TEST12a: Lock fails when reserved flags non-zero");
            tb_check(ec == ERR_INVALID_REQUEST,
                     "TEST12b: Error is INVALID_REQUEST");
            tb_assert_tdi_state(0, TDI_CONFIG_UNLOCKED, "TEST12");
        end

        //======================================================================
        // TEST 13: Lock with no_fw_update flag
        //======================================================================
        $display("");
        $display("--- TEST 13: Lock with no_fw_update flag ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.no_fw_update = 1'b1;
            tb_send_lock_interface(2, flags, 8'h01, success, ec);
            tb_check(success, "TEST13: Lock succeeds with no_fw_update flag");
            tb_assert_tdi_state(2, TDI_CONFIG_LOCKED, "TEST13");
            tb_send_stop_interface(2, success);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 14: Lock with bind_p2p flag
        //======================================================================
        $display("");
        $display("--- TEST 14: Lock with bind_p2p flag ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.bind_p2p = 1'b1;
            tb_send_lock_interface(3, flags, 8'h01, success, ec);
            tb_check(success, "TEST14: Lock succeeds with bind_p2p flag");
            tb_assert_tdi_state(3, TDI_CONFIG_LOCKED, "TEST14");
            tb_send_stop_interface(3, success);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 15: Lock with lock_msix flag
        //======================================================================
        $display("");
        $display("--- TEST 15: Lock with lock_msix flag ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.lock_msix = 1'b1;
            tb_send_lock_interface(0, flags, 8'h01, success, ec);
            tb_check(success, "TEST15: Lock succeeds with lock_msix flag");
            tb_assert_tdi_state(0, TDI_CONFIG_LOCKED, "TEST15");
            tb_send_stop_interface(0, success);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 16: Lock with all_request_redirect flag
        //======================================================================
        $display("");
        $display("--- TEST 16: Lock with all_request_redirect flag ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.all_request_redirect = 1'b1;
            tb_send_lock_interface(0, flags, 8'h01, success, ec);
            tb_check(success, "TEST16: Lock succeeds with all_request_redirect flag");
            tb_assert_tdi_state(0, TDI_CONFIG_LOCKED, "TEST16");
            tb_send_stop_interface(0, success);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 17: Lock with all valid flags combined
        //======================================================================
        $display("");
        $display("--- TEST 17: Lock with all valid flags combined ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.no_fw_update         = 1'b1;
            flags.sys_cache_line_size  = 1'b0; // 64B matches device
            flags.lock_msix            = 1'b1;
            flags.bind_p2p             = 1'b1;
            flags.all_request_redirect = 1'b1;
            tb_send_lock_interface(0, flags, 8'h01, success, ec);
            tb_check(success, "TEST17: Lock succeeds with all valid flags");
            tb_assert_tdi_state(0, TDI_CONFIG_LOCKED, "TEST17");
            tb_send_stop_interface(0, success);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 18: Lock from RUN state → INVALID_INTERFACE_STATE
        //======================================================================
        $display("");
        $display("--- TEST 18: Lock from RUN state ---");
        begin
            logic s1, s2, s3;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;

            // Lock then we need to start to get to RUN state
            // Use the full lifecycle helper approach
            tb_send_lock_interface(0, zero_flags, 8'h01, s1, ec);
            tb_check(s1, "TEST18a: Lock TDI[0] succeeds");

            // Start interface (need valid nonce - send START_INTERFACE)
            begin
                logic [7:0] payload[$];
                logic [7:0] rsp_type;
                logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
                logic [7:0] rsp_payload[$];
                int unsigned rsp_len;
                logic [NONCE_WIDTH-1:0] nonce_val;

                // Use a known nonce value
                nonce_val = 256'hDEADBEEF_CAFEBABE_12345678_9ABCDEF0_11111111_22222222_33333333_44444444;
                payload = {};
                for (int i = 0; i < 32; i++)
                    payload.push_back(nonce_val[i*8 +: 8]);

                tb_build_request_msg(REQ_START_INTERFACE, tb_get_iface_id(0),
                                     payload, payload.size());
                tb_send_msg();
                tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
                s2 = (rsp_type == RSP_START_INTERFACE);
            end

            if (s2) begin
                tb_assert_tdi_state(0, TDI_RUN, "TEST18b: In RUN state");

                // Attempt lock from RUN state
                tb_send_lock_interface(0, zero_flags, 8'h01, s3, ec);
                tb_check(!s3, "TEST18c: Lock fails from RUN state");
                tb_check(ec == ERR_INVALID_INTERFACE_STATE,
                         "TEST18d: Error is INVALID_INTERFACE_STATE");
            end

            // Clean up
            tb_send_stop_interface(0, s1);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // TEST 19: Lock from ERROR state → INVALID_INTERFACE_STATE
        //======================================================================
        $display("");
        $display("--- TEST 19: Lock from ERROR state (via stop from any state) ---");
        $display("[LOCK_TEST] Note: Cannot easily force ERROR state without TLP violation");
        $display("[LOCK_TEST] Skipping explicit ERROR state lock test (requires TLP injection)");

        //======================================================================
        // TEST 20: Multiple lock/unlock cycles on same TDI
        //======================================================================
        $display("");
        $display("--- TEST 20: Multiple lock/unlock cycles ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;

            for (int cyc = 0; cyc < 3; cyc++) begin
                tb_send_lock_interface(0, zero_flags, 8'h01, success, ec);
                tb_check(success, $sformatf("TEST20_%0d: Lock cycle %0d succeeds", cyc, cyc));
                tb_assert_tdi_state(0, TDI_CONFIG_LOCKED, $sformatf("TEST20_lock_%0d", cyc));
                tb_send_stop_interface(0, success);
                repeat (5) @(posedge clk);
                tb_assert_tdi_state(0, TDI_CONFIG_UNLOCKED, $sformatf("TEST20_unlock_%0d", cyc));
            end
        end

        //======================================================================
        // TEST 21: Lock different TDIs independently
        //======================================================================
        $display("");
        $display("--- TEST 21: Lock different TDIs independently ---");
        begin
            logic s0, s1, s2;
            logic [15:0] ec;
            tdisp_lock_flags_s zero_flags;
            zero_flags = '0;

            tb_send_lock_interface(0, zero_flags, 8'h01, s0, ec);
            tb_send_lock_interface(1, zero_flags, 8'h02, s1, ec);
            tb_send_lock_interface(2, zero_flags, 8'h03, s2, ec);

            tb_check(s0 && s1 && s2, "TEST21a: Independent lock on TDI 0,1,2");

            tb_assert_tdi_state(0, TDI_CONFIG_LOCKED, "TEST21_TDI0");
            tb_assert_tdi_state(1, TDI_CONFIG_LOCKED, "TEST21_TDI1");
            tb_assert_tdi_state(2, TDI_CONFIG_LOCKED, "TEST21_TDI2");
            tb_assert_tdi_state(3, TDI_CONFIG_UNLOCKED, "TEST21_TDI3_unlocked");

            // Clean up
            tb_send_stop_interface(0, s0);
            tb_send_stop_interface(1, s1);
            tb_send_stop_interface(2, s2);
            repeat (5) @(posedge clk);
        end

        //======================================================================
        // Final Report
        //======================================================================
        $display("");
        $display("============================================================");
        $display("  Lock Validation Test Results");
        $display("  Total Checks : %0d", check_count);
        $display("  Passed       : %0d", pass_count);
        $display("  Failed       : %0d", fail_count);
        if (fail_count == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** %0d FAILURES DETECTED ***", fail_count);
        $display("============================================================");
        $display("");

        test_done = 1'b1;
        repeat (100) @(posedge clk);
        $finish;
    end

    //==========================================================================
    // Global Timeout Watchdog
    //==========================================================================
    initial begin
        #(CLK_PERIOD * TIMEOUT_CYCLES * 20);
        if (!test_done) begin
            $error("[LOCK_TEST] GLOBAL TIMEOUT");
            $finish;
        end
    end

endmodule : test_tdisp_lock_validation
