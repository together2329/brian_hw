
`default_nettype none

module gpio_pad_regs #(
    parameter int NUM_PADS        = 32,
    parameter int APB_ADDR_WIDTH  = 12,
    parameter int APB_DATA_WIDTH  = 32
) (
    // Clock and Reset
    input  logic                             pclk,
    input  logic                             presetn,       // active-low async

    // APB Slave Interface
    input  logic [APB_ADDR_WIDTH-1:0]        paddr,
    input  logic                             psel,
    input  logic                             penable,
    input  logic                             pwrite,
    input  logic [APB_DATA_WIDTH-1:0]        pwdata,
    input  logic [(APB_DATA_WIDTH/8)-1:0]    pstrb,         // byte strobes (unused for 32b)
    output logic [APB_DATA_WIDTH-1:0]        prdata,
    output logic                             pready,
    output logic                             pslverr,

    // Core Interface — register values
    output logic [NUM_PADS-1:0]              dir,
    output logic [NUM_PADS-1:0]              out_val,
    output logic [NUM_PADS-1:0]              inten,

    // Synchronized input from core
    input  logic [NUM_PADS-1:0]              in_sync,

    // Edge detect pulses from core (one-cycle pulses per bit)
    input  logic [NUM_PADS-1:0]              edge_pulse,

    // Interrupt output
    output logic                             gpio_irq
);

    // =========================================================================
    // Register addresses (imported from package conceptually — hardcoded here)
    // =========================================================================
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_DIR      = 12'h000;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_OUT      = 12'h004;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_IN       = 12'h008;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_INTEN    = 12'h00C;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_INTSTAT  = 12'h010;
    localparam logic [APB_ADDR_WIDTH-1:0] ADDR_INTCLEAR = 12'h014;

    // =========================================================================
    // Register storage
    // =========================================================================
    logic [NUM_PADS-1:0] dir_reg;
    logic [NUM_PADS-1:0] out_reg;
    logic [NUM_PADS-1:0] inten_reg;
    logic [NUM_PADS-1:0] intstat_reg;   // latched edge status

    // =========================================================================
    // APB Ready / Error (simple — always ready, no error)
    // =========================================================================
    always_comb begin
        pready  = 1'b1;
        pslverr = 1'b0;
    end

    // =========================================================================
    // APB Write Decode
    // =========================================================================
    logic apb_write_valid;
    assign apb_write_valid = psel && penable && pwrite;

    // =========================================================================
    // Register Write Logic (FF block)
    // =========================================================================
    always_ff @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            dir_reg    <= '0;
            out_reg    <= '0;
            inten_reg  <= '0;
            intstat_reg <= '0;
        end else begin
            // Edge detect: latch any edge pulses into INTSTAT
            if (|edge_pulse) begin
                intstat_reg <= intstat_reg | edge_pulse;
            end

            // APB writes
            if (apb_write_valid) begin
                case (paddr)
                    ADDR_DIR:      dir_reg   <= pwdata[NUM_PADS-1:0];
                    ADDR_OUT:      out_reg   <= pwdata[NUM_PADS-1:0];
                    ADDR_INTEN:    inten_reg <= pwdata[NUM_PADS-1:0];
                    // INTCLEAR: Write-1-to-clear INTSTAT
                    ADDR_INTCLEAR: intstat_reg <= intstat_reg & ~pwdata[NUM_PADS-1:0];
                    default: begin
                        // No other writable registers
                    end
                endcase
            end
        end
    end

    // =========================================================================
    // APB Read Mux
    // =========================================================================
    always_comb begin
        prdata = '0;
        if (psel && penable && !pwrite) begin
            case (paddr)
                ADDR_DIR:      prdata = {{(32-NUM_PADS){1'b0}}, dir_reg};
                ADDR_OUT:      prdata = {{(32-NUM_PADS){1'b0}}, out_reg};
                ADDR_IN:       prdata = {{(32-NUM_PADS){1'b0}}, in_sync};
                ADDR_INTEN:    prdata = {{(32-NUM_PADS){1'b0}}, inten_reg};
                ADDR_INTSTAT:  prdata = {{(32-NUM_PADS){1'b0}}, intstat_reg};
                ADDR_INTCLEAR: prdata = '0;  // write-only read returns 0
                default:       prdata = '0;
            endcase
        end
    end

    // =========================================================================
    // Interrupt Generation
    // =========================================================================
    assign gpio_irq = |(inten_reg & intstat_reg);

    // =========================================================================
    // Output assignments
    // =========================================================================
    assign dir     = dir_reg;
    assign out_val = out_reg;
    assign inten   = inten_reg;

endmodule : gpio_pad_regs

`default_nettype wire
