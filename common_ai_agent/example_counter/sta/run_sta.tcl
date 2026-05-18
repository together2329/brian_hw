# OpenSTA script for example_counter
source ../workflow/scripts/pdk_env.sh
set lib $::env(SKY130_LIB)
set lef $::env(SKY130_TLEF)

read_liberty $lib
read_lef $lef
read_verilog syn/out/synth.v
link_design example_counter

read_sdc sdc/example_counter.sdc

# Run timing analysis
report_checks -path_delay min_max -format full
report_checks -path_delay max -fields {slew cap input_pins}
report_worst_slack -max
report_worst_slack -min
report_tns
report_wns

# Write reports
redirect -tee sta/out/sta_setup.log { report_checks -path_delay max }
redirect -tee sta/out/sta_hold.log { report_checks -path_delay min }
redirect -tee sta/out/sta_summary.log { report_worst_slack -max; report_worst_slack -min; report_tns; report_wns }

exit
