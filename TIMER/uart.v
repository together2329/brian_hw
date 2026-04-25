
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: uart
// Description: Configurable baud rate UART core with TX and RX.
//
// Format: 8N1 (8 data bits, no parity, 1 stop bit)
//
// TX: start bit (0) -> 8 data bits (LSB first) -> stop bit (1)
// RX: start bit detect -> mid-bit sampling -> 8 data bits -> stop bit check
//
// Ports:
//   clk       - Rising-edge clock
//   rst_n     - Active-low synchronous reset
//   tx_enable - TX enable (active high)
//   rx_enable - RX enable (active high)
//   tx_data   - 8-bit data to transmit
//   tx_start  - Start transmission pulse (1 clock cycle)
//   rx_in     - Serial data input
//   tx_out    - Serial data output
//   rx_data   - 8-bit received data
//   rx_ready  - New byte received (cleared when rx_read is asserted)
//   rx_read   - Acknowledge rx_data (clears rx_ready)
//   tx_busy   - TX is actively sending
//   tx_done   - TX completed pulse (1 clock cycle)
//   baud_div  - Baud rate divisor (clocks per bit period)
//----------------------------------------------------------------------------

module uart (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         tx_enable,
    input  wire         rx_enable,
    input  wire  [7:0]  tx_data,
    input  wire         tx_start,
    input  wire         rx_in,
    output wire         tx_out,
    output reg  [7:0]   rx_data,
    output reg          rx_ready,
    input  wire         rx_read,
    output reg          tx_busy,
    output reg          tx_done,
    output reg          rx_overflow,
    input  wire  [15:0] baud_div
);

    //==========================================================================
    // Baud Rate Generator
    //==========================================================================
    reg [15:0] baud_cnt;
    wire       baud_tick = (baud_cnt == baud_div - 16'd1);

    always @(posedge clk) begin
        if (!rst_n)
            baud_cnt <= 16'd0;
        else if (baud_tick)
            baud_cnt <= 16'd0;
        else
            baud_cnt <= baud_cnt + 16'd1;
    end

    //==========================================================================
    // TX State Machine
    //==========================================================================
    localparam TX_IDLE  = 3'd0;
    localparam TX_START = 3'd1;
    localparam TX_DATA  = 3'd2;
    localparam TX_STOP  = 3'd3;

    reg [2:0]  tx_state;
    reg [7:0]  tx_shift;
    reg [2:0]  tx_bit_cnt;

    always @(posedge clk) begin
        if (!rst_n) begin
            tx_state   <= TX_IDLE;
            tx_shift   <= 8'd0;
            tx_bit_cnt <= 3'd0;
            tx_busy    <= 1'b0;
            tx_done    <= 1'b0;
        end else begin
            tx_done <= 1'b0;  // Default: clear pulse

            case (tx_state)
                TX_IDLE: begin
                    if (tx_enable && tx_start) begin
                        tx_shift <= tx_data;
                        tx_state <= TX_START;
                        tx_busy  <= 1'b1;
                    end
                end

                TX_START: begin
                    if (baud_tick) begin
                        tx_state <= TX_DATA;
                        tx_bit_cnt <= 3'd0;
                    end
                end

                TX_DATA: begin
                    if (baud_tick) begin
                        tx_shift <= {1'b0, tx_shift[7:1]};  // Shift right (LSB first)
                        tx_bit_cnt <= tx_bit_cnt + 3'd1;
                        if (tx_bit_cnt == 3'd7)
                            tx_state <= TX_STOP;
                    end
                end

                TX_STOP: begin
                    if (baud_tick) begin
                        tx_state <= TX_IDLE;
                        tx_busy  <= 1'b0;
                        tx_done  <= 1'b1;
                    end
                end

                default: tx_state <= TX_IDLE;
            endcase
        end
    end

    // TX output: idle=1 (mark), start=0 (space), data from shift reg, stop=1
    assign tx_out = (tx_state == TX_IDLE || tx_state == TX_STOP) ? 1'b1 :
                    (tx_state == TX_START) ? 1'b0 :
                    tx_shift[0];  // LSB first

    //==========================================================================
    // RX State Machine
    //==========================================================================
    localparam RX_IDLE      = 3'd0;
    localparam RX_START     = 3'd1;
    localparam RX_DATA      = 3'd2;
    localparam RX_STOP      = 3'd3;

    reg [2:0]  rx_state;
    reg [7:0]  rx_shift;
    reg [2:0]  rx_bit_cnt;
    reg [15:0] rx_cnt;
    reg        rx_sync;       // Synchronizer for rx_in
    reg        rx_sync_d;     // Delayed sync for edge detect

    // Double-flop synchronizer for rx_in
    always @(posedge clk) begin
        if (!rst_n) begin
            rx_sync   <= 1'b1;  // Idle high
            rx_sync_d <= 1'b1;
        end else begin
            rx_sync   <= rx_in;
            rx_sync_d <= rx_sync;
        end
    end

    // Start bit detect: falling edge on synchronized rx_in
    wire rx_falling = rx_sync_d && !rx_sync;

    always @(posedge clk) begin
        if (!rst_n) begin
            rx_state    <= RX_IDLE;
            rx_shift    <= 8'd0;
            rx_bit_cnt  <= 3'd0;
            rx_cnt      <= 16'd0;
            rx_data     <= 8'd0;
            rx_ready    <= 1'b0;
            rx_overflow <= 1'b0;
        end else begin
            // Clear rx_ready on read
            if (rx_read)
                rx_ready <= 1'b0;

            case (rx_state)
                RX_IDLE: begin
                    if (rx_enable && rx_falling) begin
                        rx_state <= RX_START;
                        rx_cnt   <= 16'd0;
                    end
                end

                RX_START: begin
                    // Wait half baud period to reach mid-bit
                    if (rx_cnt == (baud_div >> 1) - 16'd1) begin
                        if (rx_sync == 1'b0) begin
                            // Valid start bit, sample at mid-bit
                            rx_state   <= RX_DATA;
                            rx_bit_cnt <= 3'd0;
                            rx_cnt     <= 16'd0;
                        end else begin
                            // False start, go back to idle
                            rx_state <= RX_IDLE;
                        end
                    end else begin
                        rx_cnt <= rx_cnt + 16'd1;
                    end
                end

                RX_DATA: begin
                    // Sample each bit at full baud period (mid-bit)
                    if (rx_cnt == baud_div - 16'd1) begin
                        rx_shift <= {rx_sync, rx_shift[7:1]};  // Shift in LSB first
                        rx_cnt   <= 16'd0;
                        rx_bit_cnt <= rx_bit_cnt + 3'd1;
                        if (rx_bit_cnt == 3'd7)
                            rx_state <= RX_STOP;
                    end else begin
                        rx_cnt <= rx_cnt + 16'd1;
                    end
                end

                RX_STOP: begin
                    // Wait one full baud period to mid-bit of stop
                    if (rx_cnt == baud_div - 16'd1) begin
                        rx_state <= RX_IDLE;
                        if (rx_sync == 1'b1) begin
                            // Valid stop bit, data is good
                            if (rx_ready) begin
                                rx_overflow <= 1'b1;  // Previous byte not read
                            end
                            rx_data  <= rx_shift;
                            rx_ready <= 1'b1;
                        end
                        // If stop bit is 0 (framing error), discard
                    end else begin
                        rx_cnt <= rx_cnt + 16'd1;
                    end
                end

                default: rx_state <= RX_IDLE;
            endcase
        end
    end

endmodule
