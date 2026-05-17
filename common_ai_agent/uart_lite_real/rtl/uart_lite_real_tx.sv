// uart_lite_real_tx.sv — TX FSM, shift register, parity generator
// SSOT: fsm.tx_fsm, function_model.transactions.FM_TX_BYTE

`include "uart_lite_real_param.vh"

module uart_lite_real_tx (
    input  wire                  PCLK,
    input  wire                  PRESETn,
    // Control
    input  wire                  tx_enable_i,
    input  wire                  parity_en_i,
    input  wire                  parity_odd_i,
    input  wire                  stop_bits_i,
    // FIFO interface
    input  wire [DATA_WIDTH-1:0] fifo_data_i,
    input  wire                  fifo_empty_i,
    output reg                   fifo_pop_o,
    // Baud
    input  wire                  baud_tick_i,
    // Output
    output reg                   tx_o,
    output reg                   tx_active_o,
    // Debug
    output reg  [31:0]           bytes_tx_o,
    // Break
    input  wire                  break_i
);

    // TX FSM states
    localparam S_TX_IDLE   = 3'd0;
    localparam S_TX_START  = 3'd1;
    localparam S_TX_DATA   = 3'd2;
    localparam S_TX_PARITY = 3'd3;
    localparam S_TX_STOP1  = 3'd4;
    localparam S_TX_STOP2  = 3'd5;

    reg [2:0] tx_state;
    reg [2:0] tx_next;
    reg [DATA_WIDTH-1:0] tx_shift_reg;
    reg [$clog2(DATA_WIDTH+1)-1:0] tx_bit_cnt;
    reg parity_bit;

    // State register
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            tx_state <= S_TX_IDLE;
        end else begin
            tx_state <= tx_next;
        end
    end

    // Combinational next-state + output logic
    always @(*) begin
        tx_next    = tx_state;
        tx_o       = 1'b1; // default: mark (idle high)
        fifo_pop_o = 1'b0;

        case (tx_state)
            S_TX_IDLE: begin
                tx_o = 1'b1;
                if (tx_enable_i && !fifo_empty_i && baud_tick_i && !break_i) begin
                    tx_next = S_TX_START;
                end
            end

            S_TX_START: begin
                tx_o = 1'b0; // start bit
                if (baud_tick_i) begin
                    tx_next = S_TX_DATA;
                end
            end

            S_TX_DATA: begin
                tx_o = tx_shift_reg[0];
                if (baud_tick_i) begin
                    if (tx_bit_cnt >= DATA_WIDTH[$clog2(DATA_WIDTH+1)-1:0] - 1'b1) begin
                        if (parity_en_i) begin
                            tx_next = S_TX_PARITY;
                        end else begin
                            tx_next = S_TX_STOP1;
                        end
                    end
                end
            end

            S_TX_PARITY: begin
                tx_o = parity_bit;
                if (baud_tick_i) begin
                    tx_next = S_TX_STOP1;
                end
            end

            S_TX_STOP1: begin
                tx_o = 1'b1;
                if (baud_tick_i) begin
                    if (stop_bits_i) begin
                        tx_next = S_TX_STOP2;
                    end else begin
                        tx_next = S_TX_IDLE;
                    end
                end
            end

            S_TX_STOP2: begin
                tx_o = 1'b1;
                if (baud_tick_i) begin
                    tx_next = S_TX_IDLE;
                end
            end

            default: begin
                tx_next = S_TX_IDLE;
            end
        endcase
    end

    // Sequential: shift register, bit counter, parity, active, pop
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            tx_shift_reg <= {DATA_WIDTH{1'b0}};
            tx_bit_cnt   <= {$clog2(DATA_WIDTH+1){1'b0}};
            parity_bit   <= 1'b0;
            tx_active_o  <= 1'b0;
            bytes_tx_o   <= 32'd0;
        end else begin
            case (tx_state)
                S_TX_IDLE: begin
                    tx_active_o <= 1'b0;
                    if (tx_enable_i && !fifo_empty_i && baud_tick_i && !break_i) begin
                        // Entering TX_START: pop byte from FIFO
                        tx_shift_reg <= fifo_data_i;
                        tx_bit_cnt   <= {$clog2(DATA_WIDTH+1){1'b0}};
                        tx_active_o  <= 1'b1;
                        fifo_pop_o   <= 1'b1;
                    end
                end

                S_TX_DATA: begin
                    if (baud_tick_i) begin
                        tx_shift_reg <= {1'b0, tx_shift_reg[DATA_WIDTH-1:1]};
                        tx_bit_cnt   <= tx_bit_cnt + 1'b1;
                        // Compute parity on-the-fly
                        parity_bit <= parity_bit ^ tx_shift_reg[0];
                    end
                end

                S_TX_STOP1, S_TX_STOP2: begin
                    if (baud_tick_i && tx_next == S_TX_IDLE) begin
                        // Frame complete
                        tx_active_o <= 1'b0;
                        bytes_tx_o  <= bytes_tx_o + 32'd1;
                    end
                end

                default: begin
                    // S_TX_START, S_TX_PARITY: no sequential action needed
                end
            endcase
        end
    end

endmodule
