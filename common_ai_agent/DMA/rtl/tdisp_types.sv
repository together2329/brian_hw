//============================================================================
// TDISP Types Package
// TEE Device Interface Security Protocol - Type Definitions
// Based on PCIe Base Specification Rev 7.0, Chapter 11
//============================================================================

package tdisp_types;

    //==========================================================================
    // Parameters / Constants
    //==========================================================================
    parameter int unsigned TDISP_VERSION_MAJOR    = 4'h1;
    parameter int unsigned TDISP_VERSION_MINOR    = 4'h0;
    parameter logic [7:0]   TDISP_VERSION_1_0     = 8'h10;

    parameter int unsigned INTERFACE_ID_WIDTH     = 96;  // 12 bytes
    parameter int unsigned INTERFACE_ID_BYTES     = 12;
    parameter int unsigned NONCE_WIDTH            = 256; // 32 bytes
    parameter int unsigned NONCE_BYTES            = 32;
    parameter int unsigned TDISP_HDR_SIZE         = 16;  // bytes (before payload)
    parameter int unsigned TDISP_VERSION_OFFSET   = 0;
    parameter int unsigned TDISP_MSGTYPE_OFFSET   = 1;
    parameter int unsigned TDISP_RESERVED_OFFSET  = 2;
    parameter int unsigned TDISP_IFACE_ID_OFFSET  = 4;
    parameter int unsigned TDISP_PAYLOAD_OFFSET   = 16;

    // SPDM Vendor Defined constants
    parameter logic [15:0] SPDM_STANDARD_ID_PCI_SIG = 16'h0001;
    parameter logic [15:0] SPDM_VENDOR_ID_PCI_SIG   = 16'h0001;
    parameter logic [7:0]  SPDM_PROTOCOL_ID_TDISP   = 8'h01;

    //==========================================================================
    // TDISP TDI States (Section 11.2)
    //==========================================================================
    typedef enum logic [1:0] {
        TDI_CONFIG_UNLOCKED = 2'b00,
        TDI_CONFIG_LOCKED   = 2'b01,
        TDI_RUN             = 2'b10,
        TDI_ERROR           = 2'b11
    } tdisp_state_e;

    //==========================================================================
    // TDISP Request Message Codes (Table 11-4)
    //==========================================================================
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

    //==========================================================================
    // TDISP Response Message Codes (Table 11-5)
    //==========================================================================
    typedef enum logic [7:0] {
        RSP_TDISP_VERSION               = 8'h01,
        RSP_TDISP_CAPABILITIES          = 8'h02,
        RSP_LOCK_INTERFACE              = 8'h03,
        RSP_DEVICE_INTERFACE_REPORT     = 8'h04,
        RSP_DEVICE_INTERFACE_STATE      = 8'h05,
        RSP_START_INTERFACE             = 8'h06,
        RSP_STOP_INTERFACE              = 8'h07,
        RSP_BIND_P2P_STREAM             = 8'h08,
        RSP_UNBIND_P2P_STREAM           = 8'h09,
        RSP_SET_MMIO_ATTRIBUTE          = 8'h0A,
        RSP_VDM                         = 8'h0B,
        RSP_SET_TDISP_CONFIG            = 8'h0C,
        RSP_TDISP_ERROR                 = 8'h7F
    } tdisp_rsp_code_e;

    //==========================================================================
    // TDISP Error Codes (Table 11-28)
    //==========================================================================
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
        ERR_INVALID_DEVICE_CONFIGURATION= 16'h0104
    } tdisp_error_code_e;

    //==========================================================================
    // XT Bit and T Bit Encodings (Table 11-1)
    //==========================================================================
    typedef enum logic {
        NON_TEE_ORIGINATOR  = 1'b0,
        TEE_ORIGINATOR      = 1'b1
    } tdisp_t_bit_e;

    typedef enum logic {
        XT_DISABLED = 1'b0,
        XT_ENABLED  = 1'b1
    } tdisp_xt_bit_e;

    typedef struct packed {
        logic xt_bit;
        logic t_bit;
    } tdisp_xt_t_bits_s;

    // Combined XT/T encoding meanings
    localparam logic [1:0] XT_T_NON_TEE          = 2'b00; // Non-TEE originator
    localparam logic [1:0] XT_T_TEE              = 2'b01; // TEE originator
    localparam logic [1:0] XT_T_TEE_NON_TEE_MEM  = 2'b10; // TEE originator, non-TEE memory only
    localparam logic [1:0] XT_T_TEE_TEE_MEM      = 2'b11; // TEE originator, TEE memory only

    //==========================================================================
    // TDISP Message Header (Table 11-6)
    //==========================================================================
    typedef struct packed {
        logic [7:0]  tdisp_version;   // Bits 7:4 = Major, Bits 3:0 = Minor
        logic [7:0]  message_type;    // Request or Response code
        logic [15:0] reserved;        // Must be 0
        logic [INTERFACE_ID_WIDTH-1:0] interface_id; // 96-bit TDI identifier
    } tdisp_msg_header_s;

    //==========================================================================
    // LOCK_INTERFACE_REQUEST Flags (Table 11-11, Offset 16)
    //==========================================================================
    typedef struct packed {
        logic        no_fw_update;           // Bit 0: Disable firmware updates
        logic        sys_cache_line_size;    // Bit 1: 0=64B, 1=128B
        logic        lock_msix;             // Bit 2: Lock MSI-X table and PBA
        logic        bind_p2p;              // Bit 3: Enable P2P support
        logic        all_request_redirect;  // Bit 4: Redirect ATS translated reqs
        logic [10:0] reserved;              // Bits 15:5
    } tdisp_lock_flags_s;

    //==========================================================================
    // LOCK_INTERFACE_REQUEST Payload (Table 11-11)
    //==========================================================================
    typedef struct packed {
        tdisp_lock_flags_s flags;           // 2 bytes at offset 16
        logic [7:0]        stream_id;       // 1 byte at offset 18: Default IDE stream
        logic [7:0]        reserved;        // 1 byte at offset 19
        logic [63:0]       mmio_reporting_offset; // 8 bytes at offset 20
        logic [63:0]       bind_p2p_addr_mask;    // 8 bytes at offset 28
    } tdisp_lock_req_payload_s;

    //==========================================================================
    // TDISP_CAPABILITIES Response Payload (Table 11-10)
    //==========================================================================
    typedef struct packed {
        logic        xt_mode_supported;     // Bit 0 of DSM_CAPS
        logic [31:1] reserved_caps;         // Bits 31:1
    } tdisp_dsm_caps_s;

    typedef struct packed {
        tdisp_dsm_caps_s  dsm_caps;             // 4 bytes at offset 16
        logic [127:0]     req_msgs_supported;   // 16 bytes at offset 20: bitmask
        logic [15:0]      lock_iface_flags_sup; // 2 bytes at offset 36
        logic [23:0]      reserved;             // 3 bytes at offset 38
        logic [7:0]       dev_addr_width;       // 1 byte at offset 41
        logic [7:0]       num_req_this;         // 1 byte at offset 42
        logic [7:0]       num_req_all;          // 1 byte at offset 43
    } tdisp_capabilities_s;

    //==========================================================================
    // TDISP_VERSION Response Payload (Table 11-8)
    //==========================================================================
    typedef struct packed {
        logic [7:0]            version_num_count; // N at offset 16
        logic [NONCE_BYTES*8-1:0] version_entries; // Up to 32 version entries
    } tdisp_version_payload_s;

    //==========================================================================
    // START_INTERFACE_REQUEST Payload
    //==========================================================================
    typedef struct packed {
        logic [NONCE_WIDTH-1:0] start_interface_nonce; // 32 bytes at offset 16
    } tdisp_start_req_payload_s;

    //==========================================================================
    // DEVICE_INTERFACE_STATE Response (Table 11-13)
    //==========================================================================
    typedef struct packed {
        logic [7:0]  tdisp_version;
        logic [7:0]  message_type;
        logic [15:0] reserved;
        logic [INTERFACE_ID_WIDTH-1:0] interface_id;
        logic [3:0]  iface_state;        // TDI state encoded
        logic [3:0]  reserved_state;
    } tdisp_iface_state_rsp_s;

    //==========================================================================
    // TDISP_ERROR Response (Table 11-27)
    //==========================================================================
    typedef struct packed {
        logic [31:0] error_code;           // 4 bytes at offset 16
        logic [31:0] error_data;           // 4 bytes at offset 20
        // Extended error data is variable length (not packed here)
    } tdisp_error_payload_s;

    //==========================================================================
    // SET_MMIO_ATTRIBUTE Range Entry
    //==========================================================================
    typedef struct packed {
        logic [63:0] start_page_addr;      // First 4K page with offset added
        logic [31:0] num_pages;            // Number of 4K pages
        logic        is_non_tee_mem;       // Bit 2: non-TEE memory flag
        logic [1:0]  range_id;            // Bits 1:0
        logic [28:0] reserved_attrs;       // Bits 31:3
    } tdisp_mmio_range_s;

    //==========================================================================
    // Per-TDI Context Structure (for tdisp_tdi_mgr)
    //==========================================================================
    typedef struct packed {
        tdisp_state_e                state;
        logic [INTERFACE_ID_WIDTH-1:0] interface_id;
        logic [7:0]                  bound_stream_id;
        logic [63:0]                 mmio_reporting_offset;
        tdisp_lock_flags_s           lock_flags;
        logic [NONCE_WIDTH-1:0]      nonce;
        logic                        nonce_valid;
        logic                        msix_locked;
        logic                        fw_update_locked;
        logic                        p2p_enabled;
        logic                        all_req_redirect;
        logic                        xt_mode_enabled;
        logic [7:0]                  outstanding_reqs;
    } tdisp_tdi_context_s;

    //==========================================================================
    // Message Direction
    //==========================================================================
    typedef enum logic {
        DIR_REQUEST  = 1'b0,
        DIR_RESPONSE = 1'b1
    } tdisp_msg_dir_e;

    //==========================================================================
    // Request Validation Result
    //==========================================================================
    typedef enum logic [1:0] {
        VALIDATION_PASS    = 2'b00,
        VALIDATION_FAIL    = 2'b01,
        VALIDATION_ERROR   = 2'b10,
        VALIDATION_BUSY    = 2'b11
    } tdisp_validation_result_e;

endpackage : tdisp_types
