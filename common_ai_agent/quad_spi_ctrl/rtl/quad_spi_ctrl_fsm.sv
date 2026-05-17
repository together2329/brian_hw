// quad_spi_ctrl_fsm.sv — Main FSM and shift engine
// SSOT refs: fsm.channel_level, function_model.transactions, cycle_model.pipeline,
//            cycle_model.ordering, features, dataflow.control_path
module quad_spi_ctrl_fsm (
  input  wire        PCLK,
  input  wire        PRESETn,

  // Control inputs (from APB registers)
  input  wire [0:0]  start,
  input  wire [0:0]  sw_reset,
  input  wire [1:0]  lane_mode,
  input  wire        cpol,
  input  wire        cpha,
  input  wire        lsb_first,
  input  wire [2:0]  addr_len,
  input  wire [7:0]  data_len,
  input  wire [3:0]  csidle_val,
  input  wire [7:0]  csidle_hold,

  // SCLK interface
  input  wire        sclk_rising,
  input  wire        sclk_falling,
  input  wire        sclk_sample_edge,
  input  wire        prescale_tick,

  // TX FIFO interface
  input  wire        tx_empty,
  output reg         tx_pop,
  input  wire [7:0]  tx_pop_data,

  // RX FIFO interface
  output reg         rx_push,
  output reg  [7:0]  rx_push_data,
  input  wire        rx_full,

  // External SPI pins
  output reg  [3:0]  cs_n_o,
  output reg  [3:0]  io_oe_o,
  output reg  [3:0]  io_out_o,
  input  wire [3:0]  io_in_i,

  // Status and observability
  output wire        busy_o,
  output wire        done_event_o,
  output wire        error_event_o,
  output wire [3:0]  fsm_state_o,
  output wire [3:0]  io_oe_debug,
  output wire [3:0]  io_in_debug
);

  // FSM state encoding
  localparam [3:0] S_IDLE    = 4'd0;
  localparam [3:0] S_CMD     = 4'd1;
  localparam [3:0] S_ADDR    = 4'd2;
  localparam [3:0] S_DATA    = 4'd3;
  localparam [3:0] S_WAIT_CS = 4'd4;
  localparam [3:0] S_DONE    = 4'd5;

  reg [3:0]  state, next_state;
  reg [7:0]  bit_count;
  reg [7:0]  byte_count;
  reg [7:0]  shift_reg;
  reg [2:0]  lane_bit_idx;
  reg [7:0]  rx_shift_reg;
  reg [7:0]  cs_idle_cnt;

  wire launch_gate = start && !busy_o && !tx_empty;
  wire cmd_byte_done, addr_done, data_done, cs_idle_done;
  wire [1:0] lanes_bits;

  assign lanes_bits = (lane_mode == 2'd0) ? 2'd1 :
                      (lane_mode == 2'd1) ? 2'd2 : 2'd3; // 1, 2, or 4 lanes
  // bits per SCLK edge = 2^lane_mode
  wire [2:0] bits_per_edge = 3'd1 << lane_mode;

  // State register
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn)
      state <= S_IDLE;
    else if (sw_reset)
      state <= S_IDLE;
    else
      state <= next_state;
  end

  // FSM combinational next-state
  always @(*) begin
    next_state = state;
    case (state)
      S_IDLE:    if (launch_gate)           next_state = S_CMD;
      S_CMD:     if (cmd_byte_done)  begin
                   if (addr_len > 0)        next_state = S_ADDR;
                   else if (data_len > 0)   next_state = S_DATA;
                   else                     next_state = S_WAIT_CS;
                 end
      S_ADDR:    if (addr_done)      begin
                   if (data_len > 0)        next_state = S_DATA;
                   else                     next_state = S_WAIT_CS;
                 end
      S_DATA:    if (data_done)             next_state = S_WAIT_CS;
      S_WAIT_CS: if (cs_idle_done)          next_state = S_DONE;
      S_DONE:                               next_state = S_IDLE;
      default:                              next_state = S_IDLE;
    endcase
  end

  // FSM sequential output logic
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      bit_count    <= 8'd0;
      byte_count   <= 8'd0;
      shift_reg    <= 8'd0;
      lane_bit_idx <= 3'd0;
      rx_shift_reg <= 8'd0;
      cs_idle_cnt  <= 8'd0;
      tx_pop       <= 1'b0;
      rx_push      <= 1'b0;
      rx_push_data <= 8'd0;
      cs_n_o       <= 4'hF;
      io_oe_o      <= 4'h0;
      io_out_o     <= 4'h0;
    end else if (sw_reset) begin
      bit_count    <= 8'd0;
      byte_count   <= 8'd0;
      shift_reg    <= 8'd0;
      lane_bit_idx <= 3'd0;
      rx_shift_reg <= 8'd0;
      cs_idle_cnt  <= 8'd0;
      tx_pop       <= 1'b0;
      rx_push      <= 1'b0;
      rx_push_data <= 8'd0;
      cs_n_o       <= csidle_val;
      io_oe_o      <= 4'h0;
      io_out_o     <= 4'h0;
    end else begin
      // Defaults
      tx_pop   <= 1'b0;
      rx_push  <= 1'b0;

      case (state)
        S_IDLE: begin
          bit_count    <= 8'd0;
          byte_count   <= 8'd0;
          shift_reg    <= 8'd0;
          lane_bit_idx <= 3'd0;
          rx_shift_reg <= 8'd0;
          cs_idle_cnt  <= 8'd0;
          cs_n_o       <= csidle_val;
          io_oe_o      <= 4'h0;
          io_out_o     <= 4'h0;
          if (launch_gate) begin
            // Pop CMD byte from TX FIFO on launch
            tx_pop   <= 1'b1;
            cs_n_o   <= {4{1'b0}}; // Assert CS_N low (all active)
          end
        end

        S_CMD, S_ADDR, S_DATA: begin
          io_oe_o <= {4{1'b1}}; // All lanes output during TX
          if (prescale_tick) begin
            // On each SCLK edge, shift bits
            if (sclk_sample_edge) begin
              // Sample IO inputs
              lane_bit_idx <= lane_bit_idx + bits_per_edge;
            end
            // On SCLK rising edge (launch), drive new bits
            if (sclk_rising) begin
              if (bit_count == 8'd0 && lane_bit_idx == 3'd0) begin
                // Load new byte from TX FIFO or shift register
                if (byte_count > 8'd0) begin
                  tx_pop <= 1'b1;
                end
                shift_reg <= tx_pop_data;
              end
              // Drive bits to IO lanes
              if (lsb_first) begin
                io_out_o[0] <= shift_reg[0];
                if (lane_mode >= 2'd1) io_out_o[1] <= shift_reg[1];
                if (lane_mode >= 2'd2) begin
                  io_out_o[2] <= shift_reg[2];
                  io_out_o[3] <= shift_reg[3];
                end
              end else begin
                io_out_o[0] <= shift_reg[7];
                if (lane_mode >= 2'd1) io_out_o[1] <= shift_reg[6];
                if (lane_mode >= 2'd2) begin
                  io_out_o[2] <= shift_reg[5];
                  io_out_o[3] <= shift_reg[4];
                end
              end

              // Shift register
              if (lsb_first)
                shift_reg <= shift_reg >> bits_per_edge;
              else
                shift_reg <= shift_reg << bits_per_edge;

              bit_count <= bit_count + {{5{1'b0}}, bits_per_edge};
            end

            // On SCLK sample edge, capture RX
            if (sclk_sample_edge) begin
              rx_shift_reg[3:0] <= io_in_i;
            end
          end
        end

        S_WAIT_CS: begin
          cs_n_o  <= csidle_val;
          io_oe_o <= 4'h0;
          io_out_o <= 4'h0;
          if (prescale_tick) begin
            cs_idle_cnt <= cs_idle_cnt + 1'b1;
          end
        end

        S_DONE: begin
          // Push received data to RX FIFO if not full
          if (!rx_full) begin
            rx_push      <= 1'b1;
            rx_push_data <= rx_shift_reg;
          end
          cs_n_o  <= csidle_val;
          io_oe_o <= 4'h0;
          io_out_o <= 4'h0;
        end

        default: ;
      endcase
    end
  end

  // Completion detection (combinational)
  assign cmd_byte_done  = (bit_count == 8'd8);  // 1 byte of CMD
  assign addr_done      = (byte_count >= addr_len && cmd_byte_done);
  assign data_done      = (byte_count >= data_len);
  assign cs_idle_done   = (cs_idle_cnt >= csidle_hold);

  assign busy_o         = (state != S_IDLE) && (state != S_DONE);
  assign done_event_o   = (state == S_DONE);
  assign error_event_o  = 1'b0; // FSM itself doesn't generate errors
  assign fsm_state_o    = state;
  assign io_oe_debug    = io_oe_o;
  assign io_in_debug    = io_in_i;

endmodule
