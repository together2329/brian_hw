# OpenROAD PnR for example_counter — single-pass floorplan→place→CTS→route
# PDK env vars sourced before calling this script

read_lef $::env(SKY130_TLEF)
read_lef $::env(SKY130_LEF)
read_liberty $::env(SKY130_LIB)
read_verilog syn/out/synth.v
link_design example_counter

# SDC constraints
create_clock clk -name clk -period 20.0
set_input_delay 2.0 [all_inputs] -clock clk
set_output_delay 5.0 [all_outputs] -clock clk

# Floorplan — 60% utilization, 1:1 aspect ratio
initialize_floorplan -utilization 60 -aspect_ratio 1.0 -core_space 2 -site unithd

# Make tracks (sky130hd)
source $::env(SKY130_TRACKS)

# Place pins
place_pins -hor_layers met3 -ver_layers met2

# Global placement
global_placement -density 0.65

# Detailed placement
detailed_placement

# CTS
clock_tree_synthesis -root_buf sky130_fd_sc_hd__clkbuf_4 -buf_list sky130_fd_sc_hd__clkbuf_4

# Post-CTS optimization
set_propagated_clock [get_clocks clk]
detailed_placement

# Global routing
global_route -congestion_iterations 50

# Detailed routing
detailed_route

# Write outputs
write_def pnr/out/final.def
write_verilog pnr/out/pnr.v
write_sdc pnr/out/pnr.sdc

# Report
report_design_area
report_checks -path_delay min_max
report_wns
report_tns

exit
