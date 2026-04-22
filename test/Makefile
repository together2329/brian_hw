# Counter simulation helper
# Usage:
#   make sim   # compile and run the testbench with Icarus Verilog
#   make lint  # lint the RTL and testbench with Verilator
#   make clean # remove generated simulation output

SIMV = simv
RTL  = counter.sv
TB   = counter_tb.sv

.PHONY: sim lint clean

sim: $(SIMV)
	./$(SIMV)

$(SIMV): $(RTL) $(TB)
	iverilog -g2012 -o $(SIMV) $(RTL) $(TB)

lint: $(RTL) $(TB)
	verilator --lint-only -Wall $(RTL) $(TB)

clean:
	rm -f $(SIMV)
