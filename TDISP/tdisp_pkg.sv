// ============================================================================
// Module:    tdisp_pkg.sv
// Purpose:   TDISP (TEE Device Interface Security Protocol) RTL Package
//            Constants, enums, structs, parameters per PCIe 7.0 Spec Chapter 11
// Spec:      PCI Express Base Specification Revision 7.0, Section 11.3
// ============================================================================

package tdisp_pkg;

    // =========================================================================
    // TDISP Protocol Version (Section 11.3.3)
    // Bits [7:4] = Major Version, Bits [3:0] = Minor Version
    // V1.0 = 8'h10
    // =========================================================================
    localparam logic [7:0] TDISP_VERSION_1_0 = 8'h10;

    // =========================================================================
    // TDI State Encoding (Section 11.3.13, Table 11-18)
    // CONFIG_UNLOCKED = 0, CONFIG_LOCKED = 1, RUN = 2, ERROR = 3
    // =========================================================================
    typedef enum logic [1:0] {
        TDI_STATE_CONFIG_UNLOCKED = 2'h0,
        TDI_STATE_CONFIG_LOCKED   = 2'h1,
        TDI_STATE_RUN             = 2'h2,
        TDI_STATE_ERROR           = 2'h3
    } tdisp_tdi_state_e;

    // =========================================================================
    // TDI State Width constant
    // =========================================================================
    localparam int TDI_STATE_WIDTH = 2;

    // =========================================================================
    // TDISP Request Codes (Table 11-4)
    // =========================================================================
    typedef enum logic [7:0] {
        REQ_GET_TDISP_VERSION           = 8'h81,
        REQ_GET_TDISP_CAPABILITIES      = 8'h82,
        REQ_LOCK_INTERFACE              = 8'h83,
        REQ_GET_DEVICE_INTERFACE_REPORT = 8'h84,
        REQ_GET_DEVICE_INTERFACE_STATE  = 8'h85,
        REQ_START_INTERFACE             = 8'h86,
        REQ_STOP_INTERFACE              = 8'h87,
        REQ_BIND_P2P_STREAM             = 8'h88,
        REQ_UNBIND_P2P_STREAM           = 8'h89,
        REQ_SET_MMIO_ATTRIBUTE          = 8'h8A,
        REQ_VDM                         = 8'h8B,
        REQ_SET_TDISP_CONFIG            = 8'h8C
    } tdisp_req_code_e;

    // =========================================================================
    // TDISP Response Codes (Table 11-5)
    // =========================================================================
    typedef enum logic [7:0] {
        RESP_TDISP_VERSION            = 8'h01,
        RESP_TDISP_CAPABILITIES       = 8'h02,
        RESP_LOCK_INTERFACE           = 8'h03,
        RESP_DEVICE_INTERFACE_REPORT  = 8'h04,
        RESP_DEVICE_INTERFACE_STATE   = 8'h05,
        RESP_START_INTERFACE          = 8'h06,
        RESP_STOP_INTERFACE           = 8'h07,
        RESP_BIND_P2P_STREAM          = 8'h08,
        RESP_UNBIND_P2P_STREAM        = 8'h09,
        RESP_SET_MMIO_ATTRIBUTE       = 8'h0A,
        RESP_VDM                      = 8'h0B,
        RESP_SET_TDISP_CONFIG         = 8'h0C,
        RESP_TDISP_ERROR              = 8'h7F
    } tdisp_resp_code_e;

    // =========================================================================
    // TDISP Error Codes (Table 11-28)
    // =========================================================================
    typedef enum logic [15:0] {
        ERR_RESERVED                    = 16'h0000,
        ERR_INVALID_REQUEST             = 16'h0001,
        ERR_BUSY                        = 16'h0003,
        ERR_INVALID_INTERFACE_STATE     = 16'h0004,
        ERR_UNSPECIFIED                 = 16'h0005,
        ERR_UNSUPPORTED_REQUEST         = 16'h0007,
        ERR_VERSION_MISMATCH            = 16'h0041,
        ERR_VENDOR_SPECIFIC_ERROR       = 16'h00FF,
        ERR_INVALID_INTERFACE           = 16'h0101,
        ERR_INVALID_NONCE               = 16'h0102,
        ERR_INSUFFICIENT_ENTROPY        = 16'h0103,
        ERR_INVALID_DEVICE_CONFIGURATION = 16'h0104
    } tdisp_error_code_e;

    // =========================================================================
    // Message Header Constants (Table 11-6)
    // =========================================================================
    localparam int TDISP_MSG_HEADER_SIZE    = 16;   // bytes
    localparam int INTERFACE_ID_WIDTH       = 96;   // bits (12 bytes)
    localparam int NONCE_WIDTH              = 256;  // bits (32 bytes)

    // Header field offsets (bytes)
    localparam int TDISP_HDR_VER_OFFSET     = 0;
    localparam int TDISP_HDR_MSGTYPE_OFFSET = 1;
    localparam int TDISP_HDR_RESERVED_OFFSET= 2;
    localparam int TDISP_HDR_IFACE_ID_OFFSET= 4;
    localparam int TDISP_HDR_PAYLOAD_OFFSET = 16;

    // =========================================================================
    // SPDM Protocol ID for TDISP
    // =========================================================================
    localparam logic [7:0] SPDM_PROTOCOL_ID = 8'h01;

    // =========================================================================
    // Message Header Struct (Table 11-6)
    // =========================================================================
    typedef struct packed {
        logic [7:0]                tdisp_version;  // Offset 0
        logic [7:0]                msg_type;       // Offset 1
        logic [15:0]               reserved;       // Offset 2
        logic [INTERFACE_ID_WIDTH-1:0] interface_id; // Offset 4 (96 bits)
    } tdisp_msg_header_s;

    // =========================================================================
    // Lock Interface Flags (Table 11-11 FLAGS field)
    // =========================================================================
    typedef struct packed {
        logic        no_fw_update;           // Bit 0
        logic        sys_cache_line_size;    // Bit 1: 0=64B, 1=128B
        logic        lock_msix;             // Bit 2
        logic        bind_p2p;              // Bit 3
        logic        all_request_redirect;  // Bit 4
        logic [10:0] reserved_flags;        // Bits 15:5
    } tdisp_lock_flags_s;

    // =========================================================================
    // LOCK_INTERFACE_REQUEST Payload (Table 11-11)
    // =========================================================================
    typedef struct packed {
        logic [15:0] flags;                  // Offset 16
        logic [7:0]  default_stream_id;      // Offset 18
        logic [7:0]  reserved_byte;          // Offset 19
        logic [63:0] mmio_reporting_offset;  // Offset 20
        logic [63:0] bind_p2p_addr_mask;     // Offset 28
    } tdisp_lock_req_payload_s;

    // =========================================================================
    // INTERFACE_INFO in Device Interface Report (Table 11-16)
    // =========================================================================
    typedef struct packed {
        logic        no_fw_update;        // Bit 0
        logic        dma_without_pasid;   // Bit 1
        logic        dma_with_pasid;      // Bit 2
        logic        ats_enabled;         // Bit 3
        logic        prs_enabled;         // Bit 4
        logic        xt_mode_enabled;     // Bit 5
        logic [9:0]  reserved_info;       // Bits 15:6
    } tdisp_interface_report_info_s;

    // =========================================================================
    // MMIO Range Entry in Device Interface Report (Table 11-16)
    // =========================================================================
    typedef struct packed {
        logic [63:0] first_page_with_offset; // 8 bytes
        logic [31:0] num_4k_pages;           // 4 bytes
        logic        is_msix_table;          // Range attrs bit 0
        logic        is_msix_pba;            // Range attrs bit 1
        logic        is_non_tee_mem;         // Range attrs bit 2
        logic        is_mem_attr_updatable;  // Range attrs bit 3
        logic [11:0] reserved_range;         // Range attrs bits 15:4
        logic [15:0] range_id;               // Range attrs bits 31:16
    } tdisp_mmio_range_s;

    // =========================================================================
    // TDISP_CAPABILITIES Response Payload (Table 11-10)
    // =========================================================================
    typedef struct packed {
        logic          xt_mode_supported;     // DSM_CAPS bit 0
        logic [30:0]   dsm_caps_reserved;     // DSM_CAPS bits 31:1
        logic [127:0]  req_msgs_supported;     // 16-byte bitmask
        logic [15:0]   lock_iface_flags_supported; // 2 bytes
        logic [23:0]   caps_reserved;          // 3 bytes reserved
        logic [7:0]    dev_addr_width;         // 1 byte
        logic [7:0]    num_req_this;           // 1 byte
        logic [7:0]    num_req_all;            // 1 byte
    } tdisp_caps_s;

    // =========================================================================
    // SET_TDISP_CONFIG_REQUEST Payload (Section 11.3.27)
    // =========================================================================
    typedef struct packed {
        logic        xt_mode_enable;           // Bit 0
        logic        xt_bit_for_locked_msix;   // Bit 1
        logic [29:0] reserved_config;          // Bits 31:2
    } tdisp_set_config_req_s;

    // =========================================================================
    // DEVICE_INTERFACE_STATE Response Payload (Table 11-18)
    // =========================================================================
    typedef struct packed {
        logic [7:0] tdi_state;  // TDI_STATE byte
    } tdisp_iface_state_resp_s;

    // =========================================================================
    // TDISP_ERROR Response Payload (Table 11-27)
    // =========================================================================
    typedef struct packed {
        logic [31:0] error_code;    // 4 bytes at offset 16
        logic [31:0] error_data;    // 4 bytes at offset 20
        // EXTENDED_ERROR_DATA is variable length, handled separately
    } tdisp_error_resp_s;

    // =========================================================================
    // GET_DEVICE_INTERFACE_REPORT Request Payload (Table 11-14)
    // =========================================================================
    typedef struct packed {
        logic [15:0] offset;  // Offset 16: byte offset into report
        logic [15:0] length;  // Offset 18: requested length in bytes
    } tdisp_get_report_req_s;

    // =========================================================================
    // DEVICE_INTERFACE_REPORT Response Header (Table 11-15)
    // =========================================================================
    typedef struct packed {
        logic [15:0] portion_length;    // Offset 16
        logic [15:0] remainder_length;  // Offset 18
    } tdisp_report_resp_header_s;

    // =========================================================================
    // BIND_P2P_STREAM_REQUEST Payload (Section 11.3.18)
    // =========================================================================
    typedef struct packed {
        logic [7:0]  stream_id;        // Offset 16
        logic [7:0]  reserved_bind;    // Offset 17
        logic [15:0] p2p_portion;      // Offset 18: P2P portion of address
    } tdisp_bind_p2p_req_s;

    // =========================================================================
    // UNBIND_P2P_STREAM_REQUEST Payload (Section 11.3.20)
    // =========================================================================
    typedef struct packed {
        logic [7:0] stream_id;       // Offset 16
    } tdisp_unbind_p2p_req_s;

    // =========================================================================
    // SET_MMIO_ATTRIBUTE_REQUEST Payload (Section 11.3.22)
    // =========================================================================
    typedef struct packed {
        logic [63:0] start_addr;     // Offset 16: starting address
        logic [31:0] num_4k_pages;   // Offset 24: number of 4K pages
        logic        is_non_tee_mem; // Attribute bit
        logic [30:0] reserved_attr;  // Reserved attribute bits
    } tdisp_set_mmio_attr_req_s;

    // =========================================================================
    // Configurable Design Parameters
    // =========================================================================
    localparam int MAX_NUM_TDI      = 16;  // Max TDI instances
    localparam int MAX_P2P_STREAMS  = 8;   // Max P2P streams per TDI
    localparam int MAX_MMIO_RANGES  = 32;  // Max MMIO ranges per TDI
    localparam int MAX_REPORT_SIZE  = 4096; // Max report size in bytes

    // =========================================================================
    // TDI Index Width (log2 of MAX_NUM_TDI)
    // =========================================================================
    localparam int TDI_INDEX_WIDTH = 4;

    // =========================================================================
    // Function: tdisp_state_is_legal_for_req
    //   Returns 1 if the given request code is legal in the given TDI state
    //   per Table 11-4 legal states mapping
    // =========================================================================
    function automatic logic tdisp_state_is_legal_for_req(
        input logic [7:0]           req_code,
        input tdisp_tdi_state_e     current_state
    );
        case (req_code)
            REQ_GET_TDISP_VERSION:           return 1'b1; // N/A - all states
            REQ_GET_TDISP_CAPABILITIES:      return 1'b1; // N/A - all states
            REQ_LOCK_INTERFACE:              return (current_state == TDI_STATE_CONFIG_UNLOCKED);
            REQ_GET_DEVICE_INTERFACE_REPORT: return (current_state == TDI_STATE_CONFIG_LOCKED) ||
                                                   (current_state == TDI_STATE_RUN);
            REQ_GET_DEVICE_INTERFACE_STATE:  return 1'b1; // All states
            REQ_START_INTERFACE:             return (current_state == TDI_STATE_CONFIG_LOCKED);
            REQ_STOP_INTERFACE:              return 1'b1; // All states
            REQ_BIND_P2P_STREAM:             return (current_state == TDI_STATE_RUN);
            REQ_UNBIND_P2P_STREAM:           return (current_state == TDI_STATE_RUN);
            REQ_SET_MMIO_ATTRIBUTE:          return (current_state == TDI_STATE_RUN);
            REQ_VDM:                         return 1'b1; // N/A - all states
            REQ_SET_TDISP_CONFIG:            return (current_state == TDI_STATE_CONFIG_UNLOCKED);
            default:                         return 1'b0; // Unknown request
        endcase
    endfunction

    // =========================================================================
    // Function: tdisp_resp_code_for_req
    //   Returns the expected success response code for a given request code
    // =========================================================================
    function automatic logic [7:0] tdisp_resp_code_for_req(
        input logic [7:0] req_code
    );
        case (req_code)
            REQ_GET_TDISP_VERSION:           return RESP_TDISP_VERSION;
            REQ_GET_TDISP_CAPABILITIES:      return RESP_TDISP_CAPABILITIES;
            REQ_LOCK_INTERFACE:              return RESP_LOCK_INTERFACE;
            REQ_GET_DEVICE_INTERFACE_REPORT: return RESP_DEVICE_INTERFACE_REPORT;
            REQ_GET_DEVICE_INTERFACE_STATE:  return RESP_DEVICE_INTERFACE_STATE;
            REQ_START_INTERFACE:             return RESP_START_INTERFACE;
            REQ_STOP_INTERFACE:              return RESP_STOP_INTERFACE;
            REQ_BIND_P2P_STREAM:             return RESP_BIND_P2P_STREAM;
            REQ_UNBIND_P2P_STREAM:           return RESP_UNBIND_P2P_STREAM;
            REQ_SET_MMIO_ATTRIBUTE:          return RESP_SET_MMIO_ATTRIBUTE;
            REQ_VDM:                         return RESP_VDM;
            REQ_SET_TDISP_CONFIG:            return RESP_SET_TDISP_CONFIG;
            default:                         return RESP_TDISP_ERROR;
        endcase
    endfunction

endpackage : tdisp_pkg
