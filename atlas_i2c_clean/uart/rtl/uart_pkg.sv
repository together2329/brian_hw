// =============================================================================
// uart_pkg.sv — Shared parameter documentation module
// =============================================================================
// NOTE: SystemVerilog `package` is BANNED by project convention.
// This module documents shared constants. Each submodule replicates the
// localparams it needs or receives values via module #() parameters.
// This module is NOT instantiated — it exists solely for documentation
// and to satisfy the filelist.
// =============================================================================

module uart_pkg #(
    parameter integer DATA_WIDTH      = 8,
    parameter integer BAUD_DIV        = 16,
    parameter integer FIFO_DEPTH      = 16,
    parameter integer APB_ADDR_WIDTH  = 4,
    parameter integer CLOCK_FREQ_MHZ  = 100,
    parameter bit     HAS_IRQ         = 1'b1
) (
    input  logic dummy_clk    // unused — keeps module synthesizable
);

    // ---- Register offsets (word-indexed, paddr[APB_ADDR_WIDTH-1:2]) ----
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_CTRL    = {(APB_ADDR_WIDTH){1'b0}};
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_STATUS  = {{(APB_ADDR_WIDTH-2){1'b0}}, 2'b01};
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_TX_DATA = {{(APB_ADDR_WIDTH-2){1'b0}}, 2'b10};
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_RX_DATA = {{(APB_ADDR_WIDTH-2){1'b0}}, 2'b11};

    // ---- CTRL register bit positions ----
    localparam integer CTRL_TX_EN_BIT     = 0;
    localparam integer CTRL_RX_EN_BIT     = 1;
    localparam integer CTRL_FIFO_EN_BIT   = 2;
    localparam integer CTRL_PARITY_EN_BIT = 3;
    localparam integer CTRL_PARITY_ODD_BIT= 4;
    localparam integer CTRL_STOP_BITS_BIT = 5;
    localparam integer CTRL_BAUD_DIV_HI   = 8;   // baud_div[15:8]
    localparam integer CTRL_BAUD_DIV_LO   = 15;

    // ---- STATUS register bit positions ----
    localparam integer STAT_TX_EMPTY_BIT   = 0;
    localparam integer STAT_TX_FULL_BIT    = 1;
    localparam integer STAT_RX_EMPTY_BIT   = 2;
    localparam integer STAT_RX_FULL_BIT    = 3;
    localparam integer STAT_TX_BUSY_BIT    = 4;
    localparam integer STAT_RX_BUSY_BIT    = 5;
    localparam integer STAT_FRAMING_BIT    = 6;
    localparam integer STAT_OVERRUN_BIT    = 7;

endmodule
