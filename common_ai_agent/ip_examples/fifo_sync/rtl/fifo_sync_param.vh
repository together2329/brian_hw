// fifo_sync_param.vh — shared default parameter values for fifo_sync RTL.
// Included only when an integration flow wants common defaults; modules expose
// the same names as user-overridable parameters on their module headers.
`ifndef FIFO_SYNC_PARAM_VH
`define FIFO_SYNC_PARAM_VH

`define FIFO_SYNC_DEFAULT_DATA_WIDTH 32
`define FIFO_SYNC_DEFAULT_DEPTH 16
`define FIFO_SYNC_DEFAULT_ALMOST_FULL_THRESHOLD 15
`define FIFO_SYNC_DEFAULT_ALMOST_EMPTY_THRESHOLD 1
`define FIFO_SYNC_DEFAULT_USE_OUTPUT_REGISTER 0
`define FIFO_SYNC_DEFAULT_USE_APB 1
`define FIFO_SYNC_DEFAULT_USE_ECC 0
`define FIFO_SYNC_DEFAULT_CLOCK_FREQ_MHZ 50

`endif
