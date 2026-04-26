
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

# SoC sources
SOC_RTL      = soc_top.v ahb_apb_bridge.v ahb_arbiter.v sram.v dma.v timer_apb.v timer.v counter_apb.v counter.v uart_apb.v uart.v spi_apb.v spi.v
SOC_TB       = tb_soc.v
SOC_VVP      = tb_soc.vvp
SOC_VCD      = soc.vcd

# Default target
.PHONY: all sim_timer sim_counter sim_uart sim_spi sim_sram sim_dma sim_soc sim clean clean_timer clean_counter clean_uart clean_spi clean_sram clean_dma clean_soc

all: sim_timer sim_counter sim_uart sim_spi sim_sram sim_dma

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

# SoC end-to-end compile + simulate
sim_soc: $(SOC_TB) $(SOC_RTL)
	$(IVERILOG) -g2012 -Wall -o $(SOC_VVP) $(SOC_RTL) $(SOC_TB)
	$(VVP) $(SOC_VVP)

# Convenience targets
sim: sim_timer sim_counter sim_uart sim_spi sim_sram sim_dma

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

clean_soc:
	rm -f $(SOC_VVP) $(SOC_VCD)

clean: clean_timer clean_counter clean_uart clean_spi clean_sram clean_dma clean_soc
