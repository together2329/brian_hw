// ============================================================================
// Module:    tdisp_lock_handler.sv
// Purpose:   TDISP Lock Interface Handler u2014 validates LOCK_INTERFACE requests,
//            performs device/IDE configuration checks per u00a711.3.8, generates
//            secure nonces per u00a711.3.9, and manages per-TDI lock state.
// Spec:      PCI Express Base Specification Revision 7.0, Section 11.3
//
// Architecture:
//   1. Receives lock command from tdisp_req_handler.
//   2. Validates in phases: basic u2192 IDE u2192 device config u2192 config binding.
//   3. On success: generates 256-bit nonce, stores lock config, signals done.
//   4. On failure: returns specific error code.
//
// Nonce lifecycle (u00a711.3.9):
//   - Generated on successful LOCK_INTERFACE (TDI enters CONFIG_LOCKED)
//   - Consumed by START_INTERFACE_REQUEST (TDI enters RUN)
//   - Destroyed on STOP or ERROR transition from CONFIG_LOCKED
// ============================================================================

module tdisp_lock_handler
    import tdisp_pkg::*;
#(
    parameter int NUM_TDI     = MAX_NUM_TDI,
    parameter int NUM_PF      = 1,
    parameter int NUM_VF_MAX  = 256,
    parameter int NUM_BARS    = 6
)(
    input  logic clk,
    input  logic rst_n,

    // =========================================================================
    // From req_handler u2014 lock command interface (single TDI at a time)
    // =========================================================================
    input  logic                        lock_cmd_valid,
    input  logic [TDI_INDEX_WIDTH-1:0]  lock_cmd_tdi_idx,
    input  tdisp_lock_req_payload_s     lock_cmd_payload,

    // =========================================================================
    // To req_handler u2014 lock result
    // =========================================================================
    output logic                        lock_done,
    output logic                        lock_error,
    output tdisp_error_code_e           lock_error_code,
    output logic [NONCE_WIDTH-1:0]      lock_nonce_out,
    output logic [TDI_INDEX_WIDTH-1:0]  lock_done_tdi_idx,

    // =========================================================================
    // Per-TDI state (from FSM instances)
    // =========================================================================
    input  tdisp_tdi_state_e            tdi_state [NUM_TDI-1:0],

    // =========================================================================
    // To FSM u2014 lock_req pulse to transition TDI to CONFIG_LOCKED
    // =========================================================================
    output logic [NUM_TDI-1:0]          lock_ack_pulse,

    // =========================================================================
    // Stored nonce output per TDI (for START_INTERFACE validation)
    // =========================================================================
    output logic [NONCE_WIDTH-1:0]      tdi_stored_nonce [NUM_TDI-1:0],

    // =========================================================================
    // To reg_tracker u2014 register snapshot request
    // =========================================================================
    output logic                        lock_snapshot_req,
    output logic [TDI_INDEX_WIDTH-1:0]  lock_snapshot_tdi_idx,
    input  logic                        lock_snapshot_ack,

    // =========================================================================
    // From IDE module u2014 IDE stream configuration
    // =========================================================================
    input  logic                        ide_stream_valid,
    input  logic                        ide_keys_programmed,
    input  logic [7:0]                  ide_default_stream_id,
    input  logic                        ide_xt_enable_setting,
    input  logic [2:0]                  ide_tc_value,

    // =========================================================================
    // SET_TDISP_CONFIG settings (from req_handler)
    // =========================================================================
    input  logic                        xt_mode_enable,
    input  logic                        xt_bit_for_locked_msix,

    // =========================================================================
    // Device configuration inputs
    // =========================================================================
    input  logic                        pf_bar_config_valid [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic [63:0]                 pf_bar_addrs [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic [63:0]                 pf_bar_sizes [NUM_PF-1:0][NUM_BARS-1:0],

    input  logic                        vf_bar_config_valid [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic [63:0]                 vf_bar_addrs [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic [63:0]                 vf_bar_sizes [NUM_PF-1:0][NUM_BARS-1:0],

    input  logic                        phantom_funcs_enabled,
    input  logic                        expansion_rom_valid,
    input  logic [63:0]                 expansion_rom_addr,
    input  logic [63:0]                 expansion_rom_size,
    input  logic                        resizable_bar_sizes_valid,
    input  logic [2:0]                  sr_iov_page_size,
    input  logic [7:0]                  cache_line_size,
    input  logic [1:0]                  tph_mode,

    // =========================================================================
    // TRNG / Entropy source for nonce generation
    // =========================================================================
    output logic                        entropy_req,
    input  logic                        entropy_valid,
    input  logic [NONCE_WIDTH-1:0]      entropy_data
);

    // =========================================================================
    // Lock handler FSM states
    // =========================================================================
    typedef enum logic [3:0] {
        L_IDLE,
        L_PHASE1_BASIC,
        L_PHASE2_IDE,
        L_PHASE3_DEVCFG,
        L_PHASE4_BIND,
        L_GEN_NONCE,
        L_WAIT_SNAPSHOT,
        L_COMPLETE_OK,
        L_COMPLETE_ERR
    } lock_state_e;

    // =========================================================================
    // Internal registers
    // =========================================================================
    lock_state_e              l_state;
    logic [TDI_INDEX_WIDTH-1:0] active_tdi;
    tdisp_lock_req_payload_s  active_payload;
    tdisp_error_code_e        pending_error;

    // Per-TDI stored nonce
    logic [NONCE_WIDTH-1:0]   nonce_reg [NUM_TDI-1:0];

    // Per-TDI stored lock config
    typedef struct packed {
        logic [63:0] mmio_reporting_offset;
        logic [63:0] bind_p2p_addr_mask;
        logic        no_fw_update;
        logic        lock_msix;
        logic        bind_p2p;
        logic        all_request_redirect;
        logic [7:0]  default_stream_id;
    } tdi_lock_config_s;

    tdi_lock_config_s         tdi_lock_cfg [NUM_TDI-1:0];

    // Nonce generation holding register
    logic [NONCE_WIDTH-1:0]   generated_nonce;

    // =========================================================================
    // Outputs from registered state
    // =========================================================================
    logic [NUM_TDI-1:0]       lock_ack_pulse_r;
    logic                     lock_snapshot_req_r;
    logic [TDI_INDEX_WIDTH-1:0] lock_snapshot_tdi_idx_r;
    logic                     entropy_req_r;

    assign lock_ack_pulse       = lock_ack_pulse_r;
    assign lock_snapshot_req    = lock_snapshot_req_r;
    assign lock_snapshot_tdi_idx = lock_snapshot_tdi_idx_r;
    assign entropy_req          = entropy_req_r;

    // =========================================================================
    // BAR overlap check functions
    // =========================================================================

    // Check if two address ranges overlap
    // Range A: [addr_a, addr_a + size_a), Range B: [addr_b, addr_b + size_b)
    function automatic logic ranges_overlap(
        input logic [63:0] addr_a, size_a,
        input logic [63:0] addr_b, size_b
    );
        logic [63:0] a_end, b_end;
        a_end = addr_a + size_a - 64'd1;
        b_end = addr_b + size_b - 64'd1;
        return (addr_a <= b_end) && (addr_b <= a_end);
    endfunction

    // Check all PF BARs for overlaps
    function automatic logic pf_bars_have_overlap(
        input logic [63:0] bar_addrs [NUM_PF-1:0][NUM_BARS-1:0],
        input logic [63:0] bar_sizes [NUM_PF-1:0][NUM_BARS-1:0],
        input logic        bar_valid [NUM_PF-1:0][NUM_BARS-1:0]
    );
        logic [63:0] addr_a, size_a, addr_b, size_b;
        pf_bars_have_overlap = 1'b0;
        for (int pf = 0; pf < NUM_PF; pf++) begin
            for (int bar_a = 0; bar_a < NUM_BARS; bar_a++) begin
                if (bar_valid[pf][bar_a]) begin
                    addr_a = bar_addrs[pf][bar_a];
                    size_a = bar_sizes[pf][bar_a];
                    // Check against expansion ROM
                    if (expansion_rom_valid) begin
                        if (ranges_overlap(addr_a, size_a,
                                           expansion_rom_addr, expansion_rom_size)) begin
                            pf_bars_have_overlap = 1'b1;
                        end
                    end
                    // Check against other BARs in same PF
                    for (int bar_b = bar_a + 1; bar_b < NUM_BARS; bar_b++) begin
                        if (bar_valid[pf][bar_b]) begin
                            addr_b = bar_addrs[pf][bar_b];
                            size_b = bar_sizes[pf][bar_b];
                            if (ranges_overlap(addr_a, size_a, addr_b, size_b)) begin
                                pf_bars_have_overlap = 1'b1;
                            end
                        end
                    end
                    // Check against VF BARs
                    for (int vf_bar = 0; vf_bar < NUM_BARS; vf_bar++) begin
                        if (vf_bar_config_valid[pf][vf_bar]) begin
                            addr_b = vf_bar_addrs[pf][vf_bar];
                            size_b = vf_bar_sizes[pf][vf_bar];
                            if (ranges_overlap(addr_a, size_a, addr_b, size_b)) begin
                                pf_bars_have_overlap = 1'b1;
                            end
                        end
                    end
                end
            end
        end
    endfunction

    // Check VF BARs for overlaps with each other and PF BARs/Expansion ROM
    function automatic logic vf_bars_have_overlap(
        input logic [63:0] vf_addrs [NUM_PF-1:0][NUM_BARS-1:0],
        input logic [63:0] vf_sizes [NUM_PF-1:0][NUM_BARS-1:0],
        input logic        vf_valid [NUM_PF-1:0][NUM_BARS-1:0],
        input logic [63:0] pf_addrs [NUM_PF-1:0][NUM_BARS-1:0],
        input logic [63:0] pf_sizes [NUM_PF-1:0][NUM_BARS-1:0],
        input logic        pf_valid [NUM_PF-1:0][NUM_BARS-1:0]
    );
        logic [63:0] addr_a, size_a, addr_b, size_b;
        vf_bars_have_overlap = 1'b0;
        for (int pf = 0; pf < NUM_PF; pf++) begin
            for (int bar_a = 0; bar_a < NUM_BARS; bar_a++) begin
                if (vf_valid[pf][bar_a]) begin
                    addr_a = vf_addrs[pf][bar_a];
                    size_a = vf_sizes[pf][bar_a];
                    // VF vs expansion ROM
                    if (expansion_rom_valid) begin
                        if (ranges_overlap(addr_a, size_a,
                                           expansion_rom_addr, expansion_rom_size)) begin
                            vf_bars_have_overlap = 1'b1;
                        end
                    end
                    // VF vs PF BARs
                    for (int pf_bar = 0; pf_bar < NUM_BARS; pf_bar++) begin
                        if (pf_valid[pf][pf_bar]) begin
                            addr_b = pf_addrs[pf][pf_bar];
                            size_b = pf_sizes[pf][pf_bar];
                            if (ranges_overlap(addr_a, size_a, addr_b, size_b)) begin
                                vf_bars_have_overlap = 1'b1;
                            end
                        end
                    end
                    // VF vs other VF BARs
                    for (int bar_b = bar_a + 1; bar_b < NUM_BARS; bar_b++) begin
                        if (vf_valid[pf][bar_b]) begin
                            addr_b = vf_addrs[pf][bar_b];
                            size_b = vf_sizes[pf][bar_b];
                            if (ranges_overlap(addr_a, size_a, addr_b, size_b)) begin
                                vf_bars_have_overlap = 1'b1;
                            end
                        end
                    end
                end
            end
        end
    endfunction

    // =========================================================================
    // Combinational: extract lock flags from payload
    // =========================================================================
    tdisp_lock_flags_s  lock_flags;
    logic [7:0]         lock_default_stream_id;
    logic [63:0]        lock_mmio_offset;
    logic [63:0]        lock_bind_p2p_mask;

    always_comb begin
        lock_flags            = tdisp_lock_flags_s'(lock_cmd_payload.flags);
        lock_default_stream_id = lock_cmd_payload.default_stream_id;
        lock_mmio_offset      = lock_cmd_payload.mmio_reporting_offset;
        lock_bind_p2p_mask    = lock_cmd_payload.bind_p2p_addr_mask;
    end

    // For active (latched) payload
    tdisp_lock_flags_s  active_flags;
    logic [7:0]         active_stream_id;
    logic [63:0]        active_mmio_offset;
    logic [63:0]        active_bind_p2p_mask;

    always_comb begin
        active_flags        = tdisp_lock_flags_s'(active_payload.flags);
        active_stream_id    = active_payload.default_stream_id;
        active_mmio_offset  = active_payload.mmio_reporting_offset;
        active_bind_p2p_mask = active_payload.bind_p2p_addr_mask;
    end

    // =========================================================================
    // Drive nonce output array
    // =========================================================================
    always_comb begin
        for (int i = 0; i < NUM_TDI; i++) begin
            tdi_stored_nonce[i] = nonce_reg[i];
        end
    end

    // =========================================================================
    // Main lock handler state machine
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            l_state              <= L_IDLE;
            active_tdi           <= '0;
            active_payload       <= '0;
            pending_error        <= ERR_RESERVED;
            generated_nonce      <= '0;
            lock_done            <= 1'b0;
            lock_error           <= 1'b0;
            lock_error_code      <= ERR_RESERVED;
            lock_nonce_out       <= '0;
            lock_done_tdi_idx    <= '0;
            lock_ack_pulse_r     <= '0;
            lock_snapshot_req_r  <= 1'b0;
            lock_snapshot_tdi_idx_r <= '0;
            entropy_req_r        <= 1'b0;
            for (int i = 0; i < NUM_TDI; i++) begin
                nonce_reg[i]     <= '0;
                tdi_lock_cfg[i]  <= '0;
            end
        end else begin
            // Default: clear pulses and handshake signals
            lock_done            <= 1'b0;
            lock_error           <= 1'b0;
            lock_ack_pulse_r     <= '0;
            lock_snapshot_req_r  <= 1'b0;
            entropy_req_r        <= 1'b0;

            case (l_state)

                // =================================================================
                // L_IDLE: Wait for lock_cmd_valid from req_handler
                // =================================================================
                L_IDLE: begin
                    if (lock_cmd_valid) begin
                        active_tdi     <= lock_cmd_tdi_idx;
                        active_payload <= lock_cmd_payload;
                        l_state        <= L_PHASE1_BASIC;
                    end
                end

                // =================================================================
                // L_PHASE1_BASIC: Check TDI state is CONFIG_UNLOCKED
                // =================================================================
                L_PHASE1_BASIC: begin
                    if (tdi_state[active_tdi] != TDI_STATE_CONFIG_UNLOCKED) begin
                        pending_error <= ERR_INVALID_INTERFACE_STATE;
                        l_state       <= L_COMPLETE_ERR;
                    end else begin
                        l_state       <= L_PHASE2_IDE;
                    end
                end

                // =================================================================
                // L_PHASE2_IDE: Validate IDE configuration (u00a711.3.8)
                //   Checks 3-8: IDE stream validation
                // =================================================================
                L_PHASE2_IDE: begin
                    // Check 3: default_stream_id must match IDE config
                    if (active_stream_id != ide_default_stream_id) begin
                        pending_error <= ERR_INVALID_REQUEST;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 4: All sub-stream keys must be programmed
                    else if (!ide_keys_programmed) begin
                        pending_error <= ERR_INVALID_REQUEST;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 6: IDE stream must be valid (only one default)
                    else if (!ide_stream_valid) begin
                        pending_error <= ERR_INVALID_REQUEST;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 7: Default stream TC must be TC0
                    else if (ide_tc_value != 3'd0) begin
                        pending_error <= ERR_INVALID_REQUEST;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 8: XT Enable must match SET_TDISP_CONFIG setting
                    else if (ide_xt_enable_setting != xt_mode_enable) begin
                        pending_error <= ERR_INVALID_REQUEST;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    else begin
                        l_state <= L_PHASE3_DEVCFG;
                    end
                end

                // =================================================================
                // L_PHASE3_DEVCFG: Validate device configuration (u00a711.3.8)
                //   Checks 9-17: Device config validation
                // =================================================================
                L_PHASE3_DEVCFG: begin
                    // Check 9: Phantom Functions must not be enabled
                    if (phantom_funcs_enabled) begin
                        pending_error <= ERR_INVALID_DEVICE_CONFIGURATION;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 10/11: PF BARs must not overlap each other or Exp ROM
                    else if (pf_bars_have_overlap(pf_bar_addrs, pf_bar_sizes,
                                                  pf_bar_config_valid)) begin
                        pending_error <= ERR_INVALID_DEVICE_CONFIGURATION;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 12: Resizable BAR sizes must be supported
                    else if (!resizable_bar_sizes_valid) begin
                        pending_error <= ERR_INVALID_DEVICE_CONFIGURATION;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 13/14: VF BARs must not overlap PF BARs or Exp ROM
                    else if (vf_bars_have_overlap(vf_bar_addrs, vf_bar_sizes,
                                                  vf_bar_config_valid,
                                                  pf_bar_addrs, pf_bar_sizes,
                                                  pf_bar_config_valid)) begin
                        pending_error <= ERR_INVALID_DEVICE_CONFIGURATION;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 15: SR-IOV page size must be supported (0=4KB, 1=8KB..4=64KB)
                    else if (sr_iov_page_size > 3'd4) begin
                        pending_error <= ERR_INVALID_DEVICE_CONFIGURATION;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 16: Cache Line Size must be valid (32, 64, 128)
                    else if (cache_line_size != 8'd32 &&
                             cache_line_size != 8'd64 &&
                             cache_line_size != 8'd128) begin
                        pending_error <= ERR_INVALID_DEVICE_CONFIGURATION;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    // Check 17: TPH mode must be supported (0=disabled, 1=enabled)
                    else if (tph_mode > 2'd1) begin
                        pending_error <= ERR_INVALID_DEVICE_CONFIGURATION;
                        l_state       <= L_COMPLETE_ERR;
                    end
                    else begin
                        l_state <= L_PHASE4_BIND;
                    end
                end

                // =================================================================
                // L_PHASE4_BIND: Store lock configuration (u00a711.3.8 Phase 4)
                //   Checks 18-23: Config binding
                // =================================================================
                L_PHASE4_BIND: begin
                    // Store lock configuration for this TDI
                    tdi_lock_cfg[active_tdi].mmio_reporting_offset  <= active_mmio_offset;
                    tdi_lock_cfg[active_tdi].no_fw_update           <= active_flags.no_fw_update;
                    tdi_lock_cfg[active_tdi].lock_msix              <= active_flags.lock_msix;
                    tdi_lock_cfg[active_tdi].bind_p2p               <= active_flags.bind_p2p;
                    tdi_lock_cfg[active_tdi].all_request_redirect   <= active_flags.all_request_redirect;
                    tdi_lock_cfg[active_tdi].default_stream_id      <= active_stream_id;
                    tdi_lock_cfg[active_tdi].bind_p2p_addr_mask     <= active_bind_p2p_mask;

                    // Proceed to nonce generation
                    l_state <= L_GEN_NONCE;
                end

                // =================================================================
                // L_GEN_NONCE: Request entropy and generate 256-bit nonce
                //   Per u00a711.3.9 u2014 if insufficient entropy, return error
                // =================================================================
                L_GEN_NONCE: begin
                    entropy_req_r <= 1'b1;
                    if (entropy_valid) begin
                        generated_nonce <= entropy_data;
                        entropy_timeout <= '0;
                        l_state         <= L_WAIT_SNAPSHOT;
                    end else begin
                        // Timeout: if entropy not available after ~65K cycles,
                        // return INSUFFICIENT_ENTROPY per u00a711.3.9
                        entropy_timeout <= entropy_timeout + 16'd1;
                        if (entropy_timeout >= 16'hFFFF) begin
                            pending_error   <= ERR_INSUFFICIENT_ENTROPY;
                            entropy_timeout <= '0;
                            l_state         <= L_COMPLETE_ERR;
                        end
                    end
                end

                // =================================================================
                // L_WAIT_SNAPSHOT: Request register snapshot from reg_tracker
                //   Per u00a711.3.9 u2014 lock registers and take baseline snapshot
                // =================================================================
                L_WAIT_SNAPSHOT: begin
                    lock_snapshot_req_r    <= 1'b1;
                    lock_snapshot_tdi_idx_r <= active_tdi;
                    if (lock_snapshot_ack) begin
                        l_state <= L_COMPLETE_OK;
                    end
                end

                // =================================================================
                // L_COMPLETE_OK: Lock successful u2014 store nonce, pulse FSM
                // =================================================================
                L_COMPLETE_OK: begin
                    // Store nonce for START_INTERFACE validation
                    nonce_reg[active_tdi] <= generated_nonce;

                    // Pulse FSM to transition TDI to CONFIG_LOCKED
                    lock_ack_pulse_r[active_tdi] <= 1'b1;

                    // Return success to req_handler with nonce
                    lock_done         <= 1'b1;
                    lock_error        <= 1'b0;
                    lock_error_code   <= ERR_RESERVED;
                    lock_nonce_out    <= generated_nonce;
                    lock_done_tdi_idx <= active_tdi;

                    l_state <= L_IDLE;
                end

                // =================================================================
                // L_COMPLETE_ERR: Lock failed u2014 return error to req_handler
                // =================================================================
                L_COMPLETE_ERR: begin
                    lock_done         <= 1'b1;
                    lock_error        <= 1'b1;
                    lock_error_code   <= pending_error;
                    lock_nonce_out    <= '0;
                    lock_done_tdi_idx <= active_tdi;

                    l_state <= L_IDLE;
                end

                default: l_state <= L_IDLE;
            endcase

            // =================================================================
            // Nonce lifecycle management u2014 destroy on state transitions
            //   Per u00a711.3.9:
            //   - Destroy nonce when TDI leaves CONFIG_LOCKED/RUN to
            //     CONFIG_UNLOCKED or ERROR
            //   - Inlined here to avoid multi-driver on nonce_reg[]
            //   - Guard: don't clobber nonce just written in L_COMPLETE_OK
            // =================================================================
            for (int i = 0; i < NUM_TDI; i++) begin
                if (tdi_state[i] != TDI_STATE_CONFIG_LOCKED &&
                    tdi_state[i] != TDI_STATE_RUN) begin
                    if (!(l_state == L_COMPLETE_OK &&
                          active_tdi == TDI_INDEX_WIDTH'(i))) begin
                        nonce_reg[i] <= '0;
                    end
                end
            end
        end
    end

    // =========================================================================
    // Assertions
    // =========================================================================
    // pragma synthesis_off
    `ifdef FORMAL
        // Assert: lock_done is single-cycle pulse
        assert property (@(posedge clk) disable iff (!rst_n)
            lock_done |-> ##1 !lock_done)
        else $error("lock_done must be single-cycle pulse");

        // Assert: lock_ack_pulse is single-cycle
        assert property (@(posedge clk) disable iff (!rst_n)
            |lock_ack_pulse |-> ##1 (lock_ack_pulse == '0))
        else $error("lock_ack_pulse must be single-cycle");

        // Cover: successful lock sequence
        cover property (@(posedge clk) disable iff (!rst_n)
            lock_cmd_valid ##1 l_state == L_PHASE1_BASIC ##1
            l_state == L_PHASE2_IDE ##1 l_state == L_PHASE3_DEVCFG ##1
            l_state == L_PHASE4_BIND ##1 l_state == L_GEN_NONCE ##1
            l_state == L_WAIT_SNAPSHOT ##1 l_state == L_COMPLETE_OK ##1
            l_state == L_IDLE && lock_done && !lock_error);

        // Cover: error path
        cover property (@(posedge clk) disable iff (!rst_n)
            lock_cmd_valid ##1 l_state == L_PHASE1_BASIC ##1
            l_state == L_COMPLETE_ERR ##1
            l_state == L_IDLE && lock_done && lock_error);
    `endif
    // pragma synthesis_on

endmodule : tdisp_lock_handler
