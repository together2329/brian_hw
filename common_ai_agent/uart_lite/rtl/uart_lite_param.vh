// uart_lite_param.vh — shared parameter declarations for uart_lite
// Include inside each consuming module; do not list as an RTL compile source.

// Number of data bits per UART frame (range 5-8)
`ifndef UART_LITE_DATA_WIDTH
`define UART_LITE_DATA_WIDTH 8
`endif

// TX and RX FIFO depth in entries (power of two)
`ifndef UART_LITE_FIFO_DEPTH
`define UART_LITE_FIFO_DEPTH 16
`endif

// RX oversampling factor (samples per bit)
`ifndef UART_LITE_OVERSAMPLE
`define UART_LITE_OVERSAMPLE 16
`endif

// APB address width
`ifndef UART_LITE_APB_ADDR_WIDTH
`define UART_LITE_APB_ADDR_WIDTH 8
`endif

// APB data width
`ifndef UART_LITE_APB_DATA_WIDTH
`define UART_LITE_APB_DATA_WIDTH 32
`endif
