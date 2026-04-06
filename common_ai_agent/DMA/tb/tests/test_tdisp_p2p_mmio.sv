//============================================================================
// TDISP P2P Stream and MMIO Attribute Test
// Tests BIND_P2P_STREAM, UNBIND_P2P_STREAM, and SET_MMIO_ATTRIBUTE
// per PCIe TDISP spec Chapter 11
//
// Scenarios:
//   - BIND_P2P_STREAM in RUN state (success and without bind_p2p flag)
//   - UNBIND_P2P_STREAM in RUN state
//   - SET_MMIO_ATTRIBUTE in RUN state
//   - Error when P2P/MMIO attempted in wrong state
//   - Multiple P2P stream bind/unbind cycles
//============================================================================

`timescale 1ns / 1ps

module test_tdisp_p2p_mmio;

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
        $display("[P2P_MMIO_TEST] Reset deasserted at time %0t", $time);
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
    // BFM Infrastructure (same pattern as lock validation test)
    //==========================================================================
    logic [7:0] tx_byte_queue [$];
    logic [7:0] rx_byte_queue [$];

    task automatic tb_axi_reset;
        doe_rx_tdata  <= '0; doe_rx_tkeep  <= '0;
        doe_rx_tlast  <= 1'b0; doe_rx_tvalid <= 1'b0;
        doe_tx_tready <= 1'b0; tlp_valid_i   <= 1'b0;
    endtask

    task automatic tb_init_device_config;
        ide_stream_valid_i       <= 1'b1;
        ide_keys_programmed_i    <= 1'b1;
        ide_spdm_session_match_i <= 1'b1;
        ide_tc0_enabled_i        <= 1'b1;
        phantom_fn_disabled_i    <= 1'b1;
        no_bar_overlap_i         <= 1'b1;
        valid_page_size_i        <= 1'b1;
        dev_cache_line_size_i    <= 7'd0;
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
        int unsigned total_bytes, num_beats;
        logic [DATA_WIDTH-1:0]  tdata;
        logic [DATA_WIDTH/8-1:0] tkeep;
        total_bytes = tx_byte_queue.size();
        if (total_bytes == 0) return;
        num_beats = (total_bytes + (DATA_WIDTH/8 - 1)) / (DATA_WIDTH/8);
        for (int b = 0; b < num_beats; b++) begin
            int byte_idx;
            tdata = '0; tkeep = '0;
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

    //==========================================================================
    // High-level Message API
    //==========================================================================

    task automatic tb_send_lock_interface(
        input int unsigned       tdi_idx,
        input tdisp_lock_flags_s flags,
        input logic [7:0]        stream_id,
        output logic             success
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
        for (int i = 0; i < 8; i++) payload.push_back(8'h00);
        for (int i = 0; i < 8; i++) payload.push_back(8'hFF);

        tb_build_request_msg(REQ_LOCK_INTERFACE, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);

        success = (rsp_type == RSP_LOCK_INTERFACE);
        $display("[P2P_MMIO_TEST] LOCK TDI[%0d]: %s", tdi_idx, success ? "OK" : "FAIL");
    endtask

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

    task automatic tb_send_start_interface(
        input int unsigned tdi_idx,
        output logic       success
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;
        logic [NONCE_WIDTH-1:0] nonce_val;

        nonce_val = 256'hDEADBEEF_CAFEBABE_12345678_9ABCDEF0_11111111_22222222_33333333_44444444;
        payload = {};
        for (int i = 0; i < 32; i++)
            payload.push_back(nonce_val[i*8 +: 8]);

        tb_build_request_msg(REQ_START_INTERFACE, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        success = (rsp_type == RSP_START_INTERFACE);
        $display("[P2P_MMIO_TEST] START TDI[%0d]: %s", tdi_idx, success ? "OK" : "FAIL");
    endtask

    //--- BIND_P2P_STREAM -----------------------------------------------------
    task automatic tb_send_bind_p2p(
        input int unsigned tdi_idx,
        input logic [7:0]  stream_id,
        output logic       success,
        output logic [15:0] error_code
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        payload.push_back(stream_id);
        for (int i = 0; i < 3; i++) payload.push_back(8'h00);

        tb_build_request_msg(REQ_BIND_P2P_STREAM, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);

        success = 1'b0;
        error_code = '0;
        if (rsp_type == RSP_BIND_P2P_STREAM) begin
            success = 1'b1;
            $display("[P2P_MMIO_TEST] BIND_P2P TDI[%0d] stream=0x%02h: OK", tdi_idx, stream_id);
        end else if (rsp_type == RSP_TDISP_ERROR && rsp_payload.size() >= 4) begin
            error_code = {rsp_payload[3], rsp_payload[2], rsp_payload[1], rsp_payload[0]};
            $display("[P2P_MMIO_TEST] BIND_P2P TDI[%0d] ERROR: code=0x%04h", tdi_idx, error_code);
        end else begin
            $error("[P2P_MMIO_TEST] BIND_P2P TDI[%0d] UNEXPECTED rsp=0x%02h", tdi_idx, rsp_type);
        end
    endtask

    //--- UNBIND_P2P_STREAM ---------------------------------------------------
    task automatic tb_send_unbind_p2p(
        input int unsigned tdi_idx,
        input logic [7:0]  stream_id,
        output logic       success,
        output logic [15:0] error_code
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        payload.push_back(stream_id);
        for (int i = 0; i < 3; i++) payload.push_back(8'h00);

        tb_build_request_msg(REQ_UNBIND_P2P_STREAM, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);

        success = 1'b0;
        error_code = '0;
        if (rsp_type == RSP_UNBIND_P2P_STREAM) begin
            success = 1'b1;
            $display("[P2P_MMIO_TEST] UNBIND_P2P TDI[%0d] stream=0x%02h: OK", tdi_idx, stream_id);
        end else if (rsp_type == RSP_TDISP_ERROR && rsp_payload.size() >= 4) begin
            error_code = {rsp_payload[3], rsp_payload[2], rsp_payload[1], rsp_payload[0]};
            $display("[P2P_MMIO_TEST] UNBIND_P2P TDI[%0d] ERROR: code=0x%04h", tdi_idx, error_code);
        end else begin
            $error("[P2P_MMIO_TEST] UNBIND_P2P TDI[%0d] UNEXPECTED rsp=0x%02h", tdi_idx, rsp_type);
        end
    endtask

    //--- SET_MMIO_ATTRIBUTE --------------------------------------------------
    task automatic tb_send_set_mmio(
        input int unsigned tdi_idx,
        input logic [63:0] start_page_addr,
        input logic [31:0] num_pages,
        input logic        is_non_tee_mem,
        output logic       success,
        output logic [15:0] error_code
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        for (int i = 0; i < 8; i++)
            payload.push_back(start_page_addr[i*8 +: 8]);
        for (int i = 0; i < 4; i++)
            payload.push_back(num_pages[i*8 +: 8]);
        payload.push_back({5'b0, is_non_tee_mem, 2'b00});

        tb_build_request_msg(REQ_SET_MMIO_ATTRIBUTE, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);

        success = 1'b0;
        error_code = '0;
        if (rsp_type == RSP_SET_MMIO_ATTRIBUTE) begin
            success = 1'b1;
            $display("[P2P_MMIO_TEST] SET_MMIO TDI[%0d] addr=0x%016h pages=%0d non_tee=%0b: OK",
                     tdi_idx, start_page_addr, num_pages, is_non_tee_mem);
        end else if (rsp_type == RSP_TDISP_ERROR && rsp_payload.size() >= 4) begin
            error_code = {rsp_payload[3], rsp_payload[2], rsp_payload[1], rsp_payload[0]};
            $display("[P2P_MMIO_TEST] SET_MMIO TDI[%0d] ERROR: code=0x%04h", tdi_idx, error_code);
        end else begin
            $error("[P2P_MMIO_TEST] SET_MMIO TDI[%0d] UNEXPECTED rsp=0x%02h", tdi_idx, rsp_type);
        end
    endtask

    //==========================================================================
    // Assertion Helpers
    //==========================================================================
    task automatic tb_check(input condition, input string test_name);
        check_count++;
        if (condition) begin
            pass_count++;
            $display("[P2P_MMIO_TEST] PASS: %s", test_name);
        end else begin
            fail_count++;
            $error("[P2P_MMIO_TEST] FAIL: %s", test_name);
        end
    endtask

    task automatic tb_assert_tdi_state(input int unsigned tdi_idx,
                                       input tdisp_state_e expected,
                                       input string ctx);
        check_count++;
        if (tdi_state_out[tdi_idx] === expected) begin
            pass_count++;
            $display("[P2P_MMIO_TEST] PASS: TDI[%0d] state=%s @ %s", tdi_idx, expected.name(), ctx);
        end else begin
            fail_count++;
            $error("[P2P_MMIO_TEST] FAIL: TDI[%0d] expected=%s got=%s @ %s",
                   tdi_idx, expected.name(), tdi_state_out[tdi_idx].name(), ctx);
        end
    endtask

    //----------------------------------------------------------------------
    // Lifecycle helper: take TDI from UNLOCKED to RUN
    //----------------------------------------------------------------------
    task automatic tb_goto_run_state(
        input int unsigned       tdi_idx,
        input tdisp_lock_flags_s lock_flags,
        input logic [7:0]        stream_id,
        output logic             success
    );
        logic lock_ok, start_ok;
        success = 1'b0;

        tb_send_lock_interface(tdi_idx, lock_flags, stream_id, lock_ok);
        if (!lock_ok) return;

        tb_send_start_interface(tdi_idx, start_ok);
        if (!start_ok) return;

        success = 1'b1;
    endtask

    //----------------------------------------------------------------------
    // Lifecycle helper: take TDI back to UNLOCKED
    //----------------------------------------------------------------------
    task automatic tb_goto_unlocked(input int unsigned tdi_idx);
        logic ok;
        if (tdi_state_out[tdi_idx] !== TDI_CONFIG_UNLOCKED) begin
            tb_send_stop_interface(tdi_idx, ok);
            repeat (5) @(posedge clk);
        end
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
        $display("================================================================");
        $display("  TDISP P2P Stream and MMIO Attribute Test Suite");
        $display("  Time: %0t", $time);
        $display("================================================================");

        tb_program_iface_ids();
        repeat (5) @(posedge clk);

        //======================================================================
        // TEST 1: BIND_P2P_STREAM in RUN state with bind_p2p flag set
        //======================================================================
        $display("");
        $display("--- TEST 1: BIND_P2P in RUN state (with bind_p2p flag) ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.bind_p2p = 1'b1;

            tb_goto_run_state(0, flags, 8'h01, success);
            tb_check(success, "TEST1a: TDI[0] reached RUN state");

            tb_send_bind_p2p(0, 8'h02, success, ec);
            tb_check(success, "TEST1b: BIND_P2P succeeds in RUN state with bind_p2p flag");

            tb_goto_unlocked(0);
        end

        //======================================================================
        // TEST 2: BIND_P2P_STREAM without bind_p2p flag in LOCK → error
        //======================================================================
        $display("");
        $display("--- TEST 2: BIND_P2P without bind_p2p flag ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            // bind_p2p = 0 (not set)

            tb_goto_run_state(0, flags, 8'h01, success);
            tb_check(success, "TEST2a: TDI[0] reached RUN state");

            tb_send_bind_p2p(0, 8'h02, success, ec);
            tb_check(!success, "TEST2b: BIND_P2P fails when bind_p2p flag not set in LOCK");

            tb_goto_unlocked(0);
        end

        //======================================================================
        // TEST 3: UNBIND_P2P_STREAM in RUN state
        //======================================================================
        $display("");
        $display("--- TEST 3: UNBIND_P2P in RUN state ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.bind_p2p = 1'b1;

            tb_goto_run_state(0, flags, 8'h01, success);
            tb_check(success, "TEST3a: TDI[0] reached RUN state");

            // First bind
            tb_send_bind_p2p(0, 8'h03, success, ec);
            tb_check(success, "TEST3b: BIND_P2P stream_id=3 succeeds");

            // Then unbind
            tb_send_unbind_p2p(0, 8'h03, success, ec);
            tb_check(success, "TEST3c: UNBIND_P2P stream_id=3 succeeds");

            tb_goto_unlocked(0);
        end

        //======================================================================
        // TEST 4: BIND_P2P in CONFIG_LOCKED state → error
        //======================================================================
        $display("");
        $display("--- TEST 4: BIND_P2P in CONFIG_LOCKED state ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.bind_p2p = 1'b1;

            tb_send_lock_interface(0, flags, 8'h01, success);
            tb_check(success, "TEST4a: LOCK TDI[0] succeeds");
            tb_assert_tdi_state(0, TDI_CONFIG_LOCKED, "TEST4");

            tb_send_bind_p2p(0, 8'h02, success, ec);
            tb_check(!success, "TEST4b: BIND_P2P fails in CONFIG_LOCKED state");

            tb_goto_unlocked(0);
        end

        //======================================================================
        // TEST 5: BIND_P2P in CONFIG_UNLOCKED state → error
        //======================================================================
        $display("");
        $display("--- TEST 5: BIND_P2P in CONFIG_UNLOCKED state ---");
        begin
            logic success;
            logic [15:0] ec;

            tb_assert_tdi_state(0, TDI_CONFIG_UNLOCKED, "TEST5_pre");
            tb_send_bind_p2p(0, 8'h02, success, ec);
            tb_check(!success, "TEST5: BIND_P2P fails in CONFIG_UNLOCKED state");
        end

        //======================================================================
        // TEST 6: SET_MMIO_ATTRIBUTE in RUN state
        //======================================================================
        $display("");
        $display("--- TEST 6: SET_MMIO_ATTRIBUTE in RUN state ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;

            tb_goto_run_state(0, flags, 8'h01, success);
            tb_check(success, "TEST6a: TDI[0] reached RUN state");

            tb_send_set_mmio(0, 64'h1000_0000, 32'h10, 1'b0, success, ec);
            tb_check(success, "TEST6b: SET_MMIO succeeds in RUN state");

            tb_goto_unlocked(0);
        end

        //======================================================================
        // TEST 7: SET_MMIO_ATTRIBUTE with IS_NON_TEE_MEM attribute
        //======================================================================
        $display("");
        $display("--- TEST 7: SET_MMIO with IS_NON_TEE_MEM ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;

            tb_goto_run_state(0, flags, 8'h01, success);
            tb_check(success, "TEST7a: TDI[0] reached RUN state");

            tb_send_set_mmio(0, 64'h2000_0000, 32'h20, 1'b1, success, ec);
            tb_check(success, "TEST7b: SET_MMIO with non-TEE mem succeeds");

            tb_goto_unlocked(0);
        end

        //======================================================================
        // TEST 8: SET_MMIO_ATTRIBUTE in CONFIG_LOCKED state → error
        //======================================================================
        $display("");
        $display("--- TEST 8: SET_MMIO in CONFIG_LOCKED state ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;

            tb_send_lock_interface(0, flags, 8'h01, success);
            tb_check(success, "TEST8a: LOCK TDI[0] succeeds");

            tb_send_set_mmio(0, 64'h1000_0000, 32'h10, 1'b0, success, ec);
            tb_check(!success, "TEST8b: SET_MMIO fails in CONFIG_LOCKED state");

            tb_goto_unlocked(0);
        end

        //======================================================================
        // TEST 9: SET_MMIO_ATTRIBUTE in CONFIG_UNLOCKED state → error
        //======================================================================
        $display("");
        $display("--- TEST 9: SET_MMIO in CONFIG_UNLOCKED state ---");
        begin
            logic success;
            logic [15:0] ec;

            tb_send_set_mmio(0, 64'h1000_0000, 32'h10, 1'b0, success, ec);
            tb_check(!success, "TEST9: SET_MMIO fails in CONFIG_UNLOCKED state");
        end

        //======================================================================
        // TEST 10: Multiple P2P bind/unbind cycles in RUN state
        //======================================================================
        $display("");
        $display("--- TEST 10: Multiple P2P bind/unbind cycles ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;
            flags.bind_p2p = 1'b1;

            tb_goto_run_state(0, flags, 8'h01, success);
            tb_check(success, "TEST10a: TDI[0] reached RUN state");

            for (int cyc = 0; cyc < 3; cyc++) begin
                logic [7:0] sid;
                sid = 8'h10 + 8'(cyc);
                tb_send_bind_p2p(0, sid, success, ec);
                tb_check(success, $sformatf("TEST10_%0d_bind: Bind cycle %0d succeeds", cyc, cyc));

                tb_send_unbind_p2p(0, sid, success, ec);
                tb_check(success, $sformatf("TEST10_%0d_unbind: Unbind cycle %0d succeeds", cyc, cyc));
            end

            tb_goto_unlocked(0);
        end

        //======================================================================
        // TEST 11: Multiple MMIO ranges in RUN state
        //======================================================================
        $display("");
        $display("--- TEST 11: Multiple MMIO ranges in RUN state ---");
        begin
            logic success;
            logic [15:0] ec;
            tdisp_lock_flags_s flags;
            flags = '0;

            tb_goto_run_state(1, flags, 8'h01, success);
            tb_check(success, "TEST11a: TDI[1] reached RUN state");

            // Set multiple MMIO ranges
            for (int r = 0; r < 4; r++) begin
                logic [63:0] addr;
                addr = 64'h1000_0000 + 64'(r) * 64'h1_0000;
                tb_send_set_mmio(1, addr, 32'h4, (r % 2 == 0), success, ec);
                tb_check(success, $sformatf("TEST11_%0d: SET_MMIO range %0d succeeds", r, r));
            end

            tb_goto_unlocked(1);
        end

        //======================================================================
        // TEST 12: P2P and MMIO on different TDIs simultaneously
        //======================================================================
        $display("");
        $display("--- TEST 12: P2P and MMIO on different TDIs ---");
        begin
            logic s0, s1;
            logic [15:0] ec;
            tdisp_lock_flags_s flags_p2p, flags_nop2p;
            flags_p2p = '0; flags_p2p.bind_p2p = 1'b1;
            flags_nop2p = '0;

            // TDI[2] with P2P, TDI[3] without P2P
            tb_goto_run_state(2, flags_p2p, 8'h01, s0);
            tb_goto_run_state(3, flags_nop2p, 8'h01, s1);
            tb_check(s0 && s1, "TEST12a: Both TDI[2] and TDI[3] in RUN state");

            // TDI[2] can bind P2P
            tb_send_bind_p2p(2, 8'h05, s0, ec);
            tb_check(s0, "TEST12b: TDI[2] BIND_P2P succeeds (has bind_p2p flag)");

            // TDI[3] cannot bind P2P
            tb_send_bind_p2p(3, 8'h06, s1, ec);
            tb_check(!s1, "TEST12c: TDI[3] BIND_P2P fails (no bind_p2p flag)");

            // Both can set MMIO
            tb_send_set_mmio(2, 64'hA000_0000, 32'h8, 1'b0, s0, ec);
            tb_check(s0, "TEST12d: TDI[2] SET_MMIO succeeds");

            tb_send_set_mmio(3, 64'hB000_0000, 32'h8, 1'b1, s1, ec);
            tb_check(s1, "TEST12e: TDI[3] SET_MMIO succeeds");

            tb_goto_unlocked(2);
            tb_goto_unlocked(3);
        end

        //======================================================================
        // Final Report
        //======================================================================
        $display("");
        $display("================================================================");
        $display("  P2P/MMIO Test Results");
        $display("  Total Checks : %0d", check_count);
        $display("  Passed       : %0d", pass_count);
        $display("  Failed       : %0d", fail_count);
        if (fail_count == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** %0d FAILURES DETECTED ***", fail_count);
        $display("================================================================");
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
            $error("[P2P_MMIO_TEST] GLOBAL TIMEOUT");
            $finish;
        end
    end

endmodule : test_tdisp_p2p_mmio
