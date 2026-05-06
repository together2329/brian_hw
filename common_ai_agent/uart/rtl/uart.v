// =============================================================================
// UART Serial Controller - RTL Implementation (Verilog-2001)
// =============================================================================
// 8N1 frame format, 16-byte TX/RX FIFOs, APB4 slave, configurable baud rate
// =============================================================================

module uart #(
  parameter FIFO_DEPTH     = 16,
  parameter DATA_WIDTH     = 8,
  parameter ADDR_WIDTH     = 8,
  parameter BAUD_DIV_WIDTH = 16
)(
  // ---- APB4 Slave Interface ----
  input  wire                  pclk,
  input  wire                  preset_n,
  input  wire                  psel,
  input  wire                  penable,
  input  wire                  pwrite,
  input  wire [ADDR_WIDTH-1:0] paddr,
  input  wire [31:0]          pwdata,
  output wire [31:0]          prdata,
  output wire                  pready,
  output wire                  pslverr,

  // ---- UART Pins ----
  output wire                  uart_tx,
  input  wire                  uart_rx,

  // ---- Interrupt ----
  output wire                  irq
);

  // =========================================================================
  // Local parameters
  // =========================================================================
  localparam FIFO_ADDR_W = $clog2(FIFO_DEPTH);

  localparam [1:0] TX_IDLE  = 2'd0,
                   TX_START = 2'd1,
                   TX_DATA  = 2'd2,
                   TX_STOP  = 2'd3;

  localparam [1:0] RX_IDLE  = 2'd0,
                   RX_START = 2'd1,
                   RX_DATA  = 2'd2,
                   RX_STOP  = 2'd3;

  // =========================================================================
  // Internal signals
  // =========================================================================
  wire        apb_write = psel & penable & pwrite;
  wire        apb_read  = psel & penable & ~pwrite;
  wire [3:0]  reg_sel   = paddr[3:0];

  reg [BAUD_DIV_WIDTH-1:0] baud_div;
  reg [2:0]                irq_enable;

  // TX FIFO
  reg [DATA_WIDTH-1:0]    tx_fifo [0:FIFO_DEPTH-1];
  reg [FIFO_ADDR_W:0]     tx_wr_ptr;
  reg [FIFO_ADDR_W:0]     tx_rd_ptr;
  wire [FIFO_ADDR_W:0]    tx_count;
  wire                    tx_fifo_empty;
  wire                    tx_fifo_full;

  // RX FIFO
  reg [DATA_WIDTH-1:0]    rx_fifo [0:FIFO_DEPTH-1];
  reg [FIFO_ADDR_W:0]     rx_wr_ptr;
  reg [FIFO_ADDR_W:0]     rx_rd_ptr;
  wire [FIFO_ADDR_W:0]    rx_count;
  wire                    rx_fifo_empty;
  wire                    rx_fifo_full;

  // TX FSM
  reg [1:0]                tx_state;
  reg [BAUD_DIV_WIDTH-1:0] tx_baud_cnt;
  reg [2:0]                tx_bit_cnt;
  reg [DATA_WIDTH-1:0]     tx_shift_reg;
  reg                      tx_out;

  // RX FSM
  reg [1:0]                rx_state;
  reg [BAUD_DIV_WIDTH-1:0] rx_baud_cnt;
  reg [2:0]                rx_bit_cnt;
  reg [DATA_WIDTH-1:0]     rx_shift_reg;
  reg                      rx_sync_0;
  reg                      rx_sync_1;
  wire                     rx_falling;

  reg  rx_overrun;
  wire tx_busy;
  wire int_tx_empty;
  wire int_rx_data_ready;
  wire int_rx_overrun;

  // =========================================================================
  // APB Read Mux
  // =========================================================================
  always @(*) begin
    prdata = 32'd0;
    case (reg_sel)
      4'h0: begin
        if (!rx_fifo_empty)
          prdata[DATA_WIDTH-1:0] = rx_fifo[rx_rd_ptr[FIFO_ADDR_W-1:0]];
        else
          prdata[DATA_WIDTH-1:0] = {DATA_WIDTH{1'b0}};
      end
      4'h4: begin
        prdata[0] = rx_fifo_full;
        prdata[1] = tx_fifo_empty;
        prdata[2] = tx_fifo_full;
        prdata[3] = ~rx_fifo_empty;
        prdata[4] = rx_overrun;
        prdata[5] = tx_busy;
      end
      4'h8: begin
        prdata[BAUD_DIV_WIDTH-1:0] = baud_div;
      end
      4'hC: begin
        prdata[2:0] = irq_enable;
      end
      default: prdata = 32'd0;
    endcase
  end

  assign pready  = 1'b1;
  assign pslverr = 1'b0;

  // =========================================================================
  // TX FIFO pointers and count
  // =========================================================================
  assign tx_count      = tx_wr_ptr - tx_rd_ptr;
  assign tx_fifo_empty = (tx_wr_ptr == tx_rd_ptr);
  assign tx_fifo_full  = (tx_count == FIFO_DEPTH);

  // =========================================================================
  // RX FIFO pointers and count
  // =========================================================================
  assign rx_count      = rx_wr_ptr - rx_rd_ptr;
  assign rx_fifo_empty = (rx_wr_ptr == rx_rd_ptr);
  assign rx_fifo_full  = (rx_count == FIFO_DEPTH);

  // =========================================================================
  // APB Write - Register and FIFO push/pop
  // =========================================================================
  always @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      baud_div   <= {BAUD_DIV_WIDTH{1'b0}};
      irq_enable <= 3'd0;
      tx_wr_ptr  <= {(FIFO_ADDR_W+1){1'b0}};
      rx_rd_ptr  <= {(FIFO_ADDR_W+1){1'b0}};
      rx_overrun <= 1'b0;
    end else begin
      if (apb_read && reg_sel == 4'h4)
        rx_overrun <= 1'b0;

      if (apb_write) begin
        case (reg_sel)
          4'h0: begin
            if (!tx_fifo_full) begin
              tx_fifo[tx_wr_ptr[FIFO_ADDR_W-1:0]] <= pwdata[DATA_WIDTH-1:0];
              tx_wr_ptr <= tx_wr_ptr + 1'b1;
            end
          end
          4'h8: begin
            baud_div <= pwdata[BAUD_DIV_WIDTH-1:0];
          end
          4'hC: begin
            irq_enable <= pwdata[2:0];
          end
          default: ;
        endcase
      end

      if (apb_read && reg_sel == 4'h0 && !rx_fifo_empty)
        rx_rd_ptr <= rx_rd_ptr + 1'b1;
    end
  end

  // =========================================================================
  // TX FSM - Serializer (8N1)
  // =========================================================================
  assign uart_tx = tx_out;
  assign tx_busy = (tx_state != TX_IDLE);

  always @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      tx_state     <= TX_IDLE;
      tx_out       <= 1'b1;
      tx_baud_cnt  <= {BAUD_DIV_WIDTH{1'b0}};
      tx_bit_cnt   <= 3'd0;
      tx_shift_reg <= {DATA_WIDTH{1'b0}};
      tx_rd_ptr    <= {(FIFO_ADDR_W+1){1'b0}};
    end else begin
      case (tx_state)
        TX_IDLE: begin
          tx_out <= 1'b1;
          if (!tx_fifo_empty) begin
            tx_shift_reg <= tx_fifo[tx_rd_ptr[FIFO_ADDR_W-1:0]];
            tx_rd_ptr    <= tx_rd_ptr + 1'b1;
            tx_out       <= 1'b0;
            tx_baud_cnt  <= baud_div;
            tx_state     <= TX_START;
          end
        end
        TX_START: begin
          if (tx_baud_cnt == {BAUD_DIV_WIDTH{1'b0}}) begin
            tx_out      <= tx_shift_reg[0];
            tx_baud_cnt <= baud_div;
            tx_bit_cnt  <= 3'd0;
            tx_state    <= TX_DATA;
          end else begin
            tx_baud_cnt <= tx_baud_cnt - 1'b1;
          end
        end
        TX_DATA: begin
          if (tx_baud_cnt == {BAUD_DIV_WIDTH{1'b0}}) begin
            if (tx_bit_cnt == DATA_WIDTH - 1) begin
              tx_out      <= 1'b1;
              tx_baud_cnt <= baud_div;
              tx_state    <= TX_STOP;
            end else begin
              tx_bit_cnt   <= tx_bit_cnt + 1'b1;
              tx_shift_reg <= {1'b0, tx_shift_reg[DATA_WIDTH-1:1]};
              tx_out       <= tx_shift_reg[1];
              tx_baud_cnt  <= baud_div;
            end
          end else begin
            tx_baud_cnt <= tx_baud_cnt - 1'b1;
          end
        end
        TX_STOP: begin
          if (tx_baud_cnt == {BAUD_DIV_WIDTH{1'b0}}) begin
            tx_out   <= 1'b1;
            tx_state <= TX_IDLE;
          end else begin
            tx_baud_cnt <= tx_baud_cnt - 1'b1;
          end
        end
        default: tx_state <= TX_IDLE;
      endcase
    end
  end

  // =========================================================================
  // RX synchronizer (2-stage)
  // =========================================================================
  always @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      rx_sync_0 <= 1'b1;
      rx_sync_1 <= 1'b1;
    end else begin
      rx_sync_0 <= uart_rx;
      rx_sync_1 <= rx_sync_0;
    end
  end

  assign rx_falling = ~rx_sync_0 & rx_sync_1;

  // =========================================================================
  // RX FSM - Deserializer (8N1)
  // =========================================================================
  always @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      rx_state     <= RX_IDLE;
      rx_baud_cnt  <= {BAUD_DIV_WIDTH{1'b0}};
      rx_bit_cnt   <= 3'd0;
      rx_shift_reg <= {DATA_WIDTH{1'b0}};
      rx_wr_ptr    <= {(FIFO_ADDR_W+1){1'b0}};
    end else begin
      case (rx_state)
        RX_IDLE: begin
          if (rx_falling) begin
            rx_baud_cnt <= {1'b0, baud_div[BAUD_DIV_WIDTH-1:1]};
            rx_state    <= RX_START;
          end
        end
        RX_START: begin
          if (rx_baud_cnt == {BAUD_DIV_WIDTH{1'b0}}) begin
            if (rx_sync_0 == 1'b0) begin
              rx_baud_cnt <= baud_div;
              rx_bit_cnt  <= 3'd0;
              rx_state    <= RX_DATA;
            end else begin
              rx_state <= RX_IDLE;
            end
          end else begin
            rx_baud_cnt <= rx_baud_cnt - 1'b1;
          end
        end
        RX_DATA: begin
          if (rx_baud_cnt == {BAUD_DIV_WIDTH{1'b0}}) begin
            rx_shift_reg <= {rx_sync_0, rx_shift_reg[DATA_WIDTH-1:1]};
            if (rx_bit_cnt == DATA_WIDTH - 1)
              rx_state <= RX_STOP;
            else
              rx_bit_cnt <= rx_bit_cnt + 1'b1;
            rx_baud_cnt <= baud_div;
          end else begin
            rx_baud_cnt <= rx_baud_cnt - 1'b1;
          end
        end
        RX_STOP: begin
          if (rx_baud_cnt == {BAUD_DIV_WIDTH{1'b0}}) begin
            if (!rx_fifo_full) begin
              rx_fifo[rx_wr_ptr[FIFO_ADDR_W-1:0]] <= rx_shift_reg;
              rx_wr_ptr <= rx_wr_ptr + 1'b1;
            end else begin
              rx_overrun <= 1'b1;
            end
            rx_state <= RX_IDLE;
          end else begin
            rx_baud_cnt <= rx_baud_cnt - 1'b1;
          end
        end
        default: rx_state <= RX_IDLE;
      endcase
    end
  end

  // =========================================================================
  // Interrupt logic
  // =========================================================================
  assign int_tx_empty      = tx_fifo_empty;
  assign int_rx_data_ready = ~rx_fifo_empty;
  assign int_rx_overrun    = rx_overrun;

  assign irq = (irq_enable[0] & int_tx_empty) |
               (irq_enable[1] & int_rx_data_ready) |
               (irq_enable[2] & int_rx_overrun);

endmodule
