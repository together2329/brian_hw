// uart_lite_real_param.vh — shared parameter declarations
// Generated from uart_lite_real.ssot.yaml

`ifndef UART_LITE_REAL_PARAM_VH
`define UART_LITE_REAL_PARAM_VH

    parameter DATA_WIDTH    = 8;
    parameter FIFO_DEPTH    = 16;
    parameter OVERSAMPLE    = 16;
    parameter APB_ADDR_WIDTH = 8;
    parameter APB_DATA_WIDTH = 32;
    parameter CLOCK_FREQ_MHZ = 50;

    // Derived parameters
    parameter FIFO_PTR_WIDTH = $clog2(FIFO_DEPTH);
    parameter BAUD_DIV_WIDTH = 16;
    parameter OVERSAMPLE_WIDTH = $clog2(OVERSAMPLE);

`endif // UART_LITE_REAL_PARAM_VH
