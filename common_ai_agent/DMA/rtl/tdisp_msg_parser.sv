//============================================================================
// TDISP Message Parser
// Parses incoming TDISP messages from SPDM secured session layer
// Extracts header fields and routes payload to appropriate handlers
// Based on PCIe Base Spec Rev 7.0, Chapter 11, Table 11-6
//============================================================================

module tdisp_msg_parser #(
    parameter int unsigned DATA_WIDTH = 32,  // AXI-Stream data width (must be power of 2)
    parameter int unsigned MAX_PAYLOAD_BYTES = 256
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //--- AXI-Stream input from SPDM/DOE transport ---
    input  logic [DATA_WIDTH-1:0]           s_axis_tdata,
    input  logic [DATA_WIDTH/8-1:0]         s_axis_tkeep,
    input  logic                            s_axis_tlast,
    input  logic                            s_axis_tvalid,
    output logic                            s_axis_tready,

    //--- Parsed header output ---
    output logic                            hdr_valid_o,          // Header parsed successfully
    output logic [7:0]                      tdisp_version_o,      // TDISPVersion field
    output logic [3:0]                      tdisp_version_major_o,// Major version (bits 7:4)
    output logic [3:0]                      tdisp_version_minor_o,// Minor version (bits 3:0)
    output tdisp_types::tdisp_req_code_e    msg_type_o,           // MessageType field
    output logic [95:0]                     interface_id_o,       // INTERFACE_ID (96-bit)

    //--- Version validation ---
    output logic                            version_valid_o,      // Version matches negotiated version
    output logic                            version_mismatch_o,   // Version mismatch detected

    //--- Payload streaming output ---
    output logic [DATA_WIDTH-1:0]           m_payload_tdata,
    output logic [DATA_WIDTH/8-1:0]         m_payload_tkeep,
    output logic                            m_payload_tlast,
    output logic                            m_payload_tvalid,
    input  logic                            m_payload_tready,

    //--- Message length info ---
    output logic [15:0]                     msg_total_len_o,      // Total message length in bytes
    output logic [15:0]                     payload_len_o,        // Payload length in bytes

    //--- Parse status ---
    output logic                            parse_done_o,         // Entire message parsed
    output logic                            parse_error_o,        // Parse error detected
    output tdisp_types::tdisp_error_code_e  parse_error_code_o    // Specific error code
);

    import tdisp_types::*;

    //==========================================================================
    // Local parameters
    //==========================================================================
    localparam int unsigned BYTES_PER_BEAT = DATA_WIDTH / 8;
    localparam int unsigned HDR_BYTES      = TDISP_HDR_SIZE; // 16 bytes
    localparam int unsigned BYTE_CNT_W     = $clog2(MAX_PAYLOAD_BYTES + HDR_BYTES + 1);

    //==========================================================================
    // FSM states for parsing
    //==========================================================================
    typedef enum logic [2:0] {
        PARSE_IDLE,
        PARSE_HEADER,
        PARSE_IFACE_ID,
        PARSE_PAYLOAD,
        PARSE_COMPLETE,
        PARSE_ERROR
    } parse_state_e;

    //==========================================================================
    // Internal registers
    //==========================================================================
    parse_state_e    state_q;
    logic [BYTE_CNT_W-1:0] byte_cnt_q;     // Byte counter within current phase
    logic [BYTE_CNT_W-1:0] total_bytes_q;  // Total bytes received

    // Header staging registers
    logic [7:0]      hdr_version_q;
    logic [7:0]      hdr_msg_type_q;
    logic [15:0]     hdr_reserved_q;
    logic [95:0]     hdr_iface_id_q;

    // INTERFACE_ID accumulator (96 bits = 12 bytes)
    logic [95:0]     iface_id_shift;
    logic [3:0]      iface_id_bytes_q;

    // Payload length tracking
    logic [15:0]     payload_bytes_q;

    //==========================================================================
    // Combinational: derived signals
    //==========================================================================
    assign tdisp_version_o       = hdr_version_q;
    assign tdisp_version_major_o = hdr_version_q[7:4];
    assign tdisp_version_minor_o = hdr_version_q[3:0];
    assign msg_type_o            = tdisp_req_code_e'(hdr_msg_type_q);
    assign interface_id_o        = hdr_iface_id_q;
    assign msg_total_len_o       = total_bytes_q[15:0];

    // Version check: TDISP v1.0 = 8'h10
    assign version_valid_o    = (hdr_version_q == TDISP_VERSION_1_0);
    assign version_mismatch_o = (hdr_version_q != TDISP_VERSION_1_0) && (state_q != PARSE_IDLE);

    //==========================================================================
    // Calculate expected payload length based on message type
    //==========================================================================
    function automatic logic [15:0] get_expected_payload_len(
        input tdisp_req_code_e msg_code
    );
        case (msg_code)
            REQ_GET_TDISP_VERSION:           return 16'd0;   // No payload beyond header
            REQ_GET_TDISP_CAPABILITIES:      return 16'd4;   // TSM_CAPS (4 bytes)
            REQ_LOCK_INTERFACE:              return 16'd20;  // FLAGS(2)+StreamID(1)+Rsvd(1)+MMIO_OFFSET(8)+P2P_MASK(8)
            REQ_GET_DEVICE_INTERFACE_REPORT: return 16'd0;   // No payload
            REQ_GET_DEVICE_INTERFACE_STATE:  return 16'd0;   // No payload
            REQ_START_INTERFACE:             return 16'd32;  // START_INTERFACE_NONCE (32 bytes)
            REQ_STOP_INTERFACE:              return 16'd0;   // No payload
            REQ_BIND_P2P_STREAM:             return 16'd4;   // Stream_ID + reserved
            REQ_UNBIND_P2P_STREAM:           return 16'd4;   // Stream_ID + reserved
            REQ_SET_MMIO_ATTRIBUTE:          return 16'd16;  // Variable, min 16 bytes
            REQ_VDM:                         return 16'd0;   // Variable length
            REQ_SET_TDISP_CONFIG:            return 16'd4;   // Config data
            default:                         return 16'd0;
        endcase
    endfunction

    //==========================================================================
    // Helper: extract byte from current beat at position
    //==========================================================================
    function automatic logic [7:0] extract_byte(
        input logic [DATA_WIDTH-1:0] data,
        input int unsigned           byte_pos
    );
        int unsigned idx;
        idx = byte_pos % BYTES_PER_BEAT;
        return data[idx*8 +: 8];
    endfunction

    //==========================================================================
    // Main parsing FSM
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q           <= PARSE_IDLE;
            byte_cnt_q        <= '0;
            total_bytes_q     <= '0;
            hdr_version_q     <= '0;
            hdr_msg_type_q    <= '0;
            hdr_reserved_q    <= '0;
            hdr_iface_id_q    <= '0;
            iface_id_bytes_q  <= '0;
            payload_bytes_q   <= '0;
            hdr_valid_o       <= 1'b0;
            parse_done_o      <= 1'b0;
            parse_error_o     <= 1'b0;
            parse_error_code_o<= ERR_RESERVED;
            m_payload_tvalid  <= 1'b0;
            m_payload_tdata   <= '0;
            m_payload_tkeep   <= '0;
            m_payload_tlast   <= 1'b0;
            payload_len_o     <= '0;
        end else begin
            // Default pulse clears
            hdr_valid_o       <= 1'b0;
            parse_done_o      <= 1'b0;
            m_payload_tvalid  <= 1'b0;

            case (state_q)
                //--------------------------------------------------------------
                PARSE_IDLE: begin
                    byte_cnt_q    <= '0;
                    total_bytes_q <= '0;
                    parse_error_o <= 1'b0;
                    iface_id_bytes_q <= '0;
                    if (s_axis_tvalid && s_axis_tready) begin
                        state_q <= PARSE_HEADER;
                        // First beat: extract version and message type
                        hdr_version_q  <= extract_byte(s_axis_tdata, 0); // Offset 0
                        hdr_msg_type_q <= extract_byte(s_axis_tdata, 1); // Offset 1
                        // Extract reserved (offsets 2-3)
                        hdr_reserved_q[7:0]  <= extract_byte(s_axis_tdata, 2);
                        hdr_reserved_q[15:8] <= extract_byte(s_axis_tdata, 3);
                        byte_cnt_q    <= BYTES_PER_BEAT[BYTE_CNT_W-1:0];
                        total_bytes_q <= BYTES_PER_BEAT[BYTE_CNT_W-1:0];

                        // If DATA_WIDTH >= 128, header fits in one beat
                        if (DATA_WIDTH >= 128) begin
                            // Extract INTERFACE_ID (bytes 4-15)
                            hdr_iface_id_q[7:0]   <= extract_byte(s_axis_tdata, 4);
                            hdr_iface_id_q[15:8]  <= extract_byte(s_axis_tdata, 5);
                            hdr_iface_id_q[23:16] <= extract_byte(s_axis_tdata, 6);
                            hdr_iface_id_q[31:24] <= extract_byte(s_axis_tdata, 7);
                            hdr_iface_id_q[39:32] <= extract_byte(s_axis_tdata, 8);
                            hdr_iface_id_q[47:40] <= extract_byte(s_axis_tdata, 9);
                            hdr_iface_id_q[55:48] <= extract_byte(s_axis_tdata, 10);
                            hdr_iface_id_q[63:56] <= extract_byte(s_axis_tdata, 11);
                            hdr_iface_id_q[71:64] <= extract_byte(s_axis_tdata, 12);
                            hdr_iface_id_q[79:72] <= extract_byte(s_axis_tdata, 13);
                            hdr_iface_id_q[87:80] <= extract_byte(s_axis_tdata, 14);
                            hdr_iface_id_q[95:88] <= extract_byte(s_axis_tdata, 15);
                            byte_cnt_q <= 16'd16;

                            // Header complete, validate version
                            if (extract_byte(s_axis_tdata, 0) != TDISP_VERSION_1_0) begin
                                state_q           <= PARSE_ERROR;
                                parse_error_o     <= 1'b1;
                                parse_error_code_o<= ERR_VERSION_MISMATCH;
                            end else begin
                                hdr_valid_o  <= 1'b1;
                                payload_len_o <= get_expected_payload_len(
                                    tdisp_req_code_e'(extract_byte(s_axis_tdata, 1)));
                                if (s_axis_tlast) begin
                                    state_q <= PARSE_COMPLETE;
                                    parse_done_o <= 1'b1;
                                end else begin
                                    state_q <= PARSE_PAYLOAD;
                                end
                            end
                        end
                    end
                end

                //--------------------------------------------------------------
                PARSE_HEADER: begin
                    if (s_axis_tvalid && s_axis_tready) begin
                        // Continue accumulating INTERFACE_ID bytes (starting from byte 4)
                        // For 32-bit: beats 1-3 provide bytes 4-15
                        case (byte_cnt_q)
                            8'd4: begin // Bytes 4-7 of message
                                hdr_iface_id_q[7:0]   <= s_axis_tdata[7:0];
                                hdr_iface_id_q[15:8]  <= s_axis_tdata[15:8];
                                hdr_iface_id_q[23:16] <= s_axis_tdata[23:16];
                                hdr_iface_id_q[31:24] <= s_axis_tdata[31:24];
                                byte_cnt_q <= byte_cnt_q + BYTES_PER_BEAT;
                            end
                            8'd8: begin // Bytes 8-11
                                hdr_iface_id_q[39:32] <= s_axis_tdata[7:0];
                                hdr_iface_id_q[47:40] <= s_axis_tdata[15:8];
                                hdr_iface_id_q[55:48] <= s_axis_tdata[23:16];
                                hdr_iface_id_q[63:56] <= s_axis_tdata[31:24];
                                byte_cnt_q <= byte_cnt_q + BYTES_PER_BEAT;
                            end
                            8'd12: begin // Bytes 12-15
                                hdr_iface_id_q[71:64] <= s_axis_tdata[7:0];
                                hdr_iface_id_q[79:72] <= s_axis_tdata[15:8];
                                hdr_iface_id_q[87:80] <= s_axis_tdata[23:16];
                                hdr_iface_id_q[95:88] <= s_axis_tdata[31:24];
                                byte_cnt_q <= 16'd16;

                                // Header complete - validate version
                                if (hdr_version_q != TDISP_VERSION_1_0) begin
                                    state_q           <= PARSE_ERROR;
                                    parse_error_o     <= 1'b1;
                                    parse_error_code_o<= ERR_VERSION_MISMATCH;
                                end else begin
                                    hdr_valid_o   <= 1'b1;
                                    payload_len_o <= get_expected_payload_len(msg_type_o);
                                    if (s_axis_tlast) begin
                                        state_q      <= PARSE_COMPLETE;
                                        parse_done_o <= 1'b1;
                                    end else begin
                                        state_q <= PARSE_PAYLOAD;
                                    end
                                end
                            end
                            default: begin
                                byte_cnt_q <= byte_cnt_q + BYTES_PER_BEAT;
                            end
                        endcase
                        total_bytes_q <= total_bytes_q + BYTES_PER_BEAT;
                    end
                end

                //--------------------------------------------------------------
                PARSE_PAYLOAD: begin
                    if (s_axis_tvalid && s_axis_tready) begin
                        // Forward payload data to handler
                        m_payload_tdata  <= s_axis_tdata;
                        m_payload_tkeep  <= s_axis_tkeep;
                        m_payload_tvalid <= 1'b1;
                        m_payload_tlast  <= s_axis_tlast;
                        payload_bytes_q  <= payload_bytes_q + BYTES_PER_BEAT;
                        total_bytes_q    <= total_bytes_q + BYTES_PER_BEAT;

                        if (s_axis_tlast) begin
                            state_q      <= PARSE_COMPLETE;
                            parse_done_o <= 1'b1;
                        end
                    end
                end

                //--------------------------------------------------------------
                PARSE_COMPLETE: begin
                    state_q <= PARSE_IDLE;
                end

                //--------------------------------------------------------------
                PARSE_ERROR: begin
                    // Hold error state until acknowledged
                    state_q <= PARSE_IDLE;
                    parse_error_o <= 1'b0;
                end

                default: state_q <= PARSE_IDLE;
            endcase
        end
    end

    //==========================================================================
    // AXI-Stream ready generation - backpressure from downstream
    //==========================================================================
    always_comb begin
        s_axis_tready = 1'b0;
        case (state_q)
            PARSE_IDLE,
            PARSE_HEADER:   s_axis_tready = 1'b1;
            PARSE_PAYLOAD:  s_axis_tready = m_payload_tready;
            default:        s_axis_tready = 1'b0;
        endcase
    end

endmodule : tdisp_msg_parser
