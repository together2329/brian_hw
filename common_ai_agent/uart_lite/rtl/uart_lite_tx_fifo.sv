// uart_lite_tx_fifo.sv — TX FIFO (SRAM-based circular buffer)
// Depth FIFO_DEPTH (power of two), width DATA_WIDTH.
// Write on APB TXDATA write (wr_en_i), read on TX FSM pop (rd_en_i).
//
// SSOT: memory.instances.tx_fifo — parameterized to FIFO_DEPTH × DATA_WIDTH
//       latency: 1 (read data available one cycle after rd_en)

`include "uart_lite_param.vh"

module uart_lite_tx_fifo #(
    parameter integer DATA_WIDTH  = `UART_LITE_DATA_WIDTH,
    parameter integer FIFO_DEPTH  = `UART_LITE_FIFO_DEPTH
) (
    input  logic                     PCLK,
    input  logic                     PRESETn,

    // Write side
    input  logic                     wr_en_i,
    input  logic [DATA_WIDTH-1:0]    wr_data_i,

    // Read side
    input  logic                     rd_en_i,
    output logic [DATA_WIDTH-1:0]    rd_data_o,

    // Status flags
    output logic                     full_o,
    output logic                     empty_o,
    output logic [$clog2(FIFO_DEPTH):0] level_o
);

    localparam integer ADDR_W = $clog2(FIFO_DEPTH);

    // FIFO storage — register array
    logic [DATA_WIDTH-1:0] fifo_mem [0:FIFO_DEPTH-1];

    logic [ADDR_W-1:0] wr_ptr, rd_ptr;
    logic [ADDR_W:0]   count;  // one extra bit to represent FIFO_DEPTH

    // Full/empty derived from count (power-of-two FIFO)
    wire full_comb;
    wire empty_comb;
    assign full_comb  = (count == FIFO_DEPTH[ADDR_W:0]);
    assign empty_comb = (count == {(ADDR_W+1){1'b0}});

    // Write operation
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            wr_ptr  <= {ADDR_W{1'b0}};
        end else begin
            if (wr_en_i && !full_comb) begin
                fifo_mem[wr_ptr] <= wr_data_i;
                wr_ptr           <= wr_ptr + {{(ADDR_W-1){1'b0}}, 1'b1};
            end
        end
    end

    // Read operation — latency 1: data appears on rd_data_o one cycle after rd_en
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            rd_ptr   <= {ADDR_W{1'b0}};
            rd_data_o <= {DATA_WIDTH{1'b0}};
        end else begin
            if (rd_en_i && !empty_comb) begin
                // With latency=1, data from the read pointer arrives next cycle
                rd_data_o <= fifo_mem[rd_ptr];
                rd_ptr    <= rd_ptr + {{(ADDR_W-1){1'b0}}, 1'b1};
            end
        end
    end

    // Occupancy counter
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            count <= {(ADDR_W+1){1'b0}};
        end else begin
            case ({wr_en_i && !full_comb, rd_en_i && !empty_comb})
                2'b01: count <= count - {{(ADDR_W){1'b0}}, 1'b1};
                2'b10: count <= count + {{(ADDR_W){1'b0}}, 1'b1};
                default: count <= count;
            endcase
        end
    end

    // Registered status outputs
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            full_o  <= 1'b0;
            empty_o <= 1'b1;
            level_o <= {(ADDR_W+1){1'b0}};
        end else begin
            full_o  <= full_comb;
            empty_o <= empty_comb;
            level_o <= count;
        end
    end

endmodule
