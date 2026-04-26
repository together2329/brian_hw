
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: spi
// Description: SPI master core with configurable CPOL/CPHA and clock divider.
//
// Supports all 4 SPI modes (CPOL/CPHA combinations).
// 8-bit transfers, MSB first.
//
// SPI Modes:
//   Mode 0: CPOL=0, CPHA=0 - SCK idle low,  sample on leading  (rising)
//   Mode 1: CPOL=0, CPHA=1 - SCK idle low,  sample on trailing (falling)
//   Mode 2: CPOL=1, CPHA=0 - SCK idle high, sample on leading  (falling)
//   Mode 3: CPOL=1, CPHA=1 - SCK idle high, sample on trailing (rising)
//
// Ports:
//   clk      - Rising-edge system clock
//   rst_n    - Active-low synchronous reset
//   enable   - SPI enable (active high)
//   start    - Start transfer pulse (1 clock cycle)
//   tx_data  - 8-bit data to transmit
//   rx_data  - 8-bit received data (valid when done=1)
//   busy     - Transfer in progress
//   done     - Transfer completed pulse (1 clock cycle)
//   miso     - Master In Slave Out (serial data input)
//   mosi     - Master Out Slave In (serial data output)
//   sck      - Serial clock output
//   cs_n     - Chip select (active low, asserted during transfer)
//   cpol     - Clock polarity
//   cpha     - Clock phase
//   clk_div  - Clock divider (system clocks per SCK half-period)
//----------------------------------------------------------------------------

module spi (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         enable,
    input  wire         start,
    input  wire  [7:0]  tx_data,
    output reg  [7:0]   rx_data,
    output reg          busy,
    output reg          done,
    input  wire         miso,
    output wire         mosi,
    output wire         sck,
    output wire         cs_n,
    input  wire         cpol,
    input  wire         cpha,
    input  wire  [15:0] clk_div
);

    //==========================================================================
    // FSM states
    //==========================================================================
    localparam IDLE     = 1'b0;
    localparam TRANSFER = 1'b1;

    reg        state;
    reg [15:0] clk_cnt;
    reg        sck_reg;
    reg [3:0]  edge_cnt;      // 0-15 for 16 SCK half-edges (8 bits)
    reg [7:0]  shift_reg;     // TX shift register
    reg [7:0]  rx_shift;      // RX shift register
    reg        mosi_reg;

    //==========================================================================
    // Output assignments
    //==========================================================================
    // SCK idle = cpol, toggles during transfer
    assign sck  = sck_reg ^ cpol;
    assign mosi = mosi_reg;
    assign cs_n = (state == TRANSFER) ? 1'b0 : 1'b1;

    //==========================================================================
    // Main FSM
    //==========================================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            state     <= IDLE;
            clk_cnt   <= 16'd0;
            sck_reg   <= 1'b0;
            edge_cnt  <= 4'd0;
            shift_reg <= 8'd0;
            rx_shift  <= 8'd0;
            rx_data   <= 8'd0;
            busy      <= 1'b0;
            done      <= 1'b0;
            mosi_reg  <= 1'b1;
        end else begin
            done <= 1'b0;  // Default: clear pulse

            case (state)
                //--------------------------------------------------------------
                IDLE: begin
                    if (enable && start) begin
                        shift_reg <= tx_data;
                        busy      <= 1'b1;
                        clk_cnt   <= 16'd0;
                        edge_cnt  <= 4'd0;
                        sck_reg   <= 1'b0;

                        if (cpha == 1'b0) begin
                            // CPHA=0: MOSI must be valid before first SCK edge
                            mosi_reg <= tx_data[7];  // MSB first
                        end

                        state <= TRANSFER;
                    end
                end

                //--------------------------------------------------------------
                TRANSFER: begin
                    if (clk_cnt == clk_div - 16'd1) begin
                        clk_cnt <= 16'd0;

                        // Toggle SCK on each tick
                        sck_reg <= ~sck_reg;

                        // Perform shift/sample based on edge count and CPHA
                        if (cpha == 1'b0) begin
                            // CPHA=0: even edges = sample, odd edges = shift
                            if (edge_cnt[0] == 1'b0) begin
                                // Sample MISO on leading edge
                                rx_shift <= {rx_shift[6:0], miso};
                            end else begin
                                // Shift out next MOSI bit on trailing edge
                                mosi_reg  <= shift_reg[6];
                                shift_reg <= {shift_reg[6:0], 1'b0};
                            end
                        end else begin
                            // CPHA=1: even edges = shift, odd edges = sample
                            if (edge_cnt[0] == 1'b0) begin
                                // Shift out MOSI bit on leading edge
                                mosi_reg  <= shift_reg[7];
                                shift_reg <= {shift_reg[6:0], 1'b0};
                            end else begin
                                // Sample MISO on trailing edge
                                rx_shift <= {rx_shift[6:0], miso};
                            end
                        end

                        // Check if transfer is complete (16 half-edges = 8 bits)
                        if (edge_cnt == 4'd15) begin
                            state <= IDLE;
                            busy  <= 1'b0;
                            done  <= 1'b1;

                            // Capture RX data:
                            // CPHA=0: last sample was at edge 14, rx_shift is complete
                            // CPHA=1: last sample is at edge 15 (now), assemble directly
                            if (cpha == 1'b1)
                                rx_data <= {rx_shift[6:0], miso};
                            else
                                rx_data <= rx_shift;
                        end

                        edge_cnt <= edge_cnt + 4'd1;
                    end else begin
                        clk_cnt <= clk_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                default: state <= IDLE;
            endcase
        end
    end

endmodule
