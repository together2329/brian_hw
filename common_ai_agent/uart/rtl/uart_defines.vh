// =============================================================================
// uart_defines.vh — Cross-module constants for UART IP
// =============================================================================
// PROJECT CONVENTION: NO package/endpackage/import. Shared constants via
// this include file with `ifndef guards.
// =============================================================================

`ifndef UART_DEFINES_VH
`define UART_DEFINES_VH

// APB bus width
`define APB_DATA_W     32
`define APB_ADDR_W     12

// FIFO parameters
`define FIFO_DEPTH     16
`define PTR_W          5    // $clog2(FIFO_DEPTH) + 1

// Register offsets
`define ADDR_CTRL       12'h000
`define ADDR_STATUS     12'h004
`define ADDR_BRD        12'h008
`define ADDR_TX_DATA    12'h00C
`define ADDR_RX_DATA    12'h010
`define ADDR_INT_EN     12'h014
`define ADDR_INT_STATUS 12'h018

// TX FSM states
`define TX_IDLE   3'd0
`define TX_START  3'd1
`define TX_DATA   3'd2
`define TX_PARITY 3'd3
`define TX_STOP   3'd4

// RX FSM states
`define RX_IDLE       3'd0
`define RX_START_SYNC 3'd1
`define RX_START_CHK  3'd2
`define RX_DATA       3'd3
`define RX_PARITY     3'd4
`define RX_STOP_CHK   3'd5
`define RX_DONE       3'd6

`endif // UART_DEFINES_VH
