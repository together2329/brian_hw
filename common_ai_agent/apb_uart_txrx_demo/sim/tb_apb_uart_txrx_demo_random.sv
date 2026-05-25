`timescale 1ns/1ps

module tb_apb_uart_txrx_demo_random;
  localparam integer APB_ADDR_WIDTH = 8;
  localparam integer BAUD_DIV_WIDTH = 16;
  localparam integer CLK_PERIOD = 10;
  localparam [7:0] A_CTRL=8'h00, A_STATUS=8'h04, A_BAUD_DIV=8'h08, A_TXDATA=8'h0c, A_RXDATA=8'h10, A_IRQ_STATUS=8'h14;

  reg pclk, preset_n, psel, penable, pwrite, uart_rx;
  reg [APB_ADDR_WIDTH-1:0] paddr;
  reg [31:0] pwdata;
  wire [31:0] prdata;
  wire pready, pslverr, uart_tx, irq;

  integer seed, initial_seed, txns, vcd_en, csv_fd, json_fd, pass_cnt, fail_cnt, op, i, baud_div;
  reg [31:0] r;
  reg err;
  reg [7:0] b;

  apb_uart_txrx_demo #(.APB_ADDR_WIDTH(APB_ADDR_WIDTH), .BAUD_DIV_WIDTH(BAUD_DIV_WIDTH)) dut (
    .pclk(pclk), .preset_n(preset_n), .psel(psel), .penable(penable), .pwrite(pwrite),
    .paddr(paddr), .pwdata(pwdata), .prdata(prdata), .pready(pready), .pslverr(pslverr),
    .uart_tx(uart_tx), .uart_rx(uart_rx), .irq(irq)
  );

  initial begin pclk=0; forever #(CLK_PERIOD/2) pclk=~pclk; end

  task log_event;
    input [1023:0] name; input ok; input [1023:0] detail;
    begin
      if (ok) pass_cnt=pass_cnt+1; else fail_cnt=fail_cnt+1;
      $fdisplay(csv_fd, "%0t,%0d,%0s,%0s,%0s", $time, initial_seed, name, ok?"PASS":"FAIL", detail);
      if (!ok) $display("RANDOM_FAIL %0s %0s", name, detail);
    end
  endtask

  task apb_write; input [7:0] a; input [31:0] d; output e; begin
    @(posedge pclk); psel<=1; penable<=0; pwrite<=1; paddr<=a; pwdata<=d;
    @(posedge pclk); penable<=1; #1 e=pslverr;
    @(posedge pclk); psel<=0; penable<=0; pwrite<=0; paddr<=0; pwdata<=0;
  end endtask

  task apb_read; input [7:0] a; output [31:0] d; output e; begin
    @(posedge pclk); psel<=1; penable<=0; pwrite<=0; paddr<=a; pwdata<=0;
    @(posedge pclk); penable<=1; #1 d=prdata; e=pslverr;
    @(posedge pclk); psel<=0; penable<=0; paddr<=0;
  end endtask

  task reset_dut; begin
    psel<=0; penable<=0; pwrite<=0; paddr<=0; pwdata<=0; uart_rx<=1; preset_n<=0; baud_div=4;
    repeat(6) @(posedge pclk); preset_n<=1; repeat(6) @(posedge pclk);
  end endtask

  task wait_tx_idle; integer k; begin
    for (k=0;k<300;k=k+1) begin
      apb_read(A_STATUS,r,err);
      if (!err && r[1] && !r[2]) k=300;
    end
  end endtask

  task decode_tx; output [7:0] d; integer j; begin
    wait(uart_tx===0); #(CLK_PERIOD*baud_div + CLK_PERIOD/2);
    for (j=0;j<8;j=j+1) begin d[j]=uart_tx; #(CLK_PERIOD*baud_div); end
  end endtask

  task send_rx; input [7:0] d; input good_stop; integer j; begin
    uart_rx<=1; repeat(2) @(posedge pclk);
    uart_rx<=0; repeat(baud_div) @(posedge pclk);
    for (j=0;j<8;j=j+1) begin uart_rx<=d[j]; repeat(baud_div) @(posedge pclk); end
    uart_rx<=good_stop?1'b1:1'b0; repeat(baud_div) @(posedge pclk);
    uart_rx<=1; repeat(baud_div*3) @(posedge pclk);
  end endtask

  task random_ctrl; reg [31:0] d; begin
    d = {$random(seed)} & 32'h0000_000f; d[0]=1'b1;
    apb_write(A_CTRL,d,err); log_event("random_irq_enable_toggle", !err, "CTRL legal write");
  end endtask

  task random_invalid; reg [7:0] a; begin
    a = 8'h80 | ({$random(seed)} & 8'h3c);
    apb_read(a,r,err); log_event("random_invalid_read", err, "invalid read pslverr expected");
    apb_write(a,{$random(seed)},err); log_event("random_invalid_write", err, "invalid write pslverr expected");
  end endtask

  task random_tx; reg [7:0] exp, got; begin
    wait_tx_idle(); exp = {$random(seed)};
    fork
      decode_tx(got);
      begin apb_write(A_TXDATA,{24'h0,exp},err); wait_tx_idle(); end
    join
    log_event("random_tx_byte", !err && got===exp, "TX decoded byte matches APB write");
  end endtask

  task random_rx; reg [7:0] exp; reg good; begin
    exp={$random(seed)}; good = (({$random(seed)} % 5) != 0);
    send_rx(exp,good);
    apb_read(A_STATUS,r,err);
    if (good) begin
      log_event("random_rx_valid", !err && r[0], "good RX frame sets rx_valid");
      apb_read(A_RXDATA,r,err); log_event("random_rx_byte", !err && r[7:0]===exp, "RXDATA matches injected byte");
    end else begin
      log_event("random_rx_bad_stop", !err && r[3], "bad stop sets frame_err");
      apb_write(A_STATUS,32'h8,err); apb_write(A_IRQ_STATUS,32'h4,err);
    end
  end endtask

  initial begin
    if (!$value$plusargs("SEED=%d", seed)) seed=1;
    initial_seed = seed;
    if (!$value$plusargs("TXNS=%d", txns)) txns=20;
    if (!$value$plusargs("VCD=%d", vcd_en)) vcd_en=0;
    if (vcd_en) begin $dumpfile("sim/random/waves/random.vcd"); $dumpvars(0,tb_apb_uart_txrx_demo_random); end
    csv_fd=$fopen("sim/random/random_scoreboard_events.csv","w");
    $fdisplay(csv_fd,"time,seed,check,result,detail");
    pass_cnt=0; fail_cnt=0; reset_dut();
    apb_read(A_CTRL,r,err); log_event("reset_ctrl", !err && r==32'h1, "CTRL reset");
    apb_write(A_BAUD_DIV,4,err); baud_div=4; log_event("set_baud_default", !err, "BAUD_DIV=4");
    for (i=0;i<txns;i=i+1) begin
      op = {$random(seed)} % 5;
      case (op)
        0: random_ctrl();
        1: random_invalid();
        2: random_tx();
        3: random_rx();
        default: begin apb_read(A_STATUS,r,err); log_event("random_status_read", !err, "STATUS legal read"); end
      endcase
      repeat(({$random(seed)} & 3)+1) @(posedge pclk);
    end
    json_fd=$fopen("sim/random/random_results.json","w");
    $fdisplay(json_fd,"{\"passed\":%0s,\"seed\":%0d,\"txns\":%0d,\"scoreboard_pass\":%0d,\"scoreboard_fail\":%0d}",(fail_cnt==0)?"true":"false",initial_seed,txns,pass_cnt,fail_cnt);
    $fclose(json_fd); $fclose(csv_fd);
    if (fail_cnt==0) $display("RANDOM PASS seed=%0d txns=%0d pass=%0d",initial_seed,txns,pass_cnt);
    else $display("RANDOM FAIL seed=%0d fail=%0d pass=%0d",initial_seed,fail_cnt,pass_cnt);
    #20 $finish;
  end
endmodule
