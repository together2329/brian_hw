// spi_fifo.sv — TX/RX FIFO storage and level tracking from SSOT memory/dataflow
module spi_fifo #(
    `include "spi_param.vh"
) (
    input  logic                    PCLK,
    input  logic                    PRESETn,
    input  logic                    soft_reset,
    input  logic                    tx_push,
    input  logic [31:0]             tx_push_data,
    output logic                    tx_push_drop,
    input  logic                    tx_pop,
    output logic [31:0]             tx_pop_data,
    output logic                    tx_empty,
    output logic                    tx_full,
    output logic [4:0]              tx_level,
    input  logic                    rx_push,
    input  logic [31:0]             rx_push_data,
    output logic                    rx_push_drop,
    input  logic                    rx_pop,
    output logic [31:0]             rx_pop_data,
    output logic                    rx_empty,
    output logic                    rx_full,
    output logic [4:0]              rx_level
);
    localparam integer FIFO_AW = $clog2(FIFO_DEPTH);

    logic [31:0] tx_mem [0:FIFO_DEPTH-1];
    logic [31:0] rx_mem [0:FIFO_DEPTH-1];
    logic [FIFO_AW-1:0] tx_wr_ptr;
    logic [FIFO_AW-1:0] tx_rd_ptr;
    logic [FIFO_AW-1:0] rx_wr_ptr;
    logic [FIFO_AW-1:0] rx_rd_ptr;
    logic [4:0] tx_count;
    logic [4:0] rx_count;

    assign tx_empty = (tx_count == 5'd0);
    assign tx_full  = (tx_count == FIFO_DEPTH[4:0]);
    assign rx_empty = (rx_count == 5'd0);
    assign rx_full  = (rx_count == FIFO_DEPTH[4:0]);
    assign tx_level = tx_count;
    assign rx_level = rx_count;
    assign tx_pop_data = tx_empty ? 32'h00000000 : tx_mem[tx_rd_ptr];
    assign rx_pop_data = rx_empty ? 32'h00000000 : rx_mem[rx_rd_ptr];
    assign tx_push_drop = tx_push && tx_full;
    assign rx_push_drop = rx_push && rx_full;

    // SSOT backpressure: full-side writes are dropped and reported by drop pulses.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            tx_wr_ptr <= {FIFO_AW{1'b0}};
            tx_rd_ptr <= {FIFO_AW{1'b0}};
            tx_count  <= 5'd0;
        end else if (soft_reset) begin
            tx_wr_ptr <= {FIFO_AW{1'b0}};
            tx_rd_ptr <= {FIFO_AW{1'b0}};
            tx_count  <= 5'd0;
        end else begin
            if (tx_push && !tx_full) begin
                tx_mem[tx_wr_ptr] <= tx_push_data;
                tx_wr_ptr <= tx_wr_ptr + {{(FIFO_AW-1){1'b0}}, 1'b1};
            end
            if (tx_pop && !tx_empty) begin
                tx_rd_ptr <= tx_rd_ptr + {{(FIFO_AW-1){1'b0}}, 1'b1};
            end
            if (tx_push && !tx_full && !(tx_pop && !tx_empty)) begin
                tx_count <= tx_count + 5'd1;
            end else if (tx_pop && !tx_empty && !(tx_push && !tx_full)) begin
                tx_count <= tx_count - 5'd1;
            end
        end
    end

    // RX queue mirrors TX policy: completion drops received words only when full.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            rx_wr_ptr <= {FIFO_AW{1'b0}};
            rx_rd_ptr <= {FIFO_AW{1'b0}};
            rx_count  <= 5'd0;
        end else if (soft_reset) begin
            rx_wr_ptr <= {FIFO_AW{1'b0}};
            rx_rd_ptr <= {FIFO_AW{1'b0}};
            rx_count  <= 5'd0;
        end else begin
            if (rx_push && !rx_full) begin
                rx_mem[rx_wr_ptr] <= rx_push_data;
                rx_wr_ptr <= rx_wr_ptr + {{(FIFO_AW-1){1'b0}}, 1'b1};
            end
            if (rx_pop && !rx_empty) begin
                rx_rd_ptr <= rx_rd_ptr + {{(FIFO_AW-1){1'b0}}, 1'b1};
            end
            if (rx_push && !rx_full && !(rx_pop && !rx_empty)) begin
                rx_count <= rx_count + 5'd1;
            end else if (rx_pop && !rx_empty && !(rx_push && !rx_full)) begin
                rx_count <= rx_count - 5'd1;
            end
        end
    end
endmodule
