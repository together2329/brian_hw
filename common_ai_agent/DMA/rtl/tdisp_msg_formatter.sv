//============================================================================
// TDISP Message Formatter
// Builds TDISP response messages for transmission to TSM via SPDM transport
// Supports all response types per PCIe Base Spec Rev 7.0, Chapter 11
//============================================================================

module tdisp_msg_formatter #(
    parameter int unsigned DATA_WIDTH       = 32,
    parameter int unsigned NUM_TDI          = 4,
    parameter int unsigned ADDR_WIDTH       = 64,   // Device address width
    parameter int unsigned MAX_OUTSTANDING  = 8
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //--- Response build request interface ---
    input  logic                            build_req_i,             // Strobe to build a response
    input  tdisp_types::tdisp_rsp_code_e    rsp_type_i,              // Which response to build
    input  logic [95:0]                     interface_id_i,          // INTERFACE_ID for header
    input  logic [$clog2(NUM_TDI)-1:0]      tdi_index_i,             // TDI index for context

    //--- TDI state input (for DEVICE_INTERFACE_STATE) ---
    input  tdisp_types::tdisp_state_e       tdi_state_i,

    //--- TDISP_VERSION specific inputs ---
    input  logic [7:0]                      version_count_i,         // Number of version entries
    input  logic [255:0]                    version_entries_i,       // Version entry array

    //--- TDISP_CAPABILITIES specific inputs ---
    input  logic                            xt_mode_supported_i,     // DSM caps: XT mode
    input  logic [127:0]                    req_msgs_supported_i,    // Supported request bitmask
    input  logic [15:0]                     lock_iface_flags_sup_i,  // Supported lock flags
    input  logic [7:0]                      dev_addr_width_i,        // Device address width
    input  logic [7:0]                      num_req_this_i,          // Outstanding reqs per TDI
    input  logic [7:0]                      num_req_all_i,           // Outstanding reqs total

    //--- LOCK_INTERFACE_RESPONSE specific inputs ---
    input  logic [255:0]                    start_interface_nonce_i, // 32-byte nonce
    input  logic                            nonce_valid_i,           // Nonce was generated OK

    //--- DEVICE_INTERFACE_REPORT specific inputs ---
    input  logic [ADDR_WIDTH-1:0]           mmio_base_addr_i,        // MMIO base (with offset)
    input  logic [31:0]                     mmio_num_pages_i,        // Number of 4K pages
    input  logic                            mmio_is_non_tee_i,       // IS_NON_TEE_MEM flag
    input  logic                            mmio_valid_i,            // MMIO report data valid

    //--- START/STOP INTERFACE specific inputs ---
    // (no extra inputs needed beyond rsp_type and interface_id)

    //--- BIND/UNBIND P2P specific inputs ---
    input  logic [7:0]                      p2p_stream_id_i,         // P2P stream ID

    //--- SET_MMIO_ATTRIBUTE specific inputs ---
    // (response is just ack, no extra inputs)

    //--- TDISP_ERROR specific inputs ---
    input  tdisp_types::tdisp_error_code_e  error_code_i,            // Error code
    input  logic [31:0]                     error_data_i,            // Error data

    //--- AXI-Stream output to SPDM/DOE transport ---
    output logic [DATA_WIDTH-1:0]           m_axis_tdata,
    output logic [DATA_WIDTH/8-1:0]         m_axis_tkeep,
    output logic                            m_axis_tlast,
    output logic                            m_axis_tvalid,
    input  logic                            m_axis_tready,

    //--- Status ---
    output logic                            build_done_o,            // Response fully transmitted
    output logic                            build_error_o            // Build error (cannot generate)
);

    import tdisp_types::*;

    //==========================================================================
    // Local parameters
    //==========================================================================
    localparam int unsigned BYTES_PER_BEAT = DATA_WIDTH / 8;
    localparam int unsigned HDR_BITS       = TDISP_HDR_SIZE * 8; // 128 bits

    //==========================================================================
    // Formatter FSM states
    //==========================================================================
    typedef enum logic [2:0] {
        FMT_IDLE,
        FMT_HDR,
        FMT_PAYLOAD,
        FMT_COMPLETE
    } fmt_state_e;

    //==========================================================================
    // Internal registers
    //==========================================================================
    fmt_state_e          state_q;
    logic [15:0]         byte_cnt_q;
    tdisp_rsp_code_e     rsp_type_q;
    logic [95:0]         iface_id_q;
    logic [15:0]         total_len_q;

    // Header staging buffer (128 bits = 16 bytes)
    logic [HDR_BITS-1:0] hdr_buf;

    // Payload staging buffer
    logic [DATA_WIDTH-1:0]  payload_buf;
    logic [DATA_WIDTH/8-1:0] payload_keep;
    logic                   payload_last;

    // Pre-computed payload length
    logic [15:0]         payload_len;

    //==========================================================================
    // Calculate total message length based on response type
    //==========================================================================
    always_comb begin
        payload_len = 16'd0;
        case (rsp_type_q)
            RSP_TDISP_VERSION: begin
                payload_len = 16'd1 + version_count_i; // count + entries
            end
            RSP_TDISP_CAPABILITIES: begin
                payload_len = 16'd28; // DSM_CAPS(4)+REQ_MSGS(16)+LOCK_FLAGS(2)+Rsvd(3)+ADDR_W(1)+NUM_THIS(1)+NUM_ALL(1)
            end
            RSP_LOCK_INTERFACE: begin
                payload_len = 16'd32; // START_INTERFACE_NONCE
            end
            RSP_DEVICE_INTERFACE_REPORT: begin
                payload_len = 16'd12; // Variable - simplified: 1 MMIO range entry
            end
            RSP_DEVICE_INTERFACE_STATE: begin
                payload_len = 16'd4; // State field + reserved
            end
            RSP_START_INTERFACE: begin
                payload_len = 16'd0; // No payload
            end
            RSP_STOP_INTERFACE: begin
                payload_len = 16'd0; // No payload
            end
            RSP_BIND_P2P_STREAM: begin
                payload_len = 16'd0; // No payload
            end
            RSP_UNBIND_P2P_STREAM: begin
                payload_len = 16'd0; // No payload
            end
            RSP_SET_MMIO_ATTRIBUTE: begin
                payload_len = 16'd0; // No payload
            end
            RSP_VDM: begin
                payload_len = 16'd0; // Variable - placeholder
            end
            RSP_SET_TDISP_CONFIG: begin
                payload_len = 16'd0; // No payload
            end
            RSP_TDISP_ERROR: begin
                payload_len = 16'd8; // ERROR_CODE(4)+ERROR_DATA(4)
            end
            default: payload_len = 16'd0;
        endcase
    end

    //==========================================================================
    // Build the 16-byte TDISP header
    // Layout: Version(1) + MsgType(1) + Reserved(2) + INTERFACE_ID(12)
    //==========================================================================
    always_comb begin
        hdr_buf[7:0]   = TDISP_VERSION_1_0;           // Offset 0: TDISPVersion
        hdr_buf[15:8]  = rsp_type_q;                   // Offset 1: MessageType
        hdr_buf[31:16] = 16'd0;                        // Offset 2-3: Reserved
        hdr_buf[39:32] = iface_id_q[7:0];              // Offset 4: INTERFACE_ID byte 0
        hdr_buf[47:40] = iface_id_q[15:8];             // Offset 5
        hdr_buf[55:48] = iface_id_q[23:16];            // Offset 6
        hdr_buf[63:56] = iface_id_q[31:24];            // Offset 7
        hdr_buf[71:64] = iface_id_q[39:32];            // Offset 8
        hdr_buf[79:72] = iface_id_q[47:40];            // Offset 9
        hdr_buf[87:80] = iface_id_q[55:48];            // Offset 10
        hdr_buf[95:88] = iface_id_q[63:56];            // Offset 11
        hdr_buf[103:96]  = iface_id_q[71:64];          // Offset 12
        hdr_buf[111:104] = iface_id_q[79:72];          // Offset 13
        hdr_buf[119:112] = iface_id_q[87:80];          // Offset 14
        hdr_buf[127:120] = iface_id_q[95:88];          // Offset 15
    end

    //==========================================================================
    // Build payload data for current beat
    //==========================================================================
    always_comb begin
        payload_buf  = '0;
        payload_keep = '1;
        payload_last = 1'b0;

        case (rsp_type_q)
            //----------------------------------------------------------
            RSP_TDISP_VERSION: begin
                case (byte_cnt_q)
                    16'd16: begin // First payload byte
                        payload_buf[7:0] = version_count_i;
                    end
                    16'd20: begin // Version entries start at offset 17
                        payload_buf = version_entries_i[DATA_WIDTH-1:0];
                    end
                    default: begin
                        // Additional version entries if needed
                        payload_buf = version_entries_i[DATA_WIDTH-1:0];
                    end
                endcase
            end

            //----------------------------------------------------------
            RSP_TDISP_CAPABILITIES: begin
                case (byte_cnt_q)
                    16'd16: begin // DSM_CAPS at offset 16 (4 bytes)
                        payload_buf[0]     = xt_mode_supported_i;
                        payload_buf[31:1]  = '0;
                    end
                    16'd20: begin // REQ_MSGS_SUPPORTED at offset 20 (16 bytes)
                        payload_buf = req_msgs_supported_i[DATA_WIDTH-1:0];
                    end
                    16'd24: begin
                        payload_buf = req_msgs_supported_i[2*DATA_WIDTH-1:DATA_WIDTH];
                    end
                    16'd28: begin
                        payload_buf = req_msgs_supported_i[3*DATA_WIDTH-1:2*DATA_WIDTH];
                    end
                    16'd32: begin
                        payload_buf = req_msgs_supported_i[4*DATA_WIDTH-1:3*DATA_WIDTH];
                    end
                    16'd36: begin // LOCK_INTERFACE_FLAGS_SUPPORTED (2 bytes) + Reserved(3) + ADDR_W(1) + NUM(2)
                        payload_buf[15:0]  = lock_iface_flags_sup_i;
                        payload_buf[23:16] = '0;       // Reserved
                        payload_buf[31:24] = '0;       // Reserved (part)
                        payload_buf[39:32] = dev_addr_width_i;
                        payload_buf[47:40] = num_req_this_i;
                        payload_buf[55:48] = num_req_all_i;
                        payload_last = 1'b1;
                    end
                    default: begin
                        payload_buf = '0;
                    end
                endcase
            end

            //----------------------------------------------------------
            RSP_LOCK_INTERFACE: begin
                // 32-byte START_INTERFACE_NONCE at offset 16
                case (byte_cnt_q)
                    16'd16: payload_buf = start_interface_nonce_i[DATA_WIDTH-1:0];
                    16'd20: payload_buf = start_interface_nonce_i[2*DATA_WIDTH-1:DATA_WIDTH];
                    16'd24: payload_buf = start_interface_nonce_i[3*DATA_WIDTH-1:2*DATA_WIDTH];
                    16'd28: payload_buf = start_interface_nonce_i[4*DATA_WIDTH-1:3*DATA_WIDTH];
                    16'd32: payload_buf = start_interface_nonce_i[5*DATA_WIDTH-1:4*DATA_WIDTH];
                    16'd36: payload_buf = start_interface_nonce_i[6*DATA_WIDTH-1:5*DATA_WIDTH];
                    16'd40: payload_buf = start_interface_nonce_i[7*DATA_WIDTH-1:6*DATA_WIDTH];
                    16'd44: begin
                        payload_buf = start_interface_nonce_i[8*DATA_WIDTH-1:7*DATA_WIDTH];
                        payload_last = 1'b1;
                    end
                    default: payload_buf = '0;
                endcase
            end

            //----------------------------------------------------------
            RSP_DEVICE_INTERFACE_REPORT: begin
                // Simplified: single MMIO range entry
                case (byte_cnt_q)
                    16'd16: begin
                        // start_page_addr (8 bytes) with mmio_reporting_offset applied
                        payload_buf = mmio_base_addr_i[DATA_WIDTH-1:0];
                    end
                    16'd20: begin
                        payload_buf[31:0] = mmio_num_pages_i;
                        payload_buf[32]   = mmio_is_non_tee_i;
                        payload_buf[63:33]= '0;
                        payload_last = 1'b1;
                    end
                    default: payload_buf = '0;
                endcase
            end

            //----------------------------------------------------------
            RSP_DEVICE_INTERFACE_STATE: begin
                case (byte_cnt_q)
                    16'd16: begin
                        payload_buf[3:0]  = tdi_state_i;
                        payload_buf[7:4]  = '0;
                        payload_last = 1'b1;
                    end
                    default: payload_buf = '0;
                endcase
            end

            //----------------------------------------------------------
            RSP_TDISP_ERROR: begin
                case (byte_cnt_q)
                    16'd16: begin
                        payload_buf[31:0] = error_code_i;
                        payload_buf[63:32]= error_data_i;
                        payload_last = 1'b1;
                    end
                    default: payload_buf = '0;
                endcase
            end

            //----------------------------------------------------------
            // Simple response types with no payload (just header)
            RSP_START_INTERFACE,
            RSP_STOP_INTERFACE,
            RSP_BIND_P2P_STREAM,
            RSP_UNBIND_P2P_STREAM,
            RSP_SET_MMIO_ATTRIBUTE,
            RSP_SET_TDISP_CONFIG,
            RSP_VDM: begin
                payload_last = 1'b1;
            end

            default: begin
                payload_buf = '0;
            end
        endcase
    end

    //==========================================================================
    // Main formatting FSM
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q      <= FMT_IDLE;
            byte_cnt_q   <= '0;
            rsp_type_q   <= RSP_TDISP_ERROR;
            iface_id_q   <= '0;
            total_len_q  <= '0;
            m_axis_tdata <= '0;
            m_axis_tkeep <= '0;
            m_axis_tlast <= 1'b0;
            m_axis_tvalid<= 1'b0;
            build_done_o <= 1'b0;
            build_error_o<= 1'b0;
        end else begin
            m_axis_tvalid <= 1'b0;
            build_done_o  <= 1'b0;

            case (state_q)
                //----------------------------------------------------------
                FMT_IDLE: begin
                    build_error_o <= 1'b0;
                    if (build_req_i) begin
                        rsp_type_q  <= rsp_type_i;
                        iface_id_q  <= interface_id_i;
                        byte_cnt_q  <= '0;
                        total_len_q <= TDISP_HDR_SIZE + payload_len;
                        state_q     <= FMT_HDR;

                        // Special case: nonce generation failed for LOCK
                        if (rsp_type_i == RSP_LOCK_INTERFACE && !nonce_valid_i) begin
                            rsp_type_q  <= RSP_TDISP_ERROR;
                            build_error_o <= 1'b1;
                        end
                    end
                end

                //----------------------------------------------------------
                FMT_HDR: begin
                    if (m_axis_tready) begin
                        m_axis_tvalid <= 1'b1;
                        m_axis_tkeep  <= '1;

                        // Output header bytes based on DATA_WIDTH
                        if (DATA_WIDTH == 32) begin
                            case (byte_cnt_q[15:0])
                                16'd0: begin
                                    m_axis_tdata <= hdr_buf[31:0];
                                    byte_cnt_q   <= byte_cnt_q + BYTES_PER_BEAT;
                                end
                                16'd4: begin
                                    m_axis_tdata <= hdr_buf[63:32];
                                    byte_cnt_q   <= byte_cnt_q + BYTES_PER_BEAT;
                                end
                                16'd8: begin
                                    m_axis_tdata <= hdr_buf[95:64];
                                    byte_cnt_q   <= byte_cnt_q + BYTES_PER_BEAT;
                                end
                                16'd12: begin
                                    m_axis_tdata <= hdr_buf[127:96];
                                    byte_cnt_q   <= byte_cnt_q + BYTES_PER_BEAT;
                                    if (payload_len == 0) begin
                                        m_axis_tlast <= 1'b1;
                                        state_q      <= FMT_COMPLETE;
                                    end else begin
                                        state_q <= FMT_PAYLOAD;
                                    end
                                end
                                default: begin
                                    m_axis_tdata <= hdr_buf[31:0];
                                    byte_cnt_q   <= byte_cnt_q + BYTES_PER_BEAT;
                                end
                            endcase
                        end else begin // DATA_WIDTH >= 64
                            m_axis_tdata <= hdr_buf[DATA_WIDTH-1:0];
                            byte_cnt_q   <= 16'd16;
                            if (payload_len == 0) begin
                                m_axis_tlast <= 1'b1;
                                state_q      <= FMT_COMPLETE;
                            end else begin
                                state_q <= FMT_PAYLOAD;
                            end
                        end
                    end
                end

                //----------------------------------------------------------
                FMT_PAYLOAD: begin
                    if (m_axis_tready) begin
                        m_axis_tvalid <= 1'b1;
                        m_axis_tdata  <= payload_buf;
                        m_axis_tkeep  <= payload_keep;
                        m_axis_tlast  <= payload_last;

                        if (payload_last) begin
                            state_q <= FMT_COMPLETE;
                        end else begin
                            byte_cnt_q <= byte_cnt_q + BYTES_PER_BEAT;
                        end
                    end
                end

                //----------------------------------------------------------
                FMT_COMPLETE: begin
                    m_axis_tlast <= 1'b0;
                    m_axis_tvalid <= 1'b0;
                    build_done_o <= 1'b1;
                    state_q      <= FMT_IDLE;
                end

                default: state_q <= FMT_IDLE;
            endcase
        end
    end

endmodule : tdisp_msg_formatter
