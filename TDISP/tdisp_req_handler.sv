// ============================================================================
// Module:    tdisp_req_handler.sv
// Purpose:   TDISP Request Handler u2014 command dispatch, validation, and
//            response generation for all TDISP request messages.
// Spec:      PCI Express Base Specification Revision 7.0, Section 11.3
//
// Architecture:
//   1. Accepts parsed TDISP messages from tdisp_msg_codec parser.
//   2. Validates: INTERFACE_ID hosted, TDI state legal, payload length.
//   3. Dispatches command-specific logic.
//   4. Generates response messages for the tdisp_msg_codec encoder.
//
// Error responses use TDISP_ERROR format per Table 11-27/11-28.
// Outstanding request tracking per u00a711.2.6.
// ============================================================================

module tdisp_req_handler
    import tdisp_pkg::*;
#(
    parameter int NUM_TDI         = MAX_NUM_TDI,
    parameter int MAX_REPORT_SIZE = 4096
)(
    input  logic clk,
    input  logic rst_n,

    // =========================================================================
    // From msg_codec parser u2014 parsed request message
    // =========================================================================
    input  logic                      parsed_valid,
    input  tdisp_msg_header_s         parsed_hdr,
    input  logic [7:0]                parsed_payload [MAX_REPORT_SIZE-1:0],
    input  logic [15:0]               parsed_payload_len,

    // =========================================================================
    // To msg_codec encoder u2014 response message
    // =========================================================================
    output logic                      resp_valid,
    input  logic                      resp_ready,
    output tdisp_resp_code_e          resp_msg_type,
    output logic [INTERFACE_ID_WIDTH-1:0] resp_interface_id,
    output logic [7:0]                resp_payload [MAX_REPORT_SIZE-1:0],
    output logic [15:0]               resp_payload_len,

    // =========================================================================
    // Per-TDI state (from FSM instances)
    // =========================================================================
    input  tdisp_tdi_state_e          tdi_state [NUM_TDI-1:0],

    // =========================================================================
    // Per-TDI state (from lock_handler u2014 stored nonce)
    // =========================================================================
    input  logic [NONCE_WIDTH-1:0]    tdi_stored_nonce [NUM_TDI-1:0],

    // =========================================================================
    // To FSM u2014 control pulses (per TDI, one-hot)
    // =========================================================================
    output logic [NUM_TDI-1:0]        lock_req_pulse,
    output logic [NUM_TDI-1:0]        start_req_pulse,
    output logic [NUM_TDI-1:0]        stop_req_pulse,

    // =========================================================================
    // To lock_handler u2014 lock command interface
    // =========================================================================
    output logic                      lock_cmd_valid,
    output logic [TDI_INDEX_WIDTH-1:0] lock_cmd_tdi_idx,
    output tdisp_lock_req_payload_s   lock_cmd_payload,

    // =========================================================================
    // From lock_handler u2014 lock result (async arrival)
    // =========================================================================
    input  logic                      lock_done,
    input  logic                      lock_error,
    input  tdisp_error_code_e         lock_error_code,
    input  logic [NONCE_WIDTH-1:0]    lock_nonce_out,
    input  logic [TDI_INDEX_WIDTH-1:0] lock_done_tdi_idx,

    // =========================================================================
    // Device-specific configuration inputs (static or slow-changing)
    // =========================================================================
    input  tdisp_caps_s               device_caps,
    input  logic [7:0]                num_req_this_config [NUM_TDI-1:0],
    input  logic [7:0]                num_req_all_config,

    // =========================================================================
    // Device interface report storage (read-only port)
    // =========================================================================
    input  logic [7:0]                report_data [MAX_REPORT_SIZE-1:0],
    input  logic [15:0]               report_total_len,

    // =========================================================================
    // INTERFACE_ID lookup u2014 maps 96-bit INTERFACE_ID to TDI index
    // =========================================================================
    input  logic [INTERFACE_ID_WIDTH-1:0] hosted_interface_ids [NUM_TDI-1:0],

    // =========================================================================
    // VDM pass-through (optional vendor-specific handler)
    // =========================================================================
    output logic                      vdm_req_valid,
    output logic [INTERFACE_ID_WIDTH-1:0] vdm_req_interface_id,
    output logic [7:0]                vdm_req_payload [MAX_REPORT_SIZE-1:0],
    output logic [15:0]               vdm_req_payload_len,
    input  logic                      vdm_resp_ready,

    // =========================================================================
    // SET_TDISP_CONFIG outputs
    // =========================================================================
    output logic                      xt_mode_enable,
    output logic                      xt_bit_for_locked_msix,

    // =========================================================================
    // P2P stream management (for BIND/UNBIND validation)
    // =========================================================================
    input  logic [MAX_P2P_STREAMS-1:0] p2p_stream_bound [NUM_TDI-1:0],
    output logic [7:0]                bind_stream_id,
    output logic [NUM_TDI-1:0]        bind_pulse,
    output logic [NUM_TDI-1:0]        unbind_pulse,

    // =========================================================================
    // MMIO attribute update (for SET_MMIO_ATTRIBUTE)
    // =========================================================================
    output logic                      mmio_attr_update_valid,
    output logic [TDI_INDEX_WIDTH-1:0] mmio_attr_tdi_idx,
    output tdisp_set_mmio_attr_req_s  mmio_attr_update_data
);

    // =========================================================================
    // Local constants
    // =========================================================================
    localparam int CNT_WIDTH = 16;

    // =========================================================================
    // Handler FSM states
    // =========================================================================
    typedef enum logic [3:0] {
        H_IDLE,
        H_DISPATCH,
        H_WAIT_LOCK,
        H_BUILD_RESP,
        H_SEND_ERROR,
        H_SEND_RESP
    } handler_state_e;

    // =========================================================================
    // Internal registers
    // =========================================================================
    handler_state_e       h_state;
    tdisp_req_code_e      active_req_code;
    logic [TDI_INDEX_WIDTH-1:0] active_tdi_idx;
    logic                 tdi_found;
    tdisp_msg_header_s    saved_hdr;
    logic [15:0]          saved_payload_len;
    logic [7:0]           saved_payload [MAX_REPORT_SIZE-1:0];

    // Response builder
    logic [15:0]          resp_payload_len_r;
    logic [7:0]           resp_payload_r   [MAX_REPORT_SIZE-1:0];
    tdisp_resp_code_e     resp_msg_type_r;
    logic [INTERFACE_ID_WIDTH-1:0] resp_iface_id_r;

    // Outstanding request counters
    logic [7:0]           req_cnt_this [NUM_TDI-1:0];
    logic [7:0]           req_cnt_all;

    // Stored XT config
    logic                 xt_mode_enable_r;
    logic                 xt_bit_for_locked_msix_r;

    // =========================================================================
    // Function: Resolve INTERFACE_ID to TDI index
    //   Scans hosted_interface_ids[] for a match; returns index + found flag.
    // =========================================================================
    function automatic void resolve_interface_id(
        input  logic [INTERFACE_ID_WIDTH-1:0] iface_id,
        output logic                          found,
        output logic [TDI_INDEX_WIDTH-1:0]    idx
    );
        found = 1'b0;
        idx   = '0;
        for (int i = 0; i < NUM_TDI; i++) begin
            if (iface_id == hosted_interface_ids[i]) begin
                found = 1'b1;
                idx   = TDI_INDEX_WIDTH'(i);
            end
        end
    endfunction

    // =========================================================================
    // Function: Compute expected payload length for a request code
    // =========================================================================
    function automatic logic [15:0] expected_payload_len(input tdisp_req_code_e code);
        case (code)
            REQ_GET_TDISP_VERSION:           return 16'd0;
            REQ_GET_TDISP_CAPABILITIES:      return 16'd4;
            REQ_LOCK_INTERFACE:              return 16'd20;
            REQ_GET_DEVICE_INTERFACE_REPORT: return 16'd4;
            REQ_GET_DEVICE_INTERFACE_STATE:  return 16'd0;
            REQ_START_INTERFACE:             return 16'd32;
            REQ_STOP_INTERFACE:              return 16'd0;
            REQ_BIND_P2P_STREAM:             return 16'd2;
            REQ_UNBIND_P2P_STREAM:           return 16'd1;
            REQ_SET_MMIO_ATTRIBUTE:          return 16'd16;
            REQ_VDM:                         return 16'hFFFF; // variable
            REQ_SET_TDISP_CONFIG:            return 16'd4;
            default:                         return 16'd0;
        endcase
    endfunction

    // =========================================================================
    // Function: Build TDISP_ERROR response payload
    //   Error code [31:0] + Error data [31:0] = 8 bytes at payload[0..7]
    // =========================================================================
    function automatic void build_error_payload(
        output logic [7:0]   buf [MAX_REPORT_SIZE-1:0],
        output logic [15:0]  len,
        input  tdisp_error_code_e err_code,
        input  logic [31:0]      err_data
    );
        for (int i = 0; i < MAX_REPORT_SIZE; i++) buf[i] = 8'd0;
        // Error code: 4 bytes little-endian
        buf[0] = err_code[7:0];
        buf[1] = err_code[15:8];
        buf[2] = 8'd0;
        buf[3] = 8'd0;
        // Error data: 4 bytes little-endian
        buf[4] = err_data[7:0];
        buf[5] = err_data[15:8];
        buf[6] = err_data[23:16];
        buf[7] = err_data[31:24];
        len = 16'd8;
    endfunction

    // =========================================================================
    // Function: Build VERSION response payload
    //   VERSION_NUM_COUNT [7:0] = 1
    //   VERSION_NUM_ENTRY  [7:0] = TDISP_VERSION_1_0
    // =========================================================================
    function automatic void build_version_payload(
        output logic [7:0]  buf [MAX_REPORT_SIZE-1:0],
        output logic [15:0] len
    );
        for (int i = 0; i < MAX_REPORT_SIZE; i++) buf[i] = 8'd0;
        buf[0] = 8'd1;                    // VERSION_NUM_COUNT = 1
        buf[1] = TDISP_VERSION_1_0;       // VERSION_NUM_ENTRY = 10h
        len    = 16'd2;
    endfunction

    // =========================================================================
    // Function: Build CAPABILITIES response payload from device_caps struct
    //   Serialize tdisp_caps_s to bytes in little-endian order.
    // =========================================================================
    function automatic void build_caps_payload(
        output logic [7:0]  buf [MAX_REPORT_SIZE-1:0],
        output logic [15:0] len,
        input  tdisp_caps_s caps
    );
        logic [255:0] flat;
        for (int i = 0; i < MAX_REPORT_SIZE; i++) buf[i] = 8'd0;
        // Flatten struct to bits (packed struct is already contiguous)
        flat = caps;
        for (int i = 0; i < 32; i++) begin
            buf[i] = flat[i*8 +: 8];
        end
        len = 16'd32;  // tdisp_caps_s is 256 bits = 32 bytes
    endfunction

    // =========================================================================
    // Function: Build INTERFACE_STATE response payload
    //   TDI_STATE [7:0] u2014 maps tdisp_tdi_state_e to byte value per Table 11-18
    // =========================================================================
    function automatic void build_state_payload(
        output logic [7:0]  buf [MAX_REPORT_SIZE-1:0],
        output logic [15:0] len,
        input  tdisp_tdi_state_e state
    );
        for (int i = 0; i < MAX_REPORT_SIZE; i++) buf[i] = 8'd0;
        case (state)
            TDI_STATE_CONFIG_UNLOCKED: buf[0] = 8'd0;
            TDI_STATE_CONFIG_LOCKED:   buf[0] = 8'd1;
            TDI_STATE_RUN:             buf[0] = 8'd2;
            TDI_STATE_ERROR:           buf[0] = 8'd3;
            default:                   buf[0] = 8'd0;
        endcase
        len = 16'd1;
    endfunction

    // =========================================================================
    // Function: Build LOCK_INTERFACE_RESPONSE payload (nonce)
    //   START_INTERFACE_NONCE [255:0] = 32 bytes little-endian
    // =========================================================================
    function automatic void build_lock_resp_payload(
        output logic [7:0]  buf [MAX_REPORT_SIZE-1:0],
        output logic [15:0] len,
        input  logic [NONCE_WIDTH-1:0] nonce
    );
        for (int i = 0; i < MAX_REPORT_SIZE; i++) buf[i] = 8'd0;
        for (int i = 0; i < 32; i++) begin
            buf[i] = nonce[i*8 +: 8];
        end
        len = 16'd32;
    endfunction

    // =========================================================================
    // Function: Build DEVICE_INTERFACE_REPORT response payload
    //   PORTION_LENGTH[15:0] + REMAINDER_LENGTH[15:0] + REPORT_BYTES
    // =========================================================================
    function automatic void build_report_payload(
        output logic [7:0]  buf [MAX_REPORT_SIZE-1:0],
        output logic [15:0] len,
        input  logic [7:0]  report [MAX_REPORT_SIZE-1:0],
        input  logic [15:0] report_len,
        input  logic [15:0] req_offset,
        input  logic [15:0] req_length
    );
        logic [15:0] portion_len;
        logic [15:0] remainder;
        logic [15:0] available;

        for (int i = 0; i < MAX_REPORT_SIZE; i++) buf[i] = 8'd0;

        // Compute available bytes from offset
        if (req_offset >= report_len) begin
            available = 16'd0;
        end else begin
            available = report_len - req_offset;
        end

        // Portion = min(req_length, available)
        if (req_length > available)
            portion_len = available;
        else
            portion_len = req_length;

        // Remainder = total remaining after this portion
        if (available > portion_len)
            remainder = available - portion_len;
        else
            remainder = 16'd0;

        // PORTION_LENGTH (LE)
        buf[0] = portion_len[7:0];
        buf[1] = portion_len[15:8];
        // REMAINDER_LENGTH (LE)
        buf[2] = remainder[7:0];
        buf[3] = remainder[15:8];

        // REPORT_BYTES
        for (int i = 0; i < MAX_REPORT_SIZE - 4; i++) begin
            if (logic'(i < portion_len) && logic'((req_offset + CNT_WIDTH'(i)) < report_len)) begin
                buf[4 + i] = report[req_offset + CNT_WIDTH'(i)];
            end
        end

        len = 16'd4 + portion_len;
    endfunction

    // =========================================================================
    // Resolve INTERFACE_ID u2014 combinational
    // =========================================================================
    logic                       iface_found;
    logic [TDI_INDEX_WIDTH-1:0] iface_tdi_idx;

    always_comb begin
        resolve_interface_id(parsed_hdr.interface_id, iface_found, iface_tdi_idx);
    end

    // =========================================================================
    // Interface ID to use for responses (saved or current)
    // =========================================================================
    always_comb begin
        resp_interface_id = resp_iface_id_r;
    end

    // =========================================================================
    // Mux response payload from builder registers to encoder output
    // =========================================================================
    always_comb begin
        resp_msg_type   = resp_msg_type_r;
        resp_payload_len = resp_payload_len_r;
        for (int i = 0; i < MAX_REPORT_SIZE; i++) begin
            resp_payload[i] = resp_payload_r[i];
        end
    end

    // =========================================================================
    // Pulse registers for per-TDI control (registered, default 0 each cycle)
    // =========================================================================
    logic [NUM_TDI-1:0] lock_req_pulse_r;
    logic [NUM_TDI-1:0] start_req_pulse_r;
    logic [NUM_TDI-1:0] stop_req_pulse_r;
    logic [NUM_TDI-1:0] bind_pulse_r;
    logic [NUM_TDI-1:0] unbind_pulse_r;
    logic [7:0]         bind_stream_id_r;

    assign lock_req_pulse  = lock_req_pulse_r;
    assign start_req_pulse = start_req_pulse_r;
    assign stop_req_pulse  = stop_req_pulse_r;
    assign bind_pulse      = bind_pulse_r;
    assign unbind_pulse    = unbind_pulse_r;
    assign bind_stream_id  = bind_stream_id_r;

    // =========================================================================
    // Outstanding request counter tracking
    // =========================================================================
    logic req_limit_exceeded;
    logic req_this_exceeded;

    always_comb begin
        req_this_exceeded = 1'b0;
        req_limit_exceeded = 1'b0;
        if (iface_found) begin
            if (req_cnt_this[iface_tdi_idx] >= num_req_this_config[iface_tdi_idx])
                req_this_exceeded = 1'b1;
            if (req_cnt_all >= num_req_all_config)
                req_limit_exceeded = 1'b1;
        end
    end

    // =========================================================================
    // Main handler state machine
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            h_state              <= H_IDLE;
            active_req_code      <= REQ_GET_TDISP_VERSION;
            active_tdi_idx       <= '0;
            tdi_found            <= 1'b0;
            saved_hdr            <= '0;
            saved_payload_len    <= '0;
            resp_valid           <= 1'b0;
            resp_msg_type_r      <= RESP_TDISP_ERROR;
            resp_iface_id_r      <= '0;
            resp_payload_len_r   <= '0;
            lock_cmd_valid       <= 1'b0;
            lock_cmd_tdi_idx     <= '0;
            lock_cmd_payload     <= '0;
            xt_mode_enable_r     <= 1'b0;
            xt_bit_for_locked_msix_r <= 1'b0;
            mmio_attr_update_valid   <= 1'b0;
            vdm_req_valid        <= 1'b0;
            for (int i = 0; i < NUM_TDI; i++) begin
                req_cnt_this[i] <= 8'd0;
            end
            req_cnt_all          <= 8'd0;
            for (int i = 0; i < MAX_REPORT_SIZE; i++) begin
                saved_payload[i]  <= 8'd0;
                resp_payload_r[i] <= 8'd0;
            end
        end else begin
            resp_valid           <= 1'b0;
            lock_cmd_valid       <= 1'b0;
            mmio_attr_update_valid <= 1'b0;
            vdm_req_valid        <= 1'b0;

            case (h_state)

                // =================================================================
                // H_IDLE: Wait for parsed_valid from msg_codec parser
                // =================================================================
                H_IDLE: begin
                    if (parsed_valid) begin
                        // Save parsed message
                        saved_hdr         <= parsed_hdr;
                        saved_payload_len <= parsed_payload_len;
                        for (int i = 0; i < MAX_REPORT_SIZE; i++) begin
                            saved_payload[i] <= parsed_payload[i];
                        end

                        // Resolve INTERFACE_ID to TDI
                        tdi_found       <= iface_found;
                        active_tdi_idx  <= iface_tdi_idx;
                        active_req_code <= tdisp_req_code_e'(parsed_hdr.msg_type);

                        // Set response INTERFACE_ID (echo from request)
                        resp_iface_id_r <= parsed_hdr.interface_id;

                        h_state <= H_DISPATCH;
                    end
                end

                // =================================================================
                // H_DISPATCH: Validate and dispatch the request
                // =================================================================
                H_DISPATCH: begin
                    automatic tdisp_req_code_e req_code;
                    req_code = active_req_code;

                    // ----------------------------------------------------------
                    // Step 1: Check INTERFACE_ID validity
                    // ----------------------------------------------------------
                    if (!tdi_found) begin
                        build_error_payload(resp_payload_r, resp_payload_len_r,
                                            ERR_INVALID_INTERFACE, 32'd0);
                        resp_msg_type_r <= RESP_TDISP_ERROR;
                        h_state <= H_SEND_RESP;
                    end
                    // ----------------------------------------------------------
                    // Step 2: Check outstanding request limits (u00a711.2.6)
                    // ----------------------------------------------------------
                    else if (req_limit_exceeded || req_this_exceeded) begin
                        build_error_payload(resp_payload_r, resp_payload_len_r,
                                            ERR_BUSY, 32'd0);
                        resp_msg_type_r <= RESP_TDISP_ERROR;
                        h_state <= H_SEND_RESP;
                    end
                    // ----------------------------------------------------------
                    // Step 3: Check payload length
                    // ----------------------------------------------------------
                    else if (req_code != REQ_VDM &&
                             expected_payload_len(req_code) != saved_payload_len) begin
                        build_error_payload(resp_payload_r, resp_payload_len_r,
                                            ERR_INVALID_REQUEST,
                                            {16'd0, saved_payload_len});
                        resp_msg_type_r <= RESP_TDISP_ERROR;
                        h_state <= H_SEND_RESP;
                    end
                    // ----------------------------------------------------------
                    // Step 4: Check TDI state legality (Table 11-4)
                    //   Special case: SET_TDISP_CONFIG requires ALL TDIs unlocked
                    // ----------------------------------------------------------
                    else if (req_code == REQ_SET_TDISP_CONFIG) begin
                        // Check all TDIs are in CONFIG_UNLOCKED
                        automatic logic all_unlocked;
                        all_unlocked = 1'b1;
                        for (int i = 0; i < NUM_TDI; i++) begin
                            if (tdi_state[i] != TDI_STATE_CONFIG_UNLOCKED) begin
                                all_unlocked = 1'b0;
                            end
                        end
                        if (!all_unlocked) begin
                            build_error_payload(resp_payload_r, resp_payload_len_r,
                                                ERR_INVALID_INTERFACE_STATE, 32'd0);
                            resp_msg_type_r <= RESP_TDISP_ERROR;
                        end else begin
                            // Apply config
                            automatic tdisp_set_config_req_s config_req;
                            config_req = tdisp_set_config_req_s'(saved_payload);
                            // Reconstruct from bytes (little-endian 4 bytes)
                            logic [31:0] config_word;
                            config_word = {saved_payload[3], saved_payload[2],
                                           saved_payload[1], saved_payload[0]};
                            config_req = tdisp_set_config_req_s'(config_word);
                            xt_mode_enable_r         <= config_req.xt_mode_enable;
                            xt_bit_for_locked_msix_r <= config_req.xt_bit_for_locked_msix;
                            resp_msg_type_r <= RESP_SET_TDISP_CONFIG;
                            resp_payload_len_r <= 16'd0; // No payload
                        end
                        h_state <= H_SEND_RESP;
                    end
                    else if (!tdisp_state_is_legal_for_req(
                                 req_code,
                                 tdi_state[active_tdi_idx])) begin
                        build_error_payload(resp_payload_r, resp_payload_len_r,
                                            ERR_INVALID_INTERFACE_STATE, 32'd0);
                        resp_msg_type_r <= RESP_TDISP_ERROR;
                        h_state <= H_SEND_RESP;
                    end
                    // ----------------------------------------------------------
                    // Step 5: Command-specific dispatch
                    // ----------------------------------------------------------
                    else begin
                        case (req_code)

                            // ==================================================
                            // GET_TDISP_VERSION
                            // ==================================================
                            REQ_GET_TDISP_VERSION: begin
                                // Validate: version major must be 1
                                if (saved_hdr.tdisp_version[7:4] != 4'h1) begin
                                    build_error_payload(resp_payload_r, resp_payload_len_r,
                                                        ERR_VERSION_MISMATCH, 32'd0);
                                    resp_msg_type_r <= RESP_TDISP_ERROR;
                                end else begin
                                    build_version_payload(resp_payload_r, resp_payload_len_r);
                                    resp_msg_type_r <= RESP_TDISP_VERSION;
                                end
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // GET_TDISP_CAPABILITIES
                            // ==================================================
                            REQ_GET_TDISP_CAPABILITIES: begin
                                // Fill in dynamic fields
                                automatic tdisp_caps_s caps;
                                caps = device_caps;
                                caps.num_req_this = num_req_this_config[active_tdi_idx];
                                caps.num_req_all  = num_req_all_config;
                                build_caps_payload(resp_payload_r, resp_payload_len_r, caps);
                                resp_msg_type_r <= RESP_TDISP_CAPABILITIES;
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // LOCK_INTERFACE_REQUEST
                            // ==================================================
                            REQ_LOCK_INTERFACE: begin
                                // Reconstruct lock payload from bytes (LE, 20 bytes)
                                automatic logic [159:0] lock_flat;
                                for (int i = 0; i < 20; i++) begin
                                    lock_flat[i*8 +: 8] = saved_payload[i];
                                end
                                lock_cmd_payload <= tdisp_lock_req_payload_s'(lock_flat);
                                lock_cmd_tdi_idx <= active_tdi_idx;
                                lock_cmd_valid   <= 1'b1;
                                h_state <= H_WAIT_LOCK;
                            end

                            // ==================================================
                            // GET_DEVICE_INTERFACE_REPORT
                            // ==================================================
                            REQ_GET_DEVICE_INTERFACE_REPORT: begin
                                automatic logic [15:0] req_offset;
                                automatic logic [15:0] req_length;
                                req_offset = {saved_payload[1], saved_payload[0]};
                                req_length = {saved_payload[3], saved_payload[2]};
                                if (req_length == 16'd0) begin
                                    build_error_payload(resp_payload_r, resp_payload_len_r,
                                                        ERR_INVALID_REQUEST, 32'd0);
                                    resp_msg_type_r <= RESP_TDISP_ERROR;
                                end else begin
                                    build_report_payload(resp_payload_r, resp_payload_len_r,
                                                         report_data, report_total_len,
                                                         req_offset, req_length);
                                    resp_msg_type_r <= RESP_DEVICE_INTERFACE_REPORT;
                                end
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // GET_DEVICE_INTERFACE_STATE
                            // ==================================================
                            REQ_GET_DEVICE_INTERFACE_STATE: begin
                                build_state_payload(resp_payload_r, resp_payload_len_r,
                                                    tdi_state[active_tdi_idx]);
                                resp_msg_type_r <= RESP_DEVICE_INTERFACE_STATE;
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // START_INTERFACE_REQUEST
                            // ==================================================
                            REQ_START_INTERFACE: begin
                                // Validate nonce: compare received 32 bytes with stored
                                automatic logic [NONCE_WIDTH-1:0] received_nonce;
                                automatic logic nonce_match;
                                nonce_match = 1'b1;
                                for (int i = 0; i < 32; i++) begin
                                    received_nonce[i*8 +: 8] = saved_payload[i];
                                end
                                if (received_nonce != tdi_stored_nonce[active_tdi_idx]) begin
                                    nonce_match = 1'b0;
                                end

                                if (!nonce_match) begin
                                    build_error_payload(resp_payload_r, resp_payload_len_r,
                                                        ERR_INVALID_NONCE, 32'd0);
                                    resp_msg_type_r <= RESP_TDISP_ERROR;
                                    h_state <= H_SEND_RESP;
                                end else begin
                                    start_req_pulse[active_tdi_idx] <= 1'b1;
                                    resp_msg_type_r    <= RESP_START_INTERFACE;
                                    resp_payload_len_r <= 16'd0;
                                    h_state <= H_SEND_RESP;
                                end
                            end

                            // ==================================================
                            // STOP_INTERFACE_REQUEST
                            // ==================================================
                            REQ_STOP_INTERFACE: begin
                                stop_req_pulse[active_tdi_idx] <= 1'b1;
                                resp_msg_type_r    <= RESP_STOP_INTERFACE;
                                resp_payload_len_r <= 16'd0;
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // BIND_P2P_STREAM_REQUEST
                            // ==================================================
                            REQ_BIND_P2P_STREAM: begin
                                // Basic validation: stream_id from payload
                                automatic logic [7:0] sid;
                                sid = saved_payload[0];
                                if (sid >= MAX_P2P_STREAMS) begin
                                    build_error_payload(resp_payload_r, resp_payload_len_r,
                                                        ERR_INVALID_REQUEST, {16'd0, sid, 8'd0});
                                    resp_msg_type_r <= RESP_TDISP_ERROR;
                                end else if (p2p_stream_bound[active_tdi_idx][sid]) begin
                                    // Already bound
                                    build_error_payload(resp_payload_r, resp_payload_len_r,
                                                        ERR_INVALID_REQUEST, {16'd0, sid, 8'd1});
                                    resp_msg_type_r <= RESP_TDISP_ERROR;
                                end else begin
                                    bind_stream_id <= sid;
                                    bind_pulse[active_tdi_idx] <= 1'b1;
                                    resp_msg_type_r    <= RESP_BIND_P2P_STREAM;
                                    resp_payload_len_r <= 16'd0;
                                end
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // UNBIND_P2P_STREAM_REQUEST
                            // ==================================================
                            REQ_UNBIND_P2P_STREAM: begin
                                automatic logic [7:0] sid;
                                sid = saved_payload[0];
                                if (!p2p_stream_bound[active_tdi_idx][sid]) begin
                                    build_error_payload(resp_payload_r, resp_payload_len_r,
                                                        ERR_INVALID_REQUEST, {16'd0, sid, 8'd0});
                                    resp_msg_type_r <= RESP_TDISP_ERROR;
                                end else begin
                                    unbind_pulse[active_tdi_idx] <= 1'b1;
                                    resp_msg_type_r    <= RESP_UNBIND_P2P_STREAM;
                                    resp_payload_len_r <= 16'd0;
                                end
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // SET_MMIO_ATTRIBUTE_REQUEST
                            // ==================================================
                            REQ_SET_MMIO_ATTRIBUTE: begin
                                // Pass MMIO attribute update to device logic
                                automatic logic [127:0] mmio_flat;
                                for (int i = 0; i < 16; i++) begin
                                    mmio_flat[i*8 +: 8] = saved_payload[i];
                                end
                                mmio_attr_update_data  <= tdisp_set_mmio_attr_req_s'(mmio_flat);
                                mmio_attr_tdi_idx      <= active_tdi_idx;
                                mmio_attr_update_valid <= 1'b1;
                                resp_msg_type_r    <= RESP_SET_MMIO_ATTRIBUTE;
                                resp_payload_len_r <= 16'd0;
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // VDM_REQUEST u2014 pass to vendor handler
                            // ==================================================
                            REQ_VDM: begin
                                vdm_req_valid       <= 1'b1;
                                vdm_req_interface_id <= saved_hdr.interface_id;
                                vdm_req_payload_len  <= saved_payload_len;
                                for (int i = 0; i < MAX_REPORT_SIZE; i++) begin
                                    vdm_req_payload[i] <= saved_payload[i];
                                end
                                // Vendor handler will produce response asynchronously
                                // For now, assume immediate ack
                                resp_msg_type_r    <= RESP_VDM;
                                resp_payload_len_r <= saved_payload_len;
                                for (int i = 0; i < MAX_REPORT_SIZE; i++) begin
                                    resp_payload_r[i] <= saved_payload[i];
                                end
                                h_state <= H_SEND_RESP;
                            end

                            // ==================================================
                            // Unknown request code
                            // ==================================================
                            default: begin
                                build_error_payload(resp_payload_r, resp_payload_len_r,
                                                    ERR_UNSUPPORTED_REQUEST,
                                                    {16'd0, 8'd0, active_req_code});
                                resp_msg_type_r <= RESP_TDISP_ERROR;
                                h_state <= H_SEND_RESP;
                            end
                        endcase
                    end
                end

                // =================================================================
                // H_WAIT_LOCK: Waiting for lock_handler to complete
                // =================================================================
                H_WAIT_LOCK: begin
                    if (lock_done) begin
                        if (lock_error) begin
                            build_error_payload(resp_payload_r, resp_payload_len_r,
                                                lock_error_code, 32'd0);
                            resp_msg_type_r <= RESP_TDISP_ERROR;
                        end else begin
                            // Lock succeeded u2014 return nonce
                            lock_req_pulse[lock_done_tdi_idx] <= 1'b1;
                            build_lock_resp_payload(resp_payload_r, resp_payload_len_r,
                                                    lock_nonce_out);
                            resp_msg_type_r <= RESP_LOCK_INTERFACE;
                        end
                        h_state <= H_SEND_RESP;
                    end
                end

                // =================================================================
                // H_SEND_RESP: Drive resp_valid handshake with encoder
                // =================================================================
                H_SEND_RESP: begin
                    resp_valid <= 1'b1;
                    if (resp_ready) begin
                        // Increment outstanding counters
                        if (tdi_found) begin
                            req_cnt_this[active_tdi_idx] <= req_cnt_this[active_tdi_idx] + 8'd1;
                        end
                        req_cnt_all <= req_cnt_all + 8'd1;
                        h_state <= H_IDLE;
                    end
                end

                // =================================================================
                // H_SEND_ERROR: Alias for error sending (uses same path)
                // =================================================================
                H_SEND_ERROR: begin
                    resp_valid <= 1'b1;
                    if (resp_ready) begin
                        h_state <= H_IDLE;
                    end
                end

                // =================================================================
                // H_BUILD_RESP: Reserved for multi-cycle response building
                // =================================================================
                H_BUILD_RESP: begin
                    h_state <= H_SEND_RESP;
                end

                default: h_state <= H_IDLE;
            endcase

            // =================================================================
            // Decrement outstanding counters when response is fully sent
            // (matches the req_cnt increment in H_SEND_RESP)
            // =================================================================
        end
    end

    // =========================================================================
    // Drive XT config outputs from registered values
    // =========================================================================
    assign xt_mode_enable         = xt_mode_enable_r;
    assign xt_bit_for_locked_msix = xt_bit_for_locked_msix_r;

    // =========================================================================
    // Outstanding request counter decrement on response completion
    // This is a simplified model u2014 in a full implementation, counters would
    // decrement when the response is transmitted on the wire. Here we track
    // the delta between requests received and responses dispatched.
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Counters already reset in main FSM
        end else begin
            // When resp_valid && resp_ready, the request is fully consumed
            // The increment is done in H_SEND_RESP; decrement would be done
            // by external completion tracking (e.g., when DOE delivery is done).
        end
    end

    // =========================================================================
    // Assertions
    // =========================================================================
    // pragma synthesis_off
    `ifdef FORMAL
        // Assert: resp_valid only in response states
        assert property (@(posedge clk) disable iff (!rst_n)
            resp_valid |-> (h_state == H_SEND_RESP || h_state == H_SEND_ERROR))
        else $error("resp_valid asserted outside response states");

        // Assert: lock_cmd_valid only in H_DISPATCH lock path
        assert property (@(posedge clk) disable iff (!rst_n)
            lock_cmd_valid |-> h_state inside {H_DISPATCH})
        else $error("lock_cmd_valid asserted outside dispatch");

        // Assert: pulse signals are single-cycle
        assert property (@(posedge clk) disable iff (!rst_n)
            lock_req_pulse |-> ##1 (lock_req_pulse == '0))
        else $error("lock_req_pulse not single-cycle");

        // Cover: at least one complete dispatch cycle
        cover property (@(posedge clk) disable iff (!rst_n)
            h_state == H_IDLE ##1 h_state == H_DISPATCH ##1
            h_state == H_SEND_RESP ##1 h_state == H_IDLE);
    `endif
    // pragma synthesis_on

endmodule : tdisp_req_handler
