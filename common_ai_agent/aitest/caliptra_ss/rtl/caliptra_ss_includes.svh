//********************************************************************************
// SPDX-License-Identifier: Apache-2.0
//
// Caliptra Subsystem — Include File (Parameters & Macros)
// MAS Reference: caliptra_ss/mas/caliptra_ss_mas.md §2.3
//
//********************************************************************************

`ifndef CALIPTRA_SS_INCLUDES_SVH
`define CALIPTRA_SS_INCLUDES_SVH

// -------------------------------------------------------
// MCU ROM Configuration (MAS §2.3 — Integrator-configurable)
// -------------------------------------------------------
parameter CPTRA_SS_ROM_SIZE_KB = 256;
parameter CPTRA_SS_ROM_DATA_W  = 64;
parameter CPTRA_SS_ROM_DEPTH   = (CPTRA_SS_ROM_SIZE_KB * 1024) / (CPTRA_SS_ROM_DATA_W / 8);
parameter CPTRA_SS_ROM_AXI_ADDR_W = $clog2(CPTRA_SS_ROM_SIZE_KB * 1024);
parameter CPTRA_SS_ROM_MEM_ADDR_W = $clog2(CPTRA_SS_ROM_DEPTH);

// -------------------------------------------------------
// Subsystem Build Flag (MAS §8.1)
// NOTE: CALIPTRA_MODE_SUBSYSTEM must also be defined as a
//       Verilog macro on the compile command line.
// -------------------------------------------------------

// -------------------------------------------------------
// Interrupt Vector Assignments (MAS §5.1)
// NOTE: Vector 0 is reserved by VeeR
// -------------------------------------------------------
`define VEER_INTR_VEC_MCI      1
`define VEER_INTR_VEC_I3C      2
`define VEER_INTR_EXT_LSB      3

// -------------------------------------------------------
// AXI Bus Widths (MAS §2.3)
// -------------------------------------------------------
`define CSS_AXI_DATA_W  32
`define CSS_AXI_USER_W  32
`define CSS_AXI_ID_W    8

`endif // CALIPTRA_SS_INCLUDES_SVH
