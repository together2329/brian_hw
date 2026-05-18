# OpenSTA script for example_counter (simplified)
source ../workflow/scripts/pdk_env.sh
set lib $::env(SKY130_LIB)

read_liberty $lib
read_verilog syn/out/synth.v
link_design example_counter

# Create clock
create_clock clk -name clk -period 20.0

# Simple constraints
set_input_delay 2.0 [all_inputs] -clock clk
set_output_delay 5.0 [all_outputs] -clock clk

# Reports
report_checks -path_delay max -fields {slew cap}
report_checks -path_delay min -fields {slew cap}
report_worst_slack -max
report_worst_slack -min
report_tns
report_wns

# Write report
write_tcp -format full sta/out/sta_report.log

exit
