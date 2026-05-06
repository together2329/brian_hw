
`default_nettype none

package gpio_pad_pkg;
    // =========================================================================
    // gpio_pad_pkg — Parameter Package
    // =========================================================================
    // Parameters from gpio_pad SSOT YAML §2
    localparam int NUM_PADS        = 32;    // Number of GPIO pads
    localparam int APB_ADDR_WIDTH  = 12;    // APB address bus width
    localparam int APB_DATA_WIDTH  = 32;    // APB data bus width

    // Register offsets (SSOT §9)
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_DIR      = 12'h000;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_OUT      = 12'h004;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_IN       = 12'h008;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_INTEN    = 12'h00C;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_INTSTAT  = 12'h010;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_INTCLEAR = 12'h014;

endpackage : gpio_pad_pkg

`default_nettype wire
