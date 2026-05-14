// uart_lite_rx_fsm.sv — RX FSM with 2-FF synchronizer, oversampling, parity checker
// Implements: fsm.rx_fsm, cycle_model.pipeline.rx_stages, io_list.interfaces.uart_rx.protocol
// States: RX_IDLE, RX_START_DETECT, RX_START_CONFIRM, RX_DATA, RX_PARITY, RX_STOP, RX_DONE
// 2-FF synchronizer on external rxd_i; centre-samples at oversample count 7 per baud period

module uart_lite_rx_fsm #(
    parameter integer DATA_WIDTH = 8
) (
    input  logic                      clk,
    input  logic                      rst_n,
    // Serial input
    input  logic                      rxd_i,
    // Baud timing from baud_gen
    input  logic [3:0]                rx_oversample,
    // Frame configuration from CONTROL
    input  logic [2:0]                rx_data_width,
    input  logic                      parity_en,
    input  logic                      parity_odd,
    // RX FIFO interface
    output logic                      rx_fifo_wr_en,
    output logic [DATA_WIDTH-1:0]     rx_fifo_wr_data,
    input  logic                      rx_fifo_full,
    // Status outputs
    output logic                      frame_err,
    output logic                      parity_err,
    output logic                      rx_overrun,
    output logic                      break_detected,
    output logic                      rx_byte_done
);

    // FSM state encoding
    localparam [2:0] RX_IDLE           = 3'd0,
                     RX_START_DETECT   = 3'd1,
                     RX_START_CONFIRM  = 3'd2,
                     RX_DATA           = 3'd3,
                     RX_PARITY         = 3'd4,
                     RX_STOP           = 3'd5,
                     RX_DONE           = 3'd6;

    logic [2:0] state, next_state;

    // 2-FF synchronizer for rxd_i
    logic [1:0] rxd_sync;

    // Falling edge detect: rxd_sync == 2'b10 (was 1, now 0)
    wire rxd_falling;
    assign rxd_falling = (rxd_sync == 2'b10);

    // Data width mapping: 0=5, 1=6, 2=7, 3=8
    wire [3:0] data_bit_count;
    assign data_bit_count = {1'b0, rx_data_width} + 4'd5;

    // Receive shift register and bit counter
    logic [DATA_WIDTH-1:0] rx_shift_reg;
    logic [3:0]            bit_counter;

    // Helper wire for upper bits of shift register — avoid parameterized part-select in procedural block
    wire [DATA_WIDTH-2:0] rx_shift_upper;
    assign rx_shift_upper = rx_shift_reg[DATA_WIDTH-1:1];

    // Parity computation: XOR of received data bits
    // Helper wire for full shift register to avoid parameterized part-select in procedural block
    wire [DATA_WIDTH-1:0] rx_shift_full;
    assign rx_shift_full = rx_shift_reg;
    wire parity_calc;
    assign parity_calc = (^rx_shift_full) ^ parity_odd;

    // Internal sticky error outputs
    logic frame_err_i, parity_err_i, rx_overrun_i;

    // 2-FF synchronizer
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rxd_sync <= 2'b11;  // idle (mark)
        else
            rxd_sync <= {rxd_sync[0], rxd_i};
    end

    // State register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= RX_IDLE;
        else
            state <= next_state;
    end

    // Next-state combinational logic
    // The false-start check is combinatorial: in START_CONFIRM, if rxd_sync[1] is high,
    // return to IDLE (regardless of oversample). Otherwise, at oversample==15 transit to DATA.
    always @(*) begin
        next_state = state;
        case (state)
            RX_IDLE: begin
                if (rxd_falling)
                    next_state = RX_START_DETECT;
            end

            RX_START_DETECT: begin
                // Wait for oversample==7 to sample the start bit midpoint
                if (rx_oversample == 4'd7)
                    next_state = RX_START_CONFIRM;
            end

            RX_START_CONFIRM: begin
                // At the midpoint sample: if rxd is high, false start → IDLE
                if (rx_oversample == 4'd7 && rxd_sync[1])
                    next_state = RX_IDLE;
                // Otherwise, at oversample==15, start confirmed → DATA
                else if (rx_oversample == 4'd15)
                    next_state = RX_DATA;
            end

            RX_DATA: begin
                if (rx_oversample == 4'd15) begin
                    if (bit_counter == (data_bit_count - 4'd1)) begin
                        if (parity_en)
                            next_state = RX_PARITY;
                        else
                            next_state = RX_STOP;
                    end
                    // else stay in RX_DATA for next bit
                end
            end

            RX_PARITY: begin
                if (rx_oversample == 4'd15)
                    next_state = RX_STOP;
            end

            RX_STOP: begin
                if (rx_oversample == 4'd15)
                    next_state = RX_DONE;
            end

            RX_DONE: begin
                // One cycle to commit result, then back to idle
                next_state = RX_IDLE;
            end

            default: next_state = RX_IDLE;
        endcase
    end

    // Sequential output and register logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_shift_reg   <= {DATA_WIDTH{1'b0}};
            bit_counter    <= 4'd0;
            rx_fifo_wr_en  <= 1'b0;
            rx_fifo_wr_data <= {DATA_WIDTH{1'b0}};
            frame_err_i    <= 1'b0;
            parity_err_i   <= 1'b0;
            rx_overrun_i   <= 1'b0;
            rx_byte_done   <= 1'b0;
        end else begin
            // Default one-cycle pulses
            rx_fifo_wr_en  <= 1'b0;
            rx_byte_done   <= 1'b0;

            case (state)
                RX_IDLE: begin
                    bit_counter  <= 4'd0;
                    rx_shift_reg <= {DATA_WIDTH{1'b0}};
                end

                RX_START_DETECT: begin
                end

                RX_START_CONFIRM: begin
                    // False start aborts to IDLE (handled by next_state)
                    if (rx_oversample == 4'd7 && rxd_sync[1]) begin
                        // False start — abort
                    end
                end

                RX_DATA: begin
                    // Centre-sample at oversample==7
                    if (rx_oversample == 4'd7) begin
                        // Sample rxd into shift register: shift right, MSB gets sample
                        rx_shift_reg <= {rxd_sync[1], rx_shift_upper};
                    end
                    // At oversample==15, advance bit counter
                    if (rx_oversample == 4'd15) begin
                        if (bit_counter < (data_bit_count - 4'd1))
                            bit_counter <= bit_counter + 4'd1;
                    end
                end

                RX_PARITY: begin
                    // Centre-sample parity bit at oversample==7
                    if (rx_oversample == 4'd7) begin
                        // Compare sampled parity with computed
                        if (rxd_sync[1] != parity_calc)
                            parity_err_i <= 1'b1;
                    end
                end

                RX_STOP: begin
                    // Centre-sample stop bit at oversample==7
                    if (rx_oversample == 4'd7) begin
                        if (!rxd_sync[1]) begin
                            // Stop bit sampled low → frame error
                            frame_err_i <= 1'b1;
                        end
                    end
                end

                RX_DONE: begin
                    // Commit received byte to RX FIFO
                    if (!rx_fifo_full) begin
                        rx_fifo_wr_en   <= 1'b1;
                        rx_fifo_wr_data <= rx_shift_reg;
                    end else begin
                        // RX FIFO full → overrun
                        rx_overrun_i <= 1'b1;
                    end
                    rx_byte_done <= 1'b1;
                    bit_counter  <= 4'd0;
                    rx_shift_reg <= {DATA_WIDTH{1'b0}};
                end

                default: begin
                    // no-op
                end
            endcase
        end
    end

    // Drive output sticky flags
    assign frame_err      = frame_err_i;
    assign parity_err     = parity_err_i;
    assign rx_overrun     = rx_overrun_i;
    assign break_detected = 1'b0;  // Break detect on RX side: not implemented per SSOT — RX break detect not specified

endmodule
