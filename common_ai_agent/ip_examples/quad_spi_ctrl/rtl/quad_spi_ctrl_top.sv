// quad_spi_ctrl_top.sv — Top-level integration
// SSOT refs: top_module, io_list.interfaces, sub_modules
module quad_spi_ctrl_top #(
  parameter APB_ADDR_WIDTH = 12,
  parameter APB_DATA_WIDTH = 32,
  parameter TX_FIFO_DEPTH  = 16,
  parameter RX_FIFO_DEPTH  = 16,
  parameter PRESCALE_WIDTH = 16
) (
  // Clock and reset
  input  wire        PCLK,
  input  wire        PRESETn,

  // APB slave interface
  input  wire        PSEL,
  input  wire        PENABLE,
  input  wire [APB_ADDR_WIDTH-1:0] PADDR,
  input  wire [APB_DATA_WIDTH-1:0] PWDATA,
  input  wire        PWRITE,
  output wire [APB_DATA_WIDTH-1:0] PRDATA,
  output wire        PREADY,
  output wire        PSLVERR,

  // SPI master interface
  output wire        SCLK,
  output wire [3:0]  CS_N,
  inout  wire [3:0]  IO,
  output wire [3:0]  IO_OE,

  // Interrupt
  output wire        IRQ
);

  // Internal wires — APB to control
  wire [0:0]  apb_start;
  wire [0:0]  apb_sw_reset;
  wire [1:0]  apb_lane_mode;
  wire        apb_cpol, apb_cpha, apb_lsb_first;
  wire [2:0]  apb_addr_len;
  wire [7:0]  apb_data_len;
  wire [15:0] apb_prescale_div;
  wire [7:0]  apb_txdata;
  wire        apb_txdata_valid;
  wire [7:0]  apb_rxdata;
  wire [3:0]  apb_csidle_val;
  wire [7:0]  apb_csidle_hold;
  wire        apb_ie_tx_empty, apb_ie_rx_avail, apb_ie_done, apb_ie_error;
  wire        apb_w1c_done, apb_w1c_error;

  // Status wires
  wire        tx_full, tx_empty, rx_full, rx_empty, busy;
  wire [3:0]  tx_count, rx_count;
  wire        status_done, status_error_flag;

  // SCLK interface
  wire        sclk_wire;
  wire        sclk_rising, sclk_falling, sclk_sample_edge, prescale_tick;

  // FSM to FIFO
  wire        fsm_tx_pop;
  wire [7:0]  fsm_tx_pop_data;  // actually from FIFO
  wire        fsm_rx_push;
  wire [7:0]  fsm_rx_push_data;
  wire [3:0]  fsm_state, io_oe_debug, io_in_debug;

  // IO bidirectional
  wire [3:0]  io_out, io_in;

  // quad_spi_ctrl_apb
  quad_spi_ctrl_apb #(
    .APB_ADDR_WIDTH(APB_ADDR_WIDTH),
    .APB_DATA_WIDTH(APB_DATA_WIDTH)
  ) u_apb (
    .PCLK           (PCLK),
    .PRESETn        (PRESETn),
    .PSEL           (PSEL),
    .PENABLE        (PENABLE),
    .PADDR          (PADDR),
    .PWDATA         (PWDATA),
    .PWRITE         (PWRITE),
    .PRDATA         (PRDATA),
    .PREADY         (PREADY),
    .PSLVERR        (PSLVERR),
    .tx_full_i      (tx_full),
    .tx_empty_i     (tx_empty),
    .rx_full_i      (rx_full),
    .rx_empty_i     (rx_empty),
    .busy_i         (busy),
    .status_done_i  (status_done),
    .status_error_i (status_error_flag),
    .irq_out_i      (IRQ),
    .tx_count_i     (tx_count),
    .rx_count_i     (rx_count),
    .fsm_state_i    (fsm_state),
    .io_oe_i        (io_oe_debug),
    .io_in_i        (io_in_debug),
    .ctrl_start_o   (apb_start),
    .ctrl_sw_reset_o(apb_sw_reset),
    .ctrl_lane_mode_o(apb_lane_mode),
    .ctrl_cpol_o    (apb_cpol),
    .ctrl_cpha_o    (apb_cpha),
    .ctrl_lsb_first_o(apb_lsb_first),
    .ctrl_addr_len_o(apb_addr_len),
    .ctrl_data_len_o(apb_data_len),
    .prescale_div_o (apb_prescale_div),
    .txdata_o       (apb_txdata),
    .txdata_valid_o (apb_txdata_valid),
    .rxdata_i       (apb_rxdata),
    .csidle_val_o   (apb_csidle_val),
    .csidle_hold_o  (apb_csidle_hold),
    .ie_tx_empty_o  (apb_ie_tx_empty),
    .ie_rx_avail_o  (apb_ie_rx_avail),
    .ie_done_o      (apb_ie_done),
    .ie_error_o     (apb_ie_error),
    .w1c_done_o     (apb_w1c_done),
    .w1c_error_o    (apb_w1c_error)
  );

  // quad_spi_ctrl_fifo
  quad_spi_ctrl_fifo #(
    .TX_FIFO_DEPTH(TX_FIFO_DEPTH),
    .RX_FIFO_DEPTH(RX_FIFO_DEPTH)
  ) u_fifo (
    .PCLK         (PCLK),
    .PRESETn      (PRESETn),
    .tx_push      (apb_txdata_valid),
    .tx_push_data (apb_txdata),
    .tx_full      (tx_full),
    .tx_empty     (tx_empty),
    .tx_count     (tx_count),
    .tx_pop       (fsm_tx_pop),
    .tx_pop_data  (fsm_tx_pop_data),
    .rx_push      (fsm_rx_push),
    .rx_push_data (fsm_rx_push_data),
    .rx_full      (rx_full),
    .rx_empty     (rx_empty),
    .rx_pop       (rx_empty ? 1'b0 : 1'b0), // RX pop handled by APB read directly
    .rx_pop_data  (apb_rxdata),
    .rx_count     (rx_count),
    .sw_reset     (apb_sw_reset)
  );

  // quad_spi_ctrl_sclk_gen
  quad_spi_ctrl_sclk_gen #(
    .PRESCALE_WIDTH(PRESCALE_WIDTH)
  ) u_sclk_gen (
    .PCLK              (PCLK),
    .PRESETn           (PRESETn),
    .prescale_div      (apb_prescale_div),
    .cpol              (apb_cpol),
    .cpha              (apb_cpha),
    .sclk_enable       (busy),
    .sw_reset          (apb_sw_reset),
    .sclk_o            (sclk_wire),
    .sclk_rising       (sclk_rising),
    .sclk_falling      (sclk_falling),
    .sclk_sample_edge  (sclk_sample_edge),
    .prescale_tick     (prescale_tick)
  );

  // quad_spi_ctrl_fsm
  quad_spi_ctrl_fsm u_fsm (
    .PCLK             (PCLK),
    .PRESETn          (PRESETn),
    .start            (apb_start),
    .sw_reset         (apb_sw_reset),
    .lane_mode        (apb_lane_mode),
    .cpol             (apb_cpol),
    .cpha             (apb_cpha),
    .lsb_first        (apb_lsb_first),
    .addr_len         (apb_addr_len),
    .data_len         (apb_data_len),
    .csidle_val       (apb_csidle_val),
    .csidle_hold      (apb_csidle_hold),
    .sclk_rising      (sclk_rising),
    .sclk_falling     (sclk_falling),
    .sclk_sample_edge (sclk_sample_edge),
    .prescale_tick    (prescale_tick),
    .tx_empty         (tx_empty),
    .tx_pop           (fsm_tx_pop),
    .tx_pop_data      (fsm_tx_pop_data),
    .rx_push          (fsm_rx_push),
    .rx_push_data     (fsm_rx_push_data),
    .rx_full          (rx_full),
    .cs_n_o           (CS_N),
    .io_oe_o          (IO_OE),
    .io_out_o         (io_out),
    .io_in_i          (io_in),
    .busy_o           (busy),
    .done_event_o     (status_done),
    .error_event_o    (status_error_flag),
    .fsm_state_o      (fsm_state),
    .io_oe_debug      (io_oe_debug),
    .io_in_debug      (io_in_debug)
  );

  // quad_spi_ctrl_irq
  quad_spi_ctrl_irq u_irq (
    .PCLK             (PCLK),
    .PRESETn          (PRESETn),
    .tx_empty_src     (tx_empty),
    .rx_avail_src     (~rx_empty),
    .done_event       (status_done),
    .error_event      (status_error_flag),
    .ie_tx_empty      (apb_ie_tx_empty),
    .ie_rx_avail      (apb_ie_rx_avail),
    .ie_done          (apb_ie_done),
    .ie_error         (apb_ie_error),
    .w1c_done         (apb_w1c_done),
    .w1c_error        (apb_w1c_error),
    .sw_reset         (apb_sw_reset),
    .irq_o            (IRQ),
    .status_done      (),
    .status_error_flag()
  );

  // Bidirectional IO pads
  assign SCLK   = sclk_wire;
  assign io_in  = IO;
  assign IO     = (|IO_OE) ? io_out : 4'bz;

endmodule
