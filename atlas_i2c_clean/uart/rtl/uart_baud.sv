// =============================================================================
// uart_baud.sv — Baud-rate tick generator
// =============================================================================
// Generates a 1-cycle pulse (baud_tick_o) every baud_div_i system clock
// cycles. The divisor is sourced from the CTRL register baud_div field.
// A divisor of 0 is treated as 256 (wrap-around of 8-bit counter).
// =============================================================================

module uart_baud #(
    parameter integer BAUD_DIV = 16   // default oversampling divisor
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic [7:0]  baud_div_i,   // from CTRL[15:8]
    output logic        baud_tick_o   // 1-cycle pulse per baud period
);

    // Internal counter width: enough to hold max divisor 255
    logic [7:0] counter_q;

    // Effective divisor: treat 0 as 256
    logic [7:0] div;
    assign div = (baud_div_i == 8'd0) ? 8'd255 : baud_div_i;

    // Counter logic — free-running, wraps at div
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter_q <= 8'd0;
        end else begin
            if (counter_q >= div) begin
                counter_q <= 8'd0;
            end else begin
                counter_q <= counter_q + 8'd1;
            end
        end
    end

    // Tick output — asserted for 1 cycle when counter resets
    assign baud_tick_o = (counter_q >= div);

endmodule
