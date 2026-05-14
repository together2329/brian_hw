// uart_lite_baud_gen.sv — Baud-rate generator
// Implements: cycle_model.baud_generation, parameters.OVERSAMPLE
// OVERSAMPLE = 16; baud_tick is single PCLK cycle pulse
// Baud tick asserts when oversample_counter==0 AND baud_div_counter reaches (baud_div * OVERSAMPLE - 1)
// RX oversample counter 0..15 resets on each baud tick
// baud_div==0 disables baud tick generation

module uart_lite_baud_gen #(
    parameter integer OVERSAMPLE = 16,
    parameter integer BAUD_DIV_W   = 16,
    parameter integer DIV_CNT_W    = 24  // wide enough for 2^16 * OVERSAMPLE
) (
    input  logic                      clk,
    input  logic                      rst_n,
    input  logic [BAUD_DIV_W-1:0]     baud_div,
    // Baud tick output — single cycle pulse
    output logic                      baud_tick,
    // RX oversample counter 0..15 for centre-sampling alignment
    output logic [3:0]                rx_oversample
);

    // Derived baud divisor value
    // threshold = (baud_div * OVERSAMPLE - 1) when baud_div > 0
    // For baud_div==0, no tick is ever generated
    // OVERSAMPLE is a power-of-two; use shift for multiplication
    localparam OVERSAMPLE_SHIFT = $clog2(OVERSAMPLE);
    wire [DIV_CNT_W-1:0] baud_threshold;
    assign baud_threshold = ({8'd0, baud_div} << OVERSAMPLE_SHIFT) - 1'b1;

    // Baud-div counter — increments every PCLK, resets on baud_tick
    logic [DIV_CNT_W-1:0] baud_div_counter;

    wire baud_div_zero;
    assign baud_div_zero = (baud_div == {BAUD_DIV_W{1'b0}});

    // Baud tick generation: single-cycle pulse
    // Tick when: oversample_counter==0, baud_div_counter reaches threshold, baud_div != 0
    wire baud_tick_next;
    assign baud_tick_next = !baud_div_zero && (rx_oversample == 4'd0) && (baud_div_counter == baud_threshold);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_tick <= 1'b0;
        end else begin
            baud_tick <= baud_tick_next;
        end
    end

    // Baud-div counter
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_div_counter <= {DIV_CNT_W{1'b0}};
        end else if (baud_div_zero) begin
            // When baud_div==0, hold counter at 0 (disabled)
            baud_div_counter <= {DIV_CNT_W{1'b0}};
        end else if (baud_tick_next) begin
            // Reset counter on baud tick
            baud_div_counter <= {DIV_CNT_W{1'b0}};
        end else begin
            // Increment every PCLK
            baud_div_counter <= baud_div_counter + 1'b1;
        end
    end

    // RX oversample counter — 0..15, resets on baud tick
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_oversample <= 4'd0;
        end else if (baud_tick_next) begin
            // Reset to 0 on baud tick
            rx_oversample <= 4'd0;
        end else if (!baud_div_zero) begin
            // Increment, wrapping at 15
            rx_oversample <= rx_oversample + 4'd1;
        end else begin
            // Hold at 0 when disabled
            rx_oversample <= 4'd0;
        end
    end

endmodule
