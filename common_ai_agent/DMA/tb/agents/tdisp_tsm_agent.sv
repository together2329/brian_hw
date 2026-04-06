//============================================================================
// TDISP TSM (TEE Security Manager) Agent / Requester BFM
//
// Encapsulates the full TSM requester-side protocol behavior:
//   - AXI-Stream master BFM for DOE TX path (sends TDISP requests)
//   - AXI-Stream slave  BFM for DOE RX path (receives TDISP responses)
//   - SPDM session emulation and tracking
//   - IDE stream binding emulation
//   - All 12 TDISP request types as task-based API
//   - Per-TDI state tracking and nonce management
//   - Response parsing, error extraction, and automatic checking
//
// Instantiable module u2014 can be wired directly to tdisp_top DOE ports.
//============================================================================

`timescale 1ns / 1ps

module tdisp_tsm_agent #(
    parameter int unsigned DATA_WIDTH        = 32,
    parameter int unsigned NUM_TDI           = 4,
    parameter int unsigned NONCE_WIDTH       = 256,
    parameter int unsigned INTERFACE_ID_WIDTH = 96,
    parameter int unsigned MAX_RSP_BEATS     = 256,
    parameter time          CLK_PERIOD       = 10ns,
    parameter int unsigned  RSP_TIMEOUT_CYCLES = 5000
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //=== DOE Requester TX (TSM u2192 DUT) u2014 AXI-Stream Master ====================
    output logic [DATA_WIDTH-1:0]           tsm_tx_tdata,
    output logic [DATA_WIDTH/8-1:0]         tsm_tx_tkeep,
    output logic                            tsm_tx_tlast,
    output logic                            tsm_tx_tvalid,
    input  logic                            tsm_tx_tready,

    //=== DOE Requester RX (DUT u2192 TSM) u2014 AXI-Stream Slave =====================
    input  logic [DATA_WIDTH-1:0]           tsm_rx_tdata,
    input  logic [DATA_WIDTH/8-1:0]         tsm_rx_tkeep,
    input  logic                            tsm_rx_tlast,
    input  logic                            tsm_rx_tvalid,
    output logic                            tsm_rx_tready
);

    import tdisp_types::*;

    //==========================================================================
    // SPDM Session State Tracking
    //==========================================================================
    typedef struct {
        logic [31:0]              session_id;
        logic                     active;
        logic                     secured;
        logic [INTERFACE_ID_WIDTH-1:0] bound_iface_id;
    } spdm_session_s;

    spdm_session_s spdm_sessions [4]; // Up to 4 concurrent SPDM sessions
    int unsigned    active_session_idx = 0;

    //==========================================================================
    // Per-TDI TSM Tracking
    //==========================================================================
    typedef struct {
        tdisp_state_e             state;
        logic [INTERFACE_ID_WIDTH-1:0] iface_id;
        logic [NONCE_WIDTH-1:0]   last_nonce;
        logic                     nonce_valid;
        logic [7:0]               bound_stream_id;
        tdisp_lock_flags_s        lock_flags;
        int unsigned              ops_count;
        logic                     locked;
        logic                     started;
    } tsm_tdi_track_s;

    tsm_tdi_track_s tdi_track [NUM_TDI];

    //==========================================================================
    // Response Capture Storage
    //==========================================================================
    typedef struct {
        logic [7:0]               rsp_code;
        logic [INTERFACE_ID_WIDTH-1:0] iface_id;
        logic [7:0]               payload_bytes [$];
        int unsigned              payload_len;
        logic [15:0]              error_code;
        logic [31:0]              error_data;
        logic                     is_error;
        logic                     valid;
    } tsm_response_s;

    tsm_response_s  last_response;
    int unsigned    total_requests_sent  = 0;
    int unsigned    total_responses_recv = 0;
    int unsigned    total_errors_seen    = 0;

    //==========================================================================
    // IDE Stream Emulation
    //==========================================================================
    logic [7:0]    ide_stream_pool [$];
    logic [7:0]    bound_streams   [NUM_TDI][$];

    initial begin
        // Pre-populate IDE stream pool with 16 stream IDs
        for (int i = 1; i <= 16; i++) begin
            ide_stream_pool.push_back(8'(i));
        end
    end

    //==========================================================================
    // Initialize TSM Agent
    //==========================================================================
    task automatic tsm_init;
        // Clear TX
        tsm_tx_tdata  <= '0;
        tsm_tx_tkeep  <= '0;
        tsm_tx_tlast  <= 1'b0;
        tsm_tx_tvalid <= 1'b0;
        tsm_rx_tready <= 1'b1; // Always ready to accept responses

        // Clear tracking
        for (int i = 0; i < NUM_TDI; i++) begin
            tdi_track[i].state       = TDI_CONFIG_UNLOCKED;
            tdi_track[i].iface_id    = '0;
            tdi_track[i].last_nonce  = '0;
            tdi_track[i].nonce_valid = 1'b0;
            tdi_track[i].bound_stream_id = 8'h0;
            tdi_track[i].lock_flags  = '0;
            tdi_track[i].ops_count   = 0;
            tdi_track[i].locked      = 1'b0;
            tdi_track[i].started     = 1'b0;
        end

        for (int s = 0; s < 4; s++) begin
            spdm_sessions[s].session_id   = '0;
            spdm_sessions[s].active       = 1'b0;
            spdm_sessions[s].secured      = 1'b0;
            spdm_sessions[s].bound_iface_id = '0;
        end
        active_session_idx = 0;

        // Clear response
        last_response.valid       = 1'b0;
        last_response.is_error    = 1'b0;
        last_response.rsp_code    = 8'h00;
        last_response.iface_id    = '0;
        last_response.payload_len = 0;
        last_response.error_code  = '0;
        last_response.error_data  = '0;

        total_requests_sent  = 0;
        total_responses_recv = 0;
        total_errors_seen    = 0;

        $display("[TSM] Agent initialized, NUM_TDI=%0d", NUM_TDI);
    endtask

    //==========================================================================
    // SPDM Session Management
    //==========================================================================
    task automatic tsm_create_session(
        input logic [31:0] session_id,
        output int unsigned session_idx
    );
        session_idx = active_session_idx;
        spdm_sessions[session_idx].session_id    = session_id;
        spdm_sessions[session_idx].active        = 1'b1;
        spdm_sessions[session_idx].secured       = 1'b1;
        spdm_sessions[session_idx].bound_iface_id = '0;
        active_session_idx = (active_session_idx + 1) % 4;
        $display("[TSM] SPDM session created: idx=%0d, id=0x%08h", session_idx, session_id);
    endtask

    task automatic tsm_destroy_session(
        input int unsigned session_idx
    );
        spdm_sessions[session_idx].active  = 1'b0;
        spdm_sessions[session_idx].secured = 1'b0;
        $display("[TSM] SPDM session destroyed: idx=%0d", session_idx);
    endtask

    function automatic logic tsm_session_active(
        input int unsigned session_idx
    );
        return spdm_sessions[session_idx].active;
    endfunction

    //==========================================================================
    // Interface ID Management
    //==========================================================================
    task automatic tsm_set_tdi_iface_id(
        input int unsigned  tdi_idx,
        input logic [INTERFACE_ID_WIDTH-1:0] iface_id
    );
        tdi_track[tdi_idx].iface_id = iface_id;
        $display("[TSM] TDI[%0d] INTERFACE_ID set to 0x%024h", tdi_idx, iface_id);
    endtask

    function automatic logic [INTERFACE_ID_WIDTH-1:0] tsm_get_tdi_iface_id(
        input int unsigned tdi_idx
    );
        return tdi_track[tdi_idx].iface_id;
    endfunction

    // Generate a default INTERFACE_ID pattern for a TDI index
    function automatic logic [INTERFACE_ID_WIDTH-1:0] tsm_gen_iface_id(
        input int unsigned tdi_idx
    );
        logic [INTERFACE_ID_WIDTH-1:0] id;
        id = {64'hA5A5_0000_0000_0000, 16'h0001, 8'(tdi_idx + 1), 8'h00};
        return id;
    endfunction

    //==========================================================================
    // AXI-Stream TX Engine u2014 Send message byte-by-byte over 32-bit bus
    //==========================================================================
    logic [7:0] tx_byte_q [$];

    task automatic tsm_send_raw_bytes(
        input logic [7:0] bytes[$]
    );
        int unsigned total_bytes;
        int unsigned num_beats;
        logic [DATA_WIDTH-1:0]   tdata;
        logic [DATA_WIDTH/8-1:0] tkeep;

        total_bytes = bytes.size();
        if (total_bytes == 0) return;

        num_beats = (total_bytes + (DATA_WIDTH/8) - 1) / (DATA_WIDTH/8);

        for (int b = 0; b < num_beats; b++) begin
            int byte_idx;
            tdata = '0;
            tkeep = '0;
            for (int lane = 0; lane < DATA_WIDTH/8; lane++) begin
                byte_idx = b * (DATA_WIDTH/8) + lane;
                if (byte_idx < total_bytes) begin
                    tdata[lane*8 +: 8] = bytes[byte_idx];
                    tkeep[lane] = 1'b1;
                end
            end
            @(posedge clk);
            tsm_tx_tdata  <= tdata;
            tsm_tx_tkeep  <= tkeep;
            tsm_tx_tvalid <= 1'b1;
            tsm_tx_tlast  <= (b == num_beats - 1) ? 1'b1 : 1'b0;
            // Backpressure handling
            while (!tsm_tx_tready) @(posedge clk);
        end
        @(posedge clk);
        tsm_tx_tvalid <= 1'b0;
        tsm_tx_tlast  <= 1'b0;
        tsm_tx_tkeep  <= '0;
        tsm_tx_tdata  <= '0;

        total_requests_sent++;
    endtask

    //==========================================================================
    // AXI-Stream RX Engine u2014 Receive response message
    //==========================================================================
    logic [7:0] rx_byte_q [$];

    task automatic tsm_recv_raw_bytes(
        output logic [7:0] bytes[$],
        output int unsigned byte_len
    );
        bytes = {};
        byte_len = 0;
        tsm_rx_tready <= 1'b1;

        fork
            begin : recv_block
                forever begin
                    @(posedge clk);
                    if (tsm_rx_tvalid && tsm_rx_tready) begin
                        for (int lane = 0; lane < DATA_WIDTH/8; lane++) begin
                            if (tsm_rx_tkeep[lane]) begin
                                bytes.push_back(tsm_rx_tdata[lane*8 +: 8]);
                            end
                        end
                        if (tsm_rx_tlast) begin
                            byte_len = bytes.size();
                            total_responses_recv++;
                            disable recv_block;
                        end
                    end
                end
            end
            begin : timeout_block
                repeat (RSP_TIMEOUT_CYCLES) @(posedge clk);
                $error("[TSM] TIMEOUT: No response received within %0d cycles", RSP_TIMEOUT_CYCLES);
                total_errors_seen++;
                disable recv_block;
            end
        join

        tsm_rx_tready <= 1'b1;
    endtask

    //==========================================================================
    // Build TDISP Request Header + Payload
    //==========================================================================
    task automatic tsm_build_request(
        input logic [7:0]                msg_code,
        input logic [INTERFACE_ID_WIDTH-1:0] iface_id,
        input logic [7:0]                payload[$],
        output logic [7:0]               msg_bytes[$]
    );
        msg_bytes = {};
        // Header: version(1B) + msg_type(1B) + reserved(2B)
        msg_bytes.push_back(TDISP_VERSION_1_0);  // Version 1.0
        msg_bytes.push_back(msg_code);
        msg_bytes.push_back(8'h00);               // Reserved MSB
        msg_bytes.push_back(8'h00);               // Reserved LSB
        // INTERFACE_ID: 12 bytes little-endian
        for (int i = 0; i < 12; i++) begin
            msg_bytes.push_back(iface_id[i*8 +: 8]);
        end
        // Payload
        for (int i = 0; i < payload.size(); i++) begin
            msg_bytes.push_back(payload[i]);
        end
    endtask

    //==========================================================================
    // Parse Response into Structured Fields
    //==========================================================================
    task automatic tsm_parse_response(
        input logic [7:0] raw_bytes[$]
    );
        if (raw_bytes.size() < 16) begin
            $error("[TSM] Response too short: %0d bytes (min 16)", raw_bytes.size());
            last_response.valid    = 1'b0;
            last_response.is_error = 1'b1;
            total_errors_seen++;
            return;
        end

        last_response.valid       = 1'b1;
        last_response.rsp_code    = raw_bytes[1];
        last_response.is_error    = (raw_bytes[1] == RSP_TDISP_ERROR);

        // INTERFACE_ID: bytes 4..15
        last_response.iface_id = '0;
        for (int i = 0; i < 12; i++) begin
            last_response.iface_id[i*8 +: 8] = raw_bytes[4 + i];
        end

        // Payload: bytes 16+
        last_response.payload_bytes = {};
        last_response.payload_len   = 0;
        for (int i = 16; i < raw_bytes.size(); i++) begin
            last_response.payload_bytes.push_back(raw_bytes[i]);
            last_response.payload_len++;
        end

        // Error extraction
        last_response.error_code = '0;
        last_response.error_data = '0;
        if (last_response.is_error && last_response.payload_len >= 8) begin
            last_response.error_code = {last_response.payload_bytes[3],
                                        last_response.payload_bytes[2],
                                        last_response.payload_bytes[1],
                                        last_response.payload_bytes[0]};
            last_response.error_data = {last_response.payload_bytes[7],
                                        last_response.payload_bytes[6],
                                        last_response.payload_bytes[5],
                                        last_response.payload_bytes[4]};
            total_errors_seen++;
            $display("[TSM] TDISP ERROR: code=0x%04h data=0x%08h",
                     last_response.error_code, last_response.error_data);
        end

        $display("[TSM] Response parsed: code=0x%02h (%s), iface_id=0x%024h, payload_len=%0d",
                 last_response.rsp_code,
                 last_response.is_error ? "ERROR" : "OK",
                 last_response.iface_id,
                 last_response.payload_len);
    endtask

    //==========================================================================
    // Generic Send-And-Receive
    //==========================================================================
    task automatic tsm_send_request(
        input logic [7:0]                msg_code,
        input logic [INTERFACE_ID_WIDTH-1:0] iface_id,
        input logic [7:0]                payload[$]
    );
        logic [7:0] msg_bytes[$];
        logic [7:0] rsp_bytes[$];
        int unsigned rsp_len;

        tsm_build_request(msg_code, iface_id, payload, msg_bytes);
        $display("[TSM] Sending request 0x%02h, iface_id=0x%024h, payload_len=%0d",
                 msg_code, iface_id, payload.size());

        tsm_send_raw_bytes(msg_bytes);
        tsm_recv_raw_bytes(rsp_bytes, rsp_len);
        tsm_parse_response(rsp_bytes);
    endtask

    //==========================================================================
    // TDISP REQUEST API u2014 All 12 Request Types
    //==========================================================================

    //--- 1. GET_TDISP_VERSION (0x81) -----------------------------------------
    task automatic tsm_get_tdisp_version(
        input int unsigned  tdi_idx = 0,
        output logic [7:0]  version_count,
        output logic [15:0] version_entries[$]
    );
        logic [7:0] payload[$];
        payload = {};
        tsm_send_request(REQ_GET_TDISP_VERSION, tdi_track[tdi_idx].iface_id, payload);

        version_count = '0;
        version_entries = {};
        if (!last_response.is_error && last_response.payload_len >= 1) begin
            version_count = last_response.payload_bytes[0];
            // Each version entry is 2 bytes
            for (int i = 1; i + 1 < last_response.payload_len; i += 2) begin
                version_entries.push_back({last_response.payload_bytes[i+1],
                                           last_response.payload_bytes[i]});
            end
        end
        $display("[TSM] GET_TDISP_VERSION: count=%0d, entries=%0d",
                 version_count, version_entries.size());
    endtask

    //--- 2. GET_TDISP_CAPABILITIES (0x82) ------------------------------------
    task automatic tsm_get_tdisp_capabilities(
        input int unsigned  tdi_idx = 0,
        output logic        xt_mode_supported,
        output logic [127:0] req_msgs_supported,
        output logic [15:0] lock_iface_flags_supported,
        output logic [7:0]  dev_addr_width,
        output logic [7:0]  num_req_this,
        output logic [7:0]  num_req_all
    );
        logic [7:0] payload[$];
        payload = {};
        tsm_send_request(REQ_GET_TDISP_CAPABILITIES, tdi_track[tdi_idx].iface_id, payload);

        xt_mode_supported     = 1'b0;
        req_msgs_supported    = '0;
        lock_iface_flags_supported = '0;
        dev_addr_width        = '0;
        num_req_this          = '0;
        num_req_all           = '0;

        if (!last_response.is_error && last_response.payload_len >= 28) begin
            xt_mode_supported = last_response.payload_bytes[0][0];
            // req_msgs_supported: 16 bytes starting at payload offset 4
            for (int i = 0; i < 16 && (4+i) < last_response.payload_len; i++) begin
                req_msgs_supported[i*8 +: 8] = last_response.payload_bytes[4+i];
            end
            // lock_iface_flags: 2 bytes at offset 20
            if (last_response.payload_len > 21) begin
                lock_iface_flags_supported = {last_response.payload_bytes[21],
                                              last_response.payload_bytes[20]};
            end
            // dev_addr_width: offset 24 (within extended payload)
            if (last_response.payload_len > 24) dev_addr_width = last_response.payload_bytes[24];
            if (last_response.payload_len > 25) num_req_this    = last_response.payload_bytes[25];
            if (last_response.payload_len > 26) num_req_all     = last_response.payload_bytes[26];
        end
        $display("[TSM] GET_TDISP_CAPABILITIES: xt=%0b, addr_width=%0d",
                 xt_mode_supported, dev_addr_width);
    endtask

    //--- 3. LOCK_INTERFACE_REQUEST (0x83) ------------------------------------
    task automatic tsm_lock_interface(
        input int unsigned       tdi_idx = 0,
        input tdisp_lock_flags_s flags = '0,
        input logic [7:0]        stream_id = 8'h01,
        input logic [63:0]       mmio_offset = 64'h0,
        input logic [63:0]       p2p_addr_mask = 64'hFFFF_FFFF_FFFF_F000,
        output logic             success
    );
        logic [7:0] payload[$];
        payload = {};

        // Flags: 2 bytes LE
        payload.push_back(flags[7:0]);
        payload.push_back(flags[15:8]);
        // Stream ID
        payload.push_back(stream_id);
        // Reserved
        payload.push_back(8'h00);
        // MMIO Reporting Offset: 8 bytes LE
        for (int i = 0; i < 8; i++)
            payload.push_back(mmio_offset[i*8 +: 8]);
        // Bind P2P Address Mask: 8 bytes LE
        for (int i = 0; i < 8; i++)
            payload.push_back(p2p_addr_mask[i*8 +: 8]);

        tsm_send_request(REQ_LOCK_INTERFACE, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_LOCK_INTERFACE);
        if (success) begin
            tdi_track[tdi_idx].state       = TDI_CONFIG_LOCKED;
            tdi_track[tdi_idx].locked      = 1'b1;
            tdi_track[tdi_idx].lock_flags  = flags;
            tdi_track[tdi_idx].bound_stream_id = stream_id;
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] LOCK_INTERFACE SUCCESS: TDI[%0d] u2192 CONFIG_LOCKED", tdi_idx);
        end else begin
            $display("[TSM] LOCK_INTERFACE FAILED: TDI[%0d], error_code=0x%04h",
                     tdi_idx, last_response.error_code);
        end
    endtask

    //--- 4. GET_DEVICE_INTERFACE_REPORT (0x84) --------------------------------
    task automatic tsm_get_interface_report(
        input int unsigned  tdi_idx = 0,
        output logic [7:0]  report_bytes[$],
        output logic        success
    );
        logic [7:0] payload[$];
        payload = {};
        tsm_send_request(REQ_GET_DEVICE_INTERFACE_REPORT, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_DEVICE_INTERFACE_REPORT);
        report_bytes = {};
        if (success) begin
            report_bytes = last_response.payload_bytes;
            tdi_track[tdi_idx].ops_count++;
        end
    endtask

    //--- 5. GET_DEVICE_INTERFACE_STATE (0x85) ---------------------------------
    task automatic tsm_get_interface_state(
        input int unsigned   tdi_idx = 0,
        output tdisp_state_e reported_state,
        output logic         success
    );
        logic [7:0] payload[$];
        payload = {};
        tsm_send_request(REQ_GET_DEVICE_INTERFACE_STATE, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_DEVICE_INTERFACE_STATE);
        reported_state = TDI_ERROR;

        if (success && last_response.payload_len >= 1) begin
            case (last_response.payload_bytes[0][3:0])
                4'h0: reported_state = TDI_CONFIG_UNLOCKED;
                4'h1: reported_state = TDI_CONFIG_LOCKED;
                4'h2: reported_state = TDI_RUN;
                4'h3: reported_state = TDI_ERROR;
                default: reported_state = TDI_ERROR;
            endcase
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] GET_DEVICE_INTERFACE_STATE: TDI[%0d] = %s",
                     tdi_idx, reported_state.name());
        end
    endtask

    //--- 6. START_INTERFACE_REQUEST (0x86) ------------------------------------
    task automatic tsm_start_interface(
        input int unsigned             tdi_idx = 0,
        input logic [NONCE_WIDTH-1:0]  nonce = '0,
        output logic                   success
    );
        logic [7:0] payload[$];
        payload = {};

        // 32-byte nonce, little-endian
        for (int i = 0; i < 32; i++) begin
            payload.push_back(nonce[i*8 +: 8]);
        end

        // Store nonce for potential validation
        tdi_track[tdi_idx].last_nonce  = nonce;
        tdi_track[tdi_idx].nonce_valid = 1'b1;

        tsm_send_request(REQ_START_INTERFACE, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_START_INTERFACE);
        if (success) begin
            tdi_track[tdi_idx].state   = TDI_RUN;
            tdi_track[tdi_idx].started = 1'b1;
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] START_INTERFACE SUCCESS: TDI[%0d] u2192 RUN", tdi_idx);
        end else begin
            $display("[TSM] START_INTERFACE FAILED: TDI[%0d], error_code=0x%04h",
                     tdi_idx, last_response.error_code);
        end
    endtask

    // Generate a random nonce for START_INTERFACE
    function automatic logic [NONCE_WIDTH-1:0] tsm_gen_nonce(
        input int unsigned seed_val = 0
    );
        logic [NONCE_WIDTH-1:0] nonce;
        // Deterministic pseudo-random nonce for verification
        nonce = {64'(seed_val + 1), 64'hCAFEBABE_DEADBEEF,
                 64'h12345678_9ABCDEF0, 64'(seed_val ^ 32'hA5A5A5A5)};
        return nonce;
    endfunction

    //--- 7. STOP_INTERFACE_REQUEST (0x87) -------------------------------------
    task automatic tsm_stop_interface(
        input int unsigned tdi_idx = 0,
        output logic       success
    );
        logic [7:0] payload[$];
        payload = {};
        tsm_send_request(REQ_STOP_INTERFACE, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_STOP_INTERFACE);
        if (success) begin
            tdi_track[tdi_idx].state       = TDI_CONFIG_UNLOCKED;
            tdi_track[tdi_idx].locked      = 1'b0;
            tdi_track[tdi_idx].started     = 1'b0;
            tdi_track[tdi_idx].nonce_valid = 1'b0;
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] STOP_INTERFACE SUCCESS: TDI[%0d] u2192 CONFIG_UNLOCKED", tdi_idx);
        end else begin
            $display("[TSM] STOP_INTERFACE result: error_code=0x%04h", last_response.error_code);
        end
    endtask

    //--- 8. BIND_P2P_STREAM_REQUEST (0x88) -----------------------------------
    task automatic tsm_bind_p2p_stream(
        input int unsigned tdi_idx = 0,
        input logic [7:0]  stream_id = 8'h02,
        output logic       success
    );
        logic [7:0] payload[$];
        payload = {};
        payload.push_back(stream_id);
        payload.push_back(8'h00); payload.push_back(8'h00); payload.push_back(8'h00);

        tsm_send_request(REQ_BIND_P2P_STREAM, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_BIND_P2P_STREAM);
        if (success) begin
            bound_streams[tdi_idx].push_back(stream_id);
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] BIND_P2P_STREAM SUCCESS: TDI[%0d] stream_id=0x%02h", tdi_idx, stream_id);
        end
    endtask

    //--- 9. UNBIND_P2P_STREAM_REQUEST (0x89) ---------------------------------
    task automatic tsm_unbind_p2p_stream(
        input int unsigned tdi_idx = 0,
        input logic [7:0]  stream_id = 8'h02,
        output logic       success
    );
        logic [7:0] payload[$];
        payload = {};
        payload.push_back(stream_id);
        payload.push_back(8'h00); payload.push_back(8'h00); payload.push_back(8'h00);

        tsm_send_request(REQ_UNBIND_P2P_STREAM, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_UNBIND_P2P_STREAM);
        if (success) begin
            // Remove from bound streams list
            for (int i = 0; i < bound_streams[tdi_idx].size(); i++) begin
                if (bound_streams[tdi_idx][i] == stream_id) begin
                    bound_streams[tdi_idx].delete(i);
                    break;
                end
            end
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] UNBIND_P2P_STREAM SUCCESS: TDI[%0d] stream_id=0x%02h", tdi_idx, stream_id);
        end
    endtask

    //--- 10. SET_MMIO_ATTRIBUTE_REQUEST (0x8A) --------------------------------
    task automatic tsm_set_mmio_attribute(
        input int unsigned tdi_idx = 0,
        input logic [63:0] start_page_addr = 64'h1000_0000,
        input logic [31:0] num_pages = 32'h10,
        input logic         is_non_tee_mem = 1'b0,
        input logic [1:0]   range_id = 2'b00,
        output logic        success
    );
        logic [7:0] payload[$];
        payload = {};

        // start_page_addr: 8 bytes LE
        for (int i = 0; i < 8; i++)
            payload.push_back(start_page_addr[i*8 +: 8]);
        // num_pages: 4 bytes LE
        for (int i = 0; i < 4; i++)
            payload.push_back(num_pages[i*8 +: 8]);
        // attributes byte: {5'b0, is_non_tee_mem, range_id}
        payload.push_back({5'b0, is_non_tee_mem, range_id});

        tsm_send_request(REQ_SET_MMIO_ATTRIBUTE, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_SET_MMIO_ATTRIBUTE);
        if (success) begin
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] SET_MMIO_ATTRIBUTE SUCCESS: TDI[%0d]", tdi_idx);
        end
    endtask

    //--- 11. VDM_REQUEST (0x8B) -----------------------------------------------
    task automatic tsm_vdm_request(
        input int unsigned  tdi_idx = 0,
        input logic [7:0]   vdm_data[$],
        output logic         success
    );
        tsm_send_request(REQ_VDM, tdi_track[tdi_idx].iface_id, vdm_data);

        success = !last_response.is_error && (last_response.rsp_code == RSP_VDM);
        if (success) begin
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] VDM_REQUEST SUCCESS: TDI[%0d]", tdi_idx);
        end
    endtask

    //--- 12. SET_TDISP_CONFIG_REQUEST (0x8C) ----------------------------------
    task automatic tsm_set_tdisp_config(
        input int unsigned  tdi_idx = 0,
        input logic [31:0]  config_data,
        output logic        success
    );
        logic [7:0] payload[$];
        payload = {};
        for (int i = 0; i < 4; i++)
            payload.push_back(config_data[i*8 +: 8]);

        tsm_send_request(REQ_SET_TDISP_CONFIG, tdi_track[tdi_idx].iface_id, payload);

        success = !last_response.is_error && (last_response.rsp_code == RSP_SET_TDISP_CONFIG);
        if (success) begin
            tdi_track[tdi_idx].ops_count++;
            $display("[TSM] SET_TDISP_CONFIG SUCCESS: TDI[%0d]", tdi_idx);
        end
    endtask

    //==========================================================================
    // High-Level Composite Sequences
    //==========================================================================

    //--- Full TDI Lifecycle: VERSION u2192 CAPS u2192 LOCK u2192 STATE u2192 REPORT u2192 START u2192 STATE u2192 STOP
    task automatic tsm_run_full_lifecycle(
        input int unsigned tdi_idx = 0,
        output logic       all_passed
    );
        logic success;
        logic [7:0] ver_count;
        logic [15:0] ver_entries[$];
        tdisp_state_e reported_state;

        all_passed = 1'b1;
        $display("[TSM] u2550u2550u2550 Full Lifecycle: TDI[%0d] u2550u2550u2550", tdi_idx);

        // 1. GET_TDISP_VERSION
        tsm_get_tdisp_version(tdi_idx, ver_count, ver_entries);
        if (last_response.is_error) begin
            $error("[TSM] LIFECYCLE FAIL: GET_TDISP_VERSION error");
            all_passed = 1'b0;
            return;
        end

        // 2. GET_TDISP_CAPABILITIES
        begin
            logic xt; logic [127:0] msgs; logic [15:0] flags;
            logic [7:0] aw, nt, na;
            tsm_get_tdisp_capabilities(tdi_idx, xt, msgs, flags, aw, nt, na);
            if (last_response.is_error) begin
                $error("[TSM] LIFECYCLE FAIL: GET_TDISP_CAPABILITIES error");
                all_passed = 1'b0;
                return;
            end
        end

        // 3. LOCK_INTERFACE
        tsm_lock_interface(tdi_idx, '0, 8'h01, 64'h0, 64'hFFFF_FFFF_FFFF_F000, success);
        if (!success) begin
            $error("[TSM] LIFECYCLE FAIL: LOCK_INTERFACE");
            all_passed = 1'b0;
            return;
        end

        // 4. GET_DEVICE_INTERFACE_STATE u2192 CONFIG_LOCKED
        tsm_get_interface_state(tdi_idx, reported_state, success);
        if (!success || reported_state != TDI_CONFIG_LOCKED) begin
            $error("[TSM] LIFECYCLE FAIL: expected CONFIG_LOCKED, got %s", reported_state.name());
            all_passed = 1'b0;
        end

        // 5. GET_DEVICE_INTERFACE_REPORT
        begin
            logic [7:0] report[$];
            tsm_get_interface_report(tdi_idx, report, success);
        end

        // 6. START_INTERFACE
        tsm_start_interface(tdi_idx, tsm_gen_nonce(tdi_idx), success);
        if (!success) begin
            $error("[TSM] LIFECYCLE FAIL: START_INTERFACE");
            all_passed = 1'b0;
            return;
        end

        // 7. GET_DEVICE_INTERFACE_STATE u2192 RUN
        tsm_get_interface_state(tdi_idx, reported_state, success);
        if (!success || reported_state != TDI_RUN) begin
            $error("[TSM] LIFECYCLE FAIL: expected RUN, got %s", reported_state.name());
            all_passed = 1'b0;
        end

        // 8. STOP_INTERFACE
        tsm_stop_interface(tdi_idx, success);
        if (!success) begin
            $error("[TSM] LIFECYCLE FAIL: STOP_INTERFACE");
            all_passed = 1'b0;
        end

        $display("[TSM] u2550u2550u2550 Lifecycle TDI[%0d]: %s u2550u2550u2550",
                 tdi_idx, all_passed ? "ALL PASSED" : "FAILED");
    endtask

    //--- Multi-TDI lifecycle: run independent lifecycles on multiple TDIs
    task automatic tsm_run_multi_tdi_lifecycle(
        input int unsigned start_tdi = 0,
        input int unsigned num_tdis  = NUM_TDI,
        output logic       all_passed
    );
        all_passed = 1'b1;
        for (int t = start_tdi; t < start_tdi + num_tdis && t < NUM_TDI; t++) begin
            logic pass;
            tsm_run_full_lifecycle(t, pass);
            if (!pass) all_passed = 1'b0;
        end
    endtask

    //--- Lock-and-start without intermediate queries
    task automatic tsm_lock_and_start(
        input int unsigned             tdi_idx = 0,
        input tdisp_lock_flags_s       flags = '0,
        input logic [NONCE_WIDTH-1:0]  nonce = '0,
        output logic                   success
    );
        logic lock_ok, start_ok;

        tsm_lock_interface(tdi_idx, flags, 8'h01, 64'h0, 64'hFFFF_FFFF_FFFF_F000, lock_ok);
        if (!lock_ok) begin
            success = 1'b0;
            return;
        end

        tsm_start_interface(tdi_idx, nonce, start_ok);
        success = start_ok;
    endtask

    //--- Quick state check
    task automatic tsm_check_state(
        input int unsigned   tdi_idx = 0,
        input tdisp_state_e  expected,
        output logic         match
    );
        tdisp_state_e reported;
        logic         success;
        tsm_get_interface_state(tdi_idx, reported, success);
        match = success && (reported == expected);
        if (!match) begin
            $display("[TSM] STATE CHECK TDI[%0d]: expected=%s, got=%s (%s)",
                     tdi_idx, expected.name(), reported.name(),
                     success ? "valid" : "error");
        end
    endtask

    //==========================================================================
    // TSM Agent Status Report
    //==========================================================================
    task automatic tsm_report;
        $display("");
        $display("u2554u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2557");
        $display("u2551          TSM AGENT REPORT                  u2551");
        $display("u2560u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2563");
        $display("u2551 Requests Sent     : %0d", total_requests_sent);
        $display("u2551 Responses Received: %0d", total_responses_recv);
        $display("u2551 Errors Seen       : %0d", total_errors_seen);
        $display("u2560u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2563");
        for (int i = 0; i < NUM_TDI; i++) begin
            $display("u2551 TDI[%0d]: state=%-16s ops=%0d locked=%0b started=%0b",
                     i, tdi_track[i].state.name(),
                     tdi_track[i].ops_count,
                     tdi_track[i].locked,
                     tdi_track[i].started);
            if (bound_streams[i].size() > 0) begin
                $display("u2551        bound_streams=%0d", bound_streams[i].size());
            end
        end
        $display("u2560u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2563");
        for (int s = 0; s < 4; s++) begin
            if (spdm_sessions[s].active) begin
                $display("u2551 SPDM Session[%0d]: id=0x%08h secured=%0b",
                         s, spdm_sessions[s].session_id, spdm_sessions[s].secured);
            end
        end
        $display("u255au2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u2550u255d");
        $display("");
    endtask

    //==========================================================================
    // Response Polling (non-blocking check for pending response)
    //==========================================================================
    task automatic tsm_poll_response(
        output logic rsp_available
    );
        rsp_available = tsm_rx_tvalid;
    endtask

    //==========================================================================
    // Error Code Lookup
    //==========================================================================
    function automatic string tsm_error_name(
        input logic [15:0] error_code
    );
        case (error_code)
            16'h0000: return "RESERVED";
            16'h0001: return "INVALID_REQUEST";
            16'h0003: return "BUSY";
            16'h0004: return "INVALID_INTERFACE_STATE";
            16'h0005: return "UNSPECIFIED";
            16'h0007: return "UNSUPPORTED_REQUEST";
            16'h0041: return "VERSION_MISMATCH";
            16'h00FF: return "VENDOR_SPECIFIC_ERROR";
            16'h0101: return "INVALID_INTERFACE";
            16'h0102: return "INVALID_NONCE";
            16'h0103: return "INSUFFICIENT_ENTROPY";
            16'h0104: return "INVALID_DEVICE_CONFIGURATION";
            default:  return "UNKNOWN";
        endcase
    endfunction

    //==========================================================================
    // Version with Bad Version (for negative testing)
    //==========================================================================
    task automatic tsm_send_bad_version_request(
        input int unsigned  tdi_idx = 0,
        input logic [7:0]   bad_version = 8'h20,
        output logic        got_version_error
    );
        logic [7:0] msg_bytes[$];
        logic [7:0] rsp_bytes[$];
        int unsigned rsp_len;

        msg_bytes = {};
        msg_bytes.push_back(bad_version);            // Bad version
        msg_bytes.push_back(REQ_GET_TDISP_VERSION);
        msg_bytes.push_back(8'h00);
        msg_bytes.push_back(8'h00);
        for (int i = 0; i < 12; i++)
            msg_bytes.push_back(tdi_track[tdi_idx].iface_id[i*8 +: 8]);

        tsm_send_raw_bytes(msg_bytes);
        tsm_recv_raw_bytes(rsp_bytes, rsp_len);
        tsm_parse_response(rsp_bytes);

        got_version_error = last_response.is_error &&
                            (last_response.error_code == ERR_VERSION_MISMATCH);
    endtask

    //==========================================================================
    // Unsupported Request (for negative testing)
    //==========================================================================
    task automatic tsm_send_unsupported_request(
        input int unsigned tdi_idx = 0,
        input logic [7:0]  bad_msg_code = 8'hFF,
        output logic       got_unsupported_error
    );
        logic [7:0] payload[$];
        payload = {};
        tsm_send_request(bad_msg_code, tdi_track[tdi_idx].iface_id, payload);
        got_unsupported_error = last_response.is_error &&
                                (last_response.error_code == ERR_UNSUPPORTED_REQUEST);
    endtask

endmodule : tdisp_tsm_agent
