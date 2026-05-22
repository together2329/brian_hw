# AUTO-GENERATED from SSOT. Do not edit.
# Source: cortex_m0lite/yaml/cortex_m0lite.ssot.yaml
# Generator: workflow/syn/scripts/emit_sdc.py
# SDC for OpenSTA / OpenROAD / generic STA flows.

# =========================================================
# Clock definitions
# =========================================================
# core_clk — Core clock at 300 MHz.
create_clock -name core_clk -period 3.333 [get_ports clk]
# bus_clk — AHB bus clock at 150 MHz, synchronous 2:1 divided from core clock source.
create_clock -name bus_clk -period 6.667 [get_ports hclk]

# =========================================================
# Clock relationships
# =========================================================
# synchronous clocks: core_clk bus_clk ratio=2:1

# =========================================================
# Input delays
# =========================================================
# instr_ahb_m inputs — relative to bus_clk
set_input_delay -clock bus_clk 0.6 [get_ports {i_hrdata i_hready i_hresp}]
# data_ahb_m inputs — relative to bus_clk
set_input_delay -clock bus_clk 0.6 [get_ports {d_hrdata d_hready d_hresp}]

# =========================================================
# Output delays
# =========================================================
# instr_ahb_m outputs — relative to bus_clk
set_output_delay -clock bus_clk 0.6 [get_ports {i_haddr i_htrans i_hwrite i_hsize i_hburst i_hwdata}]
# data_ahb_m outputs — relative to bus_clk
set_output_delay -clock bus_clk 0.6 [get_ports {d_haddr d_htrans d_hwrite d_hsize d_hburst d_hwdata}]

# =========================================================
# Reset paths (async assert, sync deassert)
# =========================================================
set_false_path -from [get_ports rst_n]
set_false_path -from [get_ports hresetn]

# =========================================================
# Driving cell / load defaults (override per technology)
# =========================================================
set_load 0.05 [all_outputs]
