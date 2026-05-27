`timescale 1ns/1ps

module tb_apb_uart_txrx_demo;
  localparam integer APB_ADDR_WIDTH = 8;
  localparam integer BAUD_DIV_WIDTH = 16;
  localparam integer CLK_PERIOD = 10;

  localparam [7:0] A_CTRL       = 8'h00;
  localparam [7:0] A_STATUS     = 8'h04;
  localparam [7:0] A_BAUD_DIV   = 8'h08;
  localparam [7:0] A_TXDATA     = 8'h0c;
  localparam [7:0] A_RXDATA     = 8'h10;
  localparam [7:0] A_IRQ_STATUS = 8'h14;

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
  reg cov_apb_regs, cov_invalid, cov_tx_zero, cov_tx_ff, cov_tx_random;
  reg cov_rx_zero, cov_rx_ff, cov_rx_random, cov_tx_busy_empty, cov_rx_valid_clear;
  reg cov_tx_irq, cov_rx_irq, cov_err_irq, cov_frame_err, cov_overrun, cov_baud_min, cov_baud_default, cov_baud_alt;
  reg cov_tx_b2b, cov_rx_b2b;

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
      for (k = 0; k < 2000; k = k + 1) begin
        apb_read(A_STATUS, r, err);
        if (!err && r[1] && !r[2]) k = 2000;
      end
    end
  endtask

  task tx_decode_byte;
    output [7:0] b;
    integer i;
    begin
      wait (uart_tx === 1'b0);
      #(CLK_PERIOD*baud_div + CLK_PERIOD/2);
      for (i = 0; i < 8; i = i + 1) begin
        b[i] = uart_tx;
        #(CLK_PERIOD*baud_div);
      end
    end
  endtask

  task send_rx_byte;
    input [7:0] b;
    input good_stop;
    integer i;
    begin
      uart_rx <= 1'b1;
      repeat (3) @(posedge pclk);
      uart_rx <= 1'b0; repeat (baud_div) @(posedge pclk);
      for (i = 0; i < 8; i = i + 1) begin
        uart_rx <= b[i]; repeat (baud_div) @(posedge pclk);
      end
      uart_rx <= good_stop ? 1'b1 : 1'b0; repeat (baud_div) @(posedge pclk);
      uart_rx <= 1'b1; repeat (3*baud_div) @(posedge pclk);
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
      // leaving the neighboring early/late samples correct for majority vote.
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
      apb_read(A_STATUS, r, err); expect_eq32("STATUS_RESET", r, 32'h2);
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
      apb_read(A_CTRL, r, err); expect_eq32("CTRL_MASK", r, 32'h2f);
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
      start_scenario("SC_RX_OVERRUN"); reset_dut(); set_baud(4); send_rx_byte(8'h11, 1); send_rx_byte(8'h22, 1);
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

  task write_results;
    begin
      json_fd = $fopen("sim/sim_results.json", "w");
      $fdisplay(json_fd, "{\"passed\":%0s,\"scoreboard_pass\":%0d,\"scoreboard_fail\":%0d,\"scenario_count\":%0d}", (scoreboard_fail==0)?"true":"false", scoreboard_pass, scoreboard_fail, scenario_count);
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
    csv_fd = $fopen("sim/scoreboard_events.csv", "w");
    $fdisplay(csv_fd, "time,scenario,check,result,detail");
    preset_n=0; psel=0; penable=0; pwrite=0; paddr=0; pwdata=0; uart_rx=1;

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

    write_results();
    $fclose(csv_fd);
    if (scoreboard_fail == 0) $display("SIM PASS scoreboard_pass=%0d scenarios=%0d", scoreboard_pass, scenario_count);
    else $display("SIM FAIL scoreboard_fail=%0d scoreboard_pass=%0d", scoreboard_fail, scoreboard_pass);
    #20 $finish;
  end
endmodule
