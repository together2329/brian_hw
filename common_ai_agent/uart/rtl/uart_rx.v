// =============================================================================
// uart_rx.v — UART Receiver with FIFO and 3-of-16 Majority Sampler
// =============================================================================
`default_nettype none
`include "uart_defines.vh"

module uart_rx (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        rx_en,
    input  wire [2:0]  data_bits,
    input  wire        parity_en,
    input  wire        parity_odd,
    input  wire        baud_tick,
    input  wire        rx_in,
    output wire [7:0]  rx_data,
    output wire        fifo_empty,
    output wire        fifo_not_empty,
    output wire        rx_active,
    output reg         framing_err,
    output reg         parity_err,
    output reg         overrun_err
);

    // RX FIFO
    localparam integer FIFO_D = `FIFO_DEPTH;
    localparam integer PTR_W  = `PTR_W;

    reg [7:0]  fifo_mem [0:FIFO_D-1];
    reg [PTR_W-1:0] wr_ptr, rd_ptr;

    wire fifo_empty_w = (wr_ptr == rd_ptr);
    wire fifo_full_w  = (wr_ptr[PTR_W-2:0] == rd_ptr[PTR_W-2:0]) &&
                        (wr_ptr[PTR_W-1] != rd_ptr[PTR_W-1]);

    assign fifo_empty    = fifo_empty_w;
    assign fifo_not_empty = ~fifo_empty_w;
    assign rx_data       = fifo_mem[rd_ptr[PTR_W-2:0]];

    // Edge detection on rx_in
    reg rx_sync_0;
    wire rx_falling = rx_sync_0 & ~rx_in;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) rx_sync_0 <= 1'b1;
        else        rx_sync_0 <= rx_in;
    end

    // 3-of-16 majority sampler
    reg [3:0] sample_cnt;
    reg [1:0] vote;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_cnt <= 4'd0;
            vote       <= 2'd0;
        end else if (baud_tick) begin
            if (sample_cnt == 4'd15)
                sample_cnt <= 4'd0;
            else
                sample_cnt <= sample_cnt + 4'd1;
            if (sample_cnt == 4'd6 || sample_cnt == 4'd7 || sample_cnt == 4'd8) begin
                if (rx_in)
                    vote <= {1'b0, vote[0]} + 2'd1;
            end
        end
    end

    wire sample_bit = vote[1];

    // Shift register
    reg [7:0] rx_shift_reg;

    // RX FSM
    reg [2:0] state, next_state;
    reg [3:0] bit_cnt;

    assign rx_active = (state != `RX_IDLE);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) state <= `RX_IDLE;
        else        state <= next_state;
    end

    always @(*) begin
        next_state = state;
        case (state)
            `RX_IDLE:       if (rx_en && rx_falling)   next_state = `RX_START_SYNC;
            `RX_START_SYNC: if (baud_tick && sample_cnt == 4'd7)
                                                      next_state = `RX_START_CHK;
            `RX_START_CHK:  if (~sample_bit)           next_state = `RX_DATA;
                            else                       next_state = `RX_IDLE;
            `RX_DATA:       if (baud_tick && sample_cnt == 4'd7 &&
                                bit_cnt >= {1'b0, data_bits})
                                                      next_state = (parity_en) ? `RX_PARITY : `RX_STOP_CHK;
            `RX_PARITY:     if (baud_tick && sample_cnt == 4'd7)
                                                      next_state = `RX_STOP_CHK;
            `RX_STOP_CHK:   if (baud_tick && sample_cnt == 4'd7)
                                                      next_state = `RX_DONE;
            `RX_DONE:                                  next_state = `RX_IDLE;
            default:                                  next_state = `RX_IDLE;
        endcase
    end

    // Datapath
    reg rx_fifo_wr;
    reg parity_calc_rx;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr        <= {(PTR_W){1'b0}};
            rd_ptr        <= {(PTR_W){1'b0}};
            rx_shift_reg  <= 8'd0;
            bit_cnt       <= 4'd0;
            framing_err   <= 1'b0;
            parity_err    <= 1'b0;
            overrun_err   <= 1'b0;
            rx_fifo_wr    <= 1'b0;
            parity_calc_rx<= 1'b0;
        end else begin
            framing_err <= 1'b0;
            parity_err  <= 1'b0;
            overrun_err <= 1'b0;
            rx_fifo_wr  <= 1'b0;

            case (state)
                `RX_IDLE: begin
                    bit_cnt <= 4'd0;
                    vote    <= 2'd0;
                end
                `RX_DATA: begin
                    if (baud_tick && sample_cnt == 4'd7) begin
                        rx_shift_reg  <= {sample_bit, rx_shift_reg[7:1]};
                        parity_calc_rx<= parity_calc_rx ^ sample_bit;
                        bit_cnt <= bit_cnt + 4'd1;
                    end
                end
                `RX_PARITY: begin
                    if (baud_tick && sample_cnt == 4'd7) begin
                        if (parity_calc_rx ^ sample_bit ^ parity_odd)
                            parity_err <= 1'b1;
                    end
                end
                `RX_STOP_CHK: begin
                    if (baud_tick && sample_cnt == 4'd7) begin
                        if (!sample_bit)
                            framing_err <= 1'b1;
                        rx_fifo_wr <= 1'b1;
                        if (fifo_full_w)
                            overrun_err <= 1'b1;
                    end
                end
                default: ;
            endcase

            // FIFO write
            if (rx_fifo_wr && !fifo_full_w) begin
                fifo_mem[wr_ptr[PTR_W-2:0]] <= rx_shift_reg;
                wr_ptr <= wr_ptr + {{(PTR_W-1){1'b0}}, 1'b1};
            end
        end
    end

endmodule

`default_nettype wire
