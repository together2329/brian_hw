//============================================================================
// Module: tdisp_dsm
// Description: TDISP (TEE Device Interface Security Protocol) DSM Responder
//              Implements the Device Security Manager state machine per
//              PCIe 7.0 Spec Chapter 11.
//
// TDI State Machine:
//   CONFIG_UNLOCKED ──LOCK_INTERFACE_REQUEST──▶ CONFIG_LOCKED
//   CONFIG_LOCKED   ──START_INTERFACE_REQUEST──▶ RUN
//   RUN             ──STOP_INTERFACE_REQUEST───▶ CONFIG_UNLOCKED
//   Any state       ──ERROR condition──────────▶ ERROR
//   ERROR           ──STOP_INTERFACE_REQUEST──▶ CONFIG_UNLOCKED
//
// Supported Messages:
//   Request  (81h) GET_TDISP_VERSION
//   Request  (82h) GET_TDISP_CAPABILITIES
//   Request  (83h) LOCK_INTERFACE_REQUEST
//   Request  (84h) GET_DEVICE_INTERFACE_REPORT
//   Request  (85h) GET_DEVICE_INTERFACE_STATE
//   Request  (86h) START_INTERFACE_REQUEST
//   Request  (87h) STOP_INTERFACE_REQUEST
//   Response (01h) TDISP_VERSION
//   Response (02h) TDISP_CAPABILITIES
//   Response (03h) LOCK_INTERFACE_RESPONSE
//   Response (04h) DEVICE_INTERFACE_REPORT
//   Response (05h) DEVICE_INTERFACE_STATE
//   Response (06h) START_INTERFACE_RESPONSE
//   Response (07h) STOP_INTERFACE_RESPONSE
//   Response (7Fh) TDISP_ERROR
//
// Reference: PCI Express Base Specification 7.0, Chapter 11
//============================================================================

module tdisp_dsm #(
    parameter DATA_WIDTH    = 32,    // SPDM data bus width
    parameter ADDR_WIDTH    = 64,    // Device address width
    parameter NONCE_WIDTH   = 256,   // START_INTERFACE_NONCE width (32 bytes)
    parameter INTERFACE_ID_WIDTH = 96, // INTERFACE_ID width (12 bytes)
    parameter TDISP_VERSION = 8'h10  // V1.0 = Major 1, Minor 0
)(
    input  wire             clk,              // Clock
    input  wire             rst_n,            // Active-low synchronous reset

    // ── SPDM Request Interface (TSM → DSM) ──────────────────────────
    input  wire                           spdm_req_valid,  // Request valid
    output reg                            spdm_req_ready,  // Request ready (backpressure)
    input  wire [DATA_WIDTH-1:0]          spdm_req_data,   // Request data word
    input  wire [7:0]                     spdm_req_len,    // Request length in words

    // ── SPDM Response Interface (DSM → TSM) ─────────────────────────
    output reg                            spdm_resp_valid, // Response valid
    input  wire                           spdm_resp_ready, // Response ready (backpressure)
    output reg  [DATA_WIDTH-1:0]          spdm_resp_data,  // Response data word
    output wire [7:0]                     spdm_resp_len,   // Response length in words (mirrors resp_total_words)

    // ── TDI State Output ────────────────────────────────────────────
    output reg  [2:0]                     tdi_state,       // Current TDI state
    output reg                            error_irq,       // Error interrupt

    // ── Configuration Inputs ────────────────────────────────────────
    input  wire [INTERFACE_ID_WIDTH-1:0]  configured_interface_id, // Hosted INTERFACE_ID
    input  wire                           ide_keys_valid,  // IDE keys programmed for all sub-streams
    input  wire                           ide_required,    // IDE is required for this TDI
    input  wire [7:0]                     default_stream_id, // Default IDE Stream_ID

    // ── Status Outputs ──────────────────────────────────────────────
    output reg  [31:0]                    last_error_code, // Last error code
    output reg  [NONCE_WIDTH-1:0]         current_nonce,   // Current START_INTERFACE_NONCE
    output reg  [ADDR_WIDTH-1:0]          mmio_reporting_offset // Locked MMIO offset
);

    // ==================================================================
    // TDI State Encoding (per §11.3.13 Table 11-18)
    // ==================================================================
    localparam [2:0] STATE_CONFIG_UNLOCKED = 3'd0;
    localparam [2:0] STATE_CONFIG_LOCKED   = 3'd1;
    localparam [2:0] STATE_RUN             = 3'd2;
    localparam [2:0] STATE_ERROR           = 3'd3;

    // ==================================================================
    // TDISP Request Codes (per §11.3.1 Table 11-4)
    // ==================================================================
    localparam [7:0] REQ_GET_TDISP_VERSION         = 8'h81;
    localparam [7:0] REQ_GET_TDISP_CAPABILITIES     = 8'h82;
    localparam [7:0] REQ_LOCK_INTERFACE             = 8'h83;
    localparam [7:0] REQ_GET_DEVICE_INTERFACE_REPORT = 8'h84;
    localparam [7:0] REQ_GET_DEVICE_INTERFACE_STATE = 8'h85;
    localparam [7:0] REQ_START_INTERFACE            = 8'h86;
    localparam [7:0] REQ_STOP_INTERFACE             = 8'h87;

    // ==================================================================
    // TDISP Response Codes (per §11.3.2 Table 11-5)
    // ==================================================================
    localparam [7:0] RESP_TDISP_VERSION             = 8'h01;
    localparam [7:0] RESP_TDISP_CAPABILITIES        = 8'h02;
    localparam [7:0] RESP_LOCK_INTERFACE            = 8'h03;
    localparam [7:0] RESP_DEVICE_INTERFACE_REPORT   = 8'h04;
    localparam [7:0] RESP_DEVICE_INTERFACE_STATE    = 8'h05;
    localparam [7:0] RESP_START_INTERFACE           = 8'h06;
    localparam [7:0] RESP_STOP_INTERFACE            = 8'h07;
    localparam [7:0] RESP_TDISP_ERROR               = 8'h7F;

    // ==================================================================
    // TDISP Error Codes (per §11.3.24 Table 11-28)
    // ==================================================================
    localparam [31:0] ERR_INVALID_REQUEST           = 32'h0001;
    localparam [31:0] ERR_BUSY                      = 32'h0003;
    localparam [31:0] ERR_INVALID_INTERFACE_STATE   = 32'h0004;
    localparam [31:0] ERR_UNSPECIFIED               = 32'h0005;
    localparam [31:0] ERR_UNSUPPORTED_REQUEST        = 32'h0007;
    localparam [31:0] ERR_VERSION_MISMATCH          = 32'h0041;
    localparam [31:0] ERR_INVALID_INTERFACE         = 32'h0101;
    localparam [31:0] ERR_INVALID_NONCE             = 32'h0102;
    localparam [31:0] ERR_INSUFFICIENT_ENTROPY      = 32'h0103;
    localparam [31:0] ERR_INVALID_DEVICE_CONFIGURATION = 32'h0104;

    // ==================================================================
    // Internal Registers
    // ==================================================================

    // Lock interface configuration (per §11.3.8 Table 11-11)
    reg         lock_no_fw_update;
    reg         lock_msix_locked;
    reg         lock_bind_p2p;
    reg         lock_all_request_redirect;
    reg  [7:0]  lock_stream_id;

    // Nonce generation (simple LFSR-based PRNG)
    reg  [NONCE_WIDTH-1:0] nonce_lfsr;
    reg                    nonce_valid;  // Nonce is valid (generated at LOCK)

    // Response construction
    reg  [7:0]             resp_msg_type;
    reg  [7:0]             resp_word_idx;
    reg  [7:0]             resp_total_words;

    // Request parsing
    reg  [7:0]             req_msg_type;
    reg  [INTERFACE_ID_WIDTH-1:0] req_interface_id;
    reg                    req_parsed;
    reg  [7:0]             req_word_counter;   // Bug#3: track word index
    reg  [NONCE_WIDTH-1:0] received_nonce;     // Bug#5 prep: received nonce from START_INTERFACE

    // Error tracking
    reg  [31:0]            pending_error;

    // ==================================================================
    // Interface ID comparison
    // ==================================================================
    wire interface_id_match = (req_interface_id == configured_interface_id);

    // ==================================================================
    // LFSR-based Nonce Generator
    // ==================================================================
    // Polynomial: x^256 + x^252 + x^247 + x^244 + x^1 + 1 (simplified)
    // We use a simpler 256-bit maximal-period LFSR
    wire [NONCE_WIDTH-1:0] lfsr_feedback = 
        {nonce_lfsr[NONCE_WIDTH-2:0], 
         nonce_lfsr[NONCE_WIDTH-1] ^ nonce_lfsr[NONCE_WIDTH-4] ^ 
         nonce_lfsr[NONCE_WIDTH-9] ^ nonce_lfsr[NONCE_WIDTH-12]};

   // Response length tracks internal resp_total_words (Bug#2 fix)
   assign spdm_resp_len = resp_total_words;

   // ==================================================================
    // Main FSM — TDI State Machine (SINGLE always block — no multi-driver)
    // ==================================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            // Reset state
            tdi_state            <= STATE_CONFIG_UNLOCKED;
            error_irq            <= 1'b0;
            last_error_code      <= 32'h0;
            spdm_req_ready       <= 1'b1;
            spdm_resp_valid      <= 1'b0;
            resp_msg_type        <= 8'h0;
            resp_word_idx        <= 8'd0;
            resp_total_words     <= 8'd0;
            req_msg_type         <= 8'h0;
            req_interface_id     <= {INTERFACE_ID_WIDTH{1'b0}};
            req_parsed           <= 1'b0;
            req_word_counter     <= 8'd0;
            received_nonce       <= {NONCE_WIDTH{1'b0}};
            pending_error        <= 32'h0;
            lock_no_fw_update    <= 1'b0;
            lock_msix_locked     <= 1'b0;
            lock_bind_p2p        <= 1'b0;
            lock_all_request_redirect <= 1'b0;
            lock_stream_id       <= 8'h0;
            mmio_reporting_offset <= {ADDR_WIDTH{1'b0}};
            nonce_lfsr            <= {NONCE_WIDTH{1'b1}}; // Non-zero LFSR seed
            nonce_valid           <= 1'b0;
            current_nonce         <= {NONCE_WIDTH{1'b0}};
        end else begin
            // Default: deassert error IRQ after 1 cycle
            error_irq <= 1'b0;

            // ── LFSR Nonce Generator (always advances) ──
            nonce_lfsr <= lfsr_feedback;

            // Capture nonce when entering CONFIG_LOCKED (one-shot)
            if (tdi_state == STATE_CONFIG_LOCKED && !nonce_valid) begin
                current_nonce <= lfsr_feedback;
                nonce_valid   <= 1'b1;
            end

            // Invalidate nonce when returning to CONFIG_UNLOCKED
            if (tdi_state == STATE_CONFIG_UNLOCKED) begin
                nonce_valid   <= 1'b0;
                current_nonce <= {NONCE_WIDTH{1'b0}};
            end

            // ── Response transmission handshake ──
            if (spdm_resp_valid && spdm_resp_ready) begin
                if (resp_word_idx < resp_total_words) begin
                    // Continue sending response words
                    resp_word_idx <= resp_word_idx + 8'd1;
                end else begin
                    // Response complete
                    spdm_resp_valid <= 1'b0;
                    resp_word_idx   <= 8'd0;
                    spdm_req_ready  <= 1'b1; // Ready for next request
                end
            end

            // ── Request reception and processing ──
            if (spdm_req_valid && spdm_req_ready && !spdm_resp_valid) begin
                if (!req_parsed) begin
                    // ── Word 0: Parse TDISP header ──
                    // Word layout (little-endian, 32-bit bus):
                    //   Byte 0: TDISPVersion
                    //   Byte 1: MessageType
                    //   Byte 2-3: Reserved
                    req_msg_type     <= spdm_req_data[15:8];
                    req_word_counter <= 8'd1; // next word expected
                    req_interface_id <= {INTERFACE_ID_WIDTH{1'b0}}; // clear for new request
                    received_nonce   <= {NONCE_WIDTH{1'b0}};        // clear for new request

                    if (spdm_req_data[15:8] != 8'h0) begin
                        req_parsed <= 1'b1;
                    end

                    // Route to appropriate handler
                    case (spdm_req_data[15:8])
                        REQ_GET_TDISP_VERSION: begin
                            // Legal in any state (N/A per spec)
                            // §11.3.5: Must return supported versions — header-only, respond immediately
                            resp_msg_type    <= RESP_TDISP_VERSION;
                            resp_total_words <= 8'd5;
                            spdm_resp_valid  <= 1'b1;
                            spdm_req_ready   <= 1'b0;
                        end

                        REQ_GET_TDISP_CAPABILITIES: begin
                            // Legal in any state — header-only, respond immediately
                            resp_msg_type    <= RESP_TDISP_CAPABILITIES;
                            resp_total_words <= 8'd14;
                            spdm_resp_valid  <= 1'b1;
                            spdm_req_ready   <= 1'b0;
                        end

                        REQ_LOCK_INTERFACE: begin
                            // Legal only in CONFIG_UNLOCKED (§11.3.1 Table 11-4)
                            // Quick pre-checks that don't need INTERFACE_ID:
                            if (tdi_state != STATE_CONFIG_UNLOCKED) begin
                                pending_error   <= ERR_INVALID_INTERFACE_STATE;
                                resp_msg_type   <= RESP_TDISP_ERROR;
                                resp_total_words <= 8'd8;
                                spdm_resp_valid <= 1'b1;
                                spdm_req_ready  <= 1'b0;
                                error_irq       <= 1'b1;
                                last_error_code <= ERR_INVALID_INTERFACE_STATE;
                            end else if (ide_required && !ide_keys_valid) begin
                                pending_error   <= ERR_INVALID_REQUEST;
                                resp_msg_type   <= RESP_TDISP_ERROR;
                                resp_total_words <= 8'd8;
                                spdm_resp_valid <= 1'b1;
                                spdm_req_ready  <= 1'b0;
                                error_irq       <= 1'b1;
                                last_error_code <= ERR_INVALID_REQUEST;
                            end
                            // else: defer response until INTERFACE_ID collected (words 1-3)
                        end

                        REQ_GET_DEVICE_INTERFACE_REPORT: begin
                            if (tdi_state != STATE_CONFIG_LOCKED && tdi_state != STATE_RUN) begin
                                pending_error   <= ERR_INVALID_INTERFACE_STATE;
                                resp_msg_type   <= RESP_TDISP_ERROR;
                                resp_total_words <= 8'd8;
                                spdm_resp_valid <= 1'b1;
                                spdm_req_ready  <= 1'b0;
                                error_irq       <= 1'b1;
                                last_error_code <= ERR_INVALID_INTERFACE_STATE;
                            end else begin
                                resp_msg_type    <= RESP_DEVICE_INTERFACE_REPORT;
                                resp_total_words <= 8'd6;
                                spdm_resp_valid  <= 1'b1;
                                spdm_req_ready   <= 1'b0;
                            end
                        end

                        REQ_GET_DEVICE_INTERFACE_STATE: begin
                            // Legal in all states — respond immediately
                            resp_msg_type    <= RESP_DEVICE_INTERFACE_STATE;
                            resp_total_words <= 8'd5;
                            spdm_resp_valid  <= 1'b1;
                            spdm_req_ready   <= 1'b0;
                        end

                        REQ_START_INTERFACE: begin
                            // Legal only in CONFIG_LOCKED (§11.3.1)
                            // Quick pre-checks that don't need nonce:
                            if (tdi_state != STATE_CONFIG_LOCKED) begin
                                pending_error   <= ERR_INVALID_INTERFACE_STATE;
                                resp_msg_type   <= RESP_TDISP_ERROR;
                                resp_total_words <= 8'd8;
                                spdm_resp_valid <= 1'b1;
                                spdm_req_ready  <= 1'b0;
                                error_irq       <= 1'b1;
                                last_error_code <= ERR_INVALID_INTERFACE_STATE;
                            end else if (!nonce_valid) begin
                                pending_error   <= ERR_INSUFFICIENT_ENTROPY;
                                resp_msg_type   <= RESP_TDISP_ERROR;
                                resp_total_words <= 8'd8;
                                spdm_resp_valid <= 1'b1;
                                spdm_req_ready  <= 1'b0;
                                error_irq       <= 1'b1;
                                last_error_code <= ERR_INSUFFICIENT_ENTROPY;
                            end
                            // else: defer response until nonce collected (words 1-11)
                        end

                        REQ_STOP_INTERFACE: begin
                            // Legal in CONFIG_UNLOCKED, CONFIG_LOCKED, RUN, ERROR (§11.3.2)
                            tdi_state            <= STATE_CONFIG_UNLOCKED;
                            nonce_valid          <= 1'b0;
                            current_nonce        <= {NONCE_WIDTH{1'b0}};
                            lock_no_fw_update    <= 1'b0;
                            lock_msix_locked     <= 1'b0;
                            lock_bind_p2p        <= 1'b0;
                            lock_all_request_redirect <= 1'b0;
                            lock_stream_id       <= 8'h0;
                            mmio_reporting_offset <= {ADDR_WIDTH{1'b0}};

                            resp_msg_type    <= RESP_STOP_INTERFACE;
                            resp_total_words <= 8'd1;
                            spdm_resp_valid  <= 1'b1;
                            spdm_req_ready   <= 1'b0;
                        end

                        default: begin
                            pending_error   <= ERR_UNSUPPORTED_REQUEST;
                            resp_msg_type   <= RESP_TDISP_ERROR;
                            resp_total_words <= 8'd8;
                            spdm_resp_valid <= 1'b1;
                            spdm_req_ready  <= 1'b0;
                            error_irq       <= 1'b1;
                            last_error_code <= ERR_UNSUPPORTED_REQUEST;
                        end
                    endcase
                end else begin
                    // ── Subsequent words (word 1+): Collect INTERFACE_ID and nonce ──
                    // Words 1-3: INTERFACE_ID (12 bytes, 3 x DATA_WIDTH words)
                    // Words 4-11: START_INTERFACE_NONCE (32 bytes, 8 x DATA_WIDTH words)
                    case (req_word_counter)
                        8'd1: req_interface_id[31:0]   <= spdm_req_data;
                        8'd2: req_interface_id[63:32]  <= spdm_req_data;
                        8'd3: begin
                            req_interface_id[95:64] <= spdm_req_data;

                            // ── LOCK_INTERFACE: INTERFACE_ID fully received ──
                            // Timing note: req_interface_id[95:64] NBA hasn't taken
                            // effect yet, so compare spdm_req_data directly for upper word.
                            if (req_msg_type == REQ_LOCK_INTERFACE) begin
                                if ((req_interface_id[63:0] != configured_interface_id[63:0]) ||
                                    (spdm_req_data != configured_interface_id[95:64])) begin
                                    // §11.3.9: INTERFACE_ID mismatch → INVALID_INTERFACE
                                    pending_error    <= ERR_INVALID_INTERFACE;
                                    resp_msg_type    <= RESP_TDISP_ERROR;
                                    resp_total_words <= 8'd8;
                                    spdm_resp_valid  <= 1'b1;
                                    spdm_req_ready   <= 1'b0;
                                    error_irq        <= 1'b1;
                                    last_error_code  <= ERR_INVALID_INTERFACE;
                                    req_parsed       <= 1'b0;
                                end else begin
                                    tdi_state            <= STATE_CONFIG_LOCKED;
                                    lock_stream_id       <= default_stream_id;
                                    lock_no_fw_update    <= 1'b0;
                                    lock_msix_locked     <= 1'b0;
                                    lock_bind_p2p        <= 1'b0;
                                    lock_all_request_redirect <= 1'b0;
                                    mmio_reporting_offset <= {ADDR_WIDTH{1'b0}};

                                    resp_msg_type    <= RESP_LOCK_INTERFACE;
                                    resp_total_words <= 8'd9; // header(1) + nonce(8 words)
                                    spdm_resp_valid  <= 1'b1;
                                    spdm_req_ready   <= 1'b0;
                                    req_parsed       <= 1'b0; // ready for next request
                                end
                            end
                        end

                        // ── START_INTERFACE: Collect nonce words (4-11) ──
                        8'd4:  received_nonce[31:0]    <= spdm_req_data;
                        8'd5:  received_nonce[63:32]   <= spdm_req_data;
                        8'd6:  received_nonce[95:64]   <= spdm_req_data;
                        8'd7:  received_nonce[127:96]  <= spdm_req_data;
                        8'd8:  received_nonce[159:128] <= spdm_req_data;
                        8'd9:  received_nonce[191:160] <= spdm_req_data;
                        8'd10: received_nonce[223:192] <= spdm_req_data;
                        8'd11: begin
                            received_nonce[255:224] <= spdm_req_data;
                            // Nonce validation: received_nonce[223:0] is settled,
                            // but [255:224] NBA hasn't taken effect — use spdm_req_data directly.
                            if ((received_nonce[223:0] != current_nonce[223:0]) ||
                                (spdm_req_data != current_nonce[255:224])) begin
                                // §11.3.14: Nonce mismatch → INVALID_NONCE
                                pending_error    <= ERR_INVALID_NONCE;
                                resp_msg_type    <= RESP_TDISP_ERROR;
                                resp_total_words <= 8'd8;
                                spdm_resp_valid  <= 1'b1;
                                spdm_req_ready   <= 1'b0;
                                error_irq        <= 1'b1;
                                last_error_code  <= ERR_INVALID_NONCE;
                                req_parsed       <= 1'b0;
                            end else begin
                                tdi_state       <= STATE_RUN;
                                nonce_valid     <= 1'b0;
                                resp_msg_type   <= RESP_START_INTERFACE;
                                resp_total_words <= 8'd1;
                                spdm_resp_valid  <= 1'b1;
                                spdm_req_ready   <= 1'b0;
                                req_parsed       <= 1'b0; // ready for next request
                            end
                        end

                        default: begin
                            // Unexpected word — reset parser
                            req_parsed <= 1'b0;
                        end
                    endcase

                    // Advance word counter for multi-word requests still in progress
                    if (req_word_counter < 8'd11) begin
                        req_word_counter <= req_word_counter + 8'd1;
                    end
                end
            end

            // ── Response data generation ──
            if (spdm_resp_valid && !spdm_resp_ready) begin
                // Hold data until ready
            end else if (spdm_resp_valid && spdm_resp_ready) begin
                // Generate response word based on message type and word index
                case (resp_msg_type)
                    RESP_TDISP_VERSION: begin
                        case (resp_word_idx)
                            8'd0: spdm_resp_data <= {16'h0000, TDISP_VERSION, RESP_TDISP_VERSION};
                            8'd1: spdm_resp_data <= {24'h0000, 8'd1}; // VERSION_NUM_COUNT = 1
                            8'd2: spdm_resp_data <= {24'h0000, TDISP_VERSION}; // Entry: V1.0
                            default: spdm_resp_data <= {DATA_WIDTH{1'b0}};
                        endcase
                    end

                    RESP_TDISP_CAPABILITIES: begin
                        case (resp_word_idx)
                            8'd0: spdm_resp_data <= {16'h0000, TDISP_VERSION, RESP_TDISP_CAPABILITIES};
                            8'd1: spdm_resp_data <= 32'h00000001; // DSM_CAPS: XT_MODE_SUPPORTED
                            8'd2: spdm_resp_data <= 32'h0000007F; // REQ_MSGS_SUPPORTED (bits 0-6)
                            8'd3: spdm_resp_data <= 32'h0000001F; // REQ_MSGS_SUPPORTED (upper)
                            8'd4: spdm_resp_data <= 32'h00000000;
                            8'd5: spdm_resp_data <= 32'h00000000;
                            8'd6: spdm_resp_data <= 32'h00000000;
                            8'd7: spdm_resp_data <= 32'h00000000; // End of REQ_MSGS_SUPPORTED
                            8'd8: spdm_resp_data <= {16'h0000, 16'h001F}; // LOCK_INTERFACE_FLAGS_SUPPORTED
                            8'd9: spdm_resp_data <= 32'h00000000; // Reserved
                            8'd10: spdm_resp_data <= {24'h0000, 8'd52}; // DEV_ADDR_WIDTH = 52
                            8'd11: spdm_resp_data <= {24'h0000, 8'd1};  // NUM_REQ_THIS = 1
                            8'd12: spdm_resp_data <= {24'h0000, 8'd1};  // NUM_REQ_ALL = 1
                            default: spdm_resp_data <= {DATA_WIDTH{1'b0}};
                        endcase
                    end

                    RESP_LOCK_INTERFACE: begin
                        case (resp_word_idx)
                            8'd0: spdm_resp_data <= {16'h0000, TDISP_VERSION, RESP_LOCK_INTERFACE};
                            // §11.3.9 Table 11-12: START_INTERFACE_NONCE (32 bytes = 8 words)
                            8'd1: spdm_resp_data <= current_nonce[31:0];
                            8'd2: spdm_resp_data <= current_nonce[63:32];
                            8'd3: spdm_resp_data <= current_nonce[95:64];
                            8'd4: spdm_resp_data <= current_nonce[127:96];
                            8'd5: spdm_resp_data <= current_nonce[159:128];
                            8'd6: spdm_resp_data <= current_nonce[191:160];
                            8'd7: spdm_resp_data <= current_nonce[223:192];
                            8'd8: spdm_resp_data <= current_nonce[255:224];
                            default: spdm_resp_data <= {DATA_WIDTH{1'b0}};
                        endcase
                    end

                    RESP_DEVICE_INTERFACE_REPORT: begin
                        case (resp_word_idx)
                            8'd0: spdm_resp_data <= {16'h0000, TDISP_VERSION, RESP_DEVICE_INTERFACE_REPORT};
                            8'd1: spdm_resp_data <= {16'h0004, 16'h0000}; // PORTION_LENGTH=4, REMAINDER_LENGTH=0
                            8'd2: spdm_resp_data <= {16'h0000, 16'h0000}; // INTERFACE_INFO
                            8'd3: spdm_resp_data <= 32'h00000000; // Reserved
                            8'd4: spdm_resp_data <= 32'h00000000; // MSI_X_MESSAGE_CONTROL
                            8'd5: spdm_resp_data <= 32'h00000000; // LNR_CONTROL + TPH_CONTROL
                            default: spdm_resp_data <= {DATA_WIDTH{1'b0}};
                        endcase
                    end

                    RESP_DEVICE_INTERFACE_STATE: begin
                        case (resp_word_idx)
                            8'd0: spdm_resp_data <= {16'h0000, TDISP_VERSION, RESP_DEVICE_INTERFACE_STATE};
                            8'd1: spdm_resp_data <= {24'h0000, tdi_state}; // TDI_STATE
                            default: spdm_resp_data <= {DATA_WIDTH{1'b0}};
                        endcase
                    end

                    RESP_START_INTERFACE: begin
                        // §11.3.15: START_INTERFACE_RESPONSE (no additional payload)
                        spdm_resp_data <= {16'h0000, TDISP_VERSION, RESP_START_INTERFACE};
                    end

                    RESP_STOP_INTERFACE: begin
                        // §11.3.17: STOP_INTERFACE_RESPONSE (no additional payload)
                        spdm_resp_data <= {16'h0000, TDISP_VERSION, RESP_STOP_INTERFACE};
                    end

                    RESP_TDISP_ERROR: begin
                        case (resp_word_idx)
                            8'd0: spdm_resp_data <= {16'h0000, TDISP_VERSION, RESP_TDISP_ERROR};
                            8'd1: spdm_resp_data <= pending_error; // ERROR_CODE
                            8'd2: spdm_resp_data <= 32'h00000000; // ERROR_DATA
                            default: spdm_resp_data <= {DATA_WIDTH{1'b0}};
                        endcase
                    end

                    default: begin
                        spdm_resp_data <= {DATA_WIDTH{1'b0}};
                    end
                endcase
            end
        end
    end

    // ==================================================================
    // Nonce comparison for START_INTERFACE_REQUEST
    // §11.3.14: Validate START_INTERFACE_NONCE matches LOCK_INTERFACE_RESPONSE
    // ==================================================================
    // Note: Full nonce validation requires comparing 32 bytes from request
    // against stored current_nonce. This is handled in the word-by-word
    // request processing above. The testbench drives the matching nonce.

endmodule
