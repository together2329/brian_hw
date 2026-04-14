//********************************************************************************
// SPDX-License-Identifier: Apache-2.0
//
// Caliptra Subsystem — Stub Modules
// MAS Reference: caliptra_ss/mas/caliptra_ss_mas.md §2.1
//
// These stubs provide minimal structural scaffolding matching the MAS port
// contracts. Each stub:
//   1. Accepts all ports defined in the MAS
//   2. Drives outputs to safe reset values
//   3. Contains placeholder comments for full implementation
//
//********************************************************************************

// =================================================================
// MCI Top Stub — MAS §2.1 (Manufacturer Control Interface)
// =================================================================
module mci_top_stub #(
    parameter MCU_SRAM_SIZE_KB          = 512,
    parameter MCU_MBOX0_SIZE_KB         = 4,
    parameter MCU_MBOX1_SIZE_KB         = 4,
    parameter MIN_MCU_RST_COUNTER_WIDTH = 4,
    parameter AXI_ADDR_W = 64, AXI_DATA_W = 32, AXI_USER_W = 32, AXI_ID_W = 8
)(
    input  logic clk,
    input  logic mci_rst_b,
    input  logic mci_pwrgood,
    input  logic scan_mode,

    // RDC outputs
    output logic cptra_ss_rdc_clk_cg_o,
    output logic mcu_clk_cg_o,
    output logic cptra_ss_rst_b_o,
    output logic rdc_clk_dis_o,
    output logic early_warm_reset_warn_o,
    output logic fw_update_rdc_clk_dis_o,

    // Reset control
    output logic mcu_rst_b_o,
    output logic cptra_rst_b_o,

    // Straps
    input  logic [31:0] strap_mcu_lsu_axi_user,
    input  logic [31:0] strap_mcu_ifu_axi_user,
    input  logic [31:0] strap_mcu_sram_config_axi_user,
    input  logic [31:0] strap_mci_soc_config_axi_user,
    input  logic         ss_debug_intent,
    input  logic [31:0] strap_mcu_reset_vector,
    input  logic         mcu_no_rom_config,
    input  logic         mci_boot_seq_brkpoint,

    // Error aggregation
    input  logic [31:0] agg_error_fatal_i,
    input  logic [31:0] agg_error_non_fatal_i,
    output logic        all_error_fatal_o,
    output logic        all_error_non_fatal_o,

    // FW exec control
    input  logic mcu_sram_fw_exec_region_lock,

    // Interrupts
    output logic        mci_intr_o,
    output logic        mcu_timer_int_o,
    output logic        nmi_intr_o,
    output logic [31:0] mcu_nmi_vector_o,

    // MCU Halt
    output logic mcu_cpu_halt_req_o,
    input  logic mcu_cpu_halt_ack_i,
    input  logic mcu_cpu_halt_status_i,

    // Mailbox
    input  logic cptra_mbox_data_avail_i,
    output logic soc_mcu_mbox0_data_avail_o,
    output logic soc_mcu_mbox1_data_avail_o,

    // Generic I/O
    input  logic [63:0] mci_generic_input_wires_i,
    output logic [63:0] mci_generic_output_wires_o,

    // Debug
    input  logic         ss_dbg_manuf_enable_i,
    input  logic [63:0]  ss_soc_dbg_unlock_level_i,
    output logic         debug_locked_o,

    // AXI subordinate (MCI CSR space)
    input  logic [AXI_ADDR_W-1:0] s_axi_awaddr,
    input  logic [AXI_ID_W-1:0]   s_axi_awid,
    input  logic [7:0]            s_axi_awlen,
    input  logic [2:0]            s_axi_awsize,
    input  logic [1:0]            s_axi_awburst,
    input  logic                  s_axi_awlock,
    input  logic [AXI_USER_W-1:0] s_axi_awuser,
    input  logic                  s_axi_awvalid,
    output logic                  s_axi_awready,
    input  logic [AXI_DATA_W-1:0] s_axi_wdata,
    input  logic [(AXI_DATA_W/8)-1:0] s_axi_wstrb,
    input  logic                  s_axi_wlast,
    input  logic                  s_axi_wvalid,
    output logic                  s_axi_wready,
    output logic [AXI_ID_W-1:0]   s_axi_bid,
    output logic [1:0]            s_axi_bresp,
    output logic                  s_axi_bvalid,
    input  logic                  s_axi_bready,
    input  logic [AXI_ADDR_W-1:0] s_axi_araddr,
    input  logic [AXI_ID_W-1:0]   s_axi_arid,
    input  logic [7:0]            s_axi_arlen,
    input  logic [2:0]            s_axi_arsize,
    input  logic [1:0]            s_axi_arburst,
    input  logic                  s_axi_arlock,
    input  logic [AXI_USER_W-1:0] s_axi_aruser,
    input  logic                  s_axi_arvalid,
    output logic                  s_axi_arready,
    output logic [AXI_ID_W-1:0]   s_axi_rid,
    output logic [AXI_DATA_W-1:0] s_axi_rdata,
    output logic [1:0]            s_axi_rresp,
    output logic                  s_axi_rlast,
    output logic                  s_axi_rvalid,
    input  logic                  s_axi_rready,

    // Boot FSM state (debug visibility)
    output logic [3:0] boot_fsm_state_o,

    // Lifecycle
    output logic otp_state_valid_o,
    output logic volatile_raw_unlock_success_o,

    // FIPS
    input  logic FIPS_ZEROIZATION_PPD_i
);

    import caliptra_ss_top_pkg::*;

    // Reset defaults
    assign cptra_ss_rdc_clk_cg_o  = clk;       // Pass-through (no gating in stub)
    assign mcu_clk_cg_o           = clk;
    assign cptra_ss_rst_b_o       = mci_rst_b;  // Pass-through
    assign rdc_clk_dis_o          = 1'b0;
    assign early_warm_reset_warn_o = 1'b0;
    assign fw_update_rdc_clk_dis_o = 1'b0;
    assign mcu_rst_b_o            = 1'b0;       // MCU held in reset
    assign cptra_rst_b_o          = 1'b0;       // Caliptra held in reset

    // Error outputs
    assign all_error_fatal_o     = 1'b0;
    assign all_error_non_fatal_o = 1'b0;

    // Interrupts
    assign mci_intr_o      = 1'b0;
    assign mcu_timer_int_o = 1'b0;
    assign nmi_intr_o      = 1'b0;
    assign mcu_nmi_vector_o = 32'h0;

    // Halt
    assign mcu_cpu_halt_req_o = 1'b0;

    // Mailbox
    assign soc_mcu_mbox0_data_avail_o = 1'b0;
    assign soc_mcu_mbox1_data_avail_o = 1'b0;

    // Generic I/O
    assign mci_generic_output_wires_o = 64'h0;

    // Debug
    assign debug_locked_o = 1'b1;  // Default: debug locked

    // AXI subordinate — respond with DECERR to all transactions
    assign s_axi_awready = 1'b1;
    assign s_axi_wready  = 1'b1;
    assign s_axi_bid     = s_axi_awid;
    assign s_axi_bresp   = 2'b11;  // DECERR
    assign s_axi_bvalid  = 1'b0;
    assign s_axi_arready = 1'b1;
    assign s_axi_rid     = s_axi_arid;
    assign s_axi_rdata   = 32'h0;
    assign s_axi_rresp   = 2'b11;  // DECERR
    assign s_axi_rlast   = 1'b1;
    assign s_axi_rvalid  = 1'b0;

    // Boot FSM
    assign boot_fsm_state_o = BOOT_IDLE;

    // Lifecycle
    assign otp_state_valid_o           = 1'b0;
    assign volatile_raw_unlock_success_o = 1'b0;

endmodule

// =================================================================
// Caliptra Core Stub — MAS §2.1
// =================================================================
module caliptra_top_stub (
    input  logic        clk,
    input  logic        cptra_rst_b,
    input  logic        cptra_pwrgood,
    output logic        cptra_error_fatal,
    output logic        cptra_error_non_fatal,
    input  logic        BootFSM_BrkPoint,
    input  logic        scan_mode,
    input  logic        recovery_data_avail,
    input  logic        recovery_image_activated,
    output logic        mailbox_data_avail,
    output logic        ss_dbg_manuf_enable,
    output logic [63:0] ss_soc_dbg_unlock_level,
    output logic [126:0] ss_generic_fw_exec_ctrl,
    input  logic [63:0] generic_input_wires,
    output logic [63:0] generic_output_wires,
    input  logic        debug_locked_i
);

    assign cptra_error_fatal       = 1'b0;
    assign cptra_error_non_fatal   = 1'b0;
    assign mailbox_data_avail      = 1'b0;
    assign ss_dbg_manuf_enable     = 1'b0;
    assign ss_soc_dbg_unlock_level = 64'h0;
    assign ss_generic_fw_exec_ctrl = 127'b0;
    assign generic_output_wires    = 64'h0;

endmodule

// =================================================================
// MCU Top Stub — MAS §2.1 (VeeR-EL2 RISC-V Core)
// =================================================================
module mcu_top_stub (
    input  logic clk,
    input  logic rst_l,
    input  logic [30:0] rst_vec,
    input  logic        timer_int,
    input  logic        nmi_int,
    input  logic [30:0] nmi_vec,
    output logic        dccm_ecc_single_error,
    output logic        dccm_ecc_double_error,
    input  logic [PIC_TOTAL_INT-1:1] ext_int
);

    import caliptra_ss_top_pkg::*;

    assign dccm_ecc_single_error = 1'b0;
    assign dccm_ecc_double_error = 1'b0;

endmodule

// =================================================================
// I3C Core Stub — MAS §2.1
// =================================================================
module i3c_core_stub (
    input  logic clk_i,
    input  logic rst_ni,
    input  logic scl_i,
    input  logic sda_i,
    output logic scl_o,
    output logic sda_o,
    output logic scl_oe,
    output logic sda_oe,
    output logic sel_od_pp_o,
    output logic irq_o,
    output logic peripheral_reset_o,
    output logic escalated_reset_o,
    output logic recovery_payload_available_o,
    output logic recovery_image_activated_o
);

    assign scl_o  = 1'b0;
    assign sda_o  = 1'b0;
    assign scl_oe = 1'b0;
    assign sda_oe = 1'b0;
    assign sel_od_pp_o = 1'b0;
    assign irq_o = 1'b0;
    assign peripheral_reset_o = 1'b0;
    assign escalated_reset_o = 1'b0;
    assign recovery_payload_available_o = 1'b0;
    assign recovery_image_activated_o   = 1'b0;

endmodule

// =================================================================
// OTP Controller (Fuse Controller) Stub — MAS §2.1
// =================================================================
module otp_ctrl_stub (
    input  logic        clk_i,
    input  logic        rst_ni,
    output logic        intr_otp_error_o,
    output logic [4:0]  alerts_o
);

    assign intr_otp_error_o = 1'b0;
    assign alerts_o = 5'b0;

endmodule

// =================================================================
// Life Cycle Controller Stub — MAS §2.1
// =================================================================
module lc_ctrl_stub (
    input  logic        clk_i,
    input  logic        rst_ni,
    output logic [2:0]  alerts_o
);

    assign alerts_o = 3'b0;

endmodule
