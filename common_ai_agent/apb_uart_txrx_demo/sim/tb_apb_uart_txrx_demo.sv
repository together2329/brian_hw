`timescale 1ns/1ps

module tb_apb_uart_txrx_demo;
  localparam integer APB_ADDR_WIDTH = 8;
  localparam integer BAUD_DIV_WIDTH = 16;
  localparam integer CLK_PERIOD = 10;

  localparam [7:0] A_CTRL        = 8'h00;
  localparam [7:0] A_STATUS      = 8'h04;
  localparam [7:0] A_BAUD_DIV    = 8'h08;
  localparam [7:0] A_TXDATA      = 8'h0c;
  localparam [7:0] A_RXDATA      = 8'h10;
  localparam [7:0] A_IRQ_STATUS  = 8'h14;
  localparam [7:0] A_FRAME_CFG   = 8'h18;
  localparam [7:0] A_FIFO_CTRL   = 8'h1c;
  localparam [7:0] A_FIFO_STATUS = 8'h20;
  localparam [7:0] A_FIFO_THRESH = 8'h24;
  localparam [7:0] A_RX_TIMEOUT  = 8'h28;
  localparam [7:0] A_SCRATCH     = 8'h2c;

  reg pclk;
  reg preset_n;
  reg psel;
  reg penable;
  reg pwrite;
  reg [APB_ADDR_WIDTH-1:0] paddr;
  reg [31:0] pwdata;
  wire [31:0] prdata;
  wire pready;
  wire pslverr;
  wire uart_tx;
  reg uart_rx;
  wire irq;

  integer scoreboard_pass;
  integer scoreboard_fail;
  integer scenario_count;
  integer csv_fd;
  integer json_fd;
  integer baud_div;
  reg [1023:0] current_scenario;

  // Coarse functional coverage flags emitted in sim_results.json.  The
  // run_sim.sh post-processor consumes scoreboard rows today; these flags keep
  // the testbench itself self-describing for v2+ feature coverage.
  reg cov_apb_regs, cov_invalid, cov_tx_zero, cov_tx_ff, cov_tx_random;
  reg cov_rx_zero, cov_rx_ff, cov_rx_random, cov_tx_busy_empty, cov_rx_valid_clear;
  reg cov_tx_irq, cov_rx_irq, cov_err_irq, cov_frame_err, cov_overrun;
  reg cov_baud_min, cov_baud_default, cov_baud_alt, cov_tx_b2b, cov_rx_b2b;
  reg cov_frame_cfg, cov_tx_7bit, cov_tx_5bit, cov_rx_7bit, cov_rx_5bit;
  reg cov_tx_parity, cov_rx_parity_good, cov_rx_parity_error;
  reg cov_tx_stop2, cov_rx_stop2, cov_tx_fifo_burst, cov_rx_fifo_order;
  reg cov_tx_fifo_full, cov_fifo_clear, cov_fifo_threshold_irq;
  reg cov_rx_timeout_irq, cov_loopback, cov_scratch, cov_break;

  apb_uart_txrx_demo #(
    .APB_ADDR_WIDTH(APB_ADDR_WIDTH),
    .BAUD_DIV_WIDTH(BAUD_DIV_WIDTH)
  ) dut (
    .pclk(pclk), .preset_n(preset_n), .psel(psel), .penable(penable), .pwrite(pwrite),
    .paddr(paddr), .pwdata(pwdata), .prdata(prdata), .pready(pready), .pslverr(pslverr),
    .uart_tx(uart_tx), .uart_rx(uart_rx), .irq(irq)
  );

  initial begin
    pclk = 1'b0;
    forever #(CLK_PERIOD/2) pclk = ~pclk;
  end

  function automatic parity_for_width;
    input [7:0] data;
    input integer data_bits;
    input parity_odd;
    integer i;
    reg parity_xor;
    begin
      parity_xor = 1'b0;
      for (i = 0; i < data_bits; i = i + 1) begin
        parity_xor = parity_xor ^ data[i];
      end
      parity_for_width = parity_odd ? ~parity_xor : parity_xor;
    end
  endfunction

  task log_event;
    input [1023:0] scenario;
    input [1023:0] check_name;
    input pass;
    input [1023:0] detail;
    begin
      if (pass) scoreboard_pass = scoreboard_pass + 1; else scoreboard_fail = scoreboard_fail + 1;
      $fdisplay(csv_fd, "%0t,%0s,%0s,%0s,%0s", $time, scenario, check_name, pass ? "PASS" : "FAIL", detail);
      if (!pass) $display("FAIL %0s %0s: %0s", scenario, check_name, detail);
    end
  endtask

  task start_scenario;
    input [1023:0] scenario;
    begin
      current_scenario = scenario;
      scenario_count = scenario_count + 1;
      $display("SCENARIO %0s", scenario);
      $fdisplay(csv_fd, "%0t,%0s,SCENARIO_START,PASS,start", $time, scenario);
    end
  endtask

  task expect_eq32;
    input [1023:0] name;
    input [31:0] actual;
    input [31:0] expected;
    reg [1023:0] d;
    begin
      $sformat(d, "actual=0x%08x expected=0x%08x", actual, expected);
      log_event(current_scenario, name, actual === expected, d);
    end
  endtask

  task expect_mask32;
    input [1023:0] name;
    input [31:0] actual;
    input [31:0] mask;
    input [31:0] expected;
    reg [1023:0] d;
    begin
      $sformat(d, "actual=0x%08x mask=0x%08x expected_masked=0x%08x", actual, mask, expected);
      log_event(current_scenario, name, (actual & mask) === expected, d);
    end
  endtask

  task expect_bit;
    input [1023:0] name;
    input actual;
    input expected;
    reg [1023:0] d;
    begin
      $sformat(d, "actual=%0b expected=%0b", actual, expected);
      log_event(current_scenario, name, actual === expected, d);
    end
  endtask

  task apb_write;
    input [7:0] addr;
    input [31:0] data;
    output err;
    begin
      @(posedge pclk);
      psel <= 1'b1; penable <= 1'b0; pwrite <= 1'b1; paddr <= addr; pwdata <= data;
      @(posedge pclk);
      penable <= 1'b1;
      #1 err = pslverr;
      @(posedge pclk);
      psel <= 1'b0; penable <= 1'b0; pwrite <= 1'b0; paddr <= '0; pwdata <= '0;
    end
  endtask

  task apb_read;
    input [7:0] addr;
    output [31:0] data;
    output err;
    begin
      @(posedge pclk);
      psel <= 1'b1; penable <= 1'b0; pwrite <= 1'b0; paddr <= addr; pwdata <= '0;
      @(posedge pclk);
      penable <= 1'b1;
      #1 data = prdata; err = pslverr;
      @(posedge pclk);
      psel <= 1'b0; penable <= 1'b0; paddr <= '0;
    end
  endtask

  task set_baud;
    input integer div;
    reg err;
    begin
      baud_div = div;
      apb_write(A_BAUD_DIV, div, err);
      if (div == 1) cov_baud_min = 1'b1;
      if (div == 4) cov_baud_default = 1'b1;
      if (div != 1 && div != 4) cov_baud_alt = 1'b1;
    end
  endtask

  task wait_tx_done;
    integer k;
    reg [31:0] r;
    reg err;
    begin
      for (k = 0; k < 4000; k = k + 1) begin
        apb_read(A_STATUS, r, err);
        if (!err && r[1] && !r[2]) k = 4000;
      end
    end
  endtask

  task wait_status_mask;
    input [31:0] mask;
    input [31:0] expected;
    input integer max_reads;
    output [31:0] data;
    output err;
    integer k;
    begin
      data = 32'h0;
      err = 1'b0;
      for (k = 0; k < max_reads; k = k + 1) begin
        apb_read(A_STATUS, data, err);
        if (!err && ((data & mask) == expected)) k = max_reads;
      end
    end
  endtask

  task tx_decode_frame;
    input integer data_bits;
    input parity_en;
    input stop2_cfg;
    output [7:0] data;
    output parity_bit;
    output stop1_bit;
    output stop2_bit;
    integer i;
    begin
      data = 8'h00;
      parity_bit = 1'b0;
      stop1_bit = 1'bx;
      stop2_bit = 1'bx;
      wait (uart_tx === 1'b0);
      #(CLK_PERIOD*baud_div + CLK_PERIOD/2);
      for (i = 0; i < data_bits; i = i + 1) begin
        data[i] = uart_tx;
        #(CLK_PERIOD*baud_div);
      end
      if (parity_en) begin
        parity_bit = uart_tx;
        #(CLK_PERIOD*baud_div);
      end
      stop1_bit = uart_tx;
      #(CLK_PERIOD*baud_div);
      if (stop2_cfg) begin
        stop2_bit = uart_tx;
        #(CLK_PERIOD*baud_div);
      end
    end
  endtask

  task tx_decode_byte;
    output [7:0] b;
    reg parity_bit;
    reg stop1_bit;
    reg stop2_bit;
    begin
      tx_decode_frame(8, 1'b0, 1'b0, b, parity_bit, stop1_bit, stop2_bit);
    end
  endtask

  task send_rx_frame;
    input [7:0] b;
    input integer data_bits;
    input parity_en;
    input parity_odd;
    input stop2_cfg;
    input good_parity;
    input good_stop1;
    input good_stop2;
    integer i;
    reg parity_bit;
    begin
      uart_rx <= 1'b1;
      repeat (3) @(posedge pclk);
      uart_rx <= 1'b0; repeat (baud_div) @(posedge pclk);
      for (i = 0; i < data_bits; i = i + 1) begin
        uart_rx <= b[i]; repeat (baud_div) @(posedge pclk);
      end
      if (parity_en) begin
        parity_bit = parity_for_width(b, data_bits, parity_odd);
        if (!good_parity) parity_bit = ~parity_bit;
        uart_rx <= parity_bit; repeat (baud_div) @(posedge pclk);
      end
      uart_rx <= good_stop1 ? 1'b1 : 1'b0; repeat (baud_div) @(posedge pclk);
      if (stop2_cfg) begin
        uart_rx <= good_stop2 ? 1'b1 : 1'b0; repeat (baud_div) @(posedge pclk);
      end
      uart_rx <= 1'b1; repeat (3*baud_div) @(posedge pclk);
    end
  endtask

  task send_rx_byte;
    input [7:0] b;
    input good_stop;
    begin
      send_rx_frame(b, 8, 1'b0, 1'b0, 1'b0, 1'b1, good_stop, 1'b1);
    end
  endtask

  task drive_uart_bit_with_optional_glitch;
    input bit_value;
    input integer glitch_cycle;
    integer c;
    begin
      for (c = 0; c < baud_div; c = c + 1) begin
        uart_rx <= (c == glitch_cycle) ? ~bit_value : bit_value;
        @(posedge pclk);
      end
      uart_rx <= bit_value;
    end
  endtask

  task send_rx_byte_with_center_glitches;
    input [7:0] b;
    input good_stop;
    integer i;
    integer glitch_cycle;
    begin
      // With BAUD_DIV=32 this targets one synchronized center sample while
      // leaving neighboring early/late samples correct for majority vote.
      glitch_cycle = (baud_div > 4) ? ((baud_div >> 1) + 1) : -1;
      uart_rx <= 1'b1;
      repeat (3) @(posedge pclk);
      drive_uart_bit_with_optional_glitch(1'b0, -1);
      for (i = 0; i < 8; i = i + 1) begin
        drive_uart_bit_with_optional_glitch(b[i], glitch_cycle);
      end
      drive_uart_bit_with_optional_glitch(good_stop ? 1'b1 : 1'b0, glitch_cycle);
      uart_rx <= 1'b1;
      repeat (3*baud_div) @(posedge pclk);
    end
  endtask

  task send_rx_false_start_glitch;
    begin
      uart_rx <= 1'b1;
      repeat (4) @(posedge pclk);
      uart_rx <= 1'b0;
      repeat (4) @(posedge pclk);
      uart_rx <= 1'b1;
      repeat (3*baud_div) @(posedge pclk);
    end
  endtask

  task send_rx_break;
    begin
      uart_rx <= 1'b1;
      repeat (3) @(posedge pclk);
      uart_rx <= 1'b0;
      repeat (12*baud_div) @(posedge pclk);
      uart_rx <= 1'b1;
      repeat (4*baud_div) @(posedge pclk);
    end
  endtask

  task reset_dut;
    begin
      psel <= 0; penable <= 0; pwrite <= 0; paddr <= 0; pwdata <= 0; uart_rx <= 1'b1;
      preset_n <= 1'b0;
      repeat (5) @(posedge pclk);
      preset_n <= 1'b1;
      repeat (5) @(posedge pclk);
      baud_div = 4;
    end
  endtask

  task sc_apb_reset;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_APB_RESET"); reset_dut();
      apb_read(A_CTRL, r, err); expect_eq32("CTRL_RESET", r, 32'h1); expect_bit("CTRL_ERR", err, 0);
      apb_read(A_STATUS, r, err); expect_eq32("STATUS_RESET", r, 32'h0000_0802);
      apb_read(A_BAUD_DIV, r, err); expect_eq32("BAUD_RESET", r, 32'h4);
      expect_bit("UART_TX_IDLE", uart_tx, 1'b1);
      cov_apb_regs = 1'b1;
    end
  endtask

  task sc_apb_rw;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_APB_RW"); reset_dut();
      apb_write(A_CTRL, 32'hffff_ffff, err); expect_bit("CTRL_WRITE_ERR", err, 0);
      apb_read(A_CTRL, r, err); expect_eq32("CTRL_MASK", r, 32'h0000_01ef);
      apb_write(A_CTRL, 32'h0000_0001, err);
      apb_write(A_BAUD_DIV, 32'h0, err); apb_read(A_BAUD_DIV, r, err); expect_eq32("BAUD_ZERO_COERCE", r, 32'h1); cov_baud_min = 1;
      set_baud(4);
    end
  endtask

  task sc_apb_invalid;
    reg [31:0] r0, r1; reg err;
    begin
      start_scenario("SC_APB_INVALID"); reset_dut();
      apb_read(A_CTRL, r0, err); apb_write(8'h80, 32'h1234, err); expect_bit("INVALID_WRITE_ERR", err, 1);
      apb_read(A_CTRL, r1, err); expect_eq32("INVALID_PRESERVE", r1, r0);
      apb_read(8'h84, r1, err); expect_bit("INVALID_READ_ERR", err, 1); cov_invalid = 1;
    end
  endtask

  task sc_tx_one_byte;
    reg err; reg [7:0] d;
    begin
      start_scenario("SC_TX_ONE_BYTE"); reset_dut(); set_baud(4);
      fork
        tx_decode_byte(d);
        begin apb_write(A_TXDATA, 32'h000000a5, err); wait_tx_done(); end
      join
      expect_eq32("TX_DECODE_A5", {24'h0,d}, 32'h000000a5); cov_tx_random=1; cov_tx_busy_empty=1;
    end
  endtask

  task sc_tx_back_to_back;
    reg err; reg [7:0] d1,d2;
    begin
      start_scenario("SC_TX_BACK_TO_BACK"); reset_dut(); set_baud(4);
      fork tx_decode_byte(d1); begin apb_write(A_TXDATA, 8'h00, err); wait_tx_done(); end join
      fork tx_decode_byte(d2); begin apb_write(A_TXDATA, 8'hff, err); wait_tx_done(); end join
      expect_eq32("TX_B2B_FIRST", {24'h0,d1}, 32'h0); expect_eq32("TX_B2B_SECOND", {24'h0,d2}, 32'hff);
      cov_tx_zero=1; cov_tx_ff=1; cov_tx_b2b=1;
    end
  endtask

  task sc_tx_irq;
    reg err; reg [31:0] r;
    begin
      start_scenario("SC_TX_IRQ"); reset_dut(); set_baud(4); apb_write(A_CTRL, 32'h3, err);
      apb_write(A_TXDATA, 8'h55, err); wait_tx_done(); repeat(2) @(posedge pclk);
      expect_bit("TX_IRQ_ASSERT", irq, 1); apb_read(A_IRQ_STATUS, r, err); expect_eq32("TX_IRQ_STATUS", r & 32'h1, 32'h1);
      apb_write(A_IRQ_STATUS, 32'h1, err); repeat(2) @(posedge pclk); expect_bit("TX_IRQ_CLEAR", irq, 0); cov_tx_irq=1;
    end
  endtask

  task sc_rx_one_byte;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_ONE_BYTE"); reset_dut(); set_baud(4); send_rx_byte(8'h3c, 1);
      apb_read(A_STATUS, r, err); expect_eq32("RX_VALID_SET", r & 32'h1, 32'h1);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_DATA_3C", r, 32'h3c);
      apb_read(A_STATUS, r, err); expect_eq32("RX_VALID_CLEAR", r & 32'h1, 32'h0); cov_rx_random=1; cov_rx_valid_clear=1;
    end
  endtask

  task sc_rx_back_to_back;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_BACK_TO_BACK"); reset_dut(); set_baud(4);
      send_rx_byte(8'h00, 1); apb_read(A_RXDATA, r, err); expect_eq32("RX_B2B_FIRST", r, 32'h0);
      send_rx_byte(8'hff, 1); apb_read(A_RXDATA, r, err); expect_eq32("RX_B2B_SECOND", r, 32'hff);
      cov_rx_zero=1; cov_rx_ff=1; cov_rx_b2b=1;
    end
  endtask

  task sc_rx_framing_error;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_FRAMING_ERROR"); reset_dut(); set_baud(4); apb_write(A_CTRL, 32'h9, err); send_rx_byte(8'h12, 0);
      apb_read(A_STATUS, r, err); expect_eq32("FRAME_ERR_STATUS", r & 32'h8, 32'h8); expect_bit("ERR_IRQ_FRAME", irq, 1);
      apb_write(A_STATUS, 32'h8, err); apb_write(A_IRQ_STATUS, 32'h4, err); cov_frame_err=1; cov_err_irq=1;
    end
  endtask

  task sc_rx_overrun;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_OVERRUN"); reset_dut(); set_baud(4);
      send_rx_byte(8'h11, 1); send_rx_byte(8'h22, 1); send_rx_byte(8'h33, 1); send_rx_byte(8'h44, 1); send_rx_byte(8'h55, 1);
      apb_read(A_STATUS, r, err); expect_eq32("OVERRUN_STATUS", r & 32'h10, 32'h10);
      apb_read(A_RXDATA, r, err); expect_eq32("OVERRUN_PRESERVE", r, 32'h11); cov_overrun=1;
    end
  endtask

  task sc_rx_irq;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_IRQ"); reset_dut(); set_baud(4); apb_write(A_CTRL, 32'h5, err); send_rx_byte(8'h77, 1);
      expect_bit("RX_IRQ_ASSERT", irq, 1); apb_read(A_RXDATA, r, err); repeat(2) @(posedge pclk); expect_bit("RX_IRQ_CLEAR", irq, 0); cov_rx_irq=1;
    end
  endtask

  task sc_baud_variants;
    reg err; reg [7:0] d; reg [31:0] r;
    begin
      start_scenario("SC_BAUD_VARIANTS"); reset_dut(); set_baud(8);
      fork tx_decode_byte(d); begin apb_write(A_TXDATA, 8'h5a, err); wait_tx_done(); end join
      expect_eq32("TX_BAUD8", {24'h0,d}, 32'h5a);
      send_rx_byte(8'ha6, 1); apb_read(A_RXDATA, r, err); expect_eq32("RX_BAUD8", r, 32'ha6);
    end
  endtask

  task sc_rx_majority_noise;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_MAJORITY_NOISE"); reset_dut(); set_baud(32);
      send_rx_byte_with_center_glitches(8'hc3, 1'b1);
      apb_read(A_STATUS, r, err); expect_eq32("RX_MAJORITY_VALID", r & 32'h0000_0001, 32'h0000_0001);
      expect_eq32("RX_MAJORITY_NO_ERRORS", r & 32'h0000_0018, 32'h0000_0000);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_MAJORITY_DATA_C3", r, 32'h0000_00c3);
    end
  endtask

  task sc_rx_false_start_reject;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_FALSE_START"); reset_dut(); set_baud(32);
      send_rx_false_start_glitch();
      apb_read(A_STATUS, r, err); expect_eq32("FALSE_START_NO_STATUS", r & 32'h0000_0019, 32'h0000_0000);
      send_rx_byte(8'h96, 1'b1);
      apb_read(A_RXDATA, r, err); expect_eq32("FALSE_START_RECOVERY_DATA", r, 32'h0000_0096);
    end
  endtask

  task sc_frame_config;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_FRAME_CFG"); reset_dut();
      apb_read(A_FRAME_CFG, r, err); expect_eq32("FRAME_CFG_RESET_8N1", r, 32'h0000_0003);
      apb_write(A_FRAME_CFG, 32'h0000_001c, err); expect_bit("FRAME_CFG_WRITE_ERR", err, 0);
      apb_read(A_FRAME_CFG, r, err); expect_eq32("FRAME_CFG_READBACK_5O2", r, 32'h0000_001c);
      cov_frame_cfg = 1'b1;
    end
  endtask

  task sc_tx_data_widths;
    reg err; reg [7:0] d; reg p; reg s1; reg s2;
    begin
      start_scenario("SC_TX_DATA_WIDTHS"); reset_dut(); set_baud(4);
      apb_write(A_FRAME_CFG, 32'h0000_0002, err);
      fork tx_decode_frame(7, 1'b0, 1'b0, d, p, s1, s2); begin apb_write(A_TXDATA, 8'hff, err); wait_tx_done(); end join
      expect_eq32("TX_7BIT_MASK", {24'h0,d}, 32'h0000_007f); expect_bit("TX_7BIT_STOP_AFTER_DATA", s1, 1'b1);
      apb_write(A_FRAME_CFG, 32'h0000_0000, err);
      fork tx_decode_frame(5, 1'b0, 1'b0, d, p, s1, s2); begin apb_write(A_TXDATA, 8'hff, err); wait_tx_done(); end join
      expect_eq32("TX_5BIT_MASK", {24'h0,d}, 32'h0000_001f); expect_bit("TX_5BIT_STOP_AFTER_DATA", s1, 1'b1);
      cov_tx_7bit = 1'b1; cov_tx_5bit = 1'b1;
    end
  endtask

  task sc_rx_data_widths;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_DATA_WIDTHS"); reset_dut(); set_baud(4);
      apb_write(A_FRAME_CFG, 32'h0000_0002, err);
      send_rx_frame(8'hff, 7, 1'b0, 1'b0, 1'b0, 1'b1, 1'b1, 1'b1);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_7BIT_MASK", r, 32'h0000_007f);
      apb_write(A_FRAME_CFG, 32'h0000_0000, err);
      send_rx_frame(8'hff, 5, 1'b0, 1'b0, 1'b0, 1'b1, 1'b1, 1'b1);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_5BIT_MASK", r, 32'h0000_001f);
      cov_rx_7bit = 1'b1; cov_rx_5bit = 1'b1;
    end
  endtask

  task sc_tx_parity_even_odd;
    reg err; reg [7:0] d; reg p; reg s1; reg s2;
    begin
      start_scenario("SC_TX_PARITY_EVEN_ODD"); reset_dut(); set_baud(4);
      apb_write(A_FRAME_CFG, 32'h0000_0007, err); // 8 data, even parity, 1 stop
      fork tx_decode_frame(8, 1'b1, 1'b0, d, p, s1, s2); begin apb_write(A_TXDATA, 8'ha5, err); wait_tx_done(); end join
      expect_eq32("TX_PARITY_EVEN_DATA", {24'h0,d}, 32'h0000_00a5); expect_bit("TX_PARITY_EVEN_BIT", p, 1'b0);
      apb_write(A_FRAME_CFG, 32'h0000_000f, err); // 8 data, odd parity, 1 stop
      fork tx_decode_frame(8, 1'b1, 1'b0, d, p, s1, s2); begin apb_write(A_TXDATA, 8'ha5, err); wait_tx_done(); end join
      expect_eq32("TX_PARITY_ODD_DATA", {24'h0,d}, 32'h0000_00a5); expect_bit("TX_PARITY_ODD_BIT", p, 1'b1);
      cov_tx_parity = 1'b1;
    end
  endtask

  task sc_rx_parity_good;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_PARITY_GOOD"); reset_dut(); set_baud(4);
      apb_write(A_FRAME_CFG, 32'h0000_0007, err);
      send_rx_frame(8'ha5, 8, 1'b1, 1'b0, 1'b0, 1'b1, 1'b1, 1'b1);
      apb_read(A_STATUS, r, err); expect_eq32("RX_PARITY_EVEN_NOERR", r & 32'h0000_0108, 32'h0000_0000);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_PARITY_EVEN_DATA", r, 32'h0000_00a5);
      apb_write(A_FRAME_CFG, 32'h0000_000f, err);
      send_rx_frame(8'h5a, 8, 1'b1, 1'b1, 1'b0, 1'b1, 1'b1, 1'b1);
      apb_read(A_STATUS, r, err); expect_eq32("RX_PARITY_ODD_NOERR", r & 32'h0000_0108, 32'h0000_0000);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_PARITY_ODD_DATA", r, 32'h0000_005a);
      cov_rx_parity_good = 1'b1;
    end
  endtask

  task sc_rx_parity_error;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_PARITY_ERROR"); reset_dut(); set_baud(4);
      apb_write(A_CTRL, 32'h0000_0009, err); // enable + error IRQ enable
      apb_write(A_FRAME_CFG, 32'h0000_0007, err);
      send_rx_frame(8'h55, 8, 1'b1, 1'b0, 1'b0, 1'b0, 1'b1, 1'b1);
      apb_read(A_STATUS, r, err); expect_eq32("RX_PARITY_ERR_STATUS", r & 32'h0000_0100, 32'h0000_0100); expect_bit("RX_PARITY_ERR_IRQ", irq, 1'b1);
      apb_read(A_IRQ_STATUS, r, err); expect_eq32("RX_PARITY_ERR_IRQ_STATUS", r & 32'h0000_0004, 32'h0000_0004);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_PARITY_ERR_DATA_PRESERVED", r, 32'h0000_0055);
      cov_rx_parity_error = 1'b1; cov_err_irq = 1'b1;
    end
  endtask

  task sc_tx_stop2;
    reg err; reg [7:0] d; reg p; reg s1; reg s2;
    begin
      start_scenario("SC_TX_STOP2"); reset_dut(); set_baud(4);
      apb_write(A_FRAME_CFG, 32'h0000_0013, err);
      fork tx_decode_frame(8, 1'b0, 1'b1, d, p, s1, s2); begin apb_write(A_TXDATA, 8'hc6, err); wait_tx_done(); end join
      expect_eq32("TX_STOP2_DATA", {24'h0,d}, 32'h0000_00c6); expect_bit("TX_STOP2_STOP1", s1, 1'b1); expect_bit("TX_STOP2_STOP2", s2, 1'b1);
      cov_tx_stop2 = 1'b1;
    end
  endtask

  task sc_rx_stop2;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_STOP2"); reset_dut(); set_baud(4);
      apb_write(A_FRAME_CFG, 32'h0000_0013, err);
      send_rx_frame(8'h6c, 8, 1'b0, 1'b0, 1'b1, 1'b1, 1'b1, 1'b1);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_STOP2_GOOD_DATA", r, 32'h0000_006c);
      send_rx_frame(8'h2d, 8, 1'b0, 1'b0, 1'b1, 1'b1, 1'b1, 1'b0);
      apb_read(A_STATUS, r, err); expect_eq32("RX_STOP2_BAD_FRAME_ERR", r & 32'h0000_0008, 32'h0000_0008);
      cov_rx_stop2 = 1'b1; cov_frame_err = 1'b1;
    end
  endtask

  task sc_tx_fifo_burst;
    reg err; reg [7:0] d0,d1,d2,d3; reg p; reg s1; reg s2;
    begin
      start_scenario("SC_TX_FIFO_BURST"); reset_dut(); set_baud(16);
      fork
        begin
          tx_decode_frame(8, 1'b0, 1'b0, d0, p, s1, s2);
          tx_decode_frame(8, 1'b0, 1'b0, d1, p, s1, s2);
          tx_decode_frame(8, 1'b0, 1'b0, d2, p, s1, s2);
          tx_decode_frame(8, 1'b0, 1'b0, d3, p, s1, s2);
        end
        begin
          apb_write(A_TXDATA, 8'h10, err); expect_bit("TX_FIFO_BURST_WR0", err, 1'b0);
          apb_write(A_TXDATA, 8'h20, err); expect_bit("TX_FIFO_BURST_WR1", err, 1'b0);
          apb_write(A_TXDATA, 8'h30, err); expect_bit("TX_FIFO_BURST_WR2", err, 1'b0);
          apb_write(A_TXDATA, 8'h40, err); expect_bit("TX_FIFO_BURST_WR3", err, 1'b0);
        end
      join
      expect_eq32("TX_FIFO_BURST_D0", {24'h0,d0}, 32'h0000_0010);
      expect_eq32("TX_FIFO_BURST_D1", {24'h0,d1}, 32'h0000_0020);
      expect_eq32("TX_FIFO_BURST_D2", {24'h0,d2}, 32'h0000_0030);
      expect_eq32("TX_FIFO_BURST_D3", {24'h0,d3}, 32'h0000_0040);
      cov_tx_fifo_burst = 1'b1;
    end
  endtask

  task sc_rx_fifo_order;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_FIFO_ORDER"); reset_dut(); set_baud(4);
      send_rx_byte(8'h10, 1); send_rx_byte(8'h20, 1); send_rx_byte(8'h30, 1); send_rx_byte(8'h40, 1);
      apb_read(A_FIFO_STATUS, r, err); expect_eq32("RX_FIFO_LEVEL4", r[15:8], 32'h0000_0004);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_FIFO_ORDER0", r, 32'h0000_0010);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_FIFO_ORDER1", r, 32'h0000_0020);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_FIFO_ORDER2", r, 32'h0000_0030);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_FIFO_ORDER3", r, 32'h0000_0040);
      cov_rx_fifo_order = 1'b1;
    end
  endtask

  task sc_tx_fifo_full;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_TX_FIFO_FULL"); reset_dut(); set_baud(32);
      apb_write(A_CTRL, 32'h0000_0021, err); // enable + TX break blocks FIFO drain
      apb_write(A_TXDATA, 8'h01, err); expect_bit("TX_FIFO_FILL0", err, 1'b0);
      apb_write(A_TXDATA, 8'h02, err); expect_bit("TX_FIFO_FILL1", err, 1'b0);
      apb_write(A_TXDATA, 8'h03, err); expect_bit("TX_FIFO_FILL2", err, 1'b0);
      apb_write(A_TXDATA, 8'h04, err); expect_bit("TX_FIFO_FILL3", err, 1'b0);
      apb_read(A_FIFO_STATUS, r, err); expect_eq32("TX_FIFO_FULL_LEVEL", r[7:0], 32'h0000_0004); expect_bit("TX_FIFO_FULL_STATUS", r[17], 1'b1);
      apb_write(A_TXDATA, 8'h05, err); expect_bit("TX_FIFO_FULL_WRITE_ERR", err, 1'b1);
      cov_tx_fifo_full = 1'b1;
    end
  endtask

  task sc_fifo_clear;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_FIFO_CLEAR"); reset_dut(); set_baud(16);
      apb_write(A_CTRL, 32'h0000_0021, err);
      apb_write(A_TXDATA, 8'haa, err); apb_write(A_TXDATA, 8'hbb, err);
      send_rx_byte(8'hcc, 1); send_rx_byte(8'hdd, 1);
      apb_read(A_FIFO_STATUS, r, err); expect_eq32("FIFO_CLEAR_PRE_LEVELS", r[15:0], 32'h0000_0202);
      apb_write(A_FIFO_CTRL, 32'h0000_0003, err); expect_bit("FIFO_CLEAR_WRITE_ERR", err, 1'b0);
      repeat (2) @(posedge pclk);
      apb_read(A_FIFO_STATUS, r, err); expect_bit("FIFO_CLEAR_TX_EMPTY", r[16], 1'b1); expect_bit("FIFO_CLEAR_RX_EMPTY", r[18], 1'b1);
      apb_read(A_STATUS, r, err); expect_eq32("FIFO_CLEAR_RX_VALID_CLEAR", r & 32'h1, 32'h0);
      cov_fifo_clear = 1'b1;
    end
  endtask

  task sc_fifo_threshold_irq;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_FIFO_THRESHOLD_IRQ"); reset_dut(); set_baud(16);
      apb_write(A_FIFO_THRESH, 32'h0000_0200, err); // tx threshold 0, rx threshold 2
      apb_write(A_CTRL, 32'h0000_0121, err); // enable + tx_break + fifo_irq_en
      apb_write(A_TXDATA, 8'h99, err); // keep TX level above threshold, so only RX threshold can assert
      repeat (2) @(posedge pclk); expect_bit("FIFO_THRESH_IRQ_IDLE", irq, 1'b0);
      send_rx_byte(8'h11, 1); repeat (2) @(posedge pclk); expect_bit("FIFO_THRESH_IRQ_BELOW_RX", irq, 1'b0);
      send_rx_byte(8'h22, 1); repeat (2) @(posedge pclk); expect_bit("FIFO_THRESH_IRQ_ASSERT", irq, 1'b1);
      apb_read(A_STATUS, r, err); expect_eq32("FIFO_THRESH_STATUS_RX", r & 32'h0000_1000, 32'h0000_1000);
      apb_read(A_IRQ_STATUS, r, err); expect_eq32("FIFO_THRESH_IRQ_STATUS_RX", r & 32'h0000_0020, 32'h0000_0020);
      cov_fifo_threshold_irq = 1'b1;
    end
  endtask

  task sc_rx_timeout_irq;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_RX_TIMEOUT_IRQ"); reset_dut(); set_baud(4);
      apb_write(A_RX_TIMEOUT, 32'h0000_000c, err);
      apb_write(A_CTRL, 32'h0000_0081, err); // enable + timeout IRQ enable
      send_rx_byte(8'h5e, 1);
      repeat (40) @(posedge pclk);
      apb_read(A_STATUS, r, err); expect_eq32("RX_TIMEOUT_STATUS", r & 32'h0000_0400, 32'h0000_0400); expect_bit("RX_TIMEOUT_IRQ_ASSERT", irq, 1'b1);
      apb_read(A_IRQ_STATUS, r, err); expect_eq32("RX_TIMEOUT_IRQ_STATUS", r & 32'h0000_0008, 32'h0000_0008);
      apb_read(A_RXDATA, r, err); expect_eq32("RX_TIMEOUT_DATA_BEFORE_CLEAR", r, 32'h0000_005e);
      apb_write(A_STATUS, 32'h0000_0400, err); apb_write(A_IRQ_STATUS, 32'h0000_0008, err); repeat (3) @(posedge pclk);
      expect_bit("RX_TIMEOUT_IRQ_CLEAR", irq, 1'b0);
      cov_rx_timeout_irq = 1'b1;
    end
  endtask

  task sc_loopback;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_LOOPBACK"); reset_dut(); set_baud(4);
      apb_write(A_CTRL, 32'h0000_0041, err); // enable + loopback
      apb_write(A_TXDATA, 32'h0000_003c, err); expect_bit("LOOPBACK_TX_WRITE_ERR", err, 1'b0);
      wait_status_mask(32'h0000_0001, 32'h0000_0001, 200, r, err);
      expect_eq32("LOOPBACK_RX_VALID", r & 32'h0000_0001, 32'h0000_0001);
      apb_read(A_RXDATA, r, err); expect_eq32("LOOPBACK_RX_DATA", r, 32'h0000_003c);
      cov_loopback = 1'b1;
    end
  endtask

  task sc_break;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_BREAK"); reset_dut(); set_baud(4);
      apb_write(A_CTRL, 32'h0000_0021, err); repeat (3) @(posedge pclk); expect_bit("TX_BREAK_LINE_LOW", uart_tx, 1'b0);
      apb_write(A_CTRL, 32'h0000_0001, err); repeat (3) @(posedge pclk); expect_bit("TX_BREAK_RELEASE_HIGH", uart_tx, 1'b1);
      apb_write(A_CTRL, 32'h0000_0009, err); // enable + error IRQ
      send_rx_break();
      apb_read(A_STATUS, r, err); expect_eq32("RX_BREAK_STATUS", r & 32'h0000_0200, 32'h0000_0200); expect_bit("RX_BREAK_IRQ", irq, 1'b1);
      cov_break = 1'b1; cov_err_irq = 1'b1;
    end
  endtask

  task sc_scratch;
    reg [31:0] r; reg err;
    begin
      start_scenario("SC_SCRATCH"); reset_dut();
      apb_write(A_SCRATCH, 32'hdead_beef, err); expect_bit("SCRATCH_WRITE_ERR", err, 1'b0);
      apb_read(A_SCRATCH, r, err); expect_eq32("SCRATCH_READBACK", r, 32'hdead_beef);
      apb_read(A_STATUS, r, err); expect_eq32("SCRATCH_NO_RX_VALID", r & 32'h0000_0001, 32'h0000_0000);
      cov_scratch = 1'b1;
    end
  endtask

  task write_results;
    begin
      json_fd = $fopen("sim/sim_results.json", "w");
      $fdisplay(json_fd, "{");
      $fdisplay(json_fd, "  \"passed\":%0s,", (scoreboard_fail==0)?"true":"false");
      $fdisplay(json_fd, "  \"scoreboard_pass\":%0d,", scoreboard_pass);
      $fdisplay(json_fd, "  \"scoreboard_fail\":%0d,", scoreboard_fail);
      $fdisplay(json_fd, "  \"scenario_count\":%0d,", scenario_count);
      $fdisplay(json_fd, "  \"coverage_flags\":{");
      $fdisplay(json_fd, "    \"legacy_apb\":%0s,", (cov_apb_regs && cov_invalid)?"true":"false");
      $fdisplay(json_fd, "    \"legacy_tx_rx_irq_error\":%0s,", (cov_tx_irq && cov_rx_irq && cov_err_irq && cov_frame_err && cov_overrun)?"true":"false");
      $fdisplay(json_fd, "    \"frame_cfg\":%0s,", cov_frame_cfg?"true":"false");
      $fdisplay(json_fd, "    \"data_widths\":%0s,", (cov_tx_7bit && cov_tx_5bit && cov_rx_7bit && cov_rx_5bit)?"true":"false");
      $fdisplay(json_fd, "    \"parity\":%0s,", (cov_tx_parity && cov_rx_parity_good && cov_rx_parity_error)?"true":"false");
      $fdisplay(json_fd, "    \"stop2\":%0s,", (cov_tx_stop2 && cov_rx_stop2)?"true":"false");
      $fdisplay(json_fd, "    \"fifo\":%0s,", (cov_tx_fifo_burst && cov_rx_fifo_order && cov_tx_fifo_full && cov_fifo_clear)?"true":"false");
      $fdisplay(json_fd, "    \"threshold_irq\":%0s,", cov_fifo_threshold_irq?"true":"false");
      $fdisplay(json_fd, "    \"timeout_irq\":%0s,", cov_rx_timeout_irq?"true":"false");
      $fdisplay(json_fd, "    \"loopback\":%0s,", cov_loopback?"true":"false");
      $fdisplay(json_fd, "    \"break_error\":%0s,", cov_break?"true":"false");
      $fdisplay(json_fd, "    \"scratch\":%0s", cov_scratch?"true":"false");
      $fdisplay(json_fd, "  }");
      $fdisplay(json_fd, "}");
      $fclose(json_fd);
    end
  endtask

  initial begin
    $dumpfile("sim/waves/apb_uart_txrx_demo.vcd");
    $dumpvars(0, tb_apb_uart_txrx_demo);
    scoreboard_pass=0; scoreboard_fail=0; scenario_count=0; baud_div=4;
    cov_apb_regs=0; cov_invalid=0; cov_tx_zero=0; cov_tx_ff=0; cov_tx_random=0; cov_rx_zero=0; cov_rx_ff=0; cov_rx_random=0;
    cov_tx_busy_empty=0; cov_rx_valid_clear=0; cov_tx_irq=0; cov_rx_irq=0; cov_err_irq=0; cov_frame_err=0; cov_overrun=0;
    cov_baud_min=0; cov_baud_default=0; cov_baud_alt=0; cov_tx_b2b=0; cov_rx_b2b=0;
    cov_frame_cfg=0; cov_tx_7bit=0; cov_tx_5bit=0; cov_rx_7bit=0; cov_rx_5bit=0;
    cov_tx_parity=0; cov_rx_parity_good=0; cov_rx_parity_error=0; cov_tx_stop2=0; cov_rx_stop2=0;
    cov_tx_fifo_burst=0; cov_rx_fifo_order=0; cov_tx_fifo_full=0; cov_fifo_clear=0; cov_fifo_threshold_irq=0;
    cov_rx_timeout_irq=0; cov_loopback=0; cov_scratch=0; cov_break=0;
    csv_fd = $fopen("sim/scoreboard_events.csv", "w");
    $fdisplay(csv_fd, "time,scenario,check,result,detail");
    preset_n=0; psel=0; penable=0; pwrite=0; paddr=0; pwdata=0; uart_rx=1;

    // Legacy directed scenarios retained.
    sc_apb_reset();
    sc_apb_rw();
    sc_apb_invalid();
    sc_tx_one_byte();
    sc_tx_back_to_back();
    sc_tx_irq();
    sc_rx_one_byte();
    sc_rx_back_to_back();
    sc_rx_framing_error();
    sc_rx_overrun();
    sc_rx_irq();
    sc_baud_variants();
    sc_rx_majority_noise();
    sc_rx_false_start_reject();

    // Enhanced v2+ directed scenarios.
    sc_frame_config();
    sc_tx_data_widths();
    sc_rx_data_widths();
    sc_tx_parity_even_odd();
    sc_rx_parity_good();
    sc_rx_parity_error();
    sc_tx_stop2();
    sc_rx_stop2();
    sc_tx_fifo_burst();
    sc_rx_fifo_order();
    sc_tx_fifo_full();
    sc_fifo_clear();
    sc_fifo_threshold_irq();
    sc_rx_timeout_irq();
    sc_loopback();
    sc_break();
    sc_scratch();

    write_results();
    $fclose(csv_fd);
    if (scoreboard_fail == 0) $display("SIM PASS scoreboard_pass=%0d scenarios=%0d", scoreboard_pass, scenario_count);
    else $display("SIM FAIL scoreboard_fail=%0d scoreboard_pass=%0d", scoreboard_fail, scoreboard_pass);
    #20 $finish;
  end
endmodule
