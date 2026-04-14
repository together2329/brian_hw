// SPDX-License-Identifier: Apache-2.0
//
// Caliptra Subsystem — Top-Level Package
// MAS Reference: caliptra_ss/mas/caliptra_ss_mas.md §2.3, §3.12
//
// This file defines all types, enums, and constants for the Caliptra Subsystem.

`ifndef CALIPTRA_SS_TOP_PKG_SV
`define CALIPTRA_SS_TOP_PKG_SV

package caliptra_ss_top_pkg;

    // -------------------------------------------------------
    // AXI Bus Parameters (MAS §2.3)
    // -------------------------------------------------------
    parameter int unsigned AXI_DATA_W   = 32;
    parameter int unsigned AXI_USER_W   = 32;
    parameter int unsigned AXI_ID_W     = 8;
    parameter int unsigned AXI_ADDR_W   = 64;

    // -------------------------------------------------------
    // MCU VeeR-EL2 Bus Tag Widths (MAS §2.3)
    // -------------------------------------------------------
    parameter int unsigned MCU_IFU_BUS_TAG = 3;  // IDs 0–7
    parameter int unsigned MCU_LSU_BUS_TAG = 3;  // IDs 0–7
    parameter int unsigned MCU_SB_BUS_TAG  = 1;  // IDs 0–1
    parameter int unsigned PIC_TOTAL_INT   = 255;

    // -------------------------------------------------------
    // Interrupt Vector Assignments (MAS §5.1)
    // -------------------------------------------------------
    parameter int unsigned VEER_INTR_VEC_MCI     = 1;
    parameter int unsigned VEER_INTR_VEC_I3C     = 2;
    parameter int unsigned VEER_INTR_EXT_LSB     = 3;

    // -------------------------------------------------------
    // Error Aggregation Bit Map (MAS §3.11 — RTL-Verified)
    // -------------------------------------------------------
    // Fatal / Non-Fatal aggregate bus [31:0]:
    //   [5:0]   = Caliptra core  (bit 5 active)
    //   [11:6]  = MCU            (bit 6 = DCCM ECC)
    //   [17:12] = LCC alerts
    //   [23:18] = FC (otp_error + alerts)
    //   [29:24] = I3C            (bit 25=peripheral_rst, bit 24=escalated_rst)
    //   [31:30] = Spare

    parameter int unsigned AGG_CPTRA_BIT     = 5;
    parameter int unsigned AGG_MCU_DCCM_BIT  = 6;
    parameter int unsigned AGG_LCC_LSB       = 12;
    parameter int unsigned AGG_FC_LSB        = 18;
    parameter int unsigned AGG_I3C_LSB       = 24;
    parameter int unsigned AGG_SPARE_LSB     = 30;

    // -------------------------------------------------------
    // Boot FSM Encoding (MAS §3.12 — RTL-Verified from mci_pkg.sv)
    // -------------------------------------------------------
    typedef enum logic [3:0] {
        BOOT_IDLE               = 4'h0,
        BOOT_OTP_FC             = 4'h1,
        BOOT_LCC                = 4'h2,
        BOOT_BREAKPOINT_CHECK   = 4'h3,
        BOOT_BREAKPOINT         = 4'h4,
        BOOT_MCU                = 4'h5,
        BOOT_WAIT_CPTRA_GO      = 4'h6,
        BOOT_CPTRA              = 4'h7,
        BOOT_WAIT_MCU_RST_REQ   = 4'h8,
        BOOT_HALT_MCU           = 4'h9,
        BOOT_WAIT_MCU_HALTED    = 4'ha,
        BOOT_RST_MCU            = 4'hb,
        BOOT_UNKNOWN            = 4'hf
    } boot_fsm_state_e;

    // -------------------------------------------------------
    // LCC State Translator FSM (MAS §3.12b — RTL-Verified)
    // -------------------------------------------------------
    typedef enum logic [2:0] {
        TRANSLATOR_RESET            = 3'd0,
        TRANSLATOR_IDLE             = 3'd1,
        TRANSLATOR_NON_DEBUG        = 3'd2,
        TRANSLATOR_UNPROV_DEBUG     = 3'd3,
        TRANSLATOR_MANUF_NON_DEBUG  = 3'd4,
        TRANSLATOR_MANUF_DEBUG      = 3'd5,
        TRANSLATOR_PROD_NON_DEBUG   = 3'd6,
        TRANSLATOR_PROD_DEBUG       = 3'd7
    } translator_state_e;

    // -------------------------------------------------------
    // Reset Reason Encoding (MAS §3.9)
    // -------------------------------------------------------
    typedef enum logic [1:0] {
        RESET_REASON_WARM            = 2'd0,
        RESET_REASON_FW_BOOT_UPD    = 2'd1,
        RESET_REASON_FW_HITLESS_UPD = 2'd2
    } reset_reason_e;

    // -------------------------------------------------------
    // Mailbox Data Widths (MAS §6.1)
    // -------------------------------------------------------
    parameter int unsigned MCU_MBOX_DATA_W     = 32;
    parameter int unsigned MCU_MBOX_ECC_DATA_W = 7;
    parameter int unsigned MCU_MBOX_TOTAL_W    = MCU_MBOX_DATA_W + MCU_MBOX_ECC_DATA_W;

    // -------------------------------------------------------
    // WDT Configuration (MAS §3.10)
    // -------------------------------------------------------
    parameter int unsigned MCI_WDT_TIMEOUT_PERIOD_NUM_DWORDS = 2;
    parameter int unsigned MCI_MCU_UPDATE_RESET_CYCLES       = 10;

    // -------------------------------------------------------
    // Default Mailbox AXI User
    // -------------------------------------------------------
    parameter logic [31:0] MCU_DEF_MBOX_VALID_AXI_USER = 32'hFFFF_FFFF;

    // -------------------------------------------------------
    // MCI Register Addresses (MAS §4.2 — RTL-Verified)
    // -------------------------------------------------------
    localparam logic [31:0] MCI_BASE                         = 32'h2100_0000;
    localparam logic [31:0] MCI_HW_CAPABILITIES              = 32'h2100_0000;
    localparam logic [31:0] MCI_FW_CAPABILITIES              = 32'h2100_0004;
    localparam logic [31:0] MCI_CAP_LOCK                     = 32'h2100_0008;
    localparam logic [31:0] MCI_HW_REV_ID                    = 32'h2100_000C;
    localparam logic [31:0] MCI_FW_FLOW_STATUS               = 32'h2100_0030;
    localparam logic [31:0] MCI_HW_FLOW_STATUS               = 32'h2100_0034;
    localparam logic [31:0] MCI_RESET_REASON                 = 32'h2100_0038;
    localparam logic [31:0] MCI_RESET_STATUS                 = 32'h2100_003C;
    localparam logic [31:0] MCI_SECURITY_STATE               = 32'h2100_0040;
    localparam logic [31:0] MCI_HW_ERROR_FATAL               = 32'h2100_0050;
    localparam logic [31:0] MCI_AGG_ERROR_FATAL              = 32'h2100_0054;
    localparam logic [31:0] MCI_HW_ERROR_NON_FATAL           = 32'h2100_0058;
    localparam logic [31:0] MCI_AGG_ERROR_NON_FATAL          = 32'h2100_005C;
    localparam logic [31:0] MCI_FW_ERROR_FATAL               = 32'h2100_0060;
    localparam logic [31:0] MCI_FW_ERROR_NON_FATAL           = 32'h2100_0064;
    localparam logic [31:0] MCI_RESET_REQUEST                = 32'h2100_0100;
    localparam logic [31:0] MCI_MCI_BOOTFSM_GO               = 32'h2100_0104;
    localparam logic [31:0] MCI_CPTRA_BOOT_GO                = 32'h2100_0108;
    localparam logic [31:0] MCI_FW_SRAM_EXEC_REGION_SIZE     = 32'h2100_010C;
    localparam logic [31:0] MCI_MCU_NMI_VECTOR               = 32'h2100_0110;
    localparam logic [31:0] MCI_MCU_RESET_VECTOR             = 32'h2100_0114;

    // -------------------------------------------------------
    // I3C CSR Base Address (MAS §4.1)
    // -------------------------------------------------------
    localparam logic [31:0] I3C_CSR_BASE                     = 32'h2000_4000;

    // -------------------------------------------------------
    // FC / OTP Base Address (MAS §4.1)
    // -------------------------------------------------------
    localparam logic [31:0] OTP_FC_BASE                       = 32'h7000_0000;

    // -------------------------------------------------------
    // LC Controller Base Address (MAS §4.1)
    // -------------------------------------------------------
    localparam logic [31:0] LC_CTRL_BASE                      = 32'h7000_0400;

endpackage

`endif // CALIPTRA_SS_TOP_PKG_SV
