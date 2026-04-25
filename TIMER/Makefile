#----------------------------------------------------------------------------
# Makefile for timer and counter modules
#----------------------------------------------------------------------------

# Tools
IVERILOG   = iverilog
VVP        = vvp
GTKWAVE    = gtkwave

# Timer sources
TIMER_RTL    = timer.v timer_apb.v
TIMER_TB     = tb_timer.v
TIMER_VVP    = tb_timer.vvp
TIMER_VCD    = timer.vcd

# Counter sources
COUNTER_RTL  = counter.v counter_apb.v
COUNTER_TB   = tb_counter.v
COUNTER_VVP  = tb_counter.vvp
COUNTER_VCD  = counter.vcd

# Default target
.PHONY: all sim_timer sim_counter sim clean clean_timer clean_counter

all: sim_timer sim_counter

# Timer compile + simulate
sim_timer: $(TIMER_TB) $(TIMER_RTL)
	$(IVERILOG) -g2012 -Wall -o $(TIMER_VVP) $(TIMER_RTL) $(TIMER_TB)
	$(VVP) $(TIMER_VVP)

# Counter compile + simulate
sim_counter: $(COUNTER_TB) $(COUNTER_RTL)
	$(IVERILOG) -g2012 -Wall -o $(COUNTER_VVP) $(COUNTER_RTL) $(COUNTER_TB)
	$(VVP) $(COUNTER_VVP)

# Convenience targets
sim: sim_timer sim_counter

clean_timer:
	rm -f $(TIMER_VVP) $(TIMER_VCD)

clean_counter:
	rm -f $(COUNTER_VVP) $(COUNTER_VCD)

clean: clean_timer clean_counter
