
`default_nettype none

module gpio_pad_core #(
    parameter int NUM_PADS = 32
) (
    // Clock and Reset
    input  logic                     pclk,
    input  logic                     presetn,       // active-low async

    // Pad Interface
    input  logic [NUM_PADS-1:0]      gpio_in,
    output logic [NUM_PADS-1:0]      gpio_out,
    output logic [NUM_PADS-1:0]      gpio_oe,

    // Register Interface from regs block
    input  logic [NUM_PADS-1:0]      dir,
    input  logic [NUM_PADS-1:0]      out_val,

    // Synchronized input to regs block
    output logic [NUM_PADS-1:0]      in_sync,

    // Edge detect pulses to regs block
    output logic [NUM_PADS-1:0]      edge_pulse
);

    // =========================================================================
    // 2-DFF Synchronizer for gpio_in
    // =========================================================================
    logic [NUM_PADS-1:0] in_sync_ff1;

    always_ff @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            in_sync_ff1 <= '0;
            in_sync     <= '0;
        end else begin
            in_sync_ff1 <= gpio_in;
            in_sync     <= in_sync_ff1;
        end
    end

    // =========================================================================
    // Edge Detection: detect toggle of in_sync between cycles
    // =========================================================================
    logic [NUM_PADS-1:0] in_prev;

    always_ff @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            in_prev <= '0;
        end else begin
            in_prev <= in_sync;
        end
    end

    // edge_pulse is high for one cycle when in_sync changes
    assign edge_pulse = in_sync ^ in_prev;

    // =========================================================================
    // Pad Output Drive
    //   gpio_oe = dir (1 = output enabled)
    //   gpio_out = out_val driven only when dir=1
    // =========================================================================
    always_comb begin
        gpio_oe  = dir;
        gpio_out = '0;
        // Only drive gpio_out where dir is set
        for (int i = 0; i < NUM_PADS; i++) begin
            if (dir[i])
                gpio_out[i] = out_val[i];
        end
    end

endmodule : gpio_pad_core

`default_nettype wire
