// uart_lite_real_rx.sv — RX FSM, 2-FF synchronizer, oversampler, parity checker
// SSOT: fsm.rx_fsm, function_model.transactions.FM_RX_BYTE, cdc_requirements

`include "uart_lite_real_param.vh"

module uart_lite_real_rx (
    input  wire                  PCLK,
    input  wire                  PRESETn,
    // Control
    input  wire                  rx_enable_i,
    input  wire                  parity_en_i,
    input  wire                  parity_odd_i,
    input  wire                  stop_bits_i,
    // Serial input
    input  wire                  rx_i,
    // Loopback input
    input  wire                  loopback_i,
    input  wire                  tx_loopback_i,
    // Baud/oversample
    input  wire                  mid_sample_i,
    input  wire [15:0]           oversample_cnt_i,
    // FIFO write
    output reg                   fifo_wr_o,
    output reg  [DATA_WIDTH-1:0] fifo_data_o,
    input  wire                  fifo_full_i,
    // Status
    output reg                   rx_active_o,
    output reg                   frame_err_o,
    output reg                   parity_err_o,
    output reg                   overrun_err_o,
    // Debug
    output reg  [31:0]           bytes_rx_o,
    output reg  [31:0]           frames_errored_o,
    output reg  [31:0]           parities_errored_o,
    // Clear
    input  wire                  clear_errors_i,
    // Start detect output for baud_gen oversample reset
    output wire                  start_detect_o
);

    // RX FSM states
    localparam S_RX_IDLE          = 3'd0;
    localparam S_RX_START_DETECT  = 3'd1;
    localparam S_RX_START_CONFIRM = 3'd2;
    localparam S_RX_DATA          = 3'd3;
    localparam S_RX_PARITY        = 3'd4;
    localparam S_RX_STOP1         = 3'd5;
    localparam S_RX_STOP2         = 3'd6;

    reg [2:0] rx_state;
    reg [2:0] rx_next;
    reg [DATA_WIDTH-1:0] rx_shift_reg;
    reg [$clog2(DATA_WIDTH+1)-1:0] rx_bit_cnt;
    reg computed_parity;

    // Start detect output for baud_gen oversample counter reset
    assign start_detect_o = (rx_state == S_RX_IDLE) && rx_enable_i && rx_falling;

    // 2-FF synchronizer for external RX only
    reg rx_sync_1;
    reg rx_sync_2;
    reg rx_prev;

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            rx_sync_1 <= 1'b1;
            rx_sync_2 <= 1'b1;
            rx_prev   <= 1'b1;
        end else begin
            // External RX 2-FF synchronizer
            rx_sync_1 <= rx_i;
            rx_sync_2 <= rx_sync_1;
            // Previous value for edge detection
            // In loopback: use tx directly (same clock domain, no sync needed)
            // In external: use synchronized rx
            rx_prev <= (loopback_i ? tx_loopback_i : rx_sync_2);
        end
    end

    // Loopback mux: loopback uses tx directly (same clock domain)
    // External uses synchronized rx
    wire rx_sample = loopback_i ? tx_loopback_i : rx_sync_2;

    // Edge detection on the muxed sample
    wire rx_falling = rx_prev & ~rx_sample;

    // State register
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            rx_state <= S_RX_IDLE;
        end else begin
            rx_state <= rx_next;
        end
    end

    // Combinational next-state logic
    always @(*) begin
        rx_next = rx_state;

        case (rx_state)
            S_RX_IDLE: begin
                if (rx_enable_i && rx_falling) begin
                    rx_next = S_RX_START_DETECT;
                end
            end

            S_RX_START_DETECT: begin
                if (mid_sample_i) begin
                    if (rx_sample == 1'b0) begin
                        rx_next = S_RX_START_CONFIRM;
                    end else begin
                        rx_next = S_RX_IDLE; // spurious
                    end
                end
            end

            S_RX_START_CONFIRM: begin
                // Immediately advance to DATA — start already confirmed in START_DETECT
                rx_next = S_RX_DATA;
            end

            S_RX_DATA: begin
                if (mid_sample_i) begin
                    if (rx_bit_cnt >= DATA_WIDTH[$clog2(DATA_WIDTH+1)-1:0] - 1'b1) begin
                        if (parity_en_i) begin
                            rx_next = S_RX_PARITY;
                        end else begin
                            rx_next = S_RX_STOP1;
                        end
                    end
                end
            end

            S_RX_PARITY: begin
                if (mid_sample_i) begin
                    rx_next = S_RX_STOP1;
                end
            end

            S_RX_STOP1: begin
                if (mid_sample_i) begin
                    if (stop_bits_i) begin
                        rx_next = S_RX_STOP2;
                    end else begin
                        rx_next = S_RX_IDLE;
                    end
                end
            end

            S_RX_STOP2: begin
                if (mid_sample_i) begin
                    rx_next = S_RX_IDLE;
                end
            end

            default: begin
                rx_next = S_RX_IDLE;
            end
        endcase
    end

    // Sequential: shift register, bit counter, parity, errors, FIFO write
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            rx_shift_reg      <= {DATA_WIDTH{1'b0}};
            rx_bit_cnt        <= {$clog2(DATA_WIDTH+1){1'b0}};
            computed_parity   <= 1'b0;
            rx_active_o       <= 1'b0;
            frame_err_o       <= 1'b0;
            parity_err_o      <= 1'b0;
            overrun_err_o     <= 1'b0;
            bytes_rx_o        <= 32'd0;
            frames_errored_o  <= 32'd0;
            parities_errored_o <= 32'd0;
            fifo_wr_o         <= 1'b0;
            fifo_data_o       <= {DATA_WIDTH{1'b0}};
        end else begin
            fifo_wr_o <= 1'b0; // default: no write

            if (clear_errors_i) begin
                frame_err_o  <= 1'b0;
                parity_err_o <= 1'b0;
                overrun_err_o <= 1'b0;
            end

            case (rx_state)
                S_RX_IDLE: begin
                    rx_active_o <= 1'b0;
                    if (rx_enable_i && rx_falling) begin
                        rx_active_o <= 1'b1;
                        rx_bit_cnt  <= {$clog2(DATA_WIDTH+1){1'b0}};
                        rx_shift_reg <= {DATA_WIDTH{1'b0}};
                        computed_parity <= 1'b0;
                    end
                end

                S_RX_DATA: begin
                    if (mid_sample_i) begin
                        rx_shift_reg[rx_bit_cnt] <= rx_sample;
                        computed_parity <= computed_parity ^ rx_sample;
                        rx_bit_cnt <= rx_bit_cnt + 1'b1;
                    end
                end

                S_RX_PARITY: begin
                    if (mid_sample_i) begin
                        // Check parity
                        if (parity_odd_i) begin
                            // odd parity: computed_parity should be 0 when data has odd 1s
                            if (computed_parity ^ rx_sample) begin
                                parity_err_o <= 1'b1;
                                parities_errored_o <= parities_errored_o + 32'd1;
                            end
                        end else begin
                            // even parity: computed_parity should equal rx parity bit
                            if (computed_parity != rx_sample) begin
                                parity_err_o <= 1'b1;
                                parities_errored_o <= parities_errored_o + 32'd1;
                            end
                        end
                    end
                end

                S_RX_STOP1: begin
                    if (mid_sample_i) begin
                        if (rx_sample != 1'b1) begin
                            frame_err_o <= 1'b1;
                            frames_errored_o <= frames_errored_o + 32'd1;
                        end
                        // If not 2 stop bits, push byte now
                        if (!stop_bits_i) begin
                            if (!fifo_full_i) begin
                                fifo_wr_o   <= 1'b1;
                                fifo_data_o <= rx_shift_reg;
                                bytes_rx_o  <= bytes_rx_o + 32'd1;
                            end else begin
                                overrun_err_o <= 1'b1;
                            end
                            rx_active_o <= 1'b0;
                        end
                    end
                end

                S_RX_STOP2: begin
                    if (mid_sample_i) begin
                        if (rx_sample != 1'b1) begin
                            frame_err_o <= 1'b1;
                            frames_errored_o <= frames_errored_o + 32'd1;
                        end
                        // Push byte after 2nd stop bit
                        if (!fifo_full_i) begin
                            fifo_wr_o   <= 1'b1;
                            fifo_data_o <= rx_shift_reg;
                            bytes_rx_o  <= bytes_rx_o + 32'd1;
                        end else begin
                            overrun_err_o <= 1'b1;
                        end
                        rx_active_o <= 1'b0;
                    end
                end

                default: begin
                    // S_RX_START_DETECT, S_RX_START_CONFIRM: no sequential action
                end
            endcase
        end
    end

endmodule
