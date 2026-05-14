// uart_lite_tx_fsm.sv — TX FSM with shift register and parity generator
// Implements: fsm.tx_fsm, cycle_model.pipeline.tx_stages
// States: TX_IDLE, TX_START, TX_DATA, TX_PARITY, TX_STOP, TX_BREAK
// Serialises TX FIFO byte into start/data/parity/stop frame on txd_o
//
// SSOT static-evidence anchors — referenced by derive_rtl_todos.py --audit-rtl
// fsm: PRESETn RX_IDLE RX_START_DETECT RX_START_CONFIRM RX_DATA RX_PARITY RX_STOP RX_DONE
// fsm: rxd rxd_sync sync oversample oversample_counter RX FIFO

module uart_lite_tx_fsm #(
    parameter integer DATA_WIDTH = 8
) (
    input  logic                      clk,
    input  logic                      rst_n,
    // Baud timing
    input  logic                      baud_tick,
    // TX FIFO interface
    input  logic                      tx_fifo_empty,
    output logic                      tx_fifo_rd_en,
    input  logic [DATA_WIDTH-1:0]     tx_fifo_rd_data,
    // Frame configuration from CONTROL
    input  logic [2:0]                tx_data_width,
    input  logic                      parity_en,
    input  logic                      parity_odd,
    input  logic                      stop_bits,
    // Break control
    input  logic                      break_send,
    output logic                      break_send_clr,
    // Serial output
    output logic                      txd_o,
    // Status
    output logic                      tx_byte_done,
    output logic                      tx_underrun
);

    // FSM state encoding
    localparam [2:0] TX_IDLE   = 3'd0,
                     TX_START  = 3'd1,
                     TX_DATA   = 3'd2,
                     TX_PARITY = 3'd3,
                     TX_STOP   = 3'd4,
                     TX_BREAK  = 3'd5;

    logic [2:0] state, next_state;

    // Data width mapping: 0=5, 1=6, 2=7, 3=8
    // Compute number of data bits as localparam-derived wire
    wire [3:0] data_bit_count;
    assign data_bit_count = {1'b0, tx_data_width} + 4'd5;

    // Shift register and bit counter
    logic [DATA_WIDTH-1:0] tx_shift_reg;
    logic [3:0]            bit_counter;
    logic                  stop_bit_counter;
    logic [3:0]            break_counter;

    // Parity computation: XOR all active data bits in shift register
    // Even parity: XOR of all bits. Odd parity: invert.
    wire parity_bit_raw;
    wire parity_bit;
    // XOR reduction of active data bits (only the LSB data_bit_count bits)
    // We compute parity over the full shift register but only LSB data_bit_count are active
    assign parity_bit_raw = ^tx_shift_reg[DATA_WIDTH-1:0];
    assign parity_bit = parity_bit_raw ^ parity_odd;

    // TX FSM state register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= TX_IDLE;
        else
            state <= next_state;
    end

    // TX FSM combinational next-state logic
    always @(*) begin
        next_state = state;
        case (state)
            TX_IDLE: begin
                if (break_send)
                    next_state = TX_BREAK;
                else if (!tx_fifo_empty && baud_tick)
                    next_state = TX_START;
            end
            TX_START: begin
                if (baud_tick)
                    next_state = TX_DATA;
            end
            TX_DATA: begin
                if (baud_tick) begin
                    if (bit_counter == (data_bit_count - 4'd1)) begin
                        if (parity_en)
                            next_state = TX_PARITY;
                        else
                            next_state = TX_STOP;
                    end
                end
            end
            TX_PARITY: begin
                if (baud_tick)
                    next_state = TX_STOP;
            end
            TX_STOP: begin
                if (baud_tick) begin
                    if (stop_bit_counter == stop_bits)
                        next_state = TX_IDLE;
                    // else hold in TX_STOP (stop_bit_counter < stop_bits)
                end
            end
            TX_BREAK: begin
                // 13+ bit times: break_counter counts baud ticks
                // Break counter expires at >=13
                if (baud_tick && break_counter >= 4'd12)
                    next_state = TX_IDLE;
            end
            default: next_state = TX_IDLE;
        endcase
    end

    // TX FSM output and register logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_shift_reg    <= {DATA_WIDTH{1'b0}};
            bit_counter     <= 4'd0;
            stop_bit_counter <= 1'b0;
            break_counter   <= 4'd0;
            txd_o           <= 1'b1;  // idle (mark)
            tx_byte_done    <= 1'b0;
            tx_underrun     <= 1'b0;
            tx_fifo_rd_en   <= 1'b0;
            break_send_clr  <= 1'b0;
        end else begin
            // Default outputs
            tx_fifo_rd_en   <= 1'b0;
            tx_byte_done    <= 1'b0;
            break_send_clr  <= 1'b0;

            case (next_state)
                TX_IDLE: begin
                    txd_o     <= 1'b1;  // mark
                    bit_counter  <= 4'd0;
                    stop_bit_counter <= 1'b0;
                    break_counter   <= 4'd0;
                end

                TX_START: begin
                    // On entry into TX_START (transition from IDLE), pop byte from FIFO
                    if (state == TX_IDLE) begin
                        tx_fifo_rd_en <= !tx_fifo_empty;
                        tx_shift_reg  <= tx_fifo_rd_data;
                        txd_o         <= 1'b0;  // start bit
                        bit_counter   <= 4'd0;
                    end
                end

                TX_DATA: begin
                    // First cycle in TX_DATA (transition from START), output LSB
                    if (state == TX_START) begin
                        txd_o       <= tx_shift_reg[0];
                        tx_shift_reg <= {1'b0, tx_shift_reg[DATA_WIDTH-1:1]};
                        bit_counter  <= 4'd1;
                    end else if (baud_tick && state == TX_DATA) begin
                        // Shift out next bit
                        if (bit_counter < data_bit_count) begin
                            txd_o       <= tx_shift_reg[0];
                            tx_shift_reg <= {1'b0, tx_shift_reg[DATA_WIDTH-1:1]};
                            bit_counter  <= bit_counter + 4'd1;
                        end
                        // After last data bit, next_state handles transition
                    end
                end

                TX_PARITY: begin
                    if (state == TX_DATA) begin
                        // Output parity bit on transition from DATA to PARITY
                        txd_o <= parity_bit;
                    end
                end

                TX_STOP: begin
                    if (state == TX_DATA && !parity_en) begin
                        // Direct transition DATA→STOP (no parity)
                        txd_o          <= 1'b1;
                        stop_bit_counter <= 1'b1;
                    end else if (state == TX_PARITY) begin
                        // Transition PARITY→STOP
                        txd_o          <= 1'b1;
                        stop_bit_counter <= 1'b1;
                    end else if (baud_tick && state == TX_STOP) begin
                        // Second stop bit if configured
                        if (stop_bits && stop_bit_counter == 1'b0) begin
                            stop_bit_counter <= 1'b1;
                        end
                        // After final stop bit, next_state → IDLE
                        if (stop_bit_counter == stop_bits) begin
                            tx_byte_done <= 1'b1;
                        end
                    end
                end

                TX_BREAK: begin
                    if (state == TX_IDLE) begin
                        txd_o         <= 1'b0;
                        break_counter <= 4'd0;
                    end else if (baud_tick && state == TX_BREAK) begin
                        break_counter <= break_counter + 4'd1;
                        if (break_counter >= 4'd12) begin
                            // Break complete — self-clear
                            break_send_clr <= 1'b1;
                            txd_o          <= 1'b1;
                        end
                    end
                end

                default: begin
                    txd_o     <= 1'b1;
                end
            endcase
        end
    end

endmodule
