// =============================================================================
// uart_tx.v — UART Transmitter with FIFO and Shift Register
// =============================================================================
`default_nettype none
`include "uart_defines.vh"

/* verilator lint_off UNUSEDSIGNAL */
module uart_tx (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        tx_en,
    input  wire [2:0]  data_bits,
    input  wire        stop_bits,     /*verilator lint_off UNUSEDSIGNAL*/
    input  wire        parity_en,
    input  wire        parity_odd,
    input  wire        loopback_en,   /*verilator lint_off UNUSEDSIGNAL*/
    input  wire        baud_tick,
    input  wire [7:0]  fifo_wdata,
    input  wire        fifo_wr_en,
    output wire        fifo_full,
    output wire        fifo_not_empty,
    output reg         tx_out,
    output reg         tx_done,
    output reg  [7:0]  loopback_data
);

    // TX FIFO
    localparam integer FIFO_D = `FIFO_DEPTH;
    localparam integer PTR_W  = `PTR_W;

    reg [7:0]  fifo_mem [0:FIFO_D-1];
    reg [PTR_W-1:0] wr_ptr, rd_ptr;

    wire fifo_empty_w = (wr_ptr == rd_ptr);
    wire fifo_full_w  = (wr_ptr[PTR_W-2:0] == rd_ptr[PTR_W-2:0]) &&
                        (wr_ptr[PTR_W-1] != rd_ptr[PTR_W-1]);

    assign fifo_full      = fifo_full_w;
    assign fifo_not_empty = ~fifo_empty_w;

    wire fifo_rd_en;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= {(PTR_W){1'b0}};
            rd_ptr <= {(PTR_W){1'b0}};
        end else begin
            if (fifo_wr_en && !fifo_full_w) begin
                fifo_mem[wr_ptr[PTR_W-2:0]] <= fifo_wdata;
                wr_ptr <= wr_ptr + {{(PTR_W-1){1'b0}}, 1'b1};
            end
            if (fifo_rd_en && !fifo_empty_w) begin
                rd_ptr <= rd_ptr + {{(PTR_W-1){1'b0}}, 1'b1};
            end
        end
    end

    wire [7:0] fifo_rdata = fifo_mem[rd_ptr[PTR_W-2:0]];

    // Shift register & parity
    reg [7:0]  shift_reg;
    reg [3:0]  bit_cnt;
    reg        parity_calc;

    // TX FSM
    reg [2:0] state, next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) state <= `TX_IDLE;
        else        state <= next_state;
    end

    always @(*) begin
        next_state = state;
        case (state)
            `TX_IDLE:   if (tx_en && fifo_not_empty) next_state = `TX_START;
            `TX_START:  if (baud_tick)               next_state = `TX_DATA;
            `TX_DATA:   if (baud_tick && bit_cnt >= {1'b0, data_bits})
                           next_state = (parity_en) ? `TX_PARITY : `TX_STOP;
            `TX_PARITY: if (baud_tick)               next_state = `TX_STOP;
            `TX_STOP:   if (baud_tick) begin
                           if (tx_en && fifo_not_empty)
                               next_state = `TX_START;
                           else
                               next_state = `TX_IDLE;
                       end
            default:   next_state = `TX_IDLE;
        endcase
    end

    assign fifo_rd_en = (state == `TX_IDLE) && tx_en && fifo_not_empty;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_out       <= 1'b1;
            tx_done      <= 1'b0;
            shift_reg    <= 8'd0;
            bit_cnt      <= 4'd0;
            parity_calc  <= 1'b0;
            loopback_data<= 8'd0;
        end else begin
            tx_done <= 1'b0;
            case (state)
                `TX_IDLE: begin
                    tx_out <= 1'b1;
                    bit_cnt <= 4'd0;
                    if (tx_en && fifo_not_empty) begin
                        shift_reg    <= fifo_rdata;
                        parity_calc  <= ^fifo_rdata ^ parity_odd;
                        loopback_data<= fifo_rdata;
                    end
                end
                `TX_START: begin
                    tx_out <= 1'b0;
                end
                `TX_DATA: begin
                    if (baud_tick) begin
                        tx_out    <= shift_reg[0];
                        shift_reg <= {1'b0, shift_reg[7:1]};
                        bit_cnt   <= bit_cnt + 4'd1;
                    end
                end
                `TX_PARITY: begin
                    tx_out <= parity_calc;
                end
                `TX_STOP: begin
                    tx_out <= 1'b1;
                    if (baud_tick)
                        tx_done <= 1'b1;
                end
                default: tx_out <= 1'b1;
            endcase
        end
    end

endmodule

`default_nettype wire
