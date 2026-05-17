// quad_spi_ctrl_fifo.sv — TX/RX FIFO storage with level tracking
// SSOT refs: memory.instances, dataflow.tx_path, dataflow.rx_path,
//            cycle_model.backpressure, function_model.state_variables.tx_fifo/rx_fifo
module quad_spi_ctrl_fifo #(
  parameter int unsigned TX_FIFO_DEPTH = 16,
  parameter int unsigned RX_FIFO_DEPTH = 16
) (
  input  wire        PCLK,
  input  wire        PRESETn,

  // TX FIFO APB side
  input  wire        tx_push,
  input  wire [7:0]  tx_push_data,
  output wire        tx_full,
  output wire        tx_empty,
  output wire [3:0]  tx_count,

  // TX FIFO engine side
  input  wire        tx_pop,
  output wire [7:0]  tx_pop_data,

  // RX FIFO engine side
  input  wire        rx_push,
  input  wire [7:0]  rx_push_data,
  output wire        rx_full,
  output wire        rx_empty,

  // RX FIFO APB side
  input  wire        rx_pop,
  output wire [7:0]  rx_pop_data,
  output wire [3:0]  rx_count,

  // Control
  input  wire        sw_reset
);

  localparam TX_FIFO_DEPTH_W = $clog2(TX_FIFO_DEPTH);
  localparam RX_FIFO_DEPTH_W = $clog2(RX_FIFO_DEPTH);

  // TX FIFO storage
  reg [7:0] tx_mem [0:TX_FIFO_DEPTH-1];
  reg [$clog2(TX_FIFO_DEPTH):0] tx_wr_ptr, tx_rd_ptr, tx_occupancy;

  // RX FIFO storage
  reg [7:0] rx_mem [0:RX_FIFO_DEPTH-1];
  reg [$clog2(RX_FIFO_DEPTH):0] rx_wr_ptr, rx_rd_ptr, rx_occupancy;

  // TX FIFO logic
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      tx_wr_ptr    <= '0;
      tx_rd_ptr    <= '0;
      tx_occupancy <= '0;
    end else if (sw_reset) begin
      tx_wr_ptr    <= '0;
      tx_rd_ptr    <= '0;
      tx_occupancy <= '0;
    end else begin
      case ({tx_push && !tx_full, tx_pop && !tx_empty})
        2'b10: begin
          tx_mem[tx_wr_ptr[$clog2(TX_FIFO_DEPTH)-1:0]] <= tx_push_data;
          tx_wr_ptr    <= tx_wr_ptr + 1'b1;
          tx_occupancy <= tx_occupancy + 1'b1;
        end
        2'b01: begin
          tx_rd_ptr    <= tx_rd_ptr + 1'b1;
          tx_occupancy <= tx_occupancy - 1'b1;
        end
        2'b11: begin
          tx_mem[tx_wr_ptr[$clog2(TX_FIFO_DEPTH)-1:0]] <= tx_push_data;
          tx_wr_ptr    <= tx_wr_ptr + 1'b1;
          tx_rd_ptr    <= tx_rd_ptr + 1'b1;
        end
        default: ;
      endcase
    end
  end

  assign tx_full    = (tx_occupancy == TX_FIFO_DEPTH_W'(TX_FIFO_DEPTH));
  assign tx_empty   = (tx_occupancy == 0);
  assign tx_count   = tx_occupancy[3:0];
  assign tx_pop_data = tx_mem[tx_rd_ptr[$clog2(TX_FIFO_DEPTH)-1:0]];

  // RX FIFO logic
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      rx_wr_ptr    <= '0;
      rx_rd_ptr    <= '0;
      rx_occupancy <= '0;
    end else if (sw_reset) begin
      rx_wr_ptr    <= '0;
      rx_rd_ptr    <= '0;
      rx_occupancy <= '0;
    end else begin
      case ({rx_push && !rx_full, rx_pop && !rx_empty})
        2'b10: begin
          rx_mem[rx_wr_ptr[$clog2(RX_FIFO_DEPTH)-1:0]] <= rx_push_data;
          rx_wr_ptr    <= rx_wr_ptr + 1'b1;
          rx_occupancy <= rx_occupancy + 1'b1;
        end
        2'b01: begin
          rx_rd_ptr    <= rx_rd_ptr + 1'b1;
          rx_occupancy <= rx_occupancy - 1'b1;
        end
        2'b11: begin
          rx_mem[rx_wr_ptr[$clog2(RX_FIFO_DEPTH)-1:0]] <= rx_push_data;
          rx_wr_ptr    <= rx_wr_ptr + 1'b1;
          rx_rd_ptr    <= rx_rd_ptr + 1'b1;
        end
        default: ;
      endcase
    end
  end

  assign rx_full    = (rx_occupancy == RX_FIFO_DEPTH_W'(RX_FIFO_DEPTH));
  assign rx_empty   = (rx_occupancy == 0);
  assign rx_count   = rx_occupancy[3:0];
  assign rx_pop_data = rx_mem[rx_rd_ptr[$clog2(RX_FIFO_DEPTH)-1:0]];

endmodule
