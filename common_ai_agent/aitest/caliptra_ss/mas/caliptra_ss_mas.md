# Caliptra Subsystem (caliptra_ss) — Single Source of Truth (SSoT)

**Version**: 2.1  
**Date**: 2025-01-12  
**Status**: Final Release — SSoT for RTL, TB/TC, and DOC  

> **This document is the single source of truth for all downstream design work.**  
> RTL implementations, testbench/test-case generation, and documentation **must** derive from this document.  
> Any discrepancy between this MAS and RTL/behavior shall be resolved in favor of this document unless a formal waiver is filed.  
>  
> **Derived from (traceability):**
> - `caliptra-ss/docs/CaliptraSSHardwareSpecification.md` v2p1
> - `caliptra-ss/docs/CaliptraSSIntegrationSpecification.md` v2p1
> - `caliptra-ss/src/integration/rtl/caliptra_ss_top.sv` (RTL-verified)
> - `caliptra-ss/src/integration/rtl/soc_address_map/soc_address_map_defines.svh` (address-verified)
> - `caliptra-ss/src/mci/rtl/mci_pkg.sv` (FSM encoding verified)
> - `caliptra-ss/src/mci/rtl/mci_boot_seqr.sv` (boot FSM verified)

---

## 1. Overview

The Caliptra Subsystem (CSS) is a complete Root of Trust (RoT) for datacenter-class System on Chips (SoCs), including CPUs, GPUs, DPUs, and TPUs. It integrates the Caliptra 2.0 RoT IP with additional infrastructure to support manufacturer-specific controls, forming a self-contained security subsystem.

The subsystem operates in **Caliptra-subsystem-mode**, where Caliptra owns the recovery interface (I3C or AXI streaming boot) and serves as THE Root of Trust for the SoC. Key design goals include:

- **Secure Boot**: Caliptra authenticates, measures, and loads Manufacturer Control Unit (MCU) firmware at boot time.
- **Manufacturer Control**: MCU runs manufacturer-specific firmware for SoC initialization, reset control, security policy enforcement, and SoC configuration.
- **Lifecycle Management**: Hardware-based lifecycle controller (LCC) manages device states from RAW through manufacturing, production, and end-of-life (RMA/SCRAP).
- **Fuse Management**: Fuse Controller (FC) manages one-time programmable storage for secrets (UDS, field entropy) and configuration data with ECC protection.
- **Recovery Support**: I3C and AXI streaming boot interfaces enable firmware recovery through OCP streaming boot protocol.
- **Debug Architecture**: Multi-level debug access with production debug unlock using post-quantum resilient hybrid (ECC + MLDSA) authentication.
- **Error Aggregation**: Centralized error reporting through MCI with configurable severity masking.

---

## 2. Module Hierarchy

### 2.1 Instantiation Tree

```
caliptra_ss_top
├── caliptra_top_ss                      // Caliptra Core 2.0 RoT IP
│   ├── caliptra_core                    // RISC-V core + crypto accelerators
│   │   ├── veer_el2_wrapper             // Caliptra's internal RISC-V core
│   │   ├── sha256_accelerator
│   │   ├── sha512_accelerator
│   │   ├── ecc_accelerator
│   │   ├── aes_accelerator
│   │   ├── hmac_accelerator
│   │   ├── doe_accelerator              // Data Object Encryption
│   │   ├── mldsa_accelerator            // Post-Quantum ML-DSA (Adams Bridge)
│   │   └── key_vault                    // Caliptra internal KV + SOC KV
│   ├── soc_ifc                          // SOC interface (AXI DMA, mailbox, etc.)
│   │   ├── axi_dma                      // AXI DMA engine
│   │   └── mailbox                      // Caliptra core mailbox
│   └── rom                              // Caliptra ROM
│
├── mcu_top                              // Manufacturer Control Unit
│   └── css_mcu0_el2                     // VeeR-EL2 RISC-V core
│       ├── ifu                          // Instruction Fetch Unit
│       ├── lsu                          // Load Store Unit
│       ├── icache                       // Instruction Cache (16 KiB)
│       ├── dccm                         // Data Closely Coupled Memory (16 KiB)
│       ├── pic                          // Programmable Interrupt Controller
│       └── dmi_jtag                     // Debug Module Interface + JTAG
│
├── mci_top                              // Manufacturer Control Interface
│   ├── mci_reg                          // MCI CSR register bank
│   ├── mcu_mbox0                        // MCU Mailbox 0 (up to 2 MiB SRAM)
│   ├── mcu_mbox1                        // MCU Mailbox 1 (up to 2 MiB SRAM)
│   ├── mcu_sram                         // MCU shared SRAM (4 KiB – 2 MiB)
│   ├── mcu_trace_buffer                 // MCU trace buffer (64 packets)
│   ├── wdt                              // Watchdog Timer (2 cascaded timers)
│   ├── mtimer                          // RISC-V mtime/mtimecmp timer
│   └── boot_fsm                         // CSS Boot Sequencer FSM
│
├── i3c_core                             // I3C Core (recovery interface)
│   ├── i3c_controller                   // I3C bus controller
│   ├── recovery_handler                 // Streaming Boot Recovery Handler
│   └── tti_queues                       // TTI TX/RX Queues
│
├── otp_ctrl                             // Fuse Controller (FC)
│   ├── otp_ctrl_core                    // OTP controller core logic
│   ├── otp_ctrl_part_buf                // Partition buffers (secret partitions)
│   ├── otp_ctrl_dai                     // Direct Access Interface
│   ├── otp_ctrl_lci                     // Lifecycle Interface
│   └── otp_ctrl_prim                    // OTP primitive interface
│
├── lc_ctrl                              // Life Cycle Controller (LCC)
│   ├── lc_ctrl_state                    // LC state machine
│   ├── lc_ctrl_transition               // State transition logic
│   ├── lc_ctrl_token                    // Token hashing/comparison
│   └── lc_ctrl_kmac_if                  // KMAC interface for token hashing
│
├── tlul_adapter                         // TileLink-UL to AXI adapter(s)
│
└── [External SRAM Instances]            // SRAMs instantiated outside CSS
    ├── caliptra_core_iccm_sram
    ├── caliptra_core_dccm_sram
    ├── caliptra_core_mbox_sram
    ├── caliptra_core_imem_rom
    ├── caliptra_core_mldsa_sram
    ├── mcu_dccm_sram
    ├── mcu_icache_sram
    ├── mcu_rom
    ├── mcu_sram
    ├── mcu_mbox0_sram
    └── mcu_mbox1_sram
```

### 2.2 Top-Level Interface (Ports)

#### 2.2.1 Clock, Reset, Power

| Name                          | Width | Dir  | Clock Domain        | Description                                              |
|-------------------------------|-------|------|---------------------|----------------------------------------------------------|
| `cptra_ss_clk_i`              | 1     | in   | —                   | System clock (333–400 MHz required for I3C tSCO timing)  |
| `cptra_ss_pwrgood_i`          | 1     | in   | async               | Power good, active-high. Deassert triggers hard reset    |
| `cptra_ss_rst_b_i`            | 1     | in   | `cptra_ss_clk_i`    | Primary reset, active-low synchronous, min 2 cycles      |
| `cptra_ss_rst_b_o`            | 1     | out  | `cptra_ss_rdc_clk_cg_o` | Delayed reset for RDC crossing, used for memory reset |
| `cptra_ss_warm_reset_rdc_clk_dis_o` | 1 | out | `cptra_ss_clk_i`  | Clock disable for warm reset RDC                         |
| `cptra_ss_early_warm_reset_warn_o`   | 1 | out | `cptra_ss_clk_i`  | Early reset warn for security signals                    |
| `cptra_ss_mcu_fw_update_rdc_clk_dis_o`| 1| out | `cptra_ss_clk_i` | Clock disable for MCU FW update RDC                      |
| `cptra_ss_rdc_clk_cg_o`       | 1     | out  | —                   | Gated clock for RDC crossing (same freq as clk_i)        |
| `cptra_ss_mcu_clk_cg_o`       | 1     | out  | —                   | MCU gated clock for RDC (same freq as clk_i)             |

#### 2.2.2 Caliptra Core Reset Control

| Name                          | Width | Dir  | Clock Domain        | Description                                              |
|-------------------------------|-------|------|---------------------|----------------------------------------------------------|
| `cptra_ss_mci_cptra_rst_b_i`  | 1     | in   | `cptra_ss_clk_i`    | Caliptra core reset input from MCI (loopback)            |
| `cptra_ss_mci_cptra_rst_b_o`  | 1     | out  | `cptra_ss_clk_i`    | Caliptra core reset output from MCI                      |

#### 2.2.3 MCU Reset Control

| Name                          | Width | Dir  | Clock Domain        | Description                                              |
|-------------------------------|-------|------|---------------------|----------------------------------------------------------|
| `cptra_ss_mcu_rst_b_i`        | 1     | in   | `cptra_ss_clk_i`    | MCU reset input (loopback from MCI output)               |
| `cptra_ss_mcu_rst_b_o`        | 1     | out  | `cptra_ss_clk_i`    | MCU reset output from MCI                                |

#### 2.2.4 AXI Manager Interfaces (MCU LSU)

| Name                                      | Width | Dir  | Description                                  |
|-------------------------------------------|-------|------|----------------------------------------------|
| `cptra_ss_mcu_lsu_m_axi_if_w_mgr`         | —     | out  | MCU LSU AXI write manager (AW=64, DW=32, IW=3, UW=32) |
| `cptra_ss_mcu_lsu_m_axi_if_r_mgr`         | —     | out  | MCU LSU AXI read manager                     |
| `cptra_ss_mcu_lsu_m_axi_if_awcache`       | 4     | out  | AWCACHE attributes                           |
| `cptra_ss_mcu_lsu_m_axi_if_awprot`        | 3     | out  | AWPROT attributes                            |
| `cptra_ss_mcu_lsu_m_axi_if_awregion`      | 4     | out  | AWREGION attributes                          |
| `cptra_ss_mcu_lsu_m_axi_if_awqos`         | 4     | out  | AWQOS attributes                             |
| `cptra_ss_mcu_lsu_m_axi_if_arcache`       | 4     | out  | ARCACHE attributes                           |
| `cptra_ss_mcu_lsu_m_axi_if_arprot`        | 3     | out  | ARPROT attributes                            |
| `cptra_ss_mcu_lsu_m_axi_if_arregion`      | 4     | out  | ARREGION attributes                          |
| `cptra_ss_mcu_lsu_m_axi_if_arqos`         | 4     | out  | ARQOS attributes                             |

#### 2.2.5 AXI Manager Interfaces (MCU IFU)

| Name                                      | Width | Dir  | Description                                  |
|-------------------------------------------|-------|------|----------------------------------------------|
| `cptra_ss_mcu_ifu_m_axi_if_w_mgr`         | —     | out  | MCU IFU AXI write manager (IW=3, UW=32)      |
| `cptra_ss_mcu_ifu_m_axi_if_r_mgr`         | —     | out  | MCU IFU AXI read manager                     |
| `cptra_ss_mcu_ifu_m_axi_if_awcache`       | 4     | out  | AWCACHE attributes                           |
| `cptra_ss_mcu_ifu_m_axi_if_awprot`        | 3     | out  | AWPROT attributes                            |
| `cptra_ss_mcu_ifu_m_axi_if_awregion`      | 4     | out  | AWREGION attributes                          |
| `cptra_ss_mcu_ifu_m_axi_if_awqos`         | 4     | out  | AWQOS attributes                             |
| `cptra_ss_mcu_ifu_m_axi_if_arcache`       | 4     | out  | ARCACHE attributes                           |
| `cptra_ss_mcu_ifu_m_axi_if_arprot`        | 3     | out  | ARPROT attributes                            |
| `cptra_ss_mcu_ifu_m_axi_if_arregion`      | 4     | out  | ARREGION attributes                          |
| `cptra_ss_mcu_ifu_m_axi_if_arqos`         | 4     | out  | ARQOS attributes                             |

#### 2.2.6 AXI Manager Interfaces (MCU System Bus)

| Name                                      | Width | Dir  | Description                                  |
|-------------------------------------------|-------|------|----------------------------------------------|
| `cptra_ss_mcu_sb_m_axi_if_w_mgr`          | —     | out  | MCU SB AXI write manager (IW=1, debug only)  |
| `cptra_ss_mcu_sb_m_axi_if_r_mgr`          | —     | out  | MCU SB AXI read manager                      |
| `cptra_ss_mcu_sb_m_axi_if_awcache`        | 4     | out  | AWCACHE attributes                           |
| `cptra_ss_mcu_sb_m_axi_if_awprot`         | 3     | out  | AWPROT attributes                            |
| `cptra_ss_mcu_sb_m_axi_if_awregion`       | 4     | out  | AWREGION attributes                          |
| `cptra_ss_mcu_sb_m_axi_if_awqos`          | 4     | out  | AWQOS attributes                             |
| `cptra_ss_mcu_sb_m_axi_if_arcache`        | 4     | out  | ARCACHE attributes                           |
| `cptra_ss_mcu_sb_m_axi_if_arprot`         | 3     | out  | ARPROT attributes                            |
| `cptra_ss_mcu_sb_m_axi_if_arregion`       | 4     | out  | ARREGION attributes                          |
| `cptra_ss_mcu_sb_m_axi_if_arqos`          | 4     | out  | ARQOS attributes                             |

#### 2.2.7 AXI Manager Interfaces (Caliptra Core DMA)

| Name                                      | Width | Dir  | Description                                  |
|-------------------------------------------|-------|------|----------------------------------------------|
| `cptra_ss_cptra_core_m_axi_if_w_mgr`      | —     | out  | Caliptra DMA AXI write manager (IW=5, UW=32) |
| `cptra_ss_cptra_core_m_axi_if_r_mgr`      | —     | out  | Caliptra DMA AXI read manager                |

#### 2.2.8 AXI Subordinate Interfaces

| Name                                      | Width | Dir  | Description                                  |
|-------------------------------------------|-------|------|----------------------------------------------|
| `cptra_ss_cptra_core_s_axi_if_w_sub`      | —     | in   | Caliptra core AXI write subordinate (IW=8)   |
| `cptra_ss_cptra_core_s_axi_if_r_sub`      | —     | in   | Caliptra core AXI read subordinate            |
| `cptra_ss_mci_s_axi_if_w_sub`             | —     | in   | MCI AXI write subordinate                     |
| `cptra_ss_mci_s_axi_if_r_sub`             | —     | in   | MCI AXI read subordinate                      |
| `cptra_ss_mcu_rom_s_axi_if_w_sub`         | —     | in   | MCU ROM AXI write sub (tie off, no write)     |
| `cptra_ss_mcu_rom_s_axi_if_r_sub`         | —     | in   | MCU ROM AXI read subordinate                  |
| `cptra_ss_i3c_s_axi_if_w_sub`             | —     | in   | I3C AXI write subordinate                     |
| `cptra_ss_i3c_s_axi_if_r_sub`             | —     | in   | I3C AXI read subordinate                      |

#### 2.2.9 LC / OTP Controller AXI Interfaces

| Name                                      | Width | Dir  | Description                                  |
|-------------------------------------------|-------|------|----------------------------------------------|
| `cptra_ss_lc_axi_wr_req_i`                | —     | in   | LC controller AXI write request               |
| `cptra_ss_lc_axi_wr_rsp_o`                | —     | out  | LC controller AXI write response              |
| `cptra_ss_lc_axi_rd_req_i`                | —     | in   | LC controller AXI read request                |
| `cptra_ss_lc_axi_rd_rsp_o`                | —     | out  | LC controller AXI read response               |
| `cptra_ss_otp_core_axi_wr_req_i`          | —     | in   | OTP controller AXI write request              |
| `cptra_ss_otp_core_axi_wr_rsp_o`          | —     | out  | OTP controller AXI write response             |
| `cptra_ss_otp_core_axi_rd_req_i`          | —     | in   | OTP controller AXI read request               |
| `cptra_ss_otp_core_axi_rd_rsp_o`          | —     | out  | OTP controller AXI read response              |

#### 2.2.10 JTAG Interfaces

| Name                                | Width | Dir  | Description                                  |
|-------------------------------------|-------|------|----------------------------------------------|
| `cptra_ss_cptra_core_jtag_tck_i`    | 1     | in   | Caliptra core JTAG clock                     |
| `cptra_ss_cptra_core_jtag_tms_i`    | 1     | in   | Caliptra core JTAG TMS                       |
| `cptra_ss_cptra_core_jtag_tdi_i`    | 1     | in   | Caliptra core JTAG TDI                       |
| `cptra_ss_cptra_core_jtag_trst_n_i` | 1     | in   | Caliptra core JTAG reset (active-low)        |
| `cptra_ss_cptra_core_jtag_tdo_o`    | 1     | out  | Caliptra core JTAG TDO                       |
| `cptra_ss_cptra_core_jtag_tdoEn_o`  | 1     | out  | Caliptra core JTAG TDO enable                |
| `cptra_ss_mcu_jtag_tck_i`           | 1     | in   | MCU JTAG clock                               |
| `cptra_ss_mcu_jtag_tms_i`           | 1     | in   | MCU JTAG TMS                                 |
| `cptra_ss_mcu_jtag_tdi_i`           | 1     | in   | MCU JTAG TDI                                 |
| `cptra_ss_mcu_jtag_trst_n_i`        | 1     | in   | MCU JTAG reset (active-low)                  |
| `cptra_ss_mcu_jtag_tdo_o`           | 1     | out  | MCU JTAG TDO                                 |
| `cptra_ss_mcu_jtag_tdoEn_o`         | 1     | out  | MCU JTAG TDO enable                          |
| `cptra_ss_lc_ctrl_jtag_i`           | —     | in   | LC controller JTAG request                   |
| `cptra_ss_lc_ctrl_jtag_o`           | —     | out  | LC controller JTAG response                  |

#### 2.2.11 I3C Interface

| Name                                  | Width | Dir  | Description                                  |
|---------------------------------------|-------|------|----------------------------------------------|
| `cptra_ss_i3c_scl_i`                  | 1     | in   | I3C SCL input                                |
| `cptra_ss_i3c_sda_i`                  | 1     | in   | I3C SDA input                                |
| `cptra_ss_i3c_scl_o`                  | 1     | out  | I3C SCL output                               |
| `cptra_ss_i3c_sda_o`                  | 1     | out  | I3C SDA output                               |
| `cptra_ss_i3c_scl_oe`                 | 1     | out  | I3C SCL output enable                        |
| `cptra_ss_i3c_sda_oe`                 | 1     | out  | I3C SDA output enable                        |
| `cptra_i3c_axi_user_id_filtering_enable_i` | 1 | in  | I3C AXI user filtering enable (active-high)  |
| `cptra_ss_sel_od_pp_o`                | 1     | out  | Open-drain/push-pull select                  |
| `cptra_ss_i3c_recovery_payload_available_o` | 1 | out | I3C recovery payload available indication   |
| `cptra_ss_i3c_recovery_payload_available_i` | 1 | in  | Caliptra core recovery payload available     |
| `cptra_ss_i3c_recovery_image_activated_o`   | 1 | out | I3C recovery image activated indication     |
| `cptra_ss_i3c_recovery_image_activated_i`   | 1 | in  | Caliptra core recovery image activated      |

#### 2.2.12 Caliptra Core Interface Signals

| Name                                      | Width      | Dir  | Description                              |
|-------------------------------------------|------------|------|------------------------------------------|
| `cptra_ss_cptra_obf_key_i`                | 256        | in   | Obfuscation key input                    |
| `cptra_ss_cptra_csr_hmac_key_i`           | CLP_CSR_HMAC_KEY_DWORDS | in | CSR HMAC key input          |
| `cptra_ss_raw_unlock_token_hashed_i`      | 128        | in   | Hashed RAW unlock token                  |
| `cptra_ss_cptra_generic_fw_exec_ctrl_o`   | 125        | out  | Generic FW execution control output      |
| `cptra_ss_cptra_generic_fw_exec_ctrl_2_mcu_o` | 1     | out  | FW exec control bit 2 from Caliptra     |
| `cptra_ss_cptra_generic_fw_exec_ctrl_2_mcu_i` | 1     | in   | FW exec control bit 2 for MCU           |
| `cptra_ss_cptra_generic_input_wires_i`    | 64         | in   | Generic input wires for Caliptra core    |
| `cptra_ss_cptra_core_scan_mode_i`         | 1          | in   | Scan mode input                          |
| `cptra_ss_cptra_core_bootfsm_bp_i`        | 1          | in   | Boot FSM breakpoint input                |
| `cptra_ss_cptra_core_etrng_req_o`         | 1          | out  | External TRNG request                    |
| `cptra_ss_cptra_core_itrng_data_i`        | 4          | in   | Internal TRNG data                       |
| `cptra_ss_cptra_core_itrng_valid_i`       | 1          | in   | Internal TRNG valid                      |

#### 2.2.13 Memory Export Interfaces

| Name                                      | Width | Dir  | Description                              |
|-------------------------------------------|-------|------|------------------------------------------|
| `cptra_ss_cptra_core_el2_mem_export`      | —     | —    | Caliptra core EL2 memory export          |
| `mcu_rom_mem_export_if`                   | —     | —    | MCU ROM memory export (read-only)        |
| `cptra_ss_cptra_core_mbox_sram_cs_o`      | 1     | out  | Mailbox SRAM chip select                 |
| `cptra_ss_cptra_core_mbox_sram_we_o`      | 1     | out  | Mailbox SRAM write enable                |
| `cptra_ss_cptra_core_mbox_sram_addr_o`    | CPTRA_MBOX_ADDR_W | out | Mailbox SRAM address                  |
| `cptra_ss_cptra_core_mbox_sram_wdata_o`   | CPTRA_MBOX_DATA_AND_ECC_W | out | Mailbox SRAM write data     |
| `cptra_ss_cptra_core_mbox_sram_rdata_i`   | CPTRA_MBOX_DATA_AND_ECC_W | in  | Mailbox SRAM read data      |
| `cptra_ss_cptra_core_imem_cs_o`           | 1     | out  | Instruction memory chip select           |
| `cptra_ss_cptra_core_imem_addr_o`         | CALIPTRA_IMEM_ADDR_WIDTH | out | Instruction memory address          |
| `cptra_ss_cptra_core_imem_rdata_i`        | CALIPTRA_IMEM_DATA_WIDTH | in  | Instruction memory read data         |
| `cptra_ss_mci_mcu_sram_req_if`            | —     | —    | MCI MCU SRAM request interface           |
| `cptra_ss_mci_mbox0_sram_req_if`          | —     | —    | MCI mailbox 0 SRAM request interface     |
| `cptra_ss_mci_mbox1_sram_req_if`          | —     | —    | MCI mailbox 1 SRAM request interface     |
| `cptra_ss_mcu0_el2_mem_export`            | —     | —    | MCU0 EL2 memory export interface         |

#### 2.2.14 Lifecycle & Debug Signals

| Name                                      | Width | Dir  | Description                              |
|-------------------------------------------|-------|------|------------------------------------------|
| `cptra_ss_debug_intent_i`                 | 1     | in   | Physical presence debug intent pin       |
| `cptra_ss_mcu_no_rom_config_i`            | 1     | in   | No ROM configuration mode                |
| `cptra_ss_mci_boot_seq_brkpoint_i`        | 1     | in   | MCI boot sequence breakpoint             |
| `cptra_ss_lc_Allow_RMA_or_SCRAP_on_PPD_i` | 1     | in   | Allow RMA/SCRAP on PPD                   |
| `cptra_ss_FIPS_ZEROIZATION_PPD_i`         | 1     | in   | FIPS zeroization request with PPD        |
| `cptra_ss_lc_sec_volatile_raw_unlock_en_i`| 1     | in   | Enables volatile TEST_UNLOCKED0          |
| `cptra_ss_dbg_manuf_enable_o`             | 1     | out  | Manufacturing debug unlock indication    |
| `cptra_ss_cptra_core_soc_prod_dbg_unlock_level_o` | 64 | out | Production debug unlock level (1-hot) |
| `caliptra_ss_life_cycle_steady_state_o`   | —     | out  | LC state broadcast from fuse macro       |
| `caliptra_ss_otp_state_valid_o`           | 1     | out  | Valid indicator for broadcast LC state   |
| `caliptra_ss_volatile_raw_unlock_success_o` | 1   | out  | Volatile unlock success indication       |
| `cptra_ss_lc_escalate_en_o`               | —     | out  | LCC escalation enable                    |
| `cptra_ss_lc_check_byp_en_o`              | —     | out  | LCC external clock bypass enable         |

#### 2.2.15 Error, Interrupt, and Misc Signals

| Name                                      | Width | Dir  | Description                              |
|-------------------------------------------|-------|------|------------------------------------------|
| `cptra_ss_all_error_fatal_o`              | 1     | out  | CSS aggregate fatal error                |
| `cptra_ss_all_error_non_fatal_o`          | 1     | out  | CSS aggregate non-fatal error            |
| `cptra_error_fatal`                       | 1     | out  | Caliptra core fatal error                |
| `cptra_error_non_fatal`                   | 1     | out  | Caliptra core non-fatal error            |
| `cptra_ss_mcu_halt_status_o`              | 1     | out  | MCU halt status                          |
| `cptra_ss_mcu_halt_status_i`              | 1     | in   | MCU halt status input for MCI            |
| `cptra_ss_mcu_halt_ack_o`                 | 1     | out  | MCU halt acknowledge                     |
| `cptra_ss_mcu_halt_ack_i`                 | 1     | in   | MCU halt ack input for MCI               |
| `cptra_ss_mcu_halt_req_o`                 | 1     | out  | MCU halt request                         |
| `cptra_ss_soc_mcu_mbox0_data_avail`       | 1     | out  | MCU Mailbox0 data available              |
| `cptra_ss_soc_mcu_mbox1_data_avail`       | 1     | out  | MCU Mailbox1 data available              |
| `cptra_ss_mci_generic_input_wires_i`      | 64    | in   | Generic input wires for MCI              |
| `cptra_ss_mci_generic_output_wires_o`     | 64    | out  | Generic output wires for MCI             |
| `cptra_ss_mcu_ext_int`                    | —     | —    | MCU external interrupts [255:3]           |

#### 2.2.16 Fuse Macro Interface

| Name                                      | Width      | Dir  | Description                              |
|-------------------------------------------|------------|------|------------------------------------------|
| `cptra_ss_fuse_macro_inputs_o`            | —          | out  | Fuse macro command interface outputs     |
| `cptra_ss_fuse_macro_outputs_i`           | —          | in   | Fuse macro response interface inputs     |

### 2.3 Parameters & Defines — RTL-Verified

> **Source**: `caliptra_ss_top.sv` parameter list + `caliptra_ss_includes.svh`

| Name                           | Default         | Description                                           | Configurable By |
|--------------------------------|-----------------|-------------------------------------------------------|-----------------|
| `CPTRA_SS_ROM_SIZE_KB`         | 256             | MCU ROM size in KiB                                    | Integrator      |
| `CPTRA_SS_ROM_DATA_W`          | 64              | MCU ROM data width (bits)                              | No              |
| `CPTRA_SS_ROM_DEPTH`           | 32768           | = ROM_SIZE_KB*1024 / (DATA_W/8)                        | Derived         |
| `CPTRA_SS_ROM_AXI_ADDR_W`      | 18              | = $clog2(ROM_SIZE_KB*1024)                             | Derived         |
| `CPTRA_SS_ROM_MEM_ADDR_W`      | 15              | = $clog2(ROM_DEPTH)                                    | Derived         |
| `MCU_MBOX0_SIZE_KB`            | 4               | Mailbox 0 SRAM size in KiB (0=not instantiated)        | Integrator      |
| `MCU_MBOX1_SIZE_KB`            | 4               | Mailbox 1 SRAM size in KiB (0=not instantiated)        | Integrator      |
| `MCU_SRAM_SIZE_KB`             | 512             | MCU shared SRAM size in KiB (4–2048)                   | Integrator      |
| `MIN_MCU_RST_COUNTER_WIDTH`    | 4               | MCU reset counter width (controls min reset duration)  | Integrator      |
| `MCU_MBOX0_VALID_AXI_USER`     | {5×32'h...}     | 5 trusted AXI user IDs for mailbox 0                   | Build time      |
| `MCU_MBOX1_VALID_AXI_USER`     | {5×32'h...}     | 5 trusted AXI user IDs for mailbox 1                   | Build time      |
| `SET_MCU_MBOX0_AXI_USER_INTEG` | {5×1'b0}        | AXI user integrity enables for mailbox 0               | Build time      |
| `SET_MCU_MBOX1_AXI_USER_INTEG` | {5×1'b0}        | AXI user integrity enables for mailbox 1               | Build time      |
| `CALIPTRA_MODE_SUBSYSTEM`      | (macro)         | **Must be defined** for all builds                     | Build flag      |
| `CLP_CSR_HMAC_KEY_DWORDS`      | (from Caliptra) | HMAC key width in DWORDs                               | Caliptra        |
| `CPTRA_MBOX_ADDR_W`            | (from Caliptra) | Caliptra mailbox address width                         | Caliptra        |
| `CPTRA_MBOX_DATA_AND_ECC_W`    | (from Caliptra) | Caliptra mailbox data+ECC width                        | Caliptra        |
| `CALIPTRA_IMEM_ADDR_WIDTH`     | (from Caliptra) | Caliptra IMEM address width                            | Caliptra        |
| `CALIPTRA_IMEM_DATA_WIDTH`     | (from Caliptra) | Caliptra IMEM data width                               | Caliptra        |
| `AXI_USER_WIDTH`               | 32 (from i3c)   | AXI user width for all interfaces                      | No              |
| `AXI_DATA_WIDTH`               | 32 (from i3c)   | AXI data width                                         | No              |
| `AXI_ADDR_WIDTH`               | (from i3c)      | AXI address width                                      | No              |
| `AXI_ID_WIDTH`                 | 8 (from i3c)    | AXI ID width for subordinate interfaces                | No              |

#### MCU VeeR-EL2 Core Configuration (from `css_mcu0_el2_param.vh`)

| Name                    | Value  | Description                          |
|-------------------------|--------|--------------------------------------|
| DCCM size               | 16 KiB | Data Closely Coupled Memory          |
| I-Cache depth           | 16 KiB | Instruction Cache                    |
| ICCM                    | Disabled | No instruction closely coupled mem |
| PIC_TOTAL_INT           | 255    | External interrupt vectors           |
| IFU_BUS_TAG             | 3      | IFU AXI ID width (IDs 0–7)           |
| LSU_BUS_TAG             | 3      | LSU AXI ID width (IDs 0–7)           |
| SB_BUS_TAG              | 1      | System Bus AXI ID width (IDs 0–1)    |
| CPTRA_AXI_DMA_ID_WIDTH  | 5      | Caliptra DMA AXI ID (tied to 0)      |

#### MCI Internal Constants (from `mci_pkg.sv`)

| Name                             | Value | Description                              |
|----------------------------------|-------|------------------------------------------|
| MCU_MBOX_DATA_W                  | 32    | Mailbox data width (not configurable)    |
| MCU_MBOX_ECC_DATA_W              | 7     | Mailbox ECC width (not configurable)     |
| MCU_DEF_MBOX_VALID_AXI_USER      | 0xFFFF_FFFF | Default valid AXI user              |
| MCI_MCU_UPDATE_RESET_CYCLES      | 10    | Reset cycles for hitless update          |
| MCI_WDT_TIMEOUT_PERIOD_NUM_DWORDS| 2     | WDT period is 64 bits                    |

### 2.4 Straps

All straps must be stable before `mci_rst_b` is deasserted.

| Name                                                    | Width | Type                    | Description                                    |
|---------------------------------------------------------|-------|-------------------------|------------------------------------------------|
| `cptra_ss_strap_mcu_lsu_axi_user_i`                     | 32    | Non-configurable Direct | MCU LSU AXI user ID                            |
| `cptra_ss_strap_mcu_ifu_axi_user_i`                     | 32    | Non-configurable Direct | MCU IFU AXI user ID                            |
| `cptra_ss_strap_mcu_sram_config_axi_user_i`             | 32    | Non-configurable Direct | MCU SRAM config agent (typically Caliptra)      |
| `cptra_ss_strap_mci_soc_config_axi_user_i`              | 32    | Non-configurable Direct | MCI SOC Config User (MSCU)                     |
| `cptra_ss_strap_caliptra_dma_axi_user_i`                | 32    | Non-configurable Direct | Caliptra DMA AXI user ID                       |
| `cptra_ss_strap_mcu_reset_vector_i`                     | 32    | Configurable Sampled    | MCU reset vector (sampled per warm boot)       |
| `cptra_ss_strap_caliptra_base_addr_i`                   | 64    | Non-configurable Direct | Caliptra base address                          |
| `cptra_ss_strap_mci_base_addr_i`                        | 64    | Non-configurable Direct | MCI base address                               |
| `cptra_ss_strap_recovery_ifc_base_addr_i`               | 64    | Non-configurable Direct | Recovery interface base address                |
| `cptra_ss_strap_external_staging_area_base_addr_i`      | 64    | Non-configurable Direct | External staging area base address             |
| `cptra_ss_strap_otp_fc_base_addr_i`                     | 64    | Non-configurable Direct | OTP FC base address                            |
| `cptra_ss_strap_uds_seed_base_addr_i`                   | 64    | Non-configurable Direct | UDS seed base address                          |
| `cptra_ss_strap_prod_debug_unlock_auth_pk_hash_reg_bank_offset_i` | 32 | Non-configurable Direct | PK hash reg bank offset           |
| `cptra_ss_strap_num_of_prod_debug_unlock_auth_pk_hashes_i` | 32 | Non-configurable Direct | Number of PK hashes (default 8)               |
| `cptra_ss_strap_generic_0_i`                            | 32    | Non-configurable Direct | FC status register pointer                     |
| `cptra_ss_strap_generic_1_i`                            | 32    | Non-configurable Direct | FC command register pointer                    |
| `cptra_ss_strap_generic_2_i`                            | 32    | Non-configurable Direct | Generic strap 2                                |
| `cptra_ss_strap_generic_3_i`                            | 32    | Non-configurable Direct | Generic strap 3                                |
| `cptra_ss_strap_key_release_key_size_i`                 | 16    | Non-configurable Direct | OCP L.O.C.K. MEK byte size (expected 0x40)     |
| `cptra_ss_strap_key_release_base_addr_i`                | 64    | Non-configurable Direct | OCP L.O.C.K. MEK release base address          |
| `cptra_ss_strap_ocp_lock_en_i`                          | 1     | Non-configurable Direct | OCP L.O.C.K. enable (constant 0 or 1)          |
| `cptra_ss_debug_intent_i`                               | 1     | Non-configurable Sampled | Debug intent physical presence                |

---

## 3. Feature Operation

### 3.1 Feature A: CSS Boot Sequence (CSS-BootFSM)

The Boot Sequencer FSM in MCI manages the orderly boot process after power application.

- **Trigger**: Power good assertion + reset deassertion from SoC
- **Datapath**:
  1. SoC asserts `cptra_ss_pwrgood_i` and deasserts `cptra_ss_rst_b_i`
  2. CSS-BootFSM samples all MCI straps, drives outputs to reset defaults
  3. CSS-BootFSM performs FC initialization handshake
  4. CSS-BootFSM performs LCC initialization handshake
  5. If `mcu_no_rom_config` is not set → deassert MCU reset → MCU ROM executes
  6. MCU ROM writes Caliptra fuses, owner PK hash, fuse_write_done
  7. MCU ROM brings Caliptra out of reset (CPTRA_BOOT_GO)
  8. Caliptra BootFSM reads secret fuses, sets ready_for_fuses
  9. MCU ROM polls ready_for_fuses, reads FC SW partition fuses
  10. Caliptra authenticates/loads MCU FW into MCU SRAM, sets FW_EXEC_CTL[2]
  11. FW_EXEC_CTL[2] triggers MCU reset request to MCI
  12. CSS-BootFSM does halt req/ack handshake with MCU
  13. MCU reset asserted, MCU reboots from SRAM
- **Control**: CSS-BootFSM state machine
- **Output**: MCU executing authenticated firmware from SRAM, Caliptra operational

### 3.2 Feature B: I3C Streaming Boot (Recovery)

Firmware recovery via I3C target interface using OCP streaming boot protocol.

- **Trigger**: Recovery Agent (RA) sends I3C write to INDIRECT_FIFO_DATA register
- **Datapath**:
  1. RA writes up to 256B data + 4B header to I3C target
  2. I3C target asserts `payload_available` after successful write + PEC verification
  3. Caliptra DMA assist waits for `payload_available`, reads block_size bytes
  4. `payload_available` deasserted after DMA read
  5. RA writes to RECOVERY_CTRL → I3C asserts `image_activated`
  6. Caliptra ROM waits for `image_activated`, processes image
  7. Caliptra ROM clears byte 2 of RECOVERY_CTRL via DMA → `image_activated` deasserted
- **Control**: Caliptra DMA assist FSM (block_size mode)
- **Output**: Authenticated firmware image loaded, or error reported

### 3.3 Feature C: AXI Streaming Boot (Recovery)

Alternative recovery path via AXI bus, bypassing I3C communication logic.

- **Trigger**: REC_INTF_CFG CSR set to AXI bypass mode
- **Datapath**: Direct AXI access to Streaming Boot Handler registers and Indirect FIFO, reusing I3C core's TTI queues and recovery executor logic
- **Control**: Streaming Boot Handler in bypass mode
- **Output**: Same as I3C streaming boot — authenticated firmware image

### 3.4 Feature D: AXI DMA Operations

Caliptra SOC_IFC DMA engine for autonomous AXI transfers.

- **Trigger**: Caliptra FW programs DMA descriptor registers and sets GO bit
- **Datapath**: Read/Write routes through internal 512-byte FIFO:
  - **Read Routes**: AXI read → FIFO, AHB (dataout register), Mailbox, or AXI write passthrough
  - **Write Routes**: AHB (datain register) → FIFO, Mailbox → FIFO, or AXI read → FIFO → AXI write
  - **AES Mode**: AXI read → FIFO → AES encrypt/decrypt → FIFO → AXI write
- **Control**: DMA control state machine
- **Constraints**:
  - Max transfer: 1 MiB
  - Max outstanding: 2 reads + 2 writes (1+1 with block_size)
  - Burst: INCR max AxLEN=63 (256B), FIXED max AxLEN=15
  - No narrow transfers; AxSIZE always = data width (4 bytes)
  - WSTRB always all 1s
  - All AxID = 0 (in-order required)
  - Must not cross 4KiB boundaries

### 3.5 Feature E: Lifecycle State Management

Hardware-only lifecycle state machine with forward-only transitions.

- **Trigger**: TAP token injection, LCC state transitions
- **Datapath**:
  - RAW → TEST_UNLOCKED0 (global RAW_UNLOCK token)
  - TEST_UNLOCKED{N} ↔ TEST_LOCKED{N} (TEST_UNLOCKED token)
  - TEST_UNLOCKED → MANUF (MANUF_TOKEN)
  - MANUF → PROD (PROD_TOKEN)
  - PROD/MANUF → RMA (RMA_UNLOCK token, requires PPD pin)
  - Any → SCRAP (requires PPD pin)
  - MANUF/PROD/PROD_END → debug modes (caliptra-controlled)
- **Control**: LCC state machine with token hashing (cSHAKE128)
- **Output**: DFT_EN, SOC_DFT_EN, SOC_HW_DEBUG_EN decoder signals

### 3.6 Feature F: Production Debug Unlock

Post-quantum resilient debug unlock using hybrid ECC + MLDSA authentication.

- **Trigger**: DEBUG_INTENT_STRAP + PROD_DEBUG_UNLOCK_REQ + CPTRA_BOOT_GO
- **Datapath**:
  1. Caliptra HW erases secrets (UDS, Field Entropy)
  2. ROM sets TAP_MAILBOX_AVAILABLE + PROD_DBG_UNLOCK_IN_PROGRESS
  3. Platform sends AUTH_DEBUG_UNLOCK_REQ (unlock level)
  4. ROM sends AUTH_DEBUG_UNLOCK_CHALLENGE (device ID + nonce)
  5. Platform signs challenge, sends AUTH_DEBUG_UNLOCK_TOKEN (ECC + MLDSA keys + signatures)
  6. ROM verifies PK hashes against fuse values, authenticates signatures
  7. On success: sets PROD_DBG_UNLOCK_SUCCESS, writes debug level to SOC_DEBUG_UNLOCK_LEVEL
- **Control**: Caliptra ROM challenge-response FSM
- **Output**: Debug level signals (up to 8 levels, one-hot encoded)

### 3.7 Feature G: Fuse Controller Operations

OTP fuse programming, reading, and integrity management.

- **Trigger**: Direct Access Interface (DAI) commands from Caliptra or MCU
- **Datapath**:
  1. Write address to DIRECT_ACCESS_ADDRESS
  2. Write data to WDATA_0/WDATA_1 (for writes)
  3. Write command to DIRECT_ACCESS_CMD (read/write/digest/zeroize)
  4. Poll STATUS.DAI_IDLE for completion
  5. Read RDATA_0/RDATA_1 for read results
- **Control**: OTP controller DAI FSM
- **Security**: Atomic provisioning enforced (same AXI USER for entire sequence), secret partitions accessible only by Caliptra Core, scan path exclusions for secret partitions

### 3.8 Feature H: MCU Mailbox Communication

Secure restricted communication between external SoC entities and MCU.

- **Trigger**: Trusted AXI user reads LOCK register (read-set, returns 0 on acquire)
- **Datapath**:
  1. Requester obtains lock
  2. Requester writes command/data to mailbox SRAM
  3. Requester asserts EXECUTE register → interrupt to MCU
  4. MCU reads mailbox, optionally adds Target User
  5. Target User processes, sets TARGET_DONE → interrupt to MCU
  6. MCU updates CMD_STATUS, releases lock
  7. SRAM zeroed from 0 to max DLEN set during lock period
- **Control**: Mailbox FSM with lock, execute, target user management
- **Output**: Secure data exchange with automatic SRAM zeroization

### 3.9 Feature I: MCU Hitless Firmware Update

Update MCU firmware without service interruption.

- **Trigger**: FW_EXEC_CTL[2] signal from Caliptra
- **Datapath**:
  1. Caliptra loads new MCU FW image into MCU SRAM
  2. Caliptra sets FW_EXEC_CTL[2] → interrupt to MCU
  3. MCU requests reset via RESET_REQUEST
  4. MCI performs halt req/ack handshake with MCU
  5. MCU reset asserted with RESET_REASON = FW_BOOT_UPD_RESET or FW_HITLESS_UPD_RESET
  6. MCU reboots from updated SRAM image
- **Control**: MCI boot FSM + MCU firmware handshake
- **Output**: Updated MCU firmware running without full SoC reset

### 3.10 Feature J: Watchdog Timer

Dual-mode watchdog for system reliability.

- **Trigger**: Configuration by MCU via MCI CSRs
- **Datapath**:
  - **Cascade Mode**: Timer 1 timeout → error interrupt + start Timer 2 → Timer 2 timeout → NMI + HW_ERROR_FATAL
  - **Independent Mode**: Timer 1/2 independently assert error interrupts on timeout; NMI never asserted
- **Control**: WDT FSM
- **Output**: Error interrupt, NMI, HW_ERROR_FATAL

### 3.11 Feature K: Error Aggregation — RTL-Verified

> **Source**: `caliptra_ss_top.sv` lines 584–596 — exact bit assignments verified

Centralized error collection from all subsystem components. Error signals are aggregated into two 32-bit buses (`agg_error_fatal[31:0]` and `agg_error_non_fatal[31:0]`) inside `caliptra_ss_top`, then routed to MCI for masking and output.

- **Trigger**: Error signals from Caliptra, MCU, LCC, FC, I3C, internal MCI
- **Datapath**: Error aggregation assignments (exact from RTL):

```
// Fatal aggregation (from caliptra_ss_top.sv):
agg_error_fatal[5:0]   = {5'b0, cptra_error_fatal};           // [5] Caliptra core fatal
agg_error_fatal[11:6]  = {5'b0, mcu_dccm_ecc_double_error};   // [6] MCU DCCM double-bit ECC
agg_error_fatal[17:12] = {6-NumAlerts{1'b0}, lc_alerts_o};    // [14:12] LCC alerts (3 bits)
agg_error_fatal[23:18] = {fc_intr_otp_error, fc_alerts};       // [23:18] FC: OTP error + 5 alerts
agg_error_fatal[29:24] = {4'b0, i3c_peripheral_reset, i3c_escalated_reset}; // [25:24] I3C resets
agg_error_fatal[31:30] = 2'b0;                                  // [31:30] Spare

// Non-Fatal aggregation:
agg_error_non_fatal[5:0]   = {5'b0, cptra_error_non_fatal};        // [5] Caliptra non-fatal
agg_error_non_fatal[11:6]  = {5'b0, mcu_dccm_ecc_single_error};   // [6] MCU DCCM single-bit ECC
agg_error_non_fatal[17:12] = {6-NumAlerts{1'b0}, lc_alerts_o};    // [14:12] LCC alerts (shared)
agg_error_non_fatal[23:18] = {fc_intr_otp_error, fc_alerts};       // [23:18] FC (shared)
agg_error_non_fatal[29:24] = {4'b0, i3c_peripheral_reset, i3c_escalated_reset}; // [25:24] I3C
agg_error_non_fatal[31:30] = 2'b0;                                  // [31:30] Spare
```

| **Error Register Bits** | **Component**         | **Default Fatal** | **Default Non-Fatal** | **Description**          |
| :---------              | :---------            | :---------         | :---------             | :---------                |
| Aggregate [5:0]         | Caliptra core         | bit[5]: cptra_error_fatal | bit[5]: cptra_error_non_fatal | Caliptra core errors |
| Aggregate [11:6]        | MCU                   | bit[6]: DCCM double ECC | bit[6]: DCCM single ECC | MCU DCCM ECC errors    |
| Aggregate [17:12]       | Life cycle controller | lc_alerts_o (3 bits) | lc_alerts_o (same)     | LCC alerts               |
| Aggregate [23:18]       | OTP Fuse controller   | fc_intr_otp_error + fc_alerts (6 bits) | same | FC errors + alerts |
| Aggregate [29:24]       | I3C                   | bit[25]: peripheral_reset, bit[24]: escalated_reset | same | I3C reset pins |
| Aggregate [31:30]       | Spare                 | None               | None                    | Integrator use            |

- **Control**: Configurable severity masking per component in MCI registers
- **Output**: `cptra_ss_all_error_fatal_o`, `cptra_ss_all_error_non_fatal_o`

---

### 3.12 Control FSM: CSS-BootFSM (MCI Boot Sequencer) — RTL-Verified

> **Source**: `mci_pkg.sv` enum `mci_boot_fsm_state_e`

| Encoding | State                    | Next State              | Condition                           | Output Actions                                      |
|----------|--------------------------|-------------------------|-------------------------------------|-----------------------------------------------------|
| 4'h0     | BOOT_IDLE                | BOOT_OTP_FC             | pwrgood=1 && rst_b deasserted       | Drive reset defaults                                |
| 4'h1     | BOOT_OTP_FC              | BOOT_LCC                | FC init complete (pwr_otp done)     | FC operational, OTP initialized                     |
| 4'h2     | BOOT_LCC                 | BOOT_BREAKPOINT_CHECK   | LCC init complete                   | LCC operational, LC state decoded                   |
| 4'h3     | BOOT_BREAKPOINT_CHECK    | BOOT_BREAKPOINT         | mci_boot_seq_brkpoint=1             | Enter breakpoint for debug config                   |
| 4'h3     | BOOT_BREAKPOINT_CHECK    | BOOT_MCU                | mci_boot_seq_brkpoint=0, no_rom=0   | Skip breakpoint, proceed to MCU boot                |
| 4'h3     | BOOT_BREAKPOINT_CHECK    | BOOT_WAIT_CPTRA_GO      | mci_boot_seq_brkpoint=0, no_rom=1   | Skip breakpoint, wait for SOC CPTRA_BOOT_GO         |
| 4'h4     | BOOT_BREAKPOINT          | BOOT_MCU                | MCI_BOOTFSM_GO=1, no_rom=0          | Continue to MCU boot after debug config             |
| 4'h4     | BOOT_BREAKPOINT          | BOOT_WAIT_CPTRA_GO      | MCI_BOOTFSM_GO=1, no_rom=1          | Continue to wait-for-CPTRA after debug config       |
| 4'h5     | BOOT_MCU                 | BOOT_WAIT_CPTRA_GO      | MCU reset deasserted                | MCU ROM starts executing                            |
| 4'h6     | BOOT_WAIT_CPTRA_GO       | BOOT_CPTRA              | MCU writes CPTRA_BOOT_GO            | Caliptra reset deasserted                           |
| 4'h7     | BOOT_CPTRA               | BOOT_WAIT_MCU_RST_REQ   | Caliptra boot FSM running           | Normal — both cores running, wait for MCU reset req |
| 4'h8     | BOOT_WAIT_MCU_RST_REQ    | BOOT_HALT_MCU           | MCU RESET_REQUEST=1                 | Initiate MCU halt for FW update                     |
| 4'h9     | BOOT_HALT_MCU            | BOOT_WAIT_MCU_HALTED    | halt_req asserted                   | MCU halt request sent                               |
| 4'ha     | BOOT_WAIT_MCU_HALTED     | BOOT_RST_MCU            | halt_ack received                   | MCU confirmed halted                                |
| 4'hb     | BOOT_RST_MCU             | BOOT_MCU                | Reset counter expired               | MCU reset with new FW image, re-enter BOOT_MCU      |
| 4'hf     | BOOT_UNKNOWN             | —                       | Illegal state                       | Error condition                                      |

### 3.12b Control FSM: MCI LCC State Translator — RTL-Verified

> **Source**: `mci_pkg.sv` enum `mci_state_translator_fsm_state_e`

| Encoding | State                      | LCC Condition                        | Caliptra Core Security State         |
|----------|----------------------------|--------------------------------------|--------------------------------------|
| 3'd0     | TRANSLATOR_RESET           | In reset                             | Reset                                |
| 3'd1     | TRANSLATOR_IDLE            | Waiting for LC init                  | Idle                                 |
| 3'd2     | TRANSLATOR_NON_DEBUG       | RAW/TEST_LOCKED/SCRAP/INVALID        | Prod Non-Debug                       |
| 3'd3     | TRANSLATOR_UNPROV_DEBUG    | TEST_UNLOCKED                        | Unprovisioned Debug                  |
| 3'd4     | TRANSLATOR_MANUF_NON_DEBUG | MANUF (no Caliptra debug grant)      | Manuf Non-Debug                      |
| 3'd5     | TRANSLATOR_MANUF_DEBUG     | MANUF + Caliptra debug grant         | Manuf Debug                          |
| 3'd6     | TRANSLATOR_PROD_NON_DEBUG  | PROD/PROD_END (no debug grant)       | Prod Non-Debug                       |
| 3'd7     | TRANSLATOR_PROD_DEBUG      | PROD/PROD_END + debug grant OR RMA   | Prod Debug                           |

---

### 3.13 Control FSM: Lifecycle Controller States

| LCC State        | Encoding | DFT_EN | SOC_DFT_EN       | SOC_HW_DEBUG_EN  | Caliptra Core Security State |
|------------------|----------|--------|-------------------|-------------------|------------------------------|
| RAW              | FUSE     | Low    | Low               | Low               | Prod Non-Debug               |
| TEST_LOCKED{N}   | FUSE     | Low    | Low               | Low               | Prod Non-Debug               |
| TEST_UNLOCKED{N} | FUSE     | High   | High              | High              | Unprovisioned Debug          |
| MANUF            | FUSE     | Low    | Token-conditioned | High              | Manuf Non-Debug              |
| MANUF*           | FUSE     | Low    | High              | High              | Manuf Debug                  |
| PROD             | FUSE     | Low    | Token-conditioned | Token-conditioned | Prod Non-Debug               |
| PROD*            | FUSE     | Low    | High              | High              | Prod Debug                   |
| PROD_END         | FUSE     | Low    | Token-conditioned | Token-conditioned | Prod Non-Debug               |
| PROD_END*        | FUSE     | Low    | High              | High              | Prod Debug                   |
| RMA              | FUSE     | High   | High              | High              | Prod Debug (RMA)             |
| SCRAP            | FUSE     | Low    | Low               | Low               | Prod Non-Debug               |
| INVALID          | FUSE     | Low    | Low               | Low               | Prod Non-Debug               |

\* = Caliptra SS extension: debug mode granted by Caliptra ROM despite LCC being in MANUF/PROD/PROD_END state.

---

## 4. Registers (FAM — Functional Address Map)

### 4.1 Subsystem Address Map (Reference)

| Start Address    | End Address      | Addr Width | Subordinate     | Name                    |
|------------------|------------------|------------|-----------------|-------------------------|
| 0x1000_0000      | 0x1FFF_FFFF      | —          | 0               | Reserved                |
| 0x2000_4000      | 0x2000_4FFF      | 12         | I3C Core        | I3C Core                |
| 0x7000_0000      | 0x7000_01FF      | 9          | Fuse Controller  | Fuse Controller         |
| 0x7000_0400      | 0x7000_05FF      | 9          | Life Cycle Ctrl  | Life Cycle Controller   |
| 0x8000_0000      | 0x80FF_FFFF      | 24         | MCU ROM         | MCU ROM (read-only)     |
| 0xA002_0000      | 0xA003_FFFF      | 17         | SoC IFC         | Caliptra Core AXI Sub   |
| 0x2100_0000      | 0x21DF_FFFF      | 24         | MCI             | MCI (CSR + SRAM + MBOX) |

**Note**: Addresses are reference only. Integrator must configure address map. MCU DCCM (0x5000_0000–0x5FFF_FFFF) and PIC (0x6000_0000–0x6FFF_FFFF) are internal to MCU and must not be assigned to external subordinates.

### 4.2 MCI Register Bank — RTL-Verified Addresses

> **Source**: `soc_address_map_defines.svh` — all offsets are absolute SoC addresses.  
> MCI CSR base: `0x2100_0000`

#### MCI Capabilities & Configuration

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_0000  | HW_CAPABILITIES                   | 32    | RO     | Hardware capabilities                    |
| 0x2100_0004  | FW_CAPABILITIES                   | 32    | RW     | Firmware capabilities                    |
| 0x2100_0008  | CAP_LOCK                          | 32    | RW     | Capabilities lock register               |
| 0x2100_000C  | HW_REV_ID                         | 32    | RO     | Hardware revision ID                     |
| 0x2100_0010  | FW_REV_ID_0                       | 32    | RW     | Firmware revision ID low                 |
| 0x2100_0014  | FW_REV_ID_1                       | 32    | RW     | Firmware revision ID high                |
| 0x2100_0018  | HW_CONFIG0                        | 32    | RO     | Hardware configuration 0                 |
| 0x2100_001C  | HW_CONFIG1                        | 32    | RO     | Hardware configuration 1                 |
| 0x2100_0020  | MCU_IFU_AXI_USER                  | 32    | RO     | Sampled IFU AXI user strap               |
| 0x2100_0024  | MCU_LSU_AXI_USER                  | 32    | RO     | Sampled LSU AXI user strap               |
| 0x2100_0028  | MCU_SRAM_CONFIG_AXI_USER          | 32    | RO     | Sampled SRAM config AXI user strap       |
| 0x2100_002C  | MCI_SOC_CONFIG_AXI_USER           | 32    | RO     | Sampled SOC config AXI user strap        |

#### MCI Flow Status & Boot Control

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_0030  | FW_FLOW_STATUS                    | 32    | RW     | Firmware flow status                     |
| 0x2100_0034  | HW_FLOW_STATUS                    | 32    | RO     | Hardware flow status (ready bits)        |
| 0x2100_0038  | RESET_REASON                      | 32    | RW     | Reset reason (WARM/FW_BOOT_UPD/FW_HITLESS_UPD) |
| 0x2100_003C  | RESET_STATUS                      | 32    | RO     | Current reset status                     |
| 0x2100_0040  | SECURITY_STATE                    | 32    | RO     | Security state from LCC translator       |

#### MCI Error Registers

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_0050  | HW_ERROR_FATAL                    | 32    | RO     | Hardware fatal errors                    |
| 0x2100_0054  | AGG_ERROR_FATAL                   | 32    | RW     | Aggregated fatal errors (maskable)       |
| 0x2100_0058  | HW_ERROR_NON_FATAL                | 32    | RO     | Hardware non-fatal errors                |
| 0x2100_005C  | AGG_ERROR_NON_FATAL               | 32    | RW     | Aggregated non-fatal errors (maskable)   |
| 0x2100_0060  | FW_ERROR_FATAL                    | 32    | RW     | Firmware fatal error code                |
| 0x2100_0064  | FW_ERROR_NON_FATAL                | 32    | RW     | Firmware non-fatal error code            |
| 0x2100_0068  | HW_ERROR_ENC                      | 32    | RO     | Hardware error encoding                  |
| 0x2100_006C  | FW_ERROR_ENC                      | 32    | RO     | Firmware error encoding                  |
| 0x2100_0070–0x2100_008C | FW_EXTENDED_ERROR_INFO_[0-7] | 32 | RO  | Extended error information registers     |
| 0x2100_0090  | INTERNAL_HW_ERROR_FATAL_MASK      | 32    | RW     | Internal fatal error mask                |
| 0x2100_0094  | INTERNAL_HW_ERROR_NON_FATAL_MASK  | 32    | RW     | Internal non-fatal error mask            |
| 0x2100_0098  | INTERNAL_AGG_ERROR_FATAL_MASK     | 32    | RW     | Aggregated fatal error mask              |
| 0x2100_009C  | INTERNAL_AGG_ERROR_NON_FATAL_MASK | 32    | RW     | Aggregated non-fatal error mask          |
| 0x2100_00A0  | INTERNAL_FW_ERROR_FATAL_MASK      | 32    | RW     | FW fatal error mask                      |
| 0x2100_00A4  | INTERNAL_FW_ERROR_NON_FATAL_MASK  | 32    | RW     | FW non-fatal error mask                  |

#### MCI Watchdog Timer

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_00B0  | WDT_TIMER1_EN                     | 32    | RW     | WDT Timer 1 enable                       |
| 0x2100_00B4  | WDT_TIMER1_CTRL                   | 32    | RW     | WDT Timer 1 control                      |
| 0x2100_00B8  | WDT_TIMER1_TIMEOUT_PERIOD_0       | 32    | RW     | Timer 1 timeout period low (64-bit)      |
| 0x2100_00BC  | WDT_TIMER1_TIMEOUT_PERIOD_1       | 32    | RW     | Timer 1 timeout period high              |
| 0x2100_00C0  | WDT_TIMER2_EN                     | 32    | RW     | WDT Timer 2 enable                       |
| 0x2100_00C4  | WDT_TIMER2_CTRL                   | 32    | RW     | WDT Timer 2 control                      |
| 0x2100_00C8  | WDT_TIMER2_TIMEOUT_PERIOD_0       | 32    | RW     | Timer 2 timeout period low               |
| 0x2100_00CC  | WDT_TIMER2_TIMEOUT_PERIOD_1       | 32    | RW     | Timer 2 timeout period high              |
| 0x2100_00D0  | WDT_STATUS                        | 32    | RO     | WDT status                               |
| 0x2100_00D4  | WDT_CFG_0                         | 32    | RW     | WDT configuration 0                      |
| 0x2100_00D8  | WDT_CFG_1                         | 32    | RW     | WDT configuration 1                      |

#### MCI MCU Timer (mtime/mtimecmp)

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_00E0  | MCU_TIMER_CONFIG                  | 32    | RW     | Timer frequency configuration            |
| 0x2100_00E4  | MCU_RV_MTIME_L                    | 32    | RW     | mtime register low                       |
| 0x2100_00E8  | MCU_RV_MTIME_H                    | 32    | RW     | mtime register high                      |
| 0x2100_00EC  | MCU_RV_MTIMECMP_L                 | 32    | RW     | mtimecmp register low                    |
| 0x2100_00F0  | MCU_RV_MTIMECMP_H                 | 32    | RW     | mtimecmp register high                   |

#### MCI Boot & Reset Control

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_0100  | RESET_REQUEST                     | 32    | RW     | MCU reset request register               |
| 0x2100_0104  | MCI_BOOTFSM_GO                    | 32    | RW     | Boot FSM continue from breakpoint        |
| 0x2100_0108  | CPTRA_BOOT_GO                     | 32    | RW     | Caliptra boot go (MCU writes)            |
| 0x2100_010C  | FW_SRAM_EXEC_REGION_SIZE          | 32    | RW     | MCU SRAM exec region size (4 KiB inc, base-0) |
| 0x2100_0110  | MCU_NMI_VECTOR                    | 32    | RW     | MCU NMI vector address                   |
| 0x2100_0114  | MCU_RESET_VECTOR                  | 32    | RW     | MCU reset vector override                |

#### MCI Mailbox AXI User Configuration

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_0180–0x2100_0190 | MBOX0_VALID_AXI_USER_[0-4] | 32 | RW   | Mailbox 0 trusted AXI user IDs           |
| 0x2100_01A0–0x2100_01B0 | MBOX0_AXI_USER_LOCK_[0-4]  | 32 | RW   | Mailbox 0 user lock registers            |
| 0x2100_01C0–0x2100_01D0 | MBOX1_VALID_AXI_USER_[0-4] | 32 | RW   | Mailbox 1 trusted AXI user IDs           |
| 0x2100_01E0–0x2100_01F0 | MBOX1_AXI_USER_LOCK_[0-4]  | 32 | RW   | Mailbox 1 user lock registers            |

#### MCI SOC Debug Control

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_0300  | SOC_DFT_EN_0                      | 32    | RW     | SOC DFT enable mask 0                    |
| 0x2100_0304  | SOC_DFT_EN_1                      | 32    | RW     | SOC DFT enable mask 1                    |
| 0x2100_0308  | SOC_HW_DEBUG_EN_0                 | 32    | RW     | SOC HW debug enable mask 0               |
| 0x2100_030C  | SOC_HW_DEBUG_EN_1                 | 32    | RW     | SOC HW debug enable mask 1               |
| 0x2100_0310  | SOC_PROD_DEBUG_STATE_0            | 32    | RW     | Production debug state 0                 |
| 0x2100_0314  | SOC_PROD_DEBUG_STATE_1            | 32    | RW     | Production debug state 1                 |
| 0x2100_0318  | FC_FIPS_ZEROIZATION               | 32    | RW     | FIPS zeroization control                 |
| 0x2100_031C  | FC_FIPS_ZEROIZATION_STS           | 32    | RO     | FIPS zeroization status                  |

#### MCI Generic I/O & Debug

| Address      | Name                              | Width | Access | Description                              |
|--------------|-----------------------------------|-------|--------|------------------------------------------|
| 0x2100_0400  | GENERIC_INPUT_WIRES_0             | 32    | RO     | Generic input wires low                  |
| 0x2100_0404  | GENERIC_INPUT_WIRES_1             | 32    | RO     | Generic input wires high                 |
| 0x2100_0408  | GENERIC_OUTPUT_WIRES_0            | 32    | RW     | Generic output wires low                 |
| 0x2100_040C  | GENERIC_OUTPUT_WIRES_1            | 32    | RW     | Generic output wires high                |
| 0x2100_0410  | DEBUG_IN                          | 32    | RO     | Debug input                              |
| 0x2100_0414  | DEBUG_OUT                         | 32    | RW     | Debug output                             |

### 4.3 MCU Mailbox Registers (per mailbox)

| Offset (within MBOX) | Name          | Width | Access | Description                              |
|-----------------------|---------------|-------|--------|------------------------------------------|
| 0x0000_0000–0x001F_FFFF | MBOX SRAM   | 32    | RW     | Mailbox SRAM (up to 2 MiB, DWORD aligned)|
| 0x0020_0000–0x0020_003F | MBOX CSR    | —     | —      | Mailbox CSRs                             |
| — (in CSR space)      | LOCK          | 1     | RW     | Lock status (read-set, write 0 to unlock)|
| — (in CSR space)      | EXECUTE       | 1     | RW     | Execute flag (data available)            |
| — (in CSR space)      | CMD_STATUS    | 32    | RW     | Command status (MCU-only write)          |
| — (in CSR space)      | DLEN          | 32    | RW     | Data length                              |
| — (in CSR space)      | TARGET_USER   | 32    | RW     | Target user AXI ID (MCU-only write)      |
| — (in CSR space)      | TARGET_STATUS | 32    | RW     | Target user status                       |
| — (in CSR space)      | TARGET_DONE   | 1     | RW     | Target user done flag                    |

### 4.4 Fuse Controller Registers (Key)

| Offset  | Name                        | Width | Access | Description                       |
|---------|-----------------------------|-------|--------|-----------------------------------|
| 0x00    | STATUS                      | 32    | RO     | OTP status (DAI_IDLE, errors)    |
| 0x04    | CHECK_TIMEOUT               | 32    | RW     | Background check timeout          |
| 0x08    | INTEGRITY_CHECK_PERIOD      | 32    | RW     | Integrity check period mask       |
| 0x0C    | CONSISTENCY_CHECK_PERIOD    | 32    | RW     | Consistency check period mask     |
| 0x10    | CHECK_TRIGGER               | 32    | RW     | Manual check trigger              |
| 0x14    | DIRECT_ACCESS_WDATA_0       | 32    | RW     | DAI write data low                |
| 0x18    | DIRECT_ACCESS_WDATA_1       | 32    | RW     | DAI write data high               |
| 0x1C    | DIRECT_ACCESS_RDATA_0       | 32    | RO     | DAI read data low                 |
| 0x20    | DIRECT_ACCESS_RDATA_1       | 32    | RO     | DAI read data high                |
| 0x24    | DIRECT_ACCESS_ADDRESS       | 32    | RW     | DAI address                       |
| 0x28    | DIRECT_ACCESS_CMD           | 32    | RW     | DAI command (read=1, write=2, digest=4) |
| 0x2C    | DIRECT_ACCESS_REGWEN        | 1     | RO     | DAI write enable (auto-clear during ops) |
| 0x30    | VENDOR_PK_HASH_LOCK         | 32    | RW     | Volatile lock for PK hash partition |

### 4.5 MCU Trace Buffer Registers (DMI Access)

| DMI Addr | Name                    | Width | Access | Description                              |
|----------|-------------------------|-------|--------|------------------------------------------|
| 0x58     | MCU_SRAM_ADDR           | 32    | RW     | MCU SRAM address (byte addr, DWORD align)|
| 0x59     | MCU_SRAM_DATA           | 32    | RW     | MCU SRAM data (read/write via mailbox)   |
| 0x5A     | MCU_TRACE_STATUS        | 32    | RO     | VALID_DATA, WRAPPED flags                |
| 0x5B     | MCU_TRACE_CONFIG        | 32    | RO     | TRACE_BUFFER_DEPTH                       |
| 0x5C     | MCU_TRACE_WR_PTR        | 32    | RO     | Write pointer                            |
| 0x5D     | MCU_TRACE_RD_PTR        | 32    | RW     | Read pointer (increment to advance)      |
| 0x5E     | MCU_TRACE_DATA          | 32    | RO     | Trace data at READ_PTR                   |

### 4.6 Caliptra AXI DMA Registers

See Caliptra Core specification for full DMA register detail. Key registers:

| Name              | Width | Access | Description                              |
|-------------------|-------|--------|------------------------------------------|
| SRC_ADDR          | 64    | RW     | Source address for DMA                   |
| DST_ADDR          | 64    | RW     | Destination address for DMA              |
| BYTE_COUNT        | 32    | RW     | Transfer size in bytes (DWORD aligned)   |
| BLOCK_SIZE        | 32    | RW     | Block size for streaming boot (0=disable)|
| CONTROL           | 32    | RW     | Routes, fixed, AES mode, GO bit          |
| STATUS0           | 32    | RO     | Busy, Error, Command Error flags         |
| DATAIN            | 32    | WO     | AHB→FIFO data input                     |
| DATAOUT           | 32    | RO     | FIFO→AHB data output                    |

#### DMA Control Register Bitfields

| Bits   | Name           | Access | Description                              |
|--------|----------------|--------|------------------------------------------|
| [0]    | GO             | RW     | Start DMA operation                      |
| [2:1]  | READ_ROUTE     | RW     | 00=DISABLE, 01=AHB, 10=MBOX, 11=AXI     |
| [4:3]  | WRITE_ROUTE    | RW     | 00=DISABLE, 01=AHB, 10=MBOX, 11=AXI     |
| [5]    | READ_FIXED     | RW     | FIXED burst on read channel              |
| [6]    | WRITE_FIXED    | RW     | FIXED burst on write channel             |
| [7]    | AES_MODE       | RW     | Enable AES passthrough                   |
| [8]    | AES_GCM_MODE   | RW     | Enable AES GCM mode                      |

### 4.7 MCI DMI-Only Register

| DMI Addr | Name                    | Width | Access | Description                              |
|----------|-------------------------|-------|--------|------------------------------------------|
| 0x7C     | MCI_DMI_MCI_HW_OVERRIDE | 32    | RW     | HW override controls (debug only)        |

#### Bitfield Detail

| Bits  | Name                            | Access | Description                              |
|-------|---------------------------------|--------|------------------------------------------|
| [0]   | mcu_sram_fw_exec_region_lock    | RW     | ORed with input signal for debugger control|
| [31:1]| RSVD                            | RW     | Reserved                                 |

---

## 5. Interrupts

### 5.1 MCU External Interrupt Map

| Vector | Source            | Description                                        |
|--------|-------------------|----------------------------------------------------|
| 0      | Reserved          | Reserved by VeeR                                   |
| 1      | MCI               | All MCI interrupts (error + notification groups)   |
| 2      | I3C               | I3C core interrupts                                |
| 255:3  | `cptra_ss_mcu_ext_int` | SoC external interrupts                        |

### 5.2 MCI Interrupt Sources

All interrupts have: Status (W1C), Enable, SW Trigger, Counter.

#### Error Group

| Source                    | Description                                  |
|---------------------------|----------------------------------------------|
| MCU SRAM ECC (single)     | Correctable ECC error in MCU SRAM            |
| MCU SRAM ECC (double)     | Uncorrectable ECC error in MCU SRAM          |
| MCU MBOX0 ECC (single)    | Correctable ECC in mailbox 0 SRAM            |
| MCU MBOX0 ECC (double)    | Uncorrectable ECC in mailbox 0 SRAM          |
| MCU MBOX1 ECC (single)    | Correctable ECC in mailbox 1 SRAM            |
| MCU MBOX1 ECC (double)    | Uncorrectable ECC in mailbox 1 SRAM          |
| WDT Timer 1               | Watchdog timer 1 timeout                     |
| WDT Timer 2               | Watchdog timer 2 timeout (cascade mode)      |
| Caliptra MBOX data avail  | Caliptra core mailbox data available          |
| OTP FC Done                | OTP operation complete                       |

#### Notification Group

| Source                    | Description                                  |
|---------------------------|----------------------------------------------|
| SOC MBOX lock request     | SOC agent requests MCU mailbox lock          |
| MBOX0 data avail from SOC | SOC agent executed mailbox 0                 |
| MBOX1 data avail from SOC | SOC agent executed mailbox 1                 |
| Target Done (MBOX0)       | Target user done processing MBOX0            |
| Target Done (MBOX1)       | Target user done processing MBOX1            |
| FW_EXEC_CTL[2]            | Caliptra requesting MCU reset (hitless update)|

- **Interrupt output**: `mci_intr` (active-high, level, OR of all groups)
- **Clear mechanism**: W1C on individual status registers, service source IP first then clear MCI
- **Masking**: Enable registers per interrupt + global group enable

### 5.3 MCU Mailbox Interrupts

| Recipient     | Source                    | Description                     |
|---------------|---------------------------|---------------------------------|
| MCU           | SOC MBOX lock request     | SOC trying to obtain lock       |
| MCU           | MBOX data available       | SOC agent set EXECUTE           |
| MCU           | Target Done               | Target user finished processing |
| SOC (output)  | MBOX data available       | MCU set EXECUTE for SOC         |

---

## 6. Memory

### 6.1 Internal Memory Map

| Instance          | Type      | Size (Range)          | Width | R Ports | W Ports | Latency | Description                    |
|-------------------|-----------|-----------------------|-------|---------|---------|---------|--------------------------------|
| MCU ROM           | ROM       | Configurable (256 KiB default) | 64 | 1       | 0       | 1 cycle | MCU boot ROM (read-only)       |
| MCU DCCM          | SRAM      | 16 KiB                | 32+ECC| 1       | 1       | 1 cycle | MCU data closely coupled mem   |
| MCU I-Cache       | SRAM      | 16 KiB                | —     | 1       | 0       | 1 cycle | MCU instruction cache          |
| MCU SRAM          | SRAM      | 4 KiB – 2 MiB         | 32+7  | 1       | 1       | 1 cycle | Shared MCU code/data (ECC SECDED)|
| MCU MBOX0 SRAM    | SRAM      | 0 – 2 MiB             | 32+7  | 1       | 1       | 1 cycle | Mailbox 0 SRAM (ECC SECDED)    |
| MCU MBOX1 SRAM    | SRAM      | 0 – 2 MiB             | 32+7  | 1       | 1       | 1 cycle | Mailbox 1 SRAM (ECC SECDED)    |
| MCU Trace Buffer  | Reg FIFO  | 64 packets            | 128   | 1       | 1       | —       | MCU trace circular buffer      |
| Caliptra ICCM     | SRAM      | (Caliptra spec)       | —     | 1       | 1       | 1 cycle | Caliptra instruction memory    |
| Caliptra DCCM     | SRAM      | (Caliptra spec)       | —     | 1       | 1       | 1 cycle | Caliptra data memory           |
| Caliptra MBOX     | SRAM      | (Caliptra spec)       | —     | 1       | 1       | 1 cycle | Caliptra mailbox SRAM          |
| Caliptra IMEM     | ROM       | (Caliptra spec)       | —     | 1       | 0       | 1 cycle | Caliptra ROM                   |
| Caliptra MLDSA    | SRAM      | (Adams Bridge spec)   | —     | 1       | 1       | 1 cycle | MLDSA SRAM                     |
| DMA FIFO          | Reg FIFO  | 512 bytes             | 32    | 1       | 1       | —       | AXI DMA internal buffer        |
| OTP Macro         | OTP       | (fuse map)            | 16    | 1       | 1       | Variable| One-time programmable storage  |

### 6.2 MCU SRAM Region Partitioning

The MCU SRAM is divided into two regions by MCU ROM:

| Region                       | Access Before Lock  | Access After Lock       | Description               |
|------------------------------|---------------------|-------------------------|---------------------------|
| Updatable Execution Region   | MCU SRAM Config User (Caliptra) | MCU IFU/LSU only | FW code + data            |
| Protected Data Region        | MCU LSU only        | MCU LSU only            | Stack/heap, never writable externally |

- Boundary set by `FW_SRAM_EXEC_REGION_SIZE` register (4 KiB granularity, base-0 count)
- Lock signal: `mcu_sram_fw_exec_region_lock` (from Caliptra or DMI override)

### 6.3 SRAM Timing

- **Writes**: `wren` asserted simultaneously with data and address → stored 1 clock cycle later
- **Reads**: Clock enable asserted with address → output data available 1 clock cycle later (flip-flop register stage)
- **SRAM BIST/Repair**: External to CSS boundary; performed during cold reset only, before `cptra_ss_rst_b_i` deassertion
- **SRAM Initialization**: All entries must be zeroed before `cptra_ss_rst_b_i` deassertion during powergood cycling

---

## 7. Timing

### 7.1 Clock

- **Primary Clock**: `cptra_ss_clk_i`
- **Required Frequency**: 333 MHz – 400 MHz
  - I3C core requires ≥333 MHz to meet 12ns tSCO timing
  - SOCs with large PAD delays may need faster clock
- **Single clock domain**: All subsystem components operate on `cptra_ss_clk_i`
- **Gated clocks**: `cptra_ss_rdc_clk_cg_o` (warm reset RDC), `cptra_ss_mcu_clk_cg_o` (MCU RDC)

### 7.2 Reset Architecture

| Reset              | Type     | Trigger                    | Domain                | Notes                                  |
|--------------------|----------|----------------------------|-----------------------|----------------------------------------|
| `cptra_ss_rst_b_i` | Primary  | SoC reset controller       | `cptra_ss_clk_i`      | Cold or warm reset, min 2 cycles       |
| `cptra_ss_rst_b_o` | Delayed  | MCI                        | `cptra_ss_rdc_clk_cg_o` | For memory RDC crossing              |
| MCU reset          | Controlled| MCI boot FSM              | `cptra_ss_clk_i`      | Loopback `cptra_ss_mcu_rst_b_o` → `_i` |
| Caliptra reset     | Controlled| MCI boot FSM              | `cptra_ss_clk_i`      | Loopback `cptra_ss_mci_cptra_rst_b_o` → `_i` |

- **Warm Reset**: Preserves MCU SRAM content. MCI tracks `RESET_REASON`.
- **Cold Reset** (Powergood cycling): All memories cleared, full reinitialization.

### 7.3 Reset Sequencing (RDC Considerations)

1. `cptra_ss_warm_reset_rdc_clk_dis_o` asserted few cycles after `cptra_ss_rst_b_i`
2. `cptra_ss_rdc_clk_cg_o` gated → `cptra_ss_rst_b_o` asserted
3. On deassertion: `cptra_ss_rst_b_i` deasserted → few cycles → `cptra_ss_warm_reset_rdc_clk_dis_o` deasserted → `cptra_ss_rdc_clk_cg_o` ungated

### 7.4 Latency & Throughput

- **Input-to-output latency**: AXI DMA 1 MiB transfer: varies by route
- **Throughput**: AXI DMA supports up to 2 outstanding reads + 2 outstanding writes (1+1 in streaming boot mode)
- **Critical path**: I3C tSCO timing (12ns requirement drives 333 MHz minimum)

### 7.5 CDC Crossings

- All components operate on single clock domain (`cptra_ss_clk_i`)
- **Known CDC**: I3C core has CDC issue requiring ≥333 MHz operation
- **RDC crossings**: Warm reset domain → cold reset/memory domain handled by gated clock and delayed reset
  - `cptra_ss_rdc_clk_cg_o` used for MCU SRAM, MCU MBOX memories
  - `cptra_ss_mcu_clk_cg_o` used for MCU warm/cold reset domain crossing
- LCC may start on SoC internal clock (not `cptra_ss_clk_i`) to prevent clock stretch attacks

---

## 8. RTL Implementation Notes

### 8.1 Coding Style

- Nonblocking assignments (`<=`) in `always_ff`, blocking (`=`) in `always_comb`
- All FFs must have synchronous reset to `rst_n` (active-low)
- No latches: every `always_comb` branch must assign all outputs
- `CALIPTRA_MODE_SUBSYSTEM` macro must be defined for all builds

### 8.2 Integrator Modifications Required

| File | Modification |
|------|-------------|
| `css_mcu0_dmi_jtag_to_core_sync.v` | Replace with technology-specific sync cell |
| `css_mcu0_beh_lib.sv` | Replace clock gaters and sync cells with technology-specific |
| `caliptra_ss_includes.svh` | Modify `CPTRA_SS_ROM_SIZE_KB` for correct MCU ROM size |

### 8.3 AXI Protocol Rules

- AXI USER width: 32 bits for all interfaces
- Only ARUSER and AWUSER used for filtering; WUSER, RUSER, BUSER tied to 0
- Interconnect passes AXI USER unmodified — each IP performs own filtering
- Subordinates accept up to 2 Read + 2 Write requests, in-order responses
- Recommended: configure interconnect for single outstanding request for area optimization

### 8.4 Security Constraints

- Secret fuse partitions (UDS_SEED, FIELD_ENTROPY, SECRET_PROD_{0-3}) must be excluded from scan path
- `otp_broadcast_o` port and its drivers must not be scannable
- PRESENT cipher keys (from `otp_ctrl_part_pkg.sv`) must be excluded from scan path
- LCC TAP runs on its own clock (SoC internal) to prevent clock stretch attacks
- All OTP programming must be atomic — single AXI USER for entire DAI sequence
- Double-bit ECC errors on MCU SRAM/MBOX trigger HW_ERROR_FATAL

### 8.5 Memory Implementation

- All SRAMs instantiated outside CSS boundary via memory export interfaces
- SRAM repair/BIST is integrator responsibility (external to CSS)
- SRAMs must NOT go through BIST/repair across warm reset
- All SRAMs must be zeroed during cold reset before `cptra_ss_rst_b_i` deassertion
- MCU MBOX and MCU SRAM use 32-bit data + 7-bit ECC (Hamming SECDED)

### 8.6 Lint Guidelines

- Use Synopsys SpyGlass U-2023.03-SP2-8
- Known lint issues: signal width mismatches (intentional), undriven signals
- Recommended lint rules per `config/compilespecs.yml`

---

## 9. DV Plan

### 9.1 Test Sequence

| ID  | Sequence Name                    | Steps                                                                 | Expected Result                          | Priority |
|-----|----------------------------------|-----------------------------------------------------------------------|------------------------------------------|----------|
| S1  | Power-on Reset                   | 1. Assert pwrgood 2. Deassert rst_b 3. Wait for boot FSM completion   | All outputs at reset defaults, CSS-BootFSM completes | High |
| S2  | MCU Hello World                  | 1. Complete boot sequence 2. MCU ROM executes 3. Print to trace       | "Hello World" in trace buffer            | High |
| S3  | MCU Caliptra Bringup             | 1. Boot sequence 2. MCU ROM provisions Caliptra 3. Caliptra boot      | Caliptra operational, MCU executing from SRAM | High |
| S4  | MCU DCCM Access                  | 1. MCU writes/reads DCCM 2. Verify all address ranges                 | Data matches, no errors                  | High |
| S5  | MCU Fuse Controller Bringup      | 1. FC initialization 2. Read FC STATUS 3. Verify DAI idle             | STATUS shows no errors, DAI idle         | High |
| S6  | MCU LMEM Execution               | 1. Load FW into MCU SRAM 2. Execute from SRAM                        | FW executes correctly from MCU SRAM      | High |
| S7  | I3C Streaming Boot               | 1. Send image via I3C 2. Verify payload_available/image_activated 3. Caliptra processes | Image authenticated and loaded          | High |
| S8  | AXI Streaming Boot               | 1. Configure REC_INTF_CFG 2. Send image via AXI 3. Caliptra processes | Image authenticated and loaded           | High |
| S9  | Fuse Provisioning with LC Ctrl   | 1. Transition LC states 2. Program fuses 3. Lock partitions           | Fuses programmed, partitions locked      | High |
| S10 | LC Controller Bringup            | 1. FC init 2. LCC init 3. Read LC state                              | LCC operational, correct LC state        | High |
| S11 | LC State Transitions             | 1. RAW → TEST_UNLOCKED 2. → MANUF 3. → PROD 4. → RMA/SCRAP           | State transitions succeed, correct signals | High |
| S12 | Production Debug Unlock          | 1. Set DEBUG_INTENT 2. Challenge-response 3. Verify unlock level      | Debug level granted, secrets erased      | High |
| S13 | MCU Mailbox Communication        | 1. SOC obtains lock 2. Write data 3. Execute 4. MCU reads             | Data transferred, SRAM zeroized on unlock | High |
| S14 | MCU Mailbox Target User          | 1. SOC locks 2. MCU adds Target 3. Target processes 4. Target done    | Target user completes, MCU updates status | Medium |
| S15 | MCU Hitless Update               | 1. Caliptra loads new FW 2. FW_EXEC_CTL[2] set 3. MCU reset 4. Reboot | MCU runs new FW without full SoC reset   | High |
| S16 | Watchdog Timer Cascade           | 1. Configure WDT cascade 2. Let Timer 1 expire 3. Let Timer 2 expire  | Error interrupt then NMI + FATAL         | Medium |
| S17 | Watchdog Timer Independent       | 1. Configure WDT independent 2. Let timers expire                     | Error interrupts only, no NMI            | Medium |
| S18 | Error Aggregation                | 1. Inject errors from each source 2. Check aggregate registers         | Correct error bits set, masking works    | Medium |
| S19 | MCU Trace Buffer                 | 1. MCU enables trace 2. Generate traces 3. Read via DMI               | Correct trace data extracted             | Medium |
| S20 | AXI DMA AXI→AXI Transfer         | 1. Configure DMA 2. Transfer data SoC→SoC 3. Verify data              | Data matches, STATUS shows complete      | High |
| S21 | AXI DMA Mailbox Route            | 1. Configure DMA read→mailbox 2. Transfer 3. Read from mailbox        | Data in mailbox matches source           | Medium |
| S22 | AXI DMA AES Mode                 | 1. Configure AES 2. Set DMA AES mode 3. Transfer encrypted image      | Decrypted data matches expected          | Medium |
| S23 | Back-to-back DMA Operations      | 1. Issue multiple DMA transfers without idle                          | No data loss, all transfers complete     | Medium |
| S24 | MCU No ROM Config                | 1. Set no_rom_config strap 2. SOC writes CPTRA_BOOT_GO 3. Boot        | Caliptra boots without MCU ROM           | Medium |
| S25 | Volatile RAW Unlock              | 1. In RAW state 2. Inject hashed token via TAP 3. Transition           | TEST_UNLOCKED0 reached without fuse programming | Medium |
| S26 | FIPS Zeroization                 | 1. Set FIPS_ZEROIZATION_PPD 2. Caliptra issues DAI zeroize commands 3. Cold reset 4. Verify | Partition digests show zeroized values | Medium |
| S27 | Boot FSM Breakpoint              | 1. Assert boot_seq_brkpoint 2. Deassert reset 3. Configure via DMI 4. Set BRKPOINT_GO | FSM resumes after configuration | Low |
| S28 | DMI Access Control               | 1. Access DMI in debug locked state 2. Access in debug unlocked state  | Correct access restrictions enforced     | Medium |
| S29 | MCU SRAM Execution Region Lock   | 1. Caliptra loads FW 2. Set exec_region_lock 3. MCU accesses           | MCU IFU/LSU access, others blocked       | High |
| S30 | MCU MRAC and Split Memory        | 1. Configure address map 2. Test DWORD alignment 3. Test iCache       | Correct side-effect behavior, iCache functional | Low |

### 9.2 Coverage Goals

#### Functional Coverage

- All CSS-BootFSM states visited
- All LCC states visited (RAW, TEST_UNLOCKED, TEST_LOCKED, MANUF, PROD, PROD_END, RMA, SCRAP)
- All LCC state transitions exercised (forward-only)
- All Caliptra Core security states entered
- All DMA routes exercised (AHB, MBOX, AXI combinations)
- All DMA modes (normal, streaming boot, AES)
- All interrupt sources fired and cleared
- All register bits toggled (RW bits)
- All mailbox flows (lock, execute, target user, unlock with zeroization)
- All WDT modes (cascade, independent)
- MCU SRAM: full, empty, single-entry, protected vs execution regions
- All fuse partition programming and locking sequences
- Production debug unlock: all 8 debug levels
- Manufacturing debug unlock flow
- Hitless update flow (FW_BOOT_UPD_RESET, FW_HITLESS_UPD_RESET)
- MCU trace buffer: empty, full, wrapped, single entry

#### Code Coverage

- **Line**: ≥ 90%
- **Branch**: ≥ 85%
- **Toggle**: ≥ 80%
- **FSM**: 100% state + transition coverage

#### SVA Assertions

- No CSS-BootFSM illegal state transitions
- No LCC backward state transitions
- LCC escalation enable cannot be cleared without reset
- `mci_intr` must deassert within N cycles of all interrupt sources cleared
- DMA FIFO never overflow/underflow
- MCU SRAM execution region access violations generate AXI error
- Mailbox SRAM zeroized after lock release (data = 0 from 0 to DLEN)
- WDT Timer 2 only starts after Timer 1 timeout in cascade mode
- Secret fuse scan exclusion paths are never in scan mode during production
- `payload_available` only asserted after successful I3C write + PEC verification
- `image_activated` only deasserted after ROM clears RECOVERY_CTRL byte 2

### 9.3 Known Corner Cases / Hazards

| Hazard                              | Description                                                    | Mitigation                          |
|-------------------------------------|----------------------------------------------------------------|-------------------------------------|
| Warm reset during OTP programming   | Can corrupt OTP values                                         | FC blank check on re-program; only LC partition modified in-field |
| RDC during warm reset               | MCU SRAM/MBOX corruption when clock/reset domains cross       | Gated clock + delayed reset (`cptra_ss_rdc_clk_cg_o`) |
| I3C CDC timing                      | I3C core CDC requires minimum clock frequency                  | Enforce ≥333 MHz clock              |
| Double-bit ECC in MCU SRAM          | Fatal error, potential data loss                               | HW_ERROR_FATAL asserted, AXI SLVERR |
| Double write to OTP                 | Can damage OTP array                                           | FC performs blank check before write |
| Token race in LCC                   | Multiple TAP token injections during transition                | LCC claim_transition_if mutex       |
| Mailbox lock starvation             | MCU never releases lock                                        | MCU always has override access      |
| MCU SRAM not initialized on cold boot | Uninitialized SRAM may cause MCU to execute garbage           | Integrator must zero all SRAMs before rst_b deassertion |
| AXI interconnect ID width mismatch  | MCU IFU/LSU/SB have different ID widths (3/3/1)                | Interconnect must support all widths|
| MCU MRAC side-effect on MBOX access | DWORD alignment required for side-effect regions               | Use split memory mapping or ensure DWORD alignment |
| Debug unlock + secret leakage       | Secrets may leak through debug interfaces                      | HW erases UDS/FE before debug enable |
| MCU halt without ack                | MCU may not respond to halt request                            | WDT timeout as backup               |

### 9.4 Test Suite Reference

| Test Name                        | Description                                                        |
|----------------------------------|--------------------------------------------------------------------|
| `MCU_HELLO_WORLD`                | Basic MCU operation verification                                   |
| `MCU_CPTRA_BRINGUP`              | MCU + Caliptra bring-up sequence                                   |
| `MCU_DCCM_ACCESS`                | MCU DCCM read/write validation                                     |
| `MCU_FUSE_CTRL_BRINGUP`          | Fuse Controller bring-up by MCU                                    |
| `MCU_LMEM_EXE`                   | MCU SRAM execution test                                            |
| `MCU_MCTP_SMOKE_TEST`            | I3C main target operation                                          |
| `MCU_TEST_ROM_I3C_STREAMING_BOOT`| I3C recovery target with Caliptra test ROM                         |
| `FUSE_PROV_WITH_LC_CTRL`         | Fuse provisioning + LC state transitions                           |
| `CALIPTRA_SS_LC_CTRL_BRINGUP`    | LC Controller bring-up sequence                                    |
| `CALIPTRA_SS_LC_CTRL_ST_TRANS`   | LC Controller state transition validation                          |

### 9.5 Simulation Environment

| Tool                    | Version                   |
|-------------------------|---------------------------|
| VCS                     | U-2023.03-SP1-1_Full64    |
| Verdi                   | (VCS bundle)              |
| Avery AXI/I3C VIP       | 2025.1                    |
| ARM AXI Protocol Checker| BP063-r0p1                |
| UVM                     | 1.1d                      |
| RISC-V Toolchain        | 2023.04.29 (gcc 12.2.0)   |

### 9.6 Environment Variables (Simulation)

| Variable                 | Description                                           |
|--------------------------|-------------------------------------------------------|
| `CALIPTRA_WORKSPACE`     | Absolute path to workspace containing repo            |
| `CALIPTRA_SS_ROOT`       | Absolute path to caliptra-ss repo root                |
| `CALIPTRA_ROOT`          | `${CALIPTRA_SS_ROOT}/third_party/caliptra-rtl`        |
| `CALIPTRA_AXI4PC_DIR`    | Path to ARM AXI4 Protocol Checker                     |
| `AVERY_HOME`             | Avery VIP installation root                           |
| `TESTNAME`               | Test suite name (e.g., `mcu_hello_world`)             |
| `CALIPTRA_TESTNAME`      | Caliptra core firmware test name                      |
