//      // verilator_coverage annotation
        
        `default_nettype none
        
        module gpio_pad_core #(
            parameter int NUM_PADS = 32
        ) (
            // Clock and Reset
%000000     input  logic                     pclk,
%000000     input  logic                     presetn,       // active-low async
        
            // Pad Interface
%000000     input  logic [NUM_PADS-1:0]      gpio_in,
%000000     output logic [NUM_PADS-1:0]      gpio_out,
%000000     output logic [NUM_PADS-1:0]      gpio_oe,
        
            // Register Interface from regs block
%000000     input  logic [NUM_PADS-1:0]      dir,
%000000     input  logic [NUM_PADS-1:0]      out_val,
        
            // Synchronized input to regs block
%000000     output logic [NUM_PADS-1:0]      in_sync,
        
            // Edge detect pulses to regs block
%000000     output logic [NUM_PADS-1:0]      edge_pulse
        );
        
            // =========================================================================
            // 2-DFF Synchronizer for gpio_in
            // =========================================================================
%000000     logic [NUM_PADS-1:0] in_sync_ff1;
        
%000000     always_ff @(posedge pclk or negedge presetn) begin
%000000         if (!presetn) begin
%000000             in_sync_ff1 <= '0;
%000000             in_sync     <= '0;
%000000         end else begin
%000000             in_sync_ff1 <= gpio_in;
%000000             in_sync     <= in_sync_ff1;
                end
            end
        
            // =========================================================================
            // Edge Detection: detect toggle of in_sync between cycles
            // =========================================================================
%000000     logic [NUM_PADS-1:0] in_prev;
        
%000000     always_ff @(posedge pclk or negedge presetn) begin
%000000         if (!presetn) begin
%000000             in_prev <= '0;
%000000         end else begin
%000000             in_prev <= in_sync;
                end
            end
        
            // edge_pulse is high for one cycle when in_sync changes
            assign edge_pulse = in_sync ^ in_prev;
        
            // =========================================================================
            // Pad Output Drive
            //   gpio_oe = dir (1 = output enabled)
            //   gpio_out = out_val driven only when dir=1
            // =========================================================================
%000001     always_comb begin
%000001         gpio_oe  = dir;
%000001         gpio_out = '0;
                // Only drive gpio_out where dir is set
~000032         for (int i = 0; i < NUM_PADS; i++) begin
~000032             if (dir[i])
%000000                 gpio_out[i] = out_val[i];
                end
            end
        
        endmodule : gpio_pad_core
        
        `default_nettype wire
        
