//============================================================================
// TDISP Top-Level Module
// Integrates all TDISP sub-modules into a cohesive TEE Device Interface
// Security Protocol implementation per PCIe Base Spec Rev 7.0, Chapter 11
//
// Module Hierarchy:
//   tdisp_top
//     u251cu2500u2500 tdisp_transport      - SPDM VENDOR_DEFINED encapsulation/decapsulation
//     u251cu2500u2500 tdisp_msg_parser     - Incoming TDISP message parsing
//     u251cu2500u2500 tdisp_msg_formatter  - Outgoing TDISP response formatting
//     u251cu2500u2500 tdisp_fsm            - Per-TDI state machine
//     u251cu2500u2500 tdisp_lock_ctrl      - LOCK_INTERFACE validation & processing
//     u251cu2500u2500 tdisp_nonce_gen      - Nonce generation and validation
//     u251cu2500u2500 tdisp_tdi_mgr        - Per-TDI context management
//     u2514u2500u2500 tdisp_tlp_rules      - TLP access control & XT/T bit enforcement
//============================================================================

module tdisp_top #(
    parameter int unsigned DATA_WIDTH       = 32,
    parameter int unsigned NUM_TDI          = 4,
    parameter int unsigned ADDR_WIDTH       = 64,
    parameter int unsigned BUS_WIDTH        = 8,    // Max MMIO ranges per TDI
    parameter int unsigned MAX_OUTSTANDING  = 255,
    parameter int unsigned MAX_MSG_BYTES    = 1024,
    parameter int unsigned MAC_WIDTH        = 32,   // MAC tag width in bytes
    parameter int unsigned SESSION_ID_WIDTH = 32,
    parameter int unsigned NONCE_WIDTH      = 256,
    parameter int unsigned INTERFACE_ID_WIDTH = 96,
    parameter int unsigned MAX_PAYLOAD_BYTES = 256,
    parameter int unsigned PAGE_SIZE        = 4096,
    parameter int unsigned NONCE_SEED       = 32'hDEADBEEF
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //=== DOE Mailbox Interface (AXI-Stream) ===================================
    input  logic [DATA_WIDTH-1:0]           doe_rx_tdata,
    input  logic [DATA_WIDTH/8-1:0]         doe_rx_tkeep,
    input  logic                            doe_rx_tlast,
    input  logic                            doe_rx_tvalid,
    output logic                            doe_rx_tready,

    output logic [DATA_WIDTH-1:0]           doe_tx_tdata,
    output logic [DATA_WIDTH/8-1:0]         doe_tx_tkeep,
    output logic                            doe_tx_tlast,
    output logic                            doe_tx_tvalid,
    input  logic                            doe_tx_tready,

    //=== TLP Interface (from PCIe core for access control) ====================
    input  logic                            tlp_valid_i,
    input  logic [31:0]                     tlp_header_dw0_i,
    input  logic [31:0]                     tlp_header_dw2_i,
    input  logic [31:0]                     tlp_header_dw3_i,
    input  logic                            tlp_is_4dw_i,
    input  logic [15:0]                     tlp_requester_id_i,
    input  logic [1:0]                      tlp_at_i,
    input  logic                            tlp_tee_originator_i,
    input  logic                            tlp_xt_enabled_i,

    output logic                            tlp_allow_o,
    output logic                            tlp_blocked_o,
    output logic [$clog2(NUM_TDI)-1:0]      tlp_tdi_index_o,
    output logic                            tlp_violation_irq_o,

    //=== Device Configuration Inputs ==========================================
    input  logic                            ide_stream_valid_i,
    input  logic                            ide_keys_programmed_i,
    input  logic                            ide_spdm_session_match_i,
    input  logic                            ide_tc0_enabled_i,
    input  logic                            phantom_fn_disabled_i,
    input  logic                            no_bar_overlap_i,
    input  logic                            valid_page_size_i,
    input  logic [6:0]                      dev_cache_line_size_i,
    input  logic                            fw_update_supported_i,

    //=== Interface ID Initialization (firmware/config at boot) ================
    input  logic                            iface_id_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      iface_id_tdi_index_i,
    input  logic [INTERFACE_ID_WIDTH-1:0]   iface_id_value_i,

    //=== Status Outputs =======================================================
    output tdisp_types::tdisp_state_e       tdi_state_out [NUM_TDI],
    output logic [7:0]                      total_outstanding_o,
    output logic                            transport_error_o,
    output tdisp_types::tdisp_error_code_e  transport_error_code_o,
    output logic                            entropy_warn_o
);

    import tdisp_types::*;

    //==========================================================================
    // Internal Signal Declarations
    //==========================================================================

    //--- Transport u2194 Parser/Formatter AXI-Stream ----------------------------
    logic [DATA_WIDTH-1:0]       tdisp_rx_tdata;
    logic [DATA_WIDTH/8-1:0]     tdisp_rx_tkeep;
    logic                        tdisp_rx_tlast;
    logic                        tdisp_rx_tvalid;
    logic                        tdisp_rx_tready;

    logic [DATA_WIDTH-1:0]       tdisp_tx_tdata;
    logic [DATA_WIDTH/8-1:0]     tdisp_tx_tkeep;
    logic                        tdisp_tx_tlast;
    logic                        tdisp_tx_tvalid;
    logic                        tdisp_tx_tready;

    //--- Parser Outputs -----------------------------------------------------
    logic                        parser_hdr_valid;
    logic [7:0]                  parser_tdisp_version;
    logic [3:0]                  parser_version_major;
    logic [3:0]                  parser_version_minor;
    tdisp_req_code_e             parser_msg_type;
    logic [95:0]                 parser_interface_id;
    logic                        parser_version_valid;
    logic                        parser_version_mismatch;
    logic [DATA_WIDTH-1:0]       parser_payload_tdata;
    logic [DATA_WIDTH/8-1:0]     parser_payload_tkeep;
    logic                        parser_payload_tlast;
    logic                        parser_payload_tvalid;
    logic                        parser_payload_tready;
    logic [15:0]                 parser_msg_total_len;
    logic [15:0]                 parser_payload_len;
    logic                        parser_parse_done;
    logic                        parser_parse_error;
    tdisp_error_code_e           parser_parse_error_code;

    //--- TDI Manager: Lookup ------------------------------------------------
    logic [INTERFACE_ID_WIDTH-1:0] lookup_iface_id;
    logic                          lookup_valid;
    logic                          lookup_match;
    logic [$clog2(NUM_TDI)-1:0]    lookup_tdi_index;
    tdisp_state_e                  lookup_tdi_state;

    //--- TDI Manager: Context Read ------------------------------------------
    logic [$clog2(NUM_TDI)-1:0]    ctx_read_index;
    tdisp_tdi_context_s            ctx_read_data;

    //--- TDI Manager: Per-TDI Broadcast -------------------------------------
    tdisp_state_e                  tdi_states [NUM_TDI];
    logic                          tdi_xt_enabled [NUM_TDI];
    logic                          tdi_fw_locked  [NUM_TDI];
    logic                          tdi_p2p_enabled[NUM_TDI];
    logic                          tdi_req_redirect[NUM_TDI];
    logic [ADDR_WIDTH-1:0]         mmio_start_addr [NUM_TDI][BUS_WIDTH];
    logic [31:0]                   mmio_num_pages  [NUM_TDI][BUS_WIDTH];
    logic                          mmio_is_non_tee [NUM_TDI][BUS_WIDTH];
    logic                          mmio_range_valid[NUM_TDI][BUS_WIDTH];
    logic [63:0]                   p2p_addr_mask   [NUM_TDI];
    logic [7:0]                    outstanding_reqs[NUM_TDI];

    //--- FSM Interface -------------------------------------------------------
    logic [$clog2(NUM_TDI)-1:0]    fsm_tdi_index;
    logic                          fsm_transition_req;
    tdisp_state_e                  fsm_target_state;
    tdisp_req_code_e               fsm_msg_code;
    logic                          fsm_security_violation;
    logic [$clog2(NUM_TDI)-1:0]    fsm_violation_tdi;
    tdisp_state_e                  fsm_tdi_states [NUM_TDI];
    logic                          fsm_transition_ack;
    logic                          fsm_transition_err;
    logic [$clog2(NUM_TDI)-1:0]    fsm_chk_tdi_index;
    tdisp_req_code_e               fsm_chk_msg_code;
    logic                          fsm_chk_legal;

    //--- Lock Controller Interface -------------------------------------------
    logic                          lock_req;
    logic [$clog2(NUM_TDI)-1:0]    lock_tdi_index;
    logic [INTERFACE_ID_WIDTH-1:0] lock_interface_id;
    tdisp_lock_flags_s             lock_flags;
    logic [7:0]                    lock_stream_id;
    logic [63:0]                   lock_mmio_offset;
    logic [63:0]                   lock_p2p_mask;
    tdisp_state_e                  lock_tdi_state;
    logic [INTERFACE_ID_WIDTH-1:0] lock_tdi_iface_id;
    logic                          lock_nonce_req;
    logic                          lock_nonce_ack;
    logic [NONCE_WIDTH-1:0]        lock_nonce_data;
    logic                          lock_ctx_update;
    logic [$clog2(NUM_TDI)-1:0]    lock_ctx_tdi_index;
    tdisp_state_e                  lock_ctx_state;
    tdisp_lock_flags_s             lock_ctx_flags;
    logic [7:0]                    lock_ctx_stream_id;
    logic [63:0]                   lock_ctx_mmio_offset;
    logic [63:0]                   lock_ctx_p2p_mask;
    logic [NONCE_WIDTH-1:0]        lock_ctx_nonce;
    logic                          lock_ctx_nonce_valid;
    logic                          lock_ctx_fw_locked;
    logic                          lock_rsp_valid;
    logic                          lock_rsp_error;
    tdisp_error_code_e             lock_rsp_error_code;
    logic [NONCE_WIDTH-1:0]        lock_rsp_nonce;
    logic                          lock_rsp_done;
    logic                          lock_busy;

    //--- Nonce Generator Interface -------------------------------------------
    logic                          nonce_gen_req;
    logic [$clog2(NUM_TDI)-1:0]    nonce_gen_tdi_index;
    logic                          nonce_gen_ack;
    logic [NONCE_WIDTH-1:0]        nonce_gen_nonce;
    logic                          nonce_val_req;
    logic [$clog2(NUM_TDI)-1:0]    nonce_val_tdi_index;
    logic [NONCE_WIDTH-1:0]        nonce_val_nonce;
    logic                          nonce_val_ack;
    logic                          nonce_val_match;
    logic                          nonce_inv_req;
    logic [$clog2(NUM_TDI)-1:0]    nonce_inv_tdi_index;

    //--- TLP Rules Violation u2192 FSM ------------------------------------------
    logic                          tlp_violation_valid;
    logic [$clog2(NUM_TDI)-1:0]    tlp_violation_tdi;
    tdisp_error_code_e             tlp_violation_code;
    logic                          tlp_violation_ack;

    //--- Transport Request Count Tracking ------------------------------------
    logic                          transport_req_count_update;
    logic [$clog2(NUM_TDI)-1:0]    transport_req_count_tdi;
    logic                          transport_req_count_increment;

    //--- Formatter Interface -------------------------------------------------
    logic                          fmt_build_req;
    tdisp_rsp_code_e               fmt_rsp_type;
    logic [95:0]                   fmt_interface_id;
    logic [$clog2(NUM_TDI)-1:0]    fmt_tdi_index;
    tdisp_state_e                  fmt_tdi_state;
    logic [7:0]                    fmt_version_count;
    logic [511:0]                  fmt_version_entries;
    logic                          fmt_xt_mode_supported;
    logic [127:0]                  fmt_req_msgs_supported;
    logic [15:0]                   fmt_lock_iface_flags_sup;
    logic [7:0]                    fmt_dev_addr_width;
    logic [7:0]                    fmt_num_req_this;
    logic [7:0]                    fmt_num_req_all;
    logic [255:0]                  fmt_start_interface_nonce;
    logic                          fmt_nonce_valid;
    logic [ADDR_WIDTH-1:0]         fmt_mmio_base_addr;
    logic [31:0]                   fmt_mmio_num_pages;
    logic                          fmt_mmio_is_non_tee;
    logic                          fmt_mmio_valid;
    logic [7:0]                    fmt_p2p_stream_id;
    tdisp_error_code_e             fmt_error_code;
    logic [31:0]                   fmt_error_data;
    logic                          fmt_build_done;
    logic                          fmt_build_error;

    //--- START/STOP/Other Handler Signals ------------------------------------
    logic                          start_ctx_update;
    logic [$clog2(NUM_TDI)-1:0]    start_ctx_tdi_index;
    tdisp_state_e                  start_ctx_state;
    logic                          stop_ctx_update;
    logic [$clog2(NUM_TDI)-1:0]    stop_ctx_tdi_index;
    tdisp_state_e                  stop_ctx_state;

    //--- MMIO Attribute Update -----------------------------------------------
    logic                          mmio_update;
    logic [$clog2(NUM_TDI)-1:0]    mmio_tdi_index;
    logic [$clog2(BUS_WIDTH)-1:0]  mmio_range_index;
    logic [ADDR_WIDTH-1:0]         mmio_start_addr_in;
    logic [31:0]                   mmio_num_pages_in;
    logic                          mmio_is_non_tee_in;

    //--- Error State Update (from TLP violation) -----------------------------
    logic                          error_update;
    logic [$clog2(NUM_TDI)-1:0]    error_tdi_index;

    //--- XT Mode Update ------------------------------------------------------
    logic                          xt_mode_update;
    logic [$clog2(NUM_TDI)-1:0]    xt_tdi_index;
    logic                          xt_enabled;

    //--- Outstanding request tracking to TDI mgr -----------------------------
    logic                          req_count_update;
    logic [$clog2(NUM_TDI)-1:0]    req_count_tdi_index;
    logic                          req_count_increment;

    //--- Session info from transport -----------------------------------------
    logic [SESSION_ID_WIDTH-1:0]    session_id;
    logic                           session_active;
    logic                           secured_msg;

    //--- Payload capture for lock request ------------------------------------
    tdisp_lock_flags_s              captured_lock_flags;
    logic [7:0]                     captured_stream_id;
    logic [63:0]                    captured_mmio_offset;
    logic [63:0]                    captured_p2p_mask;
    logic [NONCE_WIDTH-1:0]         captured_start_nonce;

    //==========================================================================
    // Device Capability Constants (configurable per implementation)
    //==========================================================================
    localparam logic                DEV_XT_MODE_SUPPORTED    = 1'b1;
    localparam logic [127:0]        DEV_REQ_MSGS_SUPPORTED   = 128'hFFF; // All 12 request types
    localparam logic [15:0]         DEV_LOCK_IFACE_FLAGS_SUP = 16'h001F; // All 5 flags
    localparam logic [7:0]          DEV_ADDR_WIDTH           = 8'd64;
    localparam logic [7:0]          DEV_VERSION_COUNT        = 8'd1;
    localparam logic [15:0]         DEV_VERSION_ENTRY        = 16'h0010; // v1.0

    //==========================================================================
    // TDI Index resolved from INTERFACE_ID lookup
    //==========================================================================
    logic [$clog2(NUM_TDI)-1:0]     resolved_tdi_index;
    logic                           resolved_tdi_valid;

    assign resolved_tdi_index = lookup_tdi_index;
    assign resolved_tdi_valid = lookup_match;

    //==========================================================================
    // Central Request Router
    // Dispatches parsed TDISP messages to appropriate handlers based on
    // message type. Manages response collection and formatter invocation.
    //==========================================================================
    typedef enum logic [3:0] {
        ROUTER_IDLE,
        ROUTER_LOOKUP,
        ROUTER_DISPATCH,
        ROUTER_LOCK_WAIT,
        ROUTER_START_VALIDATE,
        ROUTER_START_COMMIT,
        ROUTER_STOP_COMMIT,
        ROUTER_BUILD_RSP,
        ROUTER_WAIT_RSP,
        ROUTER_ERROR
    } router_state_e;

    router_state_e  router_state_q;
    tdisp_req_code_e router_msg_type_q;
    logic [95:0]    router_iface_id_q;
    logic [$clog2(NUM_TDI)-1:0] router_tdi_q;
    tdisp_error_code_e router_error_q;
    logic           router_is_lock_q;

    // Payload capture registers
    logic           payload_capture_en;
    tdisp_lock_flags_s payload_lock_flags_q;
    logic [7:0]     payload_stream_id_q;
    logic [63:0]    payload_mmio_offset_q;
    logic [63:0]    payload_p2p_mask_q;
    logic [NONCE_WIDTH-1:0] payload_start_nonce_q;
    logic           payload_nonce_captured_q;

    //==========================================================================
    // Payload Capture from Parser Stream
    // For LOCK_INTERFACE: captures flags, stream_id, mmio_offset, p2p_mask
    // For START_INTERFACE: captures 32-byte nonce
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            payload_lock_flags_q   <= '0;
            payload_stream_id_q    <= '0;
            payload_mmio_offset_q  <= '0;
            payload_p2p_mask_q     <= '0;
            payload_start_nonce_q  <= '0;
            payload_nonce_captured_q <= 1'b0;
        end else if (parser_payload_tvalid && parser_payload_tready) begin
            // LOCK_INTERFACE payload capture (bytes at specific offsets)
            if (router_msg_type_q == REQ_LOCK_INTERFACE && payload_capture_en) begin
                // First payload beat contains flags(2B) + stream_id(1B) + rsvd(1B)
                // followed by mmio_offset(8B) + p2p_mask(8B)
                case (parser_payload_tkeep)
                    4'b1111: begin // First payload beat
                        payload_lock_flags_q  <= tdisp_lock_flags_s'(parser_payload_tdata[15:0]);
                        payload_stream_id_q   <= parser_payload_tdata[23:16];
                    end
                    default: begin
                        // Subsequent beats: mmio_offset and p2p_mask
                        if (!payload_mmio_offset_q[31]) begin
                            payload_mmio_offset_q <= parser_payload_tdata;
                        end else begin
                            payload_p2p_mask_q <= parser_payload_tdata;
                        end
                    end
                endcase
            end

            // START_INTERFACE nonce capture
            if (router_msg_type_q == REQ_START_INTERFACE && payload_capture_en) begin
                // Accumulate 32 bytes of nonce from 8 beats of 32-bit data
                if (!payload_nonce_captured_q) begin
                    payload_start_nonce_q <= {parser_payload_tdata, payload_start_nonce_q[NONCE_WIDTH-1:DATA_WIDTH]};
                    if (parser_payload_tlast) begin
                        payload_nonce_captured_q <= 1'b1;
                    end
                end
            end
        end else if (router_state_q == ROUTER_IDLE) begin
            payload_capture_en       <= 1'b0;
            payload_nonce_captured_q <= 1'b0;
        end
    end

    //==========================================================================
    // Request Router FSM
    //==========================================================================
    logic [7:0] total_outstanding_comb;

    always_comb begin
        total_outstanding_comb = '0;
        for (int i = 0; i < NUM_TDI; i++) begin
            total_outstanding_comb += outstanding_reqs[i];
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            router_state_q      <= ROUTER_IDLE;
            router_msg_type_q   <= REQ_GET_TDISP_VERSION;
            router_iface_id_q   <= '0;
            router_tdi_q        <= '0;
            router_error_q      <= ERR_RESERVED;
            router_is_lock_q    <= 1'b0;
            payload_capture_en  <= 1'b0;

            // Drive defaults
            lookup_valid        <= 1'b0;
            lookup_iface_id     <= '0;
            lock_req            <= 1'b0;
            lock_tdi_index      <= '0;
            lock_interface_id   <= '0;
            lock_flags          <= '0;
            lock_stream_id      <= '0;
            lock_mmio_offset    <= '0;
            lock_p2p_mask       <= '0;
            lock_tdi_state      <= TDI_CONFIG_UNLOCKED;
            lock_tdi_iface_id   <= '0;
            lock_rsp_done       <= 1'b0;
            lock_ctx_update     <= 1'b0;
            start_ctx_update    <= 1'b0;
            stop_ctx_update     <= 1'b0;
            start_ctx_tdi_index <= '0;
            stop_ctx_tdi_index  <= '0;
            start_ctx_state     <= TDI_CONFIG_UNLOCKED;
            stop_ctx_state      <= TDI_CONFIG_UNLOCKED;
            error_update        <= 1'b0;
            error_tdi_index     <= '0;
            nonce_val_req       <= 1'b0;
            nonce_inv_req       <= 1'b0;
            nonce_val_tdi_index <= '0;
            nonce_val_nonce     <= '0;
            nonce_inv_tdi_index <= '0;
            mmio_update         <= 1'b0;
            xt_mode_update      <= 1'b0;
            fsm_transition_req  <= 1'b0;
            fsm_tdi_index       <= '0;
            fsm_target_state    <= TDI_CONFIG_UNLOCKED;
            fsm_msg_code        <= REQ_GET_TDISP_VERSION;
            fsm_security_violation <= 1'b0;
            fsm_violation_tdi   <= '0;
            fmt_build_req       <= 1'b0;
            fmt_rsp_type        <= RSP_TDISP_ERROR;
            fmt_interface_id    <= '0;
            fmt_tdi_index       <= '0;
            fmt_tdi_state       <= TDI_CONFIG_UNLOCKED;
            fmt_version_count   <= '0;
            fmt_version_entries <= '0;
            fmt_xt_mode_supported <= 1'b0;
            fmt_req_msgs_supported <= '0;
            fmt_lock_iface_flags_sup <= '0;
            fmt_dev_addr_width  <= '0;
            fmt_num_req_this    <= '0;
            fmt_num_req_all     <= '0;
            fmt_start_interface_nonce <= '0;
            fmt_nonce_valid     <= 1'b0;
            fmt_mmio_base_addr  <= '0;
            fmt_mmio_num_pages  <= '0;
            fmt_mmio_is_non_tee <= 1'b0;
            fmt_mmio_valid      <= 1'b0;
            fmt_p2p_stream_id   <= '0;
            fmt_error_code      <= ERR_RESERVED;
            fmt_error_data      <= '0;
            ctx_read_index      <= '0;
        end else begin
            // Default pulse clears
            lock_req            <= 1'b0;
            lock_rsp_done       <= 1'b0;
            lock_ctx_update     <= 1'b0;
            start_ctx_update    <= 1'b0;
            stop_ctx_update     <= 1'b0;
            error_update        <= 1'b0;
            nonce_val_req       <= 1'b0;
            nonce_inv_req       <= 1'b0;
            mmio_update         <= 1'b0;
            xt_mode_update      <= 1'b0;
            fsm_transition_req  <= 1'b0;
            fsm_security_violation <= 1'b0;
            fmt_build_req       <= 1'b0;
            lookup_valid        <= 1'b0;

            case (router_state_q)
                //==============================================================
                ROUTER_IDLE: begin
                    if (parser_hdr_valid) begin
                        router_msg_type_q <= parser_msg_type;
                        router_iface_id_q <= parser_interface_id;

                        // Check version first
                        if (parser_version_mismatch) begin
                            router_error_q <= ERR_VERSION_MISMATCH;
                            router_state_q <= ROUTER_ERROR;
                        end else begin
                            // Initiate INTERFACE_ID lookup
                            lookup_iface_id <= parser_interface_id;
                            lookup_valid    <= 1'b1;
                            router_state_q  <= ROUTER_LOOKUP;
                        end
                    end
                end

                //==============================================================
                ROUTER_LOOKUP: begin
                    router_tdi_q <= resolved_tdi_index;
                    ctx_read_index <= resolved_tdi_index;

                    // Check if message requires a valid TDI
                    case (router_msg_type_q)
                        REQ_GET_TDISP_VERSION,
                        REQ_GET_TDISP_CAPABILITIES: begin
                            // These don't require a valid TDI index
                            router_state_q <= ROUTER_DISPATCH;
                        end

                        default: begin
                            if (!resolved_tdi_valid) begin
                                router_error_q <= ERR_INVALID_INTERFACE;
                                router_state_q <= ROUTER_ERROR;
                            end else begin
                                router_state_q <= ROUTER_DISPATCH;
                            end
                        end
                    endcase
                end

                //==============================================================
                ROUTER_DISPATCH: begin
                    payload_capture_en <= 1'b0;

                    case (router_msg_type_q)
                        //----------------------------------------------------------
                        REQ_GET_TDISP_VERSION: begin
                            fmt_build_req         <= 1'b1;
                            fmt_rsp_type          <= RSP_TDISP_VERSION;
                            fmt_interface_id      <= router_iface_id_q;
                            fmt_tdi_index         <= router_tdi_q;
                            fmt_version_count     <= DEV_VERSION_COUNT;
                            fmt_version_entries   <= {(32-1)*16'd0, DEV_VERSION_ENTRY};
                            router_state_q        <= ROUTER_WAIT_RSP;
                        end

                        //----------------------------------------------------------
                        REQ_GET_TDISP_CAPABILITIES: begin
                            fmt_build_req           <= 1'b1;
                            fmt_rsp_type            <= RSP_TDISP_CAPABILITIES;
                            fmt_interface_id        <= router_iface_id_q;
                            fmt_tdi_index           <= router_tdi_q;
                            fmt_xt_mode_supported   <= DEV_XT_MODE_SUPPORTED;
                            fmt_req_msgs_supported  <= DEV_REQ_MSGS_SUPPORTED;
                            fmt_lock_iface_flags_sup <= DEV_LOCK_IFACE_FLAGS_SUP;
                            fmt_dev_addr_width      <= DEV_ADDR_WIDTH;
                            fmt_num_req_this        <= outstanding_reqs[router_tdi_q];
                            fmt_num_req_all         <= total_outstanding_comb;
                            router_state_q          <= ROUTER_WAIT_RSP;
                        end

                        //----------------------------------------------------------
                        REQ_LOCK_INTERFACE: begin
                            // Check FSM legality first
                            fsm_chk_tdi_index <= router_tdi_q;
                            fsm_chk_msg_code  <= REQ_LOCK_INTERFACE;
                            if (!fsm_chk_legal) begin
                                router_error_q <= ERR_INVALID_INTERFACE_STATE;
                                router_state_q <= ROUTER_ERROR;
                            end else begin
                                // Enable payload capture and wait for payload
                                payload_capture_en <= 1'b1;
                                router_is_lock_q   <= 1'b1;
                                router_state_q     <= ROUTER_LOCK_WAIT;
                            end
                        end

                        //----------------------------------------------------------
                        REQ_GET_DEVICE_INTERFACE_REPORT: begin
                            fsm_chk_tdi_index <= router_tdi_q;
                            fsm_chk_msg_code  <= REQ_GET_DEVICE_INTERFACE_REPORT;
                            if (!fsm_chk_legal) begin
                                router_error_q <= ERR_INVALID_INTERFACE_STATE;
                                router_state_q <= ROUTER_ERROR;
                            end else begin
                                fmt_build_req      <= 1'b1;
                                fmt_rsp_type       <= RSP_DEVICE_INTERFACE_REPORT;
                                fmt_interface_id   <= router_iface_id_q;
                                fmt_tdi_index      <= router_tdi_q;
                                fmt_mmio_base_addr <= ctx_read_data.mmio_reporting_offset;
                                fmt_mmio_valid     <= 1'b1;
                                router_state_q     <= ROUTER_WAIT_RSP;
                            end
                        end

                        //----------------------------------------------------------
                        REQ_GET_DEVICE_INTERFACE_STATE: begin
                            fmt_build_req      <= 1'b1;
                            fmt_rsp_type       <= RSP_DEVICE_INTERFACE_STATE;
                            fmt_interface_id   <= router_iface_id_q;
                            fmt_tdi_index      <= router_tdi_q;
                            fmt_tdi_state      <= tdi_states[router_tdi_q];
                            router_state_q     <= ROUTER_WAIT_RSP;
                        end

                        //----------------------------------------------------------
                        REQ_START_INTERFACE: begin
                            fsm_chk_tdi_index <= router_tdi_q;
                            fsm_chk_msg_code  <= REQ_START_INTERFACE;
                            if (!fsm_chk_legal) begin
                                router_error_q <= ERR_INVALID_INTERFACE_STATE;
                                router_state_q <= ROUTER_ERROR;
                            end else begin
                                payload_capture_en <= 1'b1;
                                router_state_q     <= ROUTER_START_VALIDATE;
                            end
                        end

                        //----------------------------------------------------------
                        REQ_STOP_INTERFACE: begin
                            fsm_chk_tdi_index <= router_tdi_q;
                            fsm_chk_msg_code  <= REQ_STOP_INTERFACE;
                            // STOP is always legal
                            stop_ctx_update    <= 1'b1;
                            stop_ctx_tdi_index <= router_tdi_q;
                            stop_ctx_state     <= TDI_CONFIG_UNLOCKED;

                            // Also request FSM transition
                            fsm_transition_req <= 1'b1;
                            fsm_tdi_index      <= router_tdi_q;
                            fsm_target_state   <= TDI_CONFIG_UNLOCKED;
                            fsm_msg_code       <= REQ_STOP_INTERFACE;

                            // Invalidate nonce
                            nonce_inv_req       <= 1'b1;
                            nonce_inv_tdi_index <= router_tdi_q;

                            fmt_build_req      <= 1'b1;
                            fmt_rsp_type       <= RSP_STOP_INTERFACE;
                            fmt_interface_id   <= router_iface_id_q;
                            fmt_tdi_index      <= router_tdi_q;
                            router_state_q     <= ROUTER_WAIT_RSP;
                        end

                        //----------------------------------------------------------
                        REQ_BIND_P2P_STREAM: begin
                            fsm_chk_tdi_index <= router_tdi_q;
                            fsm_chk_msg_code  <= REQ_BIND_P2P_STREAM;
                            if (!fsm_chk_legal || !tdi_p2p_enabled[router_tdi_q]) begin
                                router_error_q <= ERR_INVALID_INTERFACE_STATE;
                                router_state_q <= ROUTER_ERROR;
                            end else begin
                                fmt_build_req      <= 1'b1;
                                fmt_rsp_type       <= RSP_BIND_P2P_STREAM;
                                fmt_interface_id   <= router_iface_id_q;
                                fmt_tdi_index      <= router_tdi_q;
                                router_state_q     <= ROUTER_WAIT_RSP;
                            end
                        end

                        //----------------------------------------------------------
                        REQ_UNBIND_P2P_STREAM: begin
                            fsm_chk_tdi_index <= router_tdi_q;
                            fsm_chk_msg_code  <= REQ_UNBIND_P2P_STREAM;
                            if (!fsm_chk_legal) begin
                                router_error_q <= ERR_INVALID_INTERFACE_STATE;
                                router_state_q <= ROUTER_ERROR;
                            end else begin
                                fmt_build_req      <= 1'b1;
                                fmt_rsp_type       <= RSP_UNBIND_P2P_STREAM;
                                fmt_interface_id   <= router_iface_id_q;
                                fmt_tdi_index      <= router_tdi_q;
                                router_state_q     <= ROUTER_WAIT_RSP;
                            end
                        end

                        //----------------------------------------------------------
                        REQ_SET_MMIO_ATTRIBUTE: begin
                            fsm_chk_tdi_index <= router_tdi_q;
                            fsm_chk_msg_code  <= REQ_SET_MMIO_ATTRIBUTE;
                            if (!fsm_chk_legal) begin
                                router_error_q <= ERR_INVALID_INTERFACE_STATE;
                                router_state_q <= ROUTER_ERROR;
                            end else begin
                                // Would capture MMIO range from payload here
                                // Simplified: ack immediately
                                fmt_build_req      <= 1'b1;
                                fmt_rsp_type       <= RSP_SET_MMIO_ATTRIBUTE;
                                fmt_interface_id   <= router_iface_id_q;
                                fmt_tdi_index      <= router_tdi_q;
                                router_state_q     <= ROUTER_WAIT_RSP;
                            end
                        end

                        //----------------------------------------------------------
                        REQ_VDM: begin
                            fmt_build_req      <= 1'b1;
                            fmt_rsp_type       <= RSP_VDM;
                            fmt_interface_id   <= router_iface_id_q;
                            fmt_tdi_index      <= router_tdi_q;
                            router_state_q     <= ROUTER_WAIT_RSP;
                        end

                        //----------------------------------------------------------
                        REQ_SET_TDISP_CONFIG: begin
                            fsm_chk_tdi_index <= router_tdi_q;
                            fsm_chk_msg_code  <= REQ_SET_TDISP_CONFIG;
                            if (!fsm_chk_legal) begin
                                router_error_q <= ERR_INVALID_INTERFACE_STATE;
                                router_state_q <= ROUTER_ERROR;
                            end else begin
                                fmt_build_req      <= 1'b1;
                                fmt_rsp_type       <= RSP_SET_TDISP_CONFIG;
                                fmt_interface_id   <= router_iface_id_q;
                                fmt_tdi_index      <= router_tdi_q;
                                router_state_q     <= ROUTER_WAIT_RSP;
                            end
                        end

                        //----------------------------------------------------------
                        default: begin
                            router_error_q <= ERR_UNSUPPORTED_REQUEST;
                            router_state_q <= ROUTER_ERROR;
                        end
                    endcase
                end

                //==============================================================
                ROUTER_LOCK_WAIT: begin
                    // Wait for payload capture to complete, then start lock_ctrl
                    if (parser_parse_done || payload_lock_flags_q != '0) begin
                        lock_req           <= 1'b1;
                        lock_tdi_index     <= router_tdi_q;
                        lock_interface_id  <= router_iface_id_q;
                        lock_flags         <= payload_lock_flags_q;
                        lock_stream_id     <= payload_stream_id_q;
                        lock_mmio_offset   <= payload_mmio_offset_q;
                        lock_p2p_mask      <= payload_p2p_mask_q;
                        lock_tdi_state     <= tdi_states[router_tdi_q];
                        lock_tdi_iface_id  <= ctx_read_data.interface_id;
                        router_state_q     <= ROUTER_BUILD_RSP;
                    end
                end

                //==============================================================
                ROUTER_BUILD_RSP: begin
                    // Wait for lock_ctrl response
                    if (lock_rsp_valid) begin
                        if (lock_rsp_error) begin
                            // Lock failed - send error
                            fmt_build_req    <= 1'b1;
                            fmt_rsp_type     <= RSP_TDISP_ERROR;
                            fmt_interface_id <= router_iface_id_q;
                            fmt_tdi_index    <= router_tdi_q;
                            fmt_error_code   <= lock_rsp_error_code;
                            fmt_error_data   <= '0;
                            lock_rsp_done    <= 1'b1;
                            router_state_q   <= ROUTER_WAIT_RSP;
                        end else begin
                            // Lock succeeded - format success response
                            fmt_build_req            <= 1'b1;
                            fmt_rsp_type             <= RSP_LOCK_INTERFACE;
                            fmt_interface_id         <= router_iface_id_q;
                            fmt_tdi_index            <= router_tdi_q;
                            fmt_start_interface_nonce <= lock_rsp_nonce;
                            fmt_nonce_valid          <= 1'b1;
                            lock_rsp_done            <= 1'b1;
                            router_state_q           <= ROUTER_WAIT_RSP;
                        end
                    end
                end

                //==============================================================
                ROUTER_START_VALIDATE: begin
                    // Wait for nonce capture then validate
                    if (payload_nonce_captured_q) begin
                        nonce_val_req       <= 1'b1;
                        nonce_val_tdi_index <= router_tdi_q;
                        nonce_val_nonce     <= payload_start_nonce_q;
                        router_state_q      <= ROUTER_START_COMMIT;
                    end
                end

                //==============================================================
                ROUTER_START_COMMIT: begin
                    if (nonce_val_ack) begin
                        if (nonce_val_match) begin
                            // Nonce valid - commit state transition to RUN
                            start_ctx_update    <= 1'b1;
                            start_ctx_tdi_index <= router_tdi_q;
                            start_ctx_state     <= TDI_RUN;

                            fsm_transition_req  <= 1'b1;
                            fsm_tdi_index       <= router_tdi_q;
                            fsm_target_state    <= TDI_RUN;
                            fsm_msg_code        <= REQ_START_INTERFACE;

                            // Invalidate used nonce
                            nonce_inv_req       <= 1'b1;
                            nonce_inv_tdi_index <= router_tdi_q;

                            fmt_build_req      <= 1'b1;
                            fmt_rsp_type       <= RSP_START_INTERFACE;
                            fmt_interface_id   <= router_iface_id_q;
                            fmt_tdi_index      <= router_tdi_q;
                            router_state_q     <= ROUTER_WAIT_RSP;
                        end else begin
                            router_error_q <= ERR_INVALID_NONCE;
                            router_state_q <= ROUTER_ERROR;
                        end
                    end
                end

                //==============================================================
                ROUTER_WAIT_RSP: begin
                    if (fmt_build_done) begin
                        router_state_q <= ROUTER_IDLE;
                    end
                    if (fmt_build_error) begin
                        // Retry with error response
                        fmt_build_req    <= 1'b1;
                        fmt_rsp_type     <= RSP_TDISP_ERROR;
                        fmt_interface_id <= router_iface_id_q;
                        fmt_tdi_index    <= router_tdi_q;
                        fmt_error_code   <= ERR_UNSPECIFIED;
                        fmt_error_data   <= '0;
                    end
                end

                //==============================================================
                ROUTER_ERROR: begin
                    fmt_build_req      <= 1'b1;
                    fmt_rsp_type       <= RSP_TDISP_ERROR;
                    fmt_interface_id   <= router_iface_id_q;
                    fmt_tdi_index      <= router_tdi_q;
                    fmt_error_code     <= router_error_q;
                    fmt_error_data     <= '0;
                    router_state_q     <= ROUTER_WAIT_RSP;
                end

                default: router_state_q <= ROUTER_IDLE;
            endcase
        end
    end

    //==========================================================================
    // TLP Violation u2192 FSM Error State Transition
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tlp_violation_ack <= 1'b0;
        end else begin
            tlp_violation_ack <= 1'b0;
            if (tlp_violation_valid && !tlp_violation_ack) begin
                // Trigger security violation in FSM
                fsm_security_violation <= 1'b1;
                fsm_violation_tdi      <= tlp_violation_tdi;
                // Update TDI context to ERROR state
                error_update    <= 1'b1;
                error_tdi_index <= tlp_violation_tdi;
                tlp_violation_ack <= 1'b1;
            end
        end
    end

    //==========================================================================
    // TDI Manager Outstanding Request Tracking Merge
    // Merges transport-level tracking with local request tracking
    //==========================================================================
    always_comb begin
        req_count_update    = transport_req_count_update;
        req_count_tdi_index = transport_req_count_tdi;
        req_count_increment = transport_req_count_increment;
    end

    //==========================================================================
    // Parser payload ready - always accept payload data
    //==========================================================================
    assign parser_payload_tready = 1'b1;

    //==========================================================================
    // Module Instantiations
    //==========================================================================

    //--------------------------------------------------------------------------
    // Transport Layer
    //--------------------------------------------------------------------------
    tdisp_transport #(
        .DATA_WIDTH       (DATA_WIDTH),
        .NUM_TDI          (NUM_TDI),
        .MAX_OUTSTANDING  (MAX_OUTSTANDING),
        .MAX_MSG_BYTES    (MAX_MSG_BYTES),
        .MAC_WIDTH        (MAC_WIDTH),
        .SESSION_ID_WIDTH (SESSION_ID_WIDTH)
    ) u_transport (
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

        .tdisp_rx_tdata         (tdisp_rx_tdata),
        .tdisp_rx_tkeep         (tdisp_rx_tkeep),
        .tdisp_rx_tlast         (tdisp_rx_tlast),
        .tdisp_rx_tvalid        (tdisp_rx_tvalid),
        .tdisp_rx_tready        (tdisp_rx_tready),

        .tdisp_tx_tdata         (tdisp_tx_tdata),
        .tdisp_tx_tkeep         (tdisp_tx_tkeep),
        .tdisp_tx_tlast         (tdisp_tx_tlast),
        .tdisp_tx_tvalid        (tdisp_tx_tvalid),
        .tdisp_tx_tready        (tdisp_tx_tready),

        .tdi_index_i            (resolved_tdi_index),
        .tdi_index_valid_i      (resolved_tdi_valid),

        .req_count_update_o     (transport_req_count_update),
        .req_count_tdi_o        (transport_req_count_tdi),
        .req_count_increment_o  (transport_req_count_increment),

        .session_id_o           (session_id),
        .session_active_o       (session_active),
        .secured_msg_o          (secured_msg),

        .transport_error_o      (transport_error_o),
        .transport_error_code_o (transport_error_code_o),
        .total_outstanding_o    (total_outstanding_o)
    );

    //--------------------------------------------------------------------------
    // Message Parser
    //--------------------------------------------------------------------------
    tdisp_msg_parser #(
        .DATA_WIDTH       (DATA_WIDTH),
        .MAX_PAYLOAD_BYTES(MAX_PAYLOAD_BYTES)
    ) u_parser (
        .clk                    (clk),
        .rst_n                  (rst_n),

        .s_axis_tdata           (tdisp_rx_tdata),
        .s_axis_tkeep           (tdisp_rx_tkeep),
        .s_axis_tlast           (tdisp_rx_tlast),
        .s_axis_tvalid          (tdisp_rx_tvalid),
        .s_axis_tready          (tdisp_rx_tready),

        .hdr_valid_o            (parser_hdr_valid),
        .tdisp_version_o        (parser_tdisp_version),
        .tdisp_version_major_o  (parser_version_major),
        .tdisp_version_minor_o  (parser_version_minor),
        .msg_type_o             (parser_msg_type),
        .interface_id_o         (parser_interface_id),

        .version_valid_o        (parser_version_valid),
        .version_mismatch_o     (parser_version_mismatch),

        .m_payload_tdata        (parser_payload_tdata),
        .m_payload_tkeep        (parser_payload_tkeep),
        .m_payload_tlast        (parser_payload_tlast),
        .m_payload_tvalid       (parser_payload_tvalid),
        .m_payload_tready       (parser_payload_tready),

        .msg_total_len_o        (parser_msg_total_len),
        .payload_len_o          (parser_payload_len),

        .parse_done_o           (parser_parse_done),
        .parse_error_o          (parser_parse_error),
        .parse_error_code_o     (parser_parse_error_code)
    );

    //--------------------------------------------------------------------------
    // Message Formatter
    //--------------------------------------------------------------------------
    tdisp_msg_formatter #(
        .DATA_WIDTH       (DATA_WIDTH),
        .NUM_TDI          (NUM_TDI),
        .ADDR_WIDTH       (ADDR_WIDTH),
        .MAX_OUTSTANDING  (MAX_OUTSTANDING)
    ) u_formatter (
        .clk                    (clk),
        .rst_n                  (rst_n),

        .build_req_i            (fmt_build_req),
        .rsp_type_i             (fmt_rsp_type),
        .interface_id_i         (fmt_interface_id),
        .tdi_index_i            (fmt_tdi_index),

        .tdi_state_i            (fmt_tdi_state),

        .version_count_i        (fmt_version_count),
        .version_entries_i      (fmt_version_entries),

        .xt_mode_supported_i    (fmt_xt_mode_supported),
        .req_msgs_supported_i   (fmt_req_msgs_supported),
        .lock_iface_flags_sup_i (fmt_lock_iface_flags_sup),
        .dev_addr_width_i       (fmt_dev_addr_width),
        .num_req_this_i         (fmt_num_req_this),
        .num_req_all_i          (fmt_num_req_all),

        .start_interface_nonce_i(fmt_start_interface_nonce),
        .nonce_valid_i          (fmt_nonce_valid),

        .mmio_base_addr_i       (fmt_mmio_base_addr),
        .mmio_num_pages_i       (fmt_mmio_num_pages),
        .mmio_is_non_tee_i      (fmt_mmio_is_non_tee),
        .mmio_valid_i           (fmt_mmio_valid),

        .p2p_stream_id_i        (fmt_p2p_stream_id),

        .error_code_i           (fmt_error_code),
        .error_data_i           (fmt_error_data),

        .m_axis_tdata           (tdisp_tx_tdata),
        .m_axis_tkeep           (tdisp_tx_tkeep),
        .m_axis_tlast           (tdisp_tx_tlast),
        .m_axis_tvalid          (tdisp_tx_tvalid),
        .m_axis_tready          (tdisp_tx_tready),

        .build_done_o           (fmt_build_done),
        .build_error_o          (fmt_build_error)
    );

    //--------------------------------------------------------------------------
    // FSM
    //--------------------------------------------------------------------------
    tdisp_fsm #(
        .NUM_TDI   (NUM_TDI)
    ) u_fsm (
        .clk                    (clk),
        .rst_n                  (rst_n),

        .tdi_index_i            (fsm_tdi_index),
        .transition_req_i       (fsm_transition_req),
        .target_state_i         (fsm_target_state),
        .msg_code_i             (fsm_msg_code),
        .security_violation_i   (fsm_security_violation),
        .violation_tdi_i        (fsm_violation_tdi),

        .tdi_state_o            (fsm_tdi_states),
        .transition_ack_o       (fsm_transition_ack),
        .transition_err_o       (fsm_transition_err),

        .chk_tdi_index_i        (fsm_chk_tdi_index),
        .chk_msg_code_i         (fsm_chk_msg_code),
        .chk_legal_o            (fsm_chk_legal)
    );

    //--------------------------------------------------------------------------
    // Lock Controller
    //--------------------------------------------------------------------------
    tdisp_lock_ctrl #(
        .NUM_TDI            (NUM_TDI),
        .INTERFACE_ID_WIDTH (INTERFACE_ID_WIDTH),
        .NONCE_WIDTH        (NONCE_WIDTH),
        .MAX_OUTSTANDING    (MAX_OUTSTANDING)
    ) u_lock_ctrl (
        .clk                    (clk),
        .rst_n                  (rst_n),

        .lock_req_i             (lock_req),
        .tdi_index_i            (lock_tdi_index),
        .interface_id_i         (lock_interface_id),
        .lock_flags_i           (lock_flags),
        .stream_id_i            (lock_stream_id),
        .mmio_reporting_offset_i(lock_mmio_offset),
        .bind_p2p_addr_mask_i   (lock_p2p_mask),

        .tdi_state_i            (lock_tdi_state),
        .tdi_interface_id_i     (lock_tdi_iface_id),

        .ide_stream_valid_i     (ide_stream_valid_i),
        .ide_keys_programmed_i  (ide_keys_programmed_i),
        .ide_spdm_session_match_i(ide_spdm_session_match_i),
        .ide_tc0_enabled_i      (ide_tc0_enabled_i),

        .phantom_fn_disabled_i  (phantom_fn_disabled_i),
        .no_bar_overlap_i       (no_bar_overlap_i),
        .valid_page_size_i      (valid_page_size_i),
        .dev_cache_line_size_i  (dev_cache_line_size_i),
        .fw_update_supported_i  (fw_update_supported_i),

        .nonce_req_o            (lock_nonce_req),
        .nonce_ack_i            (lock_nonce_ack),
        .nonce_data_i           (lock_nonce_data),

        .ctx_update_o           (lock_ctx_update),
        .ctx_tdi_index_o        (lock_ctx_tdi_index),
        .ctx_new_state_o        (lock_ctx_state),
        .ctx_lock_flags_o       (lock_ctx_flags),
        .ctx_stream_id_o        (lock_ctx_stream_id),
        .ctx_mmio_offset_o      (lock_ctx_mmio_offset),
        .ctx_p2p_mask_o         (lock_ctx_p2p_mask),
        .ctx_nonce_o            (lock_ctx_nonce),
        .ctx_nonce_valid_o      (lock_ctx_nonce_valid),
        .ctx_fw_update_locked_o (lock_ctx_fw_locked),

        .rsp_valid_o            (lock_rsp_valid),
        .rsp_error_o            (lock_rsp_error),
        .rsp_error_code_o       (lock_rsp_error_code),
        .rsp_nonce_o            (lock_rsp_nonce),
        .rsp_done_i             (lock_rsp_done),

        .busy_o                 (lock_busy)
    );

    //--------------------------------------------------------------------------
    // Nonce Generator
    //--------------------------------------------------------------------------
    tdisp_nonce_gen #(
        .NUM_TDI      (NUM_TDI),
        .NONCE_WIDTH  (NONCE_WIDTH),
        .SEED         (NONCE_SEED)
    ) u_nonce_gen (
        .clk                (clk),
        .rst_n              (rst_n),

        .gen_req_i          (lock_nonce_req),
        .gen_tdi_index_i    (lock_tdi_index),
        .gen_ack_o          (lock_nonce_ack),
        .gen_nonce_o        (lock_nonce_data),

        .val_req_i          (nonce_val_req),
        .val_tdi_index_i    (nonce_val_tdi_index),
        .val_nonce_i        (nonce_val_nonce),
        .val_ack_o          (nonce_val_ack),
        .val_match_o        (nonce_val_match),

        .inv_req_i          (nonce_inv_req),
        .inv_tdi_index_i    (nonce_inv_tdi_index),

        .entropy_warn_o     (entropy_warn_o)
    );

    //--------------------------------------------------------------------------
    // TDI Context Manager
    //--------------------------------------------------------------------------
    tdisp_tdi_mgr #(
        .NUM_TDI            (NUM_TDI),
        .BUS_WIDTH          (BUS_WIDTH),
        .ADDR_WIDTH         (ADDR_WIDTH),
        .NONCE_WIDTH        (NONCE_WIDTH),
        .INTERFACE_ID_WIDTH (INTERFACE_ID_WIDTH)
    ) u_tdi_mgr (
        .clk                    (clk),
        .rst_n                  (rst_n),

        // Port A: Lock commit
        .lock_ctx_update_i      (lock_ctx_update),
        .lock_ctx_tdi_index_i   (lock_ctx_tdi_index),
        .lock_ctx_state_i       (lock_ctx_state),
        .lock_ctx_flags_i       (lock_ctx_flags),
        .lock_ctx_stream_id_i   (lock_ctx_stream_id),
        .lock_ctx_mmio_offset_i (lock_ctx_mmio_offset),
        .lock_ctx_p2p_mask_i    (lock_ctx_p2p_mask),
        .lock_ctx_nonce_i       (lock_ctx_nonce),
        .lock_ctx_nonce_valid_i (lock_ctx_nonce_valid),
        .lock_ctx_fw_locked_i   (lock_ctx_fw_locked),

        // Port B: FSM state transition
        .fsm_transition_ack_i   (fsm_transition_ack),
        .fsm_tdi_index_i        (fsm_tdi_index),
        .fsm_target_state_i     (fsm_target_state),

        // Port C: START_INTERFACE
        .start_ctx_update_i     (start_ctx_update),
        .start_ctx_tdi_index_i  (start_ctx_tdi_index),
        .start_ctx_state_i      (start_ctx_state),

        // Port D: STOP_INTERFACE
        .stop_ctx_update_i      (stop_ctx_update),
        .stop_ctx_tdi_index_i   (stop_ctx_tdi_index),
        .stop_ctx_state_i       (stop_ctx_state),

        // Port E: MMIO range update
        .mmio_update_i          (mmio_update),
        .mmio_tdi_index_i       (mmio_tdi_index),
        .mmio_range_index_i     (mmio_range_index),
        .mmio_start_addr_i      (mmio_start_addr_in),
        .mmio_num_pages_i       (mmio_num_pages_in),
        .mmio_is_non_tee_i      (mmio_is_non_tee_in),

        // Port F: Error state
        .error_update_i         (error_update),
        .error_tdi_index_i      (error_tdi_index),

        // XT mode
        .xt_mode_update_i       (xt_mode_update),
        .xt_tdi_index_i         (xt_tdi_index),
        .xt_enabled_i           (xt_enabled),

        // Interface ID init
        .iface_id_update_i      (iface_id_update_i),
        .iface_id_tdi_index_i   (iface_id_tdi_index_i),
        .iface_id_value_i       (iface_id_value_i),

        // Outstanding request tracking
        .req_count_update_i     (req_count_update),
        .req_count_tdi_index_i  (req_count_tdi_index),
        .req_count_increment_i  (req_count_increment),

        // Read ports
        .lookup_iface_id_i      (lookup_iface_id),
        .lookup_valid_i         (lookup_valid),
        .lookup_match_o         (lookup_match),
        .lookup_tdi_index_o     (lookup_tdi_index),
        .lookup_tdi_state_o     (lookup_tdi_state),

        .ctx_read_index_i       (ctx_read_index),
        .ctx_read_data_o        (ctx_read_data),

        // Broadcast outputs
        .tdi_state_o            (tdi_states),
        .tdi_xt_enabled_o       (tdi_xt_enabled),
        .tdi_fw_locked_o        (tdi_fw_locked),
        .tdi_p2p_enabled_o      (tdi_p2p_enabled),
        .tdi_req_redirect_o     (tdi_req_redirect),

        .mmio_start_addr_o      (mmio_start_addr),
        .mmio_num_pages_o       (mmio_num_pages),
        .mmio_is_non_tee_o      (mmio_is_non_tee),
        .mmio_range_valid_o     (mmio_range_valid),

        .p2p_addr_mask_o        (p2p_addr_mask),
        .outstanding_reqs_o     (outstanding_reqs)
    );

    //--------------------------------------------------------------------------
    // TLP Access Rules
    //--------------------------------------------------------------------------
    tdisp_tlp_rules #(
        .NUM_TDI    (NUM_TDI),
        .ADDR_WIDTH (ADDR_WIDTH),
        .BUS_WIDTH  (BUS_WIDTH),
        .PAGE_SIZE  (PAGE_SIZE)
    ) u_tlp_rules (
        .clk                    (clk),
        .rst_n                  (rst_n),

        .tdi_state_i            (tdi_states),
        .tdi_xt_enabled_i       (tdi_xt_enabled),
        .tdi_fw_locked_i        (tdi_fw_locked),
        .tdi_p2p_enabled_i      (tdi_p2p_enabled),
        .tdi_req_redirect_i     (tdi_req_redirect),

        .tlp_valid_i            (tlp_valid_i),
        .tlp_header_dw0_i       (tlp_header_dw0_i),
        .tlp_header_dw2_i       (tlp_header_dw2_i),
        .tlp_header_dw3_i       (tlp_header_dw3_i),
        .tlp_is_4dw_i           (tlp_is_4dw_i),
        .tlp_requester_id_i     (tlp_requester_id_i),
        .tlp_at_i               (tlp_at_i),

        .tlp_tee_originator_i   (tlp_tee_originator_i),
        .tlp_xt_enabled_i       (tlp_xt_enabled_i),

        .mmio_start_addr_i      (mmio_start_addr),
        .mmio_num_pages_i       (mmio_num_pages),
        .mmio_is_non_tee_i      (mmio_is_non_tee),
        .mmio_range_valid_i     (mmio_range_valid),

        .tlp_allow_o            (tlp_allow_o),
        .tlp_blocked_o          (tlp_blocked_o),
        .tlp_tdi_index_o        (tlp_tdi_index_o),
        .tlp_violation_irq_o    (tlp_violation_irq_o),

        .violation_valid_o      (tlp_violation_valid),
        .violation_tdi_o        (tlp_violation_tdi),
        .violation_code_o       (tlp_violation_code),
        .violation_ack_i        (tlp_violation_ack)
    );

    //==========================================================================
    // Output assignments
    //==========================================================================
    always_comb begin
        for (int i = 0; i < NUM_TDI; i++) begin
            tdi_state_out[i] = tdi_states[i];
        end
    end

endmodule : tdisp_top
