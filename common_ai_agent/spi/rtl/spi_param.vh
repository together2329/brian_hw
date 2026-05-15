// spi_param.vh — shared SSOT defaults for the SPI RTL modules
parameter integer APB_ADDR_WIDTH = 12,     // APB byte address width
parameter integer APB_DATA_WIDTH = 32,     // APB register data width
parameter integer DATA_WIDTH     = 8,      // Reset/default frame width; runtime CTRL selects 4..32 bits
parameter integer FIFO_DEPTH     = 16,     // TX and RX FIFO depth; SSOT default is 16
parameter integer NUM_CS         = 4,      // Number of active-low chip selects
parameter integer PRESCALE_WIDTH = 16,     // PRESCALE.divisor width
parameter integer CPOL_RESET     = 0,      // CTRL.cpol reset value
parameter integer CPHA_RESET     = 0,      // CTRL.cpha reset value
parameter integer LSB_FIRST_RESET = 0,     // CTRL.lsb_first reset value
parameter integer PCLK_FREQ_MHZ  = 100     // Nominal PCLK frequency for constraints/documentation
