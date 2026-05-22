read_liberty $::env(SKY130_LIB)
read_verilog syn/out/synth.v
link_design example_counter
create_clock clk -name clk -period 20.0
set_input_delay 2.0 [all_inputs] -clock clk
set_output_delay 5.0 [all_outputs] -clock clk
report_checks -path_delay max
report_checks -path_delay min
report_worst_slack -max
report_worst_slack -min
report_tns
report_wns
redirect sta/out/sta_report.log { report_checks -path_delay min_max; report_worst_slack -max; report_worst_slack -min; report_tns; report_wns }
exit
