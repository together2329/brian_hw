`include "atcwdt200_param.vh"

module atcwdt200_sync (
    input  logic pclk,
    input  logic presetn,
    input  logic extclk,
    input  logic wdt_pause,
    output logic extclk_rise,
    output logic wdt_pause_sync
);
    logic extclk_meta;
    logic extclk_sync;
    logic extclk_sync_dly;
    logic pause_meta;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            extclk_meta     <= 1'b0;
            extclk_sync     <= 1'b0;
            extclk_sync_dly <= 1'b0;
            extclk_rise     <= 1'b0;
            pause_meta      <= 1'b0;
            wdt_pause_sync  <= 1'b0;
        end else begin
            extclk_meta     <= extclk;
            extclk_sync     <= extclk_meta;
            extclk_sync_dly <= extclk_sync;
            extclk_rise     <= extclk_sync & ~extclk_sync_dly;
            pause_meta      <= wdt_pause;
            wdt_pause_sync  <= pause_meta;
        end
    end
endmodule
