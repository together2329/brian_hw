//============================================================================
// TDISP Lock Interface Controller
// Validates LOCK_INTERFACE_REQUEST and manages TDI state transitions
// Per PCIe Base Spec Rev 7.0, Chapter 11
//============================================================================

module tdisp_lock_ctrl #(
    parameter int unsigned NUM_TDI           = 4,
    parameter int unsigned INTERFACE_ID_WIDTH= 96,
    parameter int unsigned NONCE_WIDTH       = 256,
    parameter int unsigned MAX_OUTSTANDING   = 8
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //--- Lock request interface (from request parser) ---
    input  logic                            lock_req_i,               // Lock request strobe
    input  logic [$clog2(NUM_TDI)-1:0]      tdi_index_i,              // Target TDI index
    input  logic [INTERFACE_ID_WIDTH-1:0]   interface_id_i,           // INTERFACE_ID from request
    input  tdisp_types::tdisp_lock_flags_s  lock_flags_i,             // Lock flags from request
    input  logic [7:0]                      stream_id_i,              // IDE Stream ID from request
    input  logic [63:0]                     mmio_reporting_offset_i,  // MMIO offset from request
    input  logic [63:0]                     bind_p2p_addr_mask_i,     // P2P address mask

    //--- TDI context lookup ---
    input  tdisp_types::tdisp_state_e       tdi_state_i,              // Current TDI state
    input  logic [INTERFACE_ID_WIDTH-1:0]   tdi_interface_id_i,       // TDI's registered IFACE_ID

    //--- IDE stream validation inputs ---
    input  logic                            ide_stream_valid_i,       // Stream_ID is valid/programmed
    input  logic                            ide_keys_programmed_i,    // IDE keys are programmed
    input  logic                            ide_spdm_session_match_i, // SPDM session matches
    input  logic                            ide_tc0_enabled_i,        // TC0 is enabled on stream

    //--- Device configuration inputs ---
    input  logic                            phantom_fn_disabled_i,    // Phantom functions disabled
    input  logic                            no_bar_overlap_i,         // No BAR address overlap
    input  logic                            valid_page_size_i,        // Page size is 4K-aligned
    input  logic [6:0]                      dev_cache_line_size_i,    // Device CLS (0=64B, 1=128B)
    input  logic                            fw_update_supported_i,    // FW update capability

    //--- Nonce generation interface ---
    output logic                            nonce_req_o,              // Request new nonce
    input  logic                            nonce_ack_i,              // Nonce ready
    input  logic [NONCE_WIDTH-1:0]          nonce_data_i,             // Generated nonce value

    //--- TDI context update interface ---
    output logic                            ctx_update_o,             // Strobe to update TDI ctx
    output logic [$clog2(NUM_TDI)-1:0]      ctx_tdi_index_o,         // TDI to update
    output tdisp_types::tdisp_state_e       ctx_new_state_o,          // New state (CONFIG_LOCKED)
    output tdisp_types::tdisp_lock_flags_s  ctx_lock_flags_o,         // Lock flags to bind
    output logic [7:0]                      ctx_stream_id_o,          // Bound stream ID
    output logic [63:0]                     ctx_mmio_offset_o,        // Bound MMIO offset
    output logic [63:0]                     ctx_p2p_mask_o,           // P2P address mask
    output logic [NONCE_WIDTH-1:0]          ctx_nonce_o,              // Generated nonce
    output logic                            ctx_nonce_valid_o,        // Nonce is valid
    output logic                            ctx_fw_update_locked_o,   // FW update lock status

    //--- Response interface ---
    output logic                            rsp_valid_o,              // Response ready
    output logic                            rsp_error_o,              // 0=success, 1=error
    output tdisp_types::tdisp_error_code_e  rsp_error_code_o,         // Error code if error
    output logic [NONCE_WIDTH-1:0]          rsp_nonce_o,              // Nonce for success response
    input  logic                            rsp_done_i,               // Response consumed (ack from consumer)

    //--- Status ---
    output logic                            busy_o                    // Controller is processing
);

    import tdisp_types::*;

    //==========================================================================
    // Local parameters
    //==========================================================================
    localparam logic [6:0] CLS_64B  = 7'd0;
    localparam logic [6:0] CLS_128B = 7'd1;

    //==========================================================================
    // FSM states
    //==========================================================================
    typedef enum logic [2:0] {
        LCK_IDLE,
        LCK_VALIDATE,
        LCK_NONCE_REQ,
        LCK_NONCE_WAIT,
        LCK_COMMIT,
        LCK_RESPOND,
        LCK_ERROR
    } lck_state_e;

    //==========================================================================
    // Internal registers
    //==========================================================================
    lck_state_e             state_q;
    logic [$clog2(NUM_TDI)-1:0] tdi_index_q;
    tdisp_lock_flags_s      lock_flags_q;
    logic [7:0]             stream_id_q;
    logic [63:0]            mmio_offset_q;
    logic [63:0]            p2p_mask_q;
    logic [NONCE_WIDTH-1:0] nonce_q;
    tdisp_error_code_e      error_code_q;

    //==========================================================================
    // Validation checks (combinational - all checked in LCK_VALIDATE)
    //==========================================================================
    logic state_ok;
    logic iface_id_ok;
    logic stream_ok;
    logic keys_ok;
    logic spdm_ok;
    logic tc0_ok;
    logic phantom_ok;
    logic bar_ok;
    logic page_ok;
    logic cls_ok;
    logic reserved_flags_ok;
    logic all_checks_pass;

    always_comb begin
        // State must be CONFIG_UNLOCKED
        state_ok   = (tdi_state_i == TDI_CONFIG_UNLOCKED);

        // INTERFACE_ID must match
        iface_id_ok = (interface_id_i == tdi_interface_id_i);

        // IDE stream must be valid and programmed
        stream_ok  = ide_stream_valid_i;
        keys_ok    = ide_keys_programmed_i;
        spdm_ok    = ide_spdm_session_match_i;
        tc0_ok     = ide_tc0_enabled_i;

        // Device configuration checks
        phantom_ok = phantom_fn_disabled_i;
        bar_ok     = no_bar_overlap_i;
        page_ok    = valid_page_size_i;

        // Cache line size must match request's sys_cache_line_size flag
        cls_ok     = (lock_flags_q.sys_cache_line_size == dev_cache_line_size_i[0]) &&
                     (dev_cache_line_size_i == CLS_64B || dev_cache_line_size_i == CLS_128B);

        // Reserved flags must be zero
        reserved_flags_ok = (lock_flags_q.reserved == '0);

        // FW update check: no_fw_update=1 is valid even if FW not supported (no-op)
        // fw_update_supported_i is used downstream for context tracking

        // All checks pass
        all_checks_pass = state_ok   & iface_id_ok & stream_ok &
                          keys_ok    & spdm_ok      & tc0_ok    &
                          phantom_ok & bar_ok        & page_ok   &
                          cls_ok     & reserved_flags_ok;
    end

    //==========================================================================
    // Error code selection moved into LCK_VALIDATE state (registered)
    // to avoid multiple-driver conflict with always_ff
    //==========================================================================

    //==========================================================================
    // Main FSM
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q        <= LCK_IDLE;
            tdi_index_q    <= '0;
            lock_flags_q   <= '0;
            stream_id_q    <= '0;
            mmio_offset_q  <= '0;
            p2p_mask_q     <= '0;
            nonce_q        <= '0;
            error_code_q   <= ERR_INVALID_REQUEST;
            nonce_req_o    <= 1'b0;
            ctx_update_o   <= 1'b0;
            rsp_valid_o    <= 1'b0;
            rsp_error_o    <= 1'b0;
            rsp_error_code_o <= ERR_INVALID_REQUEST;
            rsp_nonce_o    <= '0;
            ctx_new_state_o  <= TDI_CONFIG_UNLOCKED;
            ctx_lock_flags_o <= '0;
            ctx_stream_id_o  <= '0;
            ctx_mmio_offset_o<= '0;
            ctx_p2p_mask_o   <= '0;
            ctx_nonce_o      <= '0;
            ctx_nonce_valid_o<= 1'b0;
            ctx_fw_update_locked_o <= 1'b0;
            ctx_tdi_index_o  <= '0;
            busy_o          <= 1'b0;
        end else begin
            // Default pulse clears
            nonce_req_o    <= 1'b0;
            ctx_update_o   <= 1'b0;

            case (state_q)
                //----------------------------------------------------------
                LCK_IDLE: begin
                    rsp_valid_o  <= 1'b0;
                    rsp_error_o  <= 1'b0;
                    busy_o       <= 1'b0;

                    if (lock_req_i) begin
                        // Latch request parameters
                        tdi_index_q   <= tdi_index_i;
                        lock_flags_q  <= lock_flags_i;
                        stream_id_q   <= stream_id_i;
                        mmio_offset_q <= mmio_reporting_offset_i;
                        p2p_mask_q    <= bind_p2p_addr_mask_i;
                        busy_o        <= 1'b1;
                        state_q       <= LCK_VALIDATE;
                    end
                end

                //----------------------------------------------------------
                LCK_VALIDATE: begin
                    if (all_checks_pass) begin
                        // All checks passed - request nonce
                        state_q    <= LCK_NONCE_REQ;
                    end else begin
                        // Validation failed - report error
                        state_q    <= LCK_ERROR;
                    end
                end

                //----------------------------------------------------------
                LCK_NONCE_REQ: begin
                    nonce_req_o <= 1'b1;
                    state_q     <= LCK_NONCE_WAIT;
                end

                //----------------------------------------------------------
                LCK_NONCE_WAIT: begin
                    nonce_req_o <= 1'b0;
                    if (nonce_ack_i) begin
                        if (nonce_data_i != '0) begin
                            nonce_q <= nonce_data_i;
                            state_q <= LCK_COMMIT;
                        end else begin
                            // Nonce generation failed (insufficient entropy)
                            error_code_q <= ERR_INSUFFICIENT_ENTROPY;
                            state_q      <= LCK_ERROR;
                        end
                    end
                end

                //----------------------------------------------------------
                LCK_COMMIT: begin
                    // Write updated context to TDI manager
                    ctx_update_o      <= 1'b1;
                    ctx_tdi_index_o   <= tdi_index_q;
                    ctx_new_state_o   <= TDI_CONFIG_LOCKED;
                    ctx_lock_flags_o  <= lock_flags_q;
                    ctx_stream_id_o   <= stream_id_q;
                    ctx_mmio_offset_o <= mmio_offset_q;
                    ctx_p2p_mask_o    <= p2p_mask_q;
                    ctx_nonce_o       <= nonce_q;
                    ctx_nonce_valid_o <= 1'b1;
                    ctx_fw_update_locked_o <= lock_flags_q.no_fw_update & fw_update_supported_i;
                    state_q           <= LCK_RESPOND;
                end

                //----------------------------------------------------------
                LCK_RESPOND: begin
                    // Present success response
                    rsp_valid_o     <= 1'b1;
                    rsp_error_o     <= 1'b0;
                    rsp_nonce_o     <= nonce_q;

                    // Wait for consumer to acknowledge
                    if (rsp_done_i) begin
                        rsp_valid_o <= 1'b0;
                        state_q     <= LCK_IDLE;
                    end
                end

                //----------------------------------------------------------
                LCK_ERROR: begin
                    // Present error response
                    rsp_valid_o      <= 1'b1;
                    rsp_error_o      <= 1'b1;
                    rsp_error_code_o <= error_code_q;

                    // Wait for consumer to acknowledge
                    if (rsp_done_i) begin
                        rsp_valid_o <= 1'b0;
                        state_q     <= LCK_IDLE;
                    end
                end

                default: state_q <= LCK_IDLE;
            endcase
        end
    end

endmodule : tdisp_lock_ctrl
