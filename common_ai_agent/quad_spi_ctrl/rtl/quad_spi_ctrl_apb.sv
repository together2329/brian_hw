// quad_spi_ctrl_apb.sv — APB register decode and access policy
// SSOT refs: registers.register_list, io_list.interfaces.apb_slave,
//            error_handling.error_sources, interrupts
module quad_spi_ctrl_apb #(
  parameter APB_ADDR_WIDTH = 12,
  parameter APB_DATA_WIDTH = 32
) (
  input  wire        PCLK,
  input  wire        PRESETn,

  // APB slave interface
  input  wire        PSEL,
  input  wire        PENABLE,
  input  wire [APB_ADDR_WIDTH-1:0] PADDR,
  input  wire [APB_DATA_WIDTH-1:0] PWDATA,
  input  wire        PWRITE,
  output reg  [APB_DATA_WIDTH-1:0] PRDATA,
  output reg         PREADY,
  output reg         PSLVERR,

  // Status inputs from other modules
  input  wire        tx_full_i,
  input  wire        tx_empty_i,
  input  wire        rx_full_i,
  input  wire        rx_empty_i,
  input  wire        busy_i,
  input  wire        status_done_i,
  input  wire        status_error_i,
  input  wire        irq_out_i,
  input  wire [3:0]  tx_count_i,
  input  wire [3:0]  rx_count_i,
  input  wire [3:0]  fsm_state_i,
  input  wire [3:0]  io_oe_i,
  input  wire [3:0]  io_in_i,

  // Control outputs
  output reg  [0:0]  ctrl_start_o,
  output reg  [0:0]  ctrl_sw_reset_o,
  output reg  [1:0]  ctrl_lane_mode_o,
  output reg         ctrl_cpol_o,
  output reg         ctrl_cpha_o,
  output reg         ctrl_lsb_first_o,
  output reg  [2:0]  ctrl_addr_len_o,
  output reg  [7:0]  ctrl_data_len_o,

  output reg  [15:0] prescale_div_o,

  output reg  [7:0]  txdata_o,
  output reg         txdata_valid_o,

  input  wire [7:0]  rxdata_i,

  output reg  [3:0]  csidle_val_o,
  output reg  [7:0]  csidle_hold_o,

  output reg         ie_tx_empty_o,
  output reg         ie_rx_avail_o,
  output reg         ie_done_o,
  output reg         ie_error_o,

  // Sticky clear signals
  output reg         w1c_done_o,
  output reg         w1c_error_o
);

  // Register map offsets
  localparam CTRL     = 8'h00;  // 0x000
  localparam STATUS   = 8'h04;  // 0x004
  localparam PRESCALE = 8'h08;  // 0x008
  localparam TXDATA   = 8'h0C;  // 0x00C
  localparam RXDATA   = 8'h10;  // 0x010
  localparam CS_IDLE  = 8'h14;  // 0x014
  localparam IE       = 8'h18;  // 0x018
  localparam DEBUG    = 8'h1C;  // 0x01C

  wire [7:0] byte_addr = PADDR[7:0];
  wire       access_phase = PSEL && PENABLE;
  wire       valid_addr;

  // Address decode
  assign valid_addr = (byte_addr == CTRL)     ||
                      (byte_addr == STATUS)   ||
                      (byte_addr == PRESCALE) ||
                      (byte_addr == TXDATA)   ||
                      (byte_addr == RXDATA)   ||
                      (byte_addr == CS_IDLE)  ||
                      (byte_addr == IE)       ||
                      (byte_addr == DEBUG);

  // APB handshake
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      PREADY  <= 1'b0;
      PRDATA  <= '0;
      PSLVERR <= 1'b0;
    end else begin
      if (access_phase) begin
        PREADY <= 1'b1;
        PSLVERR <= !valid_addr;
      end else begin
        PREADY  <= 1'b0;
        PSLVERR <= 1'b0;
      end
    end
  end

  // Register storage
  reg [1:0]  lane_mode_r;
  reg        cpol_r, cpha_r, lsb_first_r;
  reg [2:0]  addr_len_r;
  reg [7:0]  data_len_r;
  reg [15:0] prescale_r;
  reg [3:0]  csidle_val_r;
  reg [7:0]  csidle_hold_r;
  reg        ie_tx_empty_r, ie_rx_avail_r, ie_done_r, ie_error_r;

  // Write decode
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      lane_mode_r    <= 2'b00;
      cpol_r         <= 1'b0;
      cpha_r         <= 1'b0;
      lsb_first_r    <= 1'b0;
      addr_len_r     <= 3'd0;
      data_len_r     <= 8'd0;
      prescale_r     <= 16'd0;
      csidle_val_r   <= 4'hF;
      csidle_hold_r  <= 8'd1;
      ie_tx_empty_r  <= 1'b0;
      ie_rx_avail_r  <= 1'b0;
      ie_done_r      <= 1'b0;
      ie_error_r     <= 1'b0;
      ctrl_start_o   <= 1'b0;
      ctrl_sw_reset_o <= 1'b0;
      txdata_valid_o <= 1'b0;
      txdata_o       <= 8'd0;
      w1c_done_o     <= 1'b0;
      w1c_error_o    <= 1'b0;
    end else begin
      // Default pulse clears
      ctrl_start_o   <= 1'b0;
      ctrl_sw_reset_o <= 1'b0;
      txdata_valid_o <= 1'b0;
      w1c_done_o     <= 1'b0;
      w1c_error_o    <= 1'b0;

      if (access_phase && PWRITE && valid_addr) begin
        case (byte_addr)
          CTRL: begin
            lane_mode_r    <= PWDATA[3:2];
            cpol_r         <= PWDATA[4];
            cpha_r         <= PWDATA[5];
            lsb_first_r    <= PWDATA[6];
            addr_len_r     <= PWDATA[10:8];
            data_len_r     <= PWDATA[18:11];
            ctrl_start_o   <= PWDATA[0];
            ctrl_sw_reset_o <= PWDATA[1];
          end
          PRESCALE: prescale_r <= PWDATA[15:0];
          TXDATA: begin
            txdata_o       <= PWDATA[7:0];
            txdata_valid_o <= 1'b1;
          end
          CS_IDLE: begin
            csidle_val_r   <= PWDATA[3:0];
            csidle_hold_r  <= PWDATA[15:8];
          end
          IE: begin
            ie_tx_empty_r  <= PWDATA[0];
            ie_rx_avail_r  <= PWDATA[1];
            ie_done_r      <= PWDATA[2];
            ie_error_r     <= PWDATA[3];
          end
          // STATUS: W1C on STATUS register (write with data bits)
          STATUS: begin
            w1c_done_o  <= PWDATA[4];
            w1c_error_o <= PWDATA[6];
          end
          default: ;
        endcase
      end
    end
  end

  // Read decode (combinational)
  always @(*) begin
    case (byte_addr)
      CTRL:     PRDATA = {13'd0, data_len_r, 1'b0, addr_len_r, lsb_first_r, cpha_r, cpol_r, lane_mode_r, 2'b00};
      STATUS:   PRDATA = {25'd0, status_error_i, busy_i, status_done_i, rx_empty_i, rx_full_i, tx_empty_i, tx_full_i};
      PRESCALE: PRDATA = {16'd0, prescale_r};
      TXDATA:   PRDATA = 32'd0;  // WO
      RXDATA:   PRDATA = {24'd0, rxdata_i};
      CS_IDLE:  PRDATA = {16'd0, csidle_hold_r, 4'd0, csidle_val_r};
      IE:       PRDATA = {28'd0, ie_error_r, ie_done_r, ie_rx_avail_r, ie_tx_empty_r};
      DEBUG:    PRDATA = {12'd0, rx_count_i, tx_count_i, io_in_i, io_oe_i, fsm_state_i};
      default:  PRDATA = 32'd0;
    endcase
  end

  // Continuous output assignments
  assign ctrl_lane_mode_o  = lane_mode_r;
  assign ctrl_cpol_o       = cpol_r;
  assign ctrl_cpha_o       = cpha_r;
  assign ctrl_lsb_first_o  = lsb_first_r;
  assign ctrl_addr_len_o   = addr_len_r;
  assign ctrl_data_len_o   = data_len_r;
  assign prescale_div_o    = prescale_r;
  assign csidle_val_o      = csidle_val_r;
  assign csidle_hold_o     = csidle_hold_r;
  assign ie_tx_empty_o     = ie_tx_empty_r;
  assign ie_rx_avail_o     = ie_rx_avail_r;
  assign ie_done_o         = ie_done_r;
  assign ie_error_o        = ie_error_r;

endmodule
