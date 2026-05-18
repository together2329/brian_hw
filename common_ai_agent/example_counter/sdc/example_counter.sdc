# SDC constraints for example_counter
# SSOT: clk period 20ns (50 MHz), input delay 2ns, output delay 5ns

create_clock [get_ports clk] -name clk -period 20.0

set_input_delay 2.0 [get_ports {rst_n en load data_in[*]}] -clock clk
set_output_delay 5.0 [get_ports {count[*] overflow}] -clock clk

set_driving_cell [get_ports {rst_n en load data_in[*]}] sky130_fd_sc_hd__inv_2
set_load [expr {0.01 * [get_ports {count[*] overflow} | get_property PORT direction] ne "out" ? 0 : 0.01}] [get_ports {count[*] overflow}]
