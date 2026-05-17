// pl330realverify_param.vh
// Shared SSOT-derived parameters for pl330realverify RTL modules.

`ifndef PL330REALVERIFY_PARAM_VH
`define PL330REALVERIFY_PARAM_VH

parameter integer DATA_WIDTH        = 64;
parameter integer ADDR_WIDTH        = 32;
parameter integer ID_WIDTH          = 6;
parameter integer NUM_CHANNELS      = 8;
parameter integer NUM_EVENTS        = 32;
parameter integer REG_ADDR_WIDTH    = 12;
parameter integer MAX_BURST_LEN     = 16;
parameter integer CLOCK_FREQ_MHZ    = 500;
parameter integer SUPPORT_UNALIGNED = 0;

`endif
