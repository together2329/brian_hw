//============================================================================
// TDISP Per-TDI Context Manager
// Stores and manages per-TDI state, lock flags, MMIO ranges, and config
// Single source of truth for all TDI context, accessed by multiple agents
// Per PCIe Base Spec Rev 7.0, Chapter 11
//============================================================================

module tdisp_tdi_mgr #(
    parameter int unsigned NUM_TDI       = 4,
    parameter int unsigned BUS_WIDTH     = 8,    // Max MMIO ranges per TDI
    parameter int unsigned ADDR_WIDTH    = 64,
    parameter int unsigned NONCE_WIDTH   = 256,
    parameter int unsigned INTERFACE_ID_WIDTH = 96
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //=== Context write ports (arbitrated) ====================================

    //--- Port A: LOCK_INTERFACE commit (from tdisp_lock_ctrl) ---
    input  logic                            lock_ctx_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      lock_ctx_tdi_index_i,
    input  tdisp_types::tdisp_state_e       lock_ctx_state_i,
    input  tdisp_types::tdisp_lock_flags_s  lock_ctx_flags_i,
    input  logic [7:0]                      lock_ctx_stream_id_i,
    input  logic [63:0]                     lock_ctx_mmio_offset_i,
    input  logic [63:0]                     lock_ctx_p2p_mask_i,
    input  logic [NONCE_WIDTH-1:0]          lock_ctx_nonce_i,
    input  logic                            lock_ctx_nonce_valid_i,
    input  logic                            lock_ctx_fw_locked_i,

    //--- Port B: State transition (from tdisp_fsm) ---
    input  logic                            fsm_transition_ack_i,
    input  logic [$clog2(NUM_TDI)-1:0]      fsm_tdi_index_i,
    input  tdisp_types::tdisp_state_e       fsm_target_state_i,

    //--- Port C: START_INTERFACE (nonce consumed, transition to RUN) ---
    input  logic                            start_ctx_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      start_ctx_tdi_index_i,
    input  tdisp_types::tdisp_state_e       start_ctx_state_i,

    //--- Port D: STOP_INTERFACE (transition back to CONFIG_LOCKED) ---
    input  logic                            stop_ctx_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      stop_ctx_tdi_index_i,
    input  tdisp_types::tdisp_state_e       stop_ctx_state_i,

    //--- Port E: MMIO range update (from SET_MMIO_ATTRIBUTE) ---
    input  logic                            mmio_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      mmio_tdi_index_i,
    input  logic [$clog2(BUS_WIDTH)-1:0]    mmio_range_index_i,
    input  logic [ADDR_WIDTH-1:0]           mmio_start_addr_i,
    input  logic [31:0]                     mmio_num_pages_i,
    input  logic                            mmio_is_non_tee_i,

    //--- Port F: Error state (from security violation) ---
    input  logic                            error_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      error_tdi_index_i,

    //--- XT mode configuration ---
    input  logic                            xt_mode_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      xt_tdi_index_i,
    input  logic                            xt_enabled_i,

    //--- Interface ID initialization (from firmware/config at boot) ---
    input  logic                            iface_id_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      iface_id_tdi_index_i,
    input  logic [INTERFACE_ID_WIDTH-1:0]   iface_id_value_i,

    //--- Outstanding request tracking ---
    input  logic                            req_count_update_i,
    input  logic [$clog2(NUM_TDI)-1:0]      req_count_tdi_index_i,
    input  logic                            req_count_increment_i, // 1=+1, 0=-1

    //=== Context read ports ==================================================

    //--- TDI lookup by INTERFACE_ID (for message routing) ---
    input  logic [INTERFACE_ID_WIDTH-1:0]   lookup_iface_id_i,
    input  logic                            lookup_valid_i,
    output logic                            lookup_match_o,
    output logic [$clog2(NUM_TDI)-1:0]      lookup_tdi_index_o,
    output tdisp_types::tdisp_state_e       lookup_tdi_state_o,

    //--- Full context read (for message formatter / response builders) ---
    input  logic [$clog2(NUM_TDI)-1:0]      ctx_read_index_i,
    output tdisp_types::tdisp_tdi_context_s ctx_read_data_o,

    //--- Per-TDI state array (for tdisp_tlp_rules) ---
    output tdisp_types::tdisp_state_e       tdi_state_o        [NUM_TDI],
    output logic                            tdi_xt_enabled_o   [NUM_TDI],
    output logic                            tdi_fw_locked_o    [NUM_TDI],
    output logic                            tdi_p2p_enabled_o  [NUM_TDI],
    output logic                            tdi_req_redirect_o [NUM_TDI],

    //--- MMIO range outputs (for tdisp_tlp_rules) ---
    output logic [ADDR_WIDTH-1:0]           mmio_start_addr_o  [NUM_TDI][BUS_WIDTH],
    output logic [31:0]                     mmio_num_pages_o   [NUM_TDI][BUS_WIDTH],
    output logic                            mmio_is_non_tee_o  [NUM_TDI][BUS_WIDTH],
    output logic                            mmio_range_valid_o [NUM_TDI][BUS_WIDTH],

    //--- Outstanding request tracking ---
    output logic [7:0]                      outstanding_reqs_o [NUM_TDI]
);

    import tdisp_types::*;

    //==========================================================================
    // Per-TDI context storage
    //==========================================================================
    tdisp_tdi_context_s tdi_ctx_q [NUM_TDI];

    // MMIO range storage (separate from packed struct for flexible sizing)
    logic [ADDR_WIDTH-1:0] mmio_start_q   [NUM_TDI][BUS_WIDTH];
    logic [31:0]           mmio_pages_q    [NUM_TDI][BUS_WIDTH];
    logic                  mmio_non_tee_q  [NUM_TDI][BUS_WIDTH];
    logic                  mmio_valid_q    [NUM_TDI][BUS_WIDTH];

    //==========================================================================
    // Write port arbitration priorities (highest to lowest):
    //   1. Error (security violation) - immediate transition to ERROR
    //   2. Lock commit (LOCK_INTERFACE)
    //   3. START_INTERFACE commit
    //   4. STOP_INTERFACE commit
    //   5. FSM state transition
    //   6. MMIO range update
    //   7. XT mode update
    //==========================================================================

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int t = 0; t < NUM_TDI; t++) begin
                tdi_ctx_q[t].state              <= TDI_CONFIG_UNLOCKED;
                tdi_ctx_q[t].interface_id       <= '0;
                tdi_ctx_q[t].bound_stream_id    <= '0;
                tdi_ctx_q[t].mmio_reporting_offset <= '0;
                tdi_ctx_q[t].lock_flags         <= '0;
                tdi_ctx_q[t].nonce              <= '0;
                tdi_ctx_q[t].nonce_valid        <= 1'b0;
                tdi_ctx_q[t].msix_locked        <= 1'b0;
                tdi_ctx_q[t].fw_update_locked   <= 1'b0;
                tdi_ctx_q[t].p2p_enabled        <= 1'b0;
                tdi_ctx_q[t].all_req_redirect   <= 1'b0;
                tdi_ctx_q[t].xt_mode_enabled    <= 1'b0;
                tdi_ctx_q[t].outstanding_reqs   <= '0;

                for (int r = 0; r < BUS_WIDTH; r++) begin
                    mmio_start_q[t][r]   <= '0;
                    mmio_pages_q[t][r]   <= '0;
                    mmio_non_tee_q[t][r] <= 1'b0;
                    mmio_valid_q[t][r]   <= 1'b0;
                end
            end
        end else begin
            //=== Priority 1: Error state (unconditional) ===
            if (error_update_i && error_tdi_index_i < NUM_TDI) begin
                tdi_ctx_q[error_tdi_index_i].state <= TDI_ERROR;
                tdi_ctx_q[error_tdi_index_i].nonce_valid <= 1'b0;
            end
            //=== Priority 2: LOCK_INTERFACE commit ===
            else if (lock_ctx_update_i && lock_ctx_tdi_index_i < NUM_TDI) begin
                tdi_ctx_q[lock_ctx_tdi_index_i].state            <= lock_ctx_state_i;
                tdi_ctx_q[lock_ctx_tdi_index_i].lock_flags       <= lock_ctx_flags_i;
                tdi_ctx_q[lock_ctx_tdi_index_i].bound_stream_id  <= lock_ctx_stream_id_i;
                tdi_ctx_q[lock_ctx_tdi_index_i].mmio_reporting_offset <= lock_ctx_mmio_offset_i;
                tdi_ctx_q[lock_ctx_tdi_index_i].nonce            <= lock_ctx_nonce_i;
                tdi_ctx_q[lock_ctx_tdi_index_i].nonce_valid      <= lock_ctx_nonce_valid_i;
                tdi_ctx_q[lock_ctx_tdi_index_i].fw_update_locked <= lock_ctx_fw_locked_i;
                tdi_ctx_q[lock_ctx_tdi_index_i].p2p_enabled      <= lock_ctx_flags_i.bind_p2p;
                tdi_ctx_q[lock_ctx_tdi_index_i].all_req_redirect <= lock_ctx_flags_i.all_request_redirect;
                tdi_ctx_q[lock_ctx_tdi_index_i].msix_locked      <= lock_ctx_flags_i.lock_msix;
            end
            //=== Priority 3: START_INTERFACE commit ===
            else if (start_ctx_update_i && start_ctx_tdi_index_i < NUM_TDI) begin
                tdi_ctx_q[start_ctx_tdi_index_i].state       <= start_ctx_state_i;
                tdi_ctx_q[start_ctx_tdi_index_i].nonce_valid <= 1'b0; // Nonce consumed (one-time)
                tdi_ctx_q[start_ctx_tdi_index_i].nonce       <= '0;
            end
            //=== Priority 4: STOP_INTERFACE commit ===
            else if (stop_ctx_update_i && stop_ctx_tdi_index_i < NUM_TDI) begin
                tdi_ctx_q[stop_ctx_tdi_index_i].state <= stop_ctx_state_i;
                // Retain lock flags, stream ID, etc. — only state changes
            end
            //=== Priority 5: FSM state transition ===
            else if (fsm_transition_ack_i && fsm_tdi_index_i < NUM_TDI) begin
                tdi_ctx_q[fsm_tdi_index_i].state <= fsm_target_state_i;
            end

            //=== Priority 6: MMIO range update (independent of state) ===
            if (mmio_update_i && mmio_tdi_index_i < NUM_TDI &&
                mmio_range_index_i < BUS_WIDTH) begin
                mmio_start_q[mmio_tdi_index_i][mmio_range_index_i]   <= mmio_start_addr_i;
                mmio_pages_q[mmio_tdi_index_i][mmio_range_index_i]   <= mmio_num_pages_i;
                mmio_non_tee_q[mmio_tdi_index_i][mmio_range_index_i] <= mmio_is_non_tee_i;
                mmio_valid_q[mmio_tdi_index_i][mmio_range_index_i]   <= 1'b1;
            end

            //=== Priority 7: XT mode update (independent of state) ===
            if (xt_mode_update_i && xt_tdi_index_i < NUM_TDI) begin
                tdi_ctx_q[xt_tdi_index_i].xt_mode_enabled <= xt_enabled_i;
            end
        end
    end

    //==========================================================================
    // INTERFACE_ID lookup (combinational)
    //==========================================================================
    always_comb begin
        lookup_match_o    = 1'b0;
        lookup_tdi_index_o = '0;
        lookup_tdi_state_o = TDI_CONFIG_UNLOCKED;

        if (lookup_valid_i) begin
            for (int t = 0; t < NUM_TDI; t++) begin
                if (tdi_ctx_q[t].interface_id == lookup_iface_id_i) begin
                    lookup_match_o     = 1'b1;
                    lookup_tdi_index_o = t[$clog2(NUM_TDI)-1:0];
                    lookup_tdi_state_o = tdi_ctx_q[t].state;
                end
            end
        end
    end

    //==========================================================================
    // Full context read port (combinational)
    //==========================================================================
    always_comb begin
        ctx_read_data_o = '0;
        if (ctx_read_index_i < NUM_TDI) begin
            ctx_read_data_o = tdi_ctx_q[ctx_read_index_i];
        end
    end

    //==========================================================================
    // Per-TDI broadcast outputs (for tdisp_tlp_rules)
    //==========================================================================
    always_comb begin
        for (int t = 0; t < NUM_TDI; t++) begin
            tdi_state_o[t]        = tdi_ctx_q[t].state;
            tdi_xt_enabled_o[t]   = tdi_ctx_q[t].xt_mode_enabled;
            tdi_fw_locked_o[t]    = tdi_ctx_q[t].fw_update_locked;
            tdi_p2p_enabled_o[t]  = tdi_ctx_q[t].p2p_enabled;
            tdi_req_redirect_o[t] = tdi_ctx_q[t].all_req_redirect;
            outstanding_reqs_o[t] = tdi_ctx_q[t].outstanding_reqs;

            for (int r = 0; r < BUS_WIDTH; r++) begin
                mmio_start_addr_o[t][r]  = mmio_start_q[t][r];
                mmio_num_pages_o[t][r]   = mmio_pages_q[t][r];
                mmio_is_non_tee_o[t][r]  = mmio_non_tee_q[t][r];
                mmio_range_valid_o[t][r] = mmio_valid_q[t][r];
            end
        end
    end

endmodule : tdisp_tdi_mgr
