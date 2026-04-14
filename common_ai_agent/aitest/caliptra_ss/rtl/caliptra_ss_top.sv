//********************************************************************************
// SPDX-License-Identifier: Apache-2.0
//
// Caliptra Subsystem — Top-Level Integration Module
// MAS Reference: caliptra_ss/mas/caliptra_ss_mas.md §2 (all subsections)
//
// This is the single integration point for the entire Caliptra Subsystem.
// All ports, parameters, and internal wiring are derived from the MAS SSoT.
//
//********************************************************************************

`include "caliptra_ss_includes.svh"

module caliptra_ss_top
    import caliptra_ss_top_pkg::*;
#(
    // MAS §2.3 — Parameters
    parameter MCU_MBOX0_SIZE_KB = 4,
    parameter [4:0] SET_MCU_MBOX0_AXI_USER_INTEG   = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0},
    parameter [4:0][31:0] MCU_MBOX0_VALID_AXI_USER = {32'h4444_4444, 32'h3333_3333, 32'h2222_2222, 32'h1111_1111, 32'h0000_0000},
    parameter MCU_MBOX1_SIZE_KB = 4,
    parameter [4:0] SET_MCU_MBOX1_AXI_USER_INTEG   = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0},
    parameter [4:0][31:0] MCU_MBOX1_VALID_AXI_USER = {32'h4444_4444, 32'h3333_3333, 32'h2222_2222, 32'h1111_1111, 32'h0000_0000},
    parameter MCU_SRAM_SIZE_KB          = 512,
    parameter MIN_MCU_RST_COUNTER_WIDTH = 4
)(
    // =================================================================
    // MAS §2.2.1 — Clock, Reset, Power
    // =================================================================
    input  logic cptra_ss_clk_i,              // System clock (333–400 MHz)
    output logic cptra_ss_rdc_clk_cg_o,       // Gated clock for RDC crossing
    output logic cptra_ss_mcu_clk_cg_o,       // MCU gated clock for RDC
    input  logic cptra_ss_pwrgood_i,          // Power good (active-high)
    input  logic cptra_ss_rst_b_i,            // Primary reset (active-low, sync, min 2 cycles)
    output logic cptra_ss_rst_b_o,            // Delayed reset for RDC crossing

    // MAS §2.2.2 — Caliptra Core Reset Control
    input  logic cptra_ss_mci_cptra_rst_b_i,  // Caliptra reset in (loopback from MCI)
    output logic cptra_ss_mci_cptra_rst_b_o,  // Caliptra reset out from MCI

    // MAS §2.2.3 — MCU Reset Control
    output logic cptra_ss_mcu_rst_b_o,        // MCU reset out from MCI
    input  logic cptra_ss_mcu_rst_b_i,        // MCU reset in (loopback from MCI)

    // MAS §2.2.1 — RDC Control Signals
    output logic cptra_ss_warm_reset_rdc_clk_dis_o,     // Clock disable for warm reset RDC
    output logic cptra_ss_early_warm_reset_warn_o,       // Early reset warn for security signals
    output logic cptra_ss_mcu_fw_update_rdc_clk_dis_o,   // Clock disable for MCU FW update RDC

    // =================================================================
    // MAS §2.2.7 — Caliptra Core AXI Manager Interface (DMA)
    // =================================================================
    output logic [AXI_ADDR_W-1:0] cptra_ss_cptra_core_m_axi_awaddr,
    output logic [AXI_ID_W-1:0]   cptra_ss_cptra_core_m_axi_awid,
    output logic [7:0]            cptra_ss_cptra_core_m_axi_awlen,
    output logic [2:0]            cptra_ss_cptra_core_m_axi_awsize,
    output logic [1:0]            cptra_ss_cptra_core_m_axi_awburst,
    output logic                  cptra_ss_cptra_core_m_axi_awlock,
    output logic [3:0]            cptra_ss_cptra_core_m_axi_awcache,
    output logic [2:0]            cptra_ss_cptra_core_m_axi_awprot,
    output logic [3:0]            cptra_ss_cptra_core_m_axi_awregion,
    output logic [3:0]            cptra_ss_cptra_core_m_axi_awqos,
    output logic [AXI_USER_W-1:0] cptra_ss_cptra_core_m_axi_awuser,
    output logic                  cptra_ss_cptra_core_m_axi_awvalid,
    input  logic                  cptra_ss_cptra_core_m_axi_awready,

    output logic [AXI_DATA_W-1:0] cptra_ss_cptra_core_m_axi_wdata,
    output logic [(AXI_DATA_W/8)-1:0] cptra_ss_cptra_core_m_axi_wstrb,
    output logic                  cptra_ss_cptra_core_m_axi_wlast,
    output logic                  cptra_ss_cptra_core_m_axi_wvalid,
    input  logic                  cptra_ss_cptra_core_m_axi_wready,

    input  logic [AXI_ID_W-1:0]   cptra_ss_cptra_core_m_axi_bid,
    input  logic [1:0]            cptra_ss_cptra_core_m_axi_bresp,
    input  logic                  cptra_ss_cptra_core_m_axi_bvalid,
    output logic                  cptra_ss_cptra_core_m_axi_bready,

    output logic [AXI_ADDR_W-1:0] cptra_ss_cptra_core_m_axi_araddr,
    output logic [AXI_ID_W-1:0]   cptra_ss_cptra_core_m_axi_arid,
    output logic [7:0]            cptra_ss_cptra_core_m_axi_arlen,
    output logic [2:0]            cptra_ss_cptra_core_m_axi_arsize,
    output logic [1:0]            cptra_ss_cptra_core_m_axi_arburst,
    output logic                  cptra_ss_cptra_core_m_axi_arlock,
    output logic [3:0]            cptra_ss_cptra_core_m_axi_arcache,
    output logic [2:0]            cptra_ss_cptra_core_m_axi_arprot,
    output logic [3:0]            cptra_ss_cptra_core_m_axi_arregion,
    output logic [3:0]            cptra_ss_cptra_core_m_axi_arqos,
    output logic [AXI_USER_W-1:0] cptra_ss_cptra_core_m_axi_aruser,
    output logic                  cptra_ss_cptra_core_m_axi_arvalid,
    input  logic                  cptra_ss_cptra_core_m_axi_arready,

    input  logic [AXI_ID_W-1:0]   cptra_ss_cptra_core_m_axi_rid,
    input  logic [AXI_DATA_W-1:0] cptra_ss_cptra_core_m_axi_rdata,
    input  logic [1:0]            cptra_ss_cptra_core_m_axi_rresp,
    input  logic                  cptra_ss_cptra_core_m_axi_rlast,
    input  logic                  cptra_ss_cptra_core_m_axi_rvalid,
    output logic                  cptra_ss_cptra_core_m_axi_rready,

    // =================================================================
    // MAS §2.2.8 — MCI AXI Subordinate Interface
    // =================================================================
    input  logic [AXI_ADDR_W-1:0] cptra_ss_mci_s_axi_awaddr,
    input  logic [AXI_ID_W-1:0]   cptra_ss_mci_s_axi_awid,
    input  logic [7:0]            cptra_ss_mci_s_axi_awlen,
    input  logic [2:0]            cptra_ss_mci_s_axi_awsize,
    input  logic [1:0]            cptra_ss_mci_s_axi_awburst,
    input  logic                  cptra_ss_mci_s_axi_awlock,
    input  logic [AXI_USER_W-1:0] cptra_ss_mci_s_axi_awuser,
    input  logic                  cptra_ss_mci_s_axi_awvalid,
    output logic                  cptra_ss_mci_s_axi_awready,

    input  logic [AXI_DATA_W-1:0] cptra_ss_mci_s_axi_wdata,
    input  logic [(AXI_DATA_W/8)-1:0] cptra_ss_mci_s_axi_wstrb,
    input  logic                  cptra_ss_mci_s_axi_wlast,
    input  logic                  cptra_ss_mci_s_axi_wvalid,
    output logic                  cptra_ss_mci_s_axi_wready,

    output logic [AXI_ID_W-1:0]   cptra_ss_mci_s_axi_bid,
    output logic [1:0]            cptra_ss_mci_s_axi_bresp,
    output logic                  cptra_ss_mci_s_axi_bvalid,
    input  logic                  cptra_ss_mci_s_axi_bready,

    input  logic [AXI_ADDR_W-1:0] cptra_ss_mci_s_axi_araddr,
    input  logic [AXI_ID_W-1:0]   cptra_ss_mci_s_axi_arid,
    input  logic [7:0]            cptra_ss_mci_s_axi_arlen,
    input  logic [2:0]            cptra_ss_mci_s_axi_arsize,
    input  logic [1:0]            cptra_ss_mci_s_axi_arburst,
    input  logic                  cptra_ss_mci_s_axi_arlock,
    input  logic [AXI_USER_W-1:0] cptra_ss_mci_s_axi_aruser,
    input  logic                  cptra_ss_mci_s_axi_arvalid,
    output logic                  cptra_ss_mci_s_axi_arready,

    output logic [AXI_ID_W-1:0]   cptra_ss_mci_s_axi_rid,
    output logic [AXI_DATA_W-1:0] cptra_ss_mci_s_axi_rdata,
    output logic [1:0]            cptra_ss_mci_s_axi_rresp,
    output logic                  cptra_ss_mci_s_axi_rlast,
    output logic                  cptra_ss_mci_s_axi_rvalid,
    input  logic                  cptra_ss_mci_s_axi_rready,

    // =================================================================
    // MAS §2.2.12 — Caliptra Core Interface Signals
    // =================================================================
    input  logic [255:0] cptra_ss_cptra_obf_key_i,
    input  logic [127:0] cptra_ss_raw_unlock_token_hashed_i,
    output logic [124:0] cptra_ss_cptra_generic_fw_exec_ctrl_o,
    output logic         cptra_ss_cptra_generic_fw_exec_ctrl_2_mcu_o,
    input  logic         cptra_ss_cptra_generic_fw_exec_ctrl_2_mcu_i,
    input  logic         cptra_ss_cptra_core_bootfsm_bp_i,
    input  logic         cptra_ss_cptra_core_scan_mode_i,
    input  logic [63:0]  cptra_ss_cptra_core_generic_input_wires_i,
    output logic [63:0]  cptra_ss_cptra_core_generic_output_wires_o,

    // MAS §2.2.10 — JTAG Interfaces
    input  logic cptra_ss_cptra_core_jtag_tck_i,
    input  logic cptra_ss_cptra_core_jtag_tms_i,
    input  logic cptra_ss_cptra_core_jtag_tdi_i,
    input  logic cptra_ss_cptra_core_jtag_trst_n_i,
    output logic cptra_ss_cptra_core_jtag_tdo_o,
    output logic cptra_ss_cptra_core_jtag_tdoEn_o,

    input  logic cptra_ss_mcu_jtag_tck_i,
    input  logic cptra_ss_mcu_jtag_tms_i,
    input  logic cptra_ss_mcu_jtag_tdi_i,
    input  logic cptra_ss_mcu_jtag_trst_n_i,
    output logic cptra_ss_mcu_jtag_tdo_o,
    output logic cptra_ss_mcu_jtag_tdoEn_o,

    // =================================================================
    // MAS §2.2.11 — I3C Interface
    // =================================================================
    input  logic cptra_ss_i3c_scl_i,
    input  logic cptra_ss_i3c_sda_i,
    output logic cptra_ss_i3c_scl_o,
    output logic cptra_ss_i3c_sda_o,
    output logic cptra_ss_i3c_scl_oe,
    output logic cptra_ss_i3c_sda_oe,
    output logic cptra_ss_sel_od_pp_o,
    input  logic cptra_i3c_axi_user_id_filtering_enable_i,

    output logic cptra_ss_i3c_recovery_payload_available_o,
    input  logic cptra_ss_i3c_recovery_payload_available_i,
    output logic cptra_ss_i3c_recovery_image_activated_o,
    input  logic cptra_ss_i3c_recovery_image_activated_i,

    // =================================================================
    // MAS §2.2.14 — Lifecycle & Debug Signals
    // =================================================================
    input  logic         cptra_ss_debug_intent_i,
    input  logic         cptra_ss_mcu_no_rom_config_i,
    input  logic         cptra_ss_mci_boot_seq_brkpoint_i,
    input  logic         cptra_ss_lc_Allow_RMA_or_SCRAP_on_PPD_i,
    input  logic         cptra_ss_FIPS_ZEROIZATION_PPD_i,
    input  logic         cptra_ss_lc_sec_volatile_raw_unlock_en_i,

    output logic         cptra_ss_dbg_manuf_enable_o,
    output logic [63:0]  cptra_ss_cptra_core_soc_prod_dbg_unlock_level_o,
    output logic         caliptra_ss_otp_state_valid_o,
    output logic         caliptra_ss_volatile_raw_unlock_success_o,

    // =================================================================
    // MAS §2.2.15 — Error, Interrupt, Misc Signals
    // =================================================================
    output logic cptra_ss_all_error_fatal_o,
    output logic cptra_ss_all_error_non_fatal_o,
    output logic cptra_error_fatal,
    output logic cptra_error_non_fatal,

    output logic cptra_ss_mcu_halt_status_o,
    input  logic cptra_ss_mcu_halt_status_i,
    output logic cptra_ss_mcu_halt_ack_o,
    input  logic cptra_ss_mcu_halt_ack_i,
    output logic cptra_ss_mcu_halt_req_o,

    output logic cptra_ss_soc_mcu_mbox0_data_avail,
    output logic cptra_ss_soc_mcu_mbox1_data_avail,

    input  logic [63:0] cptra_ss_mci_generic_input_wires_i,
    output logic [63:0] cptra_ss_mci_generic_output_wires_o,

    input  logic [PIC_TOTAL_INT:`VEER_INTR_EXT_LSB] cptra_ss_mcu_ext_int,

    // =================================================================
    // MAS §2.2.4–2.2.6 — MCU AXI Manager Interfaces (LSU, IFU, SB)
    // =================================================================
    // MCU LSU AXI Write Manager
    output logic [AXI_ADDR_W-1:0] mcu_lsu_awaddr,
    output logic [MCU_LSU_BUS_TAG-1:0] mcu_lsu_awid,
    output logic [7:0]            mcu_lsu_awlen,
    output logic [2:0]            mcu_lsu_awsize,
    output logic [1:0]            mcu_lsu_awburst,
    output logic                  mcu_lsu_awvalid,
    input  logic                  mcu_lsu_awready,
    output logic [AXI_DATA_W-1:0] mcu_lsu_wdata,
    output logic [(AXI_DATA_W/8)-1:0] mcu_lsu_wstrb,
    output logic                  mcu_lsu_wlast,
    output logic                  mcu_lsu_wvalid,
    input  logic                  mcu_lsu_wready,
    input  logic  [MCU_LSU_BUS_TAG-1:0] mcu_lsu_bid,
    input  logic  [1:0]           mcu_lsu_bresp,
    input  logic                  mcu_lsu_bvalid,
    output logic                  mcu_lsu_bready,
    output logic [AXI_ADDR_W-1:0] mcu_lsu_araddr,
    output logic [MCU_LSU_BUS_TAG-1:0] mcu_lsu_arid,
    output logic [7:0]            mcu_lsu_arlen,
    output logic [2:0]            mcu_lsu_arsize,
    output logic [1:0]            mcu_lsu_arburst,
    output logic                  mcu_lsu_arvalid,
    input  logic                  mcu_lsu_arready,
    input  logic  [MCU_LSU_BUS_TAG-1:0] mcu_lsu_rid,
    input  logic  [AXI_DATA_W-1:0] mcu_lsu_rdata,
    input  logic  [1:0]           mcu_lsu_rresp,
    input  logic                  mcu_lsu_rlast,
    input  logic                  mcu_lsu_rvalid,
    output logic                  mcu_lsu_rready,
    output logic [3:0]            mcu_lsu_awcache,
    output logic [3:0]            mcu_lsu_arcache,
    output logic [2:0]            mcu_lsu_awprot,
    output logic [2:0]            mcu_lsu_arprot,
    output logic [3:0]            mcu_lsu_awregion,
    output logic [3:0]            mcu_lsu_arregion,
    output logic [3:0]            mcu_lsu_awqos,
    output logic [3:0]            mcu_lsu_arqos,

    // MCU IFU AXI Write Manager
    output logic [AXI_ADDR_W-1:0] mcu_ifu_awaddr,
    output logic [MCU_IFU_BUS_TAG-1:0] mcu_ifu_awid,
    output logic [7:0]            mcu_ifu_awlen,
    output logic [2:0]            mcu_ifu_awsize,
    output logic [1:0]            mcu_ifu_awburst,
    output logic                  mcu_ifu_awvalid,
    input  logic                  mcu_ifu_awready,
    output logic [AXI_DATA_W-1:0] mcu_ifu_wdata,
    output logic [(AXI_DATA_W/8)-1:0] mcu_ifu_wstrb,
    output logic                  mcu_ifu_wlast,
    output logic                  mcu_ifu_wvalid,
    input  logic                  mcu_ifu_wready,
    input  logic  [MCU_IFU_BUS_TAG-1:0] mcu_ifu_bid,
    input  logic  [1:0]           mcu_ifu_bresp,
    input  logic                  mcu_ifu_bvalid,
    output logic                  mcu_ifu_bready,
    output logic [AXI_ADDR_W-1:0] mcu_ifu_araddr,
    output logic [MCU_IFU_BUS_TAG-1:0] mcu_ifu_arid,
    output logic [7:0]            mcu_ifu_arlen,
    output logic [2:0]            mcu_ifu_arsize,
    output logic [1:0]            mcu_ifu_arburst,
    output logic                  mcu_ifu_arvalid,
    input  logic                  mcu_ifu_arready,
    input  logic  [MCU_IFU_BUS_TAG-1:0] mcu_ifu_rid,
    input  logic  [AXI_DATA_W-1:0] mcu_ifu_rdata,
    input  logic  [1:0]           mcu_ifu_rresp,
    input  logic                  mcu_ifu_rlast,
    input  logic                  mcu_ifu_rvalid,
    output logic                  mcu_ifu_rready,
    output logic [3:0]            mcu_ifu_awcache,
    output logic [3:0]            mcu_ifu_arcache,
    output logic [2:0]            mcu_ifu_awprot,
    output logic [2:0]            mcu_ifu_arprot,
    output logic [3:0]            mcu_ifu_awregion,
    output logic [3:0]            mcu_ifu_arregion,
    output logic [3:0]            mcu_ifu_awqos,
    output logic [3:0]            mcu_ifu_arqos,

    // MCU System Bus AXI Write Manager (debug only)
    output logic [AXI_ADDR_W-1:0] mcu_sb_awaddr,
    output logic [MCU_SB_BUS_TAG-1:0] mcu_sb_awid,
    output logic [7:0]            mcu_sb_awlen,
    output logic [2:0]            mcu_sb_awsize,
    output logic [1:0]            mcu_sb_awburst,
    output logic                  mcu_sb_awvalid,
    input  logic                  mcu_sb_awready,
    output logic [AXI_DATA_W-1:0] mcu_sb_wdata,
    output logic [(AXI_DATA_W/8)-1:0] mcu_sb_wstrb,
    output logic                  mcu_sb_wlast,
    output logic                  mcu_sb_wvalid,
    input  logic                  mcu_sb_wready,
    input  logic  [MCU_SB_BUS_TAG-1:0] mcu_sb_bid,
    input  logic  [1:0]           mcu_sb_bresp,
    input  logic                  mcu_sb_bvalid,
    output logic                  mcu_sb_bready,
    output logic [AXI_ADDR_W-1:0] mcu_sb_araddr,
    output logic [MCU_SB_BUS_TAG-1:0] mcu_sb_arid,
    output logic [7:0]            mcu_sb_arlen,
    output logic [2:0]            mcu_sb_arsize,
    output logic [1:0]            mcu_sb_arburst,
    output logic                  mcu_sb_arvalid,
    input  logic                  mcu_sb_arready,
    input  logic  [MCU_SB_BUS_TAG-1:0] mcu_sb_rid,
    input  logic  [AXI_DATA_W-1:0] mcu_sb_rdata,
    input  logic  [1:0]           mcu_sb_rresp,
    input  logic                  mcu_sb_rlast,
    input  logic                  mcu_sb_rvalid,
    output logic                  mcu_sb_rready,
    output logic [3:0]            mcu_sb_awcache,
    output logic [3:0]            mcu_sb_arcache,
    output logic [2:0]            mcu_sb_awprot,
    output logic [2:0]            mcu_sb_arprot,
    output logic [3:0]            mcu_sb_awregion,
    output logic [3:0]            mcu_sb_arregion,
    output logic [3:0]            mcu_sb_awqos,
    output logic [3:0]            mcu_sb_arqos,

    // =================================================================
    // MAS §2.4 — Straps
    // =================================================================
    input  logic [31:0] cptra_ss_strap_mcu_lsu_axi_user_i,
    input  logic [31:0] cptra_ss_strap_mcu_ifu_axi_user_i,
    input  logic [31:0] cptra_ss_strap_mcu_sram_config_axi_user_i,
    input  logic [31:0] cptra_ss_strap_mci_soc_config_axi_user_i,
    input  logic [31:0] cptra_ss_strap_caliptra_dma_axi_user_i,
    input  logic [31:0] cptra_ss_strap_mcu_reset_vector_i,
    input  logic [63:0] cptra_ss_strap_caliptra_base_addr_i,
    input  logic [63:0] cptra_ss_strap_mci_base_addr_i,
    input  logic [63:0] cptra_ss_strap_recovery_ifc_base_addr_i,
    input  logic [63:0] cptra_ss_strap_otp_fc_base_addr_i,
    input  logic [63:0] cptra_ss_strap_uds_seed_base_addr_i,
    input  logic [31:0] cptra_ss_strap_prod_debug_unlock_auth_pk_hash_reg_bank_offset_i,
    input  logic [31:0] cptra_ss_strap_num_of_prod_debug_unlock_auth_pk_hashes_i,
    input  logic [31:0] cptra_ss_strap_generic_0_i,
    input  logic [31:0] cptra_ss_strap_generic_1_i,
    input  logic [31:0] cptra_ss_strap_generic_2_i,
    input  logic [31:0] cptra_ss_strap_generic_3_i,
    input  logic [15:0] cptra_ss_strap_key_release_key_size_i,
    input  logic [63:0] cptra_ss_strap_key_release_base_addr_i,
    input  logic         cptra_ss_strap_ocp_lock_en_i
);

    // =================================================================
    // Internal Signals — MAS §3.11 Error Aggregation (RTL-Verified)
    // =================================================================
    logic [31:0] agg_error_fatal;
    logic [31:0] agg_error_non_fatal;

    // Sub-error signals from each component
    logic        cptra_err_fatal;
    logic        cptra_err_non_fatal;
    logic        mcu_dccm_ecc_single_error;
    logic        mcu_dccm_ecc_double_error;
    logic [2:0]  lc_alerts;   // NumAlerts=3 for LCC
    logic        fc_intr_otp_error;
    logic [4:0]  fc_alerts;   // NumAlerts=5 for FC
    logic        i3c_peripheral_reset;
    logic        i3c_escalated_reset;
    logic        i3c_irq;

    // MCI Signals
    logic        mci_intr;
    logic        mci_mcu_timer_int;
    logic        mci_mcu_nmi_int;
    logic [31:0] mci_mcu_nmi_vector;
    logic        mailbox_data_avail;
    logic [31:0] reset_vector;
    logic        cptra_in_debug_mode;

    // Boot FSM State (for debug visibility)
    boot_fsm_state_e boot_fsm_state;

    // Security state from MCI LCC translator
    logic debug_locked;

    // =================================================================
    // Error Aggregation (MAS §3.11 — exact bit mapping from RTL)
    // =================================================================
    assign agg_error_fatal[5:0]   = {5'b0, cptra_err_fatal};
    assign agg_error_fatal[11:6]  = {5'b0, mcu_dccm_ecc_double_error};
    assign agg_error_fatal[17:12] = {3'b0, lc_alerts};
    assign agg_error_fatal[23:18] = {fc_intr_otp_error, fc_alerts};
    assign agg_error_fatal[29:24] = {4'b0, i3c_peripheral_reset, i3c_escalated_reset};
    assign agg_error_fatal[31:30] = 2'b0;

    assign agg_error_non_fatal[5:0]   = {5'b0, cptra_err_non_fatal};
    assign agg_error_non_fatal[11:6]  = {5'b0, mcu_dccm_ecc_single_error};
    assign agg_error_non_fatal[17:12] = {3'b0, lc_alerts};
    assign agg_error_non_fatal[23:18] = {fc_intr_otp_error, fc_alerts};
    assign agg_error_non_fatal[29:24] = {4'b0, i3c_peripheral_reset, i3c_escalated_reset};
    assign agg_error_non_fatal[31:30] = 2'b0;

    // =================================================================
    // Top-Level Error Outputs
    // =================================================================
    assign cptra_error_fatal     = cptra_err_fatal;
    assign cptra_error_non_fatal = cptra_err_non_fatal;

    // =================================================================
    // Debug mode indication (MAS §3.12b)
    // =================================================================
    assign cptra_in_debug_mode = ~debug_locked;

    // =================================================================
    // Stub Instance: MCI Top (MAS §2.1)
    // TODO: Replace with full mci_top implementation
    // =================================================================
    mci_top_stub #(
        .MCU_SRAM_SIZE_KB(MCU_SRAM_SIZE_KB),
        .MCU_MBOX0_SIZE_KB(MCU_MBOX0_SIZE_KB),
        .MCU_MBOX1_SIZE_KB(MCU_MBOX1_SIZE_KB),
        .MIN_MCU_RST_COUNTER_WIDTH(MIN_MCU_RST_COUNTER_WIDTH)
    ) u_mci_top (
        .clk                        (cptra_ss_clk_i),
        .mci_rst_b                  (cptra_ss_rst_b_i),
        .mci_pwrgood                (cptra_ss_pwrgood_i),
        .scan_mode                  (cptra_ss_cptra_core_scan_mode_i),

        // RDC outputs
        .cptra_ss_rdc_clk_cg_o      (cptra_ss_rdc_clk_cg_o),
        .mcu_clk_cg_o               (cptra_ss_mcu_clk_cg_o),
        .cptra_ss_rst_b_o           (cptra_ss_rst_b_o),
        .rdc_clk_dis_o              (cptra_ss_warm_reset_rdc_clk_dis_o),
        .early_warm_reset_warn_o    (cptra_ss_early_warm_reset_warn_o),
        .fw_update_rdc_clk_dis_o    (cptra_ss_mcu_fw_update_rdc_clk_dis_o),

        // Reset control
        .mcu_rst_b_o                (cptra_ss_mcu_rst_b_o),
        .cptra_rst_b_o              (cptra_ss_mci_cptra_rst_b_o),

        // Straps
        .strap_mcu_lsu_axi_user     (cptra_ss_strap_mcu_lsu_axi_user_i),
        .strap_mcu_ifu_axi_user     (cptra_ss_strap_mcu_ifu_axi_user_i),
        .strap_mcu_sram_config_axi_user(cptra_ss_strap_mcu_sram_config_axi_user_i),
        .strap_mci_soc_config_axi_user(cptra_ss_strap_mci_soc_config_axi_user_i),
        .ss_debug_intent            (cptra_ss_debug_intent_i),
        .strap_mcu_reset_vector     (cptra_ss_strap_mcu_reset_vector_i),
        .mcu_no_rom_config          (cptra_ss_mcu_no_rom_config_i),
        .mci_boot_seq_brkpoint      (cptra_ss_mci_boot_seq_brkpoint_i),

        // Error aggregation
        .agg_error_fatal_i          (agg_error_fatal),
        .agg_error_non_fatal_i      (agg_error_non_fatal),
        .all_error_fatal_o          (cptra_ss_all_error_fatal_o),
        .all_error_non_fatal_o      (cptra_ss_all_error_non_fatal_o),

        // FW exec control
        .mcu_sram_fw_exec_region_lock(cptra_ss_cptra_generic_fw_exec_ctrl_2_mcu_i),

        // Interrupts
        .mci_intr_o                 (mci_intr),
        .mcu_timer_int_o            (mci_mcu_timer_int),
        .nmi_intr_o                 (mci_mcu_nmi_int),
        .mcu_nmi_vector_o           (mci_mcu_nmi_vector),

        // MCU Halt
        .mcu_cpu_halt_req_o         (cptra_ss_mcu_halt_req_o),
        .mcu_cpu_halt_ack_i         (cptra_ss_mcu_halt_ack_i),
        .mcu_cpu_halt_status_i      (cptra_ss_mcu_halt_status_i),

        // Mailbox
        .cptra_mbox_data_avail_i    (mailbox_data_avail),
        .soc_mcu_mbox0_data_avail_o (cptra_ss_soc_mcu_mbox0_data_avail),
        .soc_mcu_mbox1_data_avail_o (cptra_ss_soc_mcu_mbox1_data_avail),

        // Generic I/O
        .mci_generic_input_wires_i  (cptra_ss_mci_generic_input_wires_i),
        .mci_generic_output_wires_o (cptra_ss_mci_generic_output_wires_o),

        // Debug
        .ss_dbg_manuf_enable_i      (cptra_ss_dbg_manuf_enable_o),
        .ss_soc_dbg_unlock_level_i  (cptra_ss_cptra_core_soc_prod_dbg_unlock_level_o),
        .debug_locked_o             (debug_locked),

        // AXI subordinate
        .s_axi_awaddr               (cptra_ss_mci_s_axi_awaddr),
        .s_axi_awid                 (cptra_ss_mci_s_axi_awid),
        .s_axi_awlen                (cptra_ss_mci_s_axi_awlen),
        .s_axi_awsize               (cptra_ss_mci_s_axi_awsize),
        .s_axi_awburst              (cptra_ss_mci_s_axi_awburst),
        .s_axi_awlock               (cptra_ss_mci_s_axi_awlock),
        .s_axi_awuser               (cptra_ss_mci_s_axi_awuser),
        .s_axi_awvalid              (cptra_ss_mci_s_axi_awvalid),
        .s_axi_awready              (cptra_ss_mci_s_axi_awready),
        .s_axi_wdata                (cptra_ss_mci_s_axi_wdata),
        .s_axi_wstrb                (cptra_ss_mci_s_axi_wstrb),
        .s_axi_wlast                (cptra_ss_mci_s_axi_wlast),
        .s_axi_wvalid               (cptra_ss_mci_s_axi_wvalid),
        .s_axi_wready               (cptra_ss_mci_s_axi_wready),
        .s_axi_bid                  (cptra_ss_mci_s_axi_bid),
        .s_axi_bresp                (cptra_ss_mci_s_axi_bresp),
        .s_axi_bvalid               (cptra_ss_mci_s_axi_bvalid),
        .s_axi_bready               (cptra_ss_mci_s_axi_bready),
        .s_axi_araddr               (cptra_ss_mci_s_axi_araddr),
        .s_axi_arid                 (cptra_ss_mci_s_axi_arid),
        .s_axi_arlen                (cptra_ss_mci_s_axi_arlen),
        .s_axi_arsize               (cptra_ss_mci_s_axi_arsize),
        .s_axi_arburst              (cptra_ss_mci_s_axi_arburst),
        .s_axi_arlock               (cptra_ss_mci_s_axi_arlock),
        .s_axi_aruser               (cptra_ss_mci_s_axi_aruser),
        .s_axi_arvalid              (cptra_ss_mci_s_axi_arvalid),
        .s_axi_arready              (cptra_ss_mci_s_axi_arready),
        .s_axi_rid                  (cptra_ss_mci_s_axi_rid),
        .s_axi_rdata                (cptra_ss_mci_s_axi_rdata),
        .s_axi_rresp                (cptra_ss_mci_s_axi_rresp),
        .s_axi_rlast                (cptra_ss_mci_s_axi_rlast),
        .s_axi_rvalid               (cptra_ss_mci_s_axi_rvalid),
        .s_axi_rready               (cptra_ss_mci_s_axi_rready),

        // Boot FSM state for debug
        .boot_fsm_state_o           (boot_fsm_state),

        // Lifecycle
        .otp_state_valid_o          (caliptra_ss_otp_state_valid_o),
        .volatile_raw_unlock_success_o(caliptra_ss_volatile_raw_unlock_success_o),

        // FIPS
        .FIPS_ZEROIZATION_PPD_i     (cptra_ss_FIPS_ZEROIZATION_PPD_i)
    );

    // =================================================================
    // Stub Instance: Caliptra Core (MAS §2.1)
    // TODO: Replace with caliptra_top instantiation
    // =================================================================
    caliptra_top_stub u_caliptra_top (
        .clk                        (cptra_ss_clk_i),
        .cptra_rst_b                (cptra_ss_mci_cptra_rst_b_i),
        .cptra_pwrgood              (cptra_ss_pwrgood_i),
        .cptra_error_fatal          (cptra_err_fatal),
        .cptra_error_non_fatal      (cptra_err_non_fatal),
        .BootFSM_BrkPoint           (cptra_ss_cptra_core_bootfsm_bp_i),
        .scan_mode                  (cptra_ss_cptra_core_scan_mode_i),
        .recovery_data_avail        (cptra_ss_i3c_recovery_payload_available_i),
        .recovery_image_activated   (cptra_ss_i3c_recovery_image_activated_i),
        .mailbox_data_avail         (mailbox_data_avail),
        .ss_dbg_manuf_enable        (cptra_ss_dbg_manuf_enable_o),
        .ss_soc_dbg_unlock_level    (cptra_ss_cptra_core_soc_prod_dbg_unlock_level_o),
        .ss_generic_fw_exec_ctrl    ({2'b0, cptra_ss_cptra_generic_fw_exec_ctrl_2_mcu_o, cptra_ss_cptra_generic_fw_exec_ctrl_o}),
        .generic_input_wires        (cptra_ss_cptra_core_generic_input_wires_i),
        .generic_output_wires       (cptra_ss_cptra_core_generic_output_wires_o),
        .debug_locked_i             (debug_locked)
    );

    assign cptra_ss_cptra_generic_fw_exec_ctrl_2_mcu_o = cptra_ss_cptra_generic_fw_exec_ctrl_2_mcu_i;

    // =================================================================
    // Stub Instance: MCU Top (MAS §2.1 — VeeR-EL2)
    // TODO: Replace with mcu_top instantiation
    // =================================================================
    mcu_top_stub u_mcu_top (
        .clk                        (cptra_ss_mcu_clk_cg_o),
        .rst_l                      (cptra_ss_mcu_rst_b_i),
        .rst_vec                    (reset_vector[31:1]),
        .timer_int                  (mci_mcu_timer_int),
        .nmi_int                    (mci_mcu_nmi_int),
        .nmi_vec                    (mci_mcu_nmi_vector[31:1]),
        .dccm_ecc_single_error      (mcu_dccm_ecc_single_error),
        .dccm_ecc_double_error      (mcu_dccm_ecc_double_error),
        .ext_int                    ({cptra_ss_mcu_ext_int, i3c_irq, mci_intr})
    );

    // =================================================================
    // Stub Instance: I3C Core (MAS §2.1)
    // TODO: Replace with i3c_wrapper instantiation
    // =================================================================
    i3c_core_stub u_i3c_core (
        .clk_i                      (cptra_ss_clk_i),
        .rst_ni                     (cptra_ss_rst_b_o),
        .scl_i                      (cptra_ss_i3c_scl_i),
        .sda_i                      (cptra_ss_i3c_sda_i),
        .scl_o                      (cptra_ss_i3c_scl_o),
        .sda_o                      (cptra_ss_i3c_sda_o),
        .scl_oe                     (cptra_ss_i3c_scl_oe),
        .sda_oe                     (cptra_ss_i3c_sda_oe),
        .sel_od_pp_o                (cptra_ss_sel_od_pp_o),
        .irq_o                      (i3c_irq),
        .peripheral_reset_o         (i3c_peripheral_reset),
        .escalated_reset_o          (i3c_escalated_reset),
        .recovery_payload_available_o(cptra_ss_i3c_recovery_payload_available_o),
        .recovery_image_activated_o (cptra_ss_i3c_recovery_image_activated_o)
    );

    // =================================================================
    // Stub Instance: Fuse Controller (MAS §2.1)
    // =================================================================
    otp_ctrl_stub u_otp_ctrl (
        .clk_i                      (cptra_ss_clk_i),
        .rst_ni                     (cptra_ss_rst_b_o),
        .intr_otp_error_o           (fc_intr_otp_error),
        .alerts_o                   (fc_alerts)
    );

    // =================================================================
    // Stub Instance: Life Cycle Controller (MAS §2.1)
    // =================================================================
    lc_ctrl_stub u_lc_ctrl (
        .clk_i                      (cptra_ss_clk_i),
        .rst_ni                     (cptra_ss_rst_b_o),
        .alerts_o                   (lc_alerts)
    );

endmodule
