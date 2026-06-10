// edge_det_cx1.sv
// Rising/falling edge detector with 2-flop synchronizer.
// SSOT: yaml/edge_det_cx1.ssot.yaml
// Obligations: OBL_EDGE_SYNC_001, OBL_EDGE_RISE_001, OBL_EDGE_FALL_001, OBL_EDGE_RESET_001

`timescale 1ns/1ps

module edge_det_cx1 (
    input  wire clk,       // System clock
    input  wire rst_n,     // Active-low async assert / sync deassert reset
    input  wire sig_in,    // Asynchronous input signal
    output wire rise_out,  // 1-cycle pulse on rising edge of sig_in (after sync)
    output wire fall_out   // 1-cycle pulse on falling edge of sig_in (after sync)
);

    // sync_ff FSM: single-state IDLE (no explicit state register; purely sequential pipeline)
    localparam [0:0] IDLE = 1'b0;  // state encoding: reset drives all FFs to IDLE
    reg sync1;
    reg sync2;
    // Previous value for edge detection
    reg prev_sync;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sync1     <= IDLE;
            sync2     <= IDLE;
            prev_sync <= IDLE;
        end else begin
            sync1     <= sig_in;
            sync2     <= sync1;
            prev_sync <= sync2;
        end
    end

    // Rising edge detect: sync2 went 0->1 (OBL_EDGE_RISE_001)
    assign rise_out = sync2 & ~prev_sync;

    // Falling edge detect: sync2 went 1->0 (OBL_EDGE_FALL_001)
    assign fall_out = ~sync2 & prev_sync;

endmodule
