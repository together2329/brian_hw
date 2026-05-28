`timescale 1ns/1ps

module tb_apb_uart_txrx_demo_random;
  localparam integer APB_ADDR_WIDTH = 8;
  localparam integer BAUD_DIV_WIDTH = 16;
  localparam integer CLK_PERIOD = 10;
  localparam integer NUM_OPS = 12;
  localparam integer MIN_REQUIRED_TXNS = 17;

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
  reg uart_rx;
  reg [APB_ADDR_WIDTH-1:0] paddr;
  reg [31:0] pwdata;
  wire [31:0] prdata;
  wire pready;
  wire pslverr;
  wire uart_tx;
  wire irq;

  integer seed;
  integer initial_seed;
  integer txns;
  integer vcd_en;
  integer csv_fd;
  integer json_fd;
  integer pass_cnt;
  integer fail_cnt;
  integer op;
  integer i;
  integer current_txn;
  integer baud_div;
  integer cfg_data_bits;
  reg [1:0] cfg_sel;
  reg cfg_parity_en;
  reg cfg_parity_odd;
  reg cfg_stop2;
  reg [31:0] r;
  reg err;

  integer cov_frame_cfg;
  integer cov_tx_frame_cfg;
  integer cov_rx_frame_cfg;
  integer cov_parity_good;
  integer cov_parity_error;
  integer cov_stop2;
  integer cov_tx_fifo_burst;
  integer cov_rx_fifo_order;
  integer cov_fifo_full;
  integer cov_overrun;
  integer cov_threshold_irq;
  integer cov_timeout_irq;
  integer cov_loopback;
  integer cov_invalid_access;
  integer cov_break_error;
  integer cov_scratch;

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

  function integer rand_range;
    input integer max_value;
    reg [31:0] raw;
    begin
      raw = $random(seed);
      if (max_value <= 1) begin
        rand_range = 0;
      end else begin
        rand_range = (raw & 32'h7fff_ffff) % max_value;
      end
    end
  endfunction

  function [7:0] rand_byte;
    reg [31:0] raw;
    begin
      raw = $random(seed);
      rand_byte = raw[7:0];
    end
  endfunction

  function integer data_bits_from_sel;
    input [1:0] sel;
    begin
      case (sel)
        2'd0: data_bits_from_sel = 5;
        2'd1: data_bits_from_sel = 6;
        2'd2: data_bits_from_sel = 7;
        default: data_bits_from_sel = 8;
      endcase
    end
  endfunction

  function [7:0] mask_data;
    input [7:0] data;
    input integer bits;
    begin
      case (bits)
        5: mask_data = {3'b000, data[4:0]};
        6: mask_data = {2'b00, data[5:0]};
        7: mask_data = {1'b0, data[6:0]};
        default: mask_data = data;
      endcase
    end
  endfunction

  function parity_for_width;
    input [7:0] data;
    input integer bits;
    input odd;
    integer idx;
    reg parity_xor;
    begin
      parity_xor = 1'b0;
      for (idx = 0; idx < bits; idx = idx + 1) begin
        parity_xor = parity_xor ^ data[idx];
      end
      parity_for_width = odd ? ~parity_xor : parity_xor;
    end
  endfunction

  task log_event;
    input [1023:0] name;
    input ok;
    input [1023:0] detail;
    begin
      if (ok) begin
        pass_cnt = pass_cnt + 1;
      end else begin
        fail_cnt = fail_cnt + 1;
      end
      $fdisplay(csv_fd, "%0t,%0d,%0d,%0s,%0s,%0s", $time, initial_seed, current_txn, name, ok ? "PASS" : "FAIL", detail);
      if (!ok) begin
        $display("RANDOM_FAIL seed=%0d txn=%0d check=%0s detail=%0s", initial_seed, current_txn, name, detail);
      end
    end
  endtask

  task apb_write;
    input [7:0] a;
    input [31:0] d;
    output e;
    begin
      @(posedge pclk);
      psel <= 1'b1; penable <= 1'b0; pwrite <= 1'b1; paddr <= a; pwdata <= d;
      @(posedge pclk);
      penable <= 1'b1;
      #1 e = pslverr;
      @(posedge pclk);
      psel <= 1'b0; penable <= 1'b0; pwrite <= 1'b0; paddr <= '0; pwdata <= '0;
    end
  endtask

  task apb_read;
    input [7:0] a;
    output [31:0] d;
    output e;
    begin
      @(posedge pclk);
      psel <= 1'b1; penable <= 1'b0; pwrite <= 1'b0; paddr <= a; pwdata <= '0;
      @(posedge pclk);
      penable <= 1'b1;
      #1 d = prdata; e = pslverr;
      @(posedge pclk);
      psel <= 1'b0; penable <= 1'b0; paddr <= '0;
    end
  endtask

  task random_gap;
    input integer max_cycles;
    integer g;
    integer n;
    begin
      n = rand_range(max_cycles + 1);
      for (g = 0; g < n; g = g + 1) begin
        @(posedge pclk);
      end
    end
  endtask

  task reset_dut;
    begin
      psel <= 1'b0; penable <= 1'b0; pwrite <= 1'b0; paddr <= '0; pwdata <= '0; uart_rx <= 1'b1;
      preset_n <= 1'b0;
      repeat (6) @(posedge pclk);
      preset_n <= 1'b1;
      repeat (6) @(posedge pclk);
      baud_div = 4;
      cfg_sel = 2'd3;
      cfg_data_bits = 8;
      cfg_parity_en = 1'b0;
      cfg_parity_odd = 1'b0;
      cfg_stop2 = 1'b0;
    end
  endtask

  task program_baud;
    input integer div;
    begin
      baud_div = div;
      apb_write(A_BAUD_DIV, div, err);
      log_event("baud_program", !err, "BAUD_DIV legal write");
    end
  endtask

  task program_frame;
    input [1:0] sel;
    input parity_en;
    input parity_odd;
    input stop2;
    reg [31:0] frame_word;
    reg [1023:0] detail;
    begin
      cfg_sel = sel;
      cfg_data_bits = data_bits_from_sel(sel);
      cfg_parity_en = parity_en;
      cfg_parity_odd = parity_odd;
      cfg_stop2 = stop2;
      frame_word = {27'b0, stop2, parity_odd, parity_en, sel};
      apb_write(A_FRAME_CFG, frame_word, err);
      apb_read(A_FRAME_CFG, r, err);
      $sformat(detail, "frame_word=0x%08x readback=0x%08x bits=%0d parity_en=%0b odd=%0b stop2=%0b", frame_word, r, cfg_data_bits, parity_en, parity_odd, stop2);
      log_event("frame_config_model_readback", !err && (r === frame_word), detail);
      cov_frame_cfg = 1;
    end
  endtask

  task program_random_frame;
    input force_parity;
    input force_stop2;
    reg [1:0] sel_rand;
    reg parity_rand;
    reg odd_rand;
    reg stop2_rand;
    begin
      sel_rand = rand_range(4);
      parity_rand = force_parity ? 1'b1 : (rand_range(2) != 0);
      odd_rand = (rand_range(2) != 0);
      stop2_rand = force_stop2 ? 1'b1 : (rand_range(2) != 0);
      program_frame(sel_rand, parity_rand, odd_rand, stop2_rand);
    end
  endtask

  task wait_tx_idle;
    output ok;
    integer k;
    begin
      ok = 1'b0;
      for (k = 0; k < 5000; k = k + 1) begin
        apb_read(A_STATUS, r, err);
        if (!err && r[1] && !r[2]) begin
          ok = 1'b1;
          k = 5000;
        end
      end
    end
  endtask

  task wait_status_mask;
    input [31:0] mask;
    input [31:0] expected;
    input integer max_reads;
    output [31:0] data;
    output ok;
    integer k;
    begin
      ok = 1'b0;
      data = 32'h0;
      for (k = 0; k < max_reads; k = k + 1) begin
        apb_read(A_STATUS, data, err);
        if (!err && ((data & mask) == expected)) begin
          ok = 1'b1;
          k = max_reads;
        end
      end
    end
  endtask

  task tx_decode_frame;
    output [7:0] data;
    output parity_bit;
    output stop1_bit;
    output stop2_bit;
    output start_seen;
    integer j;
    integer timeout;
    begin
      data = 8'h00;
      parity_bit = 1'b0;
      stop1_bit = 1'b0;
      stop2_bit = 1'b0;
      start_seen = 1'b0;
      for (timeout = 0; timeout < 6000 && uart_tx !== 1'b0; timeout = timeout + 1) begin
        @(posedge pclk);
      end
      if (uart_tx === 1'b0) begin
        start_seen = 1'b1;
        #(CLK_PERIOD*baud_div + CLK_PERIOD/2);
        for (j = 0; j < cfg_data_bits; j = j + 1) begin
          data[j] = uart_tx;
          #(CLK_PERIOD*baud_div);
        end
        if (cfg_parity_en) begin
          parity_bit = uart_tx;
          #(CLK_PERIOD*baud_div);
        end
        stop1_bit = uart_tx;
        #(CLK_PERIOD*baud_div);
        if (cfg_stop2) begin
          stop2_bit = uart_tx;
          #(CLK_PERIOD*baud_div);
        end
      end
    end
  endtask

  task send_rx_frame;
    input [7:0] data;
    input good_parity;
    input good_stop1;
    input good_stop2;
    integer j;
    reg parity_bit;
    begin
      uart_rx <= 1'b1;
      repeat (3) @(posedge pclk);
      uart_rx <= 1'b0; repeat (baud_div) @(posedge pclk);
      for (j = 0; j < cfg_data_bits; j = j + 1) begin
        uart_rx <= data[j]; repeat (baud_div) @(posedge pclk);
      end
      if (cfg_parity_en) begin
        parity_bit = parity_for_width(data, cfg_data_bits, cfg_parity_odd);
        if (!good_parity) parity_bit = ~parity_bit;
        uart_rx <= parity_bit; repeat (baud_div) @(posedge pclk);
      end
      uart_rx <= good_stop1 ? 1'b1 : 1'b0; repeat (baud_div) @(posedge pclk);
      if (cfg_stop2) begin
        uart_rx <= good_stop2 ? 1'b1 : 1'b0; repeat (baud_div) @(posedge pclk);
      end
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

  task random_frame_config_op;
    begin
      reset_dut();
      program_baud(4 + 4*rand_range(4));
      program_random_frame(1'b0, 1'b0);
    end
  endtask

  task random_tx_frame_op;
    reg [7:0] exp;
    reg [7:0] got;
    reg parity_bit;
    reg stop1_bit;
    reg stop2_bit;
    reg start_seen;
    reg idle_ok;
    reg expected_parity;
    reg [1023:0] detail;
    begin
      reset_dut();
      program_baud(4 + 4*rand_range(4));
      program_random_frame(1'b0, 1'b0);
      apb_write(A_CTRL, 32'h0000_0001, err);
      exp = rand_byte();
      fork
        tx_decode_frame(got, parity_bit, stop1_bit, stop2_bit, start_seen);
        begin
          random_gap(3);
          apb_write(A_TXDATA, {24'h0, exp}, err);
          wait_tx_idle(idle_ok);
        end
      join
      expected_parity = parity_for_width(exp, cfg_data_bits, cfg_parity_odd);
      $sformat(detail, "bits=%0d pe=%0b odd=%0b st2=%0b exp=0x%02x got=0x%02x parity=%0b stop1=%0b stop2=%0b idle=%0b", cfg_data_bits, cfg_parity_en, cfg_parity_odd, cfg_stop2, mask_data(exp, cfg_data_bits), got, parity_bit, stop1_bit, stop2_bit, idle_ok);
      log_event("random_tx_frame_configured", !err && start_seen && idle_ok && (got === mask_data(exp, cfg_data_bits)) && stop1_bit && (!cfg_stop2 || stop2_bit) && (!cfg_parity_en || (parity_bit === expected_parity)), detail);
      cov_tx_frame_cfg = 1;
      if (cfg_parity_en) cov_parity_good = 1;
      if (cfg_stop2) cov_stop2 = 1;
    end
  endtask

  task random_rx_frame_op;
    integer err_kind;
    reg [7:0] exp;
    reg [1023:0] detail;
    reg [31:0] status;
    begin
      reset_dut();
      program_baud(4 + 4*rand_range(4));
      // Deterministically cover RX sub-modes during the fixed prefix. Later
      // random invocations continue to randomize the selected sub-mode.
      case (current_txn)
        2:  err_kind = 0; // legal RX frame
        12: err_kind = 1; // parity error
        13: err_kind = 2; // stop/framing error
        14: err_kind = 3; // legal RX frame with parity+stop2 forced
        default: err_kind = rand_range(4);
      endcase
      if (err_kind == 1) begin
        program_random_frame(1'b1, 1'b0);
      end else if (err_kind == 2) begin
        program_random_frame(1'b0, (rand_range(2) != 0));
      end else if (err_kind == 3) begin
        program_random_frame(1'b1, 1'b1);
      end else begin
        program_random_frame(1'b0, 1'b0);
      end
      apb_write(A_CTRL, (err_kind == 0 || err_kind == 3) ? 32'h0000_0001 : 32'h0000_0009, err);
      exp = rand_byte();
      if (err_kind == 1) begin
        send_rx_frame(exp, 1'b0, 1'b1, 1'b1);
        apb_read(A_STATUS, status, err);
        apb_read(A_RXDATA, r, err);
        $sformat(detail, "parity_error bits=%0d exp=0x%02x got=0x%02x status=0x%08x irq=%0b", cfg_data_bits, mask_data(exp, cfg_data_bits), r[7:0], status, irq);
        log_event("random_rx_parity_error", status[8] && irq && (r[7:0] === mask_data(exp, cfg_data_bits)), detail);
        cov_parity_error = 1;
      end else if (err_kind == 2) begin
        send_rx_frame(exp, 1'b1, cfg_stop2 ? 1'b1 : 1'b0, cfg_stop2 ? 1'b0 : 1'b1);
        apb_read(A_STATUS, status, err);
        apb_read(A_RXDATA, r, err);
        $sformat(detail, "frame_error bits=%0d exp=0x%02x got=0x%02x status=0x%08x irq=%0b", cfg_data_bits, mask_data(exp, cfg_data_bits), r[7:0], status, irq);
        log_event("random_rx_framing_error", status[3] && irq && (r[7:0] === mask_data(exp, cfg_data_bits)), detail);
      end else begin
        send_rx_frame(exp, 1'b1, 1'b1, 1'b1);
        apb_read(A_STATUS, status, err);
        apb_read(A_RXDATA, r, err);
        $sformat(detail, "good_rx bits=%0d pe=%0b st2=%0b exp=0x%02x got=0x%02x status=0x%08x", cfg_data_bits, cfg_parity_en, cfg_stop2, mask_data(exp, cfg_data_bits), r[7:0], status);
        log_event("random_rx_frame_configured", !err && status[0] && (r[7:0] === mask_data(exp, cfg_data_bits)) && ((status & 32'h0000_0318) == 32'h0), detail);
        cov_rx_frame_cfg = 1;
        if (cfg_parity_en) cov_parity_good = 1;
        if (cfg_stop2) cov_stop2 = 1;
      end
    end
  endtask

  task random_tx_fifo_burst_op;
    integer len;
    reg [7:0] e0, e1, e2, e3;
    reg [7:0] g0, g1, g2, g3;
    reg p0, p1, p2, p3;
    reg s10, s11, s12, s13;
    reg s20, s21, s22, s23;
    reg seen0, seen1, seen2, seen3;
    reg [1023:0] detail;
    begin
      reset_dut();
      program_baud(16 + 8*rand_range(3));
      program_random_frame(1'b0, 1'b0);
      len = 1 + rand_range(4);
      e0 = rand_byte(); e1 = rand_byte(); e2 = rand_byte(); e3 = rand_byte();
      fork
        begin
          if (len > 0) tx_decode_frame(g0, p0, s10, s20, seen0);
          if (len > 1) tx_decode_frame(g1, p1, s11, s21, seen1);
          if (len > 2) tx_decode_frame(g2, p2, s12, s22, seen2);
          if (len > 3) tx_decode_frame(g3, p3, s13, s23, seen3);
        end
        begin
          if (len > 0) begin apb_write(A_TXDATA, {24'h0, e0}, err); random_gap(3); end
          if (len > 1) begin apb_write(A_TXDATA, {24'h0, e1}, err); random_gap(3); end
          if (len > 2) begin apb_write(A_TXDATA, {24'h0, e2}, err); random_gap(3); end
          if (len > 3) begin apb_write(A_TXDATA, {24'h0, e3}, err); random_gap(3); end
        end
      join
      $sformat(detail, "len=%0d cfg_bits=%0d got=%02x_%02x_%02x_%02x exp=%02x_%02x_%02x_%02x", len, cfg_data_bits, g0, g1, g2, g3, mask_data(e0,cfg_data_bits), mask_data(e1,cfg_data_bits), mask_data(e2,cfg_data_bits), mask_data(e3,cfg_data_bits));
      log_event("random_tx_fifo_burst_order", ((len < 1) || (seen0 && g0 === mask_data(e0,cfg_data_bits))) && ((len < 2) || (seen1 && g1 === mask_data(e1,cfg_data_bits))) && ((len < 3) || (seen2 && g2 === mask_data(e2,cfg_data_bits))) && ((len < 4) || (seen3 && g3 === mask_data(e3,cfg_data_bits))), detail);
      cov_tx_fifo_burst = 1;
    end
  endtask

  task random_rx_fifo_order_overrun_op;
    reg [7:0] e0, e1, e2, e3, e4;
    reg [1023:0] detail;
    reg [31:0] status;
    begin
      reset_dut();
      program_baud(4 + 4*rand_range(3));
      program_random_frame(1'b0, 1'b0);
      e0 = rand_byte(); e1 = rand_byte(); e2 = rand_byte(); e3 = rand_byte(); e4 = rand_byte();
      send_rx_frame(e0, 1'b1, 1'b1, 1'b1);
      random_gap(2);
      send_rx_frame(e1, 1'b1, 1'b1, 1'b1);
      random_gap(2);
      send_rx_frame(e2, 1'b1, 1'b1, 1'b1);
      random_gap(2);
      send_rx_frame(e3, 1'b1, 1'b1, 1'b1);
      send_rx_frame(e4, 1'b1, 1'b1, 1'b1);
      apb_read(A_STATUS, status, err);
      apb_read(A_RXDATA, r, err); e0 = mask_data(e0, cfg_data_bits); log_event("random_rx_fifo_order0", r[7:0] === e0, "RX FIFO oldest byte 0");
      apb_read(A_RXDATA, r, err); e1 = mask_data(e1, cfg_data_bits); log_event("random_rx_fifo_order1", r[7:0] === e1, "RX FIFO oldest byte 1");
      apb_read(A_RXDATA, r, err); e2 = mask_data(e2, cfg_data_bits); log_event("random_rx_fifo_order2", r[7:0] === e2, "RX FIFO oldest byte 2");
      apb_read(A_RXDATA, r, err); e3 = mask_data(e3, cfg_data_bits); log_event("random_rx_fifo_order3", r[7:0] === e3, "RX FIFO oldest byte 3");
      $sformat(detail, "status=0x%08x overrun_bit=%0b discarded=0x%02x", status, status[4], mask_data(e4,cfg_data_bits));
      log_event("random_rx_fifo_overrun", status[4], detail);
      cov_rx_fifo_order = 1;
      cov_overrun = 1;
    end
  endtask

  task random_tx_fifo_full_op;
    reg [31:0] fs;
    reg [1023:0] detail;
    begin
      reset_dut();
      program_baud(24);
      apb_write(A_CTRL, 32'h0000_0021, err); // enable + TX break blocks shifter drain.
      apb_write(A_TXDATA, {24'h0, rand_byte()}, err); log_event("random_tx_fifo_fill0", !err, "fill accepted");
      apb_write(A_TXDATA, {24'h0, rand_byte()}, err); log_event("random_tx_fifo_fill1", !err, "fill accepted");
      apb_write(A_TXDATA, {24'h0, rand_byte()}, err); log_event("random_tx_fifo_fill2", !err, "fill accepted");
      apb_write(A_TXDATA, {24'h0, rand_byte()}, err); log_event("random_tx_fifo_fill3", !err, "fill accepted");
      apb_read(A_FIFO_STATUS, fs, err);
      apb_write(A_TXDATA, {24'h0, rand_byte()}, err);
      $sformat(detail, "fifo_status=0x%08x level=%0d full=%0b extra_err=%0b", fs, fs[7:0], fs[17], err);
      log_event("random_tx_fifo_full_write_error", fs[17] && (fs[7:0] == 8'd4) && err, detail);
      cov_fifo_full = 1;
    end
  endtask

  task random_threshold_irq_op;
    integer rx_thresh;
    integer n;
    reg irq_before;
    reg irq_after;
    reg [31:0] status;
    reg [31:0] irq_status;
    reg [1023:0] detail;
    begin
      reset_dut();
      program_baud(8 + 4*rand_range(3));
      program_frame(2'd3, 1'b0, 1'b0, 1'b0);
      rx_thresh = 1 + rand_range(4);
      apb_write(A_FIFO_THRESH, {16'h0, rx_thresh[7:0], 8'h00}, err);
      apb_write(A_CTRL, 32'h0000_0121, err); // enable + tx_break + fifo_irq_en.
      apb_write(A_TXDATA, {24'h0, rand_byte()}, err); // Keep TX level above threshold 0.
      repeat (3) @(posedge pclk);
      irq_before = irq;
      for (n = 0; n < rx_thresh; n = n + 1) begin
        send_rx_frame(rand_byte(), 1'b1, 1'b1, 1'b1);
      end
      repeat (3) @(posedge pclk);
      irq_after = irq;
      apb_read(A_STATUS, status, err);
      apb_read(A_IRQ_STATUS, irq_status, err);
      $sformat(detail, "rx_thresh=%0d irq_before=%0b irq_after=%0b status=0x%08x irq_status=0x%08x", rx_thresh, irq_before, irq_after, status, irq_status);
      log_event("random_fifo_threshold_irq", !irq_before && irq_after && status[12] && irq_status[5], detail);
      cov_threshold_irq = 1;
    end
  endtask

  task random_timeout_irq_op;
    integer timeout_cycles;
    reg [31:0] status;
    reg [31:0] irq_status;
    reg [1023:0] detail;
    begin
      reset_dut();
      program_baud(4 + 4*rand_range(3));
      program_frame(2'd3, 1'b0, 1'b0, 1'b0);
      timeout_cycles = 8 + rand_range(16);
      apb_write(A_RX_TIMEOUT, timeout_cycles, err);
      apb_write(A_CTRL, 32'h0000_0081, err); // enable + timeout IRQ enable.
      send_rx_frame(rand_byte(), 1'b1, 1'b1, 1'b1);
      repeat (timeout_cycles + 24) @(posedge pclk);
      apb_read(A_STATUS, status, err);
      apb_read(A_IRQ_STATUS, irq_status, err);
      apb_read(A_RXDATA, r, err);
      apb_write(A_STATUS, 32'h0000_0400, err);
      apb_write(A_IRQ_STATUS, 32'h0000_0008, err);
      repeat (3) @(posedge pclk);
      $sformat(detail, "timeout_cycles=%0d status=0x%08x irq_status=0x%08x irq_after_clear=%0b", timeout_cycles, status, irq_status, irq);
      log_event("random_rx_timeout_irq", status[10] && irq_status[3] && !irq, detail);
      cov_timeout_irq = 1;
    end
  endtask

  task random_loopback_op;
    reg [7:0] exp;
    reg rx_seen;
    reg [31:0] status;
    reg [1023:0] detail;
    begin
      reset_dut();
      program_baud(4 + 4*rand_range(3));
      program_random_frame(1'b0, 1'b0);
      exp = rand_byte();
      apb_write(A_CTRL, 32'h0000_0041, err); // enable + loopback.
      apb_write(A_TXDATA, {24'h0, exp}, err);
      wait_status_mask(32'h0000_0001, 32'h0000_0001, 300, status, rx_seen);
      apb_read(A_RXDATA, r, err);
      $sformat(detail, "bits=%0d pe=%0b st2=%0b exp=0x%02x got=0x%02x rx_seen=%0b", cfg_data_bits, cfg_parity_en, cfg_stop2, mask_data(exp,cfg_data_bits), r[7:0], rx_seen);
      log_event("random_loopback", rx_seen && (r[7:0] === mask_data(exp, cfg_data_bits)), detail);
      cov_loopback = 1;
    end
  endtask

  task random_invalid_access_op;
    reg [7:0] bad_addr;
    begin
      reset_dut();
      bad_addr = 8'h80 | (rand_byte() & 8'h3c);
      apb_read(bad_addr, r, err); log_event("random_invalid_read", err, "invalid address read pslverr expected");
      apb_write(bad_addr, $random(seed), err); log_event("random_invalid_write", err, "invalid address write pslverr expected");
      apb_write(A_CTRL, 32'h0000_0000, err);
      apb_write(A_TXDATA, {24'h0, rand_byte()}, err); log_event("random_disabled_txdata_write", err, "disabled TXDATA pslverr expected");
      cov_invalid_access = 1;
    end
  endtask

  task random_break_op;
    reg [31:0] status;
    reg [1023:0] detail;
    begin
      reset_dut();
      program_baud(4 + 4*rand_range(3));
      apb_write(A_CTRL, 32'h0000_0021, err);
      repeat (3) @(posedge pclk);
      log_event("random_tx_break_low", uart_tx === 1'b0, "TX break forces low");
      apb_write(A_CTRL, 32'h0000_0009, err); // enable + error IRQ.
      send_rx_break();
      apb_read(A_STATUS, status, err);
      $sformat(detail, "status=0x%08x irq=%0b", status, irq);
      log_event("random_rx_break_error", status[9] && irq, detail);
      cov_break_error = 1;
    end
  endtask

  task random_scratch_op;
    reg [31:0] value;
    reg [1023:0] detail;
    begin
      reset_dut();
      value = $random(seed);
      apb_write(A_SCRATCH, value, err);
      apb_read(A_SCRATCH, r, err);
      $sformat(detail, "scratch_exp=0x%08x scratch_got=0x%08x", value, r);
      log_event("random_scratch_readback", !err && (r === value), detail);
      cov_scratch = 1;
    end
  endtask

  task run_random_operation;
    input integer op_sel;
    begin
      case (op_sel)
        0: random_frame_config_op();
        1: random_tx_frame_op();
        2: random_rx_frame_op();
        3: random_tx_fifo_burst_op();
        4: random_rx_fifo_order_overrun_op();
        5: random_tx_fifo_full_op();
        6: random_threshold_irq_op();
        7: random_timeout_irq_op();
        8: random_loopback_op();
        9: random_invalid_access_op();
        10: random_break_op();
        default: random_scratch_op();
      endcase
    end
  endtask

  task write_results;
    begin
      json_fd = $fopen("sim/random/random_results.json", "w");
      $fdisplay(json_fd, "{");
      $fdisplay(json_fd, "  \"passed\":%0s,", (fail_cnt==0)?"true":"false");
      $fdisplay(json_fd, "  \"seed\":%0d,", initial_seed);
      $fdisplay(json_fd, "  \"final_seed\":%0d,", seed);
      $fdisplay(json_fd, "  \"txns\":%0d,", txns);
      $fdisplay(json_fd, "  \"scoreboard_pass\":%0d,", pass_cnt);
      $fdisplay(json_fd, "  \"scoreboard_fail\":%0d,", fail_cnt);
      $fdisplay(json_fd, "  \"coverage_flags\":{");
      $fdisplay(json_fd, "    \"frame_cfg\":%0s,", cov_frame_cfg?"true":"false");
      $fdisplay(json_fd, "    \"tx_frame_config\":%0s,", cov_tx_frame_cfg?"true":"false");
      $fdisplay(json_fd, "    \"rx_frame_config\":%0s,", cov_rx_frame_cfg?"true":"false");
      $fdisplay(json_fd, "    \"parity_good\":%0s,", cov_parity_good?"true":"false");
      $fdisplay(json_fd, "    \"parity_error\":%0s,", cov_parity_error?"true":"false");
      $fdisplay(json_fd, "    \"stop2\":%0s,", cov_stop2?"true":"false");
      $fdisplay(json_fd, "    \"tx_fifo_burst\":%0s,", cov_tx_fifo_burst?"true":"false");
      $fdisplay(json_fd, "    \"rx_fifo_order\":%0s,", cov_rx_fifo_order?"true":"false");
      $fdisplay(json_fd, "    \"fifo_full\":%0s,", cov_fifo_full?"true":"false");
      $fdisplay(json_fd, "    \"overrun\":%0s,", cov_overrun?"true":"false");
      $fdisplay(json_fd, "    \"threshold_irq\":%0s,", cov_threshold_irq?"true":"false");
      $fdisplay(json_fd, "    \"timeout_irq\":%0s,", cov_timeout_irq?"true":"false");
      $fdisplay(json_fd, "    \"loopback\":%0s,", cov_loopback?"true":"false");
      $fdisplay(json_fd, "    \"invalid_access\":%0s,", cov_invalid_access?"true":"false");
      $fdisplay(json_fd, "    \"break_error\":%0s,", cov_break_error?"true":"false");
      $fdisplay(json_fd, "    \"scratch\":%0s", cov_scratch?"true":"false");
      $fdisplay(json_fd, "  }");
      $fdisplay(json_fd, "}");
      $fclose(json_fd);
    end
  endtask

  initial begin
    if (!$value$plusargs("SEED=%d", seed)) seed = 1;
    initial_seed = seed;
    if (!$value$plusargs("TXNS=%d", txns)) txns = 20;
    if (txns < MIN_REQUIRED_TXNS) txns = MIN_REQUIRED_TXNS;
    if (!$value$plusargs("VCD=%d", vcd_en)) vcd_en = 0;
    if (vcd_en) begin
      $dumpfile("sim/random/waves/random.vcd");
      $dumpvars(0, tb_apb_uart_txrx_demo_random);
    end

    csv_fd = $fopen("sim/random/random_scoreboard_events.csv", "w");
    $fdisplay(csv_fd, "time,seed,txn,check,result,detail");
    pass_cnt = 0;
    fail_cnt = 0;
    current_txn = -1;
    cov_frame_cfg = 0;
    cov_tx_frame_cfg = 0;
    cov_rx_frame_cfg = 0;
    cov_parity_good = 0;
    cov_parity_error = 0;
    cov_stop2 = 0;
    cov_tx_fifo_burst = 0;
    cov_rx_fifo_order = 0;
    cov_fifo_full = 0;
    cov_overrun = 0;
    cov_threshold_irq = 0;
    cov_timeout_irq = 0;
    cov_loopback = 0;
    cov_invalid_access = 0;
    cov_break_error = 0;
    cov_scratch = 0;

    reset_dut();
    apb_read(A_CTRL, r, err);
    log_event("reset_ctrl", !err && r == 32'h0000_0001, "CTRL reset value");
    apb_read(A_FRAME_CFG, r, err);
    log_event("reset_frame_cfg", !err && r == 32'h0000_0003, "FRAME_CFG reset value");

    for (i = 0; i < txns; i = i + 1) begin
      current_txn = i;
      if (i < NUM_OPS) begin
        op = i;
      end else if (i < MIN_REQUIRED_TXNS) begin
        // Force RX-frame submodes after the one-pass operation sweep so all
        // seeds cover good RX, parity error, framing error, and parity+stop2.
        op = 2;
      end else begin
        op = rand_range(NUM_OPS);
      end
      run_random_operation(op);
      random_gap(5);
    end
    write_results();
    $fclose(csv_fd);
    if (fail_cnt == 0) begin
      $display("RANDOM PASS seed=%0d txns=%0d pass=%0d", initial_seed, txns, pass_cnt);
    end else begin
      $display("RANDOM FAIL seed=%0d txns=%0d fail=%0d pass=%0d", initial_seed, txns, fail_cnt, pass_cnt);
    end
    #20 $finish;
  end
endmodule
