// ============================================================================
// Module:    tdisp_top.sv
// Purpose:   TDISP Top-Level Integration Module u2014 wires all TDISP sub-modules
//            into a coherent subsystem. One instance serves an entire device.
// Spec:      PCI Express Base Specification Revision 7.0, Section 11
//
// Instance Hierarchy:
//   tdisp_top
//   u251cu2500u2500 tdisp_msg_codec          u_codec        (shared message parser/encoder)
//   u251cu2500u2500 tdisp_req_handler        u_req_handler  (shared request dispatch/response)
//   u2514u2500u2500 gen_tdi[0:NUM_TDI-1]
//       u251cu2500u2500 tdisp_fsm           u_fsm          (per-TDI state machine)
//       u251cu2500u2500 tdisp_lock_handler  u_lock         (per-TDI lock validation)
//       u251cu2500u2500 tdisp_reg_tracker   u_reg_tracker  (per-TDI register monitoring)
//       u2514u2500u2500 tdisp_tlp_filter    u_tlp_filter   (per-TDI egress/ingress filtering)
//
// Clocking: Single clock domain (clk/rst_n). All TDISP processing occurs in the
//           same domain as the DOE transport interface.
// ============================================================================

module tdisp_top
    import tdisp_pkg::*;
#(
    // -------------------------------------------------------------------------
    // TDI count and topology
    // -------------------------------------------------------------------------
    parameter int NUM_TDI         = MAX_NUM_TDI,     // Number of TDI instances (1..16)
    parameter int NUM_PF          = 1,                // Physical functions
    parameter int NUM_VF_MAX      = 256,              // Max virtual functions
    parameter int NUM_BARS        = 6,                // BARs per function

    // -------------------------------------------------------------------------
    // P2P stream resources
    // -------------------------------------------------------------------------
    parameter int NUM_P2P_STREAMS = MAX_P2P_STREAMS,  // P2P streams per TDI

    // -------------------------------------------------------------------------
    // Data-path widths
    // -------------------------------------------------------------------------
    parameter int DATA_WIDTH      = 8,                // DOE transport beat width
    parameter int TLP_DATA_WIDTH  = 128,              // TLP flit data width
    parameter int ADDR_TYPE_WIDTH = 2,                // TLP address type field
    parameter int ADDR_WIDTH      = 64,               // PCIe address width

    // -------------------------------------------------------------------------
    // Register tracker config space widths
    // -------------------------------------------------------------------------
    parameter int REG_ADDR_WIDTH  = 12,               // Config space address width
    parameter int REG_DATA_WIDTH  = 32,               // Config space data width
    parameter int REG_MASK_WIDTH  = REG_DATA_WIDTH / 8,

    // -------------------------------------------------------------------------
    // Buffer depths
    // -------------------------------------------------------------------------
    parameter int REPORT_BUF_SIZE = MAX_REPORT_SIZE   // Max payload buffer (bytes)
)(
    input  logic clk,
    input  logic rst_n,

    // =========================================================================
    // SPDM/DOE Transport Interface (AXI-S-like, byte-serial)
    // =========================================================================
    input  logic                      rx_valid,
    input  logic [DATA_WIDTH-1:0]     rx_data,
    input  logic                      rx_last,
    output logic                      rx_ready,

    output logic                      tx_valid,
    output logic [DATA_WIDTH-1:0]     tx_data,
    output logic                      tx_last,
    input  logic                      tx_ready,

    // =========================================================================
    // Negotiated TDISP Version (set during SPDM version negotiation)
    // =========================================================================
    input  logic [7:0]                negotiated_version,
    input  logic                      version_valid,

    // =========================================================================
    // Device Capabilities & Interface Report (static / slow-changing)
    // =========================================================================
    input  tdisp_caps_s               device_caps,
    input  logic [7:0]                report_data [REPORT_BUF_SIZE-1:0],
    input  logic [15:0]               report_total_len,

    // =========================================================================
    // INTERFACE_ID Mapping (96-bit per TDI, set during device init)
    // =========================================================================
    input  logic [INTERFACE_ID_WIDTH-1:0] hosted_interface_ids [NUM_TDI-1:0],

    // =========================================================================
    // Outstanding request counts (maintained by external DOE/discovery layer)
    // =========================================================================
    input  logic [7:0]                num_req_this_config [NUM_TDI-1:0],
    input  logic [7:0]                num_req_all_config,

    // =========================================================================
    // IDE Stream Interface (per-TDI IDE configuration)
    // =========================================================================
    input  logic                      ide_stream_valid,
    input  logic                      ide_keys_programmed,
    input  logic [7:0]                ide_default_stream_id,
    input  logic                      ide_xt_enable_setting,
    input  logic [2:0]                ide_tc_value,

    // =========================================================================
    // P2P Stream Binding Status (from IDE subsystem)
    // =========================================================================
    input  logic [MAX_P2P_STREAMS-1:0] p2p_stream_bound [NUM_TDI-1:0],

    // =========================================================================
    // Device Configuration u2014 BAR / Expansion ROM / Misc (for lock validation)
    // =========================================================================
    input  logic                      pf_bar_config_valid [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic [63:0]               pf_bar_addrs [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic [63:0]               pf_bar_sizes [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic                      vf_bar_config_valid [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic [63:0]               vf_bar_addrs [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic [63:0]               vf_bar_sizes [NUM_PF-1:0][NUM_BARS-1:0],
    input  logic                      phantom_funcs_enabled,
    input  logic                      expansion_rom_valid,
    input  logic [63:0]               expansion_rom_addr,
    input  logic [63:0]               expansion_rom_size,
    input  logic                      resizable_bar_sizes_valid,
    input  logic [2:0]                sr_iov_page_size,
    input  logic [7:0]                cache_line_size,
    input  logic [1:0]                tph_mode,

    // =========================================================================
    // TRNG / Entropy Source (for nonce generation during LOCK_INTERFACE)
    // =========================================================================
    input  logic                      trng_valid,
    input  logic [NONCE_WIDTH-1:0]    trng_data,

    // =========================================================================
    // Per-TDI Config Space Register Write Events (for reg_tracker)
    //   Each TDI receives writes targeting its function(s).
    // =========================================================================
    input  logic [NUM_TDI-1:0]                  reg_write_valid_per_tdi,
    input  logic [REG_ADDR_WIDTH-1:0]            reg_write_addr_per_tdi  [NUM_TDI-1:0],
    input  logic [REG_DATA_WIDTH-1:0]            reg_write_data_per_tdi  [NUM_TDI-1:0],
    input  logic [REG_MASK_WIDTH-1:0]            reg_write_mask_per_tdi  [NUM_TDI-1:0],

    // Capability base addresses (per TDI, discovered during PCIe enumeration)
    input  logic [REG_ADDR_WIDTH-1:0]            pcie_cap_base_per_tdi   [NUM_TDI-1:0],
    input  logic [REG_ADDR_WIDTH-1:0]            msix_cap_base_per_tdi   [NUM_TDI-1:0],
    input  logic [REG_ADDR_WIDTH-1:0]            pm_cap_base_per_tdi     [NUM_TDI-1:0],

    // =========================================================================
    // Per-TDI Egress TLP Interface (TDI as Requester u2014 outgoing TLPs)
    // =========================================================================
    input  logic [NUM_TDI-1:0]                  eg_tlp_valid_per_tdi,
    input  logic [TLP_DATA_WIDTH-1:0]            eg_tlp_data_per_tdi     [NUM_TDI-1:0],
    input  logic [NUM_TDI-1:0]                  eg_tlp_last_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_tlp_is_memory_req_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_tlp_is_completion_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_tlp_is_msi_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_tlp_is_msix_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_tlp_is_msix_locked_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_tlp_is_ats_request_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_tlp_is_vdm_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_tlp_is_io_req_per_tdi,
    input  logic [ADDR_TYPE_WIDTH-1:0]           eg_tlp_addr_type_per_tdi [NUM_TDI-1:0],
    input  logic [NUM_TDI-1:0]                  eg_access_tee_mem_per_tdi,
    input  logic [NUM_TDI-1:0]                  eg_access_non_tee_mem_per_tdi,

    // Egress filtered outputs (per TDI)
    output logic [NUM_TDI-1:0]                  eg_tlp_out_valid_per_tdi,
    output logic [TLP_DATA_WIDTH-1:0]            eg_tlp_out_data_per_tdi [NUM_TDI-1:0],
    output logic [NUM_TDI-1:0]                  eg_tlp_out_last_per_tdi,
    output logic [NUM_TDI-1:0]                  eg_tlp_xt_bit_per_tdi,
    output logic [NUM_TDI-1:0]                  eg_tlp_t_bit_per_tdi,
    output logic [NUM_TDI-1:0]                  eg_tlp_reject_per_tdi,

    // =========================================================================
    // Per-TDI Ingress TLP Interface (TDI as Completer u2014 incoming TLPs)
    // =========================================================================
    input  logic [NUM_TDI-1:0]                  ig_tlp_valid_per_tdi,
    input  logic [TLP_DATA_WIDTH-1:0]            ig_tlp_data_per_tdi     [NUM_TDI-1:0],
    input  logic [NUM_TDI-1:0]                  ig_tlp_last_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_tlp_xt_bit_in_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_tlp_t_bit_in_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_tlp_is_memory_req_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_tlp_is_completion_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_tlp_is_vdm_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_tlp_is_ats_request_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_tlp_target_is_non_tee_mem_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_tlp_on_bound_stream_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_ide_required_per_tdi,
    input  logic [NUM_TDI-1:0]                  ig_msix_table_locked_per_tdi,

    // Ingress filtered outputs (per TDI)
    output logic [NUM_TDI-1:0]                  ig_tlp_out_valid_per_tdi,
    output logic [TLP_DATA_WIDTH-1:0]            ig_tlp_out_data_per_tdi [NUM_TDI-1:0],
    output logic [NUM_TDI-1:0]                  ig_tlp_out_last_per_tdi,
    output logic [NUM_TDI-1:0]                  ig_tlp_reject_per_tdi,

    // =========================================================================
    // VDM Pass-through (optional vendor-specific handler)
    // =========================================================================
    output logic                                 vdm_req_valid,
    output logic [INTERFACE_ID_WIDTH-1:0]        vdm_req_interface_id,
    output logic [7:0]                           vdm_req_payload [REPORT_BUF_SIZE-1:0],
    output logic [15:0]                          vdm_req_payload_len,
    input  logic                                 vdm_resp_ready,

    // =========================================================================
    // P2P Stream Bind/Unbind (from req_handler, to IDE subsystem)
    // =========================================================================
    output logic [7:0]                           bind_stream_id,
    output logic [NUM_TDI-1:0]                   bind_pulse,
    output logic [NUM_TDI-1:0]                   unbind_pulse,

    // =========================================================================
    // MMIO Attribute Update (for SET_MMIO_ATTRIBUTE, to device MMIO manager)
    // =========================================================================
    output logic                                 mmio_attr_update_valid,
    output logic [TDI_INDEX_WIDTH-1:0]           mmio_attr_tdi_idx,
    output tdisp_set_mmio_attr_req_s             mmio_attr_update_data,

    // =========================================================================
    // External Reset (FLR / Conventional Reset u2014 resets all TDIs to UNLOCKED)
    // =========================================================================
    input  logic                                 reset_to_unlocked,

    // =========================================================================
    // Status / Interrupt Outputs
    // =========================================================================
    output logic [NUM_TDI-1:0]                   tdi_error_irq,
    output tdisp_tdi_state_e                     tdi_state_out [NUM_TDI-1:0]
);

    // =========================================================================
    // Internal Wiring u2014 Codec u2194 Req Handler
    // =========================================================================
    tdisp_msg_header_s   parsed_hdr;
    logic [7:0]          parsed_payload [REPORT_BUF_SIZE-1:0];
    logic [15:0]         parsed_payload_len;
    logic                parsed_valid;
    logic                parsed_error;

    logic                resp_valid;
    logic                resp_ready;
    tdisp_resp_code_e    resp_msg_type;
    logic [INTERFACE_ID_WIDTH-1:0] resp_interface_id;
    logic [7:0]          resp_payload [MAX_REPORT_SIZE-1:0];
    logic [15:0]         resp_payload_len;

    // =========================================================================
    // Internal Wiring u2014 Req Handler u2194 FSMs / Lock Handler
    // =========================================================================
    logic [NUM_TDI-1:0]  lock_req_pulse;
    logic [NUM_TDI-1:0]  start_req_pulse;
    logic [NUM_TDI-1:0]  stop_req_pulse;

    // Lock command interface (req_handler u2192 lock_handler)
    logic                               lock_cmd_valid_w;
    logic [TDI_INDEX_WIDTH-1:0]         lock_cmd_tdi_idx_w;
    tdisp_lock_req_payload_s            lock_cmd_payload_w;

    // Lock result (lock_handler u2192 req_handler)
    logic                               lock_done_w;
    logic                               lock_error_w;
    tdisp_error_code_e                  lock_error_code_w;
    logic [NONCE_WIDTH-1:0]             lock_nonce_out_w;
    logic [TDI_INDEX_WIDTH-1:0]         lock_done_tdi_idx_w;

    // SET_TDISP_CONFIG outputs (from req_handler)
    logic                               xt_mode_enable_w;
    logic                               xt_bit_for_locked_msix_w;

    // =========================================================================
    // Internal Wiring u2014 Per-TDI state bus
    // =========================================================================
    tdisp_tdi_state_e   tdi_state_bus [NUM_TDI-1:0];
    logic [NONCE_WIDTH-1:0] tdi_stored_nonce_bus [NUM_TDI-1:0];

    // =========================================================================
    // Internal Wiring u2014 Lock Handler u2194 FSMs
    // =========================================================================
    logic [NUM_TDI-1:0]  lock_ack_pulse_w;

    // =========================================================================
    // Internal Wiring u2014 Lock Handler u2194 Reg Tracker (snapshot)
    // =========================================================================
    logic                lock_snapshot_req_w;
    logic [TDI_INDEX_WIDTH-1:0] lock_snapshot_tdi_idx_w;
    logic                lock_snapshot_ack_w;

    // =========================================================================
    // Internal Wiring u2014 TRNG Entropy
    // =========================================================================
    logic                entropy_req_w;
    logic                entropy_valid_w;
    logic [NONCE_WIDTH-1:0] entropy_data_w;

    // =========================================================================
    // Shared Instance: tdisp_msg_codec
    //   Parser: rx u2192 parsed request    Encoder: response u2192 tx
    // =========================================================================
    tdisp_msg_codec #(
        .DATA_WIDTH      (DATA_WIDTH),
        .MAX_REPORT_SIZE (MAX_REPORT_SIZE)
    ) u_codec (
        .clk                (clk),
        .rst_n              (rst_n),

        // Negotiated version
        .negotiated_version (negotiated_version),
        .version_valid      (version_valid),

        // RX interface (from DOE)
        .rx_valid           (rx_valid),
        .rx_data            (rx_data),
        .rx_last            (rx_last),
        .rx_ready           (rx_ready),

        // Parsed request output u2192 req_handler
        .parsed_hdr         (parsed_hdr),
        .parsed_payload     (parsed_payload),
        .parsed_payload_len (parsed_payload_len),
        .parsed_valid       (parsed_valid),
        .parsed_error       (parsed_error),

        // TX interface (to DOE)
        .tx_valid           (tx_valid),
        .tx_data            (tx_data),
        .tx_last            (tx_last),
        .tx_ready           (tx_ready),

        // Response input u2190 req_handler
        .resp_valid         (resp_valid),
        .resp_ready         (resp_ready),
        .resp_msg_type      (resp_msg_type),
        .resp_interface_id  (resp_interface_id),
        .resp_payload       (resp_payload),
        .resp_payload_len   (resp_payload_len)
    );

    // =========================================================================
    // Shared Instance: tdisp_req_handler
    //   Dispatches parsed requests to correct TDI's FSM / lock handler,
    //   collects results, generates response messages.
    // =========================================================================
    tdisp_req_handler #(
        .NUM_TDI         (NUM_TDI),
        .MAX_REPORT_SIZE (MAX_REPORT_SIZE)
    ) u_req_handler (
        .clk                (clk),
        .rst_n              (rst_n),

        // From codec parser
        .parsed_valid       (parsed_valid),
        .parsed_hdr         (parsed_hdr),
        .parsed_payload     (parsed_payload),
        .parsed_payload_len (parsed_payload_len),

        // To codec encoder
        .resp_valid         (resp_valid),
        .resp_ready         (resp_ready),
        .resp_msg_type      (resp_msg_type),
        .resp_interface_id  (resp_interface_id),
        .resp_payload       (resp_payload),
        .resp_payload_len   (resp_payload_len),

        // Per-TDI state bus
        .tdi_state          (tdi_state_bus),
        .tdi_stored_nonce   (tdi_stored_nonce_bus),

        // To FSMs u2014 control pulses
        .lock_req_pulse     (lock_req_pulse),
        .start_req_pulse    (start_req_pulse),
        .stop_req_pulse     (stop_req_pulse),

        // To lock_handler u2014 lock command
        .lock_cmd_valid     (lock_cmd_valid_w),
        .lock_cmd_tdi_idx   (lock_cmd_tdi_idx_w),
        .lock_cmd_payload   (lock_cmd_payload_w),

        // From lock_handler u2014 lock result
        .lock_done          (lock_done_w),
        .lock_error         (lock_error_w),
        .lock_error_code    (lock_error_code_w),
        .lock_nonce_out     (lock_nonce_out_w),
        .lock_done_tdi_idx  (lock_done_tdi_idx_w),

        // Device configuration
        .device_caps             (device_caps),
        .num_req_this_config     (num_req_this_config),
        .num_req_all_config      (num_req_all_config),
        .report_data             (report_data),
        .report_total_len        (report_total_len),
        .hosted_interface_ids    (hosted_interface_ids),

        // VDM pass-through
        .vdm_req_valid           (vdm_req_valid),
        .vdm_req_interface_id    (vdm_req_interface_id),
        .vdm_req_payload         (vdm_req_payload),
        .vdm_req_payload_len     (vdm_req_payload_len),
        .vdm_resp_ready          (vdm_resp_ready),

        // SET_TDISP_CONFIG outputs
        .xt_mode_enable          (xt_mode_enable_w),
        .xt_bit_for_locked_msix  (xt_bit_for_locked_msix_w),

        // P2P stream management
        .p2p_stream_bound        (p2p_stream_bound),
        .bind_stream_id          (bind_stream_id),
        .bind_pulse              (bind_pulse),
        .unbind_pulse            (unbind_pulse),

        // MMIO attribute update
        .mmio_attr_update_valid  (mmio_attr_update_valid),
        .mmio_attr_tdi_idx       (mmio_attr_tdi_idx),
        .mmio_attr_update_data   (mmio_attr_update_data)
    );

    // =========================================================================
    // TRNG Entropy Gate
    //   The lock_handler drives entropy_req. We gate trng_valid with the
    //   request to produce entropy_valid_w only when requested.
    // =========================================================================
    assign entropy_valid_w = entropy_req_w & trng_valid;
    assign entropy_data_w  = trng_data;

    // =========================================================================
    // Lock Snapshot Ack
    //   In this integration, the reg_tracker snapshot is combinatorially
    //   acknowledged since the lock_handler snapshot request is handled
    //   within the same clock domain without queuing.
    // =========================================================================
    assign lock_snapshot_ack_w = lock_snapshot_req_w;

    // =========================================================================
    // Generate Per-TDI Instances
    //   Each TDI gets: FSM, Lock Handler, Register Tracker, TLP Filter
    // =========================================================================
    for (genvar i = 0; i < NUM_TDI; i++) begin : gen_tdi

        // -----------------------------------------------------------------
        // Per-TDI internal wires
        // -----------------------------------------------------------------
        logic                               error_trigger_w;
        logic                               state_is_locked_w;
        logic                               state_is_run_w;
        logic                               state_is_error_w;
        logic                               ev_entered_error_w;

        // =========================================================================
        // Per-TDI Instance: tdisp_fsm
        // =========================================================================
        tdisp_fsm #(
            .TDI_INDEX (i)
        ) u_fsm (
            .clk                (clk),
            .rst_n              (rst_n),

            // Transition requests
            .lock_req           (lock_req_pulse[i] | lock_ack_pulse_w[i]),
            .start_req          (start_req_pulse[i]),
            .stop_req           (stop_req_pulse[i]),
            .error_trigger      (error_trigger_w),
            .reset_to_unlocked  (reset_to_unlocked),

            // State outputs
            .current_state      (tdi_state_bus[i]),
            .state_is_locked    (state_is_locked_w),
            .state_is_run       (state_is_run_w),
            .state_is_error     (state_is_error_w),

            // Event outputs
            .ev_entered_locked  (),
            .ev_entered_run     (),
            .ev_exited_locked   (),
            .ev_entered_error   (ev_entered_error_w),
            .ev_nonce_valid     (),

            // Nonce interface
            .nonce_out          (),
            .nonce_in           (lock_nonce_out_w)
        );

        // =========================================================================
        // Per-TDI Instance: tdisp_lock_handler
        //   Single shared lock_handler is instantiated outside the generate.
        //   Per-TDI wiring (stored nonce, lock_ack_pulse) connects via the bus.
        //   The lock command/result interface is shared across all TDIs with
        //   arbitration handled inside lock_handler via lock_cmd_tdi_idx.
        // =========================================================================

        // =========================================================================
        // Per-TDI Instance: tdisp_reg_tracker
        // =========================================================================
        tdisp_reg_tracker #(
            .REG_ADDR_WIDTH (REG_ADDR_WIDTH),
            .REG_DATA_WIDTH (REG_DATA_WIDTH),
            .REG_MASK_WIDTH (REG_MASK_WIDTH)
        ) u_reg_tracker (
            .clk                (clk),
            .rst_n              (rst_n),

            // TDI state
            .tdi_state          (tdi_state_bus[i]),

            // Register write events
            .reg_write_valid    (reg_write_valid_per_tdi[i]),
            .reg_write_addr     (reg_write_addr_per_tdi[i]),
            .reg_write_data     (reg_write_data_per_tdi[i]),
            .reg_write_mask     (reg_write_mask_per_tdi[i]),

            // Function identification
            .tdi_function_id    (TDI_INDEX_WIDTH'(i)),

            // Tracking enable: active when CONFIG_LOCKED or RUN
            .tracking_enable    (state_is_locked_w),

            // Capability base addresses
            .pcie_cap_base      (pcie_cap_base_per_tdi[i]),
            .msix_cap_base      (msix_cap_base_per_tdi[i]),
            .pm_cap_base        (pm_cap_base_per_tdi[i]),

            // MSI-X lock status
            .msix_table_locked  (1'b0),  // TODO: wire from lock_handler per-TDI state

            // Error output
            .error_trigger      (error_trigger_w),
            .error_reg_addr     (),
            .error_reg_name     (),
            .error_reg_description (),
            .error_tdi_idx      ()
        );

        // =========================================================================
        // Per-TDI Instance: tdisp_tlp_filter
        // =========================================================================
        tdisp_tlp_filter #(
            .TLP_DATA_WIDTH  (TLP_DATA_WIDTH),
            .ADDR_TYPE_WIDTH (ADDR_TYPE_WIDTH)
        ) u_tlp_filter (
            .clk                (clk),
            .rst_n              (rst_n),

            // TDI state and configuration
            .tdi_state              (tdi_state_bus[i]),
            .xt_mode_enabled        (xt_mode_enable_w),
            .xt_bit_for_locked_msix (xt_bit_for_locked_msix_w),

            // Egress path inputs
            .eg_tlp_valid           (eg_tlp_valid_per_tdi[i]),
            .eg_tlp_data            (eg_tlp_data_per_tdi[i]),
            .eg_tlp_last            (eg_tlp_last_per_tdi[i]),
            .eg_tlp_is_memory_req   (eg_tlp_is_memory_req_per_tdi[i]),
            .eg_tlp_is_completion   (eg_tlp_is_completion_per_tdi[i]),
            .eg_tlp_is_msi          (eg_tlp_is_msi_per_tdi[i]),
            .eg_tlp_is_msix         (eg_tlp_is_msix_per_tdi[i]),
            .eg_tlp_is_msix_locked  (eg_tlp_is_msix_locked_per_tdi[i]),
            .eg_tlp_is_ats_request  (eg_tlp_is_ats_request_per_tdi[i]),
            .eg_tlp_is_vdm          (eg_tlp_is_vdm_per_tdi[i]),
            .eg_tlp_is_io_req       (eg_tlp_is_io_req_per_tdi[i]),
            .eg_tlp_addr_type       (eg_tlp_addr_type_per_tdi[i]),
            .eg_access_tee_mem      (eg_access_tee_mem_per_tdi[i]),
            .eg_access_non_tee_mem  (eg_access_non_tee_mem_per_tdi[i]),

            // Egress path outputs
            .eg_tlp_out_valid       (eg_tlp_out_valid_per_tdi[i]),
            .eg_tlp_out_data        (eg_tlp_out_data_per_tdi[i]),
            .eg_tlp_out_last        (eg_tlp_out_last_per_tdi[i]),
            .eg_tlp_xt_bit          (eg_tlp_xt_bit_per_tdi[i]),
            .eg_tlp_t_bit           (eg_tlp_t_bit_per_tdi[i]),
            .eg_tlp_reject          (eg_tlp_reject_per_tdi[i]),

            // Ingress path inputs
            .ig_tlp_valid           (ig_tlp_valid_per_tdi[i]),
            .ig_tlp_data            (ig_tlp_data_per_tdi[i]),
            .ig_tlp_last            (ig_tlp_last_per_tdi[i]),
            .ig_tlp_xt_bit          (ig_tlp_xt_bit_in_per_tdi[i]),
            .ig_tlp_t_bit           (ig_tlp_t_bit_in_per_tdi[i]),
            .ig_tlp_is_memory_req   (ig_tlp_is_memory_req_per_tdi[i]),
            .ig_tlp_is_completion   (ig_tlp_is_completion_per_tdi[i]),
            .ig_tlp_is_vdm          (ig_tlp_is_vdm_per_tdi[i]),
            .ig_tlp_is_ats_request  (ig_tlp_is_ats_request_per_tdi[i]),
            .ig_tlp_target_is_non_tee_mem (ig_tlp_target_is_non_tee_mem_per_tdi[i]),
            .ig_tlp_on_bound_stream (ig_tlp_on_bound_stream_per_tdi[i]),
            .ig_ide_required        (ig_ide_required_per_tdi[i]),
            .ig_msix_table_locked   (ig_msix_table_locked_per_tdi[i]),

            // Ingress path outputs
            .ig_tlp_out_valid       (ig_tlp_out_valid_per_tdi[i]),
            .ig_tlp_out_data        (ig_tlp_out_data_per_tdi[i]),
            .ig_tlp_out_last        (ig_tlp_out_last_per_tdi[i]),
            .ig_tlp_reject          (ig_tlp_reject_per_tdi[i])
        );

        // -----------------------------------------------------------------
        // Error IRQ: pulse when TDI enters ERROR state
        // -----------------------------------------------------------------
        assign tdi_error_irq[i] = ev_entered_error_w;

        // -----------------------------------------------------------------
        // State output
        // -----------------------------------------------------------------
        assign tdi_state_out[i] = tdi_state_bus[i];

    end : gen_tdi

    // =========================================================================
    // Shared Instance: tdisp_lock_handler
    //   A single lock_handler serves all TDIs. It receives lock commands
    //   from req_handler (with TDI index) and performs phased validation.
    // =========================================================================
    tdisp_lock_handler #(
        .NUM_TDI     (NUM_TDI),
        .NUM_PF      (NUM_PF),
        .NUM_VF_MAX  (NUM_VF_MAX),
        .NUM_BARS    (NUM_BARS)
    ) u_lock_handler (
        .clk                (clk),
        .rst_n              (rst_n),

        // Lock command from req_handler
        .lock_cmd_valid     (lock_cmd_valid_w),
        .lock_cmd_tdi_idx   (lock_cmd_tdi_idx_w),
        .lock_cmd_payload   (lock_cmd_payload_w),

        // Lock result to req_handler
        .lock_done          (lock_done_w),
        .lock_error         (lock_error_w),
        .lock_error_code    (lock_error_code_w),
        .lock_nonce_out     (lock_nonce_out_w),
        .lock_done_tdi_idx  (lock_done_tdi_idx_w),

        // Per-TDI state bus
        .tdi_state          (tdi_state_bus),

        // Lock acknowledge pulse to FSMs
        .lock_ack_pulse     (lock_ack_pulse_w),

        // Stored nonce bus
        .tdi_stored_nonce   (tdi_stored_nonce_bus),

        // Register snapshot interface
        .lock_snapshot_req     (lock_snapshot_req_w),
        .lock_snapshot_tdi_idx (lock_snapshot_tdi_idx_w),
        .lock_snapshot_ack     (lock_snapshot_ack_w),

        // IDE configuration
        .ide_stream_valid       (ide_stream_valid),
        .ide_keys_programmed    (ide_keys_programmed),
        .ide_default_stream_id  (ide_default_stream_id),
        .ide_xt_enable_setting  (ide_xt_enable_setting),
        .ide_tc_value           (ide_tc_value),

        // SET_TDISP_CONFIG settings
        .xt_mode_enable         (xt_mode_enable_w),
        .xt_bit_for_locked_msix (xt_bit_for_locked_msix_w),

        // Device BAR configuration
        .pf_bar_config_valid    (pf_bar_config_valid),
        .pf_bar_addrs           (pf_bar_addrs),
        .pf_bar_sizes           (pf_bar_sizes),
        .vf_bar_config_valid    (vf_bar_config_valid),
        .vf_bar_addrs           (vf_bar_addrs),
        .vf_bar_sizes           (vf_bar_sizes),

        // Miscellaneous device configuration
        .phantom_funcs_enabled   (phantom_funcs_enabled),
        .expansion_rom_valid     (expansion_rom_valid),
        .expansion_rom_addr      (expansion_rom_addr),
        .expansion_rom_size      (expansion_rom_size),
        .resizable_bar_sizes_valid (resizable_bar_sizes_valid),
        .sr_iov_page_size        (sr_iov_page_size),
        .cache_line_size         (cache_line_size),
        .tph_mode                (tph_mode),

        // TRNG entropy
        .entropy_req             (entropy_req_w),
        .entropy_valid           (entropy_valid_w),
        .entropy_data            (entropy_data_w)
    );

    // =========================================================================
    // Assertions
    // =========================================================================

    // Validate NUM_TDI is within spec limit
    initial begin
        assert (NUM_TDI >= 1 && NUM_TDI <= MAX_NUM_TDI)
        else $error("NUM_TDI=%0d out of range [1, %0d]", NUM_TDI, MAX_NUM_TDI);
    end

    // parsed_error from codec should never be ignored silently
    // (In a full design, an error response would be generated by req_handler)
    // This assertion catches unexpected parse errors as a safety net.
    // TODO: Wire parsed_error into req_handler for error response generation.

endmodule
