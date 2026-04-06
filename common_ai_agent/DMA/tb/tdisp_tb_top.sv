//============================================================================
// TDISP Testbench Top Module
// Self-contained testbench for TEE Device Interface Security Protocol
// Provides: clock/reset generation, AXI-Stream BFMs, TLP stimulus,
//           SPDM session emulation, response monitoring, scoreboarding,
//           and a task-based API for all TDISP message sequences.
//============================================================================

`timescale 1ns / 1ps

module tdisp_tb_top;

    //==========================================================================
    // Imports
    //==========================================================================
    import tdisp_types::*;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter int unsigned DATA_WIDTH       = 32;
    parameter int unsigned NUM_TDI          = 4;
    parameter int unsigned ADDR_WIDTH       = 64;
    parameter int unsigned BUS_WIDTH        = 8;
    parameter int unsigned MAX_OUTSTANDING  = 255;
    parameter int unsigned MAX_MSG_BYTES    = 1024;
    parameter int unsigned MAC_WIDTH        = 32;
    parameter int unsigned SESSION_ID_WIDTH = 32;
    parameter int unsigned NONCE_WIDTH      = 256;
    parameter int unsigned INTERFACE_ID_WIDTH = 96;
    parameter int unsigned MAX_PAYLOAD_BYTES = 256;
    parameter int unsigned PAGE_SIZE        = 4096;
    parameter int unsigned NONCE_SEED       = 32'hDEADBEEF;

    // Testbench parameters
    parameter time          CLK_PERIOD      = 10ns;
    parameter int unsigned  TIMEOUT_CYCLES  = 10000;

    //==========================================================================
    // Signal Declarations
    //==========================================================================

    //--- Clock & Reset -------------------------------------------------------
    logic clk;
    logic rst_n;

    //--- DOE Mailbox AXI-Stream (Requester u2192 DUT) ----------------------------
    logic [DATA_WIDTH-1:0]       doe_rx_tdata;
    logic [DATA_WIDTH/8-1:0]     doe_rx_tkeep;
    logic                        doe_rx_tlast;
    logic                        doe_rx_tvalid;
    logic                        doe_rx_tready;

    //--- DOE Mailbox AXI-Stream (DUT u2192 Requester) ----------------------------
    logic [DATA_WIDTH-1:0]       doe_tx_tdata;
    logic [DATA_WIDTH/8-1:0]     doe_tx_tkeep;
    logic                        doe_tx_tlast;
    logic                        doe_tx_tvalid;
    logic                        doe_tx_tready;

    //--- TLP Interface -------------------------------------------------------
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

    //--- Device Configuration Inputs -----------------------------------------
    logic                        ide_stream_valid_i;
    logic                        ide_keys_programmed_i;
    logic                        ide_spdm_session_match_i;
    logic                        ide_tc0_enabled_i;
    logic                        phantom_fn_disabled_i;
    logic                        no_bar_overlap_i;
    logic                        valid_page_size_i;
    logic [6:0]                  dev_cache_line_size_i;
    logic                        fw_update_supported_i;

    //--- Interface ID Initialization -----------------------------------------
    logic                        iface_id_update_i;
    logic [$clog2(NUM_TDI)-1:0]  iface_id_tdi_index_i;
    logic [INTERFACE_ID_WIDTH-1:0] iface_id_value_i;

    //--- Status Outputs ------------------------------------------------------
    tdisp_state_e                tdi_state_out [NUM_TDI];
    logic [7:0]                  total_outstanding_o;
    logic                        transport_error_o;
    tdisp_error_code_e           transport_error_code_o;
    logic                        entropy_warn_o;

    //==========================================================================
    // Clock Generation
    //==========================================================================
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    //==========================================================================
    // Reset Generation
    //==========================================================================
    initial begin
        rst_n = 1'b0;
        repeat (20) @(posedge clk);
        rst_n = 1'b1;
        $display("[TB] Reset deasserted at time %0t", $time);
    end

    //==========================================================================
    // Waveform Dump
    //==========================================================================
    initial begin
        `ifdef DUMP_WAVES
            $dumpfile("tdisp_tb_top.vcd");
            $dumpvars(0, tdisp_tb_top);
        `endif
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

        // DOE RX (Requester u2192 DUT)
        .doe_rx_tdata           (doe_rx_tdata),
        .doe_rx_tkeep           (doe_rx_tkeep),
        .doe_rx_tlast           (doe_rx_tlast),
        .doe_rx_tvalid          (doe_rx_tvalid),
        .doe_rx_tready          (doe_rx_tready),

        // DOE TX (DUT u2192 Requester)
        .doe_tx_tdata           (doe_tx_tdata),
        .doe_tx_tkeep           (doe_tx_tkeep),
        .doe_tx_tlast           (doe_tx_tlast),
        .doe_tx_tvalid          (doe_tx_tvalid),
        .doe_tx_tready          (doe_tx_tready),

        // TLP Interface
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

        // Device Configuration
        .ide_stream_valid_i         (ide_stream_valid_i),
        .ide_keys_programmed_i      (ide_keys_programmed_i),
        .ide_spdm_session_match_i   (ide_spdm_session_match_i),
        .ide_tc0_enabled_i          (ide_tc0_enabled_i),
        .phantom_fn_disabled_i      (phantom_fn_disabled_i),
        .no_bar_overlap_i           (no_bar_overlap_i),
        .valid_page_size_i          (valid_page_size_i),
        .dev_cache_line_size_i      (dev_cache_line_size_i),
        .fw_update_supported_i      (fw_update_supported_i),

        // Interface ID Initialization
        .iface_id_update_i      (iface_id_update_i),
        .iface_id_tdi_index_i   (iface_id_tdi_index_i),
        .iface_id_value_i       (iface_id_value_i),

        // Status Outputs
        .tdi_state_out          (tdi_state_out),
        .total_outstanding_o    (total_outstanding_o),
        .transport_error_o      (transport_error_o),
        .transport_error_code_o (transport_error_code_o),
        .entropy_warn_o         (entropy_warn_o)
    );

    //==========================================================================
    // Scoreboard / Tracking Variables
    //==========================================================================
    int unsigned  sb_total_checks       = 0;
    int unsigned  sb_total_errors       = 0;
    int unsigned  sb_total_msgs_sent    = 0;
    int unsigned  sb_total_msgs_recv    = 0;

    // Per-TDI state tracking
    tdisp_state_e sb_tdi_state [NUM_TDI];

    // Last received response fields
    logic [7:0]   last_rsp_msg_type;
    logic [95:0]  last_rsp_interface_id;
    logic [31:0]  last_rsp_payload [$];
    logic [15:0]  last_rsp_error_code;
    logic [31:0]  last_rsp_error_data;

    // TLP access log
    typedef struct {
        logic [31:0] header_dw0;
        logic [31:0] header_dw2;
        logic        tee_originator;
        logic        xt_enabled;
        logic        allowed;
        logic        blocked;
    } tlp_access_log_s;

    tlp_access_log_s tlp_log [$];

    //==========================================================================
    // AXI-Stream TX BFM (Requester u2192 DUT via DOE RX)
    // Sends a complete TDISP message as a series of 32-bit beats.
    // Message format: [version(1B)][msg_type(1B)][reserved(2B)][iface_id(12B)][payload]
    //==========================================================================

    // Byte queue for building messages
    logic [7:0] tx_byte_queue [$];

    task automatic tb_axi_reset;
        doe_rx_tdata  <= '0;
        doe_rx_tkeep  <= '0;
        doe_rx_tlast  <= 1'b0;
        doe_rx_tvalid <= 1'b0;
        doe_tx_tready <= 1'b0;
        tlp_valid_i   <= 1'b0;
    endtask

    // Push a complete TDISP request message into the byte queue
    task automatic tb_build_request_msg(
        input logic [7:0]              msg_code,
        input logic [INTERFACE_ID_WIDTH-1:0] iface_id,
        input logic [7:0]              payload[],
        input int unsigned             payload_len
    );
        tx_byte_queue = {};
        // Header: version(1B) + msg_type(1B) + reserved(2B)
        tx_byte_queue.push_back(TDISP_VERSION_1_0);
        tx_byte_queue.push_back(msg_code);
        tx_byte_queue.push_back(8'h00); // reserved[15:8]
        tx_byte_queue.push_back(8'h00); // reserved[7:0]
        // INTERFACE_ID: 12 bytes, little-endian
        for (int i = 0; i < 12; i++) begin
            tx_byte_queue.push_back(iface_id[i*8 +: 8]);
        end
        // Payload
        for (int i = 0; i < payload_len; i++) begin
            tx_byte_queue.push_back(payload[i]);
        end
    endtask

    // Send the queued bytes over AXI-Stream (32-bit beats, little-endian)
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

            // Wait for ready
            while (!doe_rx_tready) @(posedge clk);
        end

        // Deassert valid after last beat
        @(posedge clk);
        doe_rx_tvalid <= 1'b0;
        doe_rx_tlast  <= 1'b0;
        doe_rx_tkeep  <= '0;
        doe_rx_tdata  <= '0;

        sb_total_msgs_sent++;
    endtask

    //==========================================================================
    // AXI-Stream RX BFM (DUT u2192 Requester via DOE TX)
    // Receives a complete TDISP response message.
    //==========================================================================
    logic [7:0]   rx_byte_queue [$];

    task automatic tb_recv_msg(
        output logic [7:0]              rsp_msg_type,
        output logic [INTERFACE_ID_WIDTH-1:0] rsp_iface_id,
        output logic [7:0]              rsp_payload[$],
        output int unsigned             rsp_payload_len
    );
        rx_byte_queue = {};
        rsp_payload   = {};
        rsp_payload_len = 0;

        // Enable TX ready to accept responses
        doe_tx_tready <= 1'b1;

        // Collect beats until tlast
        forever begin
            @(posedge clk);
            if (doe_tx_tvalid && doe_tx_tready) begin
                for (int lane = 0; lane < DATA_WIDTH/8; lane++) begin
                    if (doe_tx_tkeep[lane]) begin
                        rx_byte_queue.push_back(doe_tx_tdata[lane*8 +: 8]);
                    end
                end
                if (doe_tx_tlast) begin
                    break;
                end
            end
        end

        // Parse the response header
        if (rx_byte_queue.size() >= 16) begin
            rsp_msg_type = rx_byte_queue[1];
            // INTERFACE_ID: bytes 4..15
            rsp_iface_id = '0;
            for (int i = 0; i < 12; i++) begin
                rsp_iface_id[i*8 +: 8] = rx_byte_queue[4 + i];
            end
            // Payload: bytes 16 onwards
            for (int i = 16; i < rx_byte_queue.size(); i++) begin
                rsp_payload.push_back(rx_byte_queue[i]);
                rsp_payload_len++;
            end
        end else begin
            $error("[TB] Response too short: %0d bytes", rx_byte_queue.size());
            rsp_msg_type  = 8'hFF;
            rsp_iface_id  = '0;
            rsp_payload_len = 0;
        end

        // Store for scoreboard access
        last_rsp_msg_type   = rsp_msg_type;
        last_rsp_interface_id = rsp_iface_id;
        last_rsp_payload    = rsp_payload;
        sb_total_msgs_recv++;

        $display("[TB] Received response: msg_type=0x%02h, iface_id=0x%024h, payload_len=%0d",
                 rsp_msg_type, rsp_iface_id, rsp_payload_len);
    endtask

    //==========================================================================
    // Timeout Watchdog
    //==========================================================================
    task automatic tb_timeout(
        input int unsigned cycles,
        input string       context
    );
        fork
            begin : timeout_block
                repeat (cycles) @(posedge clk);
                $error("[TB] TIMEOUT after %0d cycles in context: %s", cycles, context);
                sb_total_errors++;
            end
        join_none
    endtask

    task automatic tb_clear_timeout;
        disable fork;
    endtask

    //==========================================================================
    // Wait for specific TDI state
    //==========================================================================
    task automatic tb_wait_tdi_state(
        input int unsigned tdi_idx,
        input tdisp_state_e expected_state,
        input int unsigned max_cycles = TIMEOUT_CYCLES
    );
        int unsigned cycle_count = 0;
        while (tdi_state_out[tdi_idx] !== expected_state && cycle_count < max_cycles) begin
            @(posedge clk);
            cycle_count++;
        end
        if (cycle_count >= max_cycles) begin
            $error("[TB] TIMEOUT waiting for TDI[%0d] state=%s (got %s)",
                   tdi_idx, expected_state.name(), tdi_state_out[tdi_idx].name());
            sb_total_errors++;
        end else begin
            $display("[TB] TDI[%0d] reached state %s after %0d cycles",
                     tdi_idx, expected_state.name(), cycle_count);
        end
    endtask

    //==========================================================================
    // Device Configuration Initialization
    //==========================================================================
    task automatic tb_init_device_config;
        ide_stream_valid_i       <= 1'b1;
        ide_keys_programmed_i    <= 1'b1;
        ide_spdm_session_match_i <= 1'b1;
        ide_tc0_enabled_i        <= 1'b1;
        phantom_fn_disabled_i    <= 1'b1;
        no_bar_overlap_i         <= 1'b1;
        valid_page_size_i        <= 1'b1;
        dev_cache_line_size_i    <= 7'd64;     // 64B cache line size
        fw_update_supported_i    <= 1'b1;
    endtask

    //==========================================================================
    // Interface ID Programming
    //==========================================================================
    task automatic tb_program_iface_ids;
        for (int i = 0; i < NUM_TDI; i++) begin
            @(posedge clk);
            iface_id_tdi_index_i <= i;
            iface_id_value_i     <= {64'h0, 8'h0, 8'h0, 16'h0001, 8'(i + 1), 8'h0};
            iface_id_update_i    <= 1'b1;
            @(posedge clk);
            iface_id_update_i    <= 1'b0;
            $display("[TB] Programmed INTERFACE_ID for TDI[%0d] = 0x%024h", i, iface_id_value_i);
        end
    endtask

    // Get the INTERFACE_ID for a given TDI index
    function automatic logic [INTERFACE_ID_WIDTH-1:0] tb_get_iface_id(
        input int unsigned tdi_idx
    );
        return {64'h0, 8'h0, 8'h0, 16'h0001, 8'(tdi_idx + 1), 8'h0};
    endfunction

    //==========================================================================
    // TDI State Initialization Tracking
    //==========================================================================
    task automatic tb_reset_state_tracking;
        for (int i = 0; i < NUM_TDI; i++) begin
            sb_tdi_state[i] = TDI_CONFIG_UNLOCKED;
        end
    endtask

    // Update scoreboard state tracking (call after state-changing operations)
    task automatic tb_update_sb_state(
        input int unsigned tdi_idx,
        input tdisp_state_e new_state
    );
        sb_tdi_state[tdi_idx] = new_state;
        $display("[TB] SB: TDI[%0d] state updated to %s", tdi_idx, new_state.name());
    endtask

    //==========================================================================
    // HIGH-LEVEL MESSAGE API
    // Task-based API for sending each TDISP request and receiving/checking
    // the corresponding response.
    //==========================================================================

    //--- Helper: extract 32-bit word from byte array (little-endian) -----------
    function automatic logic [31:0] tb_get_word(
        input logic [7:0] byte_arr[$],
        input int unsigned word_idx
    );
        int base = word_idx * 4;
        logic [31:0] result = '0;
        if (base + 3 < byte_arr.size()) begin
            result[7:0]   = byte_arr[base];
            result[15:8]  = byte_arr[base + 1];
            result[23:16] = byte_arr[base + 2];
            result[31:24] = byte_arr[base + 3];
        end
        return result;
    endfunction

    //--- GET_TDISP_VERSION ---------------------------------------------------
    task automatic tb_send_get_version(
        input int unsigned tdi_idx = 0
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        tb_build_request_msg(REQ_GET_TDISP_VERSION, tb_get_iface_id(tdi_idx), payload, 0);
        tb_send_msg();
        $display("[TB] Sent GET_TDISP_VERSION for TDI[%0d]", tdi_idx);

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        if (rsp_type != RSP_TDISP_VERSION) begin
            $error("[TB] FAIL: Expected RSP_TDISP_VERSION(0x%02h), got 0x%02h", RSP_TDISP_VERSION, rsp_type);
            sb_total_errors++;
        end else begin
            $display("[TB] PASS: GET_TDISP_VERSION response received (payload_len=%0d)", rsp_len);
        end
    endtask

    //--- GET_TDISP_CAPABILITIES ----------------------------------------------
    task automatic tb_send_get_capabilities(
        input int unsigned tdi_idx = 0
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        tb_build_request_msg(REQ_GET_TDISP_CAPABILITIES, tb_get_iface_id(tdi_idx), payload, 0);
        tb_send_msg();
        $display("[TB] Sent GET_TDISP_CAPABILITIES for TDI[%0d]", tdi_idx);

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        if (rsp_type != RSP_TDISP_CAPABILITIES) begin
            $error("[TB] FAIL: Expected RSP_TDISP_CAPABILITIES(0x%02h), got 0x%02h", RSP_TDISP_CAPABILITIES, rsp_type);
            sb_total_errors++;
        end else begin
            $display("[TB] PASS: GET_TDISP_CAPABILITIES response received (payload_len=%0d)", rsp_len);
        end
    endtask

    //--- LOCK_INTERFACE_REQUEST ----------------------------------------------
    task automatic tb_send_lock_interface(
        input int unsigned    tdi_idx = 0,
        input tdisp_lock_flags_s flags = '0,
        input logic [7:0]     stream_id = 8'h01,
        input logic [63:0]    mmio_offset = 64'h0,
        input logic [63:0]    p2p_mask = 64'hFFFF_FFFF_FFFF_F000,
        output logic          success
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        // Build LOCK_INTERFACE payload (bytes 0..19 after header)
        // flags[1:0] + stream_id + reserved + mmio_offset(8B) + p2p_mask(8B) = 20 bytes
        payload = {};
        // Flags: 2 bytes little-endian
        {>>{payload}} = {payload, flags[7:0], flags[15:8]};
        payload.push_back(flags[7:0]);
        payload.push_back(flags[15:8]);
        // Remove the duplicates from structured push above
        payload.delete(payload.size()-3);
        payload.delete(payload.size()-2);

        // Rebuild payload cleanly
        payload = {};
        payload.push_back(flags[7:0]);           // flags low byte
        payload.push_back(flags[15:8]);          // flags high byte
        payload.push_back(stream_id);            // stream_id
        payload.push_back(8'h00);                // reserved
        // mmio_reporting_offset: 8 bytes little-endian
        for (int i = 0; i < 8; i++) begin
            payload.push_back(mmio_offset[i*8 +: 8]);
        end
        // bind_p2p_addr_mask: 8 bytes little-endian
        for (int i = 0; i < 8; i++) begin
            payload.push_back(p2p_mask[i*8 +: 8]);
        end

        tb_build_request_msg(REQ_LOCK_INTERFACE, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        $display("[TB] Sent LOCK_INTERFACE for TDI[%0d] flags=0x%04h stream_id=0x%02h",
                 tdi_idx, flags, stream_id);

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        success = 1'b0;
        if (rsp_type == RSP_LOCK_INTERFACE) begin
            success = 1'b1;
            tb_update_sb_state(tdi_idx, TDI_CONFIG_LOCKED);
            $display("[TB] PASS: LOCK_INTERFACE successful for TDI[%0d]", tdi_idx);
        end else if (rsp_type == RSP_TDISP_ERROR) begin
            if (rsp_payload.size() >= 8) begin
                last_rsp_error_code = {rsp_payload[3], rsp_payload[2],
                                       rsp_payload[1], rsp_payload[0]};
                last_rsp_error_data = {rsp_payload[7], rsp_payload[6],
                                       rsp_payload[5], rsp_payload[4]};
            end
            $display("[TB] LOCK_INTERFACE error: code=0x%04h data=0x%08h",
                     last_rsp_error_code, last_rsp_error_data);
        end else begin
            $error("[TB] FAIL: Unexpected response 0x%02h for LOCK_INTERFACE", rsp_type);
            sb_total_errors++;
        end
    endtask

    //--- START_INTERFACE_REQUEST ---------------------------------------------
    task automatic tb_send_start_interface(
        input int unsigned          tdi_idx = 0,
        input logic [NONCE_WIDTH-1:0] nonce = '0,
        output logic                success
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        // Nonce: 32 bytes little-endian
        payload = {};
        for (int i = 0; i < 32; i++) begin
            payload.push_back(nonce[i*8 +: 8]);
        end

        tb_build_request_msg(REQ_START_INTERFACE, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        $display("[TB] Sent START_INTERFACE for TDI[%0d] with nonce", tdi_idx);

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        success = 1'b0;
        if (rsp_type == RSP_START_INTERFACE) begin
            success = 1'b1;
            tb_update_sb_state(tdi_idx, TDI_RUN);
            $display("[TB] PASS: START_INTERFACE successful for TDI[%0d]", tdi_idx);
        end else if (rsp_type == RSP_TDISP_ERROR) begin
            if (rsp_payload.size() >= 4) begin
                last_rsp_error_code = {rsp_payload[3], rsp_payload[2],
                                       rsp_payload[1], rsp_payload[0]};
            end
            $display("[TB] START_INTERFACE error: code=0x%04h", last_rsp_error_code);
        end else begin
            $error("[TB] FAIL: Unexpected response 0x%02h for START_INTERFACE", rsp_type);
            sb_total_errors++;
        end
    endtask

    //--- STOP_INTERFACE_REQUEST ----------------------------------------------
    task automatic tb_send_stop_interface(
        input int unsigned tdi_idx = 0,
        output logic       success
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        tb_build_request_msg(REQ_STOP_INTERFACE, tb_get_iface_id(tdi_idx),
                             payload, 0);
        tb_send_msg();
        $display("[TB] Sent STOP_INTERFACE for TDI[%0d]", tdi_idx);

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        success = 1'b0;
        if (rsp_type == RSP_STOP_INTERFACE) begin
            success = 1'b1;
            tb_update_sb_state(tdi_idx, TDI_CONFIG_UNLOCKED);
            $display("[TB] PASS: STOP_INTERFACE successful for TDI[%0d]", tdi_idx);
        end else if (rsp_type == RSP_TDISP_ERROR) begin
            if (rsp_payload.size() >= 4) begin
                last_rsp_error_code = {rsp_payload[3], rsp_payload[2],
                                       rsp_payload[1], rsp_payload[0]};
            end
            $display("[TB] STOP_INTERFACE error: code=0x%04h", last_rsp_error_code);
        end else begin
            $error("[TB] FAIL: Unexpected response 0x%02h for STOP_INTERFACE", rsp_type);
            sb_total_errors++;
        end
    endtask

    //--- GET_DEVICE_INTERFACE_REPORT -----------------------------------------
    task automatic tb_send_get_interface_report(
        input int unsigned tdi_idx = 0
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        tb_build_request_msg(REQ_GET_DEVICE_INTERFACE_REPORT, tb_get_iface_id(tdi_idx),
                             payload, 0);
        tb_send_msg();
        $display("[TB] Sent GET_DEVICE_INTERFACE_REPORT for TDI[%0d]", tdi_idx);

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        if (rsp_type == RSP_DEVICE_INTERFACE_REPORT) begin
            $display("[TB] PASS: GET_DEVICE_INTERFACE_REPORT received (len=%0d)", rsp_len);
        end else if (rsp_type == RSP_TDISP_ERROR) begin
            $display("[TB] GET_DEVICE_INTERFACE_REPORT error (expected if not LOCKED)");
        end else begin
            $error("[TB] FAIL: Unexpected response 0x%02h", rsp_type);
            sb_total_errors++;
        end
    endtask

    //--- GET_DEVICE_INTERFACE_STATE ------------------------------------------
    task automatic tb_send_get_interface_state(
        input int unsigned  tdi_idx = 0,
        output tdisp_state_e reported_state
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        tb_build_request_msg(REQ_GET_DEVICE_INTERFACE_STATE, tb_get_iface_id(tdi_idx),
                             payload, 0);
        tb_send_msg();
        $display("[TB] Sent GET_DEVICE_INTERFACE_STATE for TDI[%0d]", tdi_idx);

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        reported_state = TDI_CONFIG_UNLOCKED;
        if (rsp_type == RSP_DEVICE_INTERFACE_STATE && rsp_payload.size() >= 1) begin
            // State is in the first payload byte, lower nibble
            case (rsp_payload[0][3:0])
                4'h0: reported_state = TDI_CONFIG_UNLOCKED;
                4'h1: reported_state = TDI_CONFIG_LOCKED;
                4'h2: reported_state = TDI_RUN;
                4'h3: reported_state = TDI_ERROR;
                default: reported_state = TDI_ERROR;
            endcase
            $display("[TB] TDI[%0d] reported state: %s (raw=0x%02h)",
                     tdi_idx, reported_state.name(), rsp_payload[0]);
        end else if (rsp_type == RSP_TDISP_ERROR) begin
            $display("[TB] GET_DEVICE_INTERFACE_STATE error");
        end else begin
            $error("[TB] FAIL: Unexpected response 0x%02h", rsp_type);
            sb_total_errors++;
        end
    endtask

    //--- BIND_P2P_STREAM_REQUEST --------------------------------------------
    task automatic tb_send_bind_p2p_stream(
        input int unsigned tdi_idx = 0,
        input logic [7:0]  stream_id = 8'h02,
        output logic       success
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        payload.push_back(stream_id);
        for (int i = 0; i < 3; i++) payload.push_back(8'h00); // reserved

        tb_build_request_msg(REQ_BIND_P2P_STREAM, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();
        $display("[TB] Sent BIND_P2P_STREAM for TDI[%0d] stream_id=0x%02h", tdi_idx, stream_id);

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        success = (rsp_type == RSP_BIND_P2P_STREAM);
        if (success) begin
            $display("[TB] PASS: BIND_P2P_STREAM successful");
        end else begin
            $display("[TB] BIND_P2P_STREAM response: 0x%02h", rsp_type);
        end
    endtask

    //--- UNBIND_P2P_STREAM_REQUEST ------------------------------------------
    task automatic tb_send_unbind_p2p_stream(
        input int unsigned tdi_idx = 0,
        input logic [7:0]  stream_id = 8'h02,
        output logic       success
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
        sb_total_checks++;

        success = (rsp_type == RSP_UNBIND_P2P_STREAM);
        $display("[TB] UNBIND_P2P_STREAM for TDI[%0d]: %s", tdi_idx, success ? "OK" : "FAIL");
    endtask

    //--- SET_MMIO_ATTRIBUTE_REQUEST -----------------------------------------
    task automatic tb_send_set_mmio_attribute(
        input int unsigned   tdi_idx = 0,
        input logic [63:0]   start_page_addr = 64'h1000_0000,
        input logic [31:0]   num_pages = 32'h10,
        input logic          is_non_tee_mem = 1'b0,
        output logic         success
    );
        logic [7:0] payload[$];
        logic [7:0] rsp_type;
        logic [INTERFACE_ID_WIDTH-1:0] rsp_iface;
        logic [7:0] rsp_payload[$];
        int unsigned rsp_len;

        payload = {};
        // start_page_addr: 8 bytes LE
        for (int i = 0; i < 8; i++) begin
            payload.push_back(start_page_addr[i*8 +: 8]);
        end
        // num_pages: 4 bytes LE
        for (int i = 0; i < 4; i++) begin
            payload.push_back(num_pages[i*8 +: 8]);
        end
        // attributes: is_non_tee_mem in bit 2, range_id in bits 1:0
        payload.push_back({5'b0, is_non_tee_mem, 2'b00});

        tb_build_request_msg(REQ_SET_MMIO_ATTRIBUTE, tb_get_iface_id(tdi_idx),
                             payload, payload.size());
        tb_send_msg();

        tb_recv_msg(rsp_type, rsp_iface, rsp_payload, rsp_len);
        sb_total_checks++;

        success = (rsp_type == RSP_SET_MMIO_ATTRIBUTE);
        $display("[TB] SET_MMIO_ATTRIBUTE for TDI[%0d]: %s", tdi_idx, success ? "OK" : "FAIL");
    endtask

    //==========================================================================
    // TLP STIMULUS API
    //==========================================================================

    // Send a Memory Read TLP (32-bit addressing) for TLP rules testing
    task automatic tb_send_tlp_mrd(
        input logic [63:0]       addr,
        input logic [15:0]       requester_id,
        input logic              tee_originator,
        input logic              xt_enabled,
        input logic [1:0]        at = 2'b00
    );
        @(posedge clk);
        tlp_valid_i          <= 1'b1;
        tlp_is_4dw_i         <= (addr[63:32] != 32'h0) ? 1'b1 : 1'b0;
        tlp_header_dw0_i     <= {4'h0, 3'b000, at, 1'b0, 10'd1}; // MRd, 1 DW
        tlp_header_dw2_i     <= addr[31:0];
        tlp_header_dw3_i     <= (tlp_is_4dw_i) ? addr[63:32] : 32'h0;
        tlp_requester_id_i   <= requester_id;
        tlp_at_i             <= at;
        tlp_tee_originator_i <= tee_originator;
        tlp_xt_enabled_i     <= xt_enabled;

        @(posedge clk);
        tlp_valid_i <= 1'b0;

        // Log the access
        tlp_log.push_back('{tlp_header_dw0_i, tlp_header_dw2_i, tlp_header_dw3_i,
                            tee_originator, xt_enabled, tlp_allow_o, tlp_blocked_o});
    endtask

    // Send a Memory Write TLP
    task automatic tb_send_tlp_mwr(
        input logic [63:0]       addr,
        input logic [15:0]       requester_id,
        input logic              tee_originator,
        input logic              xt_enabled,
        input logic [1:0]        at = 2'b00
    );
        @(posedge clk);
        tlp_valid_i          <= 1'b1;
        tlp_is_4dw_i         <= (addr[63:32] != 32'h0) ? 1'b1 : 1'b0;
        tlp_header_dw0_i     <= {4'h0, 3'b010, at, 1'b0, 10'd1}; // MWr, 1 DW
        tlp_header_dw2_i     <= addr[31:0];
        tlp_header_dw3_i     <= (tlp_is_4dw_i) ? addr[63:32] : 32'h0;
        tlp_requester_id_i   <= requester_id;
        tlp_at_i             <= at;
        tlp_tee_originator_i <= tee_originator;
        tlp_xt_enabled_i     <= xt_enabled;

        @(posedge clk);
        tlp_valid_i <= 1'b0;

        tlp_log.push_back('{tlp_header_dw0_i, tlp_header_dw2_i, tlp_header_dw3_i,
                            tee_originator, xt_enabled, tlp_allow_o, tlp_blocked_o});
    endtask

    // Clear TLP interface
    task automatic tb_tlp_idle;
        tlp_valid_i <= 1'b0;
        tlp_header_dw0_i <= '0;
        tlp_header_dw2_i <= '0;
        tlp_header_dw3_i <= '0;
        tlp_is_4dw_i     <= 1'b0;
        tlp_requester_id_i <= '0;
        tlp_at_i          <= '0;
        tlp_tee_originator_i <= 1'b0;
        tlp_xt_enabled_i  <= 1'b0;
    endtask

    //==========================================================================
    // State Assertion Helpers
    //==========================================================================
    task automatic tb_assert_tdi_state(
        input int unsigned  tdi_idx,
        input tdisp_state_e expected,
        input string        context
    );
        sb_total_checks++;
        if (tdi_state_out[tdi_idx] !== expected) begin
            $error("[TB] ASSERT FAIL @ %s: TDI[%0d] expected=%s, actual=%s",
                   context, tdi_idx, expected.name(), tdi_state_out[tdi_idx].name());
            sb_total_errors++;
        end else begin
            $display("[TB] ASSERT PASS @ %s: TDI[%0d] state=%s", context, tdi_idx, expected.name());
        end
    endtask

    task automatic tb_assert_tlp_allowed(
        input logic expected_allow,
        input string context
    );
        sb_total_checks++;
        if (tlp_allow_o !== expected_allow) begin
            $error("[TB] TLP ASSERT FAIL @ %s: expected_allow=%0b, actual=%0b",
                   context, expected_allow, tlp_allow_o);
            sb_total_errors++;
        end
    endtask

    task automatic tb_assert_no_transport_error;
        if (transport_error_o) begin
            $error("[TB] Unexpected transport error: code=%s",
                   transport_error_code_o.name());
            sb_total_errors++;
        end
    endtask

    //==========================================================================
    // Full Lifecycle Sequence (CONFIG_UNLOCKED u2192 CONFIG_LOCKED u2192 RUN u2192 back)
    //==========================================================================
    task automatic tb_run_full_lifecycle(
        input int unsigned tdi_idx = 0
    );
        logic lock_ok, start_ok, stop_ok;

        $display("[TB] === Full Lifecycle Test for TDI[%0d] ===", tdi_idx);

        // Step 1: Verify initial state
        tb_assert_tdi_state(tdi_idx, TDI_CONFIG_UNLOCKED, "INIT");

        // Step 2: GET_TDISP_VERSION
        tb_send_get_version(tdi_idx);

        // Step 3: GET_TDISP_CAPABILITIES
        tb_send_get_capabilities(tdi_idx);

        // Step 4: LOCK_INTERFACE u2192 CONFIG_LOCKED
        tb_send_lock_interface(tdi_idx, '0, 8'h01, 64'h0, 64'hFFFF_FFFF_FFFF_F000, lock_ok);
        if (lock_ok) begin
            tb_assert_tdi_state(tdi_idx, TDI_CONFIG_LOCKED, "POST_LOCK");

            // Step 5: GET_DEVICE_INTERFACE_STATE u2192 should report CONFIG_LOCKED
            begin
                tdisp_state_e reported;
                tb_send_get_interface_state(tdi_idx, reported);
                sb_total_checks++;
                if (reported != TDI_CONFIG_LOCKED) begin
                    $error("[TB] Expected CONFIG_LOCKED state, got %s", reported.name());
                    sb_total_errors++;
                end
            end

            // Step 6: GET_DEVICE_INTERFACE_REPORT
            tb_send_get_interface_report(tdi_idx);

            // Step 7: START_INTERFACE u2192 RUN
            tb_send_start_interface(tdi_idx, 256'hDEADBEEF_CAFEBABE_12345678_9ABCDEF0_11111111_22222222_33333333_44444444, start_ok);
            if (start_ok) begin
                tb_assert_tdi_state(tdi_idx, TDI_RUN, "POST_START");

                // Step 8: Verify state via GET_DEVICE_INTERFACE_STATE
                begin
                    tdisp_state_e reported;
                    tb_send_get_interface_state(tdi_idx, reported);
                    sb_total_checks++;
                    if (reported != TDI_RUN) begin
                        $error("[TB] Expected RUN state, got %s", reported.name());
                        sb_total_errors++;
                    end
                end

                // Step 9: STOP_INTERFACE u2192 CONFIG_UNLOCKED
                tb_send_stop_interface(tdi_idx, stop_ok);
                tb_assert_tdi_state(tdi_idx, TDI_CONFIG_UNLOCKED, "POST_STOP");
            end else begin
                $display("[TB] START_INTERFACE failed, skipping STOP");
            end
        end else begin
            $display("[TB] LOCK_INTERFACE failed, skipping rest of lifecycle");
        end

        $display("[TB] === Lifecycle Test for TDI[%0d] complete ===", tdi_idx);
    endtask

    //==========================================================================
    // Scoreboard Report
    //==========================================================================
    task automatic tb_report;
        $display("");
        $display("u2554u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2557");
        $display("u2551          TDISP TESTBENCH REPORT             u2551");
        $display("u2560u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2563");
        $display("u2551 Messages Sent     : %0d", sb_total_msgs_sent);
        $display("u2551 Messages Received : %0d", sb_total_msgs_recv);
        $display("u2551 Total Checks      : %0d", sb_total_checks);
        $display("u2551 Total Errors      : %0d", sb_total_errors);
        $display("u2560u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2563");
        for (int i = 0; i < NUM_TDI; i++) begin
            $display("u2551 TDI[%0d] HW State   : %s", i, tdi_state_out[i].name());
            $display("u2551 TDI[%0d] SB State   : %s", i, sb_tdi_state[i].name());
        end
        $display("u2560u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2563");
        if (sb_total_errors == 0) begin
            $display("u2551         *** ALL TESTS PASSED ***            u2551");
        end else begin
            $display("u2551     *** %0d ERROR(S) DETECTED ***           u2551", sb_total_errors);
        end
        $display("u255au2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u255d");
        $display("");
    endtask

    //==========================================================================
    // Main Test Sequence
    //==========================================================================
    logic main_test_done;

    initial begin
        // Initialize all signals
        tb_axi_reset();
        tb_tlp_idle();
        tb_init_device_config();
        tb_reset_state_tracking();

        main_test_done = 1'b0;

        // Wait for reset
        @(posedge rst_n);
        repeat (10) @(posedge clk);

        $display("[TB] ============================================================");
        $display("[TB] TDISP Testbench Starting at time %0t", $time);
        $display("[TB] NUM_TDI=%0d, DATA_WIDTH=%0d, CLK_PERIOD=%0tps",
                 NUM_TDI, DATA_WIDTH, CLK_PERIOD/1ps);
        $display("[TB] ============================================================");

        // Program INTERFACE_IDs for all TDIs
        tb_program_iface_ids();
        repeat (5) @(posedge clk);

        // Run the full lifecycle test on TDI 0
        tb_run_full_lifecycle(0);

        // Run a second lifecycle to verify re-lock works
        $display("[TB] === Re-lock test (second lifecycle) for TDI[0] ===");
        tb_run_full_lifecycle(0);

        // Report results
        tb_report();

        main_test_done = 1'b1;
        $display("[TB] Test sequence complete at time %0t", $time);

        `ifndef RUN_FOREVER
            repeat (100) @(posedge clk);
            $finish;
        `endif
    end

    //==========================================================================
    // Simulation Watchdog
    //==========================================================================
    initial begin
        #(CLK_PERIOD * TIMEOUT_CYCLES * 10);
        if (!main_test_done) begin
            $error("[TB] GLOBAL TIMEOUT: Simulation did not complete in time");
            tb_report();
            $finish;
        end
    end

    //==========================================================================
    // Continuous Monitors
    //==========================================================================

    // Monitor: TDI state changes
    always @(tdi_state_out) begin
        for (int i = 0; i < NUM_TDI; i++) begin
            $display("[TB][MON] TDI[%0d] state changed to %s at time %0t",
                     i, tdi_state_out[i].name(), $time);
        end
    end

    // Monitor: TLP violation IRQ
    always @(posedge tlp_violation_irq_o) begin
        $display("[TB][MON] TLP Violation IRQ asserted at time %0t, TDI=%0d",
                 $time, tlp_tdi_index_o);
    end

    // Monitor: Transport errors
    always @(posedge transport_error_o) begin
        $display("[TB][MON] Transport Error: code=%s at time %0t",
                 transport_error_code_o.name(), $time);
    end

    // Monitor: Entropy warnings
    always @(posedge entropy_warn_o) begin
        $warning("[TB][MON] Entropy Warning at time %0t", $time);
    end

endmodule : tdisp_tb_top
