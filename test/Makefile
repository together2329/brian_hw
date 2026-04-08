# Makefile for counter testbench
# Compile and run with VCD waveform dump

RTL      = counter.v
TB       = counter_tb.sv
TB_MOD   = counter_tb
VVP      = counter_tb.vvp
VCD      = counter_tb.vcd
COMPILER = iverilog
SIMULATOR = vvp
COMP_FLAGS = -g2012

.PHONY: all compile sim wave clean

all: sim

compile:
	$(COMPILER) $(COMP_FLAGS) -o $(VVP) $(RTL) $(TB)

sim: compile
	$(SIMULATOR) $(VVP)

wave: sim
	gtkwave $(VCD) &

clean:
	rm -f $(VVP) $(VCD)
