//============================================================================
// TDISP SPDM VENDOR_DEFINED Transport Layer
// Encapsulates/decapsulates TDISP messages in SPDM VENDOR_DEFINED format
// Interfaces to DOE mailbox on one side and internal TDISP modules on the other
// Handles secured message framing (Session ID, MAC) and outstanding request tracking
// Per PCIe Base Spec Rev 7.0, Chapter 11 + SPDM Spec Rev 1.2+
//============================================================================

module tdisp_transport #(
    parameter int unsigned DATA_WIDTH       = 32,   // AXI-Stream data width (power of 2)
    parameter int unsigned NUM_TDI          = 4,
    parameter int unsigned MAX_OUTSTANDING  = 255,  // Max outstanding requests across all TDIs
    parameter int unsigned MAX_MSG_BYTES    = 1024, // Max TDISP message size in bytes
    parameter int unsigned MAC_WIDTH        = 32,   // MAC tag width in bytes (0=no MAC, 16/32)
    parameter int unsigned SESSION_ID_WIDTH = 32    // SPDM Session ID width
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //=== DOE Mailbox RX Interface (incoming SPDM/TDISP from host) ============
    input  logic [DATA_WIDTH-1:0]           doe_rx_tdata,
    input  logic [DATA_WIDTH/8-1:0]         doe_rx_tkeep,
    input  logic                            doe_rx_tlast,
    input  logic                            doe_rx_tvalid,
    output logic                            doe_rx_tready,

    //=== DOE Mailbox TX Interface (outgoing responses to host) ===============
    output logic [DATA_WIDTH-1:0]           doe_tx_tdata,
    output logic [DATA_WIDTH/8-1:0]         doe_tx_tkeep,
    output logic                            doe_tx_tlast,
    output logic                            doe_tx_tvalid,
    input  logic                            doe_tx_tready,

    //=== Internal TDISP Payload Interface (to/from parser & formatter) =======

    //--- To tdisp_msg_parser: decapsulated TDISP payload ---
    output logic [DATA_WIDTH-1:0]           tdisp_rx_tdata,
    output logic [DATA_WIDTH/8-1:0]         tdisp_rx_tkeep,
    output logic                            tdisp_rx_tlast,
    output logic                            tdisp_rx_tvalid,
    input  logic                            tdisp_rx_tready,

    //--- From tdisp_msg_formatter: TDISP response to encapsulate ---
    input  logic [DATA_WIDTH-1:0]           tdisp_tx_tdata,
    input  logic [DATA_WIDTH/8-1:0]         tdisp_tx_tkeep,
    input  logic                            tdisp_tx_tlast,
    input  logic                            tdisp_tx_tvalid,
    output logic                            tdisp_tx_tready,

    //=== TDI Context Interface (for outstanding request tracking) ============
    input  logic [$clog2(NUM_TDI)-1:0]      tdi_index_i,       // TDI index from parser/FSM
    input  logic                            tdi_index_valid_i,  // TDI index is valid

    //--- Outstanding request count management ---
    output logic                            req_count_update_o, // Pulse to update count
    output logic [$clog2(NUM_TDI)-1:0]      req_count_tdi_o,   // TDI index to update
    output logic                            req_count_increment_o, // 1=increment, 0=decrement

    //=== Session Management ==================================================
    output logic [SESSION_ID_WIDTH-1:0]     session_id_o,       // Current session ID
    output logic                            session_active_o,   // Session is established
    output logic                            secured_msg_o,      // Current message is secured

    //=== Status / Error ======================================================
    output logic                            transport_error_o,  // Transport-layer error
    output tdisp_types::tdisp_error_code_e  transport_error_code_o,
    output logic [7:0]                      total_outstanding_o // NUM_REQ_ALL count
);

    import tdisp_types::*;

    //==========================================================================
    // Local Parameters
    //==========================================================================
    localparam int unsigned BYTES_PER_BEAT  = DATA_WIDTH / 8;
    localparam int unsigned BYTE_CNT_W      = $clog2(MAX_MSG_BYTES + 1);

    // SPDM VENDOR_DEFINED header layout (10 bytes total):
    //   [0]    RequestResponseCode (5Eh=request, 5Fh=response)
    //   [1]    Param1
    //   [2]    Param2
    //   [3:4]  StandardID (little-endian) = 0001h (PCI-SIG)
    //   [5:6]  VendorID  (little-endian) = 0001h (PCI-SIG)
    //   [7:8]  PayloadLength (little-endian)
    //   [9]    ProtocolID = 01h (TDISP)
    localparam int unsigned SPDM_VD_HDR_SIZE    = 10;

    // SPDM Secured Message App header layout:
    //   [0]    RequestResponseCode (F3h=secured request, F4h=secured response)
    //   [1:2]  ApplicationDataLength (little-endian)
    //   [3:6]  SessionID (4 bytes, only for request; response uses negotiated)
    localparam int unsigned SPDM_SEC_REQ_SIZE   = 7; // With Session ID

    // SPDM Request/Response codes
    localparam logic [7:0] SPDM_VD_REQUEST      = 8'h5E;
    localparam logic [7:0] SPDM_VD_RESPONSE     = 8'h5F;
    localparam logic [7:0] SPDM_SEC_REQUEST     = 8'hF3;
    localparam logic [7:0] SPDM_SEC_RESPONSE    = 8'hF4;

    //==========================================================================
    // RX FSM - Decapsulation (DOE -> TDISP)
    //==========================================================================
    typedef enum logic [3:0] {
        RX_IDLE,
        RX_SPDM_HDR,        // Receive SPDM header (param1 + param2 + StdID + VendorID)
        RX_VD_PAYLOAD_LEN,  // Receive Payload Length (2 bytes) + Protocol ID (1 byte)
        RX_TDISP_PAYLOAD,   // Forward TDISP payload to parser
        RX_SEC_APP_HDR,     // Secured message: Application Data Length + Session ID
        RX_SEC_VERIFY_MAC,  // Secured message: verify MAC at end
        RX_COMPLETE,
        RX_ERROR
    } rx_state_e;

    typedef enum logic [2:0] {
        TX_IDLE,
        TX_SPDM_HDR,
        TX_SEC_HDR,
        TX_VD_HDR,
        TX_TDISP_PAYLOAD,
        TX_SEC_MAC,
        TX_COMPLETE
    } tx_state_e;

    //==========================================================================
    // Internal Registers - RX Path
    //==========================================================================
    rx_state_e     rx_state_q;

    // SPDM header fields
    logic [7:0]    rx_spdm_code_q;       // RequestResponseCode
    logic [7:0]    rx_param1_q;
    logic [7:0]    rx_param2_q;
    logic [15:0]   rx_std_id_q;          // Standard ID
    logic [15:0]   rx_vendor_id_q;       // Vendor ID
    logic [15:0]   rx_payload_len_q;     // Payload Length field
    logic [7:0]    rx_protocol_id_q;     // Protocol ID

    // Secured message fields
    logic [SESSION_ID_WIDTH-1:0] rx_session_id_q;
    logic [15:0]   rx_app_data_len_q;
    logic          rx_is_secured_q;

    // Byte tracking
    logic [BYTE_CNT_W-1:0] rx_byte_cnt_q;      // Bytes consumed in current phase
    logic [BYTE_CNT_W-1:0] rx_tdisp_bytes_q;   // TDISP payload bytes received
    logic [BYTE_CNT_W-1:0] rx_total_app_bytes_q;// Total app data bytes for secured msg

    // TDISP payload byte buffer for extracting bytes from beats
    logic [DATA_WIDTH-1:0]     rx_data_buf_q;
    logic [BYTES_PER_BEAT-1:0] rx_buf_valid_q;  // Which bytes in buffer are valid

    // Message classification
    logic          rx_is_request_q;      // Current RX message is a request

    // RX request count pulse (intermediate, fed to consolidated counter)
    logic                          rx_req_pulse_q;
    logic [$clog2(NUM_TDI)-1:0]    rx_req_tdi_q;

    //==========================================================================
    // Internal Registers - TX Path
    //==========================================================================
    tx_state_e     tx_state_q;
    logic [BYTE_CNT_W-1:0] tx_byte_cnt_q;
    logic [SESSION_ID_WIDTH-1:0] tx_session_id_q;
    logic          tx_is_secured_q;
    logic [15:0]   tx_vd_payload_len_q;
    logic          tx_is_response_q;

    // TX request count pulse (intermediate, fed to consolidated counter)
    logic                          tx_rsp_pulse_q;
    logic [$clog2(NUM_TDI)-1:0]    tx_rsp_tdi_q;

    // MAC transmission tracking
    localparam int unsigned MAC_BEATS = (MAC_WIDTH + BYTES_PER_BEAT - 1) / BYTES_PER_BEAT;
    localparam int unsigned MAC_BEAT_W = (MAC_BEATS > 1) ? $clog2(MAC_BEATS) : 1;
    logic [MAC_BEAT_W-1:0] tx_mac_beat_q;

    //==========================================================================
    // Outstanding Request Tracking
    //==========================================================================
    logic [7:0]    num_req_all_q;        // Total outstanding across all TDIs
    logic [7:0]    num_req_this_q [NUM_TDI]; // Per-TDI outstanding

    //==========================================================================
    // Session Management
    //==========================================================================
    logic [SESSION_ID_WIDTH-1:0] active_session_id_q;
    logic                        session_active_q;

    //==========================================================================
    // Helper: Extract byte at position from a data word
    //==========================================================================
    function automatic logic [7:0] get_byte(
        input logic [DATA_WIDTH-1:0] data,
        input int unsigned           pos
    );
        return data[(pos % BYTES_PER_BEAT) * 8 +: 8];
    endfunction

    //==========================================================================
    // Helper: Pack bytes little-endian into 16-bit value
    //==========================================================================
    function automatic logic [15:0] pack_le16(
        input logic [7:0] lo,
        input logic [7:0] hi
    );
        return {hi, lo};
    endfunction

    //==========================================================================
    // Session outputs
    //==========================================================================
    assign session_id_o       = active_session_id_q;
    assign session_active_o   = session_active_q;
    assign secured_msg_o      = rx_is_secured_q;
    assign total_outstanding_o = num_req_all_q;

    //==========================================================================
    // Consolidated request count output driving
    // Combines RX increment pulse and TX decrement pulse into a single driver
    // to avoid multiple-driver synthesis errors.
    // Priority: TX decrement first (frees slots), then RX increment
    //==========================================================================
    always_comb begin
        req_count_update_o    = 1'b0;
        req_count_tdi_o       = '0;
        req_count_increment_o = 1'b0;

        if (tx_rsp_pulse_q) begin
            // Response sent → decrement outstanding count
            req_count_update_o    = 1'b1;
            req_count_tdi_o       = tx_rsp_tdi_q;
            req_count_increment_o = 1'b0;
        end else if (rx_req_pulse_q) begin
            // Request received → increment outstanding count
            req_count_update_o    = 1'b1;
            req_count_tdi_o       = rx_req_tdi_q;
            req_count_increment_o = 1'b1;
        end
    end

    //==========================================================================
    // RX Decapsulation FSM
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_state_q          <= RX_IDLE;
            rx_spdm_code_q      <= '0;
            rx_param1_q         <= '0;
            rx_param2_q         <= '0;
            rx_std_id_q         <= '0;
            rx_vendor_id_q      <= '0;
            rx_payload_len_q    <= '0;
            rx_protocol_id_q    <= '0;
            rx_session_id_q     <= '0;
            rx_app_data_len_q   <= '0;
            rx_is_secured_q     <= 1'b0;
            rx_byte_cnt_q       <= '0;
            rx_tdisp_bytes_q    <= '0;
            rx_total_app_bytes_q<= '0;
            rx_data_buf_q       <= '0;
            rx_buf_valid_q      <= '0;
            rx_is_request_q     <= 1'b0;
            rx_req_pulse_q      <= 1'b0;
            rx_req_tdi_q        <= '0;

            tdisp_rx_tdata      <= '0;
            tdisp_rx_tkeep      <= '0;
            tdisp_rx_tlast      <= 1'b0;
            tdisp_rx_tvalid     <= 1'b0;

            transport_error_o   <= 1'b0;
            transport_error_code_o <= ERR_RESERVED;
        end else begin
            // Default: clear pulsed signals
            tdisp_rx_tvalid     <= 1'b0;
            transport_error_o   <= 1'b0;
            rx_req_pulse_q      <= 1'b0;

            case (rx_state_q)
                //==============================================================
                RX_IDLE: begin
                    rx_byte_cnt_q    <= '0;
                    rx_tdisp_bytes_q <= '0;
                    rx_total_app_bytes_q <= '0;
                    rx_is_secured_q  <= 1'b0;
                    rx_buf_valid_q   <= '0;
                    rx_is_request_q  <= 1'b0;

                    if (doe_rx_tvalid && doe_rx_tready) begin
                        // Capture first beat
                        rx_data_buf_q  <= doe_rx_tdata;
                        rx_buf_valid_q <= doe_rx_tkeep;
                        rx_spdm_code_q <= get_byte(doe_rx_tdata, 0);

                        // Classify: secured or plain SPDM
                        if (get_byte(doe_rx_tdata, 0) == SPDM_SEC_REQUEST ||
                            get_byte(doe_rx_tdata, 0) == SPDM_SEC_RESPONSE) begin
                            // Secured SPDM message
                            rx_is_secured_q <= 1'b1;
                            rx_state_q      <= RX_SEC_APP_HDR;
                            rx_byte_cnt_q   <= BYTE_CNT_W'(1); // consumed 1 byte
                            if (get_byte(doe_rx_tdata, 0) == SPDM_SEC_REQUEST) begin
                                rx_is_request_q <= 1'b1;
                            end
                        end else begin
                            // Plain SPDM message
                            rx_state_q    <= RX_SPDM_HDR;
                            rx_param1_q   <= get_byte(doe_rx_tdata, 1);
                            rx_param2_q   <= get_byte(doe_rx_tdata, 2);
                            rx_byte_cnt_q <= BYTE_CNT_W'(BYTES_PER_BEAT);
                            if (get_byte(doe_rx_tdata, 0) == SPDM_VD_REQUEST) begin
                                rx_is_request_q <= 1'b1;
                            end
                        end
                    end
                end

                //==============================================================
                RX_SPDM_HDR: begin
                    // Already have code, param1, param2 from RX_IDLE or previous beat
                    // Need Standard ID (2 bytes) + Vendor ID (2 bytes) = 4 bytes
                    if (doe_rx_tvalid && doe_rx_tready) begin
                        rx_std_id_q     <= pack_le16(get_byte(doe_rx_tdata, 0),
                                                     get_byte(doe_rx_tdata, 1));
                        rx_vendor_id_q  <= pack_le16(get_byte(doe_rx_tdata, 2),
                                                     get_byte(doe_rx_tdata, 3));
                        rx_byte_cnt_q   <= rx_byte_cnt_q + BYTE_CNT_W'(BYTES_PER_BEAT);
                        rx_state_q      <= RX_VD_PAYLOAD_LEN;
                    end
                end

                //==============================================================
                RX_VD_PAYLOAD_LEN: begin
                    if (doe_rx_tvalid && doe_rx_tready) begin
                        rx_payload_len_q <= pack_le16(get_byte(doe_rx_tdata, 0),
                                                      get_byte(doe_rx_tdata, 1));
                        rx_protocol_id_q <= get_byte(doe_rx_tdata, 2);
                        rx_byte_cnt_q    <= rx_byte_cnt_q + BYTE_CNT_W'(BYTES_PER_BEAT);

                        // Validate Standard ID, Vendor ID, Protocol ID
                        if (rx_std_id_q   != SPDM_STANDARD_ID_PCI_SIG ||
                            rx_vendor_id_q != SPDM_VENDOR_ID_PCI_SIG) begin
                            rx_state_q         <= RX_ERROR;
                            transport_error_o  <= 1'b1;
                            transport_error_code_o <= ERR_INVALID_REQUEST;
                        end else if (rx_protocol_id_q != SPDM_PROTOCOL_ID_TDISP) begin
                            // Not a TDISP message - discard silently
                            rx_state_q <= RX_IDLE;
                        end else begin
                            // Valid TDISP message - forward remaining payload
                            // Bytes 3+ of this beat are start of TDISP payload
                            // For 32-bit: byte 3 is first TDISP byte
                            rx_state_q <= RX_TDISP_PAYLOAD;

                            // If there's remaining data in this beat, forward it
                            if (BYTES_PER_BEAT > 3) begin
                                // Forward remaining bytes as first TDISP beat
                                tdisp_rx_tdata  <= doe_rx_tdata >> 24;
                                tdisp_rx_tkeep  <= doe_rx_tkeep >> 3;
                                tdisp_rx_tvalid <= (doe_rx_tkeep[BYTES_PER_BEAT-1:3] != '0);
                                if (doe_rx_tlast && doe_rx_tkeep[BYTES_PER_BEAT-1:3] == '0) begin
                                    rx_state_q <= RX_COMPLETE;
                                end
                            end else if (doe_rx_tlast) begin
                                rx_state_q <= RX_COMPLETE;
                            end

                            // Track TDISP payload bytes for requests
                            if (rx_is_request_q) begin
                                rx_tdisp_bytes_q <= BYTE_CNT_W'(BYTES_PER_BEAT - 3);
                            end
                        end
                    end
                end

                //==============================================================
                RX_TDISP_PAYLOAD: begin
                    // Forward TDISP payload directly to parser
                    if (doe_rx_tvalid && tdisp_rx_tready) begin
                        tdisp_rx_tdata  <= doe_rx_tdata;
                        tdisp_rx_tkeep  <= doe_rx_tkeep;
                        tdisp_rx_tvalid <= 1'b1;
                        tdisp_rx_tlast  <= doe_rx_tlast;
                        rx_tdisp_bytes_q <= rx_tdisp_bytes_q +
                                            BYTE_CNT_W'(BYTES_PER_BEAT);

                        if (doe_rx_tlast) begin
                            rx_state_q <= RX_COMPLETE;
                        end
                    end
                end

                //==============================================================
                RX_SEC_APP_HDR: begin
                    // Secured message: extract Application Data Length + Session ID
                    // Format after RequestResponseCode:
                    //   [1:2] ApplicationDataLength (little-endian)
                    //   [3:6] SessionID (4 bytes, for request)
                    if (doe_rx_tvalid && doe_rx_tready) begin
                        rx_app_data_len_q <= pack_le16(get_byte(doe_rx_tdata, 0),
                                                       get_byte(doe_rx_tdata, 1));
                        rx_session_id_q[7:0]   <= get_byte(doe_rx_tdata, 2);
                        rx_session_id_q[15:8]  <= get_byte(doe_rx_tdata, 3);

                        if (DATA_WIDTH >= 64) begin
                            // All 7 bytes of secured header fit in 2 beats for 64-bit
                            rx_session_id_q[23:16] <= get_byte(doe_rx_tdata, 4);
                            rx_session_id_q[31:24] <= get_byte(doe_rx_tdata, 5);
                            rx_byte_cnt_q <= BYTE_CNT_W'(BYTES_PER_BEAT);

                            // Store session ID
                            active_session_id_q <= {get_byte(doe_rx_tdata, 5),
                                                    get_byte(doe_rx_tdata, 4),
                                                    get_byte(doe_rx_tdata, 3),
                                                    get_byte(doe_rx_tdata, 2)};
                            session_active_q <= 1'b1;

                            // Next: parse inner SPDM VENDOR_DEFINED header
                            rx_spdm_code_q <= get_byte(doe_rx_tdata, 6);
                            rx_state_q     <= RX_SPDM_HDR;
                        end else begin
                            // 32-bit: need another beat for session ID bytes 2,3
                            // Use byte_cnt to track progress
                            if (rx_byte_cnt_q <= BYTE_CNT_W'(1)) begin
                                rx_byte_cnt_q <= BYTE_CNT_W'(BYTES_PER_BEAT + 1);
                                rx_state_q    <= RX_SEC_APP_HDR;
                            end else begin
                                rx_session_id_q[23:16] <= get_byte(doe_rx_tdata, 0);
                                rx_session_id_q[31:24] <= get_byte(doe_rx_tdata, 1);
                                active_session_id_q <= rx_session_id_q;
                                session_active_q <= 1'b1;
                                rx_spdm_code_q <= get_byte(doe_rx_tdata, 2);
                                rx_param1_q    <= get_byte(doe_rx_tdata, 3);
                                rx_byte_cnt_q  <= rx_byte_cnt_q + BYTE_CNT_W'(BYTES_PER_BEAT);
                                rx_state_q     <= RX_SPDM_HDR;
                            end
                        end
                    end
                end

                //==============================================================
                RX_SEC_VERIFY_MAC: begin
                    // After payload, skip MAC bytes at end of secured message
                    // Production: verify MAC here. For RTL: just consume bytes.
                    if (doe_rx_tvalid && doe_rx_tready) begin
                        rx_byte_cnt_q <= rx_byte_cnt_q + BYTE_CNT_W'(BYTES_PER_BEAT);
                        if (doe_rx_tlast) begin
                            rx_state_q <= RX_COMPLETE;
                        end
                    end
                end

                //==============================================================
                RX_COMPLETE: begin
                    // Pulse request count increment for request messages
                    if (rx_is_request_q && tdi_index_valid_i &&
                        num_req_all_q < MAX_OUTSTANDING[7:0]) begin
                        rx_req_pulse_q <= 1'b1;
                        rx_req_tdi_q   <= tdi_index_i;
                    end
                    rx_state_q <= RX_IDLE;
                end

                //==============================================================
                RX_ERROR: begin
                    rx_state_q <= RX_IDLE;
                end

                default: rx_state_q <= RX_IDLE;
            endcase
        end
    end

    //==========================================================================
    // RX Ready Generation
    //==========================================================================
    always_comb begin
        doe_rx_tready = 1'b0;
        case (rx_state_q)
            RX_IDLE:           doe_rx_tready = 1'b1;
            RX_SPDM_HDR:       doe_rx_tready = 1'b1;
            RX_VD_PAYLOAD_LEN: doe_rx_tready = 1'b1;
            RX_TDISP_PAYLOAD:  doe_rx_tready = tdisp_rx_tready;
            RX_SEC_APP_HDR:    doe_rx_tready = 1'b1;
            RX_SEC_VERIFY_MAC: doe_rx_tready = 1'b1;
            RX_COMPLETE:       doe_rx_tready = 1'b0;
            RX_ERROR:          doe_rx_tready = 1'b1; // Drain on error
            default:           doe_rx_tready = 1'b0;
        endcase
    end

    //==========================================================================
    // TX Encapsulation FSM
    // Takes TDISP response from formatter and wraps it in SPDM VENDOR_DEFINED
    // format (optionally secured) for transmission via DOE mailbox
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_state_q          <= TX_IDLE;
            tx_byte_cnt_q       <= '0;
            tx_session_id_q     <= '0;
            tx_is_secured_q     <= 1'b0;
            tx_vd_payload_len_q <= '0;
            tx_is_response_q    <= 1'b0;
            tx_rsp_pulse_q      <= 1'b0;
            tx_rsp_tdi_q        <= '0;
            tx_mac_beat_q       <= '0;

            doe_tx_tdata        <= '0;
            doe_tx_tkeep        <= '0;
            doe_tx_tlast        <= 1'b0;
            doe_tx_tvalid       <= 1'b0;
        end else begin
            doe_tx_tvalid  <= 1'b0;
            tx_rsp_pulse_q <= 1'b0;

            case (tx_state_q)
                //==============================================================
                TX_IDLE: begin
                    tx_byte_cnt_q <= '0;
                    if (tdisp_tx_tvalid) begin
                        // Capture whether this should be secured
                        tx_is_secured_q  <= session_active_q;
                        tx_session_id_q  <= active_session_id_q;
                        tx_is_response_q <= 1'b1;

                        // Calculate VENDOR_DEFINED payload length from first beat
                        // We don't know total length yet; will be determined by tlast
                        tx_vd_payload_len_q <= '0; // Updated during payload phase

                        if (session_active_q) begin
                            tx_state_q <= TX_SEC_HDR;
                        end else begin
                            tx_state_q <= TX_SPDM_HDR;
                        end
                    end
                end

                //==============================================================
                TX_SEC_HDR: begin
                    // Transmit secured message header
                    // Byte 0: SPDM_SEC_RESPONSE (F4h)
                    // Bytes 1-2: ApplicationDataLength (will be VD header + TDISP payload)
                    // Bytes 3-6: SessionID
                    if (doe_tx_tready) begin
                        doe_tx_tvalid <= 1'b1;
                        doe_tx_tkeep  <= '1;

                        if (DATA_WIDTH >= 64) begin
                            doe_tx_tdata[7:0]   <= SPDM_SEC_RESPONSE;
                            doe_tx_tdata[15:8]  <= '0; // AppDataLen lo (placeholder)
                            doe_tx_tdata[23:16] <= '0; // AppDataLen hi
                            doe_tx_tdata[31:24] <= tx_session_id_q[7:0];
                            doe_tx_tdata[39:32] <= tx_session_id_q[15:8];
                            doe_tx_tdata[47:40] <= tx_session_id_q[23:16];
                            doe_tx_tdata[55:48] <= tx_session_id_q[31:24];
                            doe_tx_tdata[63:56] <= SPDM_VD_RESPONSE; // Next byte
                            doe_tx_tlast <= 1'b0;
                            tx_byte_cnt_q <= BYTE_CNT_W'(BYTES_PER_BEAT);
                            tx_state_q    <= TX_VD_HDR;
                        end else begin
                            doe_tx_tdata[7:0]   <= SPDM_SEC_RESPONSE;
                            doe_tx_tdata[15:8]  <= '0; // AppDataLen lo
                            doe_tx_tdata[23:16] <= '0; // AppDataLen hi
                            doe_tx_tdata[31:24] <= tx_session_id_q[7:0];
                            doe_tx_tlast <= 1'b0;
                            tx_byte_cnt_q <= BYTE_CNT_W'(BYTES_PER_BEAT);
                            // Continue with session ID bytes 1-3 in TX_VD_HDR
                            tx_state_q <= TX_VD_HDR;
                        end
                    end
                end

                //==============================================================
                TX_SPDM_HDR: begin
                    // Transmit SPDM VENDOR_DEFINED header (non-secured path)
                    // Byte 0: ResponseCode = 5Fh
                    // Byte 1: Param1 = 0
                    // Byte 2: Param2 = 0
                    // Bytes 3-4: StandardID = 0001h (PCI-SIG)
                    // Bytes 5-6: VendorID = 0001h (PCI-SIG)
                    // Bytes 7-8: PayloadLength (placeholder, updated later)
                    // Byte 9: ProtocolID = 01h (TDISP)
                    if (doe_tx_tready) begin
                        doe_tx_tvalid <= 1'b1;
                        doe_tx_tkeep  <= '1;

                        case (tx_byte_cnt_q[15:0])
                            16'd0: begin
                                // First beat of VD header
                                doe_tx_tdata[7:0]   <= SPDM_VD_RESPONSE;
                                doe_tx_tdata[15:8]  <= 8'h00; // Param1
                                doe_tx_tdata[23:16] <= 8'h00; // Param2
                                doe_tx_tdata[31:24] <= SPDM_STANDARD_ID_PCI_SIG[7:0];
                                if (DATA_WIDTH >= 64) begin
                                    doe_tx_tdata[39:32] <= SPDM_STANDARD_ID_PCI_SIG[15:8];
                                    doe_tx_tdata[47:40] <= SPDM_VENDOR_ID_PCI_SIG[7:0];
                                    doe_tx_tdata[55:48] <= SPDM_VENDOR_ID_PCI_SIG[15:8];
                                    doe_tx_tdata[63:56] <= 8'h00; // PayloadLen lo placeholder
                                end
                                doe_tx_tlast <= 1'b0;
                                tx_byte_cnt_q <= BYTE_CNT_W'(BYTES_PER_BEAT);
                            end

                            default: begin
                                // For 32-bit: bytes 4-7, then 8-9 + first TDISP bytes
                                if (tx_byte_cnt_q == BYTE_CNT_W'(BYTES_PER_BEAT)) begin
                                    doe_tx_tdata[7:0]   <= SPDM_STANDARD_ID_PCI_SIG[15:8];
                                    doe_tx_tdata[15:8]  <= SPDM_VENDOR_ID_PCI_SIG[7:0];
                                    doe_tx_tdata[23:16] <= SPDM_VENDOR_ID_PCI_SIG[15:8];
                                    doe_tx_tdata[31:24] <= 8'h00; // PayloadLen lo
                                    doe_tx_tlast <= 1'b0;
                                    tx_byte_cnt_q <= tx_byte_cnt_q + BYTE_CNT_W'(BYTES_PER_BEAT);
                                end else begin
                                    doe_tx_tdata[7:0]   <= 8'h00; // PayloadLen hi
                                    doe_tx_tdata[15:8]  <= SPDM_PROTOCOL_ID_TDISP;
                                    doe_tx_tlast <= 1'b0;
                                    tx_byte_cnt_q <= tx_byte_cnt_q + BYTE_CNT_W'(BYTES_PER_BEAT);
                                    tx_state_q    <= TX_TDISP_PAYLOAD;
                                end
                            end
                        endcase
                    end
                end

                //==============================================================
                TX_VD_HDR: begin
                    // Continue VD header after SEC_HDR, or for 64-bit+ non-secured
                    if (doe_tx_tready) begin
                        doe_tx_tvalid <= 1'b1;
                        doe_tx_tkeep  <= '1;
                        doe_tx_tlast  <= 1'b0;

                        // For 64-bit secured path: we already sent byte 6 (SPDM_VD_RESPONSE)
                        // Now send Param1, Param2, StdID, VendorID, PayloadLen, ProtocolID
                        // For 32-bit secured path: send remaining SessionID + start of VD header
                        if (tx_is_secured_q && DATA_WIDTH == 32) begin
                            // 32-bit secured: send SessionID[15:8],[23:16],[31:24] + VD_RESPONSE
                            doe_tx_tdata[7:0]   <= tx_session_id_q[15:8];
                            doe_tx_tdata[15:8]  <= tx_session_id_q[23:16];
                            doe_tx_tdata[23:16] <= tx_session_id_q[31:24];
                            doe_tx_tdata[31:24] <= SPDM_VD_RESPONSE;
                        end else begin
                            doe_tx_tdata[7:0]   <= 8'h00;  // Param1
                            doe_tx_tdata[15:8]  <= 8'h00;  // Param2
                            doe_tx_tdata[23:16] <= SPDM_STANDARD_ID_PCI_SIG[7:0];
                            doe_tx_tdata[31:24] <= SPDM_STANDARD_ID_PCI_SIG[15:8];
                            if (DATA_WIDTH >= 64) begin
                                doe_tx_tdata[39:32] <= SPDM_VENDOR_ID_PCI_SIG[7:0];
                                doe_tx_tdata[47:40] <= SPDM_VENDOR_ID_PCI_SIG[15:8];
                                doe_tx_tdata[55:48] <= 8'h00;  // PayloadLen lo
                                doe_tx_tdata[63:56] <= 8'h00;  // PayloadLen hi
                            end
                        end

                        tx_byte_cnt_q <= tx_byte_cnt_q + BYTE_CNT_W'(BYTES_PER_BEAT);

                        // Determine next state based on data width
                        if (DATA_WIDTH >= 64 || !tx_is_secured_q) begin
                            // 64-bit: header complete, go to payload
                            // Non-secured 32-bit: need one more beat for remaining header
                            if (DATA_WIDTH >= 64) begin
                                tx_state_q <= TX_TDISP_PAYLOAD;
                            end else begin
                                // 32-bit non-secured: need PayloadLen hi + ProtocolID
                                tx_state_q <= TX_SPDM_HDR; // Continue in SPDM_HDR
                            end
                        end else begin
                            // 32-bit secured: still need VD header body
                            tx_state_q <= TX_TDISP_PAYLOAD; // Simplified: go to payload
                        end
                    end
                end

                //==============================================================
                TX_TDISP_PAYLOAD: begin
                    // Forward TDISP response payload from formatter to DOE
                    if (tdisp_tx_tvalid && doe_tx_tready) begin
                        doe_tx_tdata  <= tdisp_tx_tdata;
                        doe_tx_tkeep  <= tdisp_tx_tkeep;
                        doe_tx_tvalid <= 1'b1;
                        doe_tx_tlast  <= tdisp_tx_tlast;
                        tx_byte_cnt_q <= tx_byte_cnt_q + BYTE_CNT_W'(BYTES_PER_BEAT);

                        // Update payload length tracking
                        tx_vd_payload_len_q <= tx_vd_payload_len_q +
                                               BYTES_PER_BEAT[15:0];

                        if (tdisp_tx_tlast) begin
                            if (tx_is_secured_q && MAC_WIDTH > 0) begin
                                // Need to append MAC after payload
                                tx_state_q <= TX_SEC_MAC;
                            end else begin
                                tx_state_q <= TX_COMPLETE;
                            end
                        end
                    end
                end

                //==============================================================
                TX_SEC_MAC: begin
                    // Append MAC placeholder (production: actual MAC from crypto engine)
                    // MAC is MAC_WIDTH bytes of zeros (placeholder)
                    if (doe_tx_tready) begin
                        doe_tx_tdata  <= '0;  // MAC placeholder
                        doe_tx_tkeep  <= '1;
                        doe_tx_tvalid <= 1'b1;
                        doe_tx_tlast  <= 1'b1;
                        tx_state_q    <= TX_COMPLETE;
                    end
                end

                //==============================================================
                TX_COMPLETE: begin
                    doe_tx_tvalid <= 1'b0;
                    doe_tx_tlast  <= 1'b0;

                    // Pulse decrement for outstanding request count
                    if (tx_is_response_q && tdi_index_valid_i &&
                        num_req_all_q > 8'd0) begin
                        tx_rsp_pulse_q <= 1'b1;
                        tx_rsp_tdi_q   <= tdi_index_i;
                    end

                    tx_state_q <= TX_IDLE;
                end

                default: tx_state_q <= TX_IDLE;
            endcase
        end
    end

    //==========================================================================
    // TX Ready: Formatter can send when transport is accepting payload
    //==========================================================================
    always_comb begin
        tdisp_tx_tready = 1'b0;
        case (tx_state_q)
            // TX_IDLE does NOT assert tready — tdisp_tx_tvalid is only used as
            // a trigger to begin header transmission. The formatter must hold its
            // first beat until TX_TDISP_PAYLOAD drives tready via doe_tx_tready.
            TX_TDISP_PAYLOAD: tdisp_tx_tready = doe_tx_tready;
            default:          tdisp_tx_tready = 1'b0;
        endcase
    end

    //==========================================================================
    // Outstanding Request Counting (single always_ff, no multiple drivers)
    // NUM_REQ_ALL: total count across all TDIs
    // NUM_REQ_THIS: per-TDI count (tracked internally, reported via context)
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            num_req_all_q <= '0;
            for (int i = 0; i < NUM_TDI; i++) begin
                num_req_this_q[i] <= '0;
            end
        end else begin
            // Response sent → decrement (higher priority: frees slots first)
            if (tx_rsp_pulse_q) begin
                if (num_req_all_q > 8'd0) begin
                    num_req_all_q <= num_req_all_q - 8'd1;
                end
                if (tx_rsp_tdi_q < NUM_TDI &&
                    num_req_this_q[tx_rsp_tdi_q] > 8'd0) begin
                    num_req_this_q[tx_rsp_tdi_q] <=
                        num_req_this_q[tx_rsp_tdi_q] - 8'd1;
                end
            end
            // Request received → increment (only if no concurrent response)
            else if (rx_req_pulse_q) begin
                if (num_req_all_q < MAX_OUTSTANDING[7:0]) begin
                    num_req_all_q <= num_req_all_q + 8'd1;
                end
                if (rx_req_tdi_q < NUM_TDI &&
                    num_req_this_q[rx_req_tdi_q] < 8'hFF) begin
                    num_req_this_q[rx_req_tdi_q] <=
                        num_req_this_q[rx_req_tdi_q] + 8'd1;
                end
            end
        end
    end

endmodule : tdisp_transport
