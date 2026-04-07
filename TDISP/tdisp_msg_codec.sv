// ============================================================================
// Module:    tdisp_msg_codec.sv
// Purpose:   TDISP Message Parser / Encoder - serializes and deserializes
//            TDISP request/response messages over a byte-serial AXI-S-like
//            transport (SPDM/DOE).
// Spec:      PCI Express Base Specification Revision 7.0, Section 11.3
//
// Parser:  IDLE -> HDR -> PAYLOAD -> DONE
//   - Ingests incoming byte stream, validates header, extracts payload.
//   - Outputs parsed tdisp_msg_header_s + payload byte array.
//
// Encoder:
//   - Accepts response parameters (msg_type, interface_id, payload).
//   - Emits formatted TDISP response byte-by-byte with header.
//
// Little-Endian: All multi-byte fields are emitted/received in little-endian
//   byte order per Section 11.3.3.
// ============================================================================

module tdisp_msg_codec
    import tdisp_pkg::*;
#(
    parameter int DATA_WIDTH      = 8,          // Bits per beat (8 = byte-serial)
    parameter int MAX_REPORT_SIZE = 4096         // Max payload buffer depth in bytes
)(
    input  logic clk,
    input  logic rst_n,

    // =========================================================================
    // Negotiated version (set once during version negotiation)
    // =========================================================================
    input  logic [7:0]  negotiated_version,     // Active TDISP version (e.g. 8'h10)
    input  logic        version_valid,          // High once version is negotiated

    // =========================================================================
    // RX Interface - Request Parser (AXI-S-like, byte-serial)
    // =========================================================================
    input  logic                      rx_valid,
    input  logic [DATA_WIDTH-1:0]     rx_data,
    input  logic                      rx_last,
    output logic                      rx_ready,

    // =========================================================================
    // Parsed Request Outputs (to req_handler)
    // =========================================================================
    output tdisp_msg_header_s         parsed_hdr,
    output logic [7:0]                parsed_payload [MAX_REPORT_SIZE-1:0],
    output logic [15:0]               parsed_payload_len,
    output logic                      parsed_valid,    // Pulse: complete message ready
    output logic                      parsed_error,    // Pulse: malformed message

    // =========================================================================
    // TX Interface - Response Encoder (AXI-S-like, byte-serial)
    // =========================================================================
    output logic                      tx_valid,
    output logic [DATA_WIDTH-1:0]     tx_data,
    output logic                      tx_last,
    input  logic                      tx_ready,

    // =========================================================================
    // Response Inputs (from req_handler)
    // =========================================================================
    input  logic                      resp_valid,           // Handshake: request to send
    output logic                      resp_ready,           // Handshake: encoder can accept
    input  tdisp_resp_code_e          resp_msg_type,        // Response code
    input  logic [INTERFACE_ID_WIDTH-1:0] resp_interface_id, // 96-bit INTERFACE_ID
    input  logic [7:0]                resp_payload [MAX_REPORT_SIZE-1:0],
    input  logic [15:0]               resp_payload_len      // Total payload bytes
);

    // =========================================================================
    // Local constants
    // =========================================================================
    localparam int HDR_BYTES      = TDISP_MSG_HEADER_SIZE;  // 16 bytes
    localparam int CNT_WIDTH      = 16;  // Wide enough for all counters/comparisons

    // =========================================================================
    // Parser state definition
    // =========================================================================
    typedef enum logic [2:0] {
        PARSE_IDLE,
        PARSE_HDR,
        PARSE_PAYLOAD,
        PARSE_DONE,
        PARSE_ERROR
    } parse_state_e;

    // =========================================================================
    // Encoder state definition
    // =========================================================================
    typedef enum logic [2:0] {
        ENC_IDLE,
        ENC_HDR,
        ENC_PAYLOAD,
        ENC_DONE
    } enc_state_e;

    // =========================================================================
    // Parser internal signals
    // =========================================================================
    parse_state_e          parse_state;
    logic [CNT_WIDTH-1:0]  hdr_byte_cnt;
    logic [CNT_WIDTH-1:0]  payload_byte_cnt;
    logic [15:0]           expected_payload_len;
    logic [7:0]            hdr_byte_buf [HDR_BYTES-1:0];

    // =========================================================================
    // Encoder internal signals
    // =========================================================================
    enc_state_e            enc_state;
    logic [CNT_WIDTH-1:0]  enc_hdr_idx;
    logic [CNT_WIDTH-1:0]  enc_payload_idx;
    logic [CNT_WIDTH-1:0]  enc_payload_total;
    logic [7:0]            enc_hdr_buf [HDR_BYTES-1:0];
    logic                  enc_accepted;      // Captured resp inputs

    // =========================================================================
    // Function: Compute expected payload length from request message type
    //   Returns 0 for zero-payload requests, specific length for fixed-size,
    //   and 16'hFFFF for variable-length (VDM).
    // =========================================================================
    function automatic logic [15:0] expected_payload_length(input logic [7:0] msg_type);
        case (msg_type)
            8'h81: return 16'd0;     // GET_TDISP_VERSION
            8'h82: return 16'd4;     // GET_TDISP_CAPABILITIES (TSM_CAPS)
            8'h83: return 16'd20;    // LOCK_INTERFACE_REQUEST
            8'h84: return 16'd4;     // GET_DEVICE_INTERFACE_REPORT
            8'h85: return 16'd0;     // GET_DEVICE_INTERFACE_STATE
            8'h86: return 16'd32;    // START_INTERFACE_REQUEST (NONCE)
            8'h87: return 16'd0;     // STOP_INTERFACE_REQUEST
            8'h88: return 16'd2;     // BIND_P2P_STREAM_REQUEST
            8'h89: return 16'd1;     // UNBIND_P2P_STREAM_REQUEST
            8'h8A: return 16'd16;    // SET_MMIO_ATTRIBUTE_REQUEST
            8'h8B: return 16'hFFFF;  // VDM_REQUEST - variable length
            8'h8C: return 16'd4;     // SET_TDISP_CONFIG_REQUEST
            default: return 16'd0;
        endcase
    endfunction

    // =========================================================================
    // Function: Check if a byte value is a known TDISP request code
    // =========================================================================
    function automatic logic is_known_req_code(input logic [7:0] code);
        case (code)
            8'h81, 8'h82, 8'h83, 8'h84, 8'h85,
            8'h86, 8'h87, 8'h88, 8'h89, 8'h8A,
            8'h8B, 8'h8C: return 1'b1;
            default:      return 1'b0;
        endcase
    endfunction

    // =========================================================================
    // Assemble header struct from byte buffer - combinational (no function
    // with unpacked array port; directly assigned in always block).
    // =========================================================================
    tdisp_msg_header_s assembled_hdr;

    always_comb begin
        assembled_hdr.tdisp_version = hdr_byte_buf[0];
        assembled_hdr.msg_type      = hdr_byte_buf[1];
        // Little-endian: byte 2=LSB, byte 3=MSB
        assembled_hdr.reserved      = {hdr_byte_buf[3], hdr_byte_buf[2]};
        // Little-endian: bytes 4..15 (byte 4 = LSB, byte 15 = MSB)
        assembled_hdr.interface_id  = {hdr_byte_buf[15], hdr_byte_buf[14],
                                       hdr_byte_buf[13], hdr_byte_buf[12],
                                       hdr_byte_buf[11], hdr_byte_buf[10],
                                       hdr_byte_buf[9],  hdr_byte_buf[8],
                                       hdr_byte_buf[7],  hdr_byte_buf[6],
                                       hdr_byte_buf[5],  hdr_byte_buf[4]};
    end

    // =========================================================================
    // Build encoder header buffer - combinational (inlined, no ref argument)
    // =========================================================================
    logic [7:0] enc_hdr_buf_next [HDR_BYTES-1:0];

    always_comb begin
        enc_hdr_buf_next[0]  = negotiated_version;
        enc_hdr_buf_next[1]  = resp_msg_type;
        enc_hdr_buf_next[2]  = 8'd0;  // Reserved LSB
        enc_hdr_buf_next[3]  = 8'd0;  // Reserved MSB
        // INTERFACE_ID: 96 bits = 12 bytes, little-endian (byte 4 = LSB)
        enc_hdr_buf_next[4]  = resp_interface_id[7:0];
        enc_hdr_buf_next[5]  = resp_interface_id[15:8];
        enc_hdr_buf_next[6]  = resp_interface_id[23:16];
        enc_hdr_buf_next[7]  = resp_interface_id[31:24];
        enc_hdr_buf_next[8]  = resp_interface_id[39:32];
        enc_hdr_buf_next[9]  = resp_interface_id[47:40];
        enc_hdr_buf_next[10] = resp_interface_id[55:48];
        enc_hdr_buf_next[11] = resp_interface_id[63:56];
        enc_hdr_buf_next[12] = resp_interface_id[71:64];
        enc_hdr_buf_next[13] = resp_interface_id[79:72];
        enc_hdr_buf_next[14] = resp_interface_id[87:80];
        enc_hdr_buf_next[15] = resp_interface_id[95:88];
    end

    // =========================================================================
    // Parser State Machine
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            parse_state          <= PARSE_IDLE;
            hdr_byte_cnt         <= '0;
            payload_byte_cnt     <= '0;
            expected_payload_len <= '0;
            parsed_valid         <= 1'b0;
            parsed_error         <= 1'b0;
            parsed_payload_len   <= '0;
            for (int i = 0; i < HDR_BYTES; i++) begin
                hdr_byte_buf[i] <= 8'd0;
            end
            for (int i = 0; i < MAX_REPORT_SIZE; i++) begin
                parsed_payload[i] <= 8'd0;
            end
        end else begin
            parsed_valid <= 1'b0;
            parsed_error <= 1'b0;

            case (parse_state)
                // -------------------------------------------------------------
                // PARSE_IDLE: Wait for first byte of a new message
                // -------------------------------------------------------------
                PARSE_IDLE: begin
                    if (rx_valid && rx_ready) begin
                        hdr_byte_buf[0] <= rx_data;
                        hdr_byte_cnt    <= CNT_WIDTH'(1);
                        parse_state     <= PARSE_HDR;
                    end
                end

                // -------------------------------------------------------------
                // PARSE_HDR: Accumulate bytes 0..15 of the message header
                //   Validate fields as they arrive:
                //     Byte 0: TDISPVersion
                //     Byte 1: MessageType
                //     Bytes 2-3: Reserved (must be 0)
                //     Bytes 4-15: INTERFACE_ID
                // -------------------------------------------------------------
                PARSE_HDR: begin
                    if (rx_valid && rx_ready) begin
                        hdr_byte_buf[hdr_byte_cnt] <= rx_data;

                        // Early validation on byte 1 (MessageType)
                        if (hdr_byte_cnt == CNT_WIDTH'(1)) begin
                            if (!is_known_req_code(rx_data)) begin
                                parse_state  <= PARSE_ERROR;
                                parsed_error <= 1'b1;
                            end
                        end

                        // Validate reserved bytes (must be 0)
                        if (hdr_byte_cnt == CNT_WIDTH'(2) && rx_data != 8'd0) begin
                            parse_state  <= PARSE_ERROR;
                            parsed_error <= 1'b1;
                        end
                        if (hdr_byte_cnt == CNT_WIDTH'(3) && rx_data != 8'd0) begin
                            parse_state  <= PARSE_ERROR;
                            parsed_error <= 1'b1;
                        end

                        // Check if this is the last header byte (byte 15)
                        if (hdr_byte_cnt == CNT_WIDTH'(HDR_BYTES - 1)) begin
                            // Header complete - compute expected payload length.
                            // Note: hdr_byte_buf[1] already holds msg_type from
                            // an earlier cycle. The current rx_data goes to buf[15]
                            // (INTERFACE_ID MSB), so using hdr_byte_buf[1] is safe.
                            expected_payload_len <= expected_payload_length(hdr_byte_buf[1]);

                            if (expected_payload_length(hdr_byte_buf[1]) == 16'd0) begin
                                // No payload - go directly to DONE
                                parse_state <= PARSE_DONE;
                            end else begin
                                parse_state      <= PARSE_PAYLOAD;
                                payload_byte_cnt <= '0;
                            end
                        end

                        hdr_byte_cnt <= hdr_byte_cnt + CNT_WIDTH'(1);
                    end
                end

                // -------------------------------------------------------------
                // PARSE_PAYLOAD: Accumulate payload bytes
                //   For VDM (variable length), terminate on rx_last.
                //   For fixed-length, terminate when expected count reached.
                // -------------------------------------------------------------
                PARSE_PAYLOAD: begin
                    if (rx_valid && rx_ready) begin
                        if (payload_byte_cnt < CNT_WIDTH'(MAX_REPORT_SIZE)) begin
                            parsed_payload[payload_byte_cnt] <= rx_data;
                        end
                        payload_byte_cnt <= payload_byte_cnt + CNT_WIDTH'(1);

                        // Check termination conditions
                        if (expected_payload_len == 16'hFFFF) begin
                            // VDM - variable length, end on rx_last
                            if (rx_last) begin
                                parsed_payload_len <= payload_byte_cnt[15:0] + 16'd1;
                                parse_state        <= PARSE_DONE;
                            end
                        end else begin
                            // Fixed-length payload
                            if (payload_byte_cnt == CNT_WIDTH'(expected_payload_len) - CNT_WIDTH'(1)) begin
                                parsed_payload_len <= expected_payload_len;
                                parse_state        <= PARSE_DONE;
                            end
                        end
                    end
                end

                // -------------------------------------------------------------
                // PARSE_DONE: Emit parsed_valid, latch header, return to IDLE
                // -------------------------------------------------------------
                PARSE_DONE: begin
                    parsed_hdr         <= assembled_hdr;
                    parsed_valid       <= 1'b1;
                    parse_state        <= PARSE_IDLE;
                    hdr_byte_cnt       <= '0;
                    payload_byte_cnt   <= '0;
                end

                // -------------------------------------------------------------
                // PARSE_ERROR: Drain bad message, return to IDLE
                //   Wait for rx_last or for data to stop before accepting new.
                // -------------------------------------------------------------
                PARSE_ERROR: begin
                    if (rx_valid && rx_ready && rx_last) begin
                        parse_state <= PARSE_IDLE;
                    end else if (!rx_valid) begin
                        parse_state <= PARSE_IDLE;
                    end
                end

                default: parse_state <= PARSE_IDLE;
            endcase
        end
    end

    // Parser ready: accept data when in IDLE, HDR, or PAYLOAD states
    always_comb begin
        case (parse_state)
            PARSE_IDLE, PARSE_HDR, PARSE_PAYLOAD: rx_ready = 1'b1;
            default: rx_ready = 1'b0;
        endcase
    end

    // =========================================================================
    // Encoder State Machine
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            enc_state         <= ENC_IDLE;
            enc_hdr_idx       <= '0;
            enc_payload_idx   <= '0;
            enc_payload_total <= '0;
            enc_accepted      <= 1'b0;
            tx_valid          <= 1'b0;
            tx_data           <= '0;
            tx_last           <= 1'b0;
            resp_ready        <= 1'b0;
            for (int i = 0; i < HDR_BYTES; i++) begin
                enc_hdr_buf[i] <= 8'd0;
            end
        end else begin
            tx_valid   <= 1'b0;
            tx_last    <= 1'b0;
            resp_ready <= 1'b0;

            case (enc_state)
                // -------------------------------------------------------------
                // ENC_IDLE: Wait for resp_valid handshake
                // -------------------------------------------------------------
                ENC_IDLE: begin
                    if (resp_valid && !enc_accepted) begin
                        // Capture response header from combinational logic
                        for (int i = 0; i < HDR_BYTES; i++) begin
                            enc_hdr_buf[i] <= enc_hdr_buf_next[i];
                        end
                        enc_payload_total <= CNT_WIDTH'(resp_payload_len);
                        enc_accepted      <= 1'b1;
                        enc_hdr_idx       <= '0;
                        enc_payload_idx   <= '0;
                        enc_state         <= ENC_HDR;
                        resp_ready        <= 1'b1;  // Acknowledge acceptance
                    end
                end

                // -------------------------------------------------------------
                // ENC_HDR: Transmit header bytes [0..15]
                // -------------------------------------------------------------
                ENC_HDR: begin
                    tx_valid <= 1'b1;
                    tx_data  <= enc_hdr_buf[enc_hdr_idx];

                    if (tx_ready) begin
                        if (enc_hdr_idx == CNT_WIDTH'(HDR_BYTES - 1)) begin
                            // Header sent completely
                            if (enc_payload_total == '0) begin
                                // No payload - send tx_last and finish
                                tx_last    <= 1'b1;
                                enc_state  <= ENC_DONE;
                            end else begin
                                enc_payload_idx <= '0;
                                enc_state       <= ENC_PAYLOAD;
                            end
                        end else begin
                            enc_hdr_idx <= enc_hdr_idx + CNT_WIDTH'(1);
                        end
                    end
                end

                // -------------------------------------------------------------
                // ENC_PAYLOAD: Transmit payload bytes
                // -------------------------------------------------------------
                ENC_PAYLOAD: begin
                    tx_valid <= 1'b1;
                    tx_data  <= resp_payload[enc_payload_idx];

                    if (tx_ready) begin
                        if (enc_payload_idx == enc_payload_total - CNT_WIDTH'(1)) begin
                            // Last payload byte
                            tx_last    <= 1'b1;
                            enc_state  <= ENC_DONE;
                        end else begin
                            enc_payload_idx <= enc_payload_idx + CNT_WIDTH'(1);
                        end
                    end
                end

                // -------------------------------------------------------------
                // ENC_DONE: Reset for next response
                // -------------------------------------------------------------
                ENC_DONE: begin
                    enc_accepted <= 1'b0;
                    enc_state    <= ENC_IDLE;
                end

                default: enc_state <= ENC_IDLE;
            endcase
        end
    end

    // =========================================================================
    // Assertions
    // =========================================================================
    // pragma synthesis_off
    `ifdef FORMAL
        // Assert: encoder tx_last only with tx_valid
        assert property (@(posedge clk) disable iff (!rst_n)
            tx_last |-> tx_valid)
        else $error("tx_last asserted without tx_valid");

        // Assert: parsed_valid and parsed_error are mutually exclusive
        assert property (@(posedge clk) disable iff (!rst_n)
            !(parsed_valid && parsed_error))
        else $error("parsed_valid and parsed_error both asserted");

        // Assert: payload_len never exceeds MAX_REPORT_SIZE on valid output
        assert property (@(posedge clk) disable iff (!rst_n)
            parsed_valid |-> parsed_payload_len <= MAX_REPORT_SIZE)
        else $error("parsed_payload_len exceeds MAX_REPORT_SIZE");

        // Cover: a complete parse cycle
        cover property (@(posedge clk) disable iff (!rst_n)
            parse_state == PARSE_IDLE ##1 parse_state == PARSE_HDR ##1
            parse_state == PARSE_DONE ##1 parse_state == PARSE_IDLE);

        // Cover: a complete encode cycle
        cover property (@(posedge clk) disable iff (!rst_n)
            enc_state == ENC_IDLE ##1 enc_state == ENC_HDR ##1
            enc_state == ENC_DONE ##1 enc_state == ENC_IDLE);
    `endif
    // pragma synthesis_on

endmodule : tdisp_msg_codec
