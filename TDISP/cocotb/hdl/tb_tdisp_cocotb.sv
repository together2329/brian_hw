// ============================================================================
// Module:    tb_tdisp_cocotb.sv
// Purpose:   Thin cocotb wrapper for tdisp_top
//            - Flattens packed struct ports to bit vectors for iverilog compat
//            - Provides $dumpfile/$dumpvars for waveform capture
//            - Uses NUM_TDI=2 to match the testbench configuration
// ============================================================================

module tb_tdisp_cocotb
    import tdisp_pkg::*;
#(
    parameter int TB_NUM_TDI        = 2,
    parameter int TB_NUM_PF         = 1,
    parameter int TB_NUM_BARS       = 6,
    parameter int TB_NUM_P2P        = MAX_P2P_STREAMS,
    parameter int TB_DATA_WIDTH     = 8,
    parameter int TB_TLP_DATA_WIDTH = 128,
    parameter int TB_ADDR_TYPE_WIDTH= 2,
    parameter int TB_ADDR_WIDTH     = 64,
    parameter int TB_REG_ADDR_WIDTH = 12,
    parameter int TB_REG_DATA_WIDTH = 32,
    parameter int TB_REG_MASK_WIDTH = TB_REG_DATA_WIDTH / 8,
    parameter int TB_REPORT_BUF     = 4096
)(
    input  logic clk,
    input  logic rst_n
);

    // =========================================================================
    // Waveform dump (controlled by VCD_DUMP compile-time define)
    // =========================================================================
    initial begin
        `ifdef VCD_DUMP
            $dumpfile("tdisp_cocotb.vcd");
            $dumpvars(0, tb_tdisp_cocotb);
        `endif
    end

    // =========================================================================
    // Unpacked signal declarations u2014 matching tdisp_top port list
    // Struct ports are flattened to bit vectors for iverilog compatibility
    // =========================================================================

    // SPDM/DOE Transport
    logic                      rx_valid;
    logic [TB_DATA_WIDTH-1:0]  rx_data;
    logic                      rx_last;
    logic                      rx_ready;

    logic                      tx_valid;
    logic [TB_DATA_WIDTH-1:0]  tx_data;
    logic                      tx_last;
    logic                      tx_ready;

    // Version
    logic [7:0]                negotiated_version;
    logic                      version_valid;

    // Device caps (flattened from tdisp_caps_s)
    // tdisp_caps_s: 1+30+128+16+24+8+8+8 = 223 bits
    localparam int CAPS_WIDTH = 223;
    logic [CAPS_WIDTH-1:0]     device_caps_flat;
    tdisp_caps_s               device_caps;

    assign device_caps = tdisp_caps_s'(device_caps_flat);

    // Report data
    logic [7:0]                report_data [TB_REPORT_BUF-1:0];
    logic [15:0]               report_total_len;

    // Interface IDs
    logic [INTERFACE_ID_WIDTH-1:0] hosted_interface_ids [TB_NUM_TDI-1:0];

    // Request counts
    logic [7:0]                num_req_this_config [TB_NUM_TDI-1:0];
    logic [7:0]                num_req_all_config;

    // IDE stream
    logic                      ide_stream_valid;
    logic                      ide_keys_programmed;
    logic [7:0]                ide_default_stream_id;
    logic                      ide_xt_enable_setting;
    logic [2:0]                ide_tc_value;

    // P2P stream binding
    logic [MAX_P2P_STREAMS-1:0] p2p_stream_bound [TB_NUM_TDI-1:0];

    // BAR config
    logic                      pf_bar_config_valid [TB_NUM_PF-1:0][TB_NUM_BARS-1:0];
    logic [63:0]               pf_bar_addrs [TB_NUM_PF-1:0][TB_NUM_BARS-1:0];
    logic [63:0]               pf_bar_sizes [TB_NUM_PF-1:0][TB_NUM_BARS-1:0];
    logic                      vf_bar_config_valid [TB_NUM_PF-1:0][TB_NUM_BARS-1:0];
    logic [63:0]               vf_bar_addrs [TB_NUM_PF-1:0][TB_NUM_BARS-1:0];
    logic [63:0]               vf_bar_sizes [TB_NUM_PF-1:0][TB_NUM_BARS-1:0];
    logic                      phantom_funcs_enabled;
    logic                      expansion_rom_valid;
    logic [63:0]               expansion_rom_addr;
    logic [63:0]               expansion_rom_size;
    logic                      resizable_bar_sizes_valid;
    logic [2:0]                sr_iov_page_size;
    logic [7:0]                cache_line_size;
    logic [1:0]                tph_mode;

    // TRNG
    logic                      trng_valid;
    logic [NONCE_WIDTH-1:0]    trng_data;

    // Per-TDI register writes
    logic [TB_NUM_TDI-1:0]                  reg_write_valid_per_tdi;
    logic [TB_REG_ADDR_WIDTH-1:0]            reg_write_addr_per_tdi  [TB_NUM_TDI-1:0];
    logic [TB_REG_DATA_WIDTH-1:0]            reg_write_data_per_tdi  [TB_NUM_TDI-1:0];
    logic [TB_REG_MASK_WIDTH-1:0]            reg_write_mask_per_tdi  [TB_NUM_TDI-1:0];

    // Capability bases
    logic [TB_REG_ADDR_WIDTH-1:0]            pcie_cap_base_per_tdi   [TB_NUM_TDI-1:0];
    logic [TB_REG_ADDR_WIDTH-1:0]            msix_cap_base_per_tdi   [TB_NUM_TDI-1:0];
    logic [TB_REG_ADDR_WIDTH-1:0]            pm_cap_base_per_tdi     [TB_NUM_TDI-1:0];

    // Egress TLP inputs (per TDI)
    logic [TB_NUM_TDI-1:0]                  eg_tlp_valid_per_tdi;
    logic [TB_TLP_DATA_WIDTH-1:0]            eg_tlp_data_per_tdi     [TB_NUM_TDI-1:0];
    logic [TB_NUM_TDI-1:0]                  eg_tlp_last_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_is_memory_req_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_is_completion_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_is_msi_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_is_msix_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_is_msix_locked_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_is_ats_request_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_is_vdm_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_is_io_req_per_tdi;
    logic [TB_ADDR_TYPE_WIDTH-1:0]           eg_tlp_addr_type_per_tdi [TB_NUM_TDI-1:0];
    logic [TB_NUM_TDI-1:0]                  eg_access_tee_mem_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_access_non_tee_mem_per_tdi;

    // Egress TLP outputs (per TDI)
    logic [TB_NUM_TDI-1:0]                  eg_tlp_out_valid_per_tdi;
    logic [TB_TLP_DATA_WIDTH-1:0]            eg_tlp_out_data_per_tdi [TB_NUM_TDI-1:0];
    logic [TB_NUM_TDI-1:0]                  eg_tlp_out_last_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_xt_bit_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_t_bit_per_tdi;
    logic [TB_NUM_TDI-1:0]                  eg_tlp_reject_per_tdi;

    // Ingress TLP inputs (per TDI)
    logic [TB_NUM_TDI-1:0]                  ig_tlp_valid_per_tdi;
    logic [TB_TLP_DATA_WIDTH-1:0]            ig_tlp_data_per_tdi     [TB_NUM_TDI-1:0];
    logic [TB_NUM_TDI-1:0]                  ig_tlp_last_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_xt_bit_in_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_t_bit_in_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_is_memory_req_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_is_completion_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_is_vdm_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_is_ats_request_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_target_is_non_tee_mem_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_on_bound_stream_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_ide_required_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_msix_table_locked_per_tdi;

    // Ingress TLP outputs (per TDI)
    logic [TB_NUM_TDI-1:0]                  ig_tlp_out_valid_per_tdi;
    logic [TB_TLP_DATA_WIDTH-1:0]            ig_tlp_out_data_per_tdi [TB_NUM_TDI-1:0];
    logic [TB_NUM_TDI-1:0]                  ig_tlp_out_last_per_tdi;
    logic [TB_NUM_TDI-1:0]                  ig_tlp_reject_per_tdi;

    // VDM
    logic                                 vdm_req_valid;
    logic [INTERFACE_ID_WIDTH-1:0]        vdm_req_interface_id;
    logic [7:0]                           vdm_req_payload [TB_REPORT_BUF-1:0];
    logic [15:0]                          vdm_req_payload_len;
    logic                                 vdm_resp_ready;

    // P2P bind/unbind
    logic [7:0]                           bind_stream_id;
    logic [TB_NUM_TDI-1:0]               bind_pulse;
    logic [TB_NUM_TDI-1:0]               unbind_pulse;

    // MMIO attribute update (flattened from tdisp_set_mmio_attr_req_s)
    // tdisp_set_mmio_attr_req_s: 64+32+1+30 = 127 bits
    localparam int MMIO_ATTR_WIDTH = 127;
    logic                                 mmio_attr_update_valid;
    logic [TDI_INDEX_WIDTH-1:0]           mmio_attr_tdi_idx;
    logic [MMIO_ATTR_WIDTH-1:0]           mmio_attr_update_data_flat;
    tdisp_set_mmio_attr_req_s             mmio_attr_update_data;

    assign mmio_attr_update_data = tdisp_set_mmio_attr_req_s'(mmio_attr_update_data_flat);

    // External reset
    logic                                 reset_to_unlocked;

    // Status
    logic [TB_NUM_TDI-1:0]               tdi_error_irq;
    tdisp_tdi_state_e                     tdi_state_out [TB_NUM_TDI-1:0];

    // =========================================================================
    // DUT Instantiation u2014 tdisp_top with NUM_TDI=2
    // =========================================================================
    tdisp_top #(
        .NUM_TDI        (TB_NUM_TDI),
        .NUM_PF         (TB_NUM_PF),
        .NUM_BARS       (TB_NUM_BARS),
        .NUM_P2P_STREAMS(TB_NUM_P2P),
        .DATA_WIDTH     (TB_DATA_WIDTH),
        .TLP_DATA_WIDTH (TB_TLP_DATA_WIDTH),
        .ADDR_TYPE_WIDTH(TB_ADDR_TYPE_WIDTH),
        .ADDR_WIDTH     (TB_ADDR_WIDTH),
        .REG_ADDR_WIDTH (TB_REG_ADDR_WIDTH),
        .REG_DATA_WIDTH (TB_REG_DATA_WIDTH),
        .REPORT_BUF_SIZE(TB_REPORT_BUF)
    ) u_dut (
        .clk                          (clk),
        .rst_n                        (rst_n),

        .rx_valid                     (rx_valid),
        .rx_data                      (rx_data),
        .rx_last                      (rx_last),
        .rx_ready                     (rx_ready),

        .tx_valid                     (tx_valid),
        .tx_data                      (tx_data),
        .tx_last                      (tx_last),
        .tx_ready                     (tx_ready),

        .negotiated_version           (negotiated_version),
        .version_valid                (version_valid),

        .device_caps                  (device_caps),
        .report_data                  (report_data),
        .report_total_len             (report_total_len),

        .hosted_interface_ids         (hosted_interface_ids),

        .num_req_this_config          (num_req_this_config),
        .num_req_all_config           (num_req_all_config),

        .ide_stream_valid             (ide_stream_valid),
        .ide_keys_programmed          (ide_keys_programmed),
        .ide_default_stream_id        (ide_default_stream_id),
        .ide_xt_enable_setting        (ide_xt_enable_setting),
        .ide_tc_value                 (ide_tc_value),

        .p2p_stream_bound             (p2p_stream_bound),

        .pf_bar_config_valid          (pf_bar_config_valid),
        .pf_bar_addrs                 (pf_bar_addrs),
        .pf_bar_sizes                 (pf_bar_sizes),
        .vf_bar_config_valid          (vf_bar_config_valid),
        .vf_bar_addrs                 (vf_bar_addrs),
        .vf_bar_sizes                 (vf_bar_sizes),
        .phantom_funcs_enabled        (phantom_funcs_enabled),
        .expansion_rom_valid          (expansion_rom_valid),
        .expansion_rom_addr           (expansion_rom_addr),
        .expansion_rom_size           (expansion_rom_size),
        .resizable_bar_sizes_valid    (resizable_bar_sizes_valid),
        .sr_iov_page_size             (sr_iov_page_size),
        .cache_line_size              (cache_line_size),
        .tph_mode                     (tph_mode),

        .trng_valid                   (trng_valid),
        .trng_data                    (trng_data),

        .reg_write_valid_per_tdi      (reg_write_valid_per_tdi),
        .reg_write_addr_per_tdi       (reg_write_addr_per_tdi),
        .reg_write_data_per_tdi       (reg_write_data_per_tdi),
        .reg_write_mask_per_tdi       (reg_write_mask_per_tdi),

        .pcie_cap_base_per_tdi        (pcie_cap_base_per_tdi),
        .msix_cap_base_per_tdi        (msix_cap_base_per_tdi),
        .pm_cap_base_per_tdi          (pm_cap_base_per_tdi),

        .eg_tlp_valid_per_tdi         (eg_tlp_valid_per_tdi),
        .eg_tlp_data_per_tdi          (eg_tlp_data_per_tdi),
        .eg_tlp_last_per_tdi          (eg_tlp_last_per_tdi),
        .eg_tlp_is_memory_req_per_tdi (eg_tlp_is_memory_req_per_tdi),
        .eg_tlp_is_completion_per_tdi (eg_tlp_is_completion_per_tdi),
        .eg_tlp_is_msi_per_tdi        (eg_tlp_is_msi_per_tdi),
        .eg_tlp_is_msix_per_tdi       (eg_tlp_is_msix_per_tdi),
        .eg_tlp_is_msix_locked_per_tdi(eg_tlp_is_msix_locked_per_tdi),
        .eg_tlp_is_ats_request_per_tdi(eg_tlp_is_ats_request_per_tdi),
        .eg_tlp_is_vdm_per_tdi        (eg_tlp_is_vdm_per_tdi),
        .eg_tlp_is_io_req_per_tdi     (eg_tlp_is_io_req_per_tdi),
        .eg_tlp_addr_type_per_tdi     (eg_tlp_addr_type_per_tdi),
        .eg_access_tee_mem_per_tdi    (eg_access_tee_mem_per_tdi),
        .eg_access_non_tee_mem_per_tdi(eg_access_non_tee_mem_per_tdi),

        .eg_tlp_out_valid_per_tdi     (eg_tlp_out_valid_per_tdi),
        .eg_tlp_out_data_per_tdi      (eg_tlp_out_data_per_tdi),
        .eg_tlp_out_last_per_tdi      (eg_tlp_out_last_per_tdi),
        .eg_tlp_xt_bit_per_tdi        (eg_tlp_xt_bit_per_tdi),
        .eg_tlp_t_bit_per_tdi         (eg_tlp_t_bit_per_tdi),
        .eg_tlp_reject_per_tdi        (eg_tlp_reject_per_tdi),

        .ig_tlp_valid_per_tdi         (ig_tlp_valid_per_tdi),
        .ig_tlp_data_per_tdi          (ig_tlp_data_per_tdi),
        .ig_tlp_last_per_tdi          (ig_tlp_last_per_tdi),
        .ig_tlp_xt_bit_in_per_tdi     (ig_tlp_xt_bit_in_per_tdi),
        .ig_tlp_t_bit_in_per_tdi      (ig_tlp_t_bit_in_per_tdi),
        .ig_tlp_is_memory_req_per_tdi (ig_tlp_is_memory_req_per_tdi),
        .ig_tlp_is_completion_per_tdi (ig_tlp_is_completion_per_tdi),
        .ig_tlp_is_vdm_per_tdi        (ig_tlp_is_vdm_per_tdi),
        .ig_tlp_is_ats_request_per_tdi(ig_tlp_is_ats_request_per_tdi),
        .ig_tlp_target_is_non_tee_mem_per_tdi(ig_tlp_target_is_non_tee_mem_per_tdi),
        .ig_tlp_on_bound_stream_per_tdi(ig_tlp_on_bound_stream_per_tdi),
        .ig_ide_required_per_tdi      (ig_ide_required_per_tdi),
        .ig_msix_table_locked_per_tdi (ig_msix_table_locked_per_tdi),

        .ig_tlp_out_valid_per_tdi     (ig_tlp_out_valid_per_tdi),
        .ig_tlp_out_data_per_tdi      (ig_tlp_out_data_per_tdi),
        .ig_tlp_out_last_per_tdi      (ig_tlp_out_last_per_tdi),
        .ig_tlp_reject_per_tdi        (ig_tlp_reject_per_tdi),

        .vdm_req_valid                (vdm_req_valid),
        .vdm_req_interface_id         (vdm_req_interface_id),
        .vdm_req_payload              (vdm_req_payload),
        .vdm_req_payload_len          (vdm_req_payload_len),
        .vdm_resp_ready               (vdm_resp_ready),

        .bind_stream_id               (bind_stream_id),
        .bind_pulse                   (bind_pulse),
        .unbind_pulse                 (unbind_pulse),

        .mmio_attr_update_valid       (mmio_attr_update_valid),
        .mmio_attr_tdi_idx            (mmio_attr_tdi_idx),
        .mmio_attr_update_data        (mmio_attr_update_data),

        .reset_to_unlocked            (reset_to_unlocked),

        .tdi_error_irq                (tdi_error_irq),
        .tdi_state_out                (tdi_state_out)
    );

endmodule
