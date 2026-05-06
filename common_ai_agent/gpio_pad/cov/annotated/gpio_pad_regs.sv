//      // verilator_coverage annotation
        
        `default_nettype none
        
        module gpio_pad_regs #(
            parameter int NUM_PADS        = 32,
            parameter int APB_ADDR_WIDTH  = 12,
            parameter int APB_DATA_WIDTH  = 32
        ) (
            // Clock and Reset
%000000     input  logic                             pclk,
%000000     input  logic                             presetn,       // active-low async
        
            // APB Slave Interface
%000000     input  logic [APB_ADDR_WIDTH-1:0]        paddr,
%000000     input  logic                             psel,
%000000     input  logic                             penable,
%000000     input  logic                             pwrite,
%000000     input  logic [APB_DATA_WIDTH-1:0]        pwdata,
%000000     input  logic [(APB_DATA_WIDTH/8)-1:0]    pstrb,         // byte strobes (unused for 32b)
%000000     output logic [APB_DATA_WIDTH-1:0]        prdata,
%000001     output logic                             pready,
%000000     output logic                             pslverr,
        
            // Core Interface — register values
%000000     output logic [NUM_PADS-1:0]              dir,
%000000     output logic [NUM_PADS-1:0]              out_val,
%000000     output logic [NUM_PADS-1:0]              inten,
        
            // Synchronized input from core
%000000     input  logic [NUM_PADS-1:0]              in_sync,
        
            // Edge detect pulses from core (one-cycle pulses per bit)
%000000     input  logic [NUM_PADS-1:0]              edge_pulse,
        
            // Interrupt output
%000000     output logic                             gpio_irq
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
%000000     logic [NUM_PADS-1:0] dir_reg;
%000000     logic [NUM_PADS-1:0] out_reg;
%000000     logic [NUM_PADS-1:0] inten_reg;
%000000     logic [NUM_PADS-1:0] intstat_reg;   // latched edge status
        
            // =========================================================================
            // APB Ready / Error (simple — always ready, no error)
            // =========================================================================
%000001     always_comb begin
%000001         pready  = 1'b1;
%000001         pslverr = 1'b0;
            end
        
            // =========================================================================
            // APB Write Decode
            // =========================================================================
%000000     logic apb_write_valid;
            assign apb_write_valid = psel && penable && pwrite;
        
            // =========================================================================
            // Register Write Logic (FF block)
            // =========================================================================
%000000     always_ff @(posedge pclk or negedge presetn) begin
%000000         if (!presetn) begin
%000000             dir_reg    <= '0;
%000000             out_reg    <= '0;
%000000             inten_reg  <= '0;
%000000             intstat_reg <= '0;
%000000         end else begin
                    // Edge detect: latch any edge pulses into INTSTAT
%000000             if (|edge_pulse) begin
%000000                 intstat_reg <= intstat_reg | edge_pulse;
                    end
        
                    // APB writes
%000000             if (apb_write_valid) begin
%000000                 case (paddr)
%000000                     ADDR_DIR:      dir_reg   <= pwdata[NUM_PADS-1:0];
%000000                     ADDR_OUT:      out_reg   <= pwdata[NUM_PADS-1:0];
%000000                     ADDR_INTEN:    inten_reg <= pwdata[NUM_PADS-1:0];
                            // INTCLEAR: Write-1-to-clear INTSTAT
%000000                     ADDR_INTCLEAR: intstat_reg <= intstat_reg & ~pwdata[NUM_PADS-1:0];
%000000                     default: begin
                                // No other writable registers
                            end
                        endcase
                    end
                end
            end
        
            // =========================================================================
            // APB Read Mux
            // =========================================================================
 000201     always_comb begin
 000201         prdata = '0;
~000201         if (psel && penable && !pwrite) begin
%000000             case (paddr)
%000000                 ADDR_DIR:      prdata = {{(32-NUM_PADS){1'b0}}, dir_reg};
%000000                 ADDR_OUT:      prdata = {{(32-NUM_PADS){1'b0}}, out_reg};
%000000                 ADDR_IN:       prdata = {{(32-NUM_PADS){1'b0}}, in_sync};
%000000                 ADDR_INTEN:    prdata = {{(32-NUM_PADS){1'b0}}, inten_reg};
%000000                 ADDR_INTSTAT:  prdata = {{(32-NUM_PADS){1'b0}}, intstat_reg};
%000000                 ADDR_INTCLEAR: prdata = '0;  // write-only read returns 0
%000000                 default:       prdata = '0;
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
        
