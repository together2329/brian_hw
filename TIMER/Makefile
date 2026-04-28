
#----------------------------------------------------------------------------
# Makefile for timer, counter, UART, SPI, SRAM, DMA, and SoC modules
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

# UART sources
UART_RTL     = uart.v uart_apb.v
UART_TB      = tb_uart.v
UART_VVP     = tb_uart.vvp
UART_VCD     = uart.vcd

# SPI sources
SPI_RTL      = spi.v spi_apb.v
SPI_TB       = tb_spi.v
SPI_VVP      = tb_spi.vvp
SPI_VCD      = spi.vcd

# SRAM sources
SRAM_RTL     = sram.v
SRAM_TB      = tb_sram.v
SRAM_VVP     = tb_sram.vvp
SRAM_VCD     = sram.vcd

# DMA sources (DMA test needs SRAM)
DMA_RTL      = dma.v sram.v
DMA_TB       = tb_dma.v
DMA_VVP      = tb_dma.vvp
DMA_VCD      = dma.vcd

# I3C sources
I3C_RTL      = i3c.v i3c_apb.v
I3C_TB       = tb_i3c.v
I3C_VVP      = tb_i3c.vvp
I3C_VCD      = i3c.vcd

# SMBus sources
SMBUS_RTL    = smbus.v smbus_apb.v
SMBUS_TB     = tb_smbus.v
SMBUS_VVP    = tb_smbus.vvp
SMBUS_VCD    = smbus.vcd

# AI Engine sources (AXI4-Lite slave, 256B SRAM, 8-wide MAC, 5 ops)
AI_ENGINE_RTL = ai_engine.v
AI_ENGINE_TB  = tb_ai_engine.v
AI_ENGINE_VVP = tb_ai_engine.vvp
AI_ENGINE_VCD = ai_engine.vcd

# SoC sources
SOC_RTL      = soc_top.v ahb_apb_bridge.v ahb_arbiter.v sram.v dma.v timer_apb.v timer.v counter_apb.v counter.v uart_apb.v uart.v spi_apb.v spi.v i3c_apb.v i3c.v smbus_apb.v smbus.v ahb_axi_bridge.v ai_engine.v
SOC_TB       = tb_soc.v
SOC_VVP      = tb_soc.vvp
SOC_VCD      = soc.vcd

# Default target
.PHONY: all sim_timer sim_counter sim_uart sim_spi sim_sram sim_dma sim_i3c sim_smbus sim_ai_engine sim_soc sim clean clean_timer clean_counter clean_uart clean_spi clean_sram clean_dma clean_i3c clean_smbus clean_ai_engine clean_soc

all: sim_timer sim_counter sim_uart sim_spi sim_sram sim_dma sim_i3c sim_smbus sim_ai_engine sim_soc

# Timer compile + simulate
sim_timer: $(TIMER_TB) $(TIMER_RTL)
	$(IVERILOG) -g2012 -Wall -o $(TIMER_VVP) $(TIMER_RTL) $(TIMER_TB)
	$(VVP) $(TIMER_VVP)

# Counter compile + simulate
sim_counter: $(COUNTER_TB) $(COUNTER_RTL)
	$(IVERILOG) -g2012 -Wall -o $(COUNTER_VVP) $(COUNTER_RTL) $(COUNTER_TB)
	$(VVP) $(COUNTER_VVP)

# UART compile + simulate
sim_uart: $(UART_TB) $(UART_RTL)
	$(IVERILOG) -g2012 -Wall -o $(UART_VVP) $(UART_RTL) $(UART_TB)
	$(VVP) $(UART_VVP)

# SPI compile + simulate
sim_spi: $(SPI_TB) $(SPI_RTL)
	$(IVERILOG) -g2012 -Wall -o $(SPI_VVP) $(SPI_RTL) $(SPI_TB)
	$(VVP) $(SPI_VVP)

# SRAM compile + simulate
sim_sram: $(SRAM_TB) $(SRAM_RTL)
	$(IVERILOG) -g2012 -Wall -o $(SRAM_VVP) $(SRAM_RTL) $(SRAM_TB)
	$(VVP) $(SRAM_VVP)

# DMA compile + simulate
sim_dma: $(DMA_TB) $(DMA_RTL)
	$(IVERILOG) -g2012 -Wall -o $(DMA_VVP) $(DMA_RTL) $(DMA_TB)
	$(VVP) $(DMA_VVP)

# I3C compile + simulate
sim_i3c: $(I3C_TB) $(I3C_RTL)
	$(IVERILOG) -g2012 -Wall -o $(I3C_VVP) $(I3C_RTL) $(I3C_TB)
	$(VVP) $(I3C_VVP)

# SMBus compile + simulate
sim_smbus: $(SMBUS_TB) $(SMBUS_RTL)
	$(IVERILOG) -g2012 -Wall -o $(SMBUS_VVP) $(SMBUS_RTL) $(SMBUS_TB)
	$(VVP) $(SMBUS_VVP)

# AI Engine compile + simulate
sim_ai_engine: $(AI_ENGINE_TB) $(AI_ENGINE_RTL)
	$(IVERILOG) -g2012 -Wall -o $(AI_ENGINE_VVP) $(AI_ENGINE_RTL) $(AI_ENGINE_TB)
	$(VVP) $(AI_ENGINE_VVP)

# SoC end-to-end compile + simulate
sim_soc: $(SOC_TB) $(SOC_RTL)
	$(IVERILOG) -g2012 -Wall -o $(SOC_VVP) $(SOC_RTL) $(SOC_TB)
	$(VVP) $(SOC_VVP)

# Convenience targets
sim: sim_timer sim_counter sim_uart sim_spi sim_sram sim_dma sim_i3c sim_smbus sim_ai_engine

clean_timer:
	rm -f $(TIMER_VVP) $(TIMER_VCD)

clean_counter:
	rm -f $(COUNTER_VVP) $(COUNTER_VCD)

clean_uart:
	rm -f $(UART_VVP) $(UART_VCD)

clean_spi:
	rm -f $(SPI_VVP) $(SPI_VCD)

clean_sram:
	rm -f $(SRAM_VVP) $(SRAM_VCD)

clean_dma:
	rm -f $(DMA_VVP) $(DMA_VCD)

clean_i3c:
	rm -f $(I3C_VVP) $(I3C_VCD)

clean_smbus:
	rm -f $(SMBUS_VVP) $(SMBUS_VCD)

clean_ai_engine:
	rm -f $(AI_ENGINE_VVP) $(AI_ENGINE_VCD)

clean_soc:
	rm -f $(SOC_VVP) $(SOC_VCD)

clean: clean_timer clean_counter clean_uart clean_spi clean_sram clean_dma clean_i3c clean_smbus clean_ai_engine clean_soc
